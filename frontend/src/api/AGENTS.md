# API 模块规则

适用目录：`frontend/src/api/`

必读：`../../docs/state-request-rules.md`

## 关键规则

- 一个后端资源组一个 API 文件，继续沿用 `auth`、`user`、`apiConfig`、`analysis` 的拆分方式。
- 默认复用共享 `request` 实例，不在业务文件里新建 axios client。
- API 方法返回 typed `Promise`，不返回 `any`。
- 路径写相对资源路径，不重复拼接 `/api/v1` 的完整 host。
- 不在这里做 UI 提示、跳转或字段命名转换。
- 无鉴权请求才使用 `requestWithoutAuth`。
