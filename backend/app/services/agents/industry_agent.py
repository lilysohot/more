from __future__ import annotations

import json
from textwrap import dedent

from app.services.agents.base import AgentParseError, BaseAgent
from app.services.agents.language import validate_agent_result_in_chinese
from app.services.agents.parser import StructuredOutputParseError, parse_model_response
from app.services.agents.schemas import AgentContext, AgentResult, AgentRole


def _context_json(context: AgentContext) -> str:
    return json.dumps(context.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=2)


class IndustryAgent(BaseAgent[AgentResult]):
    """Role agent focused on industry structure and positioning."""

    role = AgentRole.INDUSTRY

    def build_prompt(self, context: AgentContext) -> str:
        payload = _context_json(context)
        return dedent(
            """
            你是多 Agent 投资分析工作流中的 `industry` 角色。

            关注重点（必须优先）：
            1) 价值链位置与议价能力
            2) 行业周期阶段与敏感性
            3) 供需结构与瓶颈约束
            4) 成本曲线位置与经营杠杆
            5) 竞争格局与替代威胁

            边界规则：
            - 分析必须围绕外部产业动态展开。
            - 不要把本角色扩展成完整管理层画像或法务会计审查。
            - 如关键产业证据缺失，必须明确说明不确定性。

            输出契约：
            1) 只返回一个 JSON 对象。
            2) 不要返回 markdown、代码块或 JSON 之外的解释。
            3) JSON 字段与约束：
               - role: 必须是 "industry"
               - summary: 非空字符串
               - score: [0, 10] 范围内的数字
               - thesis: string[]
               - positives: string[]
               - risks: string[]
               - evidence: object[]，字段包括：
                 * item: 非空字符串
                 * source: 非空字符串
                 * source_type: 可选字符串
                 * source_date: 可选字符串
                 * excerpt: 可选字符串
                 * confidence: [0, 1] 范围内的数字
               - red_flags: string[]
               - questions: string[]
               - insufficient_data: boolean
            4) 规则：
               - 如果 insufficient_data == false，evidence 至少包含一项
               - 如果 insufficient_data == true，questions 至少包含一项
               - red_flags 和 questions 必须体现本角色视角，不要使用泛泛占位语
            5) 所有面向报告展示的文本字段必须使用中文；role、source/source_type/source_date、公司名、股票代码、ROE/PE/PB 等特殊标注可以保留原始写法。

            Analysis context JSON:
            {payload}
            """
        ).format(payload=payload).strip()

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
                message="industry parse failed: role must equal industry",
                raw_output=raw_text,
            )

        try:
            return validate_agent_result_in_chinese(result)
        except ValueError as exc:
            raise AgentParseError(
                role=self.role,
                message=f"{self.role.value} parse failed: {exc}",
                raw_output=raw_text,
                original_exception=exc,
            ) from exc
