"""
特变电工完整分析流程 API 测试脚本

通过 HTTP API 调用测试完整的分析流程，用于发现后台任务处理的潜在问题。

测试流程：
1. 检查 API 服务器健康状态
2. 注册/登录获取访问令牌
3. 调用 create_analysis API 创建分析任务
4. 轮询检查分析进度
5. 获取并验证分析报告

运行方式：
    cd backend
    # 首先启动服务器
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
    # 然后在另一个终端运行测试
    python test_api_analysis_flow.py

注意：
    - 需要先启动 FastAPI 服务器
    - 服务器地址默认 http://localhost:8000
"""

import httpx
import asyncio
import logging
import sys
import time
import os
from datetime import datetime
from typing import Optional

# 修复 Windows 终端编码问题
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API 配置
API_BASE_URL = "http://localhost:8123"
API_V1_STR = "/api/v1"

# 测试配置（使用已有账户）
TEST_EMAIL = "test1@qq.com"
TEST_PASSWORD = "123456"
TEST_COMPANY_NAME = "特变电工"
TEST_STOCK_CODE = "600089"


class AnalysisAPITester:
    """分析 API 测试器"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.analysis_id: Optional[str] = None
        self.client = httpx.Client(timeout=60.0)
    
    def close(self):
        """关闭 HTTP 客户端"""
        self.client.close()
    
    async def test_health_check(self) -> bool:
        """
        步骤1: 检查 API 服务器健康状态
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("Step 1: Check API server health status")
        logger.info("=" * 70)
        
        try:
            response = self.client.get(f"{self.base_url}/health")
            logger.info(f"Health check status: {response.status_code}")
            logger.info(f"Response content: {response.text[:200]}")
            response.raise_for_status()
            
            # 尝试解析 JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                data = response.json()
                logger.info(f"[OK] Server health check passed: {data}")
            else:
                logger.info(f"[OK] Server response normal (non-JSON)")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"[FAIL] Server returned error status: {e.response.status_code}")
            logger.error(f"Response: {e.response.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"[FAIL] Server health check failed: {e}")
            return False
    
    def register_user(self) -> bool:
        """
        步骤2: 注册新用户
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("Step 2: Register new user")
        logger.info("=" * 70)
        
        try:
            response = self.client.post(
                f"{self.base_url}{API_V1_STR}/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "username": "TestUser"
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data["user"]["id"]
                logger.info(f"[OK] User registered successfully")
                logger.info(f"  User ID: {self.user_id}")
                logger.info(f"  Token: {self.token[:20]}...")
                return True
            else:
                logger.error(f"[FAIL] User registration failed: HTTP {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] User registration exception: {e}")
            return False
    
    def login_user(self) -> bool:
        """
        步骤2b: 登录用户
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("Step 2b: Login user")
        logger.info("=" * 70)
        
        try:
            response = self.client.post(
                f"{self.base_url}{API_V1_STR}/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data["user"]["id"]
                logger.info(f"[OK] User logged in successfully")
                logger.info(f"  User ID: {self.user_id}")
                logger.info(f"  Token: {self.token[:20]}...")
                return True
            else:
                logger.error(f"[FAIL] User login failed: HTTP {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] User login exception: {e}")
            return False
    
    def create_analysis(self) -> bool:
        """
        步骤3: 创建分析任务
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"Step 3: Create analysis task - {TEST_COMPANY_NAME} ({TEST_STOCK_CODE})")
        logger.info("=" * 70)
        
        if not self.token:
            logger.error("[FAIL] Not logged in, cannot create analysis task")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.post(
                f"{self.base_url}{API_V1_STR}/analyses",
                json={
                    "company_name": TEST_COMPANY_NAME,
                    "stock_code": TEST_STOCK_CODE,
                    "include_charts": True
                },
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                self.analysis_id = data["id"]
                logger.info(f"[OK] Analysis task created successfully")
                logger.info(f"  Analysis ID: {self.analysis_id}")
                logger.info(f"  Company: {data['company_name']}")
                logger.info(f"  Stock Code: {data['stock_code']}")
                logger.info(f"  Status: {data['status']}")
                logger.info(f"  Created at: {data['created_at']}")
                return True
            else:
                logger.error(f"[FAIL] Create analysis task failed: HTTP {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"[ERROR] Create analysis task exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_analysis_progress(self) -> dict:
        """
        步骤4: 获取分析进度
        """
        if not self.token or not self.analysis_id:
            logger.error("[FAIL] Not logged in or no analysis task created")
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(
                f"{self.base_url}{API_V1_STR}/analyses/{self.analysis_id}/progress",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"[FAIL] Get analysis progress failed: HTTP {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"[ERROR] Get analysis progress exception: {e}")
            return None
    
    def poll_analysis_progress(self, max_wait_seconds: int = 300) -> bool:
        """
        轮询分析进度直到完成或失败
        
        Args:
            max_wait_seconds: 最大等待时间（秒）
            
        Returns:
            bool: 是否成功完成
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("Step 4: Poll analysis progress")
        logger.info("=" * 70)
        
        start_time = time.time()
        poll_interval = 2  # 每 2 秒轮询一次
        last_status = None
        
        terminal_states = ["completed", "failed"]
        
        while time.time() - start_time < max_wait_seconds:
            progress = self.get_analysis_progress()
            
            if progress is None:
                logger.warning("Failed to get progress, retrying...")
                time.sleep(poll_interval)
                continue
            
            status = progress.get("status")
            percent = progress.get("progress")
            message = progress.get("message")
            
            # 状态变化时打印
            if status != last_status:
                logger.info(f"Status changed: {status} ({percent}%) - {message}")
                last_status = status
            
            # 检查是否到达终止状态
            if status in terminal_states:
                elapsed = time.time() - start_time
                if status == "completed":
                    logger.info(f"[OK] Analysis completed! Time elapsed: {elapsed:.1f}s")
                    return True
                else:
                    logger.error(f"[FAIL] Analysis failed! Time elapsed: {elapsed:.1f}s")
                    return False
            
            time.sleep(poll_interval)
        
        logger.error(f"[FAIL] Wait timeout (>{max_wait_seconds}s)")
        return False
    
    def get_analysis_report(self) -> dict:
        """
        步骤5: 获取分析报告
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("Step 5: Get analysis report")
        logger.info("=" * 70)
        
        if not self.token or not self.analysis_id:
            logger.error("[FAIL] Not logged in or no analysis task created")
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(
                f"{self.base_url}{API_V1_STR}/analyses/{self.analysis_id}/report",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[OK] Got report successfully")
                logger.info(f"  Markdown length: {len(data.get('content_md', ''))} chars")
                logger.info(f"  HTML length: {len(data.get('content_html', ''))} chars")
                return data
            else:
                logger.error(f"[FAIL] Get report failed: HTTP {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"[ERROR] Get report exception: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_analysis_detail(self) -> dict:
        """
        获取分析详情
        """
        if not self.token or not self.analysis_id:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(
                f"{self.base_url}{API_V1_STR}/analyses/{self.analysis_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None
    
    def list_active_tasks(self) -> dict:
        """
        列出活跃任务
        """
        if not self.token:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.client.get(
                f"{self.base_url}{API_V1_STR}/analyses/active-tasks",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None


async def run_full_flow_test():
    """
    执行完整的 API 测试流程
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("=" + " " * 68 + "=")
    logger.info("=" + " " * 15 + "TEBYGD Full Analysis Flow API Test" + " " * 25 + "=")
    logger.info("=" + " " * 68 + "=")
    logger.info("")
    logger.info(f"Test start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Test target: {TEST_COMPANY_NAME} ({TEST_STOCK_CODE})")
    logger.info(f"API URL: {API_BASE_URL}")
    logger.info("")
    
    tester = AnalysisAPITester(API_BASE_URL)
    test_passed = True
    
    try:
        # 步骤1: 健康检查（跳过，因为可能有代理问题）
        logger.info("[SKIP] Health check skipped due to potential proxy issues")
        # if not await tester.test_health_check():
        #     logger.error("Server health check failed, please ensure server is running")
        #     return False
        
        # 步骤2: 注册用户
        if not tester.register_user():
            # 如果注册失败，尝试登录
            logger.info("Registration failed, trying login...")
            if not tester.login_user():
                logger.error("Login also failed")
                return False
        
        # 步骤3: 创建分析任务
        if not tester.create_analysis():
            logger.error("Create analysis task failed")
            return False
        
        # 列出活跃任务
        logger.info("")
        logger.info("=" * 70)
        logger.info("Check active tasks")
        logger.info("=" * 70)
        active_tasks = tester.list_active_tasks()
        if active_tasks:
            logger.info(f"Current active tasks: {active_tasks.get('total', 0)}")
        
        # 步骤4: 轮询分析进度
        if not tester.poll_analysis_progress(max_wait_seconds=300):
            logger.error("Analysis task not completed")
            test_passed = False
            
            # 获取分析详情
            detail = tester.get_analysis_detail()
            if detail:
                logger.info(f"Analysis detail: {detail}")
            
            # 获取活跃任务列表查看错误信息
            logger.info("Checking active tasks for error details...")
            active_tasks = tester.list_active_tasks()
            if active_tasks and active_tasks.get('tasks'):
                for task_id, task_info in active_tasks['tasks'].items():
                    logger.info(f"Task {task_id}: {task_info}")
                    if task_info.get('error'):
                        logger.error(f"Task error: {task_info['error']}")
        
        # 步骤5: 获取报告
        if test_passed:
            report = tester.get_analysis_report()
            if report:
                logger.info("")
                logger.info("=" * 70)
                logger.info("Report preview (first 500 chars):")
                logger.info("=" * 70)
                logger.info(report.get('content_md', '')[:500])
                
                # 保存报告
                output_dir = os.path.join(os.path.dirname(__file__), "test_output", "api_test")
                os.makedirs(output_dir, exist_ok=True)
                
                md_file = os.path.join(output_dir, f"tbygd_report_{tester.analysis_id}.md")
                html_file = os.path.join(output_dir, f"tbygd_report_{tester.analysis_id}.html")
                
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(report.get('content_md', ''))
                logger.info(f"[OK] Markdown report saved: {md_file}")
                
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(report.get('content_html', ''))
                logger.info(f"[OK] HTML report saved: {html_file}")
            else:
                logger.error("Get report failed")
                test_passed = False
        else:
            logger.error("Skip getting report step (analysis not completed)")
        
        return test_passed
        
    finally:
        tester.close()


if __name__ == "__main__":
    print("\n")
    print("=" * 70)
    print("=" + " " * 68 + "=")
    print("=" + " " * 15 + "TEBYGD Full Analysis Flow API Test" + " " * 25 + "=")
    print("=" + " " * 68 + "=")
    print("\n")
    
    try:
        success = asyncio.run(run_full_flow_test())
        
        print("\n")
        print("=" * 70)
        if success:
            print("[PASS] All tests passed")
        else:
            print("[FAIL] Some tests failed")
        print("=" * 70)
        print("\n")
        
    except Exception as e:
        print("\n")
        print("=" * 70)
        print(f"[ERROR] Test exception: {e}")
        print("=" * 70)
        print("\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)