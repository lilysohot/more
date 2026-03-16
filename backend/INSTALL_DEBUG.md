# Docker 调试模式安装指南

## 你的情况

- 主 docker-compose.yml 在：`C:\Users\admin\Desktop\智能投资分析师\more\docker-compose.yml`
- 当前运行的容器名：`more_backend`
- 需要添加调试端口 5678

## 解决方案（两种选择）

### 方案 1：修改主 docker-compose.yml（推荐）

**步骤：**

1. **打开文件**
   - 路径：`C:\Users\admin\Desktop\智能投资分析师\more\docker-compose.yml`

2. **找到 backend 服务部分**（第 38-62 行）

3. **在 ports 部分添加调试端口**
   
   找到这段：
   ```yaml
   ports:
     - "8000:8000"
   ```
   
   修改为：
   ```yaml
   ports:
     - "8000:8000"
     - "5678:5678"  # 调试端口
   ```

4. **添加 command（可选，用于自动启动调试器）**
   
   在 `restart: unless-stopped` 上面添加：
   ```yaml
   command: >
     python -m debugpy --listen 0.0.0.0:5678 --wait-for-client 
     -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

5. **保存文件并重启容器**
   ```bash
   cd C:\Users\admin\Desktop\智能投资分析师\more
   docker-compose up -d --build
   ```

---

### 方案 2：使用备用配置文件

如果不想修改主文件，可以使用我创建的备用配置文件：

**步骤：**

1. **停止当前容器**
   ```bash
   cd C:\Users\admin\Desktop\智能投资分析师\more
   docker-compose down
   ```

2. **使用调试配置启动**
   ```bash
   docker-compose -f docker-compose.debug.full.yml up -d
   ```

   注意：这个文件在 `backend` 目录中

---

## 验证安装

**1. 检查容器状态**
```bash
docker ps
```

应该看到：
```
PORTS: 0.0.0.0:8000->8000/tcp, 0.0.0.0:5678->5678/tcp
```

**2. 测试调试端口**
```bash
Test-NetConnection localhost -Port 5678
```

应该显示 `TcpTestSucceeded : True`

**3. 连接 VS Code 调试器**
- 按 `F5`
- 选择 **"Docker: Attach to Container"**
- 在 `app/api/deps.py` 第 17 行设置断点
- 发送请求测试

---

## 快速命令参考

```bash
# 停止所有服务
cd C:\Users\admin\Desktop\智能投资分析师\more
docker-compose down

# 重新启动（使用调试配置）
docker-compose up -d --build

# 查看日志
docker logs -f more_backend

# 检查端口
docker port more_backend
```

---

## 已创建的文件

- `docker-compose.debug.full.yml` - 完整的调试配置（可以使用）
- `.vscode/launch.json` - 已配置 Docker 调试
- `DOCKER_DEBUG_GUIDE.md` - 详细指南

---

## 推荐操作

**最简单的方式：**

1. 打开 `C:\Users\admin\Desktop\智能投资分析师\more\docker-compose.yml`
2. 在第 51 行添加 `- "5678:5678"`
3. 保存
4. 运行：
   ```bash
   cd C:\Users\admin\Desktop\智能投资分析师\more
   docker-compose up -d --build
   ```
5. 在 VS Code 中按 F5，选择 "Docker: Attach to Container"
6. 开始调试！
