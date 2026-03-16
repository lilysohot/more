# 小财大用 - 项目启动指南

## 📋 前提条件

确保你的系统已安装以下软件：

- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ Docker 和 Docker Compose（可选，用于容器化部署）
- ✅ PostgreSQL 15+（如果不用 Docker）
- ✅ Redis 7+（如果不用 Docker）

## 🚀 快速启动（5 分钟）

### 方式一：Docker 一键启动（最简单）

```bash
# 1. 进入项目目录
cd more

# 2. 复制环境变量文件
cp backend/.env.example backend/.env

# 3. 编辑环境变量（可选，使用默认配置也可以）
# 修改 backend/.env 中的 DB_PASSWORD 等配置

# 4. 启动所有服务
docker-compose up -d

# 5. 等待服务启动（约 1-2 分钟）
docker-compose logs -f

# 6. 访问应用
# 前端：http://localhost:3000
# 后端：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 方式二：本地开发

#### 步骤 1：启动数据库和缓存

**使用 Docker（推荐）**：
```bash
docker run -d --name more_postgres \
  -e POSTGRES_USER=moremoney \
  -e POSTGRES_PASSWORD=moremoney123 \
  -e POSTGRES_DB=moremoney_db \
  -p 5432:5432 \
  postgres:15-alpine

docker run -d --name more_redis \
  -p 6379:6379 \
  redis:7-alpine
```

**或手动安装**：
- 安装 PostgreSQL 15+
- 安装 Redis 7+

#### 步骤 2：配置后端

```bash
cd backend

# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# 4. 编辑 .env 文件，确保数据库连接正确
# DATABASE_URL=postgresql://moremoney:moremoney123@localhost:5432/moremoney_db

# 5. 初始化数据库
alembic upgrade head

# 6. 启动后端服务
uvicorn app.main:app --reload --port 8000
```

#### 步骤 3：配置前端

```bash
cd frontend

# 1. 安装 pnpm（如果没有）
npm install -g pnpm

# 2. 安装依赖
pnpm install

# 3. 配置环境变量
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# 4. 启动前端开发服务器
pnpm dev

# 访问 http://localhost:5173
```

## ✅ 验证安装

### 1. 检查后端

访问：http://localhost:8000/health

应该返回：
```json
{
  "status": "ok"
}
```

### 2. 检查 API 文档

访问：http://localhost:8000/docs

应该看到 Swagger UI 界面

### 3. 检查前端

访问：http://localhost:3000

应该看到登录/注册页面

### 4. 测试完整流程

1. 注册一个新账号
2. 登录
3. 进入个人中心 → API 配置
4. 添加你的 LLM API 配置（如 DashScope）
5. 返回首页，输入公司名称（如"特变电工"）
6. 点击"开始分析"
7. 等待分析完成（约 2-3 分钟）
8. 查看生成的报告

## 🔧 常见问题

### 问题 1：后端启动失败

**错误**：`could not connect to server`

**解决**：
1. 检查 PostgreSQL 是否运行
2. 检查 .env 中的 DATABASE_URL 是否正确
3. 确认数据库用户和权限

### 问题 2：前端无法连接后端

**错误**：`Network Error`

**解决**：
1. 检查后端是否在 http://localhost:8000 运行
2. 检查前端 .env 中的 VITE_API_BASE_URL
3. 检查浏览器控制台是否有 CORS 错误

### 问题 3：Docker 容器启动失败

**错误**：`container exited with code 1`

**解决**：
```bash
# 查看日志
docker-compose logs backend

# 重启服务
docker-compose down
docker-compose up -d

# 重新构建
docker-compose build --no-cache
```

### 问题 4：数据库迁移失败

**错误**：`relation "users" does not exist`

**解决**：
```bash
cd backend
alembic upgrade head
```

## 📚 下一步

启动成功后，可以：

1. 📖 阅读 [架构设计](architecture.md)
2. 🔧 开始开发功能
3. 🧪 编写测试
4. 📝 查看 [API 文档](http://localhost:8000/docs)

## 🆘 获取帮助

如果遇到问题：

1. 查看日志文件
2. 检查 .env 配置
3. 查看 Docker 日志
4. 提交 Issue

---

**小财大用 - 让投资更智慧！** 🎉
