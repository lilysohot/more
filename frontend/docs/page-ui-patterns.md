# 前端页面与 UI 规范

## 适用范围

- `frontend/src/router/`
- `frontend/src/pages/`
- `frontend/src/components/`
- `frontend/src/styles/`

## 本项目的固定事实

- 前端技术栈是 `React 18 + TypeScript + Vite`。
- 路由入口在 `frontend/src/router/index.tsx`。
- 运行时 UI 组件库以 `Ant Design` 为主，`frontend/src/main.tsx` 已通过 `ConfigProvider` 注入 `zh_CN`。
- 样式体系是 `Ant Design + Tailwind CSS + 少量全局 CSS` 的组合，不是纯 Tailwind 项目。
- 认证后的主布局和门禁在 `frontend/src/components/layout/MainLayout.tsx`。
- 报告工作台页面使用 `pages/Report.tsx + components/report/* + styles/index.css` 这一整套现有结构。

## 路由与页面规则

1. 新页面组件放在 `frontend/src/pages/`，路由统一在 `frontend/src/router/index.tsx` 注册。
2. 需要登录后访问的页面，挂到 `MainLayout` 的 `children` 下，不额外复制一套鉴权逻辑。
3. 登录与注册继续沿用当前共享入口 `pages/Login.tsx` 的模式；不要为这两个流程再拆第二套路由体系，除非产品要求已变化。
4. 新增可导航页面时，如果用户应该能在主界面发现它，要同时更新 `MainLayout` 中的导航入口。
5. 页面文件负责页面级编排：
   - 路由参数读取
   - 页面生命周期
   - 调用 store 或 API
   - 页面级消息提示
   - 页面级跳转
6. 页面里如果出现大块纯展示结构、且已经影响可读性，就抽到 `components/`。`Report.tsx` 和 `components/report/*` 是当前参考模式。

## 组件边界规则

1. `components/` 优先承载展示组件和可复用交互组件，不直接承担整页数据编排。
2. 组件 props 必须有明确类型，优先复用 `@/types` 中已有类型。
3. 没有复用价值的短小 UI，不强行抽组件；但页面内超过一个明显视觉模块时，优先拆出子组件。
4. 组件内部默认不要直接发 HTTP 请求；共享数据和异步流程优先由 page 或 store 驱动。
5. 用户可见文案默认保持中文，与现有页面和后端错误文案风格一致。

## UI 体系规则

1. 表单、表格、弹窗、消息提示、下拉、Tabs 等标准交互优先继续使用 `Ant Design`。
2. 小范围布局、间距、对齐调整优先使用 Tailwind 工具类。
3. 复杂视觉场景、跨组件共享样式或报告工作台这类整体视觉系统，继续放到 `frontend/src/styles/index.css` 管理，不把大量样式塞回 TSX 内联对象。
4. 不要再引入第二套大型 UI 组件库。
5. 继续优先使用 `@/` 别名导入 `src` 内模块，避免深层相对路径污染。

## 报告页面特殊规则

1. `pages/Report.tsx` 负责报告页面的加载、降级判断、下载和分享动作。
2. 结构化报告展示优先通过 `components/report/*` 组合，而不是把所有展示逻辑重新塞回 `Report.tsx`。
3. 纯格式化、派生展示逻辑继续收敛到 `utils/reportViewModel.ts` 一类 helper，不把金额/日期/评分格式化逻辑散落到多个组件里。
4. 如果后端结构化报告缺失，前端必须保留当前“降级展示原文报告”的能力。

## 交互与响应式规则

1. 改动页面或组件时，至少考虑桌面和移动端两种布局。
2. 像 `MainLayout` 这种布局级响应式，优先沿用现有 `Grid.useBreakpoint()` 模式。
3. 可点击元素优先使用真正的 `button`、`a`、`Ant Design` 组件，不用普通 `div` 假装交互。
4. 页面级失败、成功、警告反馈继续优先使用 `message`、`Alert`、`Spin` 等现有反馈方式。

## 变更后的最低验证

1. 从 `frontend/` 目录运行 `pnpm lint`。
2. 再运行 `pnpm build`。
3. 如果改动影响登录态、主布局、分析发起、报告展示或下载，补做对应手工验证。
