# AGENTS.md 中文报告

## 概述

这份中文报告用于说明当前根目录 `AGENTS.md` 的有效内容。它不是完整项目文档，而是面向后续 OpenCode 会话的纠偏说明，帮助代理优先相信真实配置、真实代码和最新规则，避免被过时 README、错误端口、错误测试假设带偏。

## 一、优先信任什么

1. 仓库里有几处 README 已经过时，不能直接照抄：
   - 仍提到不存在的 `docs/development.md`
   - 仍提到前端测试命令 `pnpm test`
   - 仍把后端访问端口写成 `8000`

2. 遇到冲突信息时，应优先信任真实配置和代码：
   - `frontend/package.json`
   - `frontend/vite.config.ts`
   - `docker-compose.yml`
   - `backend/app/core/config.py`

## 二、OpenCode 资产与仓库结构

1. 这个仓库不是统一工作区工具链，而是两个独立应用：
   - `backend/`：FastAPI 后端，入口 `app/main.py`
   - `frontend/`：Vite + React 前端，入口 `src/main.tsx`

2. 仓库根目录的 OpenCode 资产位于：
   - `skills/`
   - `agents/`
   - `references/`

3. `.agents/` 是兼容镜像，而且被 gitignore 忽略。
   - 如果希望改动被 Git 跟踪，应优先修改根目录对应文件，而不是 `.agents/`

4. 仓库里有两套含义不同的 `skills`：
   - 根目录 `skills/`：OpenCode 技能
   - `backend/skills/`：后端 Python 运行时代码包
   - 这两者不能混淆

5. 如果需要理解仓库内 persona 或编排规则，应先读 `agents/README.md`。

## 三、开发与验证命令

1. 前端使用 `pnpm`。

2. 前端命令：
   - 开发：`pnpm dev`
   - 验证顺序：`pnpm lint` 再 `pnpm build`
   - `pnpm build` 已经包含 `tsc`

3. 后端命令：
   - 安装依赖：`pip install -r requirements.txt`
   - 本地开发：`uvicorn app.main:app --reload --port 8123`

4. Docker 全栈启动：
   - `docker-compose up -d`

5. 后端命令必须从 `backend/` 目录运行：
   - 因为 `backend/app/core/config.py` 的 `.env` 加载依赖当前工作目录

## 四、端口、环境变量与运行事实

1. 本地前端开发不要默认后端在 `8000`：
   - Vite 代理实际使用 `8123`

2. `frontend/vite.config.ts` 会把 `/api/v1` 代理到 `http://localhost:8123`。

3. `frontend/src/utils/request.ts` 的请求基地址逻辑是：
   - 优先使用 `VITE_API_BASE_URL`
   - 否则回退到 `/api/v1`

4. Docker 对外端口是：
   - 前端：`3000`
   - 后端：`8123`

5. `backend/app/core/config.py` 在 `DEBUG` 模式下才会回退到本地默认数据库：
   - `postgresql://analyst:password@localhost:5432/analyst_db`

6. 这个 fallback 和 Docker Compose 的 Postgres 并不一致：
   - Docker 主机端口：`5433`
   - 数据库名：`moremoney_db`
   - 用户：`moremoney`

## 五、后端关键注意事项

1. 后端启动时会自动建表：
   - `app.main` 在 startup 中调用 `init_db()`
   - `init_db()` 内部执行 `Base.metadata.create_all()`
   - 所以本地即使不跑 Alembic，也可能已经看到表出现

2. 数据库 schema 改动不能只改模型：
   - 还要同步维护 `backend/app/models/` 和 `backend/alembic/versions/`

3. 非 `DEBUG` 模式下，后端缺少以下配置会直接拒绝启动：
   - `SECRET_KEY`
   - `ENCRYPTION_KEY`
   - `DATABASE_URL`

4. `app/services/analysis.py` 现在是实时数据优先流程：
   - 先走 Tushare
   - 失败后回退 EastMoney

5. Redis 不是硬依赖：
   - 活跃任务优先写 Redis
   - Redis 不可用时退回内存状态

## 六、前端关键接线点

1. 路由入口：`frontend/src/router/index.tsx`

2. 鉴权入口：`frontend/src/components/layout/MainLayout.tsx`
   - 这里负责鉴权门禁

3. 通用请求封装：`frontend/src/utils/request.ts`
   - 自动附加 Bearer Token
   - 收到 `401` 时会清理本地登录信息并跳转 `/login`

## 七、验证与测试现状

1. 前端没有测试脚本：
   - `frontend/package.json` 中没有 `pnpm test`

2. 后端测试位于：
   - `backend/tests/unit/`

3. 一个已验证可运行的聚焦测试命令是：
   - `pytest -q tests/unit/api/test_analysis_progress_helpers.py`

4. `backend/` 下直接运行 `pytest -q` 目前会在收集阶段失败：
   - 原因是 `tests/unit/skills/test_tushare_skill.py` 与顶层遗留的 `__pycache__/test_tushare_skill*.pyc` 发生模块名冲突

5. 因此前端当前更现实的验证方式仍然是：
   - `pnpm lint`
   - `pnpm build`

## 八、专题文档与模块内规则

1. 后端专题文档位于 `backend/docs/`：
   - [API 设计规范](backend/docs/api-patterns.md)：新增端点、响应契约、路由模式时必读
   - [数据库操作约束](backend/docs/database-rules.md)：涉及 `AsyncSession`、模型、迁移、事务边界时必读
   - [测试标准](backend/docs/testing-standards.md)：补测试、写验证结论、选择验证命令时必读

2. 前端专题文档位于 `frontend/docs/`：
   - [前端页面与 UI 规范](frontend/docs/page-ui-patterns.md)：页面拆分、路由接线、Ant Design 与 Tailwind 用法、报告工作台 UI 约定
   - [前端状态与请求规范](frontend/docs/state-request-rules.md)：Zustand 状态边界、API 封装、共享请求客户端、类型契约同步规则
   - [前端验证规范](frontend/docs/verification-rules.md)：`pnpm lint`、`pnpm build`、手工 smoke check 和当前测试限制

3. 为减少把所有规则都堆在根 `AGENTS.md`，关键规则已下沉到模块目录。

4. 后端模块规则文件：
   - `backend/app/api/AGENTS.md`：路由层规则、鉴权依赖、响应契约
   - `backend/app/services/AGENTS.md`：数据库写流程、事务边界、敏感数据处理
   - `backend/app/models/AGENTS.md`：模型字段约定、级联关系、迁移联动
   - `backend/alembic/AGENTS.md`：迁移编写要求
   - `backend/tests/AGENTS.md`：测试分层、聚焦执行、契约测试要求

5. 前端模块规则文件：
   - `frontend/src/router/AGENTS.md`：路由注册和鉴权入口规则
   - `frontend/src/pages/AGENTS.md`：页面编排、导航、局部状态边界规则
   - `frontend/src/components/AGENTS.md`：组件边界和报告 UI 规则
   - `frontend/src/api/AGENTS.md`：共享请求封装和类型化接口规则
   - `frontend/src/store/AGENTS.md`：Zustand 状态归属和异步流程规则
   - `frontend/src/utils/AGENTS.md`：请求客户端和 helper 规则
   - `frontend/src/types/AGENTS.md`：前后端契约同步和命名规则
   - `frontend/src/styles/AGENTS.md`：全局样式和报告视觉系统规则

6. 后续修改代码时，推荐阅读顺序是：
   - 先看根 `AGENTS.md`，了解仓库级事实
   - 再看对应模块内 `AGENTS.md`
   - 必要时再看 `backend/docs/` 或 `frontend/docs/` 下的专题规范

7. 根目录项目规划文档内容位于 `docs/`：
   - `docs/plans/`：存储项目计划清单，新文件名称以主题文件名称为开头，例如 `project_plan_YYYY-MM-DD.md`
   - `docs/progress/`：存储计划执行进度，新文件名称以主题文件名称为开头，例如 `project_progress_YYYY-MM-DD.md`
   - 项目专题文档当前直接存放在根 `docs/` 下；如果新增按日期命名的专题文档，文件名称以主题文件名称为开头，例如 `project_doc_YYYY-MM-DD.md`
        
8. `docs/plans/` 文件内容格式：
   - 文件名称：主题文件名称_YYYY-MM-DD.md，例如 `project_plan_YYYY-MM-DD.md`
   - 内容：项目计划清单，用于从项目专属文档中提取成可执行的任务清单
   - 任务清单格式：以 `[x] 任务描述`
   - 例如：`[x] 完善后端专题规范`
   - 任务完成并通过测试和审核后，将任务描述前的 `[x]` 改成 `[√]`，并添加到 `docs/progress/` 目录下对应文件中
   - 例如：`[√] 完善后端专题规范`
9. `docs/progress/` 文件内容格式：
   - 文件名称：主题文件名称_YYYY-MM-DD.md，例如 `project_progress_YYYY-MM-DD.md`
   - 内容：计划执行进度，用于记录项目计划清单执行情况

## 九、本地环境与调试

1. `.env` 文件已被 gitignore 忽略。

2. 仓库里已经存在本地 `frontend/.env` 和 `backend/.env`：
   - 除非用户明确要求，不要覆盖或提交这些文件

3. Docker 后端启用了 `debugpy`：
   - 调试端口：`5678`

4. 共用的 VS Code 附加调试配置位于：
   - `.vscode/launch.json`

## 十、这份 AGENTS.md 的实际作用

1. 它不是完整项目文档，而是仓库级纠偏文档。
2. 它要求代理优先相信真实配置和真实代码，而不是过时说明。
3. 它把最容易猜错的关键事实提前讲清楚：
   - 命令
   - 端口
   - 环境加载方式
   - 测试现状
   - 后端分析链路是否已接入实时数据
   - 规则文档和模块内规则文件分别放在哪里

## 十一、总结

最新版 `AGENTS.md` 的核心作用可以概括为：

1. 避免相信过时 README。
2. 明确前后端真实启动方式。
3. 说明 Vite 代理和 Docker 端口的真实关系。
4. 提醒后端启动会自动建表，但迁移仍需维护。
5. 说明分析服务已经是 Tushare 优先、EastMoney 回退。
6. 说明前端没有测试脚本，但后端存在可运行的聚焦单测。
7. 提醒完整 `pytest -q` 目前会被遗留 `pyc` 冲突阻塞。
8. 说明后端专题规范已经移动到 `backend/docs/`，并且关键规则已下沉到模块内 `AGENTS.md`。
9. 说明前端专题规范已经建立在 `frontend/docs/`，并补充了页面、状态、请求、样式和验证规则。
