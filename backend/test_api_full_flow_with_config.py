"""
完整的特变电工分析流程测试 - 包含 API 配置检查和设置
"""
import httpx
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8123"
TEST_EMAIL = "tebygd_test@example.com"
TEST_PASSWORD = "test123456"
TEST_COMPANY = "特变电工"
TEST_STOCK_CODE = "600089"

def test_full_flow():
    """完整的分析流程测试"""
    
    # Step 1: 登录或注册
    logger.info("=" * 70)
    logger.info("Step 1: User authentication")
    logger.info("=" * 70)
    
    # 先尝试注册
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "username": "tebygd_test"
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{API_BASE}/api/v1/auth/register", json=register_data)
        if resp.status_code == 201:
            logger.info("[OK] User registered successfully")
        elif resp.status_code == 400 and "already" in resp.text:
            logger.info("[SKIP] User already exists, trying login")
        else:
            logger.warning(f"[WARN] Registration response: {resp.status_code} {resp.text}")
        
        # 登录
        login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        resp = client.post(f"{API_BASE}/api/v1/auth/login", json=login_data)
        if resp.status_code != 200:
            logger.error(f"[FAIL] Login failed: {resp.status_code}")
            return False
        
        token = resp.json()["access_token"]
        user_id = resp.json()["user"]["id"]
        logger.info(f"[OK] Logged in successfully")
        logger.info(f"  User ID: {user_id}")
        logger.info(f"  Token: {token[:20]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: 检查 API 配置
        logger.info("")
        logger.info("=" * 70)
        logger.info("Step 2: Check API Configuration")
        logger.info("=" * 70)
        
        resp = client.get(f"{API_BASE}/api/v1/api-configs", headers=headers)
        configs = resp.json()
        logger.info(f"Found {len(configs)} API configurations")
        
        for cfg in configs:
            logger.info(f"  - Name: {cfg['config_name']}")
            logger.info(f"    Model: {cfg['model']}")
            logger.info(f"    Default: {cfg.get('is_default', False)}")
            # 不打印完整 API Key
        
        # 检查是否有默认配置
        default_config = None
        for cfg in configs:
            if cfg.get('is_default'):
                default_config = cfg
                break
        
        if not default_config and configs:
            default_config = configs[0]
            logger.info(f"No default set, using first config: {default_config['config_name']}")
        
        if not default_config:
            logger.error("[FAIL] No API configuration found!")
            logger.error("Please configure your API Key first via the frontend or API")
            logger.info("")
            logger.info("To add API config via curl:")
            logger.info(f'''curl -X POST "{API_BASE}/api/v1/api-configs" \\
  -H "Authorization: Bearer {token}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "config_name": "default",
    "api_key": "your-api-key-here",
    "model": "qwen-plus",
    "is_default": true
  }}' ''')
            return False
        
        # Step 3: 创建分析任务
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"Step 3: Create analysis task - {TEST_COMPANY} ({TEST_STOCK_CODE})")
        logger.info("=" * 70)
        
        analysis_data = {
            "company_name": TEST_COMPANY,
            "stock_code": TEST_STOCK_CODE
        }
        
        resp = client.post(f"{API_BASE}/api/v1/analyses", json=analysis_data, headers=headers)
        if resp.status_code != 201:
            logger.error(f"[FAIL] Failed to create analysis: {resp.status_code} {resp.text}")
            return False
        
        analysis = resp.json()
        analysis_id = analysis["id"]
        logger.info(f"[OK] Analysis task created")
        logger.info(f"  Analysis ID: {analysis_id}")
        logger.info(f"  Company: {analysis['company_name']}")
        logger.info(f"  Stock Code: {analysis['stock_code']}")
        logger.info(f"  Status: {analysis['status']}")
        
        # Step 4: 轮询分析进度
        logger.info("")
        logger.info("=" * 70)
        logger.info("Step 4: Poll analysis progress")
        logger.info("=" * 70)
        
        max_polls = 60  # 最多等待60次（5分钟）
        poll_interval = 5  # 每5秒轮询一次
        
        for i in range(max_polls):
            time.sleep(poll_interval)
            resp = client.get(f"{API_BASE}/api/v1/analyses/{analysis_id}/progress", headers=headers)
            
            if resp.status_code != 200:
                logger.warning(f"Poll {i+1}: HTTP {resp.status_code}")
                continue
            
            progress = resp.json()
            status = progress.get("status")
            percent = progress.get("progress", 0)
            message = progress.get("message", "")
            
            logger.info(f"Poll {i+1}/{max_polls}: {status} ({percent}%) - {message}")
            
            if status == "completed":
                logger.info("")
                logger.info("=" * 70)
                logger.info("[SUCCESS] Analysis completed!")
                logger.info("=" * 70)
                
                # 获取完整报告
                resp = client.get(f"{API_BASE}/api/v1/analyses/{analysis_id}", headers=headers)
                if resp.status_code == 200:
                    result = resp.json()
                    logger.info(f"Report preview (first 500 chars):")
                    report = result.get("report_content", "")
                    if report:
                        logger.info(report[:500] + "...")
                    else:
                        logger.info("(No report content yet)")
                return True
            
            elif status == "failed":
                logger.error("")
                logger.error("=" * 70)
                logger.error("[FAIL] Analysis failed!")
                logger.error("=" * 70)
                
                # 获取详细错误
                resp = client.get(f"{API_BASE}/api/v1/analyses/{analysis_id}", headers=headers)
                if resp.status_code == 200:
                    result = resp.json()
                    logger.info(f"Error: {result.get('error_message', 'Unknown')}")
                
                # 查看容器日志
                logger.info("")
                logger.info("Checking container logs for details...")
                return False
        
        logger.warning(f"[TIMEOUT] Analysis not completed after {max_polls * poll_interval} seconds")
        return False

if __name__ == "__main__":
    print("")
    print("=" * 70)
    print("=" * 70)
    print("=                                                                    =")
    print("=          TEBYGD Full Analysis Flow Test with API Config             =")
    print("=                                                                    =")
    print("=" * 70)
    print("")
    print(f"Test start time: {datetime.now().isoformat()}")
    print(f"Test target: {TEST_COMPANY} ({TEST_STOCK_CODE})")
    print(f"API URL: {API_BASE}")
    print("")
    
    success = test_full_flow()
    
    print("")
    print("=" * 70)
    if success:
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 70)
