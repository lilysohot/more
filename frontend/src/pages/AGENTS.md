# Pages 模块规则

适用目录：`frontend/src/pages/`

必读：`../../docs/page-ui-patterns.md`
必读：`../../docs/state-request-rules.md`

## 关键规则

- 页面负责页面级编排：拉取数据、调用 store、路由跳转、消息提示。
- 只在页面内使用的短期状态保留在本地 `useState/useEffect`。
- 跨页面共享或带轮询的流程优先交给 store，例如分析任务与进度。
- 页面文件过大且出现多个清晰展示分区时，抽到 `components/`。
- 用户可见文案默认保持中文。
- 改页面后要考虑桌面和移动端都能正常工作。
