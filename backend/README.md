# 小财大用 - 后端服务

基于 FastAPI 的高性能后端服务，提供用户认证、API 配置管理、公司分析和报告生成功能。

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写必要配置
```

### 4. 初始化数据库

```bash
alembic upgrade head
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

## 📁 项目结构

```
app/
├── api/          # API 路由
├── core/         # 核心配置和安全
├── models/       # 数据库模型
├── schemas/      # Pydantic 模型
├── services/     # 业务逻辑
└── utils/        # 工具函数
```

## 🔧 主要功能

- ✅ 用户注册/登录（JWT 认证）
- ✅ API 配置管理（支持多模型）
- ✅ 三维合一公司分析
- ✅ 报告生成（Markdown/HTML）
- ✅ 数据可视化

## 🏗️ 技术栈

- FastAPI
- SQLAlchemy (Async)
- PostgreSQL
- Redis
- JWT
- bcrypt

## 📚 开发指南

详见 [docs/development.md](../docs/development.md)

## 🧪 测试

```bash
pytest --cov=app
```

---

**小财大用 - 让投资更智慧！** 💰📈
