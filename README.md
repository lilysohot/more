# 小财大用 (MoreMoney)

**智能投资分析助手** - 基于"三维合一投资决策委员会框架"的专业公司分析系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-brightgreen.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## 🌟 项目简介

**小财大用**是一个智能化的公司分析研报生成系统，通过集成成熟的"三维合一投资决策委员会框架"，帮助用户快速生成专业的投资分析报告。

### 核心特性

- ✅ **三维合一分析框架**：芒格视角 + 产业专家视角 + 审计专家视角
- ✅ **用户系统**：注册登录、个人中心、历史记录管理
- ✅ **多模型支持**：预置 4 种 LLM 模型，支持用户自定义 API 配置
- ✅ **专业报告**：Markdown + HTML 双格式，包含数据可视化图表
- ✅ **安全可靠**：JWT 认证、API Key 加密存储、完善的权限控制

## 🚀 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd more

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，修改必要配置

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 访问应用
前端：http://localhost:3000
后端 API: http://localhost:8000
API 文档：http://localhost:8000/docs
```

### 方式二：本地开发

详见 [开发指南](docs/development.md)

## 📁 项目结构

```
more/
├──  README.md                  # 项目说明
├──  docker-compose.yml         # Docker 编排
├── 📄 .gitignore                 # Git 忽略配置
├── 📄 LICENSE                    # 开源协议
│
├── 📁 backend/                   # 后端服务（FastAPI）
│   ├── 📁 app/
│   │   ├── 📁 api/              # API 路由
│   │   ├── 📁 core/             # 核心配置
│   │   ├── 📁 models/           # 数据库模型
│   │   ├── 📁 schemas/          # Pydantic 模型
│   │   ├── 📁 services/         # 业务服务
│   │   └── 📁 utils/            # 工具函数
│   ├── 📁 alembic/              # 数据库迁移
│   ├── 📁 tests/                # 测试
│   ├── 📄 requirements.txt      # Python 依赖
│   └── 📄 Dockerfile
│
├──  frontend/                 # 前端应用（React + TypeScript）
│   ├── 📁 src/
│   │   ├── 📁 api/             # API 调用
│   │   ├── 📁 components/      # 组件
│   │   ├── 📁 pages/           # 页面
│   │   ├── 📁 store/           # 状态管理
│   │   ├── 📁 hooks/           # Hooks
│   │   ├── 📁 types/           # TypeScript 类型
│   │   ├── 📁 utils/           # 工具函数
│   │   ├── 📁 styles/          # 样式
│   │   └── 📁 router/          # 路由配置
│   ├── 📁 public/              # 静态资源
│   ├── 📁 tests/               # 测试
│   ├── 📄 package.json         # 依赖配置
│   └──  Dockerfile
│
├── 📁 docs/                     # 文档目录
│   ├── 📄 architecture.md      # 架构设计
│   ├── 📄 development.md       # 开发指南
│   └──  deployment.md        # 部署指南
│
└── 📁 scripts/                  # 脚本工具
    ├── 📄 setup.sh             # 初始化脚本
    └── 📄 deploy.sh            # 部署脚本
```

## 🏗️ 技术架构

### 后端技术栈

| 技术 | 选型 | 用途 |
|------|------|------|
| **框架** | FastAPI | 高性能 Web API |
| **数据库** | PostgreSQL 15 | 关系型数据库 |
| **ORM** | SQLAlchemy 2.0 | 异步 ORM |
| **缓存** | Redis 7 | 会话和结果缓存 |
| **认证** | JWT (python-jose) | Token 认证 |
| **加密** | bcrypt + cryptography | 密码和密钥加密 |

### 前端技术栈

| 技术 | 选型 | 用途 |
|------|------|------|
| **框架** | React 18 + TypeScript | 类型安全的 UI 开发 |
| **构建工具** | Vite 5 | 快速开发和构建 |
| **UI 组件** | Ant Design 5 | 企业级组件库 |
| **状态管理** | Zustand | 轻量级状态管理 |
| **图表库** | ECharts 5 | 数据可视化 |
| **HTTP 客户端** | Axios | API 请求 |

### Skill 框架

| Skill | 类型 | 作用 |
|-------|------|------|
| **investment-analyst** | 提示词 | 三维合一分析框架 |
| **analyzing-financial-statements** | Python 算法 | 财务比率计算 |
| **company-analysis-workflow** | 提示词 | 标准化工作流程 |
| **data-visualization** | 提示词 | 可视化指导 |

## 📋 功能清单

### 用户模块
- ✅ 用户注册（邮箱/手机号）
- ✅ 用户登录（JWT 认证）
- ✅ 个人中心
- ✅ API 配置管理（支持多模型）

### 分析模块
- ✅ 公司名称/代码输入
- ✅ 财务数据采集
- ✅ 财务比率计算（Python 算法）
- ✅ 三维合一分析（LLM）
- ✅ 数据交叉验证

### 报告模块
- ✅ Markdown 报告生成
- ✅ HTML 报告生成（含图表）
- ✅ 报告下载
- ✅ 报告预览

## 🔧 配置说明

### 后端环境变量

```bash
# 数据库
DATABASE_URL=postgresql://analyst:password@localhost:5432/analyst_db

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_DAYS=7

# 加密
ENCRYPTION_KEY=your-32-byte-encryption-key
```

### 前端环境变量

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 📊 预置 LLM 模型

| 模型 | 提供商 | 说明 | 推荐度 |
|------|--------|------|--------|
| **DashScope** | 阿里云 | 国产大模型，性价比高 | ⭐⭐⭐⭐⭐ |
| **Claude** | Anthropic | 强大的推理能力 | ⭐⭐⭐⭐ |
| **OpenAI GPT-4** | OpenAI | 行业领先 | ⭐⭐⭐⭐ |
| **本地部署** | 自建 | 数据隐私保护 | ⭐⭐⭐ |

## 🧪 测试

### 后端测试

```bash
cd backend
pytest --cov=app
```

### 前端测试

```bash
cd frontend
pnpm test
```

## 📚 文档

- [架构设计](docs/architecture.md)
- [开发指南](docs/development.md)
- [部署指南](docs/deployment.md)
- [API 文档](http://localhost:8000/docs)（启动后端后访问）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 开源协议

MIT License - 详见 [LICENSE](LICENSE)

## 📞 联系方式

- 项目主页：[GitHub](https://github.com/your-org/more)
- 问题反馈：[Issues](https://github.com/your-org/more/issues)
- 邮箱：contact@moremoney.com

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Ant Design](https://ant.design/)
- [ECharts](https://echarts.apache.org/)

---

**小财大用 - 让投资更智慧！** 💰📈

*Built with ❤️ using FastAPI + React*
