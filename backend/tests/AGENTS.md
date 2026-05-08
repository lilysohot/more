# 测试模块规则

适用目录：`backend/tests/`

必读：`../docs/testing-standards.md`

## 关键规则

- 测试优先写成聚焦单测，不依赖真实网络、真实数据库、真实第三方凭据。
- API 测试使用最小 `FastAPI()` 应用、`dependency_overrides` 和 `TestClient`。
- 异步 service 测试使用 `pytest.mark.asyncio`，优先 fake/stub，而不是实调 provider。
- 影响前端消费字段、错误码、兼容别名的改动，必须补 `unit/api` 契约测试。
- 当前不要把“`pytest -q` 全量通过”当作默认要求；优先运行与你改动直接相关的聚焦测试。
- 提交结果时，写清楚实际执行过的测试文件和验证命令。
- 回溯测试时，需要返回任务清单，将任务清单中的任务执行情况记录在 `progress` 目录下的文件中。
