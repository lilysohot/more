"""
LLM API 测试脚本

验证 DashScope/OpenAI/Claude API 参数是否正确
"""

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_dashscope_api():
    """
    测试 DashScope API 参数
    """
    from app.core.config import settings
    from app.services.llm_service import LLMService

    logger.info("=" * 60)
    logger.info("测试1: DashScope API 参数核查")
    logger.info("=" * 60)

    config = {
        "provider": "dashscope",
        "api_key": settings.DEFAULT_LLM_API_KEY,
        "model_version": settings.DEFAULT_LLM_MODEL,
    }

    logger.info(f"Provider: {config['provider']}")
    logger.info(f"Model: {config['model_version']}")
    logger.info(f"API Key: {config['api_key'][:10]}...")
    logger.info("")

    # 创建服务实例
    service = LLMService(config)

    # 检查服务初始化
    logger.info("✓ 服务初始化成功")
    logger.info(f"  - provider: {service.provider}")
    logger.info(f"  - model_version: {service.model_version}")
    logger.info("")

    # 构建测试数据
    test_company_data = {
        "company_name": "测试公司",
        "stock_code": "000001",
        "industry": "制造业",
        "exchange": "SZSE",
        "revenue": 1000000000,
        "net_profit": 100000000,
        "gross_margin": 30.5,
        "asset_liability_ratio": 40.0,
        "operating_cash_flow": 150000000,
        "roe": 15.0,
        "market_cap": 5000000000,
        "pe_ratio": 25.0,
        "pb_ratio": 2.5,
    }

    test_financial_ratios = {
        "gross_margin": 30.5,
        "net_margin": 10.0,
        "roe": 15.0,
        "roa": 8.0,
        "current_ratio": 1.5,
        "quick_ratio": 1.2,
        "debt_to_equity": 66.7,
        "asset_liability_ratio": 40.0,
        "operating_cash_flow_to_net_profit": 150.0,
    }

    # 测试 prompt 构建
    logger.info("测试2: Prompt 构建")
    logger.info("-" * 60)
    prompt = service._build_prompt(test_company_data, test_financial_ratios)
    logger.info(f"✓ Prompt 构建成功，长度: {len(prompt)} 字符")
    logger.info(f"  前200字符: {prompt[:200]}...")
    logger.info("")

    # 测试 _call_dashscope 的参数
    logger.info("测试3: API 请求参数")
    logger.info("-" * 60)

    # 模拟 _call_dashscope 的内部逻辑
    url = service.base_url or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    logger.info(f"URL: {url}")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {service.api_key}",
    }
    logger.info(f"Headers:")
    logger.info(f"  Content-Type: {headers['Content-Type']}")
    logger.info(f"  Authorization: Bearer {headers['Authorization'][:20]}...")

    payload = {
        "model": service.model_version,
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
    logger.info(f"Payload:")
    logger.info(f"  model: {payload['model']}")
    logger.info(f"  input.messages: {len(payload['input']['messages'])} 条")
    logger.info(f"  parameters.max_tokens: {payload['parameters']['max_tokens']}")
    logger.info(f"  parameters.temperature: {payload['parameters']['temperature']}")
    logger.info("")

    # 对比官方文档
    logger.info("=" * 60)
    logger.info("参数对比（官方文档 vs 代码）")
    logger.info("=" * 60)

    checks = [
        ("URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation", url),
        ("Authorization Header", "Bearer {api_key}", headers["Authorization"].startswith("Bearer ")),
        ("Content-Type", "application/json", headers["Content-Type"]),
        ("Payload.model", "qwen-turbo/qwen-plus", payload["model"]),
        ("Payload.input.messages", "数组格式", isinstance(payload["input"]["messages"], list)),
        ("Payload.parameters.max_tokens", "数值", isinstance(payload["parameters"]["max_tokens"], int)),
        ("Payload.parameters.temperature", "0.0-1.0", 0 <= payload["parameters"]["temperature"] <= 1),
    ]

    all_ok = True
    for name, expected, actual in checks:
        if isinstance(actual, bool):
            ok = actual
        else:
            ok = str(expected) in str(actual) or str(actual) in str(expected)

        if ok:
            logger.info(f"✓ {name}: {actual}")
        else:
            logger.error(f"✗ {name}: 期望 '{expected}', 实际 '{actual}'")
            all_ok = False

    logger.info("")

    # 响应格式期望
    logger.info("=" * 60)
    logger.info("响应格式期望")
    logger.info("=" * 60)
    logger.info("期望响应结构:")
    logger.info("""
{
  "output": {
    "text": "生成的内容"
  }
}
    """)
    logger.info("代码解析路径: data['output']['text']")
    logger.info("")

    if all_ok:
        logger.info("=" * 60)
        logger.info("✓ 所有参数核查通过！")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("✗ 部分参数不匹配！")
        logger.error("=" * 60)

    return all_ok


async def test_api_call():
    """
    实际调用 API 测试（可选）
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("是否要实际调用 API 测试？")
    logger.info("=" * 60)
    logger.info("注意：这会消耗 API 额度")
    logger.info("")

    choice = input("输入 y 继续，其他键跳过: ").strip().lower()

    if choice != 'y':
        logger.info("跳过实际 API 调用")
        return

    logger.info("正在调用 API...")
    from app.core.config import settings
    from app.services.llm_service import LLMService

    config = {
        "provider": "dashscope",
        "api_key": settings.DEFAULT_LLM_API_KEY,
        "model_version": settings.DEFAULT_LLM_MODEL,
    }

    service = LLMService(config)

    test_company_data = {
        "company_name": "测试公司",
        "stock_code": "000001",
        "industry": "制造业",
        "exchange": "SZSE",
        "revenue": 1000000000,
        "net_profit": 100000000,
        "gross_margin": 30.5,
        "asset_liability_ratio": 40.0,
        "operating_cash_flow": 150000000,
        "roe": 15.0,
        "market_cap": 5000000000,
        "pe_ratio": 25.0,
        "pb_ratio": 2.5,
    }

    test_financial_ratios = {
        "gross_margin": 30.5,
        "net_margin": 10.0,
        "roe": 15.0,
        "roa": 8.0,
        "current_ratio": 1.5,
        "quick_ratio": 1.2,
        "debt_to_equity": 66.7,
        "asset_liability_ratio": 40.0,
        "operating_cash_flow_to_net_profit": 150.0,
    }

    try:
        result = await service.analyze(test_company_data, test_financial_ratios)
        logger.info("✓ API 调用成功！")
        logger.info(f"响应前 300 字符: {result[:300]}...")
    except Exception as e:
        logger.error(f"✗ API 调用失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n")
    print("┌" + "─" * 58 + "┐")
    print("│" + " " * 18 + "LLM API 参数核查工具" + " " * 20 + "│")
    print("└" + "─" * 58 + "┘")
    print("\n")

    try:
        params_ok = asyncio.run(test_dashscope_api())

        if params_ok:
            asyncio.run(test_api_call())
    except Exception as e:
        logger.error(f"测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
