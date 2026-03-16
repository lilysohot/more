"""
LLM 服务模块

负责与大语言模型 API 交互，执行三维合一投资分析。

支持的 LLM 提供商：
- DashScope（阿里云通义千问）
- OpenAI（GPT 系列）
- Claude（Anthropic）

该模块构建专业的投资分析提示词，调用 LLM API 获取分析结果。
"""

import logging
import httpx
import json
from typing import Optional

logger = logging.getLogger(__name__)


INVESTMENT_ANALYST_PROMPT = """你是一位顶级投资分析师，擅长使用"三维合一投资决策委员会框架"进行公司分析。

请基于以下公司数据，进行深度分析：

## 公司基本信息
- 公司名称：{company_name}
- 股票代码：{stock_code}
- 所属行业：{industry}
- 交易所：{exchange}

## 核心财务数据
- 营业收入：{revenue}
- 净利润：{net_profit}
- 毛利率：{gross_margin}%
- 资产负债率：{asset_liability_ratio}%
- 经营现金流：{operating_cash_flow}
- ROE：{roe}%

## 估值指标
- 市值：{market_cap}
- 市盈率(PE)：{pe_ratio}
- 市净率(PB)：{pb_ratio}

## 财务比率
- 毛利率：{ratio_gross_margin}%
- 净利率：{ratio_net_margin}%
- ROE：{ratio_roe}%
- ROA：{ratio_roa}%
- 流动比率：{ratio_current_ratio}
- 速动比率：{ratio_quick_ratio}
- 负债权益比：{ratio_debt_to_equity}%
- 资产负债率：{ratio_asset_liability_ratio}%
- 经营现金流/净利润：{ratio_ocf_to_np}%

请按照以下框架进行分析：

## 第一步：身份穿透与定性
用一句话定义公司的本质（例如："披着科技外衣的周期股"）

## 第二步：三维深度辩论

### 一、【芒格视角】评估护城河、管理层诚信、估值安全边际
1. 护城河分析
2. 管理层诚信评估
3. 估值安全边际

### 二、【产业专家视角】拆解物理瓶颈、供需缺口、成本曲线位置
1. 物理瓶颈分析
2. 供需缺口评估
3. 成本曲线位置

### 三、【审计专家视角】排查关联交易、资金流向、资产质量
1. 关联交易排查
2. 资金流向分析
3. 资产质量评估

## 第三步：综合评级与策略
- 最终得分：X分（满分10分）
- 芒格的决定：[买入/卖出/持有/太难了]
- 核心理由：[请详细说明]

请以专业的投资分析报告格式输出，确保分析深入、逻辑清晰。
"""


class LLMService:
    """
    LLM 服务类
    
    负责与不同的大语言模型 API 进行交互，执行投资分析。
    
    属性:
        provider: LLM 提供商（dashscope/openai/claude）
        api_key: API 密钥
        base_url: API 端点地址（可选）
        model_version: 模型版本
    
    使用示例:
        config = {
            "provider": "dashscope",
            "api_key": "your-api-key",
            "model_version": "qwen-turbo"
        }
        service = LLMService(config)
        result = await service.analyze(company_data, financial_ratios)
    """
    
    def __init__(self, config: dict):
        """
        初始化 LLM 服务
        
        参数:
            config: 配置字典，包含 provider, api_key, base_url, model_version
        """
        self.provider = config.get("provider", "dashscope")
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.model_version = config.get("model_version", "qwen-turbo")

    async def analyze(self, company_data: dict, financial_ratios: dict) -> str:
        """
        执行投资分析
        
        根据公司数据和财务比率，调用 LLM 生成分析报告。
        
        参数:
            company_data: 公司数据字典
            financial_ratios: 财务比率字典
        
        返回:
            str: LLM 生成的分析报告文本
        
        说明:
            - 自动根据 provider 选择对应的 API 调用方法
            - 默认使用 DashScope（通义千问）
        """
        prompt = self._build_prompt(company_data, financial_ratios)
        
        if self.provider == "dashscope":
            return await self._call_dashscope(prompt)
        elif self.provider == "openai":
            return await self._call_openai(prompt)
        elif self.provider == "claude":
            return await self._call_claude(prompt)
        else:
            return await self._call_dashscope(prompt)

    def _build_prompt(self, company_data: dict, financial_ratios: dict) -> str:
        """
        构建分析提示词
        
        将公司数据和财务比率填充到提示词模板中。
        
        参数:
            company_data: 公司数据字典
            financial_ratios: 财务比率字典
        
        返回:
            str: 完整的提示词字符串
        """
        return INVESTMENT_ANALYST_PROMPT.format(
            company_name=company_data.get("company_name", "未知"),
            stock_code=company_data.get("stock_code", "未知"),
            industry=company_data.get("industry", "未知"),
            exchange=company_data.get("exchange", "未知"),
            revenue=self._format_number(company_data.get("revenue")),
            net_profit=self._format_number(company_data.get("net_profit")),
            gross_margin=self._format_percent(company_data.get("gross_margin")),
            asset_liability_ratio=self._format_percent(company_data.get("asset_liability_ratio")),
            operating_cash_flow=self._format_number(company_data.get("operating_cash_flow")),
            roe=self._format_percent(company_data.get("roe")),
            market_cap=self._format_number(company_data.get("market_cap")),
            pe_ratio=self._format_number(company_data.get("pe_ratio")),
            pb_ratio=self._format_number(company_data.get("pb_ratio")),
            ratio_gross_margin=self._format_percent(financial_ratios.get("gross_margin")),
            ratio_net_margin=self._format_percent(financial_ratios.get("net_margin")),
            ratio_roe=self._format_percent(financial_ratios.get("roe")),
            ratio_roa=self._format_percent(financial_ratios.get("roa")),
            ratio_current_ratio=self._format_number(financial_ratios.get("current_ratio")),
            ratio_quick_ratio=self._format_number(financial_ratios.get("quick_ratio")),
            ratio_debt_to_equity=self._format_percent(financial_ratios.get("debt_to_equity")),
            ratio_asset_liability_ratio=self._format_percent(financial_ratios.get("asset_liability_ratio")),
            ratio_ocf_to_np=self._format_percent(financial_ratios.get("operating_cash_flow_to_net_profit")),
        )

    def _format_number(self, value) -> str:
        """
        格式化数字显示
        
        将大数字转换为"亿"或"万"单位。
        
        参数:
            value: 数值
        
        返回:
            str: 格式化后的字符串
        """
        if value is None:
            return "未知"
        try:
            num = float(value)
            if num >= 1e8:
                return f"{num/1e8:.2f}亿"
            elif num >= 1e4:
                return f"{num/1e4:.2f}万"
            else:
                return f"{num:.2f}"
        except:
            return str(value)

    def _format_percent(self, value) -> str:
        """
        格式化百分比显示
        
        参数:
            value: 数值
        
        返回:
            str: 格式化后的字符串
        """
        if value is None:
            return "未知"
        try:
            return f"{float(value):.2f}"
        except:
            return str(value)

    async def _call_dashscope(self, prompt: str) -> str:
        """
        调用阿里云 DashScope API（通义千问）
        
        参数:
            prompt: 提示词
        
        返回:
            str: LLM 生成的文本
        
        API 文档: https://help.aliyun.com/document_detail/2712195.html
        """
        url = self.base_url or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.model_version,
            "input": {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "max_tokens": 4000,
                "temperature": 0.7,
            }
        }
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["output"]["text"]

    async def _call_openai(self, prompt: str) -> str:
        """
        调用 OpenAI API（GPT 系列）
        
        参数:
            prompt: 提示词
        
        返回:
            str: LLM 生成的文本
        
        API 文档: https://platform.openai.com/docs/api-reference/chat
        """
        url = self.base_url or "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.model_version or "gpt-4-turbo-preview",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.7,
        }
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_claude(self, prompt: str) -> str:
        """
        调用 Anthropic Claude API
        
        参数:
            prompt: 提示词
        
        返回:
            str: LLM 生成的文本
        
        API 文档: https://docs.anthropic.com/claude/reference/messages_post
        """
        url = self.base_url or "https://api.anthropic.com/v1/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        
        payload = {
            "model": self.model_version or "claude-3-opus-20240229",
            "max_tokens": 4000,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
