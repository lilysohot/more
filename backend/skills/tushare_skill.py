"""
Tushare Skill Module

东方财富财务数据 Skill，基于 Tushare 数据接口实现。
用于采集股票财务数据、估值指标、公司基本面等信息。

主要功能：
- 股票信息查询
- 财务指标数据
- 估值指标数据
- 财务报表数据

使用示例：
    from skills.tushare_skill import TushareSkill
    
    skill = TushareSkill()
    # 初始化（免费版不需要token）
    await skill.initialize()
    
    # 获取股票基本信息
    stock_info = await skill.get_stock_info("600089")
    
    # 获取财务指标
    financial_data = await skill.get_financial_data("600089")
    
    # 获取估值指标
    valuation_data = await skill.get_valuation_data("600089")
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Tushare 常用接口
# 免费版可用的接口：
# - stock_basic: 股票列表
# - daily: 每日行情
# - financial_data: 财务数据（部分）
# - coai: 偿债能力（部分免费）
# - prox: 盈利能力（部分免费）
# - york: 运营能力（部分免费）
# - dexp: 成长能力（部分免费）


class TushareSkill:
    """
    Tushare 数据采集 Skill
    
    基于 Tushare 数据接口封装，提供标准化的股票数据采集能力。
    
    Attributes:
        token: Tushare Pro API Token（免费版可为空）
        api: Tushare API 实例
        is_initialized: 是否已初始化
    """
    
    def __init__(self, token: str = None):
        """
        初始化 Tushare Skill
        
        Args:
            token: Tushare Pro API Token
                  免费版不需要token，但功能受限
                  Pro版需要申请：https://tushare.pro/
        """
        self.token = token or os.getenv("TUSHARE_TOKEN")
        self.api = None
        self.is_initialized = False
        self._stock_basic_cache = None

    @staticmethod
    def _to_ts_code(stock_code: str) -> str:
        """Normalize plain stock code to Tushare ts_code format."""
        if not stock_code:
            return ""

        normalized = str(stock_code).strip().upper()
        if "." in normalized:
            return normalized

        if normalized.startswith(("6", "9")):
            return f"{normalized}.SH"

        return f"{normalized}.SZ"

    @staticmethod
    def _to_stock_code(stock_code: str) -> str:
        """Extract 6-digit stock code from ts_code/plain code."""
        if not stock_code:
            return ""
        return str(stock_code).split(".")[0].strip()

    @staticmethod
    def _to_exchange(ts_code: str) -> Optional[str]:
        if not ts_code or "." not in ts_code:
            return None

        suffix = ts_code.split(".")[-1].upper()
        if suffix == "SH":
            return "SH"
        if suffix == "SZ":
            return "SZ"
        return suffix

    @staticmethod
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        try:
            return bool(value != value)
        except Exception:
            return False

    @staticmethod
    def _to_python(value: Any) -> Any:
        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                return value
        return value

    @staticmethod
    def _field_names(df) -> list[str]:
        if df is None:
            return []
        return [str(column) for column in getattr(df, "columns", [])]

    @classmethod
    def _first_present(cls, row: dict, *keys: str) -> Any:
        for key in keys:
            value = row.get(key)
            if not cls._is_missing(value):
                return cls._to_python(value)
        return None

    @classmethod
    def _latest_row(cls, df, *date_fields: str) -> dict[str, Any]:
        if df is None or len(df) == 0:
            return {}

        latest_df = df
        for field in date_fields:
            if field in df.columns:
                latest_df = df.sort_values(by=field, ascending=False)
                break

        return {
            str(key): cls._to_python(value)
            for key, value in latest_df.iloc[0].to_dict().items()
        }

    @staticmethod
    def _recent_date_window(days: int = 45) -> tuple[str, str]:
        end = datetime.now()
        start = end - timedelta(days=days)
        return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")

    def _query_first_available(self, method_names: tuple[str, ...], **kwargs):
        last_error = None
        empty_df = None

        for method_name in method_names:
            method = getattr(self.api, method_name, None)
            if method is None:
                continue

            try:
                df = method(**kwargs)
                if df is not None and len(df) > 0:
                    return df
                empty_df = df
            except Exception as e:
                last_error = e
                logger.warning(f"Tushare {method_name} 查询失败，尝试下一个接口: {e}")

        if empty_df is not None:
            return empty_df
        if last_error is not None:
            raise last_error
        return None

    async def resolve_stock(self, stock_code: str = None, company_name: str = None) -> Dict[str, Any]:
        """Resolve stock identity from stock code or company name."""
        if not self.is_initialized:
            await self.initialize()

        try:
            if stock_code:
                ts_code = self._to_ts_code(stock_code)
                stock_info = await self.get_stock_info(ts_code)
                if stock_info:
                    return stock_info

            if not company_name:
                return {}

            df = await self._get_stock_basic_cache()

            if df is None or len(df) == 0:
                return {}

            exact_match = df[df["name"] == company_name]
            if len(exact_match) == 0:
                exact_match = df[df["name"].astype(str).str.contains(company_name, na=False)]

            if len(exact_match) == 0:
                return {}

            row = exact_match.iloc[0]
            return {
                "stock_code": row.get("symbol") or self._to_stock_code(row.get("ts_code", "")),
                "ts_code": row.get("ts_code"),
                "name": row.get("name"),
                "area": row.get("area"),
                "industry": row.get("industry"),
                "market": row.get("market"),
                "list_date": row.get("list_date"),
                "exchange": self._to_exchange(row.get("ts_code")),
            }
        except Exception as e:
            logger.warning(f"解析股票信息失败 stock_code={stock_code} company_name={company_name}: {e}")
            return {}

    async def _get_stock_basic_cache(self):
        if self._stock_basic_cache is not None:
            return self._stock_basic_cache

        df = self.api.stock_basic(
            exchange="",
            list_status="L",
            fields="ts_code,symbol,name,area,industry,market,list_date"
        )
        self._stock_basic_cache = df
        return df
        
    async def initialize(self) -> bool:
        """
        初始化 Tushare API 连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            import tushare as ts
            
            if self.token:
                ts.set_token(self.token)
            else:
                logger.error("Tushare 初始化失败: 缺少 TUSHARE_TOKEN")
                return False

            self.api = ts.pro_api(self.token)
            self.is_initialized = True
            logger.info("Tushare Skill 初始化成功")
            return True
            
        except ImportError:
            logger.error("Tushare 未安装，请运行: pip install tushare")
            return False
        except Exception as e:
            logger.error(f"Tushare 初始化失败: {e}")
            return False
    
    async def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票基本信息
        
        Args:
            stock_code: 股票代码，如 "600089" 或 "000001"
        
        Returns:
            dict: 股票基本信息字典
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            ts_code = self._to_ts_code(stock_code)
            # 查询股票基本信息
            df = self.api.stock_basic(
                ts_code=ts_code,
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            source_fields = self._field_names(df)
            
            if df is not None and len(df) > 0:
                row = self._latest_row(df, "list_date")
                return {
                    "stock_code": self._first_present(row, 'symbol') or self._to_stock_code(row.get('ts_code', '')),
                    "ts_code": self._first_present(row, 'ts_code'),
                    "name": self._first_present(row, 'name'),
                    "area": self._first_present(row, 'area'),
                    "industry": self._first_present(row, 'industry'),
                    "market": self._first_present(row, 'market'),
                    "list_date": self._first_present(row, 'list_date'),
                    "exchange": self._to_exchange(row.get('ts_code')),
                    "_source_fields": source_fields,
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取股票信息失败 {stock_code}: {e}")
            return {}
    
    async def get_daily_price(self, stock_code: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        获取每日行情数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期，格式 YYYYMMDD
            end_date: 结束日期，格式 YYYYMMDD
        
        Returns:
            dict: 最新行情数据
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            ts_code = self._to_ts_code(stock_code)
            if not end_date:
                _, end_date = self._recent_date_window()
            if not start_date:
                try:
                    end = datetime.strptime(end_date, "%Y%m%d")
                except ValueError:
                    end = datetime.now()
                start_date = (end - timedelta(days=45)).strftime('%Y%m%d')
            
            # Query a recent range instead of today's exact date; weekends and holidays return no rows.
            df = self.api.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
            source_fields = self._field_names(df)
            
            if df is not None and len(df) > 0:
                row = self._latest_row(df, 'trade_date')
                return {
                    "date": self._first_present(row, 'trade_date'),
                    "open": self._first_present(row, 'open'),
                    "high": self._first_present(row, 'high'),
                    "low": self._first_present(row, 'low'),
                    "close": self._first_present(row, 'close'),
                    "volume": self._first_present(row, 'vol'),
                    "amount": self._first_present(row, 'amount'),
                    "_source_fields": source_fields,
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取行情数据失败 {stock_code}: {e}")
            return {}
    
    async def get_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取财务指标数据
        
        包含盈利能力、偿债能力、运营能力、成长能力等指标。
        免费版可能有限制。
        
        Args:
            stock_code: 股票代码
        
        Returns:
            dict: 财务指标数据
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            ts_code = self._to_ts_code(stock_code)
            start_date, end_date = self._recent_date_window(days=365 * 5)
            
            # 获取财务指标数据
            df = self.api.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
            source_fields = self._field_names(df)
            
            if df is not None and len(df) > 0:
                latest = self._latest_row(df, 'end_date', 'report_date', 'ann_date')
                
                return {
                    "ts_code": ts_code,
                    "report_date": self._first_present(latest, 'end_date', 'report_date', 'ann_date'),
                    # 盈利能力
                    "roe": self._first_present(latest, 'roe', 'roe_waa', 'q_roe'),
                    "net_profit_ratio": self._first_present(latest, 'netprofit_margin', 'net_profit_ratio', 'q_netprofit_margin'),
                    "gross_profit_rate": self._first_present(latest, 'grossprofit_margin', 'gross_profit_rate', 'q_gsprofit_margin'),
                    "eps": self._first_present(latest, 'eps', 'basic_eps', 'q_eps'),
                    "roa": self._first_present(latest, 'roa', 'roa2_yearly', 'q_npta'),
                    # 偿债能力
                    "current_ratio": self._first_present(latest, 'current_ratio'),
                    "quick_ratio": self._first_present(latest, 'quick_ratio'),
                    # 运营能力
                    "inventory_turnover": self._first_present(latest, 'inv_turn', 'inventory_turnover'),
                    "total_asset_turnover": self._first_present(latest, 'assets_turn', 'total_asset_turnover', 'total_fa_trun'),
                    "asset_liability_ratio": self._first_present(latest, 'debt_to_assets', 'asset_liability_ratio'),
                    "debt_to_equity": self._first_present(latest, 'debt_to_eqt', 'debt_to_equity'),
                    "operating_cash_flow_to_net_profit": self._first_present(latest, 'ocf_to_profit', 'operating_cash_flow_to_net_profit'),
                    "_source_fields": source_fields,
                }
            return {}
            
        except Exception as e:
            logger.warning(f"获取财务数据失败（免费版受限）{stock_code}: {e}")
            return {}
    
    async def get_valuation_data(self, stock_code: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        获取估值指标数据
        
        Args:
            stock_code: 股票代码
        
        Returns:
            dict: 估值指标数据
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            ts_code = self._to_ts_code(stock_code)
            if not end_date:
                _, end_date = self._recent_date_window()
            if not start_date:
                try:
                    end = datetime.strptime(end_date, "%Y%m%d")
                except ValueError:
                    end = datetime.now()
                start_date = (end - timedelta(days=45)).strftime('%Y%m%d')
            
            # 获取每日指标（包含PE、PB等）
            df = self.api.daily_basic(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )
            source_fields = self._field_names(df)
            
            if df is not None and len(df) > 0:
                row = self._latest_row(df, 'trade_date')
                return {
                    "ts_code": ts_code,
                    "trade_date": self._first_present(row, 'trade_date'),
                    "close": self._first_present(row, 'close'),
                    "pe": self._first_present(row, 'pe', 'pe_ttm'),
                    "pb": self._first_present(row, 'pb'),
                    "ps": self._first_present(row, 'ps', 'ps_ttm'),
                    "total_mv": self._first_present(row, 'total_mv'),  # 总市值（万元）
                    "circ_mv": self._first_present(row, 'circ_mv'),    # 流通市值（万元）
                    "_source_fields": source_fields,
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取估值数据失败 {stock_code}: {e}")
            return {}
    
    async def get_balance_sheet(self, stock_code: str, period: str = None) -> Dict[str, Any]:
        """
        获取资产负债表数据
        
        Args:
            stock_code: 股票代码
            period: 报告期，格式 YYYMMDD，如 "20230930"
        
        Returns:
            dict: 资产负债表关键数据
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            ts_code = self._to_ts_code(stock_code)
            
            # VIP permission is not guaranteed; use the normal endpoint as fallback.
            df = self._query_first_available(
                ("balancesheet_vip", "balancesheet"),
                ts_code=ts_code,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            source_fields = self._field_names(df)
            
            if df is not None and len(df) > 0:
                latest = self._latest_row(df, 'end_date', 'report_date', 'ann_date')
                total_assets = self._first_present(latest, 'total_assets')
                total_liabilities = self._first_present(latest, 'total_liab', 'total_liabilities')
                asset_liability_ratio = self._first_present(latest, 'debt_to_assets', 'asset_liability_ratio')
                if (
                    self._is_missing(asset_liability_ratio)
                    and not self._is_missing(total_assets)
                    and total_assets != 0
                    and not self._is_missing(total_liabilities)
                ):
                    asset_liability_ratio = (total_liabilities / total_assets) * 100
                
                return {
                    "ts_code": ts_code,
                    "report_date": self._first_present(latest, 'end_date', 'report_date', 'ann_date'),
                    "total_assets": total_assets,      # 总资产
                    "total_liabilities": total_liabilities,  # 总负债
                    "total_equity": self._first_present(latest, 'total_hldr_eqy_exc_min_int', 'total_hldr_eqy_inc_min_int', 'total_eq', 'total_equity'),  # 股东权益
                    "current_assets": self._first_present(latest, 'total_cur_assets', 'current_assets'),
                    "current_liabilities": self._first_present(latest, 'total_cur_liab', 'current_liabilities'),
                    "asset_liability_ratio": asset_liability_ratio,  # 资产负债率
                    "_source_fields": source_fields,
                }
            return {}
            
        except Exception as e:
            logger.warning(f"获取资产负债表失败 {stock_code}: {e}")
            return {}
    
    async def get_income_statement(self, stock_code: str) -> Dict[str, Any]:
        """
        获取利润表数据
        
        Args:
            stock_code: 股票代码
        
        Returns:
            dict: 利润表关键数据
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            ts_code = self._to_ts_code(stock_code)
            
            # VIP permission is not guaranteed; use the normal endpoint as fallback.
            df = self._query_first_available(
                ("income_vip", "income"),
                ts_code=ts_code,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            source_fields = self._field_names(df)
            
            if df is not None and len(df) > 0:
                latest = self._latest_row(df, 'end_date', 'report_date', 'ann_date')
                
                return {
                    "ts_code": ts_code,
                    "report_date": self._first_present(latest, 'end_date', 'report_date', 'ann_date'),
                    "revenue": self._first_present(latest, 'revenue', 'total_revenue'),  # 营业收入
                    "operating_cost": self._first_present(latest, 'oper_cost', 'operating_cost'),  # 营业成本
                    "operating_profit": self._first_present(latest, 'operate_profit', 'op_profit', 'operating_profit'),  # 营业利润
                    "net_profit": self._first_present(latest, 'n_income_attr_p', 'n_income', 'net_profit'),  # 净利润
                    "eps": self._first_present(latest, 'basic_eps', 'diluted_eps', 'eps'),  # 每股收益
                    "_source_fields": source_fields,
                }
            return {}
            
        except Exception as e:
            logger.warning(f"获取利润表失败 {stock_code}: {e}")
            return {}
    
    async def get_cash_flow(self, stock_code: str) -> Dict[str, Any]:
        """
        获取现金流量表数据
        
        Args:
            stock_code: 股票代码
        
        Returns:
            dict: 现金流量表关键数据
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            ts_code = self._to_ts_code(stock_code)
            
            # VIP permission is not guaranteed; use the normal endpoint as fallback.
            df = self._query_first_available(
                ("cashflow_vip", "cashflow"),
                ts_code=ts_code,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            source_fields = self._field_names(df)
            
            if df is not None and len(df) > 0:
                latest = self._latest_row(df, 'end_date', 'report_date', 'ann_date')
                
                return {
                    "ts_code": ts_code,
                    "report_date": self._first_present(latest, 'end_date', 'report_date', 'ann_date'),
                    "operating_cf": self._first_present(latest, 'n_cashflow_act'),  # 经营活动现金流
                    "investing_cf": self._first_present(latest, 'n_cashflow_inv_act'),  # 投资活动现金流
                    "financing_cf": self._first_present(latest, 'n_cash_flows_fnc_act', 'n_cashflow_fin_act'),  # 筹资活动现金流
                    "_source_fields": source_fields,
                }
            return {}
            
        except Exception as e:
            logger.warning(f"获取现金流量表失败 {stock_code}: {e}")
            return {}
    
    async def collect_all(self, stock_code: str = None, company_name: str = None) -> Dict[str, Any]:
        """
        采集股票全部数据
        
        综合采集股票信息、财务数据、估值数据等。
        
        Args:
            stock_code: 股票代码
        
        Returns:
            dict: 完整的股票数据
        """
        if not self.is_initialized:
            await self.initialize()

        resolved = await self.resolve_stock(stock_code=stock_code, company_name=company_name)
        resolved_stock_code = resolved.get("stock_code") or self._to_stock_code(stock_code)
        resolved_ts_code = resolved.get("ts_code") or self._to_ts_code(resolved_stock_code)

        if not resolved_stock_code:
            raise ValueError(f"Unable to resolve stock for company_name={company_name} stock_code={stock_code}")

        stock_info, daily_price, valuation, financial, balance_sheet, income, cash_flow = await asyncio.gather(
            self.get_stock_info(resolved_ts_code),
            self.get_daily_price(resolved_stock_code),
            self.get_valuation_data(resolved_stock_code),
            self.get_financial_data(resolved_stock_code),
            self.get_balance_sheet(resolved_stock_code),
            self.get_income_statement(resolved_stock_code),
            self.get_cash_flow(resolved_stock_code),
        )

        source_fields = {
            "stock_info": stock_info.pop("_source_fields", []),
            "daily_price": daily_price.pop("_source_fields", []),
            "valuation": valuation.pop("_source_fields", []),
            "financial": financial.pop("_source_fields", []),
            "balance_sheet": balance_sheet.pop("_source_fields", []),
            "income": income.pop("_source_fields", []),
            "cash_flow": cash_flow.pop("_source_fields", []),
        }

        total_assets = balance_sheet.get("total_assets")
        total_liabilities = balance_sheet.get("total_liabilities")
        asset_liability_ratio = self._first_present(
            {
                "financial": financial.get("asset_liability_ratio"),
                "balance_sheet": balance_sheet.get("asset_liability_ratio"),
            },
            "financial",
            "balance_sheet",
        )
        if (
            self._is_missing(asset_liability_ratio)
            and not self._is_missing(total_assets)
            and total_assets != 0
            and not self._is_missing(total_liabilities)
        ):
            asset_liability_ratio = (total_liabilities / total_assets) * 100

        total_mv = valuation.get("total_mv")
        market_cap = total_mv * 10000 if not self._is_missing(total_mv) else None

        result = {
            "company_name": stock_info.get("name") or resolved.get("name") or company_name,
            "stock_code": stock_info.get("stock_code") or resolved_stock_code,
            "ts_code": stock_info.get("ts_code") or resolved_ts_code,
            "exchange": stock_info.get("exchange") or resolved.get("exchange"),
            "industry": stock_info.get("industry") or resolved.get("industry"),
            "revenue": income.get("revenue"),
            "net_profit": income.get("net_profit"),
            "gross_margin": financial.get("gross_profit_rate"),
            "net_margin": financial.get("net_profit_ratio"),
            "roe": financial.get("roe"),
            "roa": financial.get("roa"),
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "equity": balance_sheet.get("total_equity"),
            "asset_liability_ratio": asset_liability_ratio,
            "debt_to_equity": financial.get("debt_to_equity"),
            "current_assets": balance_sheet.get("current_assets"),
            "current_liabilities": balance_sheet.get("current_liabilities"),
            "current_ratio": financial.get("current_ratio"),
            "quick_ratio": financial.get("quick_ratio"),
            "operating_cash_flow": cash_flow.get("operating_cf"),
            "investing_cash_flow": cash_flow.get("investing_cf"),
            "financing_cash_flow": cash_flow.get("financing_cf"),
            "operating_cash_flow_to_net_profit": financial.get("operating_cash_flow_to_net_profit"),
            "market_cap": market_cap,
            "pe_ratio": valuation.get("pe"),
            "pb_ratio": valuation.get("pb"),
            "ps_ratio": valuation.get("ps"),
            "close_price": daily_price.get("close"),
            "data_source": "tushare",
            "data_date": valuation.get("trade_date")
            or daily_price.get("date")
            or income.get("report_date")
            or balance_sheet.get("report_date")
            or datetime.now().strftime("%Y-%m-%d"),
            "source_fields": source_fields,
        }

        tracked_fields = (
            "revenue",
            "net_profit",
            "gross_margin",
            "net_margin",
            "roe",
            "roa",
            "total_assets",
            "total_liabilities",
            "equity",
            "asset_liability_ratio",
            "debt_to_equity",
            "current_assets",
            "current_liabilities",
            "current_ratio",
            "quick_ratio",
            "operating_cash_flow",
            "investing_cash_flow",
            "financing_cash_flow",
            "operating_cash_flow_to_net_profit",
            "market_cap",
            "pe_ratio",
            "pb_ratio",
            "ps_ratio",
            "close_price",
        )
        result["missing_fields"] = [field for field in tracked_fields if self._is_missing(result.get(field))]
        
        logger.info(f"Tushare 数据采集完成: {result['stock_code']}")
        return result


# 单例模式，方便复用
_tushare_skill_instance: Optional[TushareSkill] = None


async def get_tushare_skill(token: str = None) -> TushareSkill:
    """
    获取 Tushare Skill 单例
    
    Args:
        token: Tushare Pro API Token
    
    Returns:
        TushareSkill 实例
    """
    global _tushare_skill_instance
    
    if _tushare_skill_instance is None or (token and _tushare_skill_instance.token != token):
        _tushare_skill_instance = TushareSkill(token)
        await _tushare_skill_instance.initialize()
    elif not _tushare_skill_instance.is_initialized:
        await _tushare_skill_instance.initialize()
    
    return _tushare_skill_instance
