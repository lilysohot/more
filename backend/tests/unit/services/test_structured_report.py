import math
from datetime import datetime
from uuid import uuid4

from app.models.user import Analysis, Report
from app.services.agents.orchestrator import AgentRunRecord, OrchestrationResult
from app.services.agents.schemas import (
    AgentResult,
    AgentRole,
    AgentRunStatus,
    EvidenceItem,
    SynthesisResult,
)
from app.services.structured_report import build_report_response, build_structured_report_payload


def _role_result(role: AgentRole) -> AgentResult:
    return AgentResult(
        role=role,
        summary=f"{role.value} summary",
        score=7.0,
        thesis=[f"{role.value} thesis"],
        positives=[f"{role.value} positive"],
        risks=[f"{role.value} risk"],
        evidence=[
            EvidenceItem(
                item=f"{role.value} evidence",
                source="unit test",
                confidence=0.8,
            )
        ],
    )


def _orchestration_result() -> OrchestrationResult:
    return OrchestrationResult(
        role_runs=[
            AgentRunRecord(
                role=AgentRole.MUNGER,
                status=AgentRunStatus.COMPLETED,
                result=_role_result(AgentRole.MUNGER),
            )
        ],
        synthesis_result=SynthesisResult(
            company_profile="测试公司画像",
            final_score=7.0,
            investment_decision="观察",
            core_reasons=["估值需要安全边际"],
            major_risks=["财务数据缺失"],
        ),
    )


def test_structured_report_marks_none_and_nan_financial_values_as_missing():
    payload = build_structured_report_payload(
        company_data={
            "company_name": "测试股份",
            "stock_code": "600000",
            "revenue": 1000000,
            "net_profit": math.nan,
            "market_cap": None,
            "pe_ratio": 8.5,
        },
        financial_ratios={
            "gross_margin": float("nan"),
            "roe": 12.0,
            "current_ratio": None,
        },
        orchestration_result=_orchestration_result(),
    )

    assert payload["financials"]["revenue"] == 1000000
    assert payload["financials"]["net_profit"] is None
    assert payload["financials"]["gross_margin"] is None
    assert payload["financials"]["market_cap"] is None
    assert payload["financials"]["roe"] == 12.0
    assert "net_profit" in payload["data_quality"]["missing_financial_fields"]
    assert "gross_margin" in payload["data_quality"]["missing_financial_fields"]
    assert "market_cap" in payload["data_quality"]["missing_financial_fields"]
    assert "current_ratio" in payload["data_quality"]["missing_financial_fields"]
    assert "revenue" not in payload["data_quality"]["missing_financial_fields"]
    assert "roe" not in payload["data_quality"]["missing_financial_fields"]
    assert payload["data_quality"]["quality_note"].startswith("使用结构化实时数据")
    assert "Using" not in payload["data_quality"]["quality_note"]


def test_report_response_backfills_missing_financial_fields_for_stale_snapshots():
    analysis_id = uuid4()
    report = Report(
        id=uuid4(),
        analysis_id=analysis_id,
        content_md="# 测试报告",
        content_html="<h1>测试报告</h1>",
        created_at=datetime.utcnow(),
        structured_data_json={
            "financials": {
                "revenue": None,
                "net_profit": None,
                "market_cap": None,
            },
            "data_quality": {
                "is_mock": False,
                "quality_note": None,
                "missing_fields": [],
                "missing_financial_fields": [],
                "completed_agent_count": 3,
                "failed_agent_roles": [],
            },
        },
    )

    payload = build_report_response(
        analysis=Analysis(
            id=analysis_id,
            user_id=uuid4(),
            company_name="测试股份",
            stock_code="600000",
            status="completed",
        ),
        report=report,
        agent_runs=[],
    )

    missing_fields = payload["data_quality"]["missing_financial_fields"]
    assert len(missing_fields) == 20
    assert "revenue" in missing_fields
    assert "net_profit" in missing_fields
    assert "market_cap" in missing_fields
