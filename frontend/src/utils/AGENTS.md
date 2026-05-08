# Utils 模块规则

适用目录：`frontend/src/utils/`

必读：`../../docs/state-request-rules.md`

## 关键规则

- `request.ts` 是共享请求入口，token 注入和 `401` 处理统一放这里。
- 纯 helper 保持无副作用，优先写成格式化或派生函数。
- 像 `reportViewModel.ts` 这样的展示 helper，不要混入网络请求或 React 状态。
- 浏览器副作用默认留在页面层；确定多处复用后再抽到 `utils/`。
