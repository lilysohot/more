"""
分析模块 API 路由

提供公司分析相关的 REST API 接口，包括：
- 创建分析任务
- 获取分析列表
- 获取分析详情
- 获取分析进度
- 获取分析报告
- 删除分析记录
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, Analysis, Report, AgentRun
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisDetailResponse,
    AnalysisProgress,
    ReportResponse,
    AnalysisListResponse,
)
from app.services.analysis import AnalysisService, get_active_tasks
from app.services.structured_report import build_report_response

router = APIRouter()


@router.get("/active-tasks")
async def list_active_tasks(
    current_user: User = Depends(get_current_user),
):
    """
    获取当前活跃的分析任务列表
    
    参数:
        current_user: 当前登录用户
    
    返回:
        活跃任务列表，包含任务ID、公司名称、当前步骤、开始时间等
    """
    all_tasks = get_active_tasks()
    user_tasks = {
        task_id: task_info
        for task_id, task_info in all_tasks.items()
        if task_info["user_id"] == str(current_user.id)
    }
    return {
        "total": len(user_tasks),
        "tasks": user_tasks,
    }


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建新的分析任务
    
    参数:
        data: 分析创建参数，包含公司名称、股票代码、是否包含图表、API配置ID
        background_tasks: FastAPI 后台任务管理器
        db: 数据库会话
        current_user: 当前登录用户
    
    返回:
        AnalysisResponse: 创建的分析记录
    
    说明:
        - 分析任务在后台异步执行
        - 用户可选择使用自己的 API 配置或系统默认模型
    """
    service = AnalysisService()
    try:
        resolved_target = await service.resolve_analysis_target(
            company_name=data.company_name,
            stock_code=data.stock_code,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    analysis = Analysis(
        user_id=current_user.id,
        company_name=resolved_target["company_name"],
        stock_code=resolved_target["stock_code"],
        status="pending",
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    background_tasks.add_task(
        service.run_analysis,
        analysis_id=str(analysis.id),
        user_id=str(current_user.id),
        company_name=resolved_target["company_name"],
        stock_code=resolved_target["stock_code"],
        include_charts=data.include_charts,
        api_config_id=str(data.api_config_id) if data.api_config_id else None,
    )

    return analysis


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的分析记录列表
    
    参数:
        skip: 分页偏移量
        limit: 每页数量限制
        db: 数据库会话
        current_user: 当前登录用户
    
    返回:
        AnalysisListResponse: 分析记录列表及总数
    """
    result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    analyses = result.scalars().all()

    count_result = await db.execute(
        select(Analysis).where(Analysis.user_id == current_user.id)
    )
    total = len(count_result.scalars().all())

    return {"items": analyses, "total": total}


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取单个分析记录详情
    
    参数:
        analysis_id: 分析记录ID
        db: 数据库会话
        current_user: 当前登录用户
    
    返回:
        AnalysisDetailResponse: 分析记录详情
    
    异常:
        404: 分析记录不存在
    """
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在",
        )

    return analysis


@router.get("/{analysis_id}/progress", response_model=AnalysisProgress)
async def get_analysis_progress(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取分析任务的进度状态
    
    参数:
        analysis_id: 分析记录ID
        db: 数据库会话
        current_user: 当前登录用户
    
    返回:
        AnalysisProgress: 包含状态、阶段、进度百分比、进度消息
    
    说明:
        进度状态包括: pending, collecting_data, calculating_ratios,
        building_context, running_munger_agent, running_industry_agent,
        running_audit_agent, running_synthesis_agent,
        generating_report, saving_report, completed, failed
    """
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在",
        )

    return {
        "analysis_id": analysis.id,
        "status": analysis.status,
        "progress_stage": _get_progress_stage(analysis.status),
        "progress": _get_progress_percentage(analysis.status),
        "message": _get_progress_message(analysis.status),
    }


@router.get("/{analysis_id}/report", response_model=ReportResponse)
async def get_analysis_report(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取分析报告内容
    
    参数:
        analysis_id: 分析记录ID
        db: 数据库会话
        current_user: 当前登录用户
    
    返回:
        ReportResponse: 包含 Markdown 和 HTML 格式的报告内容
    
    异常:
        404: 分析记录或报告不存在
        400: 分析尚未完成
    """
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在",
        )

    if analysis.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"分析尚未完成，当前状态：{analysis.status}",
        )

    report_result = await db.execute(
        select(Report).where(Report.analysis_id == analysis_id)
    )
    report = report_result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在",
        )

    agent_runs_result = await db.execute(
        select(AgentRun)
        .where(AgentRun.analysis_id == analysis_id)
        .order_by(AgentRun.created_at.asc())
    )
    agent_runs = list(agent_runs_result.scalars().all())

    return build_report_response(
        analysis=analysis,
        report=report,
        agent_runs=agent_runs,
    )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除分析记录及其关联的报告
    
    参数:
        analysis_id: 分析记录ID
        db: 数据库会话
        current_user: 当前登录用户
    
    异常:
        404: 分析记录不存在
    """
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析记录不存在",
        )

    await db.delete(analysis)
    await db.commit()


def _get_progress_percentage(status: str) -> int:
    """
    根据分析状态返回进度百分比
    
    参数:
        status: 分析状态字符串
    
    返回:
        int: 0-100 的进度百分比
    """
    progress_map = {
        "pending": 0,
        "collecting_data": 10,
        "calculating_ratios": 20,
        "building_context": 35,
        "running_munger_agent": 50,
        "running_industry_agent": 60,
        "running_audit_agent": 70,
        "running_synthesis_agent": 80,
        "generating_report": 90,
        "saving_report": 95,
        "completed": 100,
        "failed": 0,
    }
    progress_stage = _get_progress_stage(status)
    return progress_map.get(progress_stage, 0)


def _get_progress_message(status: str) -> str:
    """
    根据分析状态返回进度提示消息
    
    参数:
        status: 分析状态字符串
    
    返回:
        str: 用户友好的进度消息
    """
    message_map = {
        "pending": "准备开始分析...",
        "collecting_data": "正在采集公司数据...",
        "calculating_ratios": "正在计算财务比率...",
        "building_context": "正在构建分析上下文...",
        "running_munger_agent": "正在执行芒格角色分析...",
        "running_industry_agent": "正在执行产业角色分析...",
        "running_audit_agent": "正在执行审计角色分析...",
        "running_synthesis_agent": "正在汇总多角色分析结果...",
        "generating_report": "正在生成分析报告...",
        "saving_report": "正在保存分析报告...",
        "completed": "分析完成！",
        "failed": "分析失败，请重试",
    }
    progress_stage = _get_progress_stage(status)
    return message_map.get(progress_stage, "处理中...")


def _get_progress_stage(status: str) -> str:
    """
    兼容旧状态值并返回标准化的阶段名称。

    参数:
        status: 分析状态字符串

    返回:
        str: 标准化后的进度阶段
    """
    alias_map = {
        "generating_prompt": "building_context",
        "calling_llm": "running_munger_agent",
    }
    return alias_map.get(status, status)
