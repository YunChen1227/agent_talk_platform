# 前端页面 (Frontend Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

基于 **Next.js 14 (App Router)** + **Tailwind CSS**，前端轮询 (5s) 自动刷新 Agent 状态、活跃会话与历史结果会话。

## 技术框架

| 技术 | 版本 | 用途 |
|------|------|------|
| **Next.js** | 14 (App Router) | React SSR 框架、文件路由系统、`useEffect` / `useState` 状态管理 |
| **React** | 18 | UI 组件渲染 |
| **TypeScript** | 5 | 类型安全，编译时错误检查 |
| **Tailwind CSS** | 3 | 原子化 CSS 样式 (响应式布局、颜色主题) |
| **Axios** | 1.x | 后端 REST API 调用 (封装在 `lib/api.ts`) |
| **Lucide React** | 0.330 | SVG 图标组件 |
| **clsx + tailwind-merge** | — | 动态 CSS 类名合并 |
| **localStorage** | Web API | 用户登录态持久化 (`user` 对象) |
| **setInterval** | Web API | 5s/3s 轮询刷新 (Dashboard / 弹窗) |

## 页面结构

| 路由 | 页面 | 详细设计 |
|------|------|----------|
| `/login` | 登录/注册页 | [DESIGN-PAGE-LOGIN.md](./DESIGN-PAGE-LOGIN.md) |
| `/` | 仪表盘 (Dashboard) | [DESIGN-PAGE-DASHBOARD.md](./DESIGN-PAGE-DASHBOARD.md) |
| `/plaza` | Agent 广场 | [DESIGN-PAGE-PLAZA.md](./DESIGN-PAGE-PLAZA.md) |
| `/agent/new` | Agent 创建页 | [DESIGN-PAGE-AGENT.md](./DESIGN-PAGE-AGENT.md) |
| `/agent/[id]` | Agent 编辑页 | [DESIGN-PAGE-AGENT.md](./DESIGN-PAGE-AGENT.md) |
| `/shop` | 用户商店页 | [DESIGN-PAGE-SHOP.md](./DESIGN-PAGE-SHOP.md) |
| `/profile` | 用户资料/媒体 | [DESIGN-PAGE-PROFILE.md](./DESIGN-PAGE-PROFILE.md) |

## 通用约定

- **认证守卫**: 除 `/login` 外所有页面在 `useEffect` 中检查 `localStorage.user`，不存在则跳转 `/login`。
- **轮询刷新**: Dashboard 全局 5s 轮询；弹窗内 3s 轮询（更高实时感）。
- **导航**: Dashboard 顶栏提供 Agent Plaza 链接、用户名（点击进入 Profile）、头像、Logout 按钮。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/app/layout.tsx` | 根布局 |
| `frontend/app/globals.css` | Tailwind 全局样式 |
| `frontend/app/page.tsx` | Dashboard |
| `frontend/app/plaza/page.tsx` | Agent 广场 |
| `frontend/app/login/page.tsx` | 登录/注册页 |
| `frontend/app/agent/new/page.tsx` | Agent 创建页 |
| `frontend/app/agent/[id]/page.tsx` | Agent 编辑页 |
| `frontend/app/shop/page.tsx` | 用户商店页 |
| `frontend/app/profile/page.tsx` | 用户资料/媒体库页 |
| `frontend/lib/api.ts` | 后端 API 调用封装 |
