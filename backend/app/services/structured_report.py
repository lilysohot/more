"""Build structured report payloads for API responses and persistence."""

from __future__ import annotations

import math
from typing import Any

from app.models.user import AgentRun, Analysis, Report
from app.services.agents import AgentRole, OrchestrationResult


AGENT_TITLES = {
    AgentRole.MUNGER.value: "芒格视角",
    AgentRole.INDUSTRY.value: "产业视角",
    AgentRole.AUDIT.value: "审计视角",
    AgentRole.SYNTHESIS.value: "综合汇总",
}

FINANCIAL_FIELDS = (
    "revenue",
    "net_profit",
    "gross_margin",
    "net_margin",
    "roe",
    "roa",
    "total_assets",
    "total_liabilities",
    "equity",
    "market_cap",
    "pe_ratio",
    "pb_ratio",
    "ps_ratio",
    "close_price",
    "asset_liability_ratio",
    "debt_to_equity",
    "current_ratio",
    "quick_ratio",
    "operating_cash_flow",
    "operating_cash_flow_to_net_profit",
)


def build_structured_report_payload(
    *,
    company_data: dict[str, Any],
    financial_ratios: dict[str, Any],
    orchestration_result: OrchestrationResult,
) -> dict[str, Any]:
    """Create a JSON-safe structured payload at report generation time."""

    company = _compact_dict(
        {
            "company_name": company_data.get("company_name"),
            "stock_code": company_data.get("stock_code"),
            "ts_code": company_data.get("ts_code"),
            "exchange": company_data.get("exchange"),
            "industry": company_data.get("industry"),
            "data_source": company_data.get("data_source"),
            "data_date": company_data.get("data_date"),
        }
    )

    financials = _build_financials(company_data=company_data, financial_ratios=financial_ratios)
    agents = [_build_agent_from_role_run(role_run) for role_run in orchestration_result.role_runs]
    synthesis = orchestration_result.synthesis_result.model_dump(mode="json")
    failed_agent_roles = [role.value for role in orchestration_result.failed_roles]
    missing_financial_fields = [field for field in FINANCIAL_FIELDS if _is_missing(financials.get(field))]

    return _json_safe(
        {
            "company": company,
            "financials": financials,
            "synthesis": synthesis,
            "agents": agents,
            "data_quality": {
                "is_mock": False,
                "quality_note": _build_quality_note(company_data, missing_financial_fields),
                "missing_fields": company_data.get("missing_fields") or [],
                "missing_financial_fields": missing_financial_fields,
                "completed_agent_count": len([agent for agent in agents if agent.get("status") == "completed"]),
                "failed_agent_roles": failed_agent_roles,
            },
        }
    )


def build_report_response(
    *,
    analysis: Analysis,
    report: Report,
    agent_runs: list[AgentRun],
) -> dict[str, Any]:
    """Build the API response while preserving legacy top-level report fields."""

    payload = dict(report.structured_data_json or {})
    company = {
        "company_name": analysis.company_name,
        "stock_code": analysis.stock_code,
        **(payload.get("company") or {}),
    }
    financials = payload.get("financials") or {}
    agents = payload.get("agents") or _build_agents_from_records(agent_runs)
    synthesis = payload.get("synthesis") or _build_synthesis_from_records(agent_runs)
    data_quality = _normalize_data_quality(payload.get("data_quality"), agent_runs, financials)

    return _json_safe(
        {
            "id": report.id,
            "analysis_id": report.analysis_id,
            "content_md": report.content_md,
            "content_html": report.content_html,
            "created_at": report.created_at,
            "company": company,
            "financials": financials,
            "synthesis": synthesis,
            "agents": agents,
            "data_quality": data_quality,
            "original": {
                "content_md": report.content_md,
                "content_html": report.content_html,
            },
        }
    )


def _build_agent_from_role_run(role_run: Any) -> dict[str, Any]:
    role = role_run.role.value if hasattr(role_run.role, "value") else str(role_run.role)
    result = role_run.result.model_dump(mode="json") if role_run.result is not None else {}

    return {
        "name": role,
        "title": AGENT_TITLES.get(role, role),
        "status": _enum_value(role_run.status),
        "score": result.get("score"),
        "summary": result.get("summary"),
        "thesis": result.get("thesis") or [],
        "positives": result.get("positives") or [],
        "risks": result.get("risks") or [],
        "red_flags": result.get("red_flags") or [],
        "questions": result.get("questions") or [],
        "evidence": result.get("evidence") or [],
        "insufficient_data": result.get("insufficient_data") or False,
        "error_message": role_run.error_message,
    }


def _build_agents_from_records(agent_runs: list[AgentRun]) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    for record in agent_runs:
        if record.role == AgentRole.SYNTHESIS.value:
            continue

        data = record.structured_output_json or {}
        agents.append(
            {
                "name": record.role,
                "title": AGENT_TITLES.get(record.role, record.role),
                "status": record.status,
                "score": data.get("score"),
                "summary": data.get("summary"),
                "thesis": data.get("thesis") or [],
                "positives": data.get("positives") or [],
                "risks": data.get("risks") or [],
                "red_flags": data.get("red_flags") or [],
                "questions": data.get("questions") or [],
                "evidence": data.get("evidence") or [],
                "insufficient_data": data.get("insufficient_data") or False,
                "error_message": record.error_message,
            }
        )

    order = {AgentRole.MUNGER.value: 0, AgentRole.INDUSTRY.value: 1, AgentRole.AUDIT.value: 2}
    return sorted(agents, key=lambda agent: order.get(agent["name"], 99))


def _build_synthesis_from_records(agent_runs: list[AgentRun]) -> dict[str, Any] | None:
    synthesis_record = next((record for record in agent_runs if record.role == AgentRole.SYNTHESIS.value), None)
    if synthesis_record is None:
        return None

    data = synthesis_record.structured_output_json or {}
    return {
        "company_profile": data.get("company_profile"),
        "consensus": data.get("consensus") or [],
        "disagreements": data.get("disagreements") or [],
        "final_score": data.get("final_score"),
        "investment_decision": data.get("investment_decision"),
        "insufficient_data": data.get("insufficient_data") or False,
        "core_reasons": data.get("core_reasons") or [],
        "major_risks": data.get("major_risks") or [],
    }


def _build_financials(*, company_data: dict[str, Any], financial_ratios: dict[str, Any]) -> dict[str, Any]:
    financials: dict[str, Any] = {}
    for field in FINANCIAL_FIELDS:
        value = _normalize_scalar(company_data.get(field))
        if _is_missing(value):
            value = _normalize_scalar(financial_ratios.get(field))
        financials[field] = value
    return financials


def _build_quality_from_records(agent_runs: list[AgentRun], financials: dict[str, Any]) -> dict[str, Any]:
    failed_agent_roles = [record.role for record in agent_runs if record.status != "completed"]
    completed_agent_count = len([record for record in agent_runs if record.status == "completed" and record.role != AgentRole.SYNTHESIS.value])
    missing_financial_fields = [field for field in FINANCIAL_FIELDS if _is_missing(financials.get(field))]

    return {
        "is_mock": False,
        "quality_note": "结构化财务快照不可用，已从历史 AgentRun 降级组装报告。" if missing_financial_fields else None,
        "missing_fields": [],
        "missing_financial_fields": missing_financial_fields,
        "completed_agent_count": completed_agent_count,
        "failed_agent_roles": failed_agent_roles,
    }


def _normalize_data_quality(
    data_quality: dict[str, Any] | None,
    agent_runs: list[AgentRun],
    financials: dict[str, Any],
) -> dict[str, Any]:
    normalized = dict(data_quality or _build_quality_from_records(agent_runs, financials))
    missing_financial_fields = [field for field in FINANCIAL_FIELDS if _is_missing(financials.get(field))]
    normalized["missing_financial_fields"] = missing_financial_fields
    normalized.setdefault("missing_fields", [])
    normalized.setdefault("completed_agent_count", 0)
    normalized.setdefault("failed_agent_roles", [])
    normalized.setdefault("is_mock", False)
    if missing_financial_fields and not normalized.get("quality_note"):
        normalized["quality_note"] = _build_quality_note({}, missing_financial_fields)
    return normalized


def _build_quality_note(company_data: dict[str, Any], missing_financial_fields: list[str]) -> str:
    source = company_data.get("data_source") or "unknown"
    if not missing_financial_fields:
        return f"使用结构化实时数据来源：{source}。"

    visible_missing = ", ".join(missing_financial_fields[:8])
    suffix = "..." if len(missing_financial_fields) > 8 else ""
    return f"使用结构化实时数据来源：{source}，缺失财务字段：{visible_missing}{suffix}。"


def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: _json_safe(item) for key, item in value.items() if _json_safe(item) is not None}


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    value = _normalize_scalar(value)
    if _is_missing(value):
        return None
    return value


def _normalize_scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    try:
        return bool(value != value)
    except Exception:
        return False
