# 数据库操作约束

## 适用范围

- `backend/app/database.py`
- `backend/app/models/`
- `backend/app/services/`
- `backend/alembic/versions/`

## 本项目的固定事实

- 数据库访问基于 `SQLAlchemy AsyncSession`。
- 路由层通过 `Depends(get_db)` 注入会话；后台异步流程可通过 `AsyncSessionLocal()` 自行创建会话。
- `backend/app/main.py` 的 startup 会调用 `init_db()`，其中执行 `Base.metadata.create_all()`。
- `create_all()` 只能帮助本地补表，不能替代 Alembic 迁移。
- 当前模型集中在 `backend/app/models/user.py`，当前迁移链为 `001 -> 002 -> 003`。
- 后端命令必须从 `backend/` 目录运行，因为 `.env` 加载依赖当前工作目录。

## 会话与事务规则

1. 新数据库代码一律使用异步会话，不引入同步 `Session`。
2. 事务边界优先放在 service 的公开方法，而不是散落在多个内部 helper 中。
3. 一个公开写操作尽量只在收口处 `commit()` 一次；内部 helper 如果只是流程中的一步，不要再额外 `commit()`。
4. `APIConfigService._unset_default()` 这种 helper 内直接提交事务的写法属于存量实现，新逻辑不要继续复制。
5. 创建或更新后如果调用方要拿数据库最终值，使用 `await db.commit()` 后再 `await db.refresh(entity)`。
6. 如果捕获异常后还要继续复用当前 session，必须先 `rollback()`；不要让脏事务状态泄漏到后续查询。

## 分层职责

1. 路由层可以保留极薄的一次性数据库操作，但多步写入、跨表更新、外部调用混合流程，应优先进入 `app/services/`。
2. service 层负责：
   - 资源归属校验后的查询复用
   - 多对象写入
   - 默认值切换、状态推进、密钥加解密等业务规则
3. model 层只定义表结构、关系和基础约束，不承载业务流程。

## 查询规则

1. 统一使用 `select()` 查询。
2. 单条读取优先用 `scalar_one_or_none()`。
3. 多条读取优先用 `result.scalars().all()`。
4. 计数使用 `select(func.count(...))`，不要先把整批记录读出来再 `len(...)`。
5. 用户私有资源必须带 `user_id` 过滤；不能只按资源 `id` 命中。
6. 没有充分理由时，不写裸 SQL。

## Schema 约定

1. 新主键继续沿用 PostgreSQL UUID：`UUID(as_uuid=True)` + `uuid.uuid4`。
2. 时间字段继续沿用 `datetime.utcnow`，与现有模型保持一致。
3. 典型父子资源继续显式写 `ondelete="CASCADE"`，并让 ORM `relationship()` 与数据库语义一致。
4. 结构化长 payload 优先用 `JSON` 字段，当前参考有：
   - `Report.structured_data_json`
   - `AgentRun.structured_output_json`
5. 新约束、索引、唯一性要求必须在 migration 中显式落地，不能只存在于 Python 代码或口头约定里。

## 迁移规则

1. 任何会改变表结构的修改，都必须同时提交模型变更和新的 Alembic migration。
2. 不要因为本地能靠 `create_all()` 启动，就省略 migration。
3. 已发布或已共享的旧 migration 不直接改写；新增 revision 表达增量变更。
4. 每个 migration 都要写 `upgrade()` 和 `downgrade()`。
5. 迁移中要明确表达：
   - 新表或新列
   - 索引/唯一约束
   - 外键及 `ondelete`
   - JSON 字段等特殊类型

## 敏感数据规则

1. API Key 落库前必须加密，当前约定复用 `encrypt_api_key()`。
2. API Key 对外展示只能返回掩码值，当前约定复用 `mask_api_key()`。
3. 只有在确实需要向上游 provider 发请求时，才允许在 service 内短暂解密使用；不要把明文写回数据库、日志或响应。

## 与本项目现状相关的特殊提醒

1. 活跃分析任务状态当前优先放 Redis，不可用时退回内存；不要把这类短生命周期运行态随意塞进持久化表，除非产品设计明确要求。
2. Docker Compose 的 Postgres 端口和本地 `DEBUG` fallback 并不一致。验证数据库改动时，不要想当然地假设本地连接参数和 Docker 一样。

## 变更后的最低验证

1. 检查模型、service、schema、migration 是否同时更新。
2. 至少补一个覆盖新行为的聚焦单测。
3. 从 `backend/` 目录运行相关命令。
