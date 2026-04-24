from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar

from pydantic import BaseModel

from app.services.agents.schemas import AgentContext, AgentRole

TResult = TypeVar("TResult", bound=BaseModel)
LLMCaller = Callable[[str], Awaitable[str]]


class AgentExecutionError(RuntimeError):
    """Base exception for all agent execution errors."""


class AgentConfigurationError(AgentExecutionError):
    """Raised when BaseAgent cannot resolve a valid LLM invocation path."""


class AgentLLMError(AgentExecutionError):
    """Raised when LLM invocation fails."""

    def __init__(self, role: AgentRole, message: str, original_exception: Optional[Exception] = None):
        self.role = role
        self.original_exception = original_exception
        super().__init__(message)


class AgentParseError(AgentExecutionError):
    """Raised when raw output cannot be parsed into structured schema."""

    def __init__(
        self,
        role: AgentRole,
        message: str,
        raw_output: str,
        original_exception: Optional[Exception] = None,
    ):
        self.role = role
        self.raw_output = raw_output
        self.original_exception = original_exception
        super().__init__(message)


class AgentParseRetryExhaustedError(AgentParseError):
    """Raised when parse-repair retry still fails."""

    def __init__(
        self,
        role: AgentRole,
        raw_output: str,
        repaired_output: str,
        first_error: Exception,
        retry_error: Exception,
    ):
        self.repaired_output = repaired_output
        self.first_error = first_error
        self.retry_error = retry_error
        message = f"{role.value} parse failed after one repair retry"
        super().__init__(role=role, message=message, raw_output=raw_output, original_exception=retry_error)


class BaseAgent(ABC, Generic[TResult]):
    """Common execution framework shared by role/synthesis agents."""

    role: AgentRole
    prompt_version: str = "v1"
    schema_version: str = "v1"
    parse_retry_limit: int = 1

    def __init__(
        self,
        llm_caller: Optional[LLMCaller] = None,
        llm_service: Optional[Any] = None,
        llm_config: Optional[dict[str, Any]] = None,
    ):
        if llm_caller and (llm_service or llm_config):
            raise AgentConfigurationError("Provide either llm_caller or llm_service/llm_config, not both")

        self._llm_caller = llm_caller

        if llm_service is not None:
            self._llm_service = llm_service
        elif llm_config is not None:
            from app.services.llm_service import LLMService

            self._llm_service = LLMService(llm_config)
        else:
            self._llm_service = None

        self.last_prompt: Optional[str] = None
        self.last_raw_output: Optional[str] = None
        self.last_retry_raw_output: Optional[str] = None
        self.last_parse_error: Optional[str] = None

    async def run(self, context: AgentContext) -> TResult:
        """Standard execution pipeline: build prompt -> call LLM -> parse -> one repair retry."""
        prompt = self.build_prompt(context)
        self.last_prompt = prompt

        raw_output = await self._invoke_llm(prompt)
        self.last_raw_output = raw_output
        self.last_retry_raw_output = None
        self.last_parse_error = None

        try:
            return self.parse_response(raw_output)
        except Exception as first_error:
            parse_error = self._to_parse_error(first_error, raw_output)
            self.last_parse_error = str(parse_error)

            if self.parse_retry_limit < 1:
                raise parse_error

            repair_prompt = self.build_repair_prompt(raw_output, parse_error)
            repaired_output = await self._invoke_llm(repair_prompt)
            self.last_retry_raw_output = repaired_output

            try:
                return self.parse_response(repaired_output)
            except Exception as retry_error:
                exhausted = AgentParseRetryExhaustedError(
                    role=self.role,
                    raw_output=raw_output,
                    repaired_output=repaired_output,
                    first_error=first_error,
                    retry_error=retry_error,
                )
                self.last_parse_error = str(exhausted)
                raise exhausted from retry_error

    @abstractmethod
    def build_prompt(self, context: AgentContext) -> str:
        """Build role-specific prompt from shared AgentContext."""

    @abstractmethod
    def parse_response(self, raw_text: str) -> TResult:
        """Parse and validate LLM raw output into structured schema."""

    def build_repair_prompt(self, raw_output: str, parse_error: Exception) -> str:
        """Build default repair prompt for one-shot parse retry."""
        return (
            "Your previous output failed JSON parsing or schema validation. "
            "Return only valid JSON and no extra text.\n"
            f"Role: {self.role.value}\n"
            f"Error: {parse_error}\n"
            "--- RAW OUTPUT START ---\n"
            f"{raw_output}\n"
            "--- RAW OUTPUT END ---"
        )

    def get_last_run_trace(self) -> dict[str, Optional[str]]:
        """Return raw output and parse error snapshot for observability/debugging."""
        return {
            "prompt": self.last_prompt,
            "raw_output": self.last_raw_output,
            "retry_raw_output": self.last_retry_raw_output,
            "parse_error": self.last_parse_error,
        }

    async def _invoke_llm(self, prompt: str) -> str:
        if self._llm_caller is not None:
            return await self._invoke_llm_with_callable(prompt)

        if self._llm_service is None:
            raise AgentConfigurationError("No llm_caller/llm_service provided for BaseAgent")

        provider = str(getattr(self._llm_service, "provider", "dashscope") or "dashscope").lower()
        method_map = {
            "dashscope": "_call_dashscope",
            "openai": "_call_openai",
            "claude": "_call_claude",
        }
        method_name = method_map.get(provider, "_call_dashscope")
        method = getattr(self._llm_service, method_name, None)

        if method is None:
            raise AgentConfigurationError(f"Unsupported provider method for provider: {provider}")

        try:
            raw_text = await method(prompt)
        except Exception as exc:
            raise AgentLLMError(self.role, f"{self.role.value} LLM call failed", original_exception=exc) from exc

        if not isinstance(raw_text, str):
            raise AgentLLMError(self.role, f"{self.role.value} LLM response must be string")

        return raw_text

    async def _invoke_llm_with_callable(self, prompt: str) -> str:
        caller = self._llm_caller
        if caller is None:
            raise AgentConfigurationError("No llm_caller provided")

        try:
            raw_text = await caller(prompt)
        except Exception as exc:
            raise AgentLLMError(self.role, f"{self.role.value} LLM callable failed", original_exception=exc) from exc

        if not isinstance(raw_text, str):
            raise AgentLLMError(self.role, f"{self.role.value} LLM callable must return string")

        return raw_text

    def _to_parse_error(self, exc: Exception, raw_output: str) -> AgentParseError:
        if isinstance(exc, AgentParseError):
            return exc

        return AgentParseError(
            role=self.role,
            message=f"{self.role.value} parse failed: {exc}",
            raw_output=raw_output,
            original_exception=exc,
        )
