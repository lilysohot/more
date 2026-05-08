# API 设计规范

## 适用范围

- `backend/app/api/`
- `backend/app/schemas/`
- `backend/app/main.py` 中的路由挂载

## 本项目的固定事实

- 后端是 `FastAPI`，统一前缀来自 `settings.API_V1_STR`，当前为 `/api/v1`。
- 路由在 `backend/app/main.py` 中集中挂载，当前按资源拆分为 `auth`、`users`、`api-configs`、`analyses`。
- 认证依赖复用 `app.api.deps.get_current_user`。
- 数据库会话依赖复用 `app.database.get_db`，类型为 `AsyncSession`。
- 前端默认通过 `/api/v1` 访问后端，`401` 会触发前端清理登录态并跳转 `/login`。

## 路由组织规则

1. 一个资源组一个路由文件，不把无关资源混进同一个 router。
2. 新增资源时，先在对应 `schema` 中定义请求和响应模型，再写路由。
3. 资源级 CRUD 继续沿用当前风格：
   - 列表：`GET ""`
   - 新建：`POST ""`
   - 详情：`GET "/{resource_id}"`
   - 删除：`DELETE "/{resource_id}"`
4. 非 CRUD 行为才使用动作型子路径，例如 `/{config_id}/set-default`、`/{analysis_id}/progress`、`/test`。
5. 静态路径放在动态路径前面，避免 `/{id}` 抢占匹配，例如 `/default`、`/active-tasks` 必须先声明。
6. 新 router 必须同步注册到 `backend/app/main.py`，并补上中文 `tags`。

## Handler 设计规则

1. 路由函数保持薄层，只做四件事：
   - 接收和校验传输层参数
   - 绑定认证和数据库依赖
   - 调用 service 或局部 helper
   - 组装响应
2. 不要在路由里直接堆积多步业务流程。跨多次查询、跨多对象写入、带外部调用的流程，放进 `app/services/`。
3. 所有受保护接口默认依赖 `get_current_user`，并且查询必须按 `user_id` 做归属过滤。
4. 不要在路由里手动创建 engine 或 session，只能通过 `Depends(get_db)` 取 `AsyncSession`。
5. 新接口优先使用强类型参数，让 FastAPI 自动校验：
   - 路径主键优先用 `UUID`
   - 分页参数优先用 `Query(..., ge=..., le=...)`
6. `api_configs.py` 里把 `config_id: str` 再手动转 `UUID` 属于存量写法；新接口不要继续复制这个模式。
7. 涉及后台任务时，先把数据库中的主记录提交成功，再把不可变标识传给 `BackgroundTasks`。`create_analysis()` 是当前参考实现。

## 请求与响应契约

1. 稳定接口必须声明 `response_model`，不要依赖隐式序列化。
2. ORM 对象只有在对应 schema 配置了 `from_attributes = True` 时才能直接返回。
3. 只要响应需要脱敏、重命名、拼装字段，就显式写映射函数，当前参考是 `api_configs.py` 的 `config_to_response()`。
4. 请求模型负责基础校验，字段约束优先写在 `app/schemas/`，不要把长度、必填、枚举校验散落在路由里。
5. 对前端已消费的响应结构，新增字段优先走向后兼容的增量扩展，不随意删旧字段。
6. 报告接口当前同时返回结构化字段和 `original.content_md/content_html`，这是现有兼容面，改动前必须同步评估前端与测试。

## 状态码与异常规则

1. 继续沿用当前状态码约定：
   - 创建成功：`201`
   - 删除成功且无响应体：`204`
   - 参数或状态不满足业务要求：`400`
   - 认证失败：`401`
   - 资源不存在或无权访问该资源：`404`
   - 请求模型校验失败：`422`
2. 可复用的业务错误优先沉淀到 `app/core/exceptions.py`。
3. 只在路由局部、且没有复用价值时直接抛 `HTTPException`。
4. 不把上游系统的原始异常细节直接透传给前端，尤其是外部网络错误、凭据错误、内部堆栈信息。
5. 含密钥、token、数据库内部细节的错误信息不能进入 API 响应。

## 安全边界

1. API Key 只允许写入时接收明文，响应中只允许返回掩码值。
2. 用户自定义 `base_url` 一类输入要按高风险外部请求面处理；若新增同类接口，先参考 `docs/api-security-audit.md` 的 SSRF 风险说明。
3. 任何用户私有数据接口都必须同时校验身份和资源归属，不能只按主键查询。

## 变更后的最低验证

1. 修改接口契约后，补 `backend/tests/unit/api/` 下的聚焦测试。
2. 修改前后端对接字段后，至少验证：
   - 后端相关 `pytest -q tests/unit/...`
   - 前端 `pnpm lint`
   - 前端 `pnpm build`
3. 不要把 `pnpm test` 写进文档或流程里；本项目当前没有这个脚本。
