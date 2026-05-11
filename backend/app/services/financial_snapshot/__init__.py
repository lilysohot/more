"""Shared contracts and quality helpers for financial snapshots."""

from app.services.financial_snapshot.constants import (
    CORE_SNAPSHOT_FIELDS,
    DEFAULT_REQUIRED_TRIO_FIELDS,
    FIELD_GROUPS,
    OUTPUT_FIELDS,
    QUALITY_TRACKED_FIELDS,
    VALUATION_ONLY_FIELDS,
)
from app.services.financial_snapshot.collector import FinancialSnapshotCollector
from app.services.financial_snapshot.providers import FinancialDataProvider
from app.services.financial_snapshot.quality import evaluate_snapshot_quality
from app.services.financial_snapshot.types import (
    CompanyFinancialSnapshot,
    FieldSources,
    ProviderErrorInfo,
    ProviderResult,
    SourceFields,
)

__all__ = [
    "CompanyFinancialSnapshot",
    "CORE_SNAPSHOT_FIELDS",
    "DEFAULT_REQUIRED_TRIO_FIELDS",
    "FIELD_GROUPS",
    "FinancialSnapshotCollector",
    "FinancialDataProvider",
    "FieldSources",
    "OUTPUT_FIELDS",
    "QUALITY_TRACKED_FIELDS",
    "ProviderErrorInfo",
    "ProviderResult",
    "SourceFields",
    "VALUATION_ONLY_FIELDS",
    "evaluate_snapshot_quality",
]
