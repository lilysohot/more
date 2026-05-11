"""Abstract provider contract for normalized financial snapshot data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.financial_snapshot.types import (
    CompanyFinancialSnapshot,
    FieldSources,
    ProviderErrorInfo,
    ProviderResult,
    SourceFields,
)


class FinancialDataProvider(ABC):
    """Common async contract for external financial data providers."""

    provider_name: str

    def __init__(self, provider_name: str | None = None) -> None:
        inferred_name = self.__class__.__name__.removesuffix("Provider").lower()
        self.provider_name = provider_name or getattr(self, "provider_name", inferred_name)

    @abstractmethod
    async def resolve_stock(
        self,
        *,
        company_name: str | None = None,
        stock_code: str | None = None,
    ) -> ProviderResult:
        """Resolve stock identity information."""

    @abstractmethod
    async def get_market_snapshot(
        self,
        *,
        stock_code: str,
        ts_code: str | None = None,
    ) -> ProviderResult:
        """Fetch market quote fields such as close price or trade date."""

    @abstractmethod
    async def get_valuation_snapshot(
        self,
        *,
        stock_code: str,
        ts_code: str | None = None,
    ) -> ProviderResult:
        """Fetch valuation fields such as market cap and PE."""

    @abstractmethod
    async def get_financial_statement_snapshot(
        self,
        *,
        stock_code: str,
        ts_code: str | None = None,
    ) -> ProviderResult:
        """Fetch balance sheet, income statement, and cash-flow fields."""

    @abstractmethod
    async def get_financial_indicator_snapshot(
        self,
        *,
        stock_code: str,
        ts_code: str | None = None,
    ) -> ProviderResult:
        """Fetch derived financial indicators such as ROE or current ratio."""

    def success_result(
        self,
        *,
        stage: str,
        data: CompanyFinancialSnapshot | None = None,
        source_fields: SourceFields | None = None,
        field_sources: FieldSources | None = None,
        missing_fields: list[str] | None = None,
        errors: list[ProviderErrorInfo] | None = None,
    ) -> ProviderResult:
        return {
            "provider": self.provider_name,
            "stage": stage,
            "success": True,
            "data": data or {},
            "source_fields": dict(source_fields or {}),
            "field_sources": dict(field_sources or {}),
            "missing_fields": list(missing_fields or []),
            "errors": list(errors or []),
        }

    def error_result(
        self,
        *,
        stage: str,
        message: str,
        code: str | None = None,
        retriable: bool | None = None,
        data: CompanyFinancialSnapshot | None = None,
        source_fields: SourceFields | None = None,
        field_sources: FieldSources | None = None,
        missing_fields: list[str] | None = None,
    ) -> ProviderResult:
        return {
            "provider": self.provider_name,
            "stage": stage,
            "success": False,
            "data": data or {},
            "source_fields": dict(source_fields or {}),
            "field_sources": dict(field_sources or {}),
            "missing_fields": list(missing_fields or []),
            "errors": [
                {
                    "provider": self.provider_name,
                    "stage": stage,
                    "message": message,
                    "code": code,
                    "retriable": retriable,
                }
            ],
        }
