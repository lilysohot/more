# 前端状态与请求规范

## 适用范围

- `frontend/src/api/`
- `frontend/src/store/`
- `frontend/src/utils/request.ts`
- `frontend/src/types/`

## 本项目的固定事实

- 所有共享 HTTP 请求基础能力集中在 `frontend/src/utils/request.ts`。
- 请求基地址优先取 `VITE_API_BASE_URL`，否则回退到 `/api/v1`。
- 认证 token 当前从 `localStorage` 读取，并由请求拦截器自动挂载到 `Authorization`。
- `401` 会在拦截器里清理本地登录信息并跳转 `/login`。
- 全局共享状态目前通过 `Zustand` 管理，核心 store 是：
  - `authStore`
  - `analysisStore`
  - `apiConfigStore`
- 类型契约集中在 `frontend/src/types/index.ts`。

## API 层规则

1. 后端资源按文件拆分，继续沿用当前结构：`auth.ts`、`user.ts`、`apiConfig.ts`、`analysis.ts`。
2. API 文件只负责请求封装和类型声明，不承担页面消息提示和导航。
3. 默认使用共享 `request` 实例；只有明确不需要鉴权时才使用 `requestWithoutAuth`。
4. API 方法统一返回强类型 `Promise<T>`。
5. 路径一律写相对 `/api/v1` 的资源路径，例如 `/users/profile`、`/analyses`，不要在业务文件里重复拼接完整 base URL。
6. 不要在 API 层偷偷把后端字段名从 `snake_case` 改成 `camelCase`；当前前后端契约就是 `snake_case`。

## Store 归属规则

1. 跨页面共享、生命周期较长、或带轮询/异步流程编排的状态，优先放 `store/`。
2. 只属于单个页面、且不需要跨页复用的短期状态，保留在页面本地 `useState/useEffect`。
3. 这也是本项目当前的真实分工：
   - 分析任务、分析进度、报告、默认模型配置在 store
   - `ProfilePage` 这类页面局部读取可以直接调用 `userApi`
4. store 应明确维护：
   - 主要数据
   - `isLoading`
   - 需要时的 `error`
   - 对外动作函数
5. 如果 store 方法失败后页面还要决定后续动作，应继续 `throw error` 给调用方；不要把错误静默吞掉。

## 认证流特殊规则

1. 当前登录态实现横跨三处：
   - `store/authStore.ts`
   - `utils/request.ts`
   - `components/layout/MainLayout.tsx`
2. 只改其中一处会造成状态不一致；凡是改 token 持久化、登出、401 处理、鉴权门禁，必须联动检查这三处。
3. `authStore` 当前使用 `persist`，同时又手动读写 `localStorage token`；这是现有兼容面，未经明确设计不要随意只保留其中一套。

## 工具与 helper 规则

1. 像 `reportViewModel.ts` 这样的文件应保持纯函数化，负责格式化、派生字段、展示判断。
2. 纯 helper 不要依赖 React 组件状态。
3. 浏览器副作用例如下载、复制链接，默认留在页面层；只有多处复用时再抽到 `utils/`。

## 类型契约规则

1. `frontend/src/types/index.ts` 是前端和后端响应契约的镜像层。
2. 只要后端 schema 改字段、增字段、改可空性，前端类型要同步更新。
3. 保持字段命名与后端一致，当前统一使用 `snake_case`，例如：
   - `created_at`
   - `api_key_masked`
   - `analysis_id`
4. 没有显式适配层时，不要在页面里混用两套命名风格。

## 变更后的最低验证

1. 改 API 契约或类型后，同时检查 `api/`、`store/`、页面消费点是否同步。
2. 从 `frontend/` 目录运行 `pnpm lint`。
3. 再运行 `pnpm build`。
4. 如果改动涉及后端响应结构，同时补做相关后端聚焦验证。
