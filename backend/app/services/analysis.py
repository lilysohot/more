"""
分析服务模块

协调整个分析流程的执行，包括：
1. 数据采集
2. 财务比率计算
3. LLM 分析调用
4. 报告生成

该服务在后台异步执行，通过数据库状态更新进度。
"""

import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import AsyncSessionLocal
from app.models.user import Analysis, Report, APIConfig
from app.services.data_collector import DataCollector
from app.services.llm_service import LLMService
from app.services.report_generator import ReportGenerator
from app.utils.encryption import decrypt_api_key
from app.core.config import settings

logger = logging.getLogger(__name__)

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
    
    def __init__(self):
        """
        初始化分析服务
        """
        pass

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
        3. 调用 LLM 执行三维合一分析
        4. 生成 Markdown 和 HTML 报告
        5. 保存报告到数据库
        
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

        logger.info(f"[Task {analysis_id}] Starting analysis for company: {company_name}")

        try:
            # 步骤1: 采集公司数据
            logger.info(f"[Task {analysis_id}] Step 1/6: Collecting company data")
            task_info["current_step"] = "collecting_data"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "collecting_data")
            
            collector = DataCollector()
            company_data = await collector.collect(company_name, stock_code)
            logger.info(f"[Task {analysis_id}] Step 1/6 completed: Data collected")
            
            # 步骤2: 计算财务比率
            logger.info(f"[Task {analysis_id}] Step 2/6: Calculating financial ratios")
            task_info["current_step"] = "calculating_ratios"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "calculating_ratios")
            financial_ratios = await collector.calculate_ratios(company_data)
            logger.info(f"[Task {analysis_id}] Step 2/6 completed: Ratios calculated")
            
            # 步骤3: 生成提示词（状态更新）
            logger.info(f"[Task {analysis_id}] Step 3/6: Generating prompt")
            task_info["current_step"] = "generating_prompt"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "generating_prompt")
            logger.info(f"[Task {analysis_id}] Step 3/6 completed: Prompt ready")
            
            # 步骤4: 调用 LLM 执行分析
            logger.info(f"[Task {analysis_id}] Step 4/6: Calling LLM for analysis")
            task_info["current_step"] = "calling_llm"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "calling_llm")
            
            llm_config = await self._get_llm_config(user_id, api_config_id)
            logger.info(f"[Task {analysis_id}] Using LLM provider: {llm_config['provider']}")
            llm_service = LLMService(llm_config)
            analysis_result = await llm_service.analyze(company_data, financial_ratios)
            logger.info(f"[Task {analysis_id}] Step 4/6 completed: LLM analysis done")
            
            # 步骤5: 生成报告
            logger.info(f"[Task {analysis_id}] Step 5/6: Generating report")
            task_info["current_step"] = "generating_report"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "generating_report")
            
            report_generator = ReportGenerator()
            content_md, content_html = await report_generator.generate(
                company_data=company_data,
                financial_ratios=financial_ratios,
                analysis_result=analysis_result,
                include_charts=include_charts,
            )
            logger.info(f"[Task {analysis_id}] Step 5/6 completed: Report generated")
            
            # 步骤6: 保存报告
            logger.info(f"[Task {analysis_id}] Step 6/6: Saving report to database")
            task_info["current_step"] = "saving_report"
            _update_active_task(analysis_id, task_info)
            await self._save_report(analysis_id, content_md, content_html)
            
            # 完成
            task_info["current_step"] = "completed"
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "completed")
            
            elapsed_time = time.time() - start_time
            logger.info(f"[Task {analysis_id}] Analysis completed successfully in {elapsed_time:.2f}s")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.exception(f"[Task {analysis_id}] Analysis failed after {elapsed_time:.2f}s: {str(e)}")
            task_info["current_step"] = "failed"
            task_info["error"] = str(e)
            _update_active_task(analysis_id, task_info)
            await self._update_status(analysis_id, "failed")
        finally:
            _remove_active_task(analysis_id)
            logger.info(f"[Task {analysis_id}] Removed from active tasks")

    async def _update_status(self, analysis_id: str, status: str):
        """
        更新分析记录的状态
        
        参数:
            analysis_id: 分析记录ID
            status: 新状态值
        
        状态值说明:
            - pending: 等待处理
            - collecting_data: 正在采集数据
            - calculating_ratios: 正在计算财务比率
            - generating_prompt: 正在生成提示词
            - calling_llm: 正在调用 LLM
            - generating_report: 正在生成报告
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
                if status == "completed":
                    analysis.completed_at = datetime.utcnow()
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

    async def _save_report(self, analysis_id: str, content_md: str, content_html: str):
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
            )
            db.add(report)
            await db.commit()
