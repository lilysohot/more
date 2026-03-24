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
            # 盈利能力
            "revenue": None,            # 营业收入
            "net_profit": None,        # 净利润
            "gross_margin": None,     # 毛利率
            "net_margin": None,       # 净利率
            "roe": None,              # 净资产收益率
            "roa": None,              # 总资产收益率
            # 财务结构
            "total_assets": None,      # 总资产
            "total_liabilities": None, # 总负债
            "equity": None,            # 股东权益
            "asset_liability_ratio": None,  # 资产负债率
            "debt_to_equity": None,    # 负债权益比
            # 偿债能力
            "current_assets": None,    # 流动资产
            "current_liabilities": None,  # 流动负债
            "current_ratio": None,    # 流动比率
            "quick_ratio": None,      # 速动比率
            # 现金流
            "operating_cash_flow": None,  # 经营现金流
            "investing_cash_flow": None,  # 投资现金流
            "financing_cash_flow": None,  # 融资现金流
            "operating_cash_flow_to_net_profit": None,  # 经营现金流/净利润
            # 估值指标
            "market_cap": None,       # 总市值
            "pe_ratio": None,         # 市盈率
            "pb_ratio": None,         # 市净率
            "ps_ratio": None,         # 市销率
            # 元数据
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
                # 支持两种结构: {"Data": [...]} 或 {"QuotationCodeTable": {"Data": [...]}}
                result_data = data.get("QuotationCodeTable", {} ).get("Data")
                # if not result_data and "QuotationCodeTable" in data:
                #     result_data = data["QuotationCodeTable"].get("Data")
                
                if result_data:
                    for item in result_data:
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
                # 获取基本行情数据
                url = "https://push2.eastmoney.com/api/qt/stock/get"
                params = {
                    "secid": secid,
                    "fields": "f57,f58,f84,f85,f116,f117,f162,f167,f92,f173,f187,f105,f190,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f84,f85,f116,f117",
                }
                response = await client.get(url, params=params, headers=self.headers)
                data = response.json()
                
                if data.get("data"):
                    d = data["data"]
                    info["exchange"] = "SH" if stock_code.startswith(("6", "9")) else "SZ"
                    # 注意：东方财富行情API (push2.eastmoney.com) 中没有行业字段
                    # f84/f85 是数值字段（总资产等），不是行业信息
                    # 行业信息需要通过其他API获取，暂时设为 None
                    info["industry"] = None
                    # 估值指标
                    info["market_cap"] = d.get("f116")  # 总市值（元）
                    info["pe_ratio"] = d.get("f162")    # 市盈率
                    info["pb_ratio"] = d.get("f167")    # 市净率
                    # 注意：f84/f85/f162 在东方财富行情API中不是财务数据
                    # 财务数据将通过 _get_financial_summary 和 _get_solvency_data 获取
                    
        except Exception as e:
            logger.warning(f"Failed to get stock info from eastmoney: {e}")
        
        # 获取财务摘要数据（总资产、总负债、资产负债率等）
        await self._get_financial_summary(stock_code, info)
        
        return info
    
    async def _get_financial_summary(self, stock_code: str, info: dict):
        """
        获取财务摘要数据
        
        从东方财富API获取财务摘要，包括总资产、总负债、净资产等
        
        参数:
            stock_code: 股票代码
            info: 已有信息字典，将更新此字典
        """
        try:
            # 东方财富财务摘要API
            async with httpx.AsyncClient(timeout=15) as client:
                url = "https://emweb.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew"
                params = {"type": "0", "code": stock_code}
                response = await client.get(url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and data.get("data"):
                        zyzb_data = data["data"]
                        if zyzb_data:
                            # 取最近一期数据
                            latest = zyzb_data[0] if zyzb_data else {}
                            info["total_assets"] = latest.get("totalAssets")  # 总资产
                            info["total_liabilities"] = latest.get("totalLiabilities")  # 总负债
                            info["equity"] = latest.get("shareholderEquity")  # 股东权益
                            
                            # 资产负债率
                            if latest.get("assetLiabilityRatio"):
                                info["asset_liability_ratio"] = float(latest.get("assetLiabilityRatio"))
                            
                            # 计算负债权益比
                            if info.get("total_liabilities") and info.get("equity"):
                                try:
                                    info["debt_to_equity"] = (
                                        info["total_liabilities"] / info["equity"]
                                    ) * 100
                                except (TypeError, ZeroDivisionError):
                                    pass
                            
                            logger.info(f"获取财务摘要成功: {stock_code}")
        except Exception as e:
            logger.warning(f"Failed to get financial summary for {stock_code}: {e}")
        
        # 获取偿债能力数据（流动比率、速动比率）
        await self._get_solvency_data(stock_code, info)
    
    async def _get_solvency_data(self, stock_code: str, info: dict):
        """
        获取偿债能力数据
        
        从东方财富API获取流动比率、速动比率等
        
        参数:
            stock_code: 股票代码
            info: 已有信息字典，将更新此字典
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # 偿债能力API
                url = "https://emweb.eastmoney.com/PC_HSF10/NewFinanceAnalysis/CzjlAjaxNew"
                params = {"type": "0", "code": stock_code}
                response = await client.get(url, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and data.get("data"):
                        czjl_data = data["data"]
                        if czjl_data:
                            latest = czjl_data[0] if czjl_data else {}
                            info["current_ratio"] = latest.get("currentRatio")  # 流动比率
                            info["quick_ratio"] = latest.get("quickRatio")      # 速动比率
                            logger.info(f"获取偿债能力数据成功: {stock_code}")
        except Exception as e:
            logger.warning(f"Failed to get solvency data for {stock_code}: {e}")

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
            - 毛利率 = (营业收入 - 营业成本) / 营业收入 * 100
            - ROE = 净利润 / 股东权益 * 100
            - ROA = 净利润 / 总资产 * 100
            - 流动比率 = 流动资产 / 流动负债
            - 速动比率 = (流动资产 - 存货) / 流动负债
            - 负债权益比 = 总负债 / 股东权益 * 100
            - 资产负债率 = 总负债 / 总资产 * 100
            - 经营现金流/净利润 = 经营现金流 / 净利润 * 100
        """
        ratios = {
            # 盈利能力比率
            "gross_margin": company_data.get("gross_margin"),  # 毛利率
            "net_margin": None,                                 # 净利率
            "roe": company_data.get("roe"),                     # 净资产收益率
            "roa": None,                                        # 总资产收益率
            # 财务结构比率
            "debt_to_equity": company_data.get("debt_to_equity"),  # 负债权益比
            "asset_liability_ratio": company_data.get("asset_liability_ratio"),  # 资产负债率
            # 偿债能力比率
            "current_ratio": company_data.get("current_ratio"),  # 流动比率
            "quick_ratio": company_data.get("quick_ratio"),    # 速动比率
            # 现金流比率
            "operating_cash_flow_to_net_profit": None,          # 经营现金流/净利润
        }
        
        # 提取关键数据，避免重复获取
        revenue = company_data.get("revenue")
        net_profit = company_data.get("net_profit")
        total_assets = company_data.get("total_assets")
        equity = company_data.get("equity")
        current_assets = company_data.get("current_assets")
        current_liabilities = company_data.get("current_liabilities")
        operating_cash_flow = company_data.get("operating_cash_flow")
        
        # 1. 计算净利率 = 净利润 / 营业收入 * 100
        if net_profit and revenue and revenue > 0:
            ratios["net_margin"] = (net_profit / revenue) * 100
        
        # 2. 计算 ROA (总资产收益率) = 净利润 / 总资产 * 100
        if net_profit and total_assets and total_assets > 0:
            ratios["roa"] = (net_profit / total_assets) * 100
        
        # 3. 计算毛利率（如果未直接提供）
        # 毛利率需要 (revenue - cost_of_goods_sold) / revenue，但我们通常只有 gross_margin
        # 如果 gross_margin 为空，尝试通过其他方式估算或设为 None
        if ratios["gross_margin"] is None and company_data.get("gross_margin") is not None:
            ratios["gross_margin"] = company_data["gross_margin"]
        
        # 4. 计算经营现金流/净利润比率
        if operating_cash_flow and net_profit and net_profit != 0:
            ratios["operating_cash_flow_to_net_profit"] = (
                operating_cash_flow / abs(net_profit)
            ) * 100  # 乘以100转为百分比
        
        # 5. 计算负债权益比（如果未从API获取）
        if ratios["debt_to_equity"] is None:
            total_liabilities = company_data.get("total_liabilities")
            if total_liabilities and equity and equity > 0:
                ratios["debt_to_equity"] = (total_liabilities / equity) * 100
        
        # 6. 计算资产负债率（如果未从API获取）
        if ratios["asset_liability_ratio"] is None:
            total_liabilities = company_data.get("total_liabilities")
            if total_liabilities and total_assets and total_assets > 0:
                ratios["asset_liability_ratio"] = (total_liabilities / total_assets) * 100
        
        # 7. 如果流动比率和速动比率为None，但有流动资产和流动负债数据，则计算
        if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
            if ratios["current_ratio"] is None:
                ratios["current_ratio"] = current_assets / current_liabilities
            # 速动比率需要存货数据，这里先保留原值或设为 None
            if ratios["quick_ratio"] is None:
                # 假设存货为流动资产的 20%（如果未提供）
                inventory = company_data.get("inventory") or (current_assets * 0.2 if current_assets else 0)
                ratios["quick_ratio"] = (current_assets - inventory) / current_liabilities
        
        logger.info(f"Calculated financial ratios: {ratios}")
        return ratios
