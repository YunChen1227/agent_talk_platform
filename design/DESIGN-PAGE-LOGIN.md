# 登录/注册页 (`/login`)

> 返回 [前端总览](./DESIGN-FRONTEND.md) | [主设计文档](./DESIGN.md)

## 概述

用户名密码认证页面，支持登录与注册两种模式切换。

## 页面布局

```
┌───────────────────────────────────┐
│         Login to AgentMatch       │
│                                   │
│  ┌─────────────────────────────┐  │
│  │ Username: [____________]    │  │
│  │ Password: [____________]    │  │
│  │                             │  │
│  │       [  Sign In  ]         │  │
│  │                             │  │
│  │  New here? [Register]       │  │
│  └─────────────────────────────┘  │
└───────────────────────────────────┘
```

## 功能说明

| 元素 | 说明 |
|------|------|
| **Username 输入框** | 必填，用于登录/注册 |
| **Password 输入框** | 必填，type=password |
| **提交按钮** | 登录模式: "Sign In"；注册模式: "Sign Up" |
| **模式切换链接** | 底部 "New here? Register" / "Already have an account? Login" 切换 |

## 交互流程

1. 用户填写 Username + Password，点击提交。
2. 登录调用 `POST /auth/login`，注册调用 `POST /auth/register`。
3. 成功 → 将返回的 user 对象存入 `localStorage("user")`，跳转 `/` (Dashboard)。
4. 失败 → 弹出 alert 展示后端错误信息。

## API 依赖

| Method | Path | 说明 |
|--------|------|------|
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/register` | 用户注册 |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/app/login/page.tsx` | 页面实现 |
