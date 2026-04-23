"""
简单后台任务测试

只测试任务启动和状态跟踪，不调用外部服务
"""

import asyncio
import logging
from uuid import uuid4

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_active_tasks_tracker():
    """
    测试活跃任务跟踪器
    """
    logger.info("=" * 60)
    logger.info("测试1: 活跃任务跟踪器")
    logger.info("=" * 60)

    from app.services.analysis import get_active_tasks, _add_active_task, _remove_active_task

    # 测试1: 初始状态
    initial_tasks = get_active_tasks()
    logger.info(f"初始活跃任务数: {len(initial_tasks)}")

    # 测试2: 添加任务
    test_id = str(uuid4())
    test_task_info = {
        "analysis_id": test_id,
        "user_id": str(uuid4()),
        "company_name": "测试公司",
        "started_at": "2026-03-18T12:00:00",
        "current_step": "pending",
    }

    _add_active_task(test_id, test_task_info)
    tasks_after_add = get_active_tasks()
    logger.info(f"添加任务后: {len(tasks_after_add)} 个任务")

    # 测试3: get_active_tasks 返回副本
    tasks = get_active_tasks()
    assert test_id in tasks, "任务应该在列表中"
    logger.info(f"✓ get_active_tasks 工作正常")

    # 测试4: 删除任务
    _remove_active_task(test_id)
    tasks_after_remove = get_active_tasks()
    logger.info(f"删除任务后: {len(tasks_after_remove)} 个任务")

    logger.info("")
    logger.info("✓ 活跃任务跟踪器测试通过！")
    logger.info("")


async def test_simple_async_flow():
    """
    测试简单的异步流程（模拟后台任务）
    """
    logger.info("=" * 60)
    logger.info("测试2: 简单异步流程")
    logger.info("=" * 60)

    from app.services.analysis import get_active_tasks, _add_active_task, _update_active_task, _remove_active_task

    test_id = str(uuid4())

    # 模拟任务启动
    logger.info("1. 模拟任务启动...")
    task_info = {
        "analysis_id": test_id,
        "user_id": str(uuid4()),
        "company_name": "模拟公司",
        "started_at": "2026-03-18T12:00:00",
        "current_step": "collecting_data",
    }
    _add_active_task(test_id, task_info)
    await asyncio.sleep(0.5)
    tasks = get_active_tasks()
    logger.info(f"   当前步骤: {tasks[test_id]['current_step']}")

    # 模拟步骤2
    logger.info("2. 模拟计算财务比率...")
    task_info["current_step"] = "calculating_ratios"
    _update_active_task(test_id, task_info)
    await asyncio.sleep(0.5)
    tasks = get_active_tasks()
    logger.info(f"   当前步骤: {tasks[test_id]['current_step']}")

    # 模拟步骤3
    logger.info("3. 模拟调用 LLM...")
    task_info["current_step"] = "calling_llm"
    _update_active_task(test_id, task_info)
    await asyncio.sleep(0.5)
    tasks = get_active_tasks()
    logger.info(f"   当前步骤: {tasks[test_id]['current_step']}")

    # 模拟完成
    logger.info("4. 模拟完成...")
    task_info["current_step"] = "completed"
    _update_active_task(test_id, task_info)
    await asyncio.sleep(0.2)

    # 清理
    _remove_active_task(test_id)

    logger.info("")
    logger.info("✓ 简单异步流程测试通过！")
    logger.info("")


def test_imports():
    """
    测试所有相关模块能否正确导入
    """
    logger.info("=" * 60)
    logger.info("测试0: 模块导入测试")
    logger.info("=" * 60)

    modules_to_test = [
        ("app.services.analysis", ["AnalysisService", "get_active_tasks"]),
        ("app.database", ["AsyncSessionLocal"]),
        ("app.models.user", ["Analysis", "User", "Report"]),
    ]

    all_ok = True
    for module_name, symbols in modules_to_test:
        try:
            module = __import__(module_name, fromlist=symbols)
            for symbol in symbols:
                if hasattr(module, symbol):
                    logger.info(f"✓ {module_name}.{symbol}")
                else:
                    logger.error(f"✗ {module_name}.{symbol} 不存在")
                    all_ok = False
        except Exception as e:
            logger.error(f"✗ 导入 {module_name} 失败: {e}")
            all_ok = False

    logger.info("")
    if all_ok:
        logger.info("✓ 所有模块导入正常！")
    else:
        logger.error("✗ 部分模块导入失败！")
    logger.info("")

    return all_ok


if __name__ == "__main__":
    print("\n")
    print("┌" + "─" * 58 + "┐")
    print("│" + " " * 15 + "简单后台任务测试" + " " * 27 + "│")
    print("└" + "─" * 58 + "┘")
    print("\n")

    # 先测试导入
    imports_ok = test_imports()

    if imports_ok:
        # 测试活跃任务跟踪器
        test_active_tasks_tracker()

        # 测试异步流程
        asyncio.run(test_simple_async_flow())

        print("\n")
        print("=" * 60)
        print("所有简单测试通过！")
        print("=" * 60)
        print("\n")
        print("下一步建议：")
        print("  1. 运行完整测试: python test_background_task.py")
        print("  2. 或者通过前端界面真实测试")
        print("\n")
    else:
        print("\n")
        print("请先解决导入问题！")
        print("\n")
