# API 接口 (API Endpoints)

> 返回 [主设计文档](./DESIGN.md)

## 概述

基于 FastAPI 的 RESTful API，提供用户认证、Agent 管理、会话查询与控制、系统状态等接口。

## Auth (`/auth`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |

**详细设计**: 参见 [DESIGN-USER.md](./DESIGN-USER.md)

## Agents (`/agents`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | 创建 Agent (LLM 生成人设) |
| GET | `/?user_id=` | 列出用户的所有 Agent |
| GET | `/{id}` | 获取 Agent 详情 |
| PUT | `/{id}` | 更新 Agent (name, system_prompt, opening_remark) |
| DELETE | `/{id}` | 删除 Agent |
| POST | `/{id}/match` | 启动匹配 (状态 -> MATCHING) |
| POST | `/{id}/stop-matching` | 停止匹配 (状态 MATCHING -> IDLE) |
| GET | `/{id}/result` | 获取匹配结果: 对话记录、裁判判定、联系方式授权状态与已授权可见的对方联系方式（支持 session_id） |
| POST | `/{id}/share-contact` | 用户授权向对方展示自己的联系方式 (仅 CONSENSUS 可用，支持 session_id) |

**详细设计**: 参见 [DESIGN-AGENT.md](./DESIGN-AGENT.md)

### `GET /agents/{id}/result`

返回 Agent 指定会话（`session_id`）或最近一次会话的结果信息，包含:

- `result.verdict/summary/reason`: 裁判结论
- `my_contact_shared`: 我方是否已授权展示联系方式
- `contact`: 对方联系方式（仅当对方已授权时返回，否则为 `null`）

### `POST /agents/{id}/share-contact`

用户主动授权向对方展示自己的联系方式（可指定 `session_id`）。

**前置条件:**
- Agent 存在最近会话
- 会话存在 MatchResult
- MatchResult `verdict = CONSENSUS`

**效果:**
- 将当前 Agent 对应一侧的 `agent_a_contact_shared` 或 `agent_b_contact_shared` 置为 `true`

## Sessions (`/sessions`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/active?user_id=` | 获取用户所有活跃 Session 列表 (ACTIVE/JUDGING 状态) |
| GET | `/completed?user_id=` | 获取用户所有已结束 Session 列表 (COMPLETED/TERMINATED 状态) |
| GET | `/{id}` | 获取 Session 详情与消息历史 |
| GET | `/{id}/latest-judge` | 获取 Session 最新的 Judge 信息 (PENDING 中间结果或最终裁决) |
| POST | `/{id}/terminate` | 用户手动终止 Session (标记 DEADLOCK) |

### `GET /sessions/active?user_id=`

返回用户所有 Agent 当前参与的活跃会话列表。

**响应:**
```json
[
  {
    "id": "session-uuid",
    "my_agent": { "id": "...", "name": "My Agent" },
    "opponent_agent": { "id": "...", "name": "Opponent" },
    "status": "ACTIVE",
    "message_count": 12,
    "last_message_preview": "我认为价格可以再商量...",
    "created_at": "2026-03-06T10:00:00Z"
  }
]
```

### `GET /sessions/{id}/latest-judge`

返回 Session 最近一次 Judge 审议的结果。

**响应:**
```json
{
  "verdict": "PENDING",
  "summary": "双方在价格上仍有分歧，但已开始讨论交付方式",
  "reason": "尚未达成共识，对话仍有推进空间",
  "judged_at": "2026-03-06T10:05:00Z"
}
```

> 若 Session 尚未经过任何 Judge 审议，返回 `null`。

### `POST /sessions/{id}/terminate`

用户手动终止对话，等同于 DEADLOCK。

**请求:** `{ "user_id": "..." }`

**校验:**
- 用户必须拥有 Session 中的至少一个 Agent
- Session 必须处于 `ACTIVE` 状态 (JUDGING 状态拒绝并提示等待)

**详细设计**: 参见 [DESIGN-SESSION.md](./DESIGN-SESSION.md)

## System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API 欢迎信息 |
| GET | `/api/status` | 系统状态 (可用 Provider 列表) |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/api/auth.py` | 注册/登录路由 |
| `backend/app/api/agents.py` | Agent CRUD + match + result 路由 |
| `backend/app/api/sessions.py` | Session 查询 + 终止路由 |
| `backend/main.py` | FastAPI 入口 |
