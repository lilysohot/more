"""
数据采集调试脚本

详细追踪每一步执行情况
"""

import asyncio
import logging
import httpx

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_search():
    """
    详细调试搜索流程
    """
    logger.info("=" * 80)
    logger.info("调试开始")
    logger.info("=" * 80)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    test_company = "振华股份"

    try:
        logger.info("[步骤 1] 创建 httpx 客户端")
        async with httpx.AsyncClient(timeout=10) as client:
            logger.info("  ✓ 客户端创建成功")

            url = "https://searchapi.eastmoney.com/api/suggest/get"
            params = {
                "input": test_company,
                "type": "14",
                "count": 5,
            }

            logger.info("")
            logger.info("[步骤 2] 发送请求")
            logger.info(f"  URL: {url}")
            logger.info(f"  参数: {params}")

            response = await client.get(url, params=params, headers=headers)
            logger.info(f"  ✓ 响应收到，状态码: {response.status_code}")

            logger.info("")
            logger.info("[步骤 3] 解析响应文本")
            text = response.text
            logger.info(f"  响应文本长度: {len(text)}")
            logger.info(f"  响应文本前 500 字符:\n{text[:500]}")

            logger.info("")
            logger.info("[步骤 4] 解析 JSON")
            import json
            try:
                data = json.loads(text)
                logger.info("  ✓ JSON 解析成功")
            except Exception as e:
                logger.error(f"  ✗ JSON 解析失败: {e}")
                import traceback
                traceback.print_exc()
                return None

            logger.info("")
            logger.info("[步骤 5] 检查数据结构")
            logger.info(f"  顶级键: {list(data.keys())}")

            logger.info("")
            logger.info("[步骤 6] 尝试获取 Data")
            result_data = data.get("Data")
            logger.info(f"  data.get('Data') = {result_data}")
            logger.info(f"  类型: {type(result_data)}")

            if not result_data:
                logger.info("")
                logger.info("[步骤 7] 尝试 QuotationCodeTable")
                if "QuotationCodeTable" in data:
                    logger.info("  ✓ 找到 QuotationCodeTable")
                    qct = data["QuotationCodeTable"]
                    logger.info(f"  QuotationCodeTable 键: {list(qct.keys())}")
                    result_data = qct.get("Data")
                    logger.info(f"  QuotationCodeTable.get('Data') = {result_data}")
                    logger.info(f"  类型: {type(result_data)}")
                else:
                    logger.warning("  ✗ 未找到 QuotationCodeTable")

            logger.info("")
            logger.info("[步骤 8] 最终 result_data")
            if result_data:
                logger.info(f"  ✓ 有数据，长度: {len(result_data)}")
                logger.info(f"  数据内容:")
                for i, item in enumerate(result_data):
                    logger.info(f"    [{i}] Code: {item.get('Code')}, Name: {item.get('Name')}")

                logger.info("")
                logger.info("[步骤 9] 查找匹配公司")
                for item in result_data:
                    code = item.get("Code", "")
                    name = item.get("Name", "")
                    logger.info(f"  检查: {name} ({code})")
                    if test_company in name or name in test_company:
                        logger.info(f"  ✓ 匹配成功!")
                        return code
            else:
                logger.warning("  ✗ 没有数据")

    except Exception as e:
        logger.error(f"")
        logger.error(f"=" * 80)
        logger.error(f"发生异常!")
        logger.error(f"=" * 80)
        logger.error(f"异常类型: {type(e).__name__}")
        logger.error(f"异常信息: {e}")
        logger.error(f"")
        import traceback
        traceback.print_exc()

    logger.info("")
    logger.info("=" * 80)
    logger.info("调试结束，未找到匹配")
    logger.info("=" * 80)
    return None


if __name__ == "__main__":
    print("\n")
    print("┌" + "─" * 78 + "┐")
    print("│" + " " * 28 + "数据采集调试工具" + " " * 33 + "│")
    print("└" + "─" * 78 + "┘")
    print("\n")

    result = asyncio.run(debug_search())

    print("\n")
    if result:
        print(f"✓ 找到股票代码: {result}")
    else:
        print("✗ 未找到股票代码")
    print("\n")
