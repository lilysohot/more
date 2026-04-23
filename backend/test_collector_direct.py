"""
直接测试 DataCollector._search_stock_code 方法
"""

import asyncio
import logging
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_search():
    print("\n" + "=" * 60)
    print("测试 DataCollector._search_stock_code 方法")
    print("=" * 60 + "\n")

    from app.services.data_collector import DataCollector

    collector = DataCollector()

    test_companies = [
        "特变电工",
    ]

    for company in test_companies:
        print(f"\n测试公司: {company}")
        print("-" * 40)
        
        result = await collector._search_stock_code(company)
        
        print(f"结果: {result}")
        
        if result:
            print(f"✓ 找到股票代码: {result}")
        else:
            print(f"✗ 未找到股票代码")


if __name__ == "__main__":
    asyncio.run(test_search())
