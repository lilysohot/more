# ⚠️ Docker 未安装 - 解决方案指南

## 📋 检查结果

**检查状态**：❌ 本机未安装 Docker

**检查时间**：2026 年 3 月 6 日

---

## 🎯 三种解决方案

### ✅ 方案一：安装 Docker Desktop（推荐）

**适合人群**：希望快速部署，环境隔离

**安装步骤**：

1. **下载 Docker Desktop**
   - 官网：https://www.docker.com/products/docker-desktop/
   - 国内镜像：https://www.docker.com.cn/

2. **安装并启动**
   - 运行安装程序
   - 按照向导完成安装
   - 重启计算机（如果需要）

3. **验证安装**
   ```bash
   docker --version
   docker-compose --version
   ```

4. **启动项目**
   ```bash
   cd more
   copy backend\.env.example backend\.env
   docker-compose up -d
   ```

**优点**：
- ✅ 一键启动，简单方便
- ✅ 环境隔离，不影响系统
- ✅ 与生产环境一致

**缺点**：
- ❌ 需要下载安装（约 500MB）
- ❌ 需要启用虚拟化
- ❌ 占用一定系统资源

---

### ✅ 方案二：本地开发环境（无需 Docker）

**适合人群**：不想安装 Docker，或没有管理员权限

**需要安装的软件**：

| 软件 | 版本 | 下载地址 | 必须 |
|------|------|----------|------|
| Python | 3.11+ | https://www.python.org/downloads/ | ✅ |
| Node.js | 18+ | https://nodejs.org/ | ✅ |
| PostgreSQL | 15+ | https://www.postgresql.org/download/windows/ | ✅ |
| Redis | 7+ | https://github.com/microsoftarchive/redis/releases | ✅ |

**快速检查脚本**：

我已经为你创建了检查脚本，运行即可：

```bash
cd more
start-dev.bat
```

这个脚本会自动检查所有依赖是否安装。

**手动启动步骤**：

#### 1. 启动数据库和缓存

**PostgreSQL**：
- 确保服务已启动
- 创建数据库：
  ```sql
  CREATE DATABASE moremoney_db;
  CREATE USER moremoney WITH PASSWORD 'moremoney123';
  GRANT ALL PRIVILEGES ON DATABASE moremoney_db TO moremoney;
  ```

**Redis**：
- Windows 用户：运行 `redis-server.exe`
- WSL 用户：运行 `wsl redis-server`

#### 2. 配置后端

```bash
cd more\backend

# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
copy .env.example .env

# 4. 编辑 .env 文件
# 修改 DATABASE_URL=postgresql://moremoney:moremoney123@localhost:5432/moremoney_db

# 5. 初始化数据库
alembic upgrade head

# 6. 启动后端
uvicorn app.main:app --reload --port 8000
```

#### 3. 配置前端

```bash
cd more\frontend

# 1. 安装 pnpm（如果还没有）
npm install -g pnpm

# 2. 安装依赖
pnpm install

# 3. 配置环境
copy .env.example .env

# 4. 启动前端
pnpm dev
```

**访问地址**：
- 前端：http://localhost:5173
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

**优点**：
- ✅ 不需要 Docker
- ✅ 灵活控制每个组件
- ✅ 适合开发调试

**缺点**：
- ❌ 需要手动安装多个软件
- ❌ 配置较复杂
- ❌ 环境与生产环境可能有差异

---

### ✅ 方案三：云端开发（无需本地安装）

**适合人群**：想快速体验，不想安装任何软件

**选项**：

#### GitHub Codespaces
1. 将项目推送到 GitHub
2. 点击 "Code" → "Create codespace"
3. 在云端环境中运行

#### Gitpod
1. 将项目推送到 GitLab/GitHub
2. 访问 https://gitpod.io
3. 输入项目 URL 开始

**优点**：
- ✅ 无需本地安装
- ✅ 开箱即用
- ✅ 性能强劲

**缺点**：
- ❌ 需要网络连接
- ❌ 有使用时长限制
- ❌ 需要 GitHub/GitLab 账号

---

## 🎯 我的推荐

### 如果你是初学者
👉 **方案二：本地开发环境**
- 可以学习每个组件的作用
- 更灵活，出错容易排查
- 但需要一定动手能力

### 如果你希望快速部署
👉 **方案一：安装 Docker Desktop**
- 最简单，一键启动
- 但需要下载安装

### 如果你只是想试试
👉 **方案三：云端开发**
- 最快，几分钟就能体验
- 但需要网络

---

## 📚 详细文档

- **Docker 安装指南**：[docs/DOCKER_INSTALL.md](docs/DOCKER_INSTALL.md)
- **快速启动指南**：[docs/QUICKSTART.md](docs/QUICKSTART.md)
- **项目 README**：[README.md](README.md)

---

## 🔧 快速检查

运行以下命令检查环境：

```bash
cd more
start-dev.bat
```

这个脚本会自动检查：
- ✅ Python 是否安装
- ✅ Node.js 是否安装
- ✅ pnpm 是否安装
- ✅ PostgreSQL 是否安装
- ✅ Redis 是否安装

---

## 📞 需要帮助？

如果遇到问题：

1. 查看 [docs/DOCKER_INSTALL.md](docs/DOCKER_INSTALL.md) 获取详细安装指南
2. 查看 [docs/QUICKSTART.md](docs/QUICKSTART.md) 获取启动指南
3. 提交 Issue 获取帮助

---

## 🎉 总结

虽然你没有安装 Docker，但有**三种方案**可以选择：

1. **安装 Docker Desktop** - 最简单，推荐！
2. **本地开发环境** - 无需 Docker，适合学习
3. **云端开发** - 最快体验，无需安装

**推荐选择**：安装 Docker Desktop，然后一键启动项目！

---

**祝你开发顺利！** 🚀
