"""AkShare provider for normalized identity, market, valuation, and financial fields."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

import pandas as pd

from app.services.financial_snapshot.providers.base import FinancialDataProvider


ClientFactory = Callable[[], Any]


def _default_client_factory():
    import akshare as ak

    return ak


class AkShareProvider(FinancialDataProvider):
    def __init__(self, *, client_factory: ClientFactory = _default_client_factory) -> None:
        super().__init__(provider_name="akshare")
        self._client_factory = client_factory

    async def resolve_stock(
        self,
        *,
        company_name: str | None = None,
        stock_code: str | None = None,
    ):
        client = self._client_factory()
        normalized_code = self._normalize_stock_code(stock_code)

        try:
            if normalized_code:
                detail_df = await asyncio.to_thread(client.stock_individual_info_em, normalized_code)
                result = self._map_identity_from_detail(detail_df, fallback_code=normalized_code)
                if result["success"]:
                    return result

            query = (company_name or "").strip()
            if not query:
                return self.error_result(stage="resolve_stock", message="company_name or stock_code is required")

            search_df = await asyncio.to_thread(client.stock_info_a_code_name)
            row = self._find_search_match(search_df, query=query)
            if row is None:
                return self.error_result(stage="resolve_stock", message="akshare search returned no matches")

            resolved_code = self._normalize_stock_code(
                row.get("code") or row.get("代码") or row.get("stock_code")
            )
            fallback_name = self._to_text(row.get("name") or row.get("名称") or row.get("company_name"))
            if not resolved_code:
                return self.error_result(stage="resolve_stock", message="akshare search returned incomplete identity data")

            detail_df = await asyncio.to_thread(client.stock_individual_info_em, resolved_code)
            detail_result = self._map_identity_from_detail(
                detail_df,
                fallback_code=resolved_code,
                fallback_name=fallback_name,
            )
            if detail_result["success"]:
                return detail_result

            if fallback_name:
                return self.success_result(
                    stage="resolve_stock",
                    data={
                        "company_name": fallback_name,
                        "stock_code": resolved_code,
                        "exchange": self._infer_exchange(resolved_code),
                        "data_source": "akshare",
                    },
                    source_fields={"identity": list(search_df.columns)},
                    field_sources={
                        "company_name": ["akshare.identity_search"],
                        "stock_code": ["akshare.identity_search"],
                        "exchange": ["akshare.identity_search"],
                    },
                )
            return self.error_result(stage="resolve_stock", message="akshare identity data unavailable")
        except Exception as exc:
            return self._map_exception(stage="resolve_stock", exc=exc)

    async def get_market_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        client = self._client_factory()
        normalized_code = self._normalize_stock_code(stock_code or ts_code)
        if not normalized_code:
            return self.error_result(stage="market_snapshot", message="stock_code is required")

        end_date = datetime.now(UTC).strftime("%Y%m%d")
        start_date = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y%m%d")

        try:
            hist_df = await asyncio.to_thread(
                client.stock_zh_a_hist,
                symbol=normalized_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="",
            )
        except Exception as exc:
            return self._map_exception(stage="market_snapshot", exc=exc)

        row = self._latest_row(hist_df)
        close_price = self._to_float(row.get("收盘") or row.get("close"))
        data_date = self._normalize_date(row.get("日期") or row.get("date") or row.get("trade_date"))

        return self.success_result(
            stage="market_snapshot",
            data={
                "stock_code": normalized_code,
                "exchange": self._infer_exchange(normalized_code),
                "close_price": close_price,
                "data_source": "akshare",
                "data_date": data_date,
            },
            source_fields={"market": list(hist_df.columns)},
            field_sources={
                "close_price": ["akshare.market"],
                "data_date": ["akshare.market"],
            },
            missing_fields=[field for field, value in {"close_price": close_price, "data_date": data_date}.items() if value is None],
        )

    async def get_valuation_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        client = self._client_factory()
        normalized_code = self._normalize_stock_code(stock_code or ts_code)
        if not normalized_code:
            return self.error_result(stage="valuation_snapshot", message="stock_code is required")

        try:
            valuation_df = await asyncio.to_thread(client.stock_value_em, symbol=normalized_code)
        except Exception:
            valuation_df = pd.DataFrame()

        try:
            detail_df = await asyncio.to_thread(client.stock_individual_info_em, normalized_code)
        except Exception as exc:
            if valuation_df.empty:
                return self._map_exception(stage="valuation_snapshot", exc=exc)
            detail_df = pd.DataFrame()

        value_row = self._latest_row(valuation_df)
        detail_map = self._frame_to_item_map(detail_df)

        market_cap = self._to_float(
            value_row.get("总市值")
            or value_row.get("market_cap")
            or detail_map.get("总市值")
        )
        pe_ratio = self._to_float(
            value_row.get("市盈率")
            or value_row.get("pe_ratio")
            or detail_map.get("市盈率")
        )
        pb_ratio = self._to_float(
            value_row.get("市净率")
            or value_row.get("pb_ratio")
            or detail_map.get("市净率")
        )
        ps_ratio = self._to_float(
            value_row.get("市销率")
            or value_row.get("ps_ratio")
            or detail_map.get("市销率")
        )
        data_date = self._normalize_date(value_row.get("日期") or value_row.get("date"))

        source_fields = {
            "valuation": list(valuation_df.columns),
            "detail": list(detail_df.columns),
        }
        return self.success_result(
            stage="valuation_snapshot",
            data={
                "stock_code": normalized_code,
                "company_name": self._to_text(detail_map.get("股票简称") or detail_map.get("简称")),
                "exchange": self._infer_exchange(normalized_code),
                "market_cap": market_cap,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "ps_ratio": ps_ratio,
                "data_source": "akshare",
                "data_date": data_date,
            },
            source_fields=source_fields,
            field_sources={
                "market_cap": ["akshare.valuation"],
                "pe_ratio": ["akshare.valuation"],
                "pb_ratio": ["akshare.valuation"],
                "ps_ratio": ["akshare.valuation"],
            },
            missing_fields=[
                field
                for field, value in {
                    "market_cap": market_cap,
                    "pe_ratio": pe_ratio,
                    "pb_ratio": pb_ratio,
                }.items()
                if value is None
            ],
        )

    async def get_financial_statement_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        client = self._client_factory()
        normalized_code = self._normalize_stock_code(stock_code or ts_code)
        if not normalized_code:
            return self.error_result(stage="financial_statement_snapshot", message="stock_code is required")

        stock_symbol = self._to_stock_symbol(normalized_code)
        try:
            balance_df, income_df, cash_df = await asyncio.gather(
                asyncio.to_thread(client.stock_financial_report_sina, stock=stock_symbol, symbol="资产负债表"),
                asyncio.to_thread(client.stock_financial_report_sina, stock=stock_symbol, symbol="利润表"),
                asyncio.to_thread(client.stock_financial_report_sina, stock=stock_symbol, symbol="现金流量表"),
            )
        except Exception as exc:
            return self._map_exception(stage="financial_statement_snapshot", exc=exc)

        balance_row = self._latest_row(balance_df)
        income_row = self._latest_row(income_df)
        cash_row = self._latest_row(cash_df)

        revenue = self._to_float(self._first_present(income_row, "营业总收入", "营业收入", "revenue"))
        net_profit = self._to_float(self._first_present(income_row, "净利润", "归属于母公司股东的净利润", "net_profit"))
        total_assets = self._to_float(self._first_present(balance_row, "资产总计", "资产总额", "总资产", "total_assets"))
        total_liabilities = self._to_float(self._first_present(balance_row, "负债合计", "负债总计", "总负债", "total_liabilities"))
        equity = self._to_float(self._first_present(balance_row, "股东权益合计", "所有者权益(或股东权益)合计", "股东权益", "equity"))
        current_assets = self._to_float(self._first_present(balance_row, "流动资产", "current_assets"))
        current_liabilities = self._to_float(self._first_present(balance_row, "流动负债", "current_liabilities"))
        operating_cash_flow = self._to_float(
            self._first_present(cash_row, "经营活动产生的现金流量净额", "operating_cash_flow")
        )
        investing_cash_flow = self._to_float(
            self._first_present(cash_row, "投资活动产生的现金流量净额", "investing_cash_flow")
        )
        financing_cash_flow = self._to_float(
            self._first_present(cash_row, "筹资活动产生的现金流量净额", "financing_cash_flow")
        )
        data_date = self._normalize_date(
            self._first_present(balance_row, "报告日", "报表日期")
            or self._first_present(income_row, "报告日", "报表日期")
            or self._first_present(cash_row, "报告日", "报表日期")
        )

        return self.success_result(
            stage="financial_statement_snapshot",
            data={
                "stock_code": normalized_code,
                "exchange": self._infer_exchange(normalized_code),
                "revenue": revenue,
                "net_profit": net_profit,
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "equity": equity,
                "current_assets": current_assets,
                "current_liabilities": current_liabilities,
                "operating_cash_flow": operating_cash_flow,
                "investing_cash_flow": investing_cash_flow,
                "financing_cash_flow": financing_cash_flow,
                "data_source": "akshare",
                "data_date": data_date,
            },
            source_fields={
                "balance_sheet": list(balance_df.columns),
                "income_statement": list(income_df.columns),
                "cash_flow": list(cash_df.columns),
            },
            field_sources={
                "revenue": ["akshare.financial_statement"],
                "net_profit": ["akshare.financial_statement"],
                "total_assets": ["akshare.financial_statement"],
                "total_liabilities": ["akshare.financial_statement"],
                "equity": ["akshare.financial_statement"],
                "current_assets": ["akshare.financial_statement"],
                "current_liabilities": ["akshare.financial_statement"],
                "operating_cash_flow": ["akshare.financial_statement"],
                "investing_cash_flow": ["akshare.financial_statement"],
                "financing_cash_flow": ["akshare.financial_statement"],
            },
            missing_fields=[
                field
                for field, value in {
                    "revenue": revenue,
                    "net_profit": net_profit,
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "equity": equity,
                }.items()
                if value is None
            ],
        )

    async def get_financial_indicator_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        client = self._client_factory()
        normalized_code = self._normalize_stock_code(stock_code or ts_code)
        if not normalized_code:
            return self.error_result(stage="financial_indicator_snapshot", message="stock_code is required")

        indicator_func = getattr(client, "stock_financial_analysis_indicator", None) or getattr(
            client,
            "stock_financial_analysis_indicator_em",
            None,
        )
        if not callable(indicator_func):
            return self.error_result(
                stage="financial_indicator_snapshot",
                message="akshare financial indicator interface unavailable",
                code="unavailable",
                retriable=False,
            )

        stock_symbol = self._to_stock_symbol(normalized_code)
        try:
            indicator_df = await asyncio.to_thread(indicator_func, symbol=normalized_code)
        except Exception as exc:
            return self._map_exception(stage="financial_indicator_snapshot", exc=exc)

        try:
            balance_df = await asyncio.to_thread(client.stock_financial_report_sina, stock=stock_symbol, symbol="资产负债表")
        except Exception:
            balance_df = pd.DataFrame()

        indicator_row = self._latest_row(indicator_df)
        balance_row = self._latest_row(balance_df)

        total_liabilities = self._to_float(self._first_present(balance_row, "负债合计", "负债总计", "总负债"))
        equity = self._to_float(self._first_present(balance_row, "股东权益合计", "所有者权益(或股东权益)合计", "股东权益"))

        roe = self._to_float(self._first_present(indicator_row, "净资产收益率(%)", "净资产收益率", "roe"))
        roa = self._to_float(self._first_present(indicator_row, "总资产净利润率(%)", "总资产报酬率(%)", "roa"))
        gross_margin = self._to_float(self._first_present(indicator_row, "销售毛利率(%)", "毛利率", "gross_margin"))
        net_margin = self._to_float(self._first_present(indicator_row, "销售净利率(%)", "净利率", "net_margin"))
        current_ratio = self._to_float(self._first_present(indicator_row, "流动比率", "current_ratio"))
        quick_ratio = self._to_float(self._first_present(indicator_row, "速动比率", "quick_ratio"))
        asset_liability_ratio = self._to_float(self._first_present(indicator_row, "资产负债率(%)", "资产负债率", "asset_liability_ratio"))
        debt_to_equity = self._to_float(self._first_present(indicator_row, "产权比率", "debt_to_equity"))
        if debt_to_equity is None and total_liabilities is not None and equity not in (None, 0):
            debt_to_equity = round((total_liabilities / equity) * 100, 4)
        operating_cash_flow_to_net_profit = self._to_float(
            self._first_present(indicator_row, "经营现金净流量/净利润", "operating_cash_flow_to_net_profit")
        )
        data_date = self._normalize_date(self._first_present(indicator_row, "日期", "报告日", "date"))

        return self.success_result(
            stage="financial_indicator_snapshot",
            data={
                "stock_code": normalized_code,
                "exchange": self._infer_exchange(normalized_code),
                "roe": roe,
                "roa": roa,
                "gross_margin": gross_margin,
                "net_margin": net_margin,
                "current_ratio": current_ratio,
                "quick_ratio": quick_ratio,
                "asset_liability_ratio": asset_liability_ratio,
                "debt_to_equity": debt_to_equity,
                "operating_cash_flow_to_net_profit": operating_cash_flow_to_net_profit,
                "data_source": "akshare",
                "data_date": data_date,
            },
            source_fields={
                "financial_indicator": list(indicator_df.columns),
                "balance_sheet": list(balance_df.columns),
            },
            field_sources={
                "roe": ["akshare.financial_indicator"],
                "roa": ["akshare.financial_indicator"],
                "gross_margin": ["akshare.financial_indicator"],
                "net_margin": ["akshare.financial_indicator"],
                "current_ratio": ["akshare.financial_indicator"],
                "quick_ratio": ["akshare.financial_indicator"],
                "asset_liability_ratio": ["akshare.financial_indicator"],
                "debt_to_equity": ["akshare.financial_indicator.derived"],
                "operating_cash_flow_to_net_profit": ["akshare.financial_indicator"],
            },
            missing_fields=[
                field
                for field, value in {
                    "roe": roe,
                    "current_ratio": current_ratio,
                    "quick_ratio": quick_ratio,
                }.items()
                if value is None
            ],
        )

    @staticmethod
    def _find_search_match(df: pd.DataFrame, *, query: str) -> dict[str, Any] | None:
        if df.empty:
            return None

        normalized_query = str(query).strip()
        rows = df.to_dict(orient="records")
        for row in rows:
            name = str(row.get("name") or row.get("名称") or "").strip()
            code = str(row.get("code") or row.get("代码") or "").strip()
            if name == normalized_query or code == normalized_query:
                return row
        for row in rows:
            name = str(row.get("name") or row.get("名称") or "").strip()
            if normalized_query and normalized_query in name:
                return row
        return None

    def _map_identity_from_detail(
        self,
        df: pd.DataFrame,
        *,
        fallback_code: str,
        fallback_name: str | None = None,
    ):
        detail_map = self._frame_to_item_map(df)
        company_name = self._to_text(detail_map.get("股票简称") or detail_map.get("简称") or fallback_name)
        stock_code = self._normalize_stock_code(
            detail_map.get("股票代码") or detail_map.get("代码") or fallback_code
        )
        exchange = self._infer_exchange(stock_code)
        industry = self._to_text(detail_map.get("行业"))

        if not company_name or not stock_code:
            return self.error_result(stage="resolve_stock", message="akshare detail returned incomplete identity data")

        return self.success_result(
            stage="resolve_stock",
            data={
                "company_name": company_name,
                "stock_code": stock_code,
                "exchange": exchange,
                "industry": industry,
                "data_source": "akshare",
            },
            source_fields={"identity": list(df.columns)},
            field_sources={
                "company_name": ["akshare.identity"],
                "stock_code": ["akshare.identity"],
                "exchange": ["akshare.identity"],
                "industry": ["akshare.identity"],
            },
        )

    @staticmethod
    def _frame_to_item_map(df: pd.DataFrame) -> dict[str, Any]:
        if df.empty:
            return {}
        records = df.to_dict(orient="records")
        if {"item", "value"}.issubset(set(df.columns)):
            return {str(row.get("item")): row.get("value") for row in records}
        if {"项目", "值"}.issubset(set(df.columns)):
            return {str(row.get("项目")): row.get("值") for row in records}
        return records[0] if records else {}

    @staticmethod
    def _latest_row(df: pd.DataFrame) -> dict[str, Any]:
        if df.empty:
            return {}
        records = df.to_dict(orient="records")
        return records[-1] if records else {}

    @staticmethod
    def _first_present(row: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _normalize_stock_code(stock_code: Any) -> str:
        if not stock_code:
            return ""
        return str(stock_code).split(".")[0].strip().upper()

    @classmethod
    def _infer_exchange(cls, stock_code: str | None) -> str | None:
        normalized = cls._normalize_stock_code(stock_code)
        if not normalized:
            return None
        if normalized.startswith(("6", "9")):
            return "SH"
        if normalized.startswith(("0", "2", "3")):
            return "SZ"
        return None

    @classmethod
    def _to_stock_symbol(cls, stock_code: str) -> str:
        exchange = cls._infer_exchange(stock_code)
        prefix = "sh" if exchange == "SH" else "sz"
        return f"{prefix}{cls._normalize_stock_code(stock_code)}"

    @staticmethod
    def _to_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            if isinstance(value, str):
                cleaned = value.replace(",", "").replace("%", "").strip()
                return float(cleaned)
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_date(value: Any) -> str | None:
        if value in (None, ""):
            return None
        text = str(value).strip()
        if not text:
            return None
        return text[:10]

    def _map_exception(self, *, stage: str, exc: Exception):
        return self.error_result(
            stage=stage,
            message=str(exc),
            code="upstream_error",
            retriable=False,
        )
