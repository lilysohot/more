"""
分析模块数据模型定义

定义分析相关的 Pydantic 模型，用于：
- 请求数据验证
- 响应数据序列化
- API 接口文档生成
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class AnalysisBase(BaseModel):
    """分析基础模型"""
    company_name: str
    stock_code: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    """
    创建分析请求模型
    
    属性:
        company_name: 公司名称（必填）
        stock_code: 股票代码（可选，如不提供会自动搜索）
        include_charts: 是否在报告中包含图表，默认 True
        api_config_id: 用户自定义的 API 配置ID（可选，不填则使用系统默认）
    """
    include_charts: bool = True
    api_config_id: Optional[UUID] = None


class AnalysisResponse(AnalysisBase):
    """
    分析记录响应模型
    
    属性:
        id: 分析记录唯一标识
        user_id: 所属用户ID
        status: 分析状态
        created_at: 创建时间
        completed_at: 完成时间（可能为空）
    """
    id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AnalysisDetailResponse(AnalysisResponse):
    """分析详情响应模型（继承自 AnalysisResponse，可扩展更多字段）"""
    pass


class AnalysisProgress(BaseModel):
    """
    分析进度响应模型
    
    属性:
        analysis_id: 分析记录ID
        status: 当前状态
        progress_stage: 进度阶段（兼容多 Agent 细粒度阶段）
        progress: 进度百分比（0-100）
        message: 进度提示消息
    """
    analysis_id: UUID
    status: str
    progress_stage: Optional[str] = None
    progress: int
    message: str


class StructuredReportCompany(BaseModel):
    """结构化报告中的公司信息。"""

    company_name: str
    stock_code: Optional[str] = None
    ts_code: Optional[str] = None
    exchange: Optional[str] = None
    industry: Optional[str] = None
    data_source: Optional[str] = None
    data_date: Optional[str] = None


class StructuredReportFinancials(BaseModel):
    """结构化报告中的财务、估值和质量指标。"""

    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    equity: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    close_price: Optional[float] = None
    asset_liability_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    operating_cash_flow_to_net_profit: Optional[float] = None


class StructuredReportDisagreement(BaseModel):
    """多 Agent 观点分歧。"""

    topic: str
    munger: Optional[str] = None
    industry: Optional[str] = None
    audit: Optional[str] = None


class StructuredReportSynthesis(BaseModel):
    """综合 Agent 的最终结论。"""

    company_profile: Optional[str] = None
    consensus: List[str] = Field(default_factory=list)
    disagreements: List[StructuredReportDisagreement] = Field(default_factory=list)
    final_score: Optional[float] = None
    investment_decision: Optional[str] = None
    insufficient_data: bool = False
    core_reasons: List[str] = Field(default_factory=list)
    major_risks: List[str] = Field(default_factory=list)


class StructuredReportEvidence(BaseModel):
    """Agent 结论证据。"""

    item: str
    source: Optional[str] = None
    source_type: Optional[str] = None
    source_date: Optional[str] = None
    excerpt: Optional[str] = None
    confidence: Optional[float] = None


class StructuredReportAgent(BaseModel):
    """单个 Agent 的结构化输出。"""

    name: str
    title: str
    status: str = "completed"
    score: Optional[float] = None
    summary: Optional[str] = None
    thesis: List[str] = Field(default_factory=list)
    positives: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    evidence: List[StructuredReportEvidence] = Field(default_factory=list)
    insufficient_data: bool = False
    error_message: Optional[str] = None


class StructuredReportDataQuality(BaseModel):
    """报告数据完整度和降级信息。"""

    is_mock: bool = False
    quality_note: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    missing_financial_fields: List[str] = Field(default_factory=list)
    completed_agent_count: int = 0
    failed_agent_roles: List[str] = Field(default_factory=list)


class StructuredReportOriginal(BaseModel):
    """原始 Markdown/HTML 报告内容。"""

    content_md: Optional[str] = None
    content_html: Optional[str] = None


class ReportResponse(BaseModel):
    """
    分析报告响应模型
    
    属性:
        id: 报告唯一标识
        analysis_id: 关联的分析记录ID
        content_md: Markdown 格式的报告内容
        content_html: HTML 格式的报告内容（包含图表）
        created_at: 创建时间
    """
    id: UUID
    analysis_id: UUID
    content_md: Optional[str]
    content_html: Optional[str]
    created_at: datetime
    company: Optional[StructuredReportCompany] = None
    financials: Optional[StructuredReportFinancials] = None
    synthesis: Optional[StructuredReportSynthesis] = None
    agents: List[StructuredReportAgent] = Field(default_factory=list)
    data_quality: Optional[StructuredReportDataQuality] = None
    original: Optional[StructuredReportOriginal] = None

    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    """
    分析列表响应模型
    
    属性:
        items: 分析记录列表
        total: 总记录数
    """
    items: List[AnalysisResponse]
    total: int


class CompanyData(BaseModel):
    """
    公司数据模型
    
    存储从外部数据源采集的公司信息
    
    属性:
        company_name: 公司名称
        stock_code: 股票代码
        exchange: 交易所（SH/SZ/HK/US）
        industry: 所属行业
        revenue: 营业收入
        net_profit: 净利润
        gross_margin: 毛利率
        asset_liability_ratio: 资产负债率
        operating_cash_flow: 经营现金流
        roe: 净资产收益率
        market_cap: 市值
        pe_ratio: 市盈率
        pb_ratio: 市净率
        data_source: 数据来源
        data_date: 数据日期
    """
    company_name: str
    stock_code: Optional[str] = None
    exchange: Optional[str] = None
    industry: Optional[str] = None
    
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    asset_liability_ratio: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    roe: Optional[float] = None
    
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    
    data_source: Optional[str] = None
    data_date: Optional[str] = None


class FinancialRatios(BaseModel):
    """
    财务比率模型
    
    存储计算得出的财务比率数据
    
    属性:
        gross_margin: 毛利率
        net_margin: 净利率
        roe: 净资产收益率
        roa: 总资产收益率
        current_ratio: 流动比率
        quick_ratio: 速动比率
        debt_to_equity: 负债权益比
        asset_liability_ratio: 资产负债率
        operating_cash_flow_to_net_profit: 经营现金流/净利润
    """
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    asset_liability_ratio: Optional[float] = None
    operating_cash_flow_to_net_profit: Optional[float] = None
