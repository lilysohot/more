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

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

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
        self.token = token
        self.api = None
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """
        初始化 Tushare API 连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            import tushare as ts
            
            if self.token:
                # Pro版设置token
                ts.set_token(self.token)
                
            self.api = ts.pro_api(self.token) if self.token else ts.pro_api()
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
            # 查询股票基本信息
            df = self.api.stock_basic(
                ts_code=stock_code,
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
            if df is not None and len(df) > 0:
                row = df.iloc[0]
                return {
                    "stock_code": row.get('symbol') or row.get('ts_code', '').split('.')[0],
                    "ts_code": row.get('ts_code'),
                    "name": row.get('name'),
                    "area": row.get('area'),
                    "industry": row.get('industry'),
                    "market": row.get('market'),
                    "list_date": row.get('list_date'),
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
            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"
            
            # 获取最新行情
            df = self.api.daily(
                ts_code=ts_code,
                start_date=start_date or (datetime.now().strftime('%Y%m%d')),
                end_date=end_date or (datetime.now().strftime('%Y%m%d'))
            )
            
            if df is not None and len(df) > 0:
                row = df.iloc[-1]  # 取最新一条
                return {
                    "date": row.get('trade_date'),
                    "open": row.get('open'),
                    "high": row.get('high'),
                    "low": row.get('low'),
                    "close": row.get('close'),
                    "volume": row.get('vol'),
                    "amount": row.get('amount'),
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
            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"
            
            # 获取财务指标数据
            df = self.api.financial_data(
                ts_code=ts_code,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            
            if df is not None and len(df) > 0:
                # 取最新一期数据
                latest = df.iloc[-1]
                
                return {
                    "ts_code": ts_code,
                    "report_date": latest.get('report_date'),
                    # 盈利能力
                    "roe": latest.get('roe'),
                    "net_profit_ratio": latest.get('net_profit_ratio'),
                    "gross_profit_rate": latest.get('gross_profit_rate'),
                    "eps": latest.get('eps'),
                    "roa": latest.get('roa'),
                    # 偿债能力
                    "current_ratio": latest.get('current_ratio'),
                    "quick_ratio": latest.get('quick_ratio'),
                    # 运营能力
                    "inventory_turnover": latest.get('inventory_turnover'),
                    "total_asset_turnover": latest.get('total_asset_turnover'),
                }
            return {}
            
        except Exception as e:
            logger.warning(f"获取财务数据失败（免费版受限）{stock_code}: {e}")
            return {}
    
    async def get_valuation_data(self, stock_code: str) -> Dict[str, Any]:
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
            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"
            
            # 获取每日指标（包含PE、PB等）
            df = self.api.daily_basic(
                ts_code=ts_code,
                trade_date=datetime.now().strftime('%Y%m%d')
            )
            
            if df is not None and len(df) > 0:
                row = df.iloc[0]
                return {
                    "ts_code": ts_code,
                    "trade_date": row.get('trade_date'),
                    "close": row.get('close'),
                    "pe": row.get('pe'),
                    "pb": row.get('pb'),
                    "ps": row.get('ps'),
                    "total_mv": row.get('total_mv'),  # 总市值（万元）
                    "circ_mv": row.get('circ_mv'),    # 流通市值（万元）
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
            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"
            
            # 获取资产负债表
            df = self.api.balancesheet_vip(
                ts_code=ts_code,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            
            if df is not None and len(df) > 0:
                # 取最新一期数据
                latest = df.iloc[-1]
                
                return {
                    "ts_code": ts_code,
                    "report_date": latest.get('report_date'),
                    "total_assets": latest.get('total_assets'),      # 总资产
                    "total_liabilities": latest.get('total_liab'),  # 总负债
                    "total_equity": latest.get('total_eq'),         # 股东权益
                    "asset_liability_ratio": latest.get('debt_to_assets'),  # 资产负债率
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
            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"
            
            # 获取利润表
            df = self.api.income_vip(
                ts_code=ts_code,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            
            if df is not None and len(df) > 0:
                # 取最新一期数据
                latest = df.iloc[-1]
                
                return {
                    "ts_code": ts_code,
                    "report_date": latest.get('report_date'),
                    "revenue": latest.get('revenue'),              # 营业收入
                    "operating_cost": latest.get('oper_cost'),    # 营业成本
                    "operating_profit": latest.get('op_profit'),  # 营业利润
                    "net_profit": latest.get('n_income'),          # 净利润
                    "eps": latest.get('eps'),                     # 每股收益
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
            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"
            
            # 获取现金流量表
            df = self.api.cashflow_vip(
                ts_code=ts_code,
                start_date='20200101',
                end_date=datetime.now().strftime('%Y%m%d')
            )
            
            if df is not None and len(df) > 0:
                # 取最新一期数据
                latest = df.iloc[-1]
                
                return {
                    "ts_code": ts_code,
                    "report_date": latest.get('report_date'),
                    "operating_cf": latest.get('n_cashflow_act'),   # 经营活动现金流
                    "investing_cf": latest.get('n_cashflow_inv_act'), # 投资活动现金流
                    "financing_cf": latest.get('n_cashflow_fin_act'), # 筹资活动现金流
                }
            return {}
            
        except Exception as e:
            logger.warning(f"获取现金流量表失败 {stock_code}: {e}")
            return {}
    
    async def collect_all(self, stock_code: str) -> Dict[str, Any]:
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
        
        # 并行采集各类数据
        stock_info = await self.get_stock_info(stock_code)
        daily_price = await self.get_daily_price(stock_code)
        valuation = await self.get_valuation_data(stock_code)
        financial = await self.get_financial_data(stock_code)
        balance_sheet = await self.get_balance_sheet(stock_code)
        income = await self.get_income_statement(stock_code)
        cash_flow = await self.get_cash_flow(stock_code)
        
        # 合并数据
        result = {
            **stock_info,
            **daily_price,
            **valuation,
            **financial,
            **balance_sheet,
            **income,
            **cash_flow,
            "data_source": "tushare",
            "data_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        logger.info(f"Tushare 数据采集完成: {stock_code}")
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
    
    if _tushare_skill_instance is None:
        _tushare_skill_instance = TushareSkill(token)
        await _tushare_skill_instance.initialize()
    
    return _tushare_skill_instance
