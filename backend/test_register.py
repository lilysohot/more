import httpx
import json

url = "http://localhost:8004/api/v1/auth/register"
data = {
    "email": "test@example.com",
    "username": "测试用户",
    "password": "password123"
}

print(f"正在请求注册接口: {url}")
print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
print("-" * 50)

response = httpx.post(url, json=data)

print(f"状态码: {response.status_code}")
print(f"响应内容:")
try:
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except:
    print(response.text)
