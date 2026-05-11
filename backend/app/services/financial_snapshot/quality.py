"""Quality evaluation rules for normalized financial snapshots."""

from __future__ import annotations

import math
from typing import Any

from app.services.financial_snapshot.constants import (
    CORE_SNAPSHOT_FIELDS,
    DEFAULT_REQUIRED_TRIO_FIELDS,
    OUTPUT_FIELDS,
    QUALITY_TRACKED_FIELDS,
    VALUATION_ONLY_FIELDS,
)
from app.services.financial_snapshot.types import CompanyFinancialSnapshot


def evaluate_snapshot_quality(snapshot: CompanyFinancialSnapshot | dict[str, Any]) -> dict[str, Any]:
    """Assess whether a snapshot is complete enough for formal analysis."""

    missing_fields = _detect_missing_fields(snapshot)
    missing_core_fields = [field for field in CORE_SNAPSHOT_FIELDS if field in missing_fields]
    missing_ratio = round(len(missing_core_fields) / len(CORE_SNAPSHOT_FIELDS), 4)

    trio_missing = all(field in missing_fields for field in DEFAULT_REQUIRED_TRIO_FIELDS)
    insufficient_data = trio_missing or missing_ratio > 0.4

    return {
        "missing_fields": missing_fields,
        "missing_core_fields": missing_core_fields,
        "missing_ratio": missing_ratio,
        "insufficient_data": insufficient_data,
        "quality_note": _build_quality_note(
            missing_fields=missing_fields,
            missing_core_fields=missing_core_fields,
            missing_ratio=missing_ratio,
            insufficient_data=insufficient_data,
            data_source=str(snapshot.get("data_source") or "unknown"),
        ),
    }


def _detect_missing_fields(snapshot: CompanyFinancialSnapshot | dict[str, Any]) -> list[str]:
    explicit_missing = snapshot.get("missing_fields") or []
    if explicit_missing:
        ordered = []
        seen = set()
        for field in explicit_missing:
            name = str(field)
            if name in QUALITY_TRACKED_FIELDS and name not in seen:
                seen.add(name)
                ordered.append(name)
        if ordered:
            return ordered

    return [field for field in QUALITY_TRACKED_FIELDS if _is_missing(snapshot.get(field))]


def _build_quality_note(
    *,
    missing_fields: list[str],
    missing_core_fields: list[str],
    missing_ratio: float,
    insufficient_data: bool,
    data_source: str,
) -> str:
    if not missing_fields:
        return f"数据源 {data_source} 的核心字段与估值字段完整，可进入正式分析。"

    valuation_missing = [field for field in VALUATION_ONLY_FIELDS if field in missing_fields]
    if insufficient_data:
        visible_core = ", ".join(missing_core_fields[:6]) or "无"
        return (
            f"数据源 {data_source} 的核心财务字段缺失率为 {missing_ratio:.0%}，"
            f"当前缺失核心字段：{visible_core}，暂不建议进入正式分析。"
        )

    if valuation_missing and len(valuation_missing) == len(missing_fields):
        visible_valuation = ", ".join(valuation_missing)
        return (
            f"数据源 {data_source} 的核心财务字段可用，但估值字段缺失：{visible_valuation}。"
            "可以继续分析，但需降低估值结论置信度。"
        )

    visible_missing = ", ".join(missing_fields[:8])
    suffix = "..." if len(missing_fields) > 8 else ""
    return (
        f"数据源 {data_source} 存在字段缺失：{visible_missing}{suffix}。"
        "可以继续分析，但报告中需要明确说明缺失范围。"
    )


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    try:
        return bool(value != value)
    except Exception:
        return False
