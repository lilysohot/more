import pytest

from app.services.llm_service import LLMService


class DummyLLMService(LLMService):
    def __init__(self, config: dict):
        super().__init__(config)
        self.calls: list[str] = []
        self.last_prompt: str | None = None

    async def _call_dashscope(self, prompt: str) -> str:
        self.calls.append("dashscope")
        self.last_prompt = prompt
        return "dashscope-ok"

    async def _call_openai(self, prompt: str) -> str:
        self.calls.append("openai")
        self.last_prompt = prompt
        return "openai-ok"

    async def _call_claude(self, prompt: str) -> str:
        self.calls.append("claude")
        self.last_prompt = prompt
        return "claude-ok"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider, expected_call, expected_result",
    [
        ("dashscope", "dashscope", "dashscope-ok"),
        ("openai", "openai", "openai-ok"),
        ("claude", "claude", "claude-ok"),
        ("unsupported", "dashscope", "dashscope-ok"),
    ],
)
async def test_generate_routes_to_expected_provider(provider: str, expected_call: str, expected_result: str):
    service = DummyLLMService({"provider": provider, "api_key": "dummy"})

    result = await service.generate("Return valid JSON")

    assert result == expected_result
    assert service.calls == [expected_call]
    assert service.last_prompt == "Return valid JSON"


@pytest.mark.asyncio
async def test_generate_rejects_empty_prompt():
    service = DummyLLMService({"provider": "openai", "api_key": "dummy"})

    with pytest.raises(ValueError):
        await service.generate("   ")

    assert service.calls == []


@pytest.mark.asyncio
async def test_analyze_keeps_legacy_path_for_backward_compatibility():
    service = DummyLLMService({"provider": "openai", "api_key": "dummy"})
    company_data = {
        "company_name": "Test Holdings",
        "stock_code": "600000",
        "industry": "Utilities",
        "exchange": "SSE",
    }
    financial_ratios = {
        "gross_margin": 12.3,
        "net_margin": 6.7,
    }

    result = await service.analyze(company_data, financial_ratios)

    assert result == "openai-ok"
    assert service.calls == ["openai"]
    assert service.last_prompt is not None
    assert "Test Holdings" in service.last_prompt
    assert "三维深度辩论" in service.last_prompt
