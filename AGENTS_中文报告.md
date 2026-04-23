# AGENTS.md 中文报告

## 概述
该 `AGENTS.md` 是面向未来 OpenCode 会话的仓库操作说明，重点不是介绍项目功能，而是帮助智能代理快速建立正确上下文，避免被过时文档误导、避免跑错命令、连错端口或误判系统行为。

## 一、核心结论
1. 这个仓库不是统一管理的 monorepo，而是两个独立应用组成：
   - `backend/`：FastAPI 后端，入口是 `app/main.py`
   - `frontend/`：Vite + React 前端，入口是 `src/main.tsx`

2. 仓库中存在过时文档，不能优先相信 README 类说明。
   - 例如仍提到不存在的 `docs/development.md`
   - 仍提到前端测试命令 `pnpm test`
   - 仍将后端端口写成 `8000`

3. 应优先依据“可执行配置”判断真实情况。
   - 如 `package.json`
   - `vite.config.ts`
   - `docker-compose.yml`
   - 后端配置代码 `backend/app/core/config.py`

## 二、已验证的开发命令
`AGENTS.md` 明确给出了当前可确认有效的命令：

1. 前端相关
   - 启动开发环境：`pnpm dev`
   - 代码检查：`pnpm lint`
   - 生产构建：`pnpm build`

2. 后端相关
   - 安装依赖：`pip install -r requirements.txt`
   - 本地开发启动：`uvicorn app.main:app --reload --port 8123`

3. Docker 全栈启动
   - `docker-compose up -d`

## 三、端口与请求路由的关键事实
这是本文件里最容易避免踩坑的一部分：

1. 本地前端开发时，不要默认后端跑在 `8000`
   - 实际应按 `8123` 理解

2. 前端开发代理配置
   - `frontend/vite.config.ts` 将 `/api/v1` 代理到 `http://localhost:8123`

3. 前端请求基础地址逻辑
   - `frontend/src/utils/request.ts` 优先读取 `VITE_API_BASE_URL`
   - 如果未设置，则回退为 `/api/v1`

4. Docker 对外端口
   - 后端：`8123`
   - 前端：`3000`

## 四、后端的重要注意事项
这部分是给代理避免误判系统行为的高价值信息：

1. 启动时会自动建表
   - `app.main` 启动时调用 `init_db()`
   - `init_db()` 内部执行 `Base.metadata.create_all()`
   - 这意味着本地即使不跑 Alembic，也可能看到表已被创建

2. Alembic 依然存在，不能忽略迁移一致性
   - 如果修改数据库 schema，模型和迁移文件都要同步维护
   - 否则容易出现“本地能跑、迁移不一致”的问题

3. 生产安全配置有强校验
   - 非 `DEBUG` 模式下，如果缺失以下配置，后端会直接启动失败：
     - `SECRET_KEY`
     - `ENCRYPTION_KEY`
     - `DATABASE_URL`

4. Redis 不是绝对必需
   - 活跃任务追踪优先使用 Redis
   - Redis 不可用时，`app/services/analysis.py` 会退回内存存储

5. 当前分析流程并未真正接入实时数据采集
   - `analysis.py` 当前显式跳过“数据采集”和“财务比率计算”
   - 使用的是 mock 数据和 mock ratios
   - 这意味着代理不应误以为系统已经完成真实行情或财务抓取链路

## 五、前端系统接线说明
这部分用于帮助代理快速定位实际逻辑入口：

1. 路由入口
   - `frontend/src/router/index.tsx`

2. 鉴权入口
   - `frontend/src/components/layout/MainLayout.tsx`
   - 通过检查 `localStorage` 中的 token 判断登录状态
   - 无 token 时重定向到 `/login`

3. 通用请求封装
   - `frontend/src/utils/request.ts`
   - 自动附带 Bearer Token
   - 遇到 `401` 时会清理登录信息并跳转 `/login`

## 六、验证与测试现状
这里说明了“不要想当然地跑测试”：

1. 前端没有可工作的测试命令
   - `frontend/package.json` 中并不存在有效的 `pnpm test`

2. 测试目录目前为空
   - `backend/tests/`
   - `frontend/tests/`

3. 因此 README 中的测试说明不可靠
   - 当前更现实的前端验证方式是：
     - `pnpm lint`
     - `pnpm build`

## 七、本地环境与安全边界
1. `.gitignore` 已忽略 `.env`
2. 仓库中已经存在本地环境文件
3. 代理可以读取 `.env` 了解运行配置
4. 但除非用户明确要求，否则不要改写或提交环境变量文件

## 八、调试信息
1. Docker 里的后端已启用 `debugpy`
2. 暴露调试端口：`5678`
3. VS Code 调试附加配置已存在：
   - `.vscode/launch.json`

## 九、这份 AGENTS.md 的价值
这份文件的价值不在“全面”，而在“纠偏”：

1. 它告诉代理哪些仓库文档已经过时
2. 它明确真实可执行命令，减少猜测
3. 它指出端口、代理、自动建表、mock 分析流程等非显而易见事实
4. 它帮助后续会话快速进入正确工作状态，降低误操作概率

## 十、总结
这份 `AGENTS.md` 是一份高信号、低噪音的仓库操作指引，适合未来 OpenCode 会话作为优先参考。其核心作用是：

1. 避免相信过时 README
2. 明确前后端实际启动方式
3. 指出真实端口与代理关系
4. 暴露后端自动建表与迁移并存的风险
5. 提醒当前分析链路仍包含 mock 数据逻辑
6. 指明目前没有可依赖的测试体系
