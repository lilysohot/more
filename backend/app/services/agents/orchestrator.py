from __future__ import annotations

from dataclasses import dataclass, field
from inspect import isawaitable
from typing import Any, Awaitable, Callable, Protocol

from app.services.agents.audit_agent import AuditAgent
from app.services.agents.base import AgentExecutionError
from app.services.agents.industry_agent import IndustryAgent
from app.services.agents.munger_agent import MungerAgent
from app.services.agents.schemas import (
    AgentContext,
    AgentResult,
    AgentRole,
    AgentRunStatus,
    ProgressStage,
    SynthesisResult,
)
from app.services.agents.synthesis_agent import SynthesisAgent

StageCallback = Callable[[ProgressStage], Awaitable[None] | None]


class RoleAgentProtocol(Protocol):
    async def run(self, context: AgentContext) -> AgentResult:
        ...

    def get_last_run_trace(self) -> dict[str, str | None]:
        ...


class SynthesisAgentProtocol(Protocol):
    async def run_with_results(
        self,
        context: AgentContext,
        role_results: list[AgentResult],
    ) -> SynthesisResult:
        ...

    def get_last_run_trace(self) -> dict[str, str | None]:
        ...


@dataclass
class AgentRunRecord:
    role: AgentRole
    status: AgentRunStatus
    result: AgentResult | None = None
    error_message: str | None = None
    trace: dict[str, str | None] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    role_runs: list[AgentRunRecord]
    synthesis_result: SynthesisResult
    synthesis_trace: dict[str, str | None] = field(default_factory=dict)

    @property
    def role_results(self) -> list[AgentResult]:
        return [run.result for run in self.role_runs if run.result is not None]

    @property
    def failed_roles(self) -> list[AgentRole]:
        return [run.role for run in self.role_runs if run.status == AgentRunStatus.FAILED]


class AgentOrchestrator:
    """Run role agents sequentially and then synthesize their outputs."""

    def __init__(
        self,
        *,
        munger_agent: RoleAgentProtocol | None = None,
        industry_agent: RoleAgentProtocol | None = None,
        audit_agent: RoleAgentProtocol | None = None,
        synthesis_agent: SynthesisAgentProtocol | None = None,
        llm_config: dict[str, Any] | None = None,
        on_stage: StageCallback | None = None,
    ):
        self.munger_agent = munger_agent or MungerAgent(llm_config=llm_config)
        self.industry_agent = industry_agent or IndustryAgent(llm_config=llm_config)
        self.audit_agent = audit_agent or AuditAgent(llm_config=llm_config)
        self.synthesis_agent = synthesis_agent or SynthesisAgent(llm_config=llm_config)
        self.on_stage = on_stage

    async def run(self, context: AgentContext) -> OrchestrationResult:
        role_runs: list[AgentRunRecord] = []

        role_pipeline: tuple[tuple[AgentRole, ProgressStage, RoleAgentProtocol], ...] = (
            (AgentRole.MUNGER, ProgressStage.RUNNING_MUNGER_AGENT, self.munger_agent),
            (AgentRole.INDUSTRY, ProgressStage.RUNNING_INDUSTRY_AGENT, self.industry_agent),
            (AgentRole.AUDIT, ProgressStage.RUNNING_AUDIT_AGENT, self.audit_agent),
        )

        for role, stage, agent in role_pipeline:
            await self._emit_stage(stage)
            run_record = await self._run_role_agent(role, agent, context)
            role_runs.append(run_record)

        await self._emit_stage(ProgressStage.RUNNING_SYNTHESIS_AGENT)
        synthesis_result = await self.synthesis_agent.run_with_results(context, self._collect_success(role_runs))
        synthesis_trace = self._safe_trace(self.synthesis_agent)

        return OrchestrationResult(
            role_runs=role_runs,
            synthesis_result=synthesis_result,
            synthesis_trace=synthesis_trace,
        )

    async def _run_role_agent(
        self,
        role: AgentRole,
        agent: RoleAgentProtocol,
        context: AgentContext,
    ) -> AgentRunRecord:
        try:
            result = await agent.run(context)
            return AgentRunRecord(
                role=role,
                status=AgentRunStatus.COMPLETED,
                result=result,
                trace=self._safe_trace(agent),
            )
        except AgentExecutionError as exc:
            return AgentRunRecord(
                role=role,
                status=AgentRunStatus.FAILED,
                error_message=str(exc),
                trace=self._safe_trace(agent),
            )
        except Exception as exc:
            return AgentRunRecord(
                role=role,
                status=AgentRunStatus.FAILED,
                error_message=f"Unexpected {role.value} error: {exc}",
                trace=self._safe_trace(agent),
            )

    async def _emit_stage(self, stage: ProgressStage) -> None:
        callback = self.on_stage
        if callback is None:
            return
        maybe_awaitable = callback(stage)
        if isawaitable(maybe_awaitable):
            await maybe_awaitable

    @staticmethod
    def _collect_success(role_runs: list[AgentRunRecord]) -> list[AgentResult]:
        return [run.result for run in role_runs if run.result is not None]

    @staticmethod
    def _safe_trace(agent: Any) -> dict[str, str | None]:
        trace_getter = getattr(agent, "get_last_run_trace", None)
        if not callable(trace_getter):
            return {}
        trace = trace_getter()
        if not isinstance(trace, dict):
            return {}
        return trace
