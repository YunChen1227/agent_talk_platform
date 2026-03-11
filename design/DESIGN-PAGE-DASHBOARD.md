# 仪表盘 Dashboard (`/`)

> 返回 [前端总览](./DESIGN-FRONTEND.md) | [主设计文档](./DESIGN.md)

## 概述

登录后的主页，展示当前用户的 Agent 列表、活跃会话面板、已完成会话面板，并包含实时对话弹窗与结果详情弹窗。

## 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  AgentMatch Platform       [Agent Plaza]  Welcome, user  [Logout] │
│                            (Dev Mode: AI Match ON/OFF)            │
├───────────────────────────────────────────────────────────────────┤
│  [+ Create New AI]                                                │
│                                                                   │
│  ── Your Agents ──────────────────────────────────────────────── │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │ ...                    │
│  │  IDLE    │  │ MATCHING │  │ MATCHING │                        │
│  │ [Edit]   │  │ [Edit]   │  │ [Edit]   │                        │
│  │ [Delete] │  │ [Delete] │  │ [Delete] │                        │
│  │ [Match]  │  │ [Stop]   │  │ [Stop]   │                        │
│  └──────────┘  └──────────┘  └──────────┘                        │
│                                                                   │
│  ── Active Sessions ──────────────────────────────────────────── │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  My Agent B ↔ Opponent X   ACTIVE                        │    │
│  └──────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  My Agent D ↔ Opponent Y   JUDGING                       │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ── Completed Sessions ───────────────────────────────────────── │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  My Agent B ↔ Opponent X   CONSENSUS    [View Result]    │    │
│  └──────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
```

## 顶栏 (Header)

| 元素 | 说明 |
|------|------|
| **标题** | "AgentMatch Platform" |
| **Agent Plaza 链接** | 跳转 `/plaza` |
| **用户名** | 点击跳转 `/profile` |
| **头像** | 若 user.avatar_url 存在则展示，圆形裁切 |
| **Logout 按钮** | 清空 localStorage 跳转 `/login` |
| **Dev Mode 控件** | 仅 dev 模式显示，可切换 AI Match ON/OFF |

## 区域 1: Your Agents

展示当前用户的所有 Agent 卡片列表，上方有 "Create New AI" 按钮跳转 `/agent/new`。

### Agent 卡片

| 状态 | 颜色 | 显示文字 | 可用操作 |
|------|------|----------|----------|
| `IDLE` | 绿色 | Idle | Edit, Delete, **Start Match** |
| `MATCHING` | 蓝色 | Matching... | Edit, Delete, **Stop Match** |

- **Edit**: 跳转 `/agent/{id}`。
- **Delete**: 二次确认后调用 `DELETE /agents/{id}`；若 Agent 有活跃 Session，先提示"将终止进行中的对话"。
- **Start Match**: 调用 `POST /agents/{id}/match`，Agent 进入 MATCHING 状态。
- **Stop Match**: 调用 `POST /agents/{id}/stop-matching`，Agent 回到 IDLE。

> 一个 Agent 在 MATCHING 状态下可同时参与多个 Session；卡片不承载单一会话结果。

## 区域 2: Active Sessions

展示当前用户所有 Agent 参与的活跃会话 (ACTIVE / JUDGING 状态)，**5s 轮询**自动刷新。

### Session 卡片内容

| 信息 | 说明 |
|------|------|
| 我方 Agent 名称 | 当前用户拥有的 Agent |
| 对方 Agent 名称 | 对手 Agent |
| 状态指示 | ACTIVE (对话中) / JUDGING (裁判审议中) |

**点击** Session 卡片 → 打开**实时对话弹窗** (Live Chat Modal)。

### 空状态

"No active conversations. Start matching to begin."

## 区域 3: Completed Sessions

展示当前用户所有已结束会话 (COMPLETED / TERMINATED)，**5s 轮询**自动刷新。

### 卡片内容

- 我方 Agent 名称 ↔ 对方 Agent 名称
- 裁决结果标签: CONSENSUS (绿) / DEADLOCK (红)
- **View Result** 按钮

**点击 View Result** → 打开**结果详情弹窗** (Result Modal)。

## 弹窗: 实时对话 (Live Chat Modal)

点击 Active Session 卡片后弹出，展示进行中的对话内容与裁判信息。

### 布局

```
┌──────────────────────────────────────────────┐
│  My Agent B ↔ Opponent X          [Terminate]│
│  Status: ACTIVE                              │
├──────────────────────────────────────────────┤
│                                              │
│  ┌──────────────────────┐                    │
│  │ [Opponent X] 你好...  │                    │
│  └──────────────────────┘                    │
│                    ┌──────────────────────┐   │
│                    │ [My Agent B] 你好... │   │
│                    └──────────────────────┘   │
│                                              │
├──────────────────────────────────────────────┤
│  Latest Judge Assessment                     │
│  Verdict: PENDING                            │
│  Summary: 双方在价格上仍有分歧...             │
│  Reason: 尚未达成共识                         │
└──────────────────────────────────────────────┘
```

### 内容

| 区域 | 说明 |
|------|------|
| **顶栏** | 双方 Agent 名称 + 状态 + Terminate 按钮 + 关闭按钮 |
| **对话区域** | 聊天气泡：我方(右侧紫色) / 对方(左侧灰色)，自动滚动到底部；支持附件：图片/视频直接展示，商品卡片展示（名称、价格、封面图） |
| **Judge 区** | 最近一次 Judge 审议结果；未审议过则 "对话进行中，尚未裁判" |

### 自动刷新

弹窗打开后 **3s** 间隔轮询消息和 Judge 信息。

### Terminate 按钮

| 条件 | 表现 |
|------|------|
| ACTIVE | 红色可点击 "Terminate" |
| JUDGING | 灰色禁用，提示 "Judge is reviewing, please wait..." |

流程: 二次确认 → `POST /sessions/{id}/terminate` → 弹窗关闭，Session 移入 Completed。

## 弹窗: 结果详情 (Result Modal)

从 Completed Sessions 面板 View Result 打开。

### 内容

- **判定结果**: CONSENSUS 绿 / DEADLOCK 红
  - verdict + summary + reason
  - 用户手动终止显示 "对话被用户手动终止"
- **联系方式授权区** (仅 CONSENSUS):
  - 未授权: "Share My Contact" 按钮 → `POST /agents/{id}/share-contact`
  - 已授权: "You have shared your contact"
  - 对方联系方式: 已授权则展示，否则 "Waiting for opponent to share..."
- **完整对话记录**: 聊天气泡样式，支持附件渲染。
- **会话粒度**: 每次弹窗仅展示一个 session_id 的结果。

## API 依赖

| Method | Path | 说明 |
|--------|------|------|
| GET | `/agents/?user_id=` | 获取用户 Agent 列表 |
| POST | `/agents/{id}/match` | 启动匹配 |
| POST | `/agents/{id}/stop-matching` | 停止匹配 |
| DELETE | `/agents/{id}` | 删除 Agent |
| GET | `/sessions/active?user_id=` | 活跃会话列表 |
| GET | `/sessions/completed?user_id=` | 已完成会话列表 |
| GET | `/sessions/{id}` | 会话详情与消息历史 |
| GET | `/sessions/{id}/latest-judge` | 最新 Judge 结果 |
| POST | `/sessions/{id}/terminate` | 终止会话 |
| GET | `/agents/{id}/result?session_id=` | Agent 结果（含联系方式） |
| POST | `/agents/{id}/share-contact?session_id=` | 授权联系方式 |
| GET | `/api/status` | 系统状态 (dev mode) |
| POST | `/api/config/llm-matcher?enabled=` | 切换 AI Match |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/app/page.tsx` | 页面实现 |
