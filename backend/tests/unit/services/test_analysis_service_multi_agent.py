from uuid import uuid4

from app.services.agents.orchestrator import AgentRunRecord, OrchestrationResult
from app.services.agents.schemas import (
    AgentResult,
    AgentRole,
    AgentRunStatus,
    EvidenceItem,
    ReportSections,
    SynthesisResult,
)
from app.services.analysis import AnalysisService


def _build_role_result(role: AgentRole, score: float) -> AgentResult:
    return AgentResult(
        role=role,
        summary=f"{role.value} summary",
        score=score,
        thesis=[f"{role.value} thesis"],
        positives=[f"{role.value} positive"],
        risks=[f"{role.value} risk"],
        evidence=[
            EvidenceItem(
                item=f"{role.value} evidence",
                source="2024 annual report",
                confidence=0.85,
            )
        ],
        red_flags=[],
        questions=[],
        insufficient_data=False,
    )


def test_build_agent_context_maps_company_and_ratio_fields():
    service = AnalysisService()

    context = service._build_agent_context(
        analysis_id=str(uuid4()),
        company_name="Test Holdings",
        stock_code="600000",
        company_data={
            "industry": "Utilities",
            "exchange": "SSE",
            "revenue": 10_000_000,
            "net_profit": 1_000_000,
            "gross_margin": 18.2,
            "roe": 12.3,
            "asset_liability_ratio": 45.6,
            "operating_cash_flow": 2_000_000,
        },
        financial_ratios={
            "gross_margin": 18.2,
            "net_margin": 10.1,
            "roe": 12.3,
            "roa": 4.5,
            "current_ratio": 1.2,
        },
    )

    assert context.company_name == "Test Holdings"
    assert context.stock_code == "600000"
    assert context.basic_profile.industry == "Utilities"
    assert context.financial_data.net_profit == 1_000_000
    assert context.financial_ratios.current_ratio == 1.2
    assert context.data_quality.is_mock is True


def test_render_orchestration_markdown_includes_degrade_and_sections():
    service = AnalysisService()
    orchestration_result = OrchestrationResult(
        role_runs=[
            AgentRunRecord(
                role=AgentRole.MUNGER,
                status=AgentRunStatus.COMPLETED,
                result=_build_role_result(AgentRole.MUNGER, 7.5),
            ),
            AgentRunRecord(
                role=AgentRole.INDUSTRY,
                status=AgentRunStatus.FAILED,
                error_message="industry role timeout",
            ),
            AgentRunRecord(
                role=AgentRole.AUDIT,
                status=AgentRunStatus.COMPLETED,
                result=_build_role_result(AgentRole.AUDIT, 6.2),
            ),
        ],
        synthesis_result=SynthesisResult(
            company_profile="Test Holdings profile",
            final_score=6.8,
            investment_decision="Neutral",
            insufficient_data=False,
            consensus=["Cash flow remains stable"],
            major_risks=["Missing industry evidence"],
            report_sections=ReportSections(
                munger_view="Munger says valuation is acceptable.",
                synthesis="Synthesis is conservative due to missing industry role.",
            ),
        ),
    )

    markdown = service._render_orchestration_markdown(orchestration_result)

    assert "最终评分：6.80/10" in markdown
    assert "降级执行：角色失败 -> 产业视角" in markdown
    assert "Munger says valuation is acceptable." in markdown
    assert "Synthesis is conservative due to missing industry role." in markdown
