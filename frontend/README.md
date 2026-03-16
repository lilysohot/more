# 小财大用 - 前端应用

基于 React + TypeScript + Vite 的现代化前端应用，提供用户友好的公司分析界面。

## 🚀 快速开始

### 1. 环境要求

- Node.js 18+
- pnpm

### 2. 安装依赖

```bash
pnpm install
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

### 4. 启动开发服务器

```bash
pnpm dev
```

访问 http://localhost:5173

### 5. 构建生产版本

```bash
pnpm build
```

## 📁 项目结构

```
src/
├── api/          # API 调用
├── components/   # 通用组件
├── pages/        # 页面组件
├── store/        # 状态管理 (Zustand)
├── hooks/        # 自定义 Hooks
├── types/        # TypeScript 类型
├── utils/        # 工具函数
├── styles/       # 全局样式
└── router/       # 路由配置
```

## 🎨 主要页面

- ✅ 登录/注册
- ✅ 首页（公司分析）
- ✅ 个人中心
- ✅ API 配置管理
- ✅ 报告预览
- ✅ 历史记录

## 🏗️ 技术栈

- React 18
- TypeScript
- Vite 5
- Ant Design 5
- Zustand
- React Router 6
- ECharts 5
- Tailwind CSS

## 🧪 测试

```bash
pnpm test
```

## 📚 开发指南

详见 [docs/development.md](../docs/development.md)

---

**小财大用 - 让投资更智慧！** 💰📈
