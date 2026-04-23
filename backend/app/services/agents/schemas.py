from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentRole(str, Enum):
    MUNGER = "munger"
    INDUSTRY = "industry"
    AUDIT = "audit"
    SYNTHESIS = "synthesis"


class AgentRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProgressStage(str, Enum):
    COLLECTING_DATA = "collecting_data"
    CALCULATING_RATIOS = "calculating_ratios"
    BUILDING_CONTEXT = "building_context"
    RUNNING_MUNGER_AGENT = "running_munger_agent"
    RUNNING_INDUSTRY_AGENT = "running_industry_agent"
    RUNNING_AUDIT_AGENT = "running_audit_agent"
    RUNNING_SYNTHESIS_AGENT = "running_synthesis_agent"
    GENERATING_REPORT = "generating_report"
    SAVING_REPORT = "saving_report"


class BasicProfile(BaseModel):
    industry: Optional[str] = None
    exchange: Optional[str] = None


class FinancialData(BaseModel):
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    roe: Optional[float] = None
    asset_liability_ratio: Optional[float] = None
    operating_cash_flow: Optional[float] = None


class FinancialRatios(BaseModel):
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    current_ratio: Optional[float] = None


class IndustryData(BaseModel):
    market_size: Optional[str] = None
    competition: Optional[str] = None
    trend: Optional[str] = None


class SourceItem(BaseModel):
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    date: Optional[str] = None


class DataQuality(BaseModel):
    is_mock: bool = False
    missing_fields: List[str] = Field(default_factory=list)
    quality_note: Optional[str] = None


class AgentContext(BaseModel):
    analysis_id: UUID
    company_name: str = Field(min_length=1)
    stock_code: Optional[str] = None
    basic_profile: BasicProfile = Field(default_factory=BasicProfile)
    financial_data: FinancialData = Field(default_factory=FinancialData)
    financial_ratios: FinancialRatios = Field(default_factory=FinancialRatios)
    industry_data: IndustryData = Field(default_factory=IndustryData)
    sources: List[SourceItem] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class EvidenceItem(BaseModel):
    item: str = Field(min_length=1)
    source: str = Field(min_length=1)
    source_type: Optional[str] = None
    source_date: Optional[str] = None
    excerpt: Optional[str] = None
    confidence: float = Field(ge=0, le=1)


class AgentResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    role: AgentRole
    summary: str = Field(min_length=1)
    score: float = Field(ge=0, le=10)
    thesis: List[str] = Field(default_factory=list)
    positives: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    insufficient_data: bool = False

    @model_validator(mode="after")
    def validate_output_constraints(self) -> "AgentResult":
        if self.role == AgentRole.SYNTHESIS:
            raise ValueError("AgentResult.role does not accept synthesis")

        if not self.insufficient_data and len(self.evidence) < 1:
            raise ValueError("evidence must contain at least one item when insufficient_data is false")

        if self.insufficient_data and len(self.questions) < 1:
            raise ValueError("questions must contain at least one item when insufficient_data is true")

        return self


class DisagreementItem(BaseModel):
    topic: str = Field(min_length=1)
    munger: Optional[str] = None
    industry: Optional[str] = None
    audit: Optional[str] = None


class ReportSections(BaseModel):
    intro: str = ""
    munger_view: str = ""
    industry_view: str = ""
    audit_view: str = ""
    synthesis: str = ""


class SynthesisResult(BaseModel):
    company_profile: str = Field(min_length=1)
    consensus: List[str] = Field(default_factory=list)
    disagreements: List[DisagreementItem] = Field(default_factory=list)
    final_score: float = Field(ge=0, le=10)
    investment_decision: str = Field(min_length=1)
    insufficient_data: bool = False
    core_reasons: List[str] = Field(default_factory=list)
    major_risks: List[str] = Field(default_factory=list)
    report_sections: ReportSections = Field(default_factory=ReportSections)
