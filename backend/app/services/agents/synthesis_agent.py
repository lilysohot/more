from __future__ import annotations

import json
import re
from textwrap import dedent
from typing import Iterable, Sequence

from app.services.agents.base import AgentExecutionError, AgentParseError, BaseAgent
from app.services.agents.parser import StructuredOutputParseError, parse_model_response
from app.services.agents.schemas import AgentContext, AgentResult, AgentRole, ReportSections, SynthesisResult

_EXPECTED_ROLE_ORDER: tuple[AgentRole, ...] = (
    AgentRole.MUNGER,
    AgentRole.INDUSTRY,
    AgentRole.AUDIT,
)

_ROLE_LABEL: dict[AgentRole, str] = {
    AgentRole.MUNGER: "芒格视角",
    AgentRole.INDUSTRY: "产业视角",
    AgentRole.AUDIT: "审计视角",
}


def _role_label(role: AgentRole | str) -> str:
    if isinstance(role, str):
        return _ROLE_LABEL.get(AgentRole(role), role)
    return _ROLE_LABEL.get(role, role.value)


_CHINESE_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")


def _has_chinese_chars(value: str) -> bool:
    return bool(_CHINESE_CHAR_RE.search(value or ""))


def _is_chinese_preferred(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False

    if not _has_chinese_chars(text):
        return False

    latin_count = len(re.findall(r"[A-Za-z]", text))
    if latin_count == 0:
        return True

    chinese_count = len(_CHINESE_CHAR_RE.findall(text))
    return chinese_count * 2 >= latin_count


def _ensure_chinese_text(value: str, field_name: str) -> None:
    if not _is_chinese_preferred(value):
        raise ValueError(f"{field_name} must be Chinese text")


def _ensure_chinese_items(items: Iterable[str], field_name: str) -> None:
    for index, value in enumerate(items, 1):
        _ensure_chinese_text(f"{value}", f"{field_name}[{index}]")


def _validate_result_in_chinese(result: SynthesisResult) -> SynthesisResult:
    _ensure_chinese_text(result.company_profile, "company_profile")
    _ensure_chinese_text(result.investment_decision, "investment_decision")
    _ensure_chinese_items(result.consensus, "consensus")
    _ensure_chinese_items(result.core_reasons, "core_reasons")
    _ensure_chinese_items(result.major_risks, "major_risks")
    _ensure_chinese_text(result.report_sections.intro, "report_sections.intro")
    _ensure_chinese_text(result.report_sections.munger_view, "report_sections.munger_view")
    _ensure_chinese_text(result.report_sections.industry_view, "report_sections.industry_view")
    _ensure_chinese_text(result.report_sections.audit_view, "report_sections.audit_view")
    _ensure_chinese_text(result.report_sections.synthesis, "report_sections.synthesis")

    for index, disagreement in enumerate(result.disagreements, 1):
        _ensure_chinese_text(disagreement.topic, f"disagreements[{index}].topic")
        if disagreement.munger is not None:
            _ensure_chinese_text(disagreement.munger, f"disagreements[{index}].munger")
        if disagreement.industry is not None:
            _ensure_chinese_text(disagreement.industry, f"disagreements[{index}].industry")
        if disagreement.audit is not None:
            _ensure_chinese_text(disagreement.audit, f"disagreements[{index}].audit")

    return result


def _context_json(context: AgentContext) -> str:
    return json.dumps(context.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=2)


def _normalize_role(role: AgentRole | str) -> AgentRole:
    if isinstance(role, AgentRole):
        return role
    return AgentRole(str(role))


def _index_role_results(role_results: Sequence[AgentResult]) -> dict[AgentRole, AgentResult]:
    indexed: dict[AgentRole, AgentResult] = {}
    for result in role_results:
        indexed[_normalize_role(result.role)] = result
    return indexed


def _compact_role_result(result: AgentResult) -> dict[str, object]:
    return {
        "score": result.score,
        "summary": result.summary,
        "thesis": result.thesis[:5],
        "positives": result.positives[:5],
        "risks": result.risks[:5],
        "red_flags": result.red_flags[:5],
        "questions": result.questions[:5],
        "insufficient_data": result.insufficient_data,
        "evidence": [
            {
                "item": item.item,
                "source": item.source,
                "confidence": item.confidence,
            }
            for item in result.evidence[:5]
        ],
    }


def _build_role_snapshots(role_results: Sequence[AgentResult]) -> dict[str, dict[str, object]]:
    indexed = _index_role_results(role_results)
    snapshots: dict[str, dict[str, object]] = {}

    for role in _EXPECTED_ROLE_ORDER:
        role_key = role.value
        result = indexed.get(role)
        if result is None:
            snapshots[role_key] = {"status": "missing"}
            continue

        snapshots[role_key] = {
            "status": "available",
            **_compact_role_result(result),
        }

    return snapshots


def _mean_score(role_results: Sequence[AgentResult]) -> float:
    if not role_results:
        return 0.0
    return round(sum(item.score for item in role_results) / len(role_results), 2)


def _unique(items: Sequence[str], limit: int = 6) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def _ensure_chinese_or_fallback(items: Sequence[str], fallback_prefix: str, limit: int = 6) -> list[str]:
    chinese_items = [item for item in items if _is_chinese_preferred(item)]
    if chinese_items:
        return _unique(chinese_items, limit=limit)

    return [f"{fallback_prefix}（原始结果未检测到中文输出，已转为中文占位）"]


def _build_aggregation_hints(role_results: Sequence[AgentResult]) -> dict[str, object]:
    indexed = _index_role_results(role_results)
    available_roles = [role.value for role in _EXPECTED_ROLE_ORDER if role in indexed]
    missing_roles = [role.value for role in _EXPECTED_ROLE_ORDER if role not in indexed]
    insufficient_data_roles = [
        role.value for role in _EXPECTED_ROLE_ORDER if role in indexed and indexed[role].insufficient_data
    ]

    return {
        "expected_roles": [role.value for role in _EXPECTED_ROLE_ORDER],
        "available_roles": available_roles,
        "missing_roles": missing_roles,
        "insufficient_data_roles": insufficient_data_roles,
        "forced_insufficient_data": len(insufficient_data_roles) >= 2,
        "degraded_mode": len(missing_roles) > 0,
        "baseline_final_score": _mean_score(role_results),
    }


class SynthesisAgent(BaseAgent[SynthesisResult]):
    """Merge role-agent outputs into one structured synthesis result."""

    role = AgentRole.SYNTHESIS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._role_results: list[AgentResult] = []
        self._aggregation_hints: dict[str, object] = _build_aggregation_hints([])

    async def run_with_results(
        self,
        context: AgentContext,
        role_results: Sequence[AgentResult],
    ) -> SynthesisResult:
        self._role_results = list(role_results)
        self._aggregation_hints = _build_aggregation_hints(self._role_results)

        if not self._role_results:
            return self._build_fallback_result(context, reason="汇总阶段未获取到角色结果，已进入降级生成。")

        try:
            return await self.run(context)
        except AgentExecutionError as exc:
            return self._build_fallback_result(context, reason="汇总执行异常，已进入降级生成。")

    def build_prompt(self, context: AgentContext) -> str:
        context_payload = _context_json(context)
        role_payload = json.dumps(_build_role_snapshots(self._role_results), ensure_ascii=False, indent=2)
        hint_payload = json.dumps(self._aggregation_hints, ensure_ascii=False, indent=2)

        return dedent(
            f"""
            你是多 Agent 股票分析工作流中的综合汇总角色，任务是把角色输出合并为一个结构化综合结论。

            输入策略：
            - 只使用下方结构化角色快照和聚合提示。
            - 不要请求重建完整长文本叙事。
            - 必须保留角色之间的真实分歧，不要强行制造共识。

            输出契约：
            1) 只返回一个 JSON 对象。
            2) 不要返回 markdown、代码块或 JSON 之外的解释。
            3) JSON 字段与约束：
                - company_profile: 非空字符串
                - consensus: string[]
                - disagreements: object[]，字段包括 topic（必填）、munger?、industry?、audit?
                - final_score: [0, 10] 范围内的数字
                - investment_decision: 非空字符串
                - insufficient_data: boolean
                - core_reasons: string[]
                - major_risks: string[]
                - report_sections: object，包含 intro、munger_view、industry_view、audit_view、synthesis 字符串字段
             4) 所有面向报告展示的文本字段必须使用中文，不得出现英文说明；公司名、股票代码、ROE/PE/PB 等特殊标注可以保留原始写法。

            决策规则：
            - 如果 aggregation_hints.forced_insufficient_data 为 true，insufficient_data 必须为 true。
            - 如果 aggregation_hints.missing_roles 非空，必须在 report_sections.synthesis 中明确说明缺失视角。
            - 除非证据强烈支持调整，否则 final_score 应接近 aggregation_hints.baseline_final_score。
            - 输出必须为中文。

            Analysis context JSON:
            {context_payload}

            Role snapshots JSON:
            {role_payload}

            Aggregation hints JSON:
            {hint_payload}
            """
        ).strip()

    def parse_response(self, raw_text: str) -> SynthesisResult:
        try:
            result = parse_model_response(raw_text, SynthesisResult)
            return _validate_result_in_chinese(result)
        except StructuredOutputParseError as exc:
            raise AgentParseError(
                role=self.role,
                message=f"{self.role.value} parse failed: {exc}",
                raw_output=raw_text,
                original_exception=exc,
            ) from exc
        except ValueError as exc:
            raise AgentParseError(
                role=self.role,
                message=f"{self.role.value} parse failed: {exc}",
                raw_output=raw_text,
                original_exception=exc,
            ) from exc

    def build_repair_prompt(self, raw_output: str, parse_error: Exception) -> str:
        return (
            "上一次输出未通过 schema/format 或中文校验。"
            "只返回有效 JSON，不要添加额外说明。所有面向报告展示的叙述字段必须翻译为中文。\n"
            f"Role: {self.role.value}\n"
            f"Error: {parse_error}\n"
            "--- RAW OUTPUT START ---\n"
            f"{raw_output}\n"
            "--- RAW OUTPUT END ---"
        )

    def _build_fallback_result(self, context: AgentContext, reason: str) -> SynthesisResult:
        indexed = _index_role_results(self._role_results)
        available_roles = [role.value for role in _EXPECTED_ROLE_ORDER if role in indexed]
        missing_roles = [role.value for role in _EXPECTED_ROLE_ORDER if role not in indexed]
        insufficient_roles = [
            role.value for role in _EXPECTED_ROLE_ORDER if role in indexed and indexed[role].insufficient_data
        ]

        final_score = _mean_score(self._role_results)
        forced_insufficient_data = len(insufficient_roles) >= 2
        insufficient_data = forced_insufficient_data or len(available_roles) < 2

        core_reasons = _ensure_chinese_or_fallback(
            [item.summary for item in self._role_results] + [reason],
            fallback_prefix="结论依据",
            limit=8,
        )
        major_risks = _ensure_chinese_or_fallback(
            [risk for item in self._role_results for risk in item.risks]
            + [flag for item in self._role_results for flag in item.red_flags],
            fallback_prefix="主要风险",
            limit=8,
        )
        if not major_risks:
            major_risks = ["当前无足够验证证据，保守输出。"]

        consensus = _ensure_chinese_or_fallback(
            [point for item in self._role_results for point in item.positives]
            + [point for item in self._role_results for point in item.thesis],
            fallback_prefix="暂无可展示的中文共识",
            limit=8,
        )

        synthesis_notes: list[str] = []
        if missing_roles:
            missing_role_names = [
                _role_label(role)
                for role in missing_roles
            ]
            synthesis_notes.append(f"缺失角色视角：{', '.join(missing_role_names)}。")
        if insufficient_roles:
            insufficient_role_names = [
                _role_label(role)
                for role in insufficient_roles
            ]
            synthesis_notes.append(f"数据不足角色：{', '.join(insufficient_role_names)}。")
        synthesis_notes.append("由于汇总阶段进入降级模式，结论采取保守口径。")

        munger_view = _ensure_chinese_or_fallback(
            [indexed[AgentRole.MUNGER].summary] if AgentRole.MUNGER in indexed else [],
            fallback_prefix="芒格视角缺失",
            limit=1,
        )[0]
        industry_view = (
            _ensure_chinese_or_fallback(
                [indexed[AgentRole.INDUSTRY].summary],
                fallback_prefix="产业视角缺失",
                limit=1,
            )[0]
            if AgentRole.INDUSTRY in indexed
            else "产业视角缺失。"
        )
        audit_view = _ensure_chinese_or_fallback(
            [indexed[AgentRole.AUDIT].summary] if AgentRole.AUDIT in indexed else [],
            fallback_prefix="审计视角缺失",
            limit=1,
        )[0]

        if insufficient_data:
            investment_decision = "数据不足 - 观望"
        elif final_score >= 7.0:
            investment_decision = "持有/观察"
        elif final_score >= 5.0:
            investment_decision = "中性"
        else:
            investment_decision = "回避"

        return SynthesisResult(
            company_profile=f"{context.company_name} 的汇总报告采用降级模式生成。",
            consensus=consensus,
            disagreements=[],
            final_score=final_score,
            investment_decision=investment_decision,
            insufficient_data=insufficient_data,
            core_reasons=core_reasons,
            major_risks=major_risks,
            report_sections=ReportSections(
                intro=f"使用了汇总降级模式。{reason}",
                munger_view=munger_view,
                industry_view=industry_view,
                audit_view=audit_view,
                synthesis=" ".join(synthesis_notes),
            ),
        )
