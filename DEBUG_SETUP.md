# Docker 后端调试配置指南

## 📋 配置说明

已配置完成 VSCode 远程调试 Docker 容器中的 Python 后端服务。

## 🔧 配置内容

### 1. Dockerfile
- ✅ 已安装 `debugpy`
- ✅ 启动命令已修改为调试模式
- ✅ 监听端口：`5678`

### 2. docker-compose.yml
- ✅ 已暴露调试端口 `5678`

### 3. VSCode 配置
- ✅ 已创建 `.vscode/launch.json`
- ✅ 配置了路径映射：本地 `backend` ↔ 容器 `/app`

## 🚀 使用步骤

### 第一步：重启 Docker 容器

```powershell
cd C:\Users\admin\Desktop\智能投资分析师\more

# 停止并重新构建容器
docker-compose down
docker-compose up -d --build backend
```

### 第二步：在 VSCode 中附加调试器

1. **打开项目文件夹**：`C:\Users\admin\Desktop\智能投资分析师\more`

2. **设置断点**：
   - 在后端代码的任何位置点击行号左侧
   - 例如：`backend/app/main.py` 的 `health_check()` 函数

3. **启动调试**：
   - 按 `F5` 或点击"运行和调试"面板
   - 选择 **"Python: Docker 远程调试"**
   - 点击绿色启动按钮

4. **等待连接**：
   - 调试器会连接到容器的 `5678` 端口
   - 状态栏显示"已附加"

### 第三步：触发接口请求

访问：`http://localhost:8000/health`

VSCode 会在你设置的断点处暂停，可以：
- 查看变量
- 单步调试
- 查看调用栈
- 在调试控制台执行代码

## 💡 调试技巧

### 1. 非阻塞模式（可选）

如果不想每次启动都等待调试器连接，修改 Dockerfile：

```dockerfile
# 移除 --wait-for-client 参数
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

这样服务会立即启动，你可以稍后再附加调试器。

### 2. 快速重启调试

```powershell
# 重启后端容器
docker-compose restart backend

# 查看日志
docker-compose logs -f backend
```

### 3. 验证调试器是否运行

```powershell
# 查看容器进程
docker exec more_backend ps aux | grep debugpy
```

## ⚠️ 注意事项

1. **首次启动会等待**：
   - 当前配置包含 `--wait-for-client`，服务会等待 VSCode 连接后才启动
   - 必须先启动调试器，再访问接口

2. **端口占用**：
   - 确保 `5678` 端口未被占用
   - 如有冲突，修改 `docker-compose.yml` 和 `launch.json` 中的端口号

3. **代码热更新**：
   - 已配置 volume 映射，修改代码后需要重启容器
   - `docker-compose restart backend`

## 🎯 调试配置参数说明

```json
{
  "name": "Python: Docker 远程调试",
  "type": "debugpy",           // 调试器类型
  "request": "attach",         // 附加到已有进程
  "connect": {
    "host": "localhost",       // Docker 暴露的主机
    "port": 5678               // 调试端口
  },
  "pathMappings": [
    {
      "localRoot": "${workspaceFolder}/backend",  // 本地代码路径
      "remoteRoot": "/app"      // 容器内代码路径
    }
  ],
  "justMyCode": false          // 可以调试第三方库代码
}
```

## ✅ 验证清单

- [ ] Dockerfile 已修改为调试模式
- [ ] docker-compose.yml 已暴露 5678 端口
- [ ] launch.json 已创建
- [ ] 重启了 backend 容器
- [ ] VSCode 成功附加到容器
- [ ] 断点可以正常触发
- [ ] 可以查看变量和单步调试

---

**配置完成时间**: 2026-03-11  
**调试端口**: 5678  
**API 端口**: 8000  
**状态**: ⏳ 等待重启容器验证
