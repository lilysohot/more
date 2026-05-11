"""Canonical snapshot field definitions used across providers and reports."""

IDENTITY_FIELDS = (
    "company_name",
    "stock_code",
    "ts_code",
    "exchange",
    "industry",
)

INCOME_FIELDS = (
    "revenue",
    "net_profit",
    "gross_margin",
    "net_margin",
    "roe",
    "roa",
)

BALANCE_SHEET_FIELDS = (
    "total_assets",
    "total_liabilities",
    "equity",
    "asset_liability_ratio",
    "debt_to_equity",
    "current_assets",
    "current_liabilities",
    "current_ratio",
    "quick_ratio",
)

CASH_FLOW_FIELDS = (
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "operating_cash_flow_to_net_profit",
)

VALUATION_ONLY_FIELDS = (
    "market_cap",
    "pe_ratio",
    "pb_ratio",
    "ps_ratio",
    "close_price",
)

OUTPUT_FIELDS = (
    *IDENTITY_FIELDS,
    *INCOME_FIELDS,
    *BALANCE_SHEET_FIELDS,
    *CASH_FLOW_FIELDS,
    *VALUATION_ONLY_FIELDS,
    "data_source",
    "data_date",
)

QUALITY_TRACKED_FIELDS = (
    *INCOME_FIELDS,
    *BALANCE_SHEET_FIELDS,
    *CASH_FLOW_FIELDS,
    *VALUATION_ONLY_FIELDS,
)

CORE_SNAPSHOT_FIELDS = (
    "revenue",
    "net_profit",
    "total_assets",
    "total_liabilities",
    "operating_cash_flow",
    "roe",
)

DEFAULT_REQUIRED_TRIO_FIELDS = (
    "revenue",
    "net_profit",
    "total_assets",
)

FIELD_GROUPS = {
    "identity": IDENTITY_FIELDS,
    "income": INCOME_FIELDS,
    "balance_sheet": BALANCE_SHEET_FIELDS,
    "cash_flow": CASH_FLOW_FIELDS,
    "valuation": VALUATION_ONLY_FIELDS,
    "core": CORE_SNAPSHOT_FIELDS,
}
