from __future__ import annotations

import re
from collections.abc import Iterable

from app.services.agents.schemas import AgentResult

_CHINESE_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")


def is_chinese_preferred(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False

    chinese_count = len(_CHINESE_CHAR_RE.findall(text))
    if chinese_count == 0:
        return False

    latin_count = len(re.findall(r"[A-Za-z]", text))
    if latin_count == 0:
        return True

    # Allow common report annotations such as ROE, PE, PB, ESG, API, and source labels.
    return chinese_count * 2 >= latin_count


def ensure_chinese_text(value: str, field_name: str) -> None:
    if not is_chinese_preferred(value):
        raise ValueError(f"{field_name} must be Chinese text")


def ensure_chinese_items(items: Iterable[str], field_name: str) -> None:
    for index, value in enumerate(items, 1):
        ensure_chinese_text(f"{value}", f"{field_name}[{index}]")


def validate_agent_result_in_chinese(result: AgentResult) -> AgentResult:
    ensure_chinese_text(result.summary, "summary")
    ensure_chinese_items(result.thesis, "thesis")
    ensure_chinese_items(result.positives, "positives")
    ensure_chinese_items(result.risks, "risks")
    ensure_chinese_items(result.red_flags, "red_flags")
    ensure_chinese_items(result.questions, "questions")

    for index, item in enumerate(result.evidence, 1):
        ensure_chinese_text(item.item, f"evidence[{index}].item")
        if item.excerpt:
            ensure_chinese_text(item.excerpt, f"evidence[{index}].excerpt")

    return result
