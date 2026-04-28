from app.api.analyses import (
    _get_progress_message,
    _get_progress_percentage,
    _get_progress_stage,
)


def test_progress_stage_aliases_old_status_values():
    assert _get_progress_stage("generating_prompt") == "building_context"
    assert _get_progress_stage("calling_llm") == "running_munger_agent"
    assert _get_progress_stage("running_industry_agent") == "running_industry_agent"


def test_progress_percentage_uses_normalized_stage():
    assert _get_progress_percentage("generating_prompt") == 35
    assert _get_progress_percentage("calling_llm") == 50


def test_progress_message_uses_normalized_stage():
    assert _get_progress_message("generating_prompt") == "正在构建分析上下文..."
    assert _get_progress_message("calling_llm") == "正在执行芒格角色分析..."


def test_unknown_progress_status_has_safe_fallback():
    assert _get_progress_percentage("unknown_stage") == 0
    assert _get_progress_message("unknown_stage") == "处理中..."
