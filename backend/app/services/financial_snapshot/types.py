"""Typed internal contracts for normalized financial snapshots."""

from __future__ import annotations

from typing import TypeAlias, TypedDict


SourceFields: TypeAlias = dict[str, list[str]]
FieldSources: TypeAlias = dict[str, list[str]]


class ProviderErrorInfo(TypedDict, total=False):
    provider: str
    stage: str
    message: str
    code: str | None
    retriable: bool | None


class CompanyFinancialSnapshot(TypedDict, total=False):
    company_name: str | None
    stock_code: str | None
    ts_code: str | None
    exchange: str | None
    industry: str | None
    revenue: float | None
    net_profit: float | None
    gross_margin: float | None
    net_margin: float | None
    roe: float | None
    roa: float | None
    total_assets: float | None
    total_liabilities: float | None
    equity: float | None
    asset_liability_ratio: float | None
    debt_to_equity: float | None
    current_assets: float | None
    current_liabilities: float | None
    current_ratio: float | None
    quick_ratio: float | None
    operating_cash_flow: float | None
    investing_cash_flow: float | None
    financing_cash_flow: float | None
    operating_cash_flow_to_net_profit: float | None
    market_cap: float | None
    pe_ratio: float | None
    pb_ratio: float | None
    ps_ratio: float | None
    close_price: float | None
    data_source: str | None
    data_date: str | None
    source_fields: SourceFields
    field_sources: FieldSources
    missing_fields: list[str]
    missing_core_fields: list[str]
    quality_note: str | None
    missing_ratio: float | None
    insufficient_data: bool
    errors: list[ProviderErrorInfo]


class ProviderResult(TypedDict, total=False):
    provider: str
    stage: str
    success: bool
    data: CompanyFinancialSnapshot
    source_fields: SourceFields
    field_sources: FieldSources
    missing_fields: list[str]
    errors: list[ProviderErrorInfo]
