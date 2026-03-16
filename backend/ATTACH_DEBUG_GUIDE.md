# 附加调试器到运行中的服务器

## 问题说明

你的 FastAPI 服务器已经在 `http://localhost:8000` 运行，现在需要附加调试器来使用断点。

## 解决方案（选择一种）

### 方案 1：附加到进程（推荐，无需重启）

**步骤：**

1. **在 VS Code 中设置断点**
   - 打开 `app/api/deps.py`
   - 在第 17 行或 18 行点击设置断点

2. **启动附加调试器**
   - 按 `F5` 打开调试面板
   - 选择 **"Python: Attach by Process ID"**
   - 在弹出的进程列表中选择你的 uvicorn/python 进程
   - 找到包含 `uvicorn` 或 `python -m uvicorn` 的进程

3. **发送请求测试**
   - 访问 `http://localhost:8000/api/v1/auth/me`
   - 断点应该会暂停

**优点：** 不需要重启服务器

**缺点：** 如果服务器启动时没有加载 debugpy，可能无法附加

---

### 方案 2：重启服务器并启用调试（最可靠）

**步骤：**

1. **停止当前服务器**
   - 在运行服务器的终端按 `Ctrl+C`

2. **使用调试脚本重启**
   ```bash
   python restart_with_debug.py
   ```

3. **连接调试器**
   - 按 `F5`
   - 选择 **"Python: Attach to Running Server"**
   - 调试器会连接到端口 5678

4. **发送请求测试**
   - 访问 `http://localhost:8000/api/v1/auth/me`
   - 断点应该会暂停

**优点：** 100% 可靠，调试器完全集成

**缺点：** 需要重启服务器

---

### 方案 3：使用命令行附加（高级）

如果你的服务器是通过命令行启动的，可以用这种方式：

1. **找到进程 ID**
   ```bash
   # PowerShell
   Get-Process | Where-Object {$_.ProcessName -eq "python"} | Select-Object Id, ProcessName
   
   # 或者查找占用 8000 端口的进程
   netstat -ano | findstr :8000
   ```

2. **在 VS Code 中创建临时配置**
   - 打开 `.vscode/launch.json`
   - 修改 "Python: Attach by Process ID" 配置
   - 将 `processId` 改为具体的数字，如 `"processId": 12345`

3. **按 F5 启动附加**

---

## 快速测试

### 测试 1：验证调试器能否附加

1. 打开 `test_breakpoint.py`
2. 在第 15 行设置断点
3. 按 `F5`，选择 "Python: Current File"
4. 如果断点暂停，说明调试器配置正确

### 测试 2：测试健康检查接口

1. 打开 `app/main.py`
2. 在第 27 行设置断点
3. 使用方案 1 或 2 附加调试器
4. 访问 `http://localhost:8000/health`
5. 断点应该暂停

### 测试 3：测试认证接口

1. 打开 `app/api/deps.py`
2. 在第 17 行设置断点
3. 附加调试器
4. 发送带 token 的请求到 `/api/v1/auth/me`
5. 断点应该暂停

---

## 常见问题

### Q: "Attach by Process ID" 找不到进程？

**A:** 可能原因：
- 服务器不是 Python 进程（检查是否用 Docker 运行）
- 进程权限问题（尝试用管理员身份运行 VS Code）
- 服务器已经停止

**解决：**
- 使用方案 2 重启服务器

### Q: 附加后断点显示"未验证的断点"？

**A:** 可能原因：
- 代码路径不匹配
- 服务器启动时没有加载 debugpy

**解决：**
- 确保在 `deps.py` 中设置断点
- 使用方案 2 重启服务器

### Q: 附加成功但断点不暂停？

**A:** 可能原因：
- 请求路径不匹配
- 没有携带 token
- 异常在断点前抛出

**解决：**
- 检查请求 URL 是否正确
- 确保请求头包含 `Authorization: Bearer <token>`
- 查看调试控制台错误信息

---

## 推荐流程

**最快解决方案：**

1. 停止当前服务器（Ctrl+C）
2. 运行：`python restart_with_debug.py`
3. 按 F5，选择 "Python: Attach to Running Server"
4. 在 `deps.py` 第 17 行设置断点
5. 发送请求测试

这样可以确保 100% 能调试成功！
