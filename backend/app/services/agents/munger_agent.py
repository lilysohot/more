from __future__ import annotations

import json
from textwrap import dedent

from app.services.agents.base import AgentParseError, BaseAgent
from app.services.agents.parser import StructuredOutputParseError, parse_model_response
from app.services.agents.schemas import AgentContext, AgentResult, AgentRole


def _context_json(context: AgentContext) -> str:
    return json.dumps(context.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=2)


class MungerAgent(BaseAgent[AgentResult]):
    """Role agent focused on business quality and long-term compounding logic."""

    role = AgentRole.MUNGER

    def build_prompt(self, context: AgentContext) -> str:
        payload = _context_json(context)
        return dedent(
            f"""
            You are the `munger` role in a multi-agent investment workflow.

            Focus areas (must prioritize):
            1) Business essence and economic model
            2) Moat durability and erosion risk
            3) Management quality and integrity signals
            4) Capital allocation discipline
            5) Margin of safety from a long-term perspective

            Boundary rules:
            - Keep the analysis centered on business quality and compounding logic.
            - Do not turn this role into a full industry cycle model or forensic audit report.
            - If key data is missing, state uncertainty explicitly.

            Output contract:
            1) Return exactly one JSON object.
            2) Do not return markdown, code fences, or explanations.
            3) JSON fields and constraints:
               - role: must be "munger"
               - summary: non-empty string
               - score: number in [0, 10]
               - thesis: string[]
               - positives: string[]
               - risks: string[]
               - evidence: object[] with fields:
                 * item: non-empty string
                 * source: non-empty string
                 * source_type: optional string
                 * source_date: optional string
                 * excerpt: optional string
                 * confidence: number in [0, 1]
               - red_flags: string[]
               - questions: string[]
               - insufficient_data: boolean
            4) Rules:
               - if insufficient_data == false, evidence must contain at least one item
               - if insufficient_data == true, questions must contain at least one item
               - include role-specific red_flags and questions instead of generic placeholders

            Analysis context JSON:
            {payload}
            """
        ).strip()

    def parse_response(self, raw_text: str) -> AgentResult:
        try:
            result = parse_model_response(raw_text, AgentResult)
        except StructuredOutputParseError as exc:
            raise AgentParseError(
                role=self.role,
                message=f"{self.role.value} parse failed: {exc}",
                raw_output=raw_text,
                original_exception=exc,
            ) from exc

        if result.role != self.role:
            raise AgentParseError(
                role=self.role,
                message="munger parse failed: role must equal munger",
                raw_output=raw_text,
            )

        return result
