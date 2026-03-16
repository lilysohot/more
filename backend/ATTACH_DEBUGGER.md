# 附加调试器到运行中的服务器 - 最终解决方案

## 你的情况

服务器 `http://localhost:8000` 已经在运行，但不是通过 VS Code 调试模式启动的，所以断点不生效。

## 解决方案（按推荐顺序）

### 方案 1：重启服务器并启用调试（最可靠，强烈推荐）

这是**最简单且 100% 有效**的方法：

**步骤：**

1. **停止当前服务器**
   - 找到运行服务器的终端窗口
   - 按 `Ctrl+C` 停止

2. **使用调试脚本重启**
   ```bash
   python restart_with_debug.py
   ```
   
   这会：
   - 启动带调试器的服务器
   - 监听端口 5678

3. **连接调试器**
   - 按 `F5`
   - 选择 **"Python: Attach to Running Server"**
   - 调试器会自动连接

4. **设置断点**
   - 打开 `app/api/deps.py`
   - 在第 **17 行**（`async def get_current_user(`）设置断点
   - 或在第 **18 行**（`token = credentials.credentials`）设置断点

5. **测试**
   - 发送请求到 `http://localhost:8000/api/v1/auth/me`
   - 确保请求头包含：`Authorization: Bearer <your_token>`
   - 断点应该会暂停！

---

### 方案 2：直接通过 VS Code 启动调试（简单）

**步骤：**

1. **停止当前服务器**（Ctrl+C）

2. **直接按 F5 启动**
   - 按 `F5`
   - 选择 **"Python: FastAPI (详细日志)"**
   - VS Code 会自动以调试模式启动服务器

3. **设置断点并测试**
   - 在 `deps.py` 第 17 行设置断点
   - 发送请求测试

---

### 方案 3：附加到进程（无需重启，但可能不生效）

如果你的服务器启动时已经加载了 debugpy，可以直接附加：

**步骤：**

1. **按 F5**
2. **选择 "Python: Attach by Process ID"**
3. **选择 uvicorn 或 python 进程**
4. **发送请求测试**

**注意：** 如果你的服务器启动时没有加载 debugpy，这个方法不会生效。此时请使用方案 1 或 2。

---

## 为什么方案 1 和 2 最可靠？

因为调试器需要在服务器启动时就注入代码。如果服务器已经运行，再附加调试器可能会错过一些初始化过程。

## 快速验证

### 测试 1：简单接口（推荐先测试这个）

1. 打开 `app/main.py`
2. 在第 **27 行**（`async def health_check():`）设置断点
3. 使用方案 1 或 2 启动
4. 访问 `http://localhost:8000/health`
5. 断点应该暂停！

### 测试 2：认证接口

1. 打开 `app/api/deps.py`
2. 在第 **17 行** 设置断点
3. 启动调试
4. 发送带 token 的请求到 `/api/v1/auth/me`
5. 断点应该暂停！

---

## 常见问题

### Q: 我没有 token，怎么测试 /me 接口？

**A:** 先登录获取 token：

1. 调用登录接口：
   - POST `http://localhost:8000/api/v1/auth/login`
   - Body:
     ```json
     {
       "email": "your@email.com",
       "password": "yourpassword",
       "remember_me": true
     }
     ```

2. 复制返回的 `access_token`

3. 在请求头中添加：
   ```
   Authorization: Bearer <复制的 token>
   ```

### Q: 重启后还是不能断点？

**A:** 检查：
- 确保在 `deps.py` 而不是 `auth.py` 中设置断点
- 确保请求路径正确：`/api/v1/auth/me`
- 确保请求携带了有效的 token
- 查看 VS Code 调试控制台的错误信息

### Q: 断点显示"未验证的断点"？

**A:** 这通常意味着：
- 服务器不是以调试模式运行的
- 代码路径不匹配

**解决：** 使用方案 1 重启服务器

---

## 推荐流程（5 分钟搞定）

1. ✅ 停止当前服务器（Ctrl+C）
2. ✅ 运行：`python restart_with_debug.py`
3. ✅ 按 F5，选择 "Python: Attach to Running Server"
4. ✅ 在 `deps.py` 第 17 行设置断点
5. ✅ 发送请求测试
6. ✅ 完成！

---

## 已创建的文件

- `restart_with_debug.py` - 调试启动脚本（使用这个）
- `.vscode/launch.json` - 调试配置（已更新）
- `ATTACH_DEBUG_GUIDE.md` - 详细指南
- `DEBUG_GUIDE.md` - 完整调试手册
