# Model 模块规则

适用目录：`backend/app/models/`

必读：`../../docs/database-rules.md`

## 关键规则

- 改模型就必须同步补 Alembic migration；本地 `create_all()` 不能代替 migration。
- 新主键继续沿用 `UUID(as_uuid=True)` + `uuid.uuid4`。
- 时间字段继续沿用 `datetime.utcnow`，与现有模型保持一致。
- 父子关系按当前约定显式写 `ondelete="CASCADE"`，并让 ORM `relationship()` 与之匹配。
- 结构化长 payload 优先使用 `JSON` 字段。
- 新增索引、唯一约束、外键语义时，要在 migration 中显式落地。
