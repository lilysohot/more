"""Model-driven public evidence supplements for incomplete company data."""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field, ValidationError

from app.services.llm_service import LLMService


LLMCaller = Callable[[str], Awaitable[str | None]]

TRIGGER_ERROR_CODES = {"permission_denied", "permission_or_unavailable", "unavailable"}
TEXT_SUPPLEMENT_FIELDS = (
    "company_profile",
    "business_segments",
    "recent_announcements",
    "data_gap_explanation",
)
DISCLOSURE_SUPPLEMENT_FIELDS = (
    "revenue",
    "net_profit",
    "total_assets",
    "total_liabilities",
    "operating_cash_flow",
    "roe",
)
NON_SUPPLEMENTABLE_FIELDS = {
    "market_cap",
    "pe_ratio",
    "pb_ratio",
    "ps_ratio",
    "close_price",
}
SUPPLEMENTABLE_FIELDS = set(TEXT_SUPPLEMENT_FIELDS) | set(DISCLOSURE_SUPPLEMENT_FIELDS)


class SupplementEvidence(BaseModel):
    url: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    date: str | None = None


class SupplementEntry(BaseModel):
    field: str = Field(min_length=1)
    value: Any = None
    unit: str | None = None
    source_type: str = "llm_search"
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence: list[SupplementEvidence] = Field(default_factory=list)
    report_period: str | None = None
    observed_at: str | None = None
    can_merge: bool = False


class SupplementResult(BaseModel):
    company_name: str
    stock_code: str | None = None
    supplements: list[SupplementEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    not_found: list[str] = Field(default_factory=list)


class ModelSupplementService:
    DEFAULT_TARGET_FIELDS = TEXT_SUPPLEMENT_FIELDS

    def __init__(
        self,
        *,
        llm_caller: LLMCaller | None = None,
        llm_service_factory: Callable[[dict[str, Any]], Any] = LLMService,
    ) -> None:
        self._llm_caller = llm_caller
        self._llm_service_factory = llm_service_factory

    @classmethod
    def build_target_fields(cls, company_data: dict[str, Any]) -> list[str]:
        if not cls.should_trigger(company_data):
            return []

        targets: list[str] = []
        for field in TEXT_SUPPLEMENT_FIELDS:
            if not company_data.get(field):
                targets.append(field)

        missing_core_fields = {str(field) for field in (company_data.get("missing_core_fields") or []) if field}
        missing_fields = {str(field) for field in (company_data.get("missing_fields") or []) if field}

        for field in DISCLOSURE_SUPPLEMENT_FIELDS:
            if field in missing_core_fields or (field in missing_fields and company_data.get(field) is None):
                targets.append(field)

        if missing_fields or missing_core_fields or cls._has_trigger_errors(company_data):
            targets.append("data_gap_explanation")

        return cls._dedupe(targets)

    @staticmethod
    def should_trigger(company_data: dict[str, Any]) -> bool:
        if company_data.get("insufficient_data"):
            return True
        if company_data.get("missing_core_fields"):
            return True
        if ModelSupplementService._has_trigger_errors(company_data):
            return True
        return False

    @staticmethod
    def trigger_reasons(company_data: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        if company_data.get("insufficient_data"):
            reasons.append("insufficient_data")
        if company_data.get("missing_core_fields"):
            reasons.append("missing_core_fields")
        for error in company_data.get("errors") or []:
            code = str(error.get("code") or "").strip()
            if code in TRIGGER_ERROR_CODES:
                reasons.append(f"provider_error:{code}")
        return ModelSupplementService._dedupe(reasons)

    def build_prompt(self, *, company_data: dict[str, Any], target_fields: list[str]) -> str:
        task_date = str(
            company_data.get("analysis_date")
            or company_data.get("task_date")
            or datetime.now(UTC).date().isoformat()
        )
        payload = {
            "company_name": company_data.get("company_name"),
            "stock_code": company_data.get("stock_code"),
            "task_date": task_date,
            "time_window": "last two years (24 months) relative to task_date",
            "snapshot_summary": self._snapshot_summary(company_data),
            "missing_fields": list(company_data.get("missing_fields") or []),
            "missing_core_fields": list(company_data.get("missing_core_fields") or []),
            "provider_errors": self._provider_error_summary(company_data),
            "target_fields": target_fields,
            "allowed_sources": [
                "Listed company announcements",
                "Annual reports",
                "Quarterly reports",
                "Exchange disclosure documents",
                "Official company website",
                "Authoritative public financial media reports",
            ],
            "output_schema": {
                "company_name": "string",
                "stock_code": "string|null",
                "supplements": [
                    {
                        "field": "string",
                        "value": "any",
                        "unit": "string|null",
                        "source_type": "llm_search",
                        "confidence": "0-1 float",
                        "evidence": [{"url": "string", "quote": "string", "date": "YYYY-MM-DD"}],
                        "report_period": "string|null",
                        "observed_at": "YYYY-MM-DD|null",
                        "can_merge": "boolean",
                    }
                ],
                "warnings": ["string"],
                "not_found": ["string"],
            },
        }
        return (
            "You are a public-disclosure data supplement module. "
            "Only search and extract evidence within the last two years (24 months) relative to task_date. "
            "If a source is older than 24 months, only use it as historical background and do not mark it mergeable. "
            "Do not estimate or infer values. Only extract explicit values from public disclosures. "
            "Do not modify company_name or stock_code. "
            "Return JSON only.\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

    async def collect(
        self,
        *,
        company_data: dict[str, Any],
        target_fields: list[str],
        llm_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        canonical_company_name = str(company_data.get("company_name") or "").strip()
        canonical_stock_code = self._normalize_stock_code(company_data.get("stock_code"))
        if not canonical_company_name:
            raise ValueError("company_name is required for model supplements")

        prompt = self.build_prompt(company_data=company_data, target_fields=target_fields)
        raw_output = await self._invoke_llm(prompt=prompt, llm_config=llm_config)
        parsed = self._parse_result(raw_output)
        task_date = str(
            company_data.get("analysis_date")
            or company_data.get("task_date")
            or datetime.now(UTC).date().isoformat()
        )
        normalized = self._normalize_identity(
            result=parsed,
            company_name=canonical_company_name,
            stock_code=canonical_stock_code,
        )
        return self._sanitize_supplements(normalized, task_date=task_date)

    @staticmethod
    def merge_into_company_data(company_data: dict[str, Any], supplement_result: dict[str, Any]) -> dict[str, Any]:
        merged = dict(company_data)
        merged["company_name"] = company_data.get("company_name")
        merged["stock_code"] = company_data.get("stock_code")
        merged["provider_data_date"] = company_data.get("provider_data_date") or company_data.get("data_date")

        supplements = list(company_data.get("supplements") or [])
        supplements.extend(list(supplement_result.get("supplements") or []))
        merged["supplements"] = supplements
        merged["supplement_warnings"] = list(supplement_result.get("warnings") or [])
        merged["supplement_not_found"] = list(supplement_result.get("not_found") or [])

        report_periods = dict(company_data.get("supplement_report_periods") or {})
        merged_dates: list[str] = []
        observed_dates: list[str] = []

        for item in supplement_result.get("supplements") or []:
            evidences = item.get("evidence") or []
            dated_evidences = [str(e.get("date")) for e in evidences if e.get("date")]
            observed_dates.extend(dated_evidences)
            if item.get("can_merge") is not True:
                continue
            if not evidences:
                continue
            if not dated_evidences:
                continue
            merged_dates.extend(dated_evidences)

            field = str(item.get("field") or "").strip()
            value = item.get("value")
            if field in NON_SUPPLEMENTABLE_FIELDS:
                continue
            if field == "company_profile" and not merged.get("company_profile"):
                merged["company_profile"] = value
            elif field == "business_segments" and not merged.get("business_segments"):
                merged["business_segments"] = value
            elif field == "recent_announcements" and not merged.get("recent_announcements"):
                merged["recent_announcements"] = value
            elif field == "data_gap_explanation" and not merged.get("data_gap_explanation"):
                merged["data_gap_explanation"] = value
            elif field in DISCLOSURE_SUPPLEMENT_FIELDS and merged.get(field) is None:
                merged[field] = value
            else:
                continue

            if item.get("report_period"):
                report_periods[field] = item.get("report_period")

        if merged_dates:
            merged["supplement_data_date"] = max(merged_dates)
        elif observed_dates:
            merged["supplement_data_date"] = max(observed_dates)
        merged["supplement_report_periods"] = report_periods

        data_quality = dict(merged.get("data_quality") or {})
        data_quality["supplement_warnings"] = merged["supplement_warnings"]
        data_quality["supplement_not_found"] = merged["supplement_not_found"]
        merged["data_quality"] = data_quality
        return merged

    async def _invoke_llm(self, *, prompt: str, llm_config: dict[str, Any] | None) -> str:
        if self._llm_caller is not None:
            raw_output = await self._llm_caller(prompt)
            if not isinstance(raw_output, str):
                raise ValueError("llm_caller must return a JSON string")
            return raw_output

        if llm_config is None:
            raise ValueError("llm_config is required when llm_caller is not provided")

        llm_service = self._llm_service_factory(llm_config)
        raw_output = await llm_service.generate(prompt)
        if not isinstance(raw_output, str):
            raise ValueError("LLM service must return a string")
        return raw_output

    @staticmethod
    def _parse_result(raw_output: str) -> dict[str, Any]:
        candidate = ModelSupplementService._extract_json(raw_output)
        try:
            parsed = SupplementResult.model_validate(json.loads(candidate))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"invalid supplement JSON: {exc}") from exc
        return parsed.model_dump(mode="json")

    @staticmethod
    def _extract_json(raw_output: str) -> str:
        text = str(raw_output or "").strip()
        if text.startswith("{") and text.endswith("}"):
            return text
        fenced_match = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced_match:
            return fenced_match.group(1)
        object_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if object_match:
            return object_match.group(1)
        return text

    @staticmethod
    def _normalize_identity(
        *,
        result: dict[str, Any],
        company_name: str,
        stock_code: str | None,
    ) -> dict[str, Any]:
        normalized = dict(result)
        warnings = list(normalized.get("warnings") or [])
        parsed_company_name = str(normalized.get("company_name") or "").strip()
        parsed_stock_code = ModelSupplementService._normalize_stock_code(normalized.get("stock_code"))

        if parsed_company_name and parsed_company_name != company_name:
            warnings.append("identity mismatch detected for company_name")
        if stock_code and parsed_stock_code and parsed_stock_code != stock_code:
            warnings.append("identity mismatch detected for stock_code")

        normalized["company_name"] = company_name
        normalized["stock_code"] = stock_code
        normalized["warnings"] = warnings
        return normalized

    @classmethod
    def _sanitize_supplements(cls, supplement_result: dict[str, Any], *, task_date: str) -> dict[str, Any]:
        normalized = dict(supplement_result)
        warnings = list(normalized.get("warnings") or [])
        sanitized: list[dict[str, Any]] = []
        task_date_value = cls._parse_date(task_date)

        for raw_item in normalized.get("supplements") or []:
            item = dict(raw_item)
            field = str(item.get("field") or "").strip()
            if not field:
                warnings.append("supplement field is empty")
                continue
            if field in NON_SUPPLEMENTABLE_FIELDS:
                item["can_merge"] = False
                warnings.append(f"field {field} is not supplementable")
            elif field not in SUPPLEMENTABLE_FIELDS:
                item["can_merge"] = False
                warnings.append(f"field {field} is not in supplement whitelist")

            evidences = list(item.get("evidence") or [])
            has_dated_evidence = any(bool(e.get("date")) for e in evidences)
            if item.get("can_merge") is True and not has_dated_evidence:
                item["can_merge"] = False
                warnings.append(f"field {field} missing evidence date")
            elif item.get("can_merge") is True and task_date_value is not None:
                newest_evidence_date = cls._newest_evidence_date(evidences)
                if newest_evidence_date is not None and (task_date_value - newest_evidence_date).days > 730:
                    item["can_merge"] = False
                    warnings.append(f"field {field} evidence is older than 24 months")

            item["evidence"] = evidences
            sanitized.append(item)

        normalized["warnings"] = cls._dedupe(warnings)
        normalized["supplements"] = sanitized
        return normalized

    @staticmethod
    def _snapshot_summary(company_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "industry": company_data.get("industry"),
            "exchange": company_data.get("exchange"),
            "data_source": company_data.get("data_source"),
            "data_date": company_data.get("data_date"),
            "provider_data_date": company_data.get("provider_data_date") or company_data.get("data_date"),
            "field_sources": company_data.get("field_sources"),
        }

    @staticmethod
    def _provider_error_summary(company_data: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "provider": error.get("provider"),
                "stage": error.get("stage"),
                "code": error.get("code"),
                "message": error.get("message"),
            }
            for error in (company_data.get("errors") or [])
        ]

    @staticmethod
    def _has_trigger_errors(company_data: dict[str, Any]) -> bool:
        for error in company_data.get("errors") or []:
            code = str(error.get("code") or "").strip()
            if code in TRIGGER_ERROR_CODES:
                return True
        return False

    @staticmethod
    def _normalize_stock_code(stock_code: Any) -> str | None:
        if not stock_code:
            return None
        return str(stock_code).split(".")[0].strip().upper() or None

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
        return ordered

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

    @classmethod
    def _newest_evidence_date(cls, evidences: list[dict[str, Any]]) -> date | None:
        dates = [cls._parse_date(evidence.get("date")) for evidence in evidences]
        valid_dates = [item for item in dates if item is not None]
        return max(valid_dates) if valid_dates else None
