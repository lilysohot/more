"""EastMoney provider for identity, market, valuation, and financial snapshot fields."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.services.financial_snapshot.providers.base import FinancialDataProvider


class EastMoneyProvider(FinancialDataProvider):
    def __init__(self) -> None:
        super().__init__(provider_name="eastmoney")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def resolve_stock(
        self,
        *,
        company_name: str | None = None,
        stock_code: str | None = None,
    ):
        normalized_code = self._normalize_stock_code(stock_code)
        if normalized_code:
            try:
                quote = await self._get_quote_data(normalized_code)
            except (httpx.HTTPError, ValueError) as exc:
                if not (company_name or "").strip():
                    return self._map_exception(stage="resolve_stock", exc=exc)
            else:
                result = self._map_identity_from_quote(quote, fallback_code=normalized_code)
                if result["success"]:
                    return result

        query = (company_name or "").strip()
        if not query:
            return self.error_result(stage="resolve_stock", message="company_name or stock_code is required")

        try:
            search_payload = await self._request_json(
                "https://searchapi.eastmoney.com/api/suggest/get",
                params={"input": query, "type": "14", "count": 5},
            )
        except (httpx.HTTPError, ValueError) as exc:
            return self._map_exception(stage="resolve_stock", exc=exc)
        search_result = self._map_identity_from_search(search_payload)
        if not search_result["success"]:
            return search_result

        resolved_code = search_result["data"].get("stock_code")
        if not resolved_code:
            return search_result

        try:
            quote = await self._get_quote_data(resolved_code)
        except (httpx.HTTPError, ValueError) as exc:
            return self._map_exception(stage="resolve_stock", exc=exc)
        quote_result = self._map_identity_from_quote(quote, fallback_code=resolved_code)
        if quote_result["success"]:
            return quote_result

        return search_result

    async def get_market_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        normalized_code = self._normalize_stock_code(stock_code or ts_code)
        if not normalized_code:
            return self.error_result(stage="market_snapshot", message="stock_code is required")

        try:
            quote = await self._get_quote_data(normalized_code)
        except (httpx.HTTPError, ValueError) as exc:
            return self._map_exception(stage="market_snapshot", exc=exc)
        data = quote.get("data") or {}
        close_price = self._normalize_price(data.get("f43"))
        data_date = self._normalize_timestamp(data.get("f124"))

        return self.success_result(
            stage="market_snapshot",
            data={
                "stock_code": normalized_code,
                "company_name": self._to_text(data.get("f58")),
                "exchange": self._infer_exchange(normalized_code),
                "close_price": close_price,
                "data_source": "eastmoney",
                "data_date": data_date,
            },
            source_fields={"market": ["f43", "f57", "f58", "f124"]},
            field_sources={
                "close_price": ["eastmoney.market"],
                "data_date": ["eastmoney.market"],
            },
            missing_fields=[
                field
                for field, value in {"close_price": close_price, "data_date": data_date}.items()
                if value is None
            ],
        )

    async def get_valuation_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        normalized_code = self._normalize_stock_code(stock_code or ts_code)
        if not normalized_code:
            return self.error_result(stage="valuation_snapshot", message="stock_code is required")

        try:
            quote = await self._get_quote_data(normalized_code)
        except (httpx.HTTPError, ValueError) as exc:
            return self._map_exception(stage="valuation_snapshot", exc=exc)
        data = quote.get("data") or {}
        market_cap = self._to_float(data.get("f116"))
        pe_ratio = self._to_float(data.get("f162"))
        pb_ratio = self._to_float(data.get("f167"))

        return self.success_result(
            stage="valuation_snapshot",
            data={
                "stock_code": normalized_code,
                "company_name": self._to_text(data.get("f58")),
                "exchange": self._infer_exchange(normalized_code),
                "market_cap": market_cap,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "data_source": "eastmoney",
                "data_date": self._normalize_timestamp(data.get("f124")),
            },
            source_fields={"valuation": ["f57", "f58", "f116", "f162", "f167", "f124"]},
            field_sources={
                "market_cap": ["eastmoney.valuation"],
                "pe_ratio": ["eastmoney.valuation"],
                "pb_ratio": ["eastmoney.valuation"],
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
        normalized_code = self._normalize_stock_code(stock_code or ts_code)
        if not normalized_code:
            return self.error_result(stage="financial_statement_snapshot", message="stock_code is required")

        try:
            payload = await self._get_financial_summary_data(normalized_code)
        except (httpx.HTTPError, ValueError) as exc:
            return self._map_exception(stage="financial_statement_snapshot", exc=exc)
        row = self._latest_row(payload)
        source_fields = {"financial_statement": list(row.keys())}

        revenue = self._to_amount(
            self._first_present(
                row,
                "revenue",
                "totalOperatingRevenue",
                "operatingRevenue",
                "totalOperateRevenue",
                "TOTALOPERATEREVE",
            )
        )
        net_profit = self._to_amount(
            self._first_present(
                row,
                "netProfit",
                "parentNetProfit",
                "netprofit",
                "PARENTNETPROFIT",
                "NETPROFIT",
            )
        )
        total_assets = self._to_amount(
            self._first_present(row, "totalAssets", "total_assets", "TOTALASSETS")
        )
        total_liabilities = self._to_amount(
            self._first_present(
                row,
                "totalLiabilities",
                "totalLiab",
                "total_liabilities",
                "TOTALLIABILITIES",
                "TOTALLIAB",
            )
        )
        equity = self._to_amount(
            self._first_present(
                row,
                "shareholderEquity",
                "equity",
                "totalEquity",
                "SHAREHOLDEREQUITY",
                "TOTALEQUITY",
            )
        )
        operating_cash_flow = self._to_amount(
            self._first_present(
                row,
                "operatingCashFlow",
                "operateCashFlow",
                "netCashFlowsOperAct",
                "OPERATINGCASHFLOW",
                "NETCASHFLOWSOPERACT",
            )
        )
        gross_margin = self._to_ratio(
            self._first_present(
                row,
                "grossMargin",
                "grossProfitMargin",
                "grossprofitMargin",
                "GROSSMARGIN",
                "GROSSPROFITMARGIN",
            )
        )
        data_date = self._normalize_date(
            self._first_present(
                row,
                "reportDate",
                "REPORT_DATE",
                "date",
                "endDate",
                "END_DATE",
            )
        )

        data = {
            "stock_code": normalized_code,
            "exchange": self._infer_exchange(normalized_code),
            "revenue": revenue,
            "net_profit": net_profit,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "equity": equity,
            "operating_cash_flow": operating_cash_flow,
            "gross_margin": gross_margin,
            "data_source": "eastmoney",
            "data_date": data_date,
        }

        return self.success_result(
            stage="financial_statement_snapshot",
            data=data,
            source_fields=source_fields,
            field_sources={
                "revenue": ["eastmoney.financial_statement"],
                "net_profit": ["eastmoney.financial_statement"],
                "total_assets": ["eastmoney.financial_statement"],
                "total_liabilities": ["eastmoney.financial_statement"],
                "equity": ["eastmoney.financial_statement"],
                "operating_cash_flow": ["eastmoney.financial_statement"],
                "gross_margin": ["eastmoney.financial_statement"],
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
        normalized_code = self._normalize_stock_code(stock_code or ts_code)
        if not normalized_code:
            return self.error_result(stage="financial_indicator_snapshot", message="stock_code is required")

        try:
            financial_summary_payload = await self._get_financial_summary_data(normalized_code)
            solvency_payload = await self._get_solvency_data(normalized_code)
        except (httpx.HTTPError, ValueError) as exc:
            return self._map_exception(stage="financial_indicator_snapshot", exc=exc)
        summary_row = self._latest_row(financial_summary_payload)
        solvency_row = self._latest_row(solvency_payload)

        total_liabilities = self._to_amount(
            self._first_present(
                summary_row,
                "totalLiabilities",
                "totalLiab",
                "total_liabilities",
                "TOTALLIABILITIES",
                "TOTALLIAB",
            )
        )
        equity = self._to_amount(
            self._first_present(
                summary_row,
                "shareholderEquity",
                "equity",
                "totalEquity",
                "SHAREHOLDEREQUITY",
                "TOTALEQUITY",
            )
        )
        asset_liability_ratio = self._to_ratio(
            self._first_present(
                summary_row,
                "assetLiabilityRatio",
                "debtToAssets",
                "ASSETLIABILITYRATIO",
                "DEBTTOASSETS",
            )
        )
        if asset_liability_ratio is None and total_liabilities is not None and equity is not None:
            total_assets = total_liabilities + equity
            if total_assets:
                asset_liability_ratio = round((total_liabilities / total_assets) * 100, 4)

        current_ratio = self._to_ratio(
            self._first_present(
                solvency_row,
                "currentRatio",
                "CURRENTRATIO",
            )
        )
        quick_ratio = self._to_ratio(
            self._first_present(
                solvency_row,
                "quickRatio",
                "QUICKRATIO",
            )
        )
        debt_to_equity = self._to_ratio(
            self._first_present(
                summary_row,
                "debtToEquity",
                "DEBTTOEQUITY",
            )
        )
        if debt_to_equity is None and total_liabilities is not None and equity not in (None, 0):
            debt_to_equity = round((total_liabilities / equity) * 100, 4)

        data = {
            "stock_code": normalized_code,
            "exchange": self._infer_exchange(normalized_code),
            "asset_liability_ratio": asset_liability_ratio,
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "debt_to_equity": debt_to_equity,
            "data_source": "eastmoney",
            "data_date": self._normalize_date(
                self._first_present(
                    summary_row,
                    "reportDate",
                    "REPORT_DATE",
                    "date",
                    "endDate",
                    "END_DATE",
                )
            ),
        }

        return self.success_result(
            stage="financial_indicator_snapshot",
            data=data,
            source_fields={
                "financial_summary": list(summary_row.keys()),
                "solvency": list(solvency_row.keys()),
            },
            field_sources={
                "asset_liability_ratio": ["eastmoney.financial_summary"],
                "current_ratio": ["eastmoney.solvency"],
                "quick_ratio": ["eastmoney.solvency"],
                "debt_to_equity": ["eastmoney.financial_summary.derived"],
            },
            missing_fields=[
                field
                for field, value in {
                    "asset_liability_ratio": asset_liability_ratio,
                    "current_ratio": current_ratio,
                    "quick_ratio": quick_ratio,
                }.items()
                if value is None
            ],
        )

    async def _get_quote_data(self, stock_code: str) -> dict[str, Any]:
        secid = self._to_secid(stock_code)
        return await self._request_json(
            "https://push2.eastmoney.com/api/qt/stock/get",
            params={
                "secid": secid,
                "fields": "f43,f57,f58,f116,f162,f167,f124",
            },
        )

    async def _get_financial_summary_data(self, stock_code: str) -> dict[str, Any]:
        return await self._request_json(
            "https://emweb.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew",
            params={"type": "0", "code": self._normalize_stock_code(stock_code)},
        )

    async def _get_solvency_data(self, stock_code: str) -> dict[str, Any]:
        return await self._request_json(
            "https://emweb.eastmoney.com/PC_HSF10/NewFinanceAnalysis/CzjlAjaxNew",
            params={"type": "0", "code": self._normalize_stock_code(stock_code)},
        )

    async def _request_json(self, url: str, *, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()

    def _map_exception(self, *, stage: str, exc: Exception):
        code = "upstream_error"
        retriable = True

        if isinstance(exc, httpx.TimeoutException):
            code = "timeout"
        elif isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code is not None and 300 <= status_code < 400:
                code = "redirect_response"
                retriable = False
            elif status_code is not None and 400 <= status_code < 500:
                code = "bad_response"
                retriable = False
        elif isinstance(exc, ValueError):
            code = "invalid_payload"
            retriable = False

        return self.error_result(
            stage=stage,
            message=str(exc),
            code=code,
            retriable=retriable,
        )

    def _map_identity_from_search(self, payload: dict[str, Any]):
        rows = payload.get("QuotationCodeTable", {}).get("Data") or []
        astock_rows = [row for row in rows if row.get("Classify") == "AStock"]
        row = (astock_rows or rows or [None])[0]
        if row is None:
            return self.error_result(stage="resolve_stock", message="eastmoney search returned no matches")

        stock_code = self._normalize_stock_code(row.get("Code"))
        company_name = self._to_text(row.get("Name"))
        exchange = "SH" if str(row.get("MktNum", "")) == "1" else "SZ"
        if not stock_code or not company_name:
            return self.error_result(stage="resolve_stock", message="eastmoney search returned incomplete identity data")

        return self.success_result(
            stage="resolve_stock",
            data={
                "company_name": company_name,
                "stock_code": stock_code,
                "exchange": exchange,
                "data_source": "eastmoney",
            },
            source_fields={"identity": ["Code", "Name", "MktNum"]},
            field_sources={
                "company_name": ["eastmoney.identity_search"],
                "stock_code": ["eastmoney.identity_search"],
                "exchange": ["eastmoney.identity_search"],
            },
        )

    def _map_identity_from_quote(self, payload: dict[str, Any], *, fallback_code: str):
        data = payload.get("data") or {}
        stock_code = self._normalize_stock_code(data.get("f57")) or fallback_code
        company_name = self._to_text(data.get("f58"))
        exchange = self._infer_exchange(stock_code)
        if not stock_code or not company_name:
            return self.error_result(stage="resolve_stock", message="eastmoney quote returned incomplete identity data")

        return self.success_result(
            stage="resolve_stock",
            data={
                "company_name": company_name,
                "stock_code": stock_code,
                "exchange": exchange,
                "data_source": "eastmoney",
            },
            source_fields={"identity": ["f57", "f58"]},
            field_sources={
                "company_name": ["eastmoney.identity_quote"],
                "stock_code": ["eastmoney.identity_quote"],
                "exchange": ["eastmoney.identity_quote"],
            },
        )

    @staticmethod
    def _latest_row(payload: dict[str, Any]) -> dict[str, Any]:
        rows = payload.get("data") or []
        if isinstance(rows, list) and rows:
            row = rows[0]
            if isinstance(row, dict):
                return row
        return {}

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
    def _to_secid(cls, stock_code: str) -> str:
        exchange = cls._infer_exchange(stock_code)
        market_prefix = "1" if exchange == "SH" else "0"
        return f"{market_prefix}.{cls._normalize_stock_code(stock_code)}"

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
                return float(value.replace(",", "").strip())
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _to_amount(cls, value: Any) -> float | None:
        return cls._to_float(value)

    @classmethod
    def _to_ratio(cls, value: Any) -> float | None:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.endswith("%"):
                return cls._to_float(stripped[:-1])
        return cls._to_float(value)

    @classmethod
    def _normalize_price(cls, value: Any) -> float | None:
        numeric = cls._to_float(value)
        if numeric is None:
            return None
        if isinstance(value, int):
            return round(numeric / 100, 4)
        return numeric

    @classmethod
    def _normalize_timestamp(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        try:
            return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d")
        except (TypeError, ValueError, OSError):
            return cls._to_text(value)

    @classmethod
    def _normalize_date(cls, value: Any) -> str | None:
        text = cls._to_text(value)
        if text is None:
            return None
        return text.replace("/", "-")
