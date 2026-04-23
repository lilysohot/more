"""
测试 DataCollector._get_stock_info 方法
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

async def test_get_stock_info():
    print("\n" + "=" * 60)
    print("测试 DataCollector._get_stock_info 方法")
    print("=" * 60 + "\n")

    from app.services.data_collector import DataCollector

    collector = DataCollector()

    # 测试多个股票代码
    test_stocks = [
        "603067",  # 振华股份
        "600089",  # 特变电工
        "000001",  # 平安银行
    ]

    for stock_code in test_stocks:
        print(f"\n测试股票：{stock_code}")
        print("-" * 40)
        
        try:
            result = await collector._get_stock_info(stock_code)
            
            print(f"结果: {result}")
            
            if result:
                print(f"✓ 获取成功:")
                for key, value in result.items():
                    if value is not None:
                        print(f"    {key}: {value}")
            else:
                print(f"✗ 返回空结果")
        except Exception as e:
            print(f"✗ 发生异常：{e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_get_stock_info())
