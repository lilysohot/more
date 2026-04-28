from uuid import uuid4

import pytest

from app.services.agents.base import AgentExecutionError
from app.services.agents.orchestrator import AgentOrchestrator
from app.services.agents.schemas import (
    AgentContext,
    AgentResult,
    AgentRole,
    AgentRunStatus,
    EvidenceItem,
    ProgressStage,
    SourceItem,
    SynthesisResult,
)


def _build_context() -> AgentContext:
    return AgentContext(
        analysis_id=uuid4(),
        company_name="Test Holdings",
        stock_code="600000",
        sources=[
            SourceItem(name="2024 annual report", type="report", date="2025-03-30"),
            SourceItem(name="Q1 earnings call", type="transcript", date="2026-04-20"),
        ],
    )


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
                source_type="report",
                source_date="2025-03-30",
                confidence=0.8,
            )
        ],
        red_flags=[],
        questions=[],
        insufficient_data=False,
    )


class StubRoleAgent:
    def __init__(
        self,
        *,
        result: AgentResult | None = None,
        error: Exception | None = None,
        trace: dict[str, str | None] | None = None,
    ):
        self.result = result
        self.error = error
        self.trace = trace or {
            "prompt": "role prompt",
            "raw_output": "role output",
            "retry_raw_output": None,
            "parse_error": None,
        }
        self.call_count = 0

    async def run(self, _context: AgentContext) -> AgentResult:
        self.call_count += 1
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise AssertionError("StubRoleAgent requires result when error is not set")
        return self.result

    def get_last_run_trace(self) -> dict[str, str | None]:
        return self.trace


class StubSynthesisAgent:
    def __init__(
        self,
        *,
        result: SynthesisResult,
        trace: dict[str, str | None] | None = None,
    ):
        self.result = result
        self.trace = trace or {
            "prompt": "synthesis prompt",
            "raw_output": "synthesis output",
            "retry_raw_output": None,
            "parse_error": None,
        }
        self.call_count = 0
        self.received_role_results: list[AgentResult] = []

    async def run_with_results(
        self,
        _context: AgentContext,
        role_results: list[AgentResult],
    ) -> SynthesisResult:
        self.call_count += 1
        self.received_role_results = list(role_results)
        return self.result

    def get_last_run_trace(self) -> dict[str, str | None]:
        return self.trace


@pytest.mark.asyncio
async def test_orchestrator_runs_full_pipeline_successfully():
    context = _build_context()
    stages: list[ProgressStage] = []

    async def on_stage(stage: ProgressStage) -> None:
        stages.append(stage)

    synthesis_agent = StubSynthesisAgent(
        result=SynthesisResult(
            company_profile="Stable operator",
            final_score=7.3,
            investment_decision="Watchlist",
        )
    )
    orchestrator = AgentOrchestrator(
        munger_agent=StubRoleAgent(result=_build_role_result(AgentRole.MUNGER, 7.6)),
        industry_agent=StubRoleAgent(result=_build_role_result(AgentRole.INDUSTRY, 7.2)),
        audit_agent=StubRoleAgent(result=_build_role_result(AgentRole.AUDIT, 6.9)),
        synthesis_agent=synthesis_agent,
        on_stage=on_stage,
    )

    result = await orchestrator.run(context)

    assert [run.role for run in result.role_runs] == [
        AgentRole.MUNGER,
        AgentRole.INDUSTRY,
        AgentRole.AUDIT,
    ]
    assert [run.status for run in result.role_runs] == [
        AgentRunStatus.COMPLETED,
        AgentRunStatus.COMPLETED,
        AgentRunStatus.COMPLETED,
    ]
    assert result.failed_roles == []
    assert [item.role for item in synthesis_agent.received_role_results] == [
        AgentRole.MUNGER,
        AgentRole.INDUSTRY,
        AgentRole.AUDIT,
    ]
    assert stages == [
        ProgressStage.RUNNING_MUNGER_AGENT,
        ProgressStage.RUNNING_INDUSTRY_AGENT,
        ProgressStage.RUNNING_AUDIT_AGENT,
        ProgressStage.RUNNING_SYNTHESIS_AGENT,
    ]
    assert result.synthesis_result.final_score == pytest.approx(7.3)
    assert result.synthesis_trace["prompt"] == "synthesis prompt"


@pytest.mark.asyncio
async def test_orchestrator_degrades_when_single_role_fails():
    context = _build_context()
    synthesis_agent = StubSynthesisAgent(
        result=SynthesisResult(
            company_profile="Degraded synthesis",
            final_score=6.8,
            investment_decision="Neutral",
        )
    )
    orchestrator = AgentOrchestrator(
        munger_agent=StubRoleAgent(result=_build_role_result(AgentRole.MUNGER, 7.5)),
        industry_agent=StubRoleAgent(
            error=AgentExecutionError("industry role timeout"),
            trace={
                "prompt": "industry prompt",
                "raw_output": None,
                "retry_raw_output": None,
                "parse_error": "industry role timeout",
            },
        ),
        audit_agent=StubRoleAgent(result=_build_role_result(AgentRole.AUDIT, 6.1)),
        synthesis_agent=synthesis_agent,
    )

    result = await orchestrator.run(context)

    assert [run.status for run in result.role_runs] == [
        AgentRunStatus.COMPLETED,
        AgentRunStatus.FAILED,
        AgentRunStatus.COMPLETED,
    ]
    assert result.failed_roles == [AgentRole.INDUSTRY]
    assert result.role_runs[1].error_message == "industry role timeout"
    assert [item.role for item in synthesis_agent.received_role_results] == [
        AgentRole.MUNGER,
        AgentRole.AUDIT,
    ]
    assert result.synthesis_result.investment_decision == "Neutral"
