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

from app.models.user import Analysis, Report, APIConfig
from app.services.data_collector import DataCollector
from app.services.llm_service import LLMService
from app.services.report_generator import ReportGenerator
from app.utils.encryption import decrypt_api_key
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    分析服务类
    
    负责协调整个分析流程的执行，包括数据采集、LLM调用和报告生成。
    
    属性:
        db: 异步数据库会话
    
    使用示例:
        service = AnalysisService(db)
        await service.run_analysis(
            analysis_id="xxx",
            user_id="xxx",
            company_name="特变电工",
            stock_code="600089"
        )
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化分析服务
        
        参数:
            db: 异步数据库会话
        """
        self.db = db

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
        try:
            # 步骤1: 采集公司数据
            await self._update_status(analysis_id, "collecting_data")
            
            collector = DataCollector()
            company_data = await collector.collect(company_name, stock_code)
            
            # 步骤2: 计算财务比率
            await self._update_status(analysis_id, "calculating_ratios")
            financial_ratios = await collector.calculate_ratios(company_data)
            
            # 步骤3: 生成提示词（状态更新）
            await self._update_status(analysis_id, "generating_prompt")
            
            # 步骤4: 调用 LLM 执行分析
            await self._update_status(analysis_id, "calling_llm")
            
            llm_config = await self._get_llm_config(user_id, api_config_id)
            llm_service = LLMService(llm_config)
            analysis_result = await llm_service.analyze(company_data, financial_ratios)
            
            # 步骤5: 生成报告
            await self._update_status(analysis_id, "generating_report")
            
            report_generator = ReportGenerator()
            content_md, content_html = await report_generator.generate(
                company_data=company_data,
                financial_ratios=financial_ratios,
                analysis_result=analysis_result,
                include_charts=include_charts,
            )
            
            # 步骤6: 保存报告
            await self._save_report(analysis_id, content_md, content_html)
            
            # 完成
            await self._update_status(analysis_id, "completed")
            
            logger.info(f"Analysis {analysis_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {str(e)}")
            await self._update_status(analysis_id, "failed")

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
        result = await self.db.execute(
            select(Analysis).where(Analysis.id == UUID(analysis_id))
        )
        analysis = result.scalar_one_or_none()
        if analysis:
            analysis.status = status
            if status == "completed":
                analysis.completed_at = datetime.utcnow()
            await self.db.commit()

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
        # 优先使用指定的配置
        if api_config_id:
            result = await self.db.execute(
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
        result = await self.db.execute(
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
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
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
        report = Report(
            analysis_id=UUID(analysis_id),
            content_md=content_md,
            content_html=content_html,
        )
        self.db.add(report)
        await self.db.commit()
