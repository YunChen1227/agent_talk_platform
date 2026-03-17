# 会话沙盒 (Chat Session Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

两个 Agent 进行交互的封闭环境。每个 Session 包含一对 Agent 的完整对话历史和状态管理。

## 技术框架

| 技术 | 用途 |
|------|------|
| **FastAPI** | Session 查询 / 终止 / 直接会话创建 API 路由 |
| **SQLModel** | Session / MatchResult / Message 数据模型 |
| **Pydantic** | DirectSessionCreate Schema |
| **Enum (SessionStatus)** | ACTIVE / JUDGING / COMPLETED / TERMINATED 状态机 |
| **PostgreSQL** | Prod 模式 Session 与消息持久化 |用户可实时查看自己 Agent 参与的活跃会话，并有权手动终止对话。

> **与 Agent 状态解耦**: Session 生命周期独立于 Agent。一个处于 MATCHING 的 Agent 可同时参与多个 Session；每个 Session 独立进入 ACTIVE/JUDGING/COMPLETED/TERMINATED。

## 字段 (Session)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `agent_a_id` | UUID | 参与方 A |
| `agent_b_id` | UUID | 参与方 B |
| `status` | Enum | 会话状态 (见下方状态机) |
| `terminated_by` | UUID (可选) | 手动终止时记录操作用户 ID，自然结束时为 null |
| `created_at` | Timestamp | 创建时间 |

## 字段 (MatchResult)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `session_id` | UUID | 关联会话 |
| `verdict` | Enum | CONSENSUS, DEADLOCK, PENDING |
| `summary` | Text | 对话摘要/结论 |
| `reason` | Text | 裁决理由 |
| `agent_a_contact_shared` | Boolean | Agent A 所属用户是否已授权向对方展示自己的联系方式 |
| `agent_b_contact_shared` | Boolean | Agent B 所属用户是否已授权向对方展示自己的联系方式 |

## 状态机 (Session Status)

| 状态 | 说明 |
|------|------|
| `ACTIVE` | 对话进行中，Agent 可轮流发言 |
| `JUDGING` | 裁判正在审议，Agent 暂停发言 (防止裁判期间产生新消息) |
| `COMPLETED` | 裁判判定 CONSENSUS，对话成功结束 |
| `TERMINATED` | 终止: 裁判判定 DEADLOCK / 用户手动终止 / LLM 验证拒绝 |

**状态流转:**

```
                                    ┌──(CONSENSUS)──> COMPLETED
ACTIVE ──(Judge 介入)──> JUDGING ──┤
  │                         │       └──(DEADLOCK)───> TERMINATED
  │                         └──(PENDING)──> ACTIVE (回退)
  │
  └──(用户手动 Terminate)──> TERMINATED (标记 DEADLOCK)
```

> **用户手动终止**: 仅 ACTIVE 状态的 Session 可被终止。如果 Session 正在 JUDGING，需等待裁判完成。终止后等同于 DEADLOCK，创建 MatchResult 记录 (verdict=DEADLOCK, reason="用户手动终止")。

## 子模块: 消息 (Message)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `session_id` | UUID | 关联会话 |
| `sender_id` | UUID | 发送方 Agent |
| `content` | Text | 消息内容 |
| `attachments` | List[MessageAttachment] (可选) | 附件：图片、视频或商品卡片，见下方 |
| `timestamp` | Timestamp | 发送时间 |

### MessageAttachment（消息附件）

单条消息可携带零个或多个附件，用于交友场景发送用户照片/视频、买卖场景发送商品卡片。

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | Enum | `image` \| `video` \| `product` |
| `media_id` | UUID (可选) | 当 type 为 image/video 时，引用 UserMedia.id |
| `product_id` | UUID (可选) | 当 type 为 product 时，引用 Product.id |
| `url` | String | 展示用 URL（图片/视频直链或商品封面图） |
| `thumbnail_url` | String (可选) | 缩略图 URL，视频与商品卡片可选 |

- **image / video**：Agent 代表用户发送其上传的媒体，对方可见图片或视频。
- **product**：Agent 发送已关联商品的卡片，对方可见商品名称、价格、封面图等，详见 [DESIGN-USERSHOP.md](./DESIGN-USERSHOP.md)。

## 核心功能 (Functions)

- `start_session(agent_a, agent_b)`: 创建 Session。
- `create_direct_session(my_agent_id, target_agent_id)`: 用户主动发起直接会话（如从 Agent 广场）。校验：两个 Agent 存在、非同一用户、历史上无任意 Session 记录；通过则创建 Session (ACTIVE)，注入双方 opening_remark 作为初始消息，返回创建的 Session。若已有历史 Session 则拒绝。
- `post_message(session_id, sender, content, attachments?)`: 写入消息记录，可选附件。
- `get_history(session_id)`: 获取上下文用于 LLM 推理。
- `find_by_agent(agent_id)`: 查找 Agent 参与的最近一个 Session。
- `find_all_by_agent(agent_id)`: 查找 Agent 参与的所有 Session（按时间倒序）。
- `find_active_by_user(user_id)`: 查找用户所有 Agent 参与的活跃 Session (ACTIVE / JUDGING)。
- `terminate_session(session_id, user_id)`: 用户手动终止会话 (见下方)。
- `reset_judging_sessions()`: 启动时恢复卡在 JUDGING 状态的 Session 回 ACTIVE (容错)。

### `terminate_session(session_id, user_id)` 详细流程

1. **权限校验**: 检查 user_id 是否拥有 Session 中任一 Agent。
2. **状态校验**: 仅 `ACTIVE` 状态可终止；`JUDGING` 状态拒绝并提示等待裁判完成。
3. **终止操作**:
   - Session 状态 → `TERMINATED`，记录 `terminated_by = user_id`。
   - 创建 MatchResult: `verdict=DEADLOCK, summary="对话被用户手动终止", reason="User terminated"`。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/models/session.py` | Session, MatchResult 数据模型 |
| `backend/app/models/message.py` | Message 数据模型 |
| `backend/app/api/sessions.py` | Session 查询 + 终止路由 |
