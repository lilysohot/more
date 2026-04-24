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

    @staticmethod
    def _normalize_stock_code(stock_code: Optional[str]) -> str:
        if not stock_code:
            return ""
        return str(stock_code).split(".")[0].strip().upper()

    @classmethod
    def _infer_exchange(cls, stock_code: Optional[str]) -> Optional[str]:
        normalized_code = cls._normalize_stock_code(stock_code)
        if not normalized_code:
            return None
        if normalized_code.startswith(("6", "9")):
            return "SH"
        if normalized_code.startswith(("0", "2", "3")):
            return "SZ"
        return None

    @staticmethod
    def _contains_chinese(value: str) -> bool:
        return any("\u4e00" <= char <= "\u9fff" for char in value)

    @staticmethod
    def _to_pinyin_initials(value: str) -> Optional[str]:
        if not value:
            return None

        try:
            from pypinyin import Style, lazy_pinyin

            initials = "".join(lazy_pinyin(value, style=Style.FIRST_LETTER)).upper()
            return initials or None
        except Exception as e:
            logger.warning(f"Failed to convert company name to pinyin: {e}")
            return None

    async def _fetch_search_results(self, query: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            url = "https://searchapi.eastmoney.com/api/suggest/get"
            params = {
                "input": query,
                "type": "14",
                "count": 5,
            }
            response = await client.get(url, params=params, headers=self.headers)
            data = response.json()
            result_data = data.get("QuotationCodeTable", {}).get("Data") or []
            if not result_data:
                return []

            astock_results = [item for item in result_data if item.get("Classify") == "AStock"]
            return astock_results or result_data

    async def resolve_stock(self, company_name: Optional[str] = None, stock_code: Optional[str] = None) -> dict:
        """Resolve official company name and stock code via EastMoney."""
        normalized_code = self._normalize_stock_code(stock_code)
        normalized_name = (company_name or "").strip()

        if normalized_code:
            stock_info = await self._get_stock_info(normalized_code)
            if stock_info.get("stock_code") and stock_info.get("company_name"):
                return {
                    "company_name": stock_info.get("company_name"),
                    "stock_code": stock_info.get("stock_code"),
                    "exchange": stock_info.get("exchange"),
                    "industry": stock_info.get("industry"),
                    "data_source": "eastmoney",
                }

        if not normalized_name:
            return {}

        search_match = await self._search_stock(normalized_name)
        if not search_match:
            return {}

        matched_code = self._normalize_stock_code(search_match.get("stock_code"))
        stock_info = await self._get_stock_info(matched_code) if matched_code else {}

        return {
            "company_name": stock_info.get("company_name") or search_match.get("company_name"),
            "stock_code": stock_info.get("stock_code") or matched_code,
            "exchange": stock_info.get("exchange") or search_match.get("exchange") or self._infer_exchange(matched_code),
            "industry": stock_info.get("industry") or search_match.get("industry"),
            "data_source": "eastmoney",
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

        resolved_identity = await self.resolve_stock(company_name=company_name, stock_code=stock_code)
        normalized_company_name = resolved_identity.get("company_name") or company_name
        normalized_stock_code = resolved_identity.get("stock_code") or self._normalize_stock_code(stock_code) or None
        
        # 初始化公司数据结构
        company_data = {
            "company_name": normalized_company_name,
            "stock_code": normalized_stock_code,
            "exchange": resolved_identity.get("exchange"),
            "industry": resolved_identity.get("industry"),
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
            "data_source": resolved_identity.get("data_source") or "eastmoney",
            "data_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # 如果没有股票代码，先搜索
        if not normalized_stock_code:
            normalized_stock_code = await self._search_stock_code(company_name)
            company_data["stock_code"] = normalized_stock_code
        
        # 获取股票详细信息
        if normalized_stock_code:
            stock_info = await self._get_stock_info(normalized_stock_code)
            company_data.update(stock_info)

        company_data["company_name"] = company_data.get("company_name") or normalized_company_name
        company_data["stock_code"] = company_data.get("stock_code") or normalized_stock_code
        company_data["exchange"] = company_data.get("exchange") or resolved_identity.get("exchange")
        company_data["industry"] = company_data.get("industry") or resolved_identity.get("industry")
        
        return company_data

    async def _search_stock(self, company_name: str) -> Optional[dict]:
        """Search EastMoney and return the best-matched stock identity."""
        try:
            search_queries = [company_name]
            if self._contains_chinese(company_name):
                pinyin_initials = self._to_pinyin_initials(company_name)
                if pinyin_initials and pinyin_initials not in search_queries:
                    search_queries.append(pinyin_initials)

            for query in search_queries:
                result_data = await self._fetch_search_results(query)
                if not result_data:
                    continue

                fuzzy_matches = []
                for item in result_data:
                    code = self._normalize_stock_code(item.get("Code"))
                    name = str(item.get("Name", "")).strip()
                    if not code or not name:
                        continue

                    candidate = {
                        "company_name": name,
                        "stock_code": code,
                        "exchange": "SH" if str(item.get("MktNum", "")) == "1" else "SZ",
                        "industry": None,
                    }

                    if name == company_name or code == company_name:
                        return candidate

                    if company_name in name or name in company_name:
                        fuzzy_matches.append(candidate)

                if len(fuzzy_matches) == 1:
                    return fuzzy_matches[0]

                if len(fuzzy_matches) > 1:
                    logger.info(f"Ambiguous stock search for {company_name}: {fuzzy_matches[:3]}")

            return None
        except Exception as e:
            logger.warning(f"Failed to search stock identity: {e}")

        return None

    async def _search_stock_code(self, company_name: str) -> Optional[str]:
        """
        根据公司名称搜索股票代码
        
        使用东方财富搜索API进行模糊匹配
        
        参数:
            company_name: 公司名称
        
        返回:
            str: 股票代码，如果未找到返回 None
        """
        result = await self._search_stock(company_name)
        return result.get("stock_code") if result else None

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
        normalized_code = self._normalize_stock_code(stock_code)
        
        try:
            # 根据股票代码判断交易所
            if normalized_code.startswith(("6", "9")):
                secid = f"1.{normalized_code}"  # 上海交易所
            else:
                secid = f"0.{normalized_code}"  # 深圳交易所
            
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
                    info["company_name"] = d.get("f58")
                    info["stock_code"] = self._normalize_stock_code(d.get("f57")) or normalized_code
                    info["exchange"] = "SH" if normalized_code.startswith(("6", "9")) else "SZ"
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
        await self._get_financial_summary(normalized_code, info)
        
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
