"""
测试默认API配置的连通性

使用默认配置向模型发送"你好"，验证是否能连通
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_default_api_connection():
    """
    测试默认API配置的连通性
    """
    from app.core.config import settings
    from app.services.llm_service import LLMService
    import httpx

    logger.info("=" * 60)
    logger.info("测试默认API配置连通性")
    logger.info("=" * 60)
    logger.info("")

    # 显示当前默认配置
    logger.info("当前默认配置:")
    logger.info(f"  - Provider: {settings.DEFAULT_LLM_PROVIDER}")
    logger.info(f"  - Model: {settings.DEFAULT_LLM_MODEL}")
    logger.info(f"  - API Key: {'已设置' if settings.DEFAULT_LLM_API_KEY else '未设置!'}")
    logger.info(f"  - Base URL: {settings.LLM_PROVIDER_URLS.get(settings.DEFAULT_LLM_PROVIDER)}")
    logger.info("")

    if not settings.DEFAULT_LLM_API_KEY:
        logger.error("错误: DEFAULT_LLM_API_KEY 未设置!")
        logger.error("请在 .env 文件中设置 DEFAULT_LLM_API_KEY")
        logger.error("")
        logger.error("示例:")
        logger.error("  DEFAULT_LLM_API_KEY=your-api-key-here")
        return False

    # 创建LLM服务
    config = {
        "provider": settings.DEFAULT_LLM_PROVIDER,
        "api_key": settings.DEFAULT_LLM_API_KEY,
        "model_version": settings.DEFAULT_LLM_MODEL,
    }

    logger.info(f"使用配置: {config['provider']} / {config['model_version']}")
    logger.info("")

    # 发送简单的测试消息
    test_message = "你好"
    logger.info(f"发送测试消息: '{test_message}'")
    logger.info("")

    try:
        service = LLMService(config)
        
        # 获取API URL
        base_url = config.get("base_url") or settings.LLM_PROVIDER_URLS.get(config["provider"])
        url = f"{base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        }
        
        payload = {
            "model": config["model_version"],
            "messages": [
                {"role": "user", "content": test_message}
            ],
            "max_tokens": 100,
            "temperature": 0.7,
        }
        
        logger.info(f"请求URL: {url}")
        logger.info(f"请求Payload: {payload}")
        logger.info("")
        
        logger.info("正在发送请求...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.info("")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✓ 连接成功!")
                logger.info("")
                
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.info("模型回复:")
                    logger.info("-" * 40)
                    logger.info(content)
                    logger.info("-" * 40)
                return True
            else:
                logger.error(f"✗ 连接失败: HTTP {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error("✗ 连接超时!")
        return False
    except httpx.ConnectError as e:
        logger.error(f"✗ 连接错误: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_models_endpoint():
    """
    测试 /models 端点验证API Key是否有效
    """
    from app.core.config import settings
    import httpx

    logger.info("")
    logger.info("=" * 60)
    logger.info("测试API Key有效性 (通过 /models 端点)")
    logger.info("=" * 60)
    logger.info("")

    if not settings.DEFAULT_LLM_API_KEY:
        logger.error("错误: DEFAULT_LLM_API_KEY 未设置!")
        return False

    base_url = settings.LLM_PROVIDER_URLS.get(settings.DEFAULT_LLM_PROVIDER)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {settings.DEFAULT_LLM_API_KEY}"},
            )
            
            logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✓ API Key 有效!")
                return True
            else:
                logger.error(f"✗ API Key 无效或已过期")
                logger.error(f"响应内容: {response.text[:500]}")
                return False
    except Exception as e:
        logger.error(f"✗ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    print("┌" + "─" * 58 + "┐")
    print("│" + " " * 15 + "默认API配置连通性测试" + " " * 19 + "│")
    print("└" + "─" * 58 + "┘")
    print("\n")

    try:
        # 首先测试API Key有效性
        api_key_valid = asyncio.run(test_with_models_endpoint())
        
        if api_key_valid:
            # 如果API Key有效，测试发送消息
            asyncio.run(test_default_api_connection())
        else:
            logger.warning("")
            logger.warning("由于 API Key 无效，跳过消息发送测试")
            
    except Exception as e:
        logger.error(f"测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
