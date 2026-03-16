# Docker 安装指南

## ❌ 检查结果

很遗憾，你的本机**没有安装 Docker**。

---

## 🎯 解决方案

### 方案一：安装 Docker Desktop（推荐）

**适用系统**：Windows 10/11 Pro、Windows 10/11 Home

#### 步骤 1：下载 Docker Desktop

访问官网下载：
- **官方下载**：https://www.docker.com/products/docker-desktop/
- **国内镜像**：https://www.docker.com.cn/

#### 步骤 2：安装 Docker Desktop

1. 运行下载的安装程序
2. 按照安装向导进行安装
3. 重启计算机（如果需要）
4. 启动 Docker Desktop

#### 步骤 3：验证安装

打开 PowerShell 或命令提示符，运行：

```bash
docker --version
docker-compose --version
```

如果显示版本号，说明安装成功！

#### 系统要求

- **操作系统**：Windows 10 64-bit Pro 或更高版本
- **内存**：至少 4GB RAM（推荐 8GB）
- **硬盘**：至少 10GB 可用空间
- **BIOS**：需要启用虚拟化（VT-x/AMD-V）

---

### 方案二：使用本地开发环境（无需 Docker）

如果你不想安装 Docker，可以选择本地开发方式。

#### 前提条件

需要安装：
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ PostgreSQL 15+
- ✅ Redis 7+

#### 步骤 1：安装 Python

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.11+
3. 安装时勾选"Add Python to PATH"

验证安装：
```bash
python --version
```

#### 步骤 2：安装 Node.js

1. 访问 https://nodejs.org/
2. 下载 LTS 版本（Node.js 18+）
3. 运行安装程序

验证安装：
```bash
node --version
npm --version
```

#### 步骤 3：安装 PostgreSQL

1. 访问 https://www.postgresql.org/download/windows/
2. 下载并安装 PostgreSQL 15+
3. 记住安装时设置的密码

验证安装：
```bash
psql --version
```

#### 步骤 4：安装 Redis（Windows 版本）

**方式 A：使用 WSL（推荐）**
```bash
# 在 WSL 中安装 Redis
wsl
sudo apt update
sudo apt install redis-server
```

**方式 B：使用 Windows 原生版本**
1. 访问 https://github.com/microsoftarchive/redis/releases
2. 下载 Redis-x64-*.zip
3. 解压并运行 `redis-server.exe`

验证安装：
```bash
redis-cli --version
```

#### 步骤 5：启动后端服务

```bash
cd more\backend

# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy .env.example .env

# 4. 编辑 .env 文件，配置数据库连接
# DATABASE_URL=postgresql://moremoney:moremoney123@localhost:5432/moremoney_db

# 5. 初始化数据库
alembic upgrade head

# 6. 启动服务
uvicorn app.main:app --reload --port 8000
```

#### 步骤 6：启动前端服务

```bash
cd more\frontend

# 1. 安装 pnpm
npm install -g pnpm

# 2. 安装依赖
pnpm install

# 3. 配置环境变量
copy .env.example .env

# 4. 启动开发服务器
pnpm dev

# 访问 http://localhost:5173
```

---

### 方案三：使用 Gitpod/GitHub Codespaces（云端开发）

如果你不想在本地安装任何软件，可以使用云端开发环境。

#### GitHub Codespaces

1. 将项目推送到 GitHub
2. 点击 "Code" 按钮
3. 选择 "Create codespace on main"
4. 在云端开发环境中运行项目

#### Gitpod

1. 将项目推送到 GitLab/GitHub/Bitbucket
2. 访问 https://gitpod.io
3. 输入项目 URL
4. 开始开发

---

## 🎯 推荐方案

### 如果你有管理员权限且电脑配置较好
👉 **方案一：安装 Docker Desktop**
- 优点：一键启动，环境隔离，与生产环境一致
- 缺点：需要下载安装，占用一定空间

### 如果你不想安装 Docker 或没有管理员权限
👉 **方案二：本地开发环境**
- 优点：灵活控制，不需要额外软件
- 缺点：需要手动安装多个软件，配置较复杂

### 如果你想快速体验
👉 **方案三：云端开发**
- 优点：无需本地安装，开箱即用
- 缺点：需要网络连接，可能有使用限制

---

## 📚 安装后的下一步

### 如果选择了 Docker 方案

安装完成后，运行：

```bash
cd more

# 配置环境变量
copy backend\.env.example backend\.env

# 一键启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

访问：
- 前端：http://localhost:3000
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 如果选择了本地开发方案

按照 [docs/QUICKSTART.md](docs/QUICKSTART.md) 中的"方式二：本地开发"进行配置。

---

## 🔧 常见问题

### Q1: Docker Desktop 安装失败？
**A**: 确保已启用 BIOS 虚拟化，并且 Windows 版本支持 Hyper-V。

### Q2: PostgreSQL 连接失败？
**A**: 检查服务是否运行，用户名密码是否正确。

### Q3: 端口被占用？
**A**: 修改 docker-compose.yml 或 .env 文件中的端口配置。

### Q4: 网络问题无法下载？
**A**: 使用国内镜像源，如清华镜像、阿里云镜像。

---

## 📞 需要帮助？

- 📖 查看 [QUICKSTART.md](docs/QUICKSTART.md)
- 💬 提交 Issue
- 📧 联系开发团队

---

**祝你安装顺利！** 🎉
