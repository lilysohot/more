# 项目迁移说明

## 📋 概述

本文档说明了如何将原有的"智能投资分析师"项目迁移到新的"小财大用 (more)"项目结构中。

## 🎯 迁移目标

- **新项目名称**：小财大用 (MoreMoney)
- **新项目名称（英文）**：more
- **目标**：建立清晰的项目结构，便于开发和维护

## 📁 新目录结构

```
more/
├── README.md                  # 项目主文档
├── docker-compose.yml         # Docker 编排
├── .gitignore                 # Git 忽略配置
├── LICENSE                    # 开源协议
├── backend/                   # 后端服务
│   ├── app/                  # 应用代码
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── services/         # 业务服务
│   │   └── utils/            # 工具函数
│   ├── alembic/              # 数据库迁移
│   ├── tests/                # 测试
│   └── requirements.txt      # 依赖配置
├── frontend/                  # 前端应用
│   ├── src/                  # 源代码
│   │   ├── api/              # API 调用
│   │   ├── components/       # 组件
│   │   ├── pages/            # 页面
│   │   ├── store/            # 状态管理
│   │   └── ...
│   ├── package.json          # 依赖配置
│   └── public/               # 静态资源
└── docs/                      # 文档目录
```

## 🔄 迁移步骤

### 1. 保留的核心资源

以下内容需要从原项目保留：

#### 1.1 Skill 框架（核心分析逻辑）
```
原位置：../.trae/skills/
新位置：../skills/ (通过软链接或复制)
```

**重要文件**：
- `investment-analyst/` - 三维合一分析框架
- `analyzing-financial-statements/` - 财务比率计算
- `company-analysis-workflow/` - 工作流程
- `data-visualization/` - 可视化指导

#### 1.2 现有代码参考
```
原位置：../web-app/
用途：参考现有实现
```

**重要文件**：
- `analyzer.py` - 分析引擎实现
- `llm_client.py` - LLM 客户端
- `prompt_templates.py` - 提示词模板
- `data_collector.py` - 数据采集
- `report_generator.py` - 报告生成

#### 1.3 文档资源
```
原位置：../公司分析研报助手需求文档*.md
新位置：docs/requirements.md
```

### 2. 新建文件清单

#### 2.1 根目录文件
- ✅ `README.md` - 项目介绍
- ✅ `docker-compose.yml` - Docker 编排
- ✅ `.gitignore` - Git 忽略配置
- ✅ `LICENSE` - 开源协议

#### 2.2 后端文件
- ✅ `backend/requirements.txt` - Python 依赖
- ✅ `backend/.env.example` - 环境变量示例
- ✅ `backend/Dockerfile` - Docker 配置
- ✅ `backend/README.md` - 后端说明

#### 2.3 前端文件
- ✅ `frontend/package.json` - Node.js 依赖
- ✅ `frontend/.env.example` - 环境变量示例
- ✅ `frontend/Dockerfile` - Docker 配置
- ✅ `frontend/nginx.conf` - Nginx 配置
- ✅ `frontend/README.md` - 前端说明

#### 2.4 文档文件
- ✅ `docs/QUICKSTART.md` - 快速启动指南

### 3. 待开发文件

#### 后端（需要从头实现）
```
backend/app/
├── main.py                    # FastAPI 入口
├── config.py                  # 配置管理
├── database.py                # 数据库连接
├── api/
│   ├── auth.py               # 认证 API
│   ├── users.py              # 用户 API
│   ├── analysis.py           # 分析 API
│   └── reports.py            # 报告 API
├── models/
│   ├── user.py               # 用户模型
│   ├── api_config.py         # API 配置模型
│   ├── analysis.py           # 分析模型
│   └── report.py             # 报告模型
├── schemas/                  # Pydantic 模型（待创建）
├── services/
│   ├── auth.py               # 认证服务
│   ├── user.py               # 用户服务
│   ├── analysis.py           # 分析服务
│   ├── llm_client.py         # LLM 客户端（参考 web-app）
│   └── data_collector.py     # 数据采集（参考 web-app）
└── utils/
    ├── encryption.py         # 加密工具
    └── helpers.py            # 辅助函数
```

#### 前端（需要从头实现）
```
frontend/src/
├── main.tsx                   # 入口文件
├── App.tsx                    # 根组件
├── api/
│   ├── auth.ts               # 认证 API
│   ├── user.ts               # 用户 API
│   ├── analysis.ts           # 分析 API
│   └── reports.ts            # 报告 API
├── pages/
│   ├── Login.tsx             # 登录页
│   ├── Register.tsx          # 注册页
│   ├── Home.tsx              # 首页
│   ├── Dashboard.tsx         # 仪表盘
│   ├── Profile.tsx           # 个人中心
│   ├── ApiConfig.tsx         # API 配置
│   └── Report.tsx            # 报告预览
├── store/
│   ├── authStore.ts          # 认证状态
│   └── analysisStore.ts      # 分析状态
└── ...（其他组件和工具）
```

## 📝 迁移检查清单

### 已完成
- ✅ 创建新目录结构
- ✅ 创建 README.md
- ✅ 创建 docker-compose.yml
- ✅ 创建 .gitignore
- ✅ 创建 LICENSE
- ✅ 创建后端基础文件
- ✅ 创建前端基础文件
- ✅ 创建文档目录

### 待完成
- [ ] 实现后端数据库模型
- [ ] 实现后端 API 路由
- [ ] 实现后端业务服务
- [ ] 实现前端页面组件
- [ ] 实现前端状态管理
- [ ] 集成 Skill 框架
- [ ] 配置数据库迁移
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 完善文档

## 🔗 与原项目的关系

### 保留
- **Skill 框架**：核心分析逻辑保持不变
- **分析流程**：三维合一分析框架保持不变
- **提示词模板**：经过验证的提示词保持不变

### 改进
- **项目结构**：更清晰的前后端分离
- **技术栈**：现代化的技术选型
- **用户体验**：更好的界面设计
- **可维护性**：模块化设计，便于扩展

### 新增
- **用户系统**：注册登录、权限管理
- **API 配置**：多模型支持、自定义配置
- **历史记录**：分析报告的保存和管理
- **数据可视化**：更丰富的图表展示

## 📚 参考文档

- [项目启动指南](docs/QUICKSTART.md)
- [架构设计](docs/architecture.md)
- [开发指南](docs/development.md)
- [原项目文档](../公司分析研报助手需求文档*.md)

## 🆘 常见问题

### Q1: 为什么要创建新项目？
**A**: 为了更好地组织代码结构，实现前后端分离，提高可维护性和扩展性。

### Q2: 原有代码还能用吗？
**A**: 可以。`web-app` 目录中的代码作为参考，新项目的实现会借鉴其中的核心逻辑。

### Q3: Skill 框架如何处理？
**A**: Skill 框架保持不变，通过软链接或复制的方式在新项目中使用。

### Q4: 何时完成迁移？
**A**: 当新项目实现所有核心功能并通过测试后，可以逐步切换到新项目。

---

**小财大用 - 让投资更智慧！** 💰📈
