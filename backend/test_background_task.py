"""
后台任务测试脚本

测试 AnalysisService.run_analysis 是否能正常执行
"""

import asyncio
import logging
from datetime import datetime
from uuid import uuid4

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_background_task():
    """
    测试后台任务的基本功能
    """
    from app.services.analysis import AnalysisService, get_active_tasks

    logger.info("=" * 60)
    logger.info("开始测试后台任务")
    logger.info("=" * 60)

    # 生成测试用的 ID
    test_analysis_id = str(uuid4())
    test_user_id = str(uuid4())
    test_company_name = "测试公司"

    logger.info(f"测试任务 ID: {test_analysis_id}")
    logger.info(f"测试公司: {test_company_name}")
    logger.info("")

    # 检查初始活跃任务
    initial_tasks = get_active_tasks()
    logger.info(f"初始活跃任务数: {len(initial_tasks)}")
    logger.info("")

    # 创建服务实例
    service = AnalysisService()

    # 启动任务（注意：这里直接调用，不通过 FastAPI BackgroundTasks）
    logger.info("启动分析任务...")
    task = asyncio.create_task(
        service.run_analysis(
            analysis_id=test_analysis_id,
            user_id=test_user_id,
            company_name=test_company_name,
            stock_code=None,
            include_charts=True,
            api_config_id=None,
        )
    )

    # 等待一小会儿，让任务启动
    await asyncio.sleep(0.5)

    # 检查活跃任务
    active_tasks = get_active_tasks()
    logger.info(f"任务启动后活跃任务数: {len(active_tasks)}")
    if test_analysis_id in active_tasks:
        task_info = active_tasks[test_analysis_id]
        logger.info(f"任务信息:")
        logger.info(f"  - 当前步骤: {task_info['current_step']}")
        logger.info(f"  - 开始时间: {task_info['started_at']}")
    logger.info("")

    # 等待任务完成
    logger.info("等待任务完成...")
    try:
        await task
        logger.info("任务执行完成！")
    except Exception as e:
        logger.error(f"任务执行出错: {e}")
        import traceback
        traceback.print_exc()
    logger.info("")

    # 再次检查活跃任务
    final_tasks = get_active_tasks()
    logger.info(f"任务结束后活跃任务数: {len(final_tasks)}")
    logger.info(f"测试任务是否在列表中: {test_analysis_id in final_tasks}")
    logger.info("")

    logger.info("=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


async def test_progress_update():
    """
    测试状态更新功能
    """
    from app.services.analysis import AnalysisService
    from app.database import AsyncSessionLocal
    from app.models.user import Analysis, User
    from uuid import uuid4

    logger.info("")
    logger.info("=" * 60)
    logger.info("测试状态更新功能")
    logger.info("=" * 60)

    # 创建测试用户和分析记录
    test_user_id = uuid4()
    test_analysis_id = uuid4()

    async with AsyncSessionLocal() as db:
        # 创建测试用户
        user = User(
            id=test_user_id,
            username="test_user",
            email="test@example.com",
            hashed_password="fake_hash",
        )
        db.add(user)

        # 创建测试分析记录
        analysis = Analysis(
            id=test_analysis_id,
            user_id=test_user_id,
            company_name="状态测试公司",
            stock_code=None,
            status="pending",
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

    logger.info(f"测试分析记录 ID: {test_analysis_id}")
    logger.info(f"初始状态: {analysis.status}")
    logger.info("")

    # 测试状态更新
    service = AnalysisService()

    states_to_test = [
        "collecting_data",
        "calculating_ratios",
        "generating_prompt",
        "calling_llm",
        "generating_report",
        "completed",
    ]

    for state in states_to_test:
        await service._update_status(str(test_analysis_id), state)
        logger.info(f"更新状态为: {state}")

        # 验证状态
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(Analysis).where(Analysis.id == test_analysis_id)
            )
            updated_analysis = result.scalar_one_or_none()
            if updated_analysis:
                logger.info(f"  ✓ 数据库中状态: {updated_analysis.status}")

        await asyncio.sleep(0.1)

    logger.info("")
    logger.info("=" * 60)
    logger.info("状态更新测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    import sys

    # 检查是否有数据库配置
    try:
        from app.core.config import settings
        logger.info(f"数据库 URL: {settings.DATABASE_URL[:30]}...")
    except Exception as e:
        logger.warning(f"无法加载配置: {e}")
        logger.warning("请确保在正确的环境中运行")
        sys.exit(1)

    # 运行测试
    print("\n")
    print("┌" + "─" * 58 + "┐")
    print("│" + " " * 10 + "后台任务测试工具" + " " * 30 + "│")
    print("└" + "─" * 58 + "┘")
    print("\n")

    choice = input("请选择测试:\n  1. 测试后台任务完整流程\n  2. 测试状态更新功能\n  3. 都测试\n\n请输入选择 (1/2/3): ").strip()

    if choice == "1":
        asyncio.run(test_background_task())
    elif choice == "2":
        asyncio.run(test_progress_update())
    elif choice == "3":
        asyncio.run(test_background_task())
        asyncio.run(test_progress_update())
    else:
        print("无效的选择")
