import httpx
import json
import subprocess
import time
import sys

PORT = 9001
BASE_URL = f"http://localhost:{PORT}"

def test_register():
    url = f"{BASE_URL}/api/v1/auth/register"
    data = {
        "email": "test@example.com",
        "username": "测试用户",
        "password": "password123"
    }
    
    print(f"正在请求注册接口: {url}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    print("-" * 50)
    
    try:
        response = httpx.post(url, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应内容:")
        try:
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        except:
            print(response.text)
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_register()
