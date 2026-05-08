# Types 模块规则

适用目录：`frontend/src/types/`

必读：`../../docs/state-request-rules.md`

## 关键规则

- 类型文件是前后端契约镜像层，字段名默认与后端保持一致。
- 当前契约统一使用 `snake_case`，不要在这里私自改成 `camelCase`。
- 后端 schema 改字段、改可空性、增字段时，要同步更新这里和消费点。
- 没有明确适配层时，不要并存两套同义类型。
