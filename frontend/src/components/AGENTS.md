# Components 模块规则

适用目录：`frontend/src/components/`

必读：`../../docs/page-ui-patterns.md`

## 关键规则

- 组件优先保持展示职责，不直接承担整页数据流编排。
- 组件 props 必须显式类型化，优先复用 `@/types`。
- 标准表单、表格、弹窗、反馈继续优先使用 `Ant Design`。
- 小范围布局调整可用 Tailwind，复杂共享视觉规则收敛到 `styles/index.css`。
- `components/report/` 继续作为报告工作台的展示模块区，不把格式化逻辑散落到各组件内部。
