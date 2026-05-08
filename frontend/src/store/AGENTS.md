# Store 模块规则

适用目录：`frontend/src/store/`

必读：`../../docs/state-request-rules.md`

## 关键规则

- 共享状态、长生命周期状态、轮询流程放在 Zustand store。
- store 要明确维护数据、加载状态、必要的错误状态和动作函数。
- 需要让页面决定后续动作时，异步失败不要静默吞掉。
- 涉及认证改动时，必须联动检查 `authStore.ts`、`utils/request.ts`、`components/layout/MainLayout.tsx`。
- 不要把一次性的页面局部状态硬塞进全局 store。
