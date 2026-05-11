"""Tushare provider adapter for normalized financial snapshot fields."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from app.services.financial_snapshot.providers.base import FinancialDataProvider
from skills import get_tushare_skill


SkillFactory = Callable[..., Awaitable[Any]]


class TushareProvider(FinancialDataProvider):
    def __init__(self, *, skill_factory: SkillFactory = get_tushare_skill, token: str | None = None) -> None:
        super().__init__(provider_name="tushare")
        self._skill_factory = skill_factory
        self._token = token

    async def resolve_stock(
        self,
        *,
        company_name: str | None = None,
        stock_code: str | None = None,
    ):
        try:
            skill = await self._get_skill()
            payload = await skill.resolve_stock(stock_code=stock_code, company_name=company_name)
        except Exception as exc:
            return self._map_exception(stage="resolve_stock", exc=exc)

        source_fields = {"identity": list(payload.pop("_source_fields", []))}
        data = {
            "company_name": payload.get("name") or payload.get("company_name"),
            "stock_code": self._normalize_stock_code(payload.get("stock_code") or stock_code),
            "ts_code": payload.get("ts_code") or self._to_ts_code(stock_code),
            "exchange": payload.get("exchange"),
            "industry": payload.get("industry"),
            "data_source": "tushare",
        }
        if not data["company_name"] or not data["stock_code"]:
            return self.error_result(
                stage="resolve_stock",
                message="tushare identity data unavailable",
                code="unavailable",
                retriable=False,
                data=data,
                source_fields=source_fields,
                missing_fields=["company_name", "stock_code"],
            )

        return self.success_result(
            stage="resolve_stock",
            data=data,
            source_fields=source_fields,
            field_sources={
                "company_name": ["tushare.identity"],
                "stock_code": ["tushare.identity"],
                "ts_code": ["tushare.identity"],
                "exchange": ["tushare.identity"],
                "industry": ["tushare.identity"],
            },
        )

    async def get_market_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        try:
            skill = await self._get_skill()
            payload = await skill.get_daily_price(self._normalize_stock_code(stock_code or ts_code))
        except Exception as exc:
            return self._map_exception(stage="market_snapshot", exc=exc)

        source_fields = {"market": list(payload.pop("_source_fields", []))}
        close_price = self._to_float(payload.get("close"))
        data_date = self._to_text(payload.get("date"))
        data = {
            "stock_code": self._normalize_stock_code(stock_code or ts_code),
            "ts_code": ts_code or self._to_ts_code(stock_code),
            "close_price": close_price,
            "data_source": "tushare",
            "data_date": data_date,
        }
        missing_fields = [field for field, value in {"close_price": close_price, "data_date": data_date}.items() if value is None]
        if missing_fields:
            return self.error_result(
                stage="market_snapshot",
                message="tushare market data unavailable",
                code="unavailable",
                retriable=False,
                data=data,
                source_fields=source_fields,
                field_sources={"close_price": ["tushare.market"], "data_date": ["tushare.market"]},
                missing_fields=missing_fields,
            )

        return self.success_result(
            stage="market_snapshot",
            data=data,
            source_fields=source_fields,
            field_sources={"close_price": ["tushare.market"], "data_date": ["tushare.market"]},
        )

    async def get_valuation_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        try:
            skill = await self._get_skill()
            payload = await skill.get_valuation_data(self._normalize_stock_code(stock_code or ts_code))
        except Exception as exc:
            return self._map_exception(stage="valuation_snapshot", exc=exc)

        source_fields = {"valuation": list(payload.pop("_source_fields", []))}
        total_mv = self._to_float(payload.get("total_mv"))
        market_cap = total_mv * 10000 if total_mv is not None else None
        pe_ratio = self._to_float(payload.get("pe"))
        pb_ratio = self._to_float(payload.get("pb"))
        ps_ratio = self._to_float(payload.get("ps"))
        data = {
            "stock_code": self._normalize_stock_code(stock_code or ts_code),
            "ts_code": ts_code or self._to_ts_code(stock_code),
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "ps_ratio": ps_ratio,
            "close_price": self._to_float(payload.get("close")),
            "data_source": "tushare",
            "data_date": self._to_text(payload.get("trade_date")),
        }
        missing_fields = [field for field, value in {"market_cap": market_cap, "pe_ratio": pe_ratio, "pb_ratio": pb_ratio}.items() if value is None]
        if missing_fields:
            return self.error_result(
                stage="valuation_snapshot",
                message="tushare valuation data unavailable",
                code="unavailable",
                retriable=False,
                data=data,
                source_fields=source_fields,
                field_sources={
                    "market_cap": ["tushare.valuation"],
                    "pe_ratio": ["tushare.valuation"],
                    "pb_ratio": ["tushare.valuation"],
                    "ps_ratio": ["tushare.valuation"],
                },
                missing_fields=missing_fields,
            )

        return self.success_result(
            stage="valuation_snapshot",
            data=data,
            source_fields=source_fields,
            field_sources={
                "market_cap": ["tushare.valuation"],
                "pe_ratio": ["tushare.valuation"],
                "pb_ratio": ["tushare.valuation"],
                "ps_ratio": ["tushare.valuation"],
            },
        )

    async def get_financial_statement_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        try:
            skill = await self._get_skill()
            balance_sheet, income_statement, cash_flow = await asyncio.gather(
                skill.get_balance_sheet(self._normalize_stock_code(stock_code or ts_code)),
                skill.get_income_statement(self._normalize_stock_code(stock_code or ts_code)),
                skill.get_cash_flow(self._normalize_stock_code(stock_code or ts_code)),
            )
        except Exception as exc:
            return self._map_exception(stage="financial_statement_snapshot", exc=exc)

        source_fields = {
            "balance_sheet": list(balance_sheet.pop("_source_fields", [])),
            "income_statement": list(income_statement.pop("_source_fields", [])),
            "cash_flow": list(cash_flow.pop("_source_fields", [])),
        }
        data = {
            "stock_code": self._normalize_stock_code(stock_code or ts_code),
            "ts_code": ts_code or self._to_ts_code(stock_code),
            "revenue": self._to_float(income_statement.get("revenue")),
            "net_profit": self._to_float(income_statement.get("net_profit")),
            "total_assets": self._to_float(balance_sheet.get("total_assets")),
            "total_liabilities": self._to_float(balance_sheet.get("total_liabilities")),
            "equity": self._to_float(balance_sheet.get("total_equity")),
            "current_assets": self._to_float(balance_sheet.get("current_assets")),
            "current_liabilities": self._to_float(balance_sheet.get("current_liabilities")),
            "operating_cash_flow": self._to_float(cash_flow.get("operating_cf")),
            "investing_cash_flow": self._to_float(cash_flow.get("investing_cf")),
            "financing_cash_flow": self._to_float(cash_flow.get("financing_cf")),
            "data_source": "tushare",
            "data_date": self._to_text(
                income_statement.get("report_date")
                or balance_sheet.get("report_date")
                or cash_flow.get("report_date")
            ),
        }
        missing_fields = [
            field
            for field, value in {
                "revenue": data["revenue"],
                "net_profit": data["net_profit"],
                "total_assets": data["total_assets"],
                "total_liabilities": data["total_liabilities"],
                "equity": data["equity"],
            }.items()
            if value is None
        ]
        if all(not source_fields[key] for key in source_fields):
            return self.error_result(
                stage="financial_statement_snapshot",
                message="tushare financial statements unavailable or permission denied",
                code="permission_or_unavailable",
                retriable=False,
                data=data,
                source_fields=source_fields,
                missing_fields=missing_fields or ["revenue", "net_profit", "total_assets"],
            )

        return self.success_result(
            stage="financial_statement_snapshot",
            data=data,
            source_fields=source_fields,
            field_sources={
                "revenue": ["tushare.income_statement"],
                "net_profit": ["tushare.income_statement"],
                "total_assets": ["tushare.balance_sheet"],
                "total_liabilities": ["tushare.balance_sheet"],
                "equity": ["tushare.balance_sheet"],
                "operating_cash_flow": ["tushare.cash_flow"],
                "investing_cash_flow": ["tushare.cash_flow"],
                "financing_cash_flow": ["tushare.cash_flow"],
            },
            missing_fields=missing_fields,
        )

    async def get_financial_indicator_snapshot(self, *, stock_code: str, ts_code: str | None = None):
        try:
            skill = await self._get_skill()
            payload = await skill.get_financial_data(self._normalize_stock_code(stock_code or ts_code))
        except Exception as exc:
            return self._map_exception(stage="financial_indicator_snapshot", exc=exc)

        source_fields = {"financial_indicator": list(payload.pop("_source_fields", []))}
        data = {
            "stock_code": self._normalize_stock_code(stock_code or ts_code),
            "ts_code": ts_code or self._to_ts_code(stock_code),
            "roe": self._to_float(payload.get("roe")),
            "roa": self._to_float(payload.get("roa")),
            "gross_margin": self._to_float(payload.get("gross_profit_rate")),
            "net_margin": self._to_float(payload.get("net_profit_ratio")),
            "current_ratio": self._to_float(payload.get("current_ratio")),
            "quick_ratio": self._to_float(payload.get("quick_ratio")),
            "asset_liability_ratio": self._to_float(payload.get("asset_liability_ratio")),
            "debt_to_equity": self._to_float(payload.get("debt_to_equity")),
            "operating_cash_flow_to_net_profit": self._to_float(payload.get("operating_cash_flow_to_net_profit")),
            "data_source": "tushare",
            "data_date": self._to_text(payload.get("report_date")),
        }
        if not source_fields["financial_indicator"]:
            return self.error_result(
                stage="financial_indicator_snapshot",
                message="tushare financial indicators unavailable or permission denied",
                code="permission_or_unavailable",
                retriable=False,
                data=data,
                source_fields=source_fields,
                missing_fields=["roe", "current_ratio", "quick_ratio"],
            )

        missing_fields = [
            field
            for field, value in {
                "roe": data["roe"],
                "current_ratio": data["current_ratio"],
                "quick_ratio": data["quick_ratio"],
            }.items()
            if value is None
        ]
        return self.success_result(
            stage="financial_indicator_snapshot",
            data=data,
            source_fields=source_fields,
            field_sources={
                "roe": ["tushare.financial_indicator"],
                "roa": ["tushare.financial_indicator"],
                "gross_margin": ["tushare.financial_indicator"],
                "net_margin": ["tushare.financial_indicator"],
                "current_ratio": ["tushare.financial_indicator"],
                "quick_ratio": ["tushare.financial_indicator"],
                "asset_liability_ratio": ["tushare.financial_indicator"],
                "debt_to_equity": ["tushare.financial_indicator"],
                "operating_cash_flow_to_net_profit": ["tushare.financial_indicator"],
            },
            missing_fields=missing_fields,
        )

    async def _get_skill(self):
        return await self._skill_factory(token=self._token)

    def _map_exception(self, *, stage: str, exc: Exception):
        code = "permission_denied" if isinstance(exc, PermissionError) else "upstream_error"
        return self.error_result(
            stage=stage,
            message=str(exc),
            code=code,
            retriable=False if isinstance(exc, PermissionError) else True,
        )

    @staticmethod
    def _normalize_stock_code(stock_code: Any) -> str:
        if not stock_code:
            return ""
        return str(stock_code).split(".")[0].strip().upper()

    @classmethod
    def _to_ts_code(cls, stock_code: Any) -> str | None:
        normalized = cls._normalize_stock_code(stock_code)
        if not normalized:
            return None
        if normalized.startswith(("6", "9")):
            return f"{normalized}.SH"
        return f"{normalized}.SZ"

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
            return float(value)
        except (TypeError, ValueError):
            return None
