import pandas as pd
import pytest

from skills.tushare_skill import TushareSkill


class FakeTushareApi:
    def __init__(self):
        self.calls = []

    def _record(self, method, kwargs):
        self.calls.append((method, kwargs))

    def stock_basic(self, **kwargs):
        self._record("stock_basic", kwargs)
        return pd.DataFrame(
            [
                {
                    "ts_code": "600089.SH",
                    "symbol": "600089",
                    "name": "特变电工",
                    "area": "新疆",
                    "industry": "电气设备",
                    "market": "主板",
                    "list_date": "19970618",
                }
            ]
        )

    def daily(self, **kwargs):
        self._record("daily", kwargs)
        return pd.DataFrame(
            [
                {"trade_date": "20240426", "open": 12.1, "high": 12.8, "low": 12.0, "close": 12.4, "vol": 1000, "amount": 12400},
                {"trade_date": "20240425", "open": 11.8, "high": 12.0, "low": 11.6, "close": 11.9, "vol": 900, "amount": 10710},
            ]
        )

    def daily_basic(self, **kwargs):
        self._record("daily_basic", kwargs)
        return pd.DataFrame(
            [
                {"trade_date": "20240426", "close": 12.4, "pe": 9.1, "pb": 1.2, "ps": 0.8, "total_mv": 6_200_000, "circ_mv": 5_100_000},
                {"trade_date": "20240425", "close": 11.9, "pe": 8.9, "pb": 1.1, "ps": 0.7, "total_mv": 6_000_000, "circ_mv": 5_000_000},
            ]
        )

    def fina_indicator(self, **kwargs):
        self._record("fina_indicator", kwargs)
        return pd.DataFrame(
            [
                {
                    "end_date": "20231231",
                    "roe": 15.5,
                    "roa": 6.2,
                    "eps": 1.23,
                    "grossprofit_margin": 27.4,
                    "netprofit_margin": 12.8,
                    "current_ratio": 1.6,
                    "quick_ratio": 1.1,
                    "inv_turn": 3.4,
                    "assets_turn": 0.7,
                    "debt_to_assets": 52.3,
                    "debt_to_eqt": 109.7,
                    "ocf_to_profit": 118.4,
                },
                {
                    "end_date": "20221231",
                    "roe": 11.0,
                    "roa": 4.4,
                    "eps": 0.87,
                    "grossprofit_margin": 21.0,
                    "netprofit_margin": 9.5,
                    "current_ratio": 1.3,
                    "quick_ratio": 0.9,
                },
            ]
        )

    def balancesheet_vip(self, **kwargs):
        self._record("balancesheet_vip", kwargs)
        return pd.DataFrame(
            [
                {
                    "end_date": "20231231",
                    "total_assets": 100_000,
                    "total_liab": 52_300,
                    "total_hldr_eqy_exc_min_int": 47_700,
                    "total_cur_assets": 30_000,
                    "total_cur_liab": 18_000,
                },
                {
                    "end_date": "20221231",
                    "total_assets": 90_000,
                    "total_liab": 50_000,
                    "total_hldr_eqy_exc_min_int": 40_000,
                    "total_cur_assets": 25_000,
                    "total_cur_liab": 17_000,
                },
            ]
        )

    def income_vip(self, **kwargs):
        self._record("income_vip", kwargs)
        return pd.DataFrame(
            [
                {"end_date": "20231231", "revenue": 20_000, "oper_cost": 14_520, "operate_profit": 3_100, "n_income_attr_p": 2_560, "basic_eps": 1.23},
                {"end_date": "20221231", "revenue": 18_000, "oper_cost": 14_220, "operate_profit": 2_500, "n_income_attr_p": 1_710, "basic_eps": 0.87},
            ]
        )

    def cashflow_vip(self, **kwargs):
        self._record("cashflow_vip", kwargs)
        return pd.DataFrame(
            [
                {"end_date": "20231231", "n_cashflow_act": 3_031, "n_cashflow_inv_act": -1_200, "n_cash_flows_fnc_act": 500},
                {"end_date": "20221231", "n_cashflow_act": 2_000, "n_cashflow_inv_act": -900, "n_cash_flows_fnc_act": 300},
            ]
        )


class FakeNonVipFallbackApi(FakeTushareApi):
    def balancesheet_vip(self, **kwargs):
        self._record("balancesheet_vip", kwargs)
        raise RuntimeError("vip balance sheet denied")

    def income_vip(self, **kwargs):
        self._record("income_vip", kwargs)
        raise RuntimeError("vip income denied")

    def cashflow_vip(self, **kwargs):
        self._record("cashflow_vip", kwargs)
        raise RuntimeError("vip cash flow denied")

    def balancesheet(self, **kwargs):
        self._record("balancesheet", kwargs)
        return pd.DataFrame(
            [
                {
                    "end_date": "20231231",
                    "total_assets": 100_000,
                    "total_liab": 52_300,
                    "total_hldr_eqy_exc_min_int": 47_700,
                    "total_cur_assets": 30_000,
                    "total_cur_liab": 18_000,
                }
            ]
        )

    def income(self, **kwargs):
        self._record("income", kwargs)
        return pd.DataFrame(
            [
                {"end_date": "20231231", "revenue": 20_000, "oper_cost": 14_520, "operate_profit": 3_100, "n_income_attr_p": 2_560, "basic_eps": 1.23}
            ]
        )

    def cashflow(self, **kwargs):
        self._record("cashflow", kwargs)
        return pd.DataFrame(
            [
                {"end_date": "20231231", "n_cashflow_act": 3_031, "n_cashflow_inv_act": -1_200, "n_cash_flows_fnc_act": 500}
            ]
        )


@pytest.mark.asyncio
async def test_collect_all_maps_actual_tushare_columns_and_reports_available_fields():
    skill = TushareSkill(token="test-token")
    skill.api = FakeTushareApi()
    skill.is_initialized = True

    data = await skill.collect_all(stock_code="600089", company_name="特变电工")

    assert data["company_name"] == "特变电工"
    assert data["stock_code"] == "600089"
    assert data["ts_code"] == "600089.SH"
    assert data["industry"] == "电气设备"
    assert data["revenue"] == 20_000
    assert data["net_profit"] == 2_560
    assert data["gross_margin"] == 27.4
    assert data["net_margin"] == 12.8
    assert data["roe"] == 15.5
    assert data["roa"] == 6.2
    assert data["total_assets"] == 100_000
    assert data["total_liabilities"] == 52_300
    assert data["equity"] == 47_700
    assert data["asset_liability_ratio"] == 52.3
    assert data["current_assets"] == 30_000
    assert data["current_liabilities"] == 18_000
    assert data["debt_to_equity"] == 109.7
    assert data["operating_cash_flow"] == 3_031
    assert data["financing_cash_flow"] == 500
    assert data["operating_cash_flow_to_net_profit"] == 118.4
    assert data["market_cap"] == 62_000_000_000
    assert data["pe_ratio"] == 9.1
    assert data["pb_ratio"] == 1.2
    assert data["close_price"] == 12.4
    assert data["data_date"] == "20240426"
    assert data["source_fields"]["financial"] == [
        "end_date",
        "roe",
        "roa",
        "eps",
        "grossprofit_margin",
        "netprofit_margin",
        "current_ratio",
        "quick_ratio",
        "inv_turn",
        "assets_turn",
        "debt_to_assets",
        "debt_to_eqt",
        "ocf_to_profit",
    ]
    assert data["missing_fields"] == []


@pytest.mark.asyncio
async def test_market_queries_use_recent_date_windows_instead_of_today_only():
    api = FakeTushareApi()
    skill = TushareSkill(token="test-token")
    skill.api = api
    skill.is_initialized = True

    await skill.collect_all(stock_code="600089", company_name="特变电工")

    daily_kwargs = next(kwargs for method, kwargs in api.calls if method == "daily")
    daily_basic_kwargs = next(kwargs for method, kwargs in api.calls if method == "daily_basic")
    assert "trade_date" not in daily_kwargs
    assert "trade_date" not in daily_basic_kwargs
    assert daily_kwargs["start_date"] <= daily_kwargs["end_date"]
    assert daily_basic_kwargs["start_date"] <= daily_basic_kwargs["end_date"]


@pytest.mark.asyncio
async def test_collect_all_falls_back_to_non_vip_financial_statement_apis():
    api = FakeNonVipFallbackApi()
    skill = TushareSkill(token="test-token")
    skill.api = api
    skill.is_initialized = True

    data = await skill.collect_all(stock_code="600089", company_name="特变电工")

    called_methods = [method for method, _ in api.calls]
    assert "balancesheet" in called_methods
    assert "income" in called_methods
    assert "cashflow" in called_methods
    assert data["revenue"] == 20_000
    assert data["net_profit"] == 2_560
    assert data["total_assets"] == 100_000
    assert data["operating_cash_flow"] == 3_031
