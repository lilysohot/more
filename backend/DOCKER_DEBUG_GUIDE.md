# Docker 容器断点调试完整指南

## 你的需求

服务器运行在 Docker 容器中（`http://localhost:8000`），想要在 VS Code 中设置断点调试容器中的应用。

## 解决方案

### 步骤 1：停止当前容器

```bash
docker stop moremoney_backend
docker rm moremoney_backend
```

或者如果你是用 docker-compose 启动的：
```bash
docker-compose down
```

---

### 步骤 2：使用调试配置重启容器

**使用 docker-compose.debug.yml 启动：**

```bash
docker-compose -f docker-compose.debug.yml up -d
```

这会：
- 构建包含 debugpy 的镜像
- 启动容器并暴露 5678 端口（调试器端口）
- 挂载本地代码到容器（修改代码会自动重载）
- 等待调试器连接

---

### 步骤 3：连接 VS Code 调试器

1. **在 VS Code 中设置断点**
   - 打开 `app/api/deps.py`
   - 在第 17 行点击设置断点
   - 或打开 `app/api/auth.py` 第 45 行设置断点

2. **启动调试**
   - 按 `F5`
   - 选择 **"Docker: Attach to Container"**
   - VS Code 会连接到容器的 5678 端口

3. **发送请求测试**
   - 访问 `http://localhost:8000/api/v1/auth/me`
   - 确保请求头包含：`Authorization: Bearer <your_token>`
   - 断点应该会暂停！

---

## 工作原理

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   VS Code   │ ──────→ │  Docker      │ ──────→ │   你的      │
│  调试器     │  5678   │  容器        │  8000   │   应用      │
│  (本地)     │ ←────── │  (debugpy)   │ ←────── │  (FastAPI)  │
└─────────────┘         └──────────────┘         └─────────────┘
```

1. 容器中的 debugpy 监听 5678 端口
2. VS Code 连接到这个端口
3. 当请求到达 8000 端口时，debugpy 会通知 VS Code
4. 在断点处暂停执行

---

## 验证步骤

### 测试 1：检查容器状态

```bash
docker ps | grep moremoney
```

应该看到：
- 端口映射：`0.0.0.0:8000->8000/tcp, 0.0.0.0:5678->5678/tcp`
- 状态：`Up`

### 测试 2：检查调试器端口

```bash
telnet localhost 5678
```

或者：
```bash
Test-NetConnection localhost -Port 5678
```

应该能连接成功。

### 测试 3：简单接口测试

1. 打开 `app/main.py`
2. 在第 27 行（`health_check` 函数）设置断点
3. 按 F5，选择 "Docker: Attach to Container"
4. 访问 `http://localhost:8000/health`
5. 断点应该暂停！

### 测试 4：认证接口测试

1. 打开 `app/api/deps.py`
2. 在第 17 行设置断点
3. 附加调试器
4. 发送带 token 的请求到 `/api/v1/auth/me`
5. 断点应该暂停！

---

## 常用命令

### 查看容器日志
```bash
docker logs -f moremoney_backend
```

### 进入容器
```bash
docker exec -it moremoney_backend bash
```

### 重启容器
```bash
docker-compose -f docker-compose.debug.yml restart
```

### 停止容器
```bash
docker-compose -f docker-compose.debug.yml down
```

### 重新构建（修改了 Dockerfile 或 requirements.txt 后）
```bash
docker-compose -f docker-compose.debug.yml up -d --build
```

---

## 热重载

由于在 `docker-compose.debug.yml` 中配置了代码挂载：
```yaml
volumes:
  - .:/app
```

当你修改本地代码时，容器中的代码会自动更新，无需重启容器。

**但是注意：** 如果修改了 `Dockerfile` 或 `requirements.txt`，需要重新构建：
```bash
docker-compose -f docker-compose.debug.yml up -d --build
```

---

## 常见问题

### Q1: 连接不上 5678 端口？

**A:** 检查：
1. 容器是否正常启动：`docker ps`
2. 端口是否映射：查看 `docker inspect moremoney_backend`
3. 防火墙是否阻止：临时关闭防火墙测试

**解决：**
```bash
# 查看容器详细信息
docker inspect moremoney_backend | grep -A 20 "Ports"

# 重启容器
docker-compose -f docker-compose.debug.yml down
docker-compose -f docker-compose.debug.yml up -d
```

---

### Q2: 断点显示"未验证的断点"？

**A:** 可能原因：
- 代码路径映射不正确
- 容器中的代码和本地不一致

**解决：**
1. 检查 `.vscode/launch.json` 中的 `pathMappings`：
   ```json
   {
     "localRoot": "${workspaceFolder}",
     "remoteRoot": "/app"
   }
   ```
2. 确保容器使用了卷挂载
3. 重启容器确保代码同步

---

### Q3: 调试器连接后，断点不暂停？

**A:** 检查：
1. 请求路径是否正确
2. 是否携带了有效的 token
3. 查看 VS Code 调试控制台的错误信息

**解决：**
- 先测试 `/health` 接口（不需要认证）
- 确保调试器已连接（VS Code 底部状态栏显示 "debugpy"）

---

### Q4: 容器启动失败？

**A:** 查看日志：
```bash
docker-compose -f docker-compose.debug.yml logs
```

常见问题：
- 端口被占用：修改 `docker-compose.debug.yml` 中的端口映射
- 依赖缺失：确保 `requirements.txt` 包含所有依赖
- 代码错误：检查 Python 语法

---

### Q5: 如何回到生产模式（不带调试器）？

**A:** 使用原始的 docker-compose 配置：

```bash
docker-compose down
docker-compose up -d
```

或者直接：
```bash
docker stop moremoney_backend
docker rm moremoney_backend
# 然后用你原来的方式启动容器
```

---

## 快速开始（5 分钟）

```bash
# 1. 停止当前容器
docker stop moremoney_backend
docker rm moremoney_backend

# 2. 使用调试配置启动
docker-compose -f docker-compose.debug.yml up -d

# 3. 等待容器启动
docker logs -f moremoney_backend

# 4. 在 VS Code 中按 F5
# 5. 选择 "Docker: Attach to Container"
# 6. 在 deps.py 第 17 行设置断点
# 7. 发送请求测试

# 完成！
```

---

## 已创建的文件

- `docker-compose.debug.yml` - Docker Compose 调试配置
- `Dockerfile` - 已更新，包含 debugpy 安装
- `.vscode/launch.json` - 已更新 Docker 调试配置
- `DOCKER_DEBUG_GUIDE.md` - 本文件

---

## 下一步

1. 停止当前容器
2. 运行 `docker-compose -f docker-compose.debug.yml up -d`
3. 按 F5 连接调试器
4. 开始调试！
