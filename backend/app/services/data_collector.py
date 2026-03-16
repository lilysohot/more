"""
数据采集服务模块

负责从外部数据源采集公司财务数据，包括：
- 股票代码搜索
- 公司基本信息
- 财务指标数据
- 估值指标数据

主要数据源：东方财富网 API
"""

import logging
import httpx
import re
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataCollector:
    """
    数据采集服务类
    
    负责从外部数据源采集公司财务数据和估值信息。
    
    使用示例:
        collector = DataCollector()
        company_data = await collector.collect("特变电工", "600089")
        ratios = await collector.calculate_ratios(company_data)
    """
    
    def __init__(self):
        """初始化数据采集器，设置请求头"""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def collect(self, company_name: str, stock_code: str = None) -> dict:
        """
        采集公司数据
        
        采集流程：
        1. 如果没有股票代码，先搜索获取
        2. 根据股票代码获取详细数据
        
        参数:
            company_name: 公司名称
            stock_code: 股票代码（可选，如不提供会自动搜索）
        
        返回:
            dict: 包含公司信息和财务数据的字典
        
        返回字段说明:
            - company_name: 公司名称
            - stock_code: 股票代码
            - exchange: 交易所（SH/SZ）
            - industry: 所属行业
            - revenue: 营业收入
            - net_profit: 净利润
            - gross_margin: 毛利率
            - asset_liability_ratio: 资产负债率
            - operating_cash_flow: 经营现金流
            - roe: 净资产收益率
            - market_cap: 市值
            - pe_ratio: 市盈率
            - pb_ratio: 市净率
            - data_source: 数据来源
            - data_date: 数据日期
        """
        logger.info(f"Collecting data for {company_name} ({stock_code})")
        
        # 初始化公司数据结构
        company_data = {
            "company_name": company_name,
            "stock_code": stock_code,
            "exchange": None,
            "industry": None,
            "revenue": None,
            "net_profit": None,
            "gross_margin": None,
            "asset_liability_ratio": None,
            "operating_cash_flow": None,
            "roe": None,
            "market_cap": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "data_source": "网络搜索",
            "data_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # 如果没有股票代码，先搜索
        if not stock_code:
            stock_code = await self._search_stock_code(company_name)
            company_data["stock_code"] = stock_code
        
        # 获取股票详细信息
        if stock_code:
            stock_info = await self._get_stock_info(stock_code)
            company_data.update(stock_info)
        
        return company_data

    async def _search_stock_code(self, company_name: str) -> Optional[str]:
        """
        根据公司名称搜索股票代码
        
        使用东方财富搜索API进行模糊匹配
        
        参数:
            company_name: 公司名称
        
        返回:
            str: 股票代码，如果未找到返回 None
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                url = f"https://searchapi.eastmoney.com/api/suggest/get"
                params = {
                    "input": company_name,
                    "type": "14",
                    "count": 5,
                }
                response = await client.get(url, params=params, headers=self.headers)
                data = response.json()
                
                # 遍历搜索结果，寻找匹配的公司
                if data.get("Data"):
                    for item in data["Data"]:
                        code = item.get("Code", "")
                        name = item.get("Name", "")
                        if company_name in name or name in company_name:
                            return code
                
        except Exception as e:
            logger.warning(f"Failed to search stock code: {e}")
        
        return None

    async def _get_stock_info(self, stock_code: str) -> dict:
        """
        获取股票详细信息
        
        从东方财富API获取股票的财务和估值数据
        
        参数:
            stock_code: 股票代码
        
        返回:
            dict: 股票信息字典，包含市值、PE、PB等
        """
        info = {}
        
        try:
            # 根据股票代码判断交易所
            if stock_code.startswith(("6", "9")):
                secid = f"1.{stock_code}"  # 上海交易所
            else:
                secid = f"0.{stock_code}"  # 深圳交易所
            
            async with httpx.AsyncClient(timeout=10) as client:
                url = "https://push2.eastmoney.com/api/qt/stock/get"
                params = {
                    "secid": secid,
                    "fields": "f57,f58,f84,f85,f116,f117,f162,f167,f92,f173,f187,f105,f190",
                }
                response = await client.get(url, params=params, headers=self.headers)
                data = response.json()
                
                if data.get("data"):
                    d = data["data"]
                    info["exchange"] = "SH" if stock_code.startswith(("6", "9")) else "SZ"
                    info["market_cap"] = d.get("f116")  # 总市值
                    info["pe_ratio"] = d.get("f162")    # 市盈率
                    info["pb_ratio"] = d.get("f167")    # 市净率
                    
        except Exception as e:
            logger.warning(f"Failed to get stock info from eastmoney: {e}")
        
        # 尝试获取财务数据（预留接口）
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                url = "https://emweb.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index"
                params = {"code": stock_code}
                response = await client.get(url, params=params, headers=self.headers)
                
        except Exception as e:
            logger.warning(f"Failed to get financial data: {e}")
        
        return info

    async def calculate_ratios(self, company_data: dict) -> dict:
        """
        计算财务比率
        
        基于采集的财务数据计算各项财务比率
        
        参数:
            company_data: 公司数据字典
        
        返回:
            dict: 财务比率字典
        
        计算公式:
            - 净利率 = 净利润 / 营业收入 * 100
            - 经营现金流/净利润 = 经营现金流 / 净利润 * 100
        """
        ratios = {
            "gross_margin": company_data.get("gross_margin"),
            "net_margin": None,
            "roe": company_data.get("roe"),
            "roa": None,
            "current_ratio": None,
            "quick_ratio": None,
            "debt_to_equity": None,
            "asset_liability_ratio": company_data.get("asset_liability_ratio"),
            "operating_cash_flow_to_net_profit": None,
        }
        
        # 计算净利率
        if company_data.get("revenue") and company_data.get("net_profit"):
            ratios["net_margin"] = (
                company_data["net_profit"] / company_data["revenue"]
            ) * 100
        
        # 计算经营现金流/净利润
        if company_data.get("operating_cash_flow") and company_data.get("net_profit"):
            if company_data["net_profit"] != 0:
                ratios["operating_cash_flow_to_net_profit"] = (
                    company_data["operating_cash_flow"] / company_data["net_profit"]
                ) * 100
        
        return ratios
