# FastAPI 断点调试完整指南

## 问题诊断

如果断点不生效，请检查以下几点：

### 1. 确认服务器启动方式
❌ **错误方式**：直接在终端运行 `uvicorn app.main:app --reload`
✅ **正确方式**：使用 VS Code 调试启动（F5）

### 2. 确认断点位置

对于请求 `http://localhost:8000/api/v1/auth/me`，代码执行顺序是：

```
请求 → main.py (路由注册) → auth.py (router) → deps.py (get_current_user)
```

**正确的断点位置：**
- ✅ `app/api/deps.py` 第 17 行 - `get_current_user` 函数入口
- ✅ `app/api/deps.py` 第 18 行 - `token = credentials.credentials`
- ✅ `app/api/deps.py` 第 24 行 - 数据库查询
- ✅ `app/api/auth.py` 第 45 行 - `get_current_user_info` 函数

### 3. 确认请求携带 Token

该接口需要认证，必须在请求头中添加：
```
Authorization: Bearer <your_token>
```

## 三种调试启动方法

### 方法 1：VS Code 标准调试（推荐）

1. 在 `deps.py` 第 17 行设置断点
2. 按 `F5`
3. 选择 **"Python: FastAPI (详细日志)"**
4. 等待服务器启动（看到 "Uvicorn running on http://0.0.0.0:8000"）
5. 发送请求测试

### 方法 2：使用 debug_server.py 脚本

1. 在终端运行：
   ```bash
   python debug_server.py
   ```
2. 在 VS Code 中按 `F5`
3. 选择 **"Python: Attach to Debug Server"**
4. 发送请求测试

### 方法 3：命令行调试模式

1. 在终端运行：
   ```bash
   python -m debugpy --listen 5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. 在 VS Code 中创建附加配置，连接到端口 5678
3. 发送请求测试

## 测试步骤

### 1. 先测试简单接口

访问 `http://localhost:8000/health`
- 这个接口不需要认证
- 可以在 `main.py` 第 27 行设置断点测试

### 2. 测试认证接口

**获取 Token：**
1. 先调用登录接口获取 token
2. POST `http://localhost:8000/api/v1/auth/login`
   ```json
   {
     "email": "your@email.com",
     "password": "yourpassword"
   }
   ```
3. 复制返回的 `access_token`

**测试 /me 接口：**
1. 在 `deps.py` 第 17 行设置断点
2. GET `http://localhost:8000/api/v1/auth/me`
3. 请求头添加：`Authorization: Bearer <token>`
4. 断点应该暂停

## 常见问题

### Q1: 断点显示"未验证的断点"
**解决：**
- 确保使用调试模式启动服务器
- 检查 `justMyCode` 设置为 `false`
- 重启 VS Code

### Q2: 服务器启动了，但断点不暂停
**解决：**
- 确认断点位置正确
- 确认请求路径匹配
- 检查是否有异常在断点前抛出
- 查看调试控制台错误信息

### Q3: 请求返回 401 未授权
**解决：**
- 这是正常的，说明代码执行到了认证逻辑
- 先登录获取 token
- 在请求头中添加 token

### Q4: 使用 --reload 后断点失效
**解决：**
- `--reload` 会导致调试器失效
- 已在新配置中移除该参数
- 如需热重载，使用方法 1 的标准调试模式

## 调试配置说明

已创建的配置：
- **Python: FastAPI** - 标准调试模式
- **Python: FastAPI (详细日志)** - 带详细日志的调试模式（推荐）
- **Python: Current File** - 调试当前文件
- **Python: Debug Tests** - 调试测试
- **Python: Attach to Debug Server** - 附加到已运行的调试服务器

## 验证调试器是否工作

运行测试脚本：
1. 打开 `test_breakpoint.py`
2. 在第 15 行设置断点
3. 按 `F5`，选择 "Python: Current File"
4. 如果断点暂停，说明调试器配置正确
