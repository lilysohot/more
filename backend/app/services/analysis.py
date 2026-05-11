"""
分析服务模块

协调整个分析流程的执行，包括：
1. 数据采集
2. 财务比率计算
3. 多 Agent 编排调用
4. 报告生成

该服务在后台异步执行，通过数据库状态更新进度。
"""

import logging
import re
from datetime import datetime
from html import escape
from sqlalchemy import select
from uuid import UUID

from app.database import AsyncSessionLocal
from app.models.user import Analysis, Report, APIConfig, AgentRun, AnalysisEvent
from app.services.agents import AgentContext, AgentOrchestrator, AgentRole, AgentRunStatus, ProgressStage
from app.services.agents.orchestrator import OrchestrationResult
from app.services.data_collector import DataCollector
from app.services.financial_snapshot import FinancialSnapshotCollector, evaluate_snapshot_quality
from app.services.report_generator import ReportGenerator
from app.services.structured_report import build_structured_report_payload
from app.utils.encryption import decrypt_api_key
from app.core.config import settings
from skills import get_tushare_skill

logger = logging.getLogger(__name__)

_STOCK_IDENTIFIER_RE = re.compile(r"^(\d{6}|[A-Za-z]{1,5})$")

# Redis key prefix for active tasks
_ACTIVE_TASKS_KEY = "active_tasks"

# Try to create Redis client, fallback to None if not available
_redis_client = None
try:
    import redis
    _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    # Test connection
    _redis_client.ping()
    logger.info("Redis connected for active tasks tracking")
except Exception as e:
    logger.warning(f"Redis not available for active tasks tracking: {e}. Using in-memory fallback.")
    _redis_client = None

# In-memory fallback when Redis is not available
_active_tasks_memory: dict[str, dict] = {}


def _get_redis_client():
    """Get Redis client, reconnecting if necessary"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


def get_active_tasks() -> dict[str, dict]:
    """
    获取当前活跃的任务列表
    
    使用 Redis 存储以支持多进程/多 worker 环境。
    如果 Redis 不可用，则回退到内存存储（仅适用于单进程环境）。
    """
    redis_client = _get_redis_client()
    
    if redis_client is not None:
        try:
            tasks_data = redis_client.hgetall(_ACTIVE_TASKS_KEY)
            result = {}
            for task_id, task_json in tasks_data.items():
                import json
                result[task_id] = json.loads(task_json)
            return result
        except Exception as e:
            logger.warning(f"Failed to get tasks from Redis: {e}")
    
    # Fallback to memory
    return _active_tasks_memory.copy()


def _add_active_task(task_id: str, task_info: dict):
    """添加活跃任务到存储"""
    import json
    redis_client = _get_redis_client()
    
    if redis_client is not None:
        try:
            redis_client.hset(_ACTIVE_TASKS_KEY, task_id, json.dumps(task_info))
            return
        except Exception as e:
            logger.warning(f"Failed to add task to Redis: {e}")
    
    # Fallback to memory
    _active_tasks_memory[task_id] = task_info


def _remove_active_task(task_id: str):
    """从存储中移除任务"""
    redis_client = _get_redis_client()
    
    if redis_client is not None:
        try:
            redis_client.hdel(_ACTIVE_TASKS_KEY, task_id)
            return
        except Exception as e:
            logger.warning(f"Failed to remove task from Redis: {e}")
    
    # Fallback to memory
    if task_id in _active_tasks_memory:
        del _active_tasks_memory[task_id]


def _update_active_task(task_id: str, task_info: dict):
    """更新任务信息"""
    import json
    redis_client = _get_redis_client()
    
    if redis_client is not None:
        try:
            redis_client.hset(_ACTIVE_TASKS_KEY, task_id, json.dumps(task_info))
            return
        except Exception as e:
            logger.warning(f"Failed to update task in Redis: {e}")
    
    # Fallback to memory
    _active_tasks_memory[task_id] = task_info


class AnalysisService:
    """
    分析服务类
    
    负责协调整个分析流程的执行，包括数据采集、LLM调用和报告生成。
    
    使用示例:
        service = AnalysisService()
        await service.run_analysis(
            analysis_id="xxx",
            user_id="xxx",
            company_name="特变电工",
            stock_code="600089"
        )
    """
    
    def __init__(self, *, snapshot_collector_factory=None):
        """
        初始化分析服务
        """
        self._snapshot_collector_factory = snapshot_collector_factory or FinancialSnapshotCollector

    @staticmethod
    def _looks_like_stock_identifier(value: str | None) -> bool:
        return bool(value and _STOCK_IDENTIFIER_RE.fullmatch(str(value).strip()))

    @staticmethod
    def _normalize_resolved_target(resolved: dict | None, *, data_source: str) -> dict | None:
        if not isinstance(resolved, dict):
            return None

        company_name = str(resolved.get("company_name") or resolved.get("name") or "").strip()
        stock_code = str(resolved.get("stock_code") or "").strip().upper()
        if not company_name or not stock_code or company_name == stock_code:
            return None

        return {
            "company_name": company_name,
            "stock_code": stock_code,
            "exchange": resolved.get("exchange"),
            "industry": resolved.get("industry"),
            "data_source": data_source,
        }

    async def resolve_analysis_target(self, *, company_name: str, stock_code: str | None = None) -> dict:
        raw_company_name = (company_name or "").strip()
        raw_stock_code = (stock_code or "").strip().upper() or None

        if not raw_company_name and not raw_stock_code:
            raise ValueError("请输入公司名称或股票代码")

        if raw_stock_code is None and self._looks_like_stock_identifier(raw_company_name):
            raw_stock_code = raw_company_name.upper()

        company_name_hint = raw_company_name if raw_company_name and raw_company_name != raw_stock_code else None
        tushare_token = settings.TUSHARE_TOKEN or None
        collector = DataCollector()

        if raw_stock_code:
            eastmoney_by_code = await collector.resolve_stock(stock_code=raw_stock_code)
            normalized = self._normalize_resolved_target(eastmoney_by_code, data_source="eastmoney")
            if normalized is not None:
                return normalized

        if tushare_token:
            try:
                skill = await get_tushare_skill(token=tushare_token)
                tushare_result = await skill.resolve_stock(stock_code=raw_stock_code, company_name=company_name_hint)
                normalized = self._normalize_resolved_target(tushare_result, data_source="tushare")
                if normalized is not None:
                    return normalized
            except Exception as e:
                logger.warning(f"Tushare resolve failed for {raw_company_name} ({raw_stock_code}): {e}")

        eastmoney_result = await collector.resolve_stock(company_name=company_name_hint or raw_company_name)
        normalized = self._normalize_resolved_target(eastmoney_result, data_source="eastmoney")
        if normalized is not None:
            return normalized

        raise ValueError("无法识别输入内容，请输入正确的公司名称或股票代码")

    async def run_analysis(
        self,
        analysis_id: str,
        user_id: str,
        company_name: str,
        stock_code: str = None,
        include_charts: bool = True,
        api_config_id: str = None,
    ):
        """
        执行完整的分析流程
        
        该方法按顺序执行以下步骤：
        1. 采集公司数据（数据采集服务）
        2. 计算财务比率
        3. 构建 AgentContext
        4. 调用 AgentOrchestrator 执行多 Agent 分析
        5. 生成 Markdown 和 HTML 报告
        6. 保存报告到数据库
        
        参数:
            analysis_id: 分析记录ID
            user_id: 用户ID
            company_name: 公司名称
            stock_code: 股票代码（可选）
            include_charts: 是否包含图表
            api_config_id: 用户自定义的 API 配置ID
        
        说明:
            - 任何步骤失败都会将状态更新为 "failed"
            - 每个步骤都会更新数据库中的分析状态
        """
        import time
        from datetime import datetime

        start_time = time.time()
        task_info = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "company_name": company_name,
            "stock_code": stock_code,
            "started_at": datetime.utcnow().isoformat(),
            "current_step": "pending",
        }
        _add_active_task(analysis_id, task_info)

        try:
            logger.info(f"[Task {analysis_id}] Starting analysis for company: {company_name}")
            await self._persist_task_event(
                analysis_id,
                stage="pending",
                level="info",
                event_type="task_started",
                message=f"开始分析任务：{company_name}",
                payload={
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "include_charts": include_charts,
                    "api_config_id": api_config_id,
                },
            )
            logger.info(f"[Task {analysis_id}] Step 1/6: Collecting company data")
            task_info["current_step"] = "collecting_data"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "collecting_data")
            await self._persist_task_event(
                analysis_id,
                stage="collecting_data",
                level="info",
                event_type="stage_started",
                message="开始采集公司数据",
                payload={"company_name": company_name, "stock_code": stock_code},
            )
            await self._persist_task_event(
                analysis_id,
                stage="collecting_data",
                level="info",
                event_type="provider_collection_started",
                message="开始调用财务快照采集器",
                payload={"company_name": company_name, "stock_code": stock_code},
            )
            try:
                company_data = await self._collect_company_data(company_name=company_name, stock_code=stock_code)
            except Exception as exc:
                await self._persist_task_event(
                    analysis_id,
                    stage="collecting_data",
                    level="error",
                    event_type="provider_collection_failed",
                    message=str(exc) or "财务快照采集失败",
                    payload={"error_type": type(exc).__name__},
                )
                raise
            stock_code = company_data.get("stock_code") or stock_code
            logger.info(
                f"[Task {analysis_id}] Step 1/6 completed: Collected {company_data.get('data_source')} data for {company_name} ({stock_code})"
            )
            await self._persist_task_event(
                analysis_id,
                stage="collecting_data",
                level="info",
                event_type="provider_collection_completed",
                message="财务快照采集完成",
                payload={
                    "providers_used": sorted({source.split(".")[0] for source_list in (company_data.get("field_sources") or {}).values() for source in source_list}),
                    "error_count": len(company_data.get("errors") or []),
                    "missing_fields_count": len(company_data.get("missing_fields") or []),
                    "missing_core_fields": company_data.get("missing_core_fields") or [],
                },
            )
            await self._persist_task_event(
                analysis_id,
                stage="collecting_data",
                level="info",
                event_type="stage_completed",
                message="公司数据采集完成",
                payload={
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "data_source": company_data.get("data_source"),
                    "data_date": company_data.get("data_date"),
                    "insufficient_data": company_data.get("insufficient_data"),
                },
            )
            
            logger.info(f"[Task {analysis_id}] Step 2/6: Calculating financial ratios")
            task_info["current_step"] = "calculating_ratios"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "calculating_ratios")
            await self._persist_task_event(
                analysis_id,
                stage="calculating_ratios",
                level="info",
                event_type="stage_started",
                message="开始计算财务比率",
            )
            financial_ratios = await self._calculate_financial_ratios(company_data)
            logger.info(f"[Task {analysis_id}] Step 2/6 completed: Calculated financial ratios")
            await self._persist_task_event(
                analysis_id,
                stage="calculating_ratios",
                level="info",
                event_type="stage_completed",
                message="财务比率计算完成",
                payload={"available_ratio_keys": sorted(financial_ratios.keys())},
            )
            
            # 步骤3: 构建 AgentContext
            logger.info(f"[Task {analysis_id}] Step 3/6: Building agent context")
            task_info["current_step"] = ProgressStage.BUILDING_CONTEXT.value
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, ProgressStage.BUILDING_CONTEXT.value)
            await self._persist_task_event(
                analysis_id,
                stage=ProgressStage.BUILDING_CONTEXT.value,
                level="info",
                event_type="stage_started",
                message="开始构建 Agent 上下文",
            )
            agent_context = self._build_agent_context(
                analysis_id=analysis_id,
                company_name=company_name,
                stock_code=stock_code,
                company_data=company_data,
                financial_ratios=financial_ratios,
            )
            logger.info(f"[Task {analysis_id}] Step 3/6 completed: Agent context ready")
            await self._persist_task_event(
                analysis_id,
                stage=ProgressStage.BUILDING_CONTEXT.value,
                level="info",
                event_type="stage_completed",
                message="Agent 上下文构建完成",
                payload={
                    "missing_core_fields": agent_context.data_quality.missing_core_fields,
                    "insufficient_data": agent_context.data_quality.insufficient_data,
                },
            )

            # 步骤4: 编排多 Agent 执行
            logger.info(f"[Task {analysis_id}] Step 4/6: Running multi-agent orchestration")
            task_info["current_step"] = "resolving_llm_config"
            _update_active_task(analysis_id, task_info)
            await self._persist_task_event(
                analysis_id,
                stage="resolving_llm_config",
                level="info",
                event_type="llm_config_started",
                message="开始解析 LLM 配置",
                payload={"api_config_id": api_config_id},
            )
            try:
                llm_config = await self._get_llm_config(user_id, api_config_id)
            except Exception as exc:
                await self._persist_task_event(
                    analysis_id,
                    stage="resolving_llm_config",
                    level="error",
                    event_type="llm_config_failed",
                    message=str(exc) or "LLM 配置读取失败",
                    payload={"error_type": type(exc).__name__},
                )
                raise
            logger.info(f"[Task {analysis_id}] Using LLM provider: {llm_config['provider']}")
            await self._persist_task_event(
                analysis_id,
                stage="resolving_llm_config",
                level="info",
                event_type="llm_config_completed",
                message="LLM 配置读取完成",
                payload={
                    "provider": llm_config.get("provider"),
                    "model_version": llm_config.get("model_version"),
                },
            )
            await self._persist_task_event(
                analysis_id,
                stage="running_multi_agent_orchestration",
                level="info",
                event_type="stage_started",
                message="开始执行多 Agent 编排",
                payload={
                    "provider": llm_config.get("provider"),
                    "model_version": llm_config.get("model_version"),
                },
            )

            async def on_stage(stage: ProgressStage):
                task_info["current_step"] = stage.value
                _update_active_task(analysis_id, task_info)
                await self._update_status(analysis_id, stage.value)
                await self._persist_task_event(
                    analysis_id,
                    stage=stage.value,
                    level="info",
                    event_type="stage_started",
                    message=f"进入阶段：{stage.value}",
                )

            async def on_role_event(role: AgentRole, status: AgentRunStatus, payload: dict | None):
                event_type_map = {
                    AgentRunStatus.RUNNING: "agent_started",
                    AgentRunStatus.COMPLETED: "agent_completed",
                    AgentRunStatus.FAILED: "agent_failed",
                }
                event_type = event_type_map.get(status)
                if event_type is None:
                    return
                await self._persist_task_event(
                    analysis_id,
                    stage=f"agent.{role.value}",
                    level="error" if status == AgentRunStatus.FAILED else "info",
                    event_type=event_type,
                    message=f"{role.value} {status.value}",
                    payload={"role": role.value, "status": status.value, **(payload or {})},
                )

            orchestrator = AgentOrchestrator(llm_config=llm_config, on_stage=on_stage, on_role_event=on_role_event)
            orchestration_result = await orchestrator.run(agent_context)
            await self._save_agent_runs(
                analysis_id=analysis_id,
                orchestration_result=orchestration_result,
                llm_config=llm_config,
            )
            analysis_result = self._render_orchestration_markdown(orchestration_result)
            logger.info(f"[Task {analysis_id}] Step 4/6 completed: Multi-agent orchestration done")
            await self._persist_task_event(
                analysis_id,
                stage="running_multi_agent_orchestration",
                level="info",
                event_type="stage_completed",
                message="多 Agent 编排完成",
                payload={
                    "failed_roles": [role.value for role in orchestration_result.failed_roles],
                    "final_score": orchestration_result.synthesis_result.final_score,
                    "investment_decision": orchestration_result.synthesis_result.investment_decision,
                },
            )
            
            # 步骤5: 生成报告
            logger.info(f"[Task {analysis_id}] Step 5/6: Generating report")
            task_info["current_step"] = ProgressStage.GENERATING_REPORT.value
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, ProgressStage.GENERATING_REPORT.value)
            await self._persist_task_event(
                analysis_id,
                stage=ProgressStage.GENERATING_REPORT.value,
                level="info",
                event_type="stage_started",
                message="开始生成报告",
            )
            
            report_generator = ReportGenerator()
            content_md, content_html = await report_generator.generate(
                company_data=company_data,
                financial_ratios=financial_ratios,
                analysis_result=analysis_result,
                orchestration_result=orchestration_result,
                include_charts=include_charts,
            )
            content_md, content_html = self._inject_data_quality_notice(
                content_md=content_md,
                content_html=content_html,
                company_data=company_data,
            )
            logger.info(f"[Task {analysis_id}] Step 5/6 completed: Report generated")
            await self._persist_task_event(
                analysis_id,
                stage=ProgressStage.GENERATING_REPORT.value,
                level="info",
                event_type="stage_completed",
                message="报告生成完成",
                payload={
                    "markdown_length": len(content_md),
                    "html_length": len(content_html),
                },
            )
            
            # 步骤6: 保存报告
            logger.info(f"[Task {analysis_id}] Step 6/6: Saving report to database")
            task_info["current_step"] = ProgressStage.SAVING_REPORT.value
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, ProgressStage.SAVING_REPORT.value)
            await self._persist_task_event(
                analysis_id,
                stage=ProgressStage.SAVING_REPORT.value,
                level="info",
                event_type="report_save_started",
                message="开始保存报告到数据库",
            )
            structured_data = build_structured_report_payload(
                company_data=company_data,
                financial_ratios=financial_ratios,
                orchestration_result=orchestration_result,
            )
            try:
                await self._save_report(analysis_id, content_md, content_html, structured_data)
            except Exception as exc:
                await self._persist_task_event(
                    analysis_id,
                    stage=ProgressStage.SAVING_REPORT.value,
                    level="error",
                    event_type="report_save_failed",
                    message=str(exc) or "报告保存失败",
                    payload={"error_type": type(exc).__name__},
                )
                raise
            await self._persist_task_event(
                analysis_id,
                stage=ProgressStage.SAVING_REPORT.value,
                level="info",
                event_type="report_save_completed",
                message="报告保存完成",
            )
            
            # 完成
            task_info["current_step"] = "completed"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "completed")
            elapsed_time = time.time() - start_time
            await self._persist_task_event(
                analysis_id,
                stage="completed",
                level="info",
                event_type="task_completed",
                message="分析任务完成",
                payload={"elapsed_time_seconds": round(elapsed_time, 2)},
            )
            
            logger.info(f"[Task {analysis_id}] Analysis completed successfully in {elapsed_time:.2f}s")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.exception(f"[Task {analysis_id}] Analysis failed after {elapsed_time:.2f}s: {str(e)}")
            failed_stage = task_info.get("current_step") or "pending"
            task_info["current_step"] = "failed"
            task_info["error"] = str(e)
            _update_active_task(analysis_id, task_info)
            await self._persist_task_event(
                analysis_id,
                stage=failed_stage,
                level="error",
                event_type="task_failed",
                message=str(e) or f"{failed_stage} 阶段失败",
                payload={
                    "error_type": type(e).__name__,
                    "current_stage": failed_stage,
                    "elapsed_time_seconds": round(elapsed_time, 2),
                },
            )
            await self._update_status(
                analysis_id,
                "failed",
                current_stage=failed_stage,
                error_message=str(e) or type(e).__name__,
            )
        finally:
            _remove_active_task(analysis_id)
            logger.info(f"[Task {analysis_id}] Removed from active tasks")

    def _build_agent_context(
        self,
        *,
        analysis_id: str,
        company_name: str,
        stock_code: str | None,
        company_data: dict,
        financial_ratios: dict,
    ) -> AgentContext:
        return AgentContext(
            analysis_id=UUID(analysis_id),
            company_name=company_name,
            stock_code=stock_code,
            basic_profile={
                "industry": company_data.get("industry"),
                "exchange": company_data.get("exchange"),
            },
            financial_data={
                "revenue": company_data.get("revenue"),
                "net_profit": company_data.get("net_profit"),
                "gross_margin": company_data.get("gross_margin"),
                "roe": company_data.get("roe"),
                "asset_liability_ratio": company_data.get("asset_liability_ratio"),
                "operating_cash_flow": company_data.get("operating_cash_flow"),
            },
            financial_ratios=financial_ratios,
            sources=[],
            data_quality={
                "is_mock": False,
                "missing_fields": company_data.get("missing_fields") or [],
                "missing_core_fields": company_data.get("missing_core_fields") or [],
                "missing_ratio": company_data.get("missing_ratio"),
                "insufficient_data": company_data.get("insufficient_data", False),
                "quality_note": company_data.get("quality_note"),
            },
        )

    async def _collect_company_data(self, *, company_name: str, stock_code: str | None) -> dict:
        """Collect a normalized company snapshot through the multi-provider collector."""
        collector = self._snapshot_collector_factory()
        company_data = await collector.collect(company_name=company_name, stock_code=stock_code)
        company_data["company_name"] = company_data.get("company_name") or company_name
        company_data["stock_code"] = company_data.get("stock_code") or stock_code
        company_data["exchange"] = company_data.get("exchange") or None
        return self._apply_snapshot_quality(company_data)

    async def _calculate_financial_ratios(self, company_data: dict) -> dict:
        collector = DataCollector()
        return await collector.calculate_ratios(company_data)

    @staticmethod
    def _build_data_quality_note(company_data: dict) -> str:
        missing_fields = [
            field
            for field in ("revenue", "net_profit", "gross_margin", "roe", "market_cap", "pe_ratio", "pb_ratio")
            if company_data.get(field) is None
        ]

        source = company_data.get("data_source", "unknown")
        if not missing_fields:
            return f"使用实时数据来源：{source}。"

        return f"使用实时数据来源：{source}，但缺失字段：{', '.join(missing_fields)}。"

    @staticmethod
    def _compose_data_quality_notice(company_data: dict) -> str:
        quality_note = str(company_data.get("quality_note") or "").strip()
        if quality_note:
            return quality_note

        source = company_data.get("data_source") or "unknown"
        missing_core_fields = [str(field) for field in (company_data.get("missing_core_fields") or []) if field]
        if missing_core_fields:
            visible_missing = "、".join(missing_core_fields[:6])
            return f"当前数据源 {source} 的核心财务字段缺失，缺失项包括：{visible_missing}。"

        if company_data.get("insufficient_data"):
            return f"当前数据源 {source} 的财务快照不足以支撑正式分析。"

        return f"当前数据源 {source} 的财务快照存在缺口，请结合结构化数据质量字段审阅。"

    @classmethod
    def _inject_data_quality_notice(cls, *, content_md: str, content_html: str, company_data: dict) -> tuple[str, str]:
        if not company_data.get("insufficient_data"):
            return content_md, content_html

        notice = cls._compose_data_quality_notice(company_data)
        if not notice:
            return content_md, content_html

        markdown_notice = "## 数据不足说明\n\n" f"> {notice}\n\n"
        if markdown_notice not in content_md:
            separator = "\n---\n\n"
            if separator in content_md:
                content_md = content_md.replace(separator, f"{separator}{markdown_notice}", 1)
            else:
                content_md = f"{markdown_notice}{content_md}"

        html_notice = (
            '<div class="data-quality-warning" '
            'style="margin: 16px 0; padding: 16px; border: 1px solid #f5c2c7; '
            'border-radius: 10px; background: #fff3f4; color: #842029;">'
            f"<strong>数据不足说明：</strong>{escape(notice)}"
            "</div>"
        )
        if html_notice not in content_html:
            container_marker = '<div class="container">'
            if container_marker in content_html:
                content_html = content_html.replace(container_marker, f"{container_marker}\n        {html_notice}", 1)
            else:
                content_html = f"{html_notice}{content_html}"

        return content_md, content_html

    @staticmethod
    def _apply_snapshot_quality(company_data: dict) -> dict:
        quality = evaluate_snapshot_quality(company_data)
        company_data["missing_fields"] = quality["missing_fields"]
        company_data["missing_core_fields"] = quality["missing_core_fields"]
        company_data["missing_ratio"] = quality["missing_ratio"]
        company_data["insufficient_data"] = quality["insufficient_data"]
        company_data["quality_note"] = quality["quality_note"]
        company_data["data_quality"] = quality
        return company_data

    @staticmethod
    def _role_display_name(role: AgentRole) -> str:
        display = {
            AgentRole.MUNGER: "芒格视角",
            AgentRole.INDUSTRY: "产业视角",
            AgentRole.AUDIT: "审计视角",
            AgentRole.SYNTHESIS: "汇总视角",
        }
        return display.get(role, role.value)

    def _render_orchestration_markdown(self, orchestration_result: OrchestrationResult) -> str:
        synthesis = orchestration_result.synthesis_result
        report_sections = synthesis.report_sections
        failed_roles = [self._role_display_name(role) for role in orchestration_result.failed_roles]

        role_summary: dict[AgentRole, str] = {}
        for run in orchestration_result.role_runs:
            if run.result is not None:
                role_summary[run.role] = run.result.summary
            elif run.error_message:
                role_summary[run.role] = f"{self._role_display_name(run.role)}执行失败：{run.error_message}"
            else:
                role_summary[run.role] = f"{self._role_display_name(run.role)}未返回输出。"

        lines = [
            "## 多 Agent 综合结论",
            "",
            f"- 最终评分：{synthesis.final_score:.2f}/10",
            f"- 投资结论：{synthesis.investment_decision}",
            f"- 数据充分性：{'不足' if synthesis.insufficient_data else '可用'}",
        ]

        if failed_roles:
            lines.append(f"- 降级执行：角色失败 -> {', '.join(failed_roles)}")

        if synthesis.consensus:
            lines.extend(["", "### 主要共识"])
            lines.extend([f"- {item}" for item in synthesis.consensus[:6]])

        if synthesis.major_risks:
            lines.extend(["", "### 主要风险"])
            lines.extend([f"- {item}" for item in synthesis.major_risks[:6]])

        if synthesis.disagreements:
            lines.extend(["", "### 关键分歧"])
            for item in synthesis.disagreements[:5]:
                lines.append(
                    f"- {item.topic}：芒格={item.munger or '未提供'}；产业={item.industry or '未提供'}；审计={item.audit or '未提供'}"
                )

        lines.extend(
            [
                "",
                "## 角色观点摘要",
                "",
                "### 芒格视角",
                report_sections.munger_view or role_summary.get(AgentRole.MUNGER, "暂无输出"),
                "",
                "### 产业视角",
                report_sections.industry_view or role_summary.get(AgentRole.INDUSTRY, "暂无输出"),
                "",
                "### 审计视角",
                report_sections.audit_view or role_summary.get(AgentRole.AUDIT, "暂无输出"),
                "",
                "## 汇总说明",
                report_sections.synthesis or "未提供额外汇总说明。",
            ]
        )

        return "\n".join(lines)

    async def _persist_task_event(
        self,
        analysis_id: str,
        *,
        stage: str | None,
        level: str,
        event_type: str,
        message: str,
        payload: dict | None = None,
    ) -> None:
        try:
            async with AsyncSessionLocal() as db:
                db.add(
                    AnalysisEvent(
                        analysis_id=UUID(analysis_id),
                        stage=stage,
                        level=level,
                        event_type=event_type,
                        message=message,
                        payload_json=payload,
                    )
                )
                await db.commit()
        except Exception as exc:
            logger.warning(
                "[Task %s] Failed to persist analysis event (%s/%s): %s",
                analysis_id,
                stage,
                event_type,
                exc,
            )

    async def _update_status(
        self,
        analysis_id: str,
        status: str,
        *,
        current_stage: str | None = None,
        error_message: str | None = None,
    ):
        """
        更新分析记录的状态
        
        参数:
            analysis_id: 分析记录ID
            status: 新状态值
        
        状态值说明:
            - pending: 等待处理
            - collecting_data: 正在采集数据
            - calculating_ratios: 正在计算财务比率
            - building_context: 正在构建 Agent 上下文
            - running_munger_agent: 正在执行芒格角色
            - running_industry_agent: 正在执行产业角色
            - running_audit_agent: 正在执行审计角色
            - running_synthesis_agent: 正在执行汇总角色
            - generating_report: 正在生成报告
            - saving_report: 正在保存报告
            - completed: 已完成
            - failed: 失败
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Analysis).where(Analysis.id == UUID(analysis_id))
            )
            analysis = result.scalar_one_or_none()
            if analysis:
                analysis.status = status
                analysis.current_stage = current_stage or status
                if status != "failed":
                    analysis.error_message = None
                    analysis.failed_at = None
                if status == "completed":
                    analysis.completed_at = datetime.utcnow()
                if status == "failed":
                    analysis.error_message = error_message
                    analysis.failed_at = datetime.utcnow()
                await db.commit()

    async def _get_llm_config(self, user_id: str, api_config_id: str = None) -> dict:
        """
        获取 LLM 配置
        
        按以下优先级获取配置：
        1. 指定的 API 配置ID
        2. 用户的默认 API 配置
        3. 系统默认配置
        
        参数:
            user_id: 用户ID
            api_config_id: 指定的 API 配置ID（可选）
        
        返回:
            dict: 包含 provider, api_key, base_url, model_version 的配置字典
        """
        async with AsyncSessionLocal() as db:
            # 优先使用指定的配置
            if api_config_id:
                result = await db.execute(
                    select(APIConfig).where(APIConfig.id == UUID(api_config_id))
                )
                config = result.scalar_one_or_none()
                if config:
                    return {
                        "provider": config.provider,
                        "api_key": decrypt_api_key(config.api_key_encrypted),
                        "base_url": config.base_url,
                        "model_version": config.model_version,
                    }
            
            # 其次使用用户默认配置
            result = await db.execute(
                select(APIConfig).where(
                    APIConfig.user_id == UUID(user_id),
                    APIConfig.is_default == True,
                )
            )
            default_config = result.scalar_one_or_none()
            
            if default_config:
                return {
                    "provider": default_config.provider,
                    "api_key": decrypt_api_key(default_config.api_key_encrypted),
                    "base_url": default_config.base_url,
                    "model_version": default_config.model_version,
                }
        
        # 最后使用系统默认配置
        return {
            "provider": settings.DEFAULT_LLM_PROVIDER,
            "api_key": settings.DEFAULT_LLM_API_KEY or None,
            "base_url": settings.LLM_PROVIDER_URLS.get(settings.DEFAULT_LLM_PROVIDER),
            "model_version": settings.DEFAULT_LLM_MODEL,
        }

    async def _save_report(
        self,
        analysis_id: str,
        content_md: str,
        content_html: str,
        structured_data: dict | None = None,
    ):
        """
        保存分析报告到数据库
        
        参数:
            analysis_id: 分析记录ID
            content_md: Markdown 格式的报告内容
            content_html: HTML 格式的报告内容
        """
        async with AsyncSessionLocal() as db:
            report = Report(
                analysis_id=UUID(analysis_id),
                content_md=content_md,
                content_html=content_html,
                structured_data_json=structured_data,
            )
            db.add(report)
            await db.commit()

    async def _save_agent_runs(
        self,
        *,
        analysis_id: str,
        orchestration_result: OrchestrationResult,
        llm_config: dict,
    ) -> None:
        analysis_uuid = UUID(analysis_id)
        provider = llm_config.get("provider")
        model_name = llm_config.get("model_version")

        def _status_value(value: AgentRunStatus | str) -> str:
            if isinstance(value, AgentRunStatus):
                return value.value
            return str(value)

        def _pick_raw_output(trace: dict[str, str | None]) -> str | None:
            return trace.get("retry_raw_output") or trace.get("raw_output")

        records: list[AgentRun] = []

        for role_run in orchestration_result.role_runs:
            trace = role_run.trace or {}
            records.append(
                AgentRun(
                    analysis_id=analysis_uuid,
                    role=role_run.role.value,
                    status=_status_value(role_run.status),
                    prompt_version="v1",
                    schema_version="v1",
                    model_provider=provider,
                    model_name=model_name,
                    raw_output=_pick_raw_output(trace),
                    structured_output_json=(
                        role_run.result.model_dump(mode="json") if role_run.result is not None else None
                    ),
                    error_message=role_run.error_message or trace.get("parse_error"),
                    latency_ms=None,
                    started_at=None,
                    completed_at=None,
                )
            )

        synthesis_trace = orchestration_result.synthesis_trace or {}
        records.append(
            AgentRun(
                analysis_id=analysis_uuid,
                role=AgentRole.SYNTHESIS.value,
                status=AgentRunStatus.COMPLETED.value,
                prompt_version="v1",
                schema_version="v1",
                model_provider=provider,
                model_name=model_name,
                raw_output=_pick_raw_output(synthesis_trace),
                structured_output_json=orchestration_result.synthesis_result.model_dump(mode="json"),
                error_message=synthesis_trace.get("parse_error"),
                latency_ms=None,
                started_at=None,
                completed_at=None,
            )
        )

        async with AsyncSessionLocal() as db:
            db.add_all(records)
            await db.commit()
