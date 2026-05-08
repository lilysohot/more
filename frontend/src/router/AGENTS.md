# Router 模块规则

适用目录：`frontend/src/router/`

必读：`../../docs/page-ui-patterns.md`

## 关键规则

- 所有页面路由统一在 `index.tsx` 注册。
- 需要登录后访问的页面挂在 `MainLayout` 的 `children` 下，不复制鉴权逻辑。
- 新增页面时检查是否需要同步更新 `MainLayout` 导航入口。
- 保持现有路径风格和命名，不随意重命名已接线页面路径，例如 `/api-config`、`/report/:analysisId`。
- 兜底路由继续显式处理，避免用户落到空白页。
