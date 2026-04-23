"""
数据采集测试脚本

测试东方财富 API 返回结构
"""

import asyncio
import logging
import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_search_api():
    """
    测试搜索 API
    """
    logger.info("=" * 60)
    logger.info("测试1: 搜索 API 返回结构")
    logger.info("=" * 60)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    test_company = "特变电工"

    async with httpx.AsyncClient(timeout=10) as client:
        url = "https://searchapi.eastmoney.com/api/suggest/get"
        params = {
            "input": test_company,
            "type": "14",
            "count": 5,
        }

        logger.info(f"请求 URL: {url}")
        logger.info(f"请求参数: {params}")
        logger.info("")

        response = await client.get(url, params=params, headers=headers)
        data = response.json()

        logger.info("完整返回结构:")
        logger.info(f"  顶级键: {list(data.keys())}")
        logger.info("")

        # 打印完整 JSON（截断过长的部分）
        import json
        logger.info("完整响应:")
        logger.info(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info("")

        # 检查 Data 字段
        if "Data" in data:
            logger.info("✓ 找到 'Data' 字段")
            data_list = data["Data"]
            logger.info(f"  Data 类型: {type(data_list)}")
            if isinstance(data_list, list):
                logger.info(f"  Data 长度: {len(data_list)}")
                if len(data_list) > 0:
                    logger.info("  第一个 item:")
                    first_item = data_list[0]
                    logger.info(f"    类型: {type(first_item)}")
                    logger.info(f"    键: {list(first_item.keys())}")
                    logger.info(f"    内容: {json.dumps(first_item, indent=2, ensure_ascii=False)}")
        else:
            logger.warning("✗ 未找到 'Data' 字段")

        logger.info("")

        # 检查是否有其他可能的字段名
        possible_fields = ["Data", "data", "Result", "result", "List", "list"]
        logger.info("检查可能的字段名:")
        for field in possible_fields:
            if field in data:
                logger.info(f"  ✓ 找到 '{field}'")

        return data


if __name__ == "__main__":
    print("\n")
    print("┌" + "─" * 58 + "┐")
    print("│" + " " * 18 + "数据采集测试工具" + " " * 23 + "│")
    print("└" + "─" * 58 + "┘")
    print("\n")

    asyncio.run(test_search_api())
