"""Collector that merges multiple provider results into one normalized snapshot."""

from __future__ import annotations

import asyncio
from typing import Any
import httpx

from app.core.config import settings
from app.services.financial_snapshot.constants import OUTPUT_FIELDS
from app.services.financial_snapshot.providers import AkShareProvider, EastMoneyProvider, TushareProvider
from app.services.financial_snapshot.quality import evaluate_snapshot_quality
from app.services.financial_snapshot.types import CompanyFinancialSnapshot, ProviderErrorInfo, ProviderResult


FIELD_PRIORITY: dict[str, tuple[str, ...]] = {
    "company_name": ("eastmoney.identity", "tushare.identity", "akshare.identity"),
    "stock_code": ("eastmoney.identity", "tushare.identity", "akshare.identity"),
    "ts_code": ("tushare.identity",),
    "exchange": ("eastmoney.identity", "tushare.identity", "akshare.identity"),
    "industry": ("eastmoney.identity", "tushare.identity", "akshare.identity"),
    "close_price": ("tushare.market", "eastmoney.market", "akshare.market"),
    "market_cap": ("eastmoney.valuation", "tushare.valuation", "akshare.valuation"),
    "pe_ratio": ("eastmoney.valuation", "tushare.valuation", "akshare.valuation"),
    "pb_ratio": ("eastmoney.valuation", "tushare.valuation", "akshare.valuation"),
    "ps_ratio": ("eastmoney.valuation", "tushare.valuation", "akshare.valuation"),
    "revenue": ("eastmoney.financial_statement", "akshare.financial_statement", "tushare.financial_statement"),
    "net_profit": ("eastmoney.financial_statement", "akshare.financial_statement", "tushare.financial_statement"),
    "gross_margin": ("eastmoney.financial_statement", "tushare.financial_indicator", "akshare.financial_indicator"),
    "net_margin": ("tushare.financial_indicator", "akshare.financial_indicator"),
    "roe": ("tushare.financial_indicator", "akshare.financial_indicator"),
    "roa": ("tushare.financial_indicator", "akshare.financial_indicator"),
    "total_assets": ("eastmoney.financial_statement", "akshare.financial_statement", "tushare.financial_statement"),
    "total_liabilities": ("eastmoney.financial_statement", "akshare.financial_statement", "tushare.financial_statement"),
    "equity": ("eastmoney.financial_statement", "akshare.financial_statement", "tushare.financial_statement"),
    "asset_liability_ratio": ("eastmoney.financial_indicator", "tushare.financial_indicator", "akshare.financial_indicator"),
    "debt_to_equity": ("eastmoney.financial_indicator", "tushare.financial_indicator", "akshare.financial_indicator"),
    "current_assets": ("akshare.financial_statement", "tushare.financial_statement"),
    "current_liabilities": ("akshare.financial_statement", "tushare.financial_statement"),
    "current_ratio": ("eastmoney.financial_indicator", "tushare.financial_indicator", "akshare.financial_indicator"),
    "quick_ratio": ("eastmoney.financial_indicator", "tushare.financial_indicator", "akshare.financial_indicator"),
    "operating_cash_flow": ("eastmoney.financial_statement", "akshare.financial_statement", "tushare.financial_statement"),
    "investing_cash_flow": ("akshare.financial_statement", "tushare.financial_statement"),
    "financing_cash_flow": ("akshare.financial_statement", "tushare.financial_statement"),
    "operating_cash_flow_to_net_profit": ("tushare.financial_indicator", "akshare.financial_indicator"),
    "data_date": (
        "tushare.market",
        "eastmoney.market",
        "akshare.market",
        "eastmoney.financial_statement",
        "akshare.financial_statement",
        "tushare.financial_statement",
        "eastmoney.valuation",
        "tushare.valuation",
        "akshare.valuation",
    ),
}

LABEL_TO_STAGE: dict[str, str] = {
    "identity": "resolve_stock",
    "market": "market_snapshot",
    "valuation": "valuation_snapshot",
    "financial_statement": "financial_statement_snapshot",
    "financial_indicator": "financial_indicator_snapshot",
}


class FinancialSnapshotCollector:
    def __init__(
        self,
        *,
        eastmoney_provider: Any | None = None,
        tushare_provider: Any | None = None,
        akshare_provider: Any | None = None,
    ) -> None:
        self.eastmoney_provider = eastmoney_provider or EastMoneyProvider()
        self.tushare_provider = tushare_provider or TushareProvider(token=settings.TUSHARE_TOKEN or None)
        if akshare_provider is not None:
            self.akshare_provider = akshare_provider
        else:
            try:
                import akshare as ak  # type: ignore
            except Exception:
                self.akshare_provider = None
            else:
                self.akshare_provider = AkShareProvider(client_factory=lambda: ak)

    async def collect(self, *, company_name: str | None = None, stock_code: str | None = None) -> CompanyFinancialSnapshot:
        provider_results: dict[str, ProviderResult] = {}

        eastmoney_identity = await self._safe_provider_call(
            label="eastmoney.identity",
            call=self.eastmoney_provider.resolve_stock(company_name=company_name, stock_code=stock_code),
        )
        provider_results["eastmoney.identity"] = eastmoney_identity

        tushare_identity: ProviderResult | None = None
        akshare_identity: ProviderResult | None = None
        if eastmoney_identity.get("success") is not True:
            tushare_identity = await self._safe_provider_call(
                label="tushare.identity",
                call=self.tushare_provider.resolve_stock(company_name=company_name, stock_code=stock_code),
            )
            provider_results["tushare.identity"] = tushare_identity
            if tushare_identity.get("success") is not True and self.akshare_provider is not None:
                akshare_identity = await self._safe_provider_call(
                    label="akshare.identity",
                    call=self.akshare_provider.resolve_stock(company_name=company_name, stock_code=stock_code),
                )
                provider_results["akshare.identity"] = akshare_identity
            else:
                provider_results["akshare.identity"] = self._empty_provider_result(provider="akshare")
        else:
            provider_results["tushare.identity"] = self._empty_provider_result(provider="tushare")
            provider_results["akshare.identity"] = self._empty_provider_result(provider="akshare")

        identity = self._choose_identity(eastmoney_identity, tushare_identity, akshare_identity)
        normalized_stock_code = identity.get("stock_code") or stock_code
        normalized_ts_code = identity.get("ts_code")

        stage_calls = {
            "eastmoney.market": self.eastmoney_provider.get_market_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
            "eastmoney.valuation": self.eastmoney_provider.get_valuation_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
            "eastmoney.financial_statement": self.eastmoney_provider.get_financial_statement_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
            "eastmoney.financial_indicator": self.eastmoney_provider.get_financial_indicator_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
            "tushare.market": self.tushare_provider.get_market_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
            "tushare.valuation": self.tushare_provider.get_valuation_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
            "tushare.financial_statement": self.tushare_provider.get_financial_statement_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
            "tushare.financial_indicator": self.tushare_provider.get_financial_indicator_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
        }
        if self.akshare_provider is not None:
            stage_calls.update(
                {
                    "akshare.market": self.akshare_provider.get_market_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
                    "akshare.valuation": self.akshare_provider.get_valuation_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
                    "akshare.financial_statement": self.akshare_provider.get_financial_statement_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
                    "akshare.financial_indicator": self.akshare_provider.get_financial_indicator_snapshot(stock_code=normalized_stock_code, ts_code=normalized_ts_code),
                }
            )
        stage_results = await asyncio.gather(*stage_calls.values(), return_exceptions=True)
        provider_results.update(
            {
                label: self._normalize_provider_result(label=label, result=result)
                for label, result in zip(stage_calls.keys(), stage_results)
            }
        )

        snapshot: CompanyFinancialSnapshot = {
            "source_fields": self._merge_source_fields(provider_results),
            "field_sources": {},
            "errors": self._collect_errors(provider_results),
        }
        snapshot.update(identity)

        for field in OUTPUT_FIELDS:
            value, source = self._pick_field(field=field, provider_results=provider_results, fallback_value=snapshot.get(field))
            snapshot[field] = value
            if source is not None:
                snapshot["field_sources"][field] = [source]

        contributors = sorted({sources[0].split(".")[0] for sources in snapshot["field_sources"].values() if sources})
        snapshot["data_source"] = ",".join(contributors) if contributors else None

        quality = evaluate_snapshot_quality(snapshot)
        snapshot["missing_fields"] = quality["missing_fields"]
        snapshot["missing_core_fields"] = quality["missing_core_fields"]
        snapshot["missing_ratio"] = quality["missing_ratio"]
        snapshot["insufficient_data"] = quality["insufficient_data"]
        snapshot["quality_note"] = quality["quality_note"]
        return snapshot

    @staticmethod
    def _choose_identity(
        eastmoney_identity: ProviderResult,
        tushare_identity: ProviderResult | None,
        akshare_identity: ProviderResult | None,
    ) -> dict[str, Any]:
        if eastmoney_identity.get("success"):
            return dict(eastmoney_identity.get("data") or {})
        if tushare_identity and tushare_identity.get("success"):
            return dict(tushare_identity.get("data") or {})
        if akshare_identity and akshare_identity.get("success"):
            return dict(akshare_identity.get("data") or {})
        return {}

    @staticmethod
    def _empty_provider_result(*, provider: str) -> ProviderResult:
        return {
            "provider": provider,
            "stage": "resolve_stock",
            "success": False,
            "data": {},
            "source_fields": {},
            "field_sources": {},
            "missing_fields": [],
            "errors": [],
        }

    @staticmethod
    def _merge_source_fields(provider_results: dict[str, ProviderResult]) -> dict[str, list[str]]:
        merged: dict[str, list[str]] = {}
        for label, result in provider_results.items():
            for key, value in (result.get("source_fields") or {}).items():
                merged[f"{label}.{key}"] = list(value)
        return merged

    @staticmethod
    def _collect_errors(provider_results: dict[str, ProviderResult]) -> list[ProviderErrorInfo]:
        errors: list[ProviderErrorInfo] = []
        for result in provider_results.values():
            errors.extend(result.get("errors") or [])
        return errors

    @staticmethod
    def _is_present(value: Any) -> bool:
        if value is None:
            return False
        try:
            return bool(value == value)
        except Exception:
            return False

    def _pick_field(
        self,
        *,
        field: str,
        provider_results: dict[str, ProviderResult],
        fallback_value: Any = None,
    ) -> tuple[Any, str | None]:
        for label in FIELD_PRIORITY.get(field, ()):
            value = (provider_results.get(label, {}).get("data") or {}).get(field)
            if self._is_present(value):
                return value, label
        return fallback_value, None

    async def _safe_provider_call(self, *, label: str, call) -> ProviderResult:
        try:
            result = await call
        except Exception as exc:
            return self._exception_to_error_result(label=label, exc=exc)
        return self._normalize_provider_result(label=label, result=result)

    def _normalize_provider_result(self, *, label: str, result: ProviderResult | Exception | Any) -> ProviderResult:
        if isinstance(result, Exception):
            return self._exception_to_error_result(label=label, exc=result)
        if isinstance(result, dict):
            return result
        return self._exception_to_error_result(
            label=label,
            exc=TypeError(f"Provider returned invalid result type: {type(result).__name__}"),
        )

    def _exception_to_error_result(self, *, label: str, exc: Exception) -> ProviderResult:
        provider, stage_label = (label.split(".", 1) + [""])[:2]
        stage = LABEL_TO_STAGE.get(stage_label, stage_label or "unknown")
        code = "upstream_error"
        retriable = True

        if isinstance(exc, PermissionError):
            code = "permission_denied"
            retriable = False
        elif isinstance(exc, httpx.TimeoutException):
            code = "timeout"
        elif isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code is not None and 300 <= status_code < 400:
                code = "redirect_response"
                retriable = False
            elif status_code is not None and 400 <= status_code < 500:
                code = "bad_response"
                retriable = False
        elif isinstance(exc, ValueError):
            code = "invalid_payload"
            retriable = False

        return {
            "provider": provider,
            "stage": stage,
            "success": False,
            "data": {},
            "source_fields": {},
            "field_sources": {},
            "missing_fields": [],
            "errors": [
                {
                    "provider": provider,
                    "stage": stage,
                    "message": str(exc),
                    "code": code,
                    "retriable": retriable,
                }
            ],
        }
