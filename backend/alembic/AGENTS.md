# Alembic 模块规则

适用目录：`backend/alembic/`

必读：`../docs/database-rules.md`

## 关键规则

- 每个 schema 变更都要新增 revision，不改写既有迁移链。
- 所有 migration 必须同时包含 `upgrade()` 和 `downgrade()`。
- migration 里显式表达表、列、索引、唯一约束、外键和 `ondelete` 语义。
- 模型改了但 migration 没补，全任务不算完成，即使本地启动成功。
- 运行 Alembic 相关命令时，从 `backend/` 目录执行。
