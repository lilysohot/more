# 测试标准

## 适用范围

- `backend/tests/`
- 前后端变更后的最小验证流程

## 本项目的固定事实

- 后端测试位于 `backend/tests/unit/`。
- 前端当前没有 `pnpm test` 脚本，前端验证方式是 `pnpm lint` 然后 `pnpm build`。
- `backend/` 下直接执行 `pytest -q` 目前会因遗留 `__pycache__/test_tushare_skill*.pyc` 冲突而在收集阶段失败。
- 当前可靠做法是运行聚焦测试文件或聚焦目录，例如 `pytest -q tests/unit/api/test_analysis_progress_helpers.py`。

## 测试分层

1. 纯函数、状态归一化、格式转换等逻辑，优先写最小单元测试。
2. service 行为测试放 `backend/tests/unit/services/`。
3. API 契约和路由行为测试放 `backend/tests/unit/api/`。
4. 外部数据源或技能相关测试放 `backend/tests/unit/skills/`。
5. 能用低层测试证明的行为，不强行上升到整应用测试。

## 本项目推荐的测试模式

1. API 契约测试：
   - 使用一个最小 `FastAPI()` 实例挂载目标 router
   - 用 `dependency_overrides` 替换 `get_current_user` 和 `get_db`
   - 用 `TestClient` 直接调用接口
   - 断言 `status_code` 和关键响应字段
2. 异步 service 测试：
   - 使用 `pytest.mark.asyncio`
   - 用假实现、假调用器、最小 stub 替代真实 provider
   - 当前参考：`SequenceCaller`、`DummyLLMService`
3. 回归测试：
   - 优先锁定行为与兼容面，而不是内部实现细节
   - 当前参考：进度状态别名兼容测试、报告接口保留 legacy payload 的契约测试

## 编写规则

1. 测试名直接描述行为或回归场景，不写空泛命名。
2. 每个测试只证明一个清晰结论，失败时能直接看出破坏了什么。
3. 不访问真实网络，不调用真实 Tushare、LLM、Redis、数据库服务，除非该测试文件明确就是集成测试。
4. 不依赖本地 `.env`、本地账号、真实 API Key。
5. 新增接口字段、状态值、兼容别名时，必须补对应断言。
6. 如果变更会影响前端展示字段，优先补 API 契约测试，而不是只补 service 测试。

## 最低补测要求

1. 改 helper 或纯逻辑函数：补对应单元测试。
2. 改 service 的业务判断、provider 路由、重试、状态推进：补 `unit/services`。
3. 改 API 输入输出、鉴权、错误码、兼容字段：补 `unit/api`。
4. 改数据库 schema：补至少一个覆盖新读写行为或兼容约束的后端测试。
5. 改前端但不涉及后端测试时，至少执行：
   - `pnpm lint`
   - `pnpm build`

## 执行规则

1. 后端命令从 `backend/` 目录运行。
2. 默认运行聚焦测试，不把当前仓库包装成“全量 `pytest -q` 已绿”，除非你先解决了现有收集冲突。
3. 提交结果时，写清楚你实际运行了哪些测试或验证命令。

## 推荐命令

```bash
pytest -q tests/unit/api/test_analysis_progress_helpers.py
pytest -q tests/unit/api/test_report_endpoint_contract.py
pytest -q tests/unit/services/test_llm_service.py
```
