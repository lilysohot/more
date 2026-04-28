import json
from uuid import uuid4

import pytest

from app.services.agents.base import (
    AgentConfigurationError,
    AgentLLMError,
    AgentParseError,
    AgentParseRetryExhaustedError,
)
from app.services.agents.audit_agent import AuditAgent
from app.services.agents.industry_agent import IndustryAgent
from app.services.agents.munger_agent import MungerAgent
from app.services.agents.schemas import AgentContext, AgentResult, AgentRole, SourceItem
from app.services.agents.synthesis_agent import SynthesisAgent


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


def _valid_role_output(role: str = "munger") -> str:
    payload = {
        "role": role,
        "summary": "业务质量保持稳健，下行风险总体可控。",
        "score": 7.8,
        "thesis": ["定价能力仍然稳定", "现金生成能力保持韧性"],
        "positives": ["毛利率表现较为稳定"],
        "risks": ["竞争强度可能上升"],
        "evidence": [
            {
                "item": "毛利率维持在历史均值以上",
                "source": "2024 annual report",
                "source_type": "report",
                "source_date": "2025-03-30",
                "confidence": 0.83,
            }
        ],
        "red_flags": [],
        "questions": [],
        "insufficient_data": False,
    }
    return json.dumps(payload)


def _valid_synthesis_output() -> str:
    payload = {
        "company_profile": "该公司具备稳定盈利能力与适度增长潜力。",
        "consensus": ["盈利质量可接受", "资产负债风险可控"],
        "disagreements": [
            {
                "topic": "近中期增长是否能提速",
                "munger": "尚不确定",
                "industry": "行业景气回升可能带动需求",
                "audit": "需要更清晰的业务披露",
            }
        ],
        "final_score": 7.4,
        "investment_decision": "观察",
        "insufficient_data": False,
        "core_reasons": ["毛利率韧性依然较强", "现金转换质量可接受"],
        "major_risks": ["宏观波动回落不及预期", "扩张执行风险"],
        "report_sections": {
            "intro": "本报告汇总了多角色观点，形成平衡判断。",
            "munger_view": "业务韧性表现平稳。",
            "industry_view": "行业竞争持续但具备结构性机会。",
            "audit_view": "未识别明显红旗信号。",
            "synthesis": "综合评估后偏向审慎乐观。",
        },
    }
    return json.dumps(payload)


class SequenceCaller:
    def __init__(self, outputs: list[str]):
        self.outputs = list(outputs)
        self.prompts: list[str] = []

    async def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.outputs:
            raise RuntimeError("No more outputs configured")
        return self.outputs.pop(0)


def test_role_prompt_contains_role_and_context():
    context = _build_context()
    agent = IndustryAgent()

    prompt = agent.build_prompt(context)

    assert "industry" in prompt
    assert "Test Holdings" in prompt
    assert "输出契约" in prompt
    assert "所有面向报告展示的文本字段必须使用中文" in prompt


def test_role_prompts_have_clear_role_boundaries():
    context = _build_context()
    munger_prompt = MungerAgent().build_prompt(context).lower()
    industry_prompt = IndustryAgent().build_prompt(context).lower()
    audit_prompt = AuditAgent().build_prompt(context).lower()

    assert "护城河" in munger_prompt
    assert "供需结构" in industry_prompt
    assert "财务报表质量" in audit_prompt
    assert "边界规则" in munger_prompt
    assert "边界规则" in industry_prompt
    assert "边界规则" in audit_prompt


def test_role_parse_success():
    agent = AuditAgent()

    result = agent.parse_response(_valid_role_output(role="audit"))

    assert result.role == AgentRole.AUDIT
    assert result.score == pytest.approx(7.8)
    assert len(result.evidence) == 1


def test_role_parse_role_mismatch_raises():
    agent = MungerAgent()

    with pytest.raises(AgentParseError):
        agent.parse_response(_valid_role_output(role="industry"))


def test_role_parse_rejects_english_report_text():
    payload = json.loads(_valid_role_output(role="munger"))
    payload["summary"] = "Business quality remains solid with manageable downside risks."
    agent = MungerAgent()

    with pytest.raises(AgentParseError, match="Chinese text"):
        agent.parse_response(json.dumps(payload))


@pytest.mark.asyncio
async def test_run_retries_once_then_succeeds():
    context = _build_context()
    caller = SequenceCaller(outputs=["not json", _valid_role_output(role="munger")])
    agent = MungerAgent(llm_caller=caller)

    result = await agent.run(context)

    assert result.role == AgentRole.MUNGER
    assert len(caller.prompts) == 2
    assert agent.last_raw_output == "not json"
    assert agent.last_retry_raw_output is not None


@pytest.mark.asyncio
async def test_role_run_repairs_english_output_into_chinese():
    context = _build_context()
    english_payload = json.loads(_valid_role_output(role="munger"))
    english_payload["summary"] = "Business quality remains solid with manageable downside risks."
    caller = SequenceCaller(outputs=[json.dumps(english_payload), _valid_role_output(role="munger")])
    agent = MungerAgent(llm_caller=caller)

    result = await agent.run(context)

    assert result.summary == "业务质量保持稳健，下行风险总体可控。"
    assert len(caller.prompts) == 2
    assert "中文" in caller.prompts[1]


@pytest.mark.asyncio
async def test_run_retry_exhausted_raises():
    context = _build_context()
    caller = SequenceCaller(outputs=["bad output", "still bad"])
    agent = IndustryAgent(llm_caller=caller)

    with pytest.raises(AgentParseRetryExhaustedError):
        await agent.run(context)

    assert len(caller.prompts) == 2
    assert agent.last_retry_raw_output == "still bad"


@pytest.mark.asyncio
async def test_run_without_llm_path_raises_configuration_error():
    context = _build_context()
    agent = AuditAgent()

    with pytest.raises(AgentConfigurationError):
        await agent.run(context)


@pytest.mark.asyncio
async def test_llm_callable_failure_is_wrapped():
    context = _build_context()

    async def failing_caller(_prompt: str) -> str:
        raise RuntimeError("upstream failure")

    agent = MungerAgent(llm_caller=failing_caller)

    with pytest.raises(AgentLLMError):
        await agent.run(context)


@pytest.mark.asyncio
async def test_provider_routing_uses_openai_method():
    context = _build_context()

    class DummyOpenAIService:
        provider = "openai"

        def __init__(self):
            self.calls: list[str] = []

        async def _call_openai(self, _prompt: str) -> str:
            self.calls.append("openai")
            return _valid_role_output(role="munger")

        async def _call_dashscope(self, _prompt: str) -> str:
            self.calls.append("dashscope")
            raise AssertionError("dashscope method should not be called")

    service = DummyOpenAIService()
    agent = MungerAgent(llm_service=service)

    result = await agent.run(context)

    assert result.role == AgentRole.MUNGER
    assert service.calls == ["openai"]


@pytest.mark.asyncio
async def test_synthesis_agent_run_with_results():
    context = _build_context()
    role_results = [
        AgentResult.model_validate(json.loads(_valid_role_output(role="munger"))),
        AgentResult.model_validate(json.loads(_valid_role_output(role="industry"))),
        AgentResult.model_validate(json.loads(_valid_role_output(role="audit"))),
    ]

    async def synthesis_caller(_prompt: str) -> str:
        return _valid_synthesis_output()

    agent = SynthesisAgent(llm_caller=synthesis_caller)
    result = await agent.run_with_results(context, role_results)

    assert result.final_score == pytest.approx(7.4)
    assert result.investment_decision == "观察"
    assert agent.last_prompt is not None
    assert "Role snapshots JSON" in agent.last_prompt
    assert "Aggregation hints JSON" in agent.last_prompt
    assert '"munger"' in agent.last_prompt


@pytest.mark.asyncio
async def test_three_role_agents_run_with_same_context():
    context = _build_context()
    role_cases = [
        (MungerAgent, "munger", AgentRole.MUNGER),
        (IndustryAgent, "industry", AgentRole.INDUSTRY),
        (AuditAgent, "audit", AgentRole.AUDIT),
    ]

    for agent_cls, role_text, role_enum in role_cases:
        async def caller(_prompt: str, payload=_valid_role_output(role=role_text)) -> str:
            return payload

        agent = agent_cls(llm_caller=caller)
        result = await agent.run(context)
        assert result.role == role_enum
        assert result.insufficient_data is False
        assert len(result.evidence) >= 1


@pytest.mark.asyncio
async def test_synthesis_agent_marks_missing_role_in_prompt_hints():
    context = _build_context()
    role_results = [
        AgentResult.model_validate(json.loads(_valid_role_output(role="munger"))),
        AgentResult.model_validate(json.loads(_valid_role_output(role="industry"))),
    ]

    captured: list[str] = []

    async def synthesis_caller(prompt: str) -> str:
        captured.append(prompt)
        return _valid_synthesis_output()

    agent = SynthesisAgent(llm_caller=synthesis_caller)
    await agent.run_with_results(context, role_results)

    assert len(captured) == 1
    prompt = captured[0]
    assert "Aggregation hints JSON" in prompt
    assert '"missing_roles"' in prompt
    assert '"audit"' in prompt


@pytest.mark.asyncio
async def test_synthesis_agent_falls_back_when_llm_fails():
    context = _build_context()
    role_results = [
        AgentResult.model_validate(json.loads(_valid_role_output(role="munger"))),
        AgentResult.model_validate(json.loads(_valid_role_output(role="industry"))),
    ]

    async def failing_caller(_prompt: str) -> str:
        raise RuntimeError("provider unavailable")

    agent = SynthesisAgent(llm_caller=failing_caller)
    result = await agent.run_with_results(context, role_results)

    assert "降级模式" in result.company_profile
    assert "降级模式" in result.report_sections.intro
    assert "审计" in result.report_sections.synthesis


@pytest.mark.asyncio
async def test_synthesis_agent_falls_back_when_parse_retry_exhausted():
    context = _build_context()
    role_results = [
        AgentResult.model_validate(json.loads(_valid_role_output(role="munger"))),
        AgentResult.model_validate(json.loads(_valid_role_output(role="industry"))),
    ]
    caller = SequenceCaller(outputs=["invalid", "still invalid"])

    agent = SynthesisAgent(llm_caller=caller)
    result = await agent.run_with_results(context, role_results)

    assert len(caller.prompts) == 2
    assert "降级模式" in result.report_sections.intro
    assert result.final_score == pytest.approx(7.8)


@pytest.mark.asyncio
async def test_synthesis_agent_handles_empty_role_results_without_llm_call():
    context = _build_context()
    calls = {"count": 0}

    async def never_called(_prompt: str) -> str:
        calls["count"] += 1
        return _valid_synthesis_output()

    agent = SynthesisAgent(llm_caller=never_called)
    result = await agent.run_with_results(context, role_results=[])

    assert calls["count"] == 0
    assert result.insufficient_data is True
    assert result.investment_decision == "数据不足 - 观望"
