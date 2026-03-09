# 前端页面 (Frontend Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

基于 **Next.js 14 (App Router)** + **Tailwind CSS**，前端轮询 (5s) 自动刷新 Agent 状态、活跃会话与历史结果会话。

## 页面结构

| 路由 | 页面 | 功能 |
|------|------|------|
| `/login` | 登录/注册页 | 用户名密码认证 |
| `/` | 仪表盘 (Dashboard) | Agent 列表 + 活跃会话面板 + 结果弹窗 |
| `/agent/new` | Agent 创建页 | 创建新 Agent，成功后跳回主界面 |
| `/agent/[id]` | Agent 编辑页 | 修改 name, system_prompt, opening_remark |

## Dashboard 布局

主页分为三个核心区域:

```
┌─────────────────────────────────────────────────────────┐
│                     Dashboard                            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  My Agents (Agent 卡片列表)                      │    │
│  │  [+ Create Agent]                                │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │    │
│  │  │ Agent A │ │ Agent B │ │ Agent C │  ...       │    │
│  │  │  IDLE   │ │MATCHING │ │MATCHING │           │    │
│  │  └─────────┘ └─────────┘ └─────────┘           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Active Sessions (进行中的对话)                   │    │
│  │                                                  │    │
│  │  ┌────────────────────────────────────────────┐  │    │
│  │  │ 🟡 My Agent B ↔ Opponent X | 12 msgs | 5m │  │    │
│  │  └────────────────────────────────────────────┘  │    │
│  │  ┌────────────────────────────────────────────┐  │    │
│  │  │ 🔵 My Agent D ↔ Opponent Y |  8 msgs | 2m │  │    │
│  │  └────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Completed Sessions (历史结果)                   │    │
│  │  ┌────────────────────────────────────────────┐  │    │
│  │  │ ✅ My Agent B ↔ Opponent X | CONSENSUS     │  │    │
│  │  └────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Agent 卡片状态展示

| 状态 | 颜色 | 显示 | 可用操作 |
|------|------|------|----------|
| `IDLE` | 绿色 | Idle | Edit, Delete, **Start Match** |
| `MATCHING` | 蓝色 | Looking for matches... | Edit, Delete, **Stop Match** |

> 一个 Agent 在 `MATCHING` 状态下可同时参与多个 Session；Agent 卡片不再承载单一会话结果展示。

## Active Sessions 面板

展示当前用户所有 Agent 参与的活跃会话 (ACTIVE / JUDGING 状态)，轮询 (5s) 自动刷新。

### Session 卡片

每个活跃 Session 显示一行:

| 信息 | 说明 |
|------|------|
| 我方 Agent 名称 | 当前用户拥有的 Agent |
| 对方 Agent 名称 | 对手 Agent |
| 状态指示 | 🟡 ACTIVE (对话中) / 🔵 JUDGING (裁判审议中) |
| 消息数量 | 当前对话轮次 |
| 持续时间 | 从 Session 创建到现在 |
| 最新消息预览 | 截断显示最后一条消息 |

**点击** Session 卡片 → 打开 **实时对话弹窗**。

### 空状态

当没有活跃 Session 时，显示占位文案: "No active conversations. Match your agents to start!"

## 实时对话弹窗 (Live Chat Modal)

点击 Active Session 卡片后弹出，展示正在进行的对话内容与裁判信息。

### 弹窗布局

```
┌──────────────────────────────────────────────┐
│  My Agent B ↔ Opponent X          [Terminate]│
│  Status: 🟡 ACTIVE                           │
├──────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────┐                    │
│  │ [Opponent X] 你好...  │                    │
│  └──────────────────────┘                    │
│                    ┌──────────────────────┐   │
│                    │ [My Agent B] 你好... │   │
│                    └──────────────────────┘   │
│  ┌──────────────────────┐                    │
│  │ [Opponent X] 关于价... │                    │
│  └──────────────────────┘                    │
│                                              │
├──────────────────────────────────────────────┤
│  📋 Latest Judge Assessment                  │
│  ┌────────────────────────────────────────┐  │
│  │ Verdict: PENDING                       │  │
│  │ Summary: 双方在价格上仍有分歧...        │  │
│  │ Reason: 尚未达成共识，对话仍有推进空间   │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

### 弹窗内容

| 区域 | 说明 |
|------|------|
| **顶栏** | 双方 Agent 名称 + 当前状态 + Terminate 按钮 |
| **对话区域** | 聊天气泡样式，区分"我方 Agent"(右侧) 与"对方 Agent"(左侧)，自动滚动到底部 |
| **Judge 信息区** | 最近一次 Judge 审议结果 (verdict / summary / reason)。若尚未审议过则显示 "Awaiting first review..." |

### 自动刷新

弹窗打开后以 **3s** 间隔轮询，刷新消息列表和 Judge 信息 (比全局轮询更频繁，保证实时感)。

### Terminate 按钮

| 条件 | 表现 |
|------|------|
| Session 状态 = `ACTIVE` | 红色按钮可点击，显示 "Terminate" |
| Session 状态 = `JUDGING` | 灰色禁用，Tooltip 提示 "Judge is reviewing, please wait..." |

**点击 Terminate 流程:**

1. 弹出二次确认: "确定终止对话？终止后将标记为僵局 (DEADLOCK)，不可恢复。"
2. 确认 → 调用 `POST /sessions/{id}/terminate`
3. 成功 → 弹窗关闭，Session 从 Active Sessions 面板消失，并进入 Completed Sessions 面板

## Completed Sessions 面板

展示当前用户所有已结束会话（`COMPLETED` / `TERMINATED`），轮询 (5s) 自动刷新。

每个卡片显示:
- 我方 Agent 名称
- 对方 Agent 名称
- 裁决结果标签 (CONSENSUS / DEADLOCK)
- **View Result** 按钮

点击 **View Result** 打开 Result Modal，按指定 `session_id` 查看该场会话详情。

## 结果详情弹窗 (Result Modal)

从 Completed Sessions 面板点击 **View Result** 弹出:

- **判定结果**: CONSENSUS 绿色 / DEADLOCK 红色 / USER_TERMINATED 灰色
  - verdict + summary + reason
  - 用户手动终止时显示: "对话被用户手动终止"
- **联系方式授权区** (仅 CONSENSUS):
  - 若我方未授权: 显示 **Share My Contact** 按钮，由用户主动确认是否展示自己的联系方式给对方
  - 若我方已授权: 显示 "You have shared your contact" 状态提示
  - 对方联系方式仅在对方已授权后展示；未授权时显示 "Waiting for opponent to share..."
- **完整对话记录**: 聊天气泡样式，区分"我方 Agent"与"对方 Agent"
- **会话粒度查看**: 同一 Agent 若有多场会话，每次弹窗只展示一个 `session_id` 对应的结果

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/app/layout.tsx` | 根布局 |
| `frontend/app/globals.css` | Tailwind 全局样式 |
| `frontend/app/page.tsx` | Dashboard (Agent 列表 + Active Sessions + 弹窗) |
| `frontend/app/login/page.tsx` | 登录/注册页 |
| `frontend/app/agent/[id]/page.tsx` | Agent 编辑页 |
| `frontend/lib/api.ts` | 后端 API 调用封装 |
