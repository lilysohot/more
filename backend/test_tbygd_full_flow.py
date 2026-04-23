"""
特变电工完整分析流程测试脚本

测试目标：对"特变电工"（股票代码：600089）进行完整的投资分析流程测试

测试覆盖：
1. 数据采集（搜索股票代码、获取股票信息、财务数据）
2. 财务比率计算
3. 报告生成（Markdown 和 HTML）

运行方式：
    cd backend
    python test_tbygd_full_flow.py
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_step1_search_stock_code():
    """
    步骤1: 测试搜索股票代码
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("步骤1: 搜索特变电工股票代码")
    logger.info("=" * 70)
    
    from app.services.data_collector import DataCollector
    
    collector = DataCollector()
    stock_code = await collector._search_stock_code("特变电工")
    
    logger.info(f"搜索结果: {stock_code}")
    
    if stock_code:
        logger.info(f"✓ 成功找到股票代码: {stock_code}")
        return stock_code
    else:
        logger.warning("✗ 未找到股票代码，使用默认代码 600089")
        return "600089"


async def test_step2_get_stock_info(stock_code: str):
    """
    步骤2: 测试获取股票详细信息
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"步骤2: 获取股票 {stock_code} 详细信息")
    logger.info("=" * 70)
    
    from app.services.data_collector import DataCollector
    
    collector = DataCollector()
    stock_info = await collector._get_stock_info(stock_code)
    
    logger.info("获取到的股票信息:")
    for key, value in stock_info.items():
        if value is not None:
            logger.info(f"  {key}: {value}")
    
    if stock_info:
        logger.info("✓ 股票信息获取成功")
    else:
        logger.warning("✗ 股票信息获取失败")
    
    return stock_info


async def test_step3_get_financial_summary(stock_code: str, info: dict):
    """
    步骤3: 测试获取财务摘要数据
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"步骤3: 获取股票 {stock_code} 财务摘要")
    logger.info("=" * 70)
    
    from app.services.data_collector import DataCollector
    
    collector = DataCollector()
    await collector._get_financial_summary(stock_code, info)
    
    logger.info("财务摘要数据:")
    financial_keys = ["total_assets", "total_liabilities", "equity", "asset_liability_ratio", "debt_to_equity"]
    for key in financial_keys:
        if key in info and info[key] is not None:
            logger.info(f"  {key}: {info[key]}")
    
    if info.get("total_assets"):
        logger.info("✓ 财务摘要获取成功")
    else:
        logger.warning("✗ 财务摘要数据为空")
    
    return info


async def test_step4_get_solvency_data(stock_code: str, info: dict):
    """
    步骤4: 测试获取偿债能力数据
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"步骤4: 获取股票 {stock_code} 偿债能力数据")
    logger.info("=" * 70)
    
    from app.services.data_collector import DataCollector
    
    collector = DataCollector()
    await collector._get_solvency_data(stock_code, info)
    
    logger.info("偿债能力数据:")
    solvency_keys = ["current_ratio", "quick_ratio"]
    for key in solvency_keys:
        if key in info and info[key] is not None:
            logger.info(f"  {key}: {info[key]}")
    
    if info.get("current_ratio"):
        logger.info("✓ 偿债能力数据获取成功")
    else:
        logger.warning("✗ 偿债能力数据为空")
    
    return info


async def test_step5_calculate_ratios(company_data: dict):
    """
    步骤5: 测试财务比率计算
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("步骤5: 计算财务比率")
    logger.info("=" * 70)
    
    from app.services.data_collector import DataCollector
    
    collector = DataCollector()
    ratios = await collector.calculate_ratios(company_data)
    
    logger.info("计算得到的财务比率:")
    for key, value in ratios.items():
        if value is not None:
            logger.info(f"  {key}: {value}")
    
    logger.info("✓ 财务比率计算完成")
    return ratios


async def test_step6_generate_report(company_data: dict, financial_ratios: dict):
    """
    步骤6: 测试报告生成
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("步骤6: 生成分析报告")
    logger.info("=" * 70)
    
    # 模拟 LLM 分析结果（实际测试时不调用 LLM）
    mock_analysis_result = """
## 第一步：身份穿透与定性
特变电工是一家以新能源产业为核心业务的综合性企业，主营业务包括光伏、风电等新能源装备制造，以及光伏电站建设和运营。

## 第二步：三维深度辩论

### 一、【芒格视角】评估护城河、管理层诚信、估值安全边际
1. **护城河分析**：特变电工在新能源装备领域具有较强的技术积累和品牌影响力，但面临激烈的市场竞争。
2. **管理层诚信评估**：公司治理结构较为完善，信息披露及时。
3. **估值安全边际**：当前估值处于历史中等水平。

### 二、【产业专家视角】拆解物理瓶颈、供需缺口、成本曲线位置
1. **物理瓶颈分析**：光伏、风电装备制造产能相对充足。
2. **供需缺口评估**：新能源行业整体需求旺盛。
3. **成本曲线位置**：公司具备一定的规模优势。

### 三、【审计专家视角】排查关联交易、资金流向、资产质量
1. **关联交易排查**：关联交易规模适中，定价公允。
2. **资金流向分析**：经营现金流改善明显。
3. **资产质量评估**：资产结构合理，商誉减值风险可控。

## 第三步：综合评级与策略
- **最终得分**：7分（满分10分）
- **芒格的决定**：持有
- **核心理由**：公司基本面稳健，新能源行业发展前景良好，但估值偏高，建议持有等待更好的买入时机。
"""
    
    from app.services.report_generator import ReportGenerator
    
    generator = ReportGenerator()
    content_md, content_html = await generator.generate(
        company_data=company_data,
        financial_ratios=financial_ratios,
        analysis_result=mock_analysis_result,
        include_charts=True,
    )
    
    logger.info(f"Markdown 报告长度: {len(content_md)} 字符")
    logger.info(f"HTML 报告长度: {len(content_html)} 字符")
    
    # 保存报告到文件
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    
    md_file = os.path.join(output_dir, "tbygd_report.md")
    html_file = os.path.join(output_dir, "tbygd_report.html")
    
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content_md)
    logger.info(f"✓ Markdown 报告已保存: {md_file}")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content_html)
    logger.info(f"✓ HTML 报告已保存: {html_file}")
    
    return content_md, content_html


async def test_full_flow():
    """
    执行完整分析流程测试
    """
    logger.info("")
    logger.info("┌" + "━" * 68 + "┐")
    logger.info("│" + " " * 18 + "特变电工完整分析流程测试" + " " * 26 + "│")
    logger.info("└" + "━" * 68 + "┘")
    logger.info("")
    logger.info(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("测试目标: 特变电工（股票代码：600089）")
    logger.info("")
    
    try:
        # 初始化公司数据
        company_data = {
            "company_name": "特变电工",
            "stock_code": "600089",
            "data_source": "网络搜索",
            "data_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # 步骤1: 搜索股票代码
        stock_code = await test_step1_search_stock_code()
        company_data["stock_code"] = stock_code
        
        # 步骤2: 获取股票信息
        stock_info = await test_step2_get_stock_info(stock_code)
        company_data.update(stock_info)
        
        # 步骤3: 获取财务摘要
        company_data = await test_step3_get_financial_summary(stock_code, company_data)
        
        # 步骤4: 获取偿债能力数据
        company_data = await test_step4_get_solvency_data(stock_code, company_data)
        
        # 打印采集到的完整数据
        logger.info("")
        logger.info("=" * 70)
        logger.info("采集到的公司数据汇总:")
        logger.info("=" * 70)
        for key, value in company_data.items():
            if value is not None:
                logger.info(f"  {key}: {value}")
        
        # 步骤5: 计算财务比率
        financial_ratios = await test_step5_calculate_ratios(company_data)
        
        # 打印财务比率
        logger.info("")
        logger.info("=" * 70)
        logger.info("计算得到的财务比率汇总:")
        logger.info("=" * 70)
        for key, value in financial_ratios.items():
            if value is not None:
                logger.info(f"  {key}: {value}")
        
        # 步骤6: 生成报告
        content_md, content_html = await test_step6_generate_report(company_data, financial_ratios)
        
        # 测试完成
        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ 完整分析流程测试完成!")
        logger.info("=" * 70)
        logger.info(f"测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            "company_data": company_data,
            "financial_ratios": financial_ratios,
            "report_md": content_md,
            "report_html": content_html,
        }
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 70)
        logger.error(f"✗ 测试失败: {e}")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        raise


async def test_collect_method_directly():
    """
    直接测试 DataCollector.collect 方法（一步到位）
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("额外测试: 直接调用 DataCollector.collect 方法")
    logger.info("=" * 70)
    
    from app.services.data_collector import DataCollector
    
    collector = DataCollector()
    
    logger.info("调用 collector.collect('特变电工', '600089')...")
    company_data = await collector.collect("特变电工", "600089")
    
    logger.info("")
    logger.info("返回的公司数据:")
    for key, value in company_data.items():
        if value is not None:
            logger.info(f"  {key}: {value}")
    
    return company_data


if __name__ == "__main__":
    print("\n")
    print("┌" + "━" * 68 + "┐")
    print("│" + " " * 18 + "特变电工完整分析流程测试" + " " * 26 + "│")
    print("└" + "━" * 68 + "┘")
    print("\n")
    
    try:
        # 执行完整流程测试
        result = asyncio.run(test_full_flow())
        
        # 执行额外测试
        asyncio.run(test_collect_method_directly())
        
        print("\n")
        print("┌" + "━" * 68 + "┐")
        print("│" + " " * 20 + "所有测试执行完成" + " " * 30 + "│")
        print("└" + "━" * 68 + "┘")
        print("\n")
        
    except Exception as e:
        print("\n")
        print("┌" + "━" * 68 + "┐")
        print("│" + " " * 20 + f"测试执行失败: {e}" + " " * 29 + "│")
        print("└" + "━" * 68 + "┘")
        print("\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
