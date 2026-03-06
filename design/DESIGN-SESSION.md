# 会话沙盒 (Chat Session Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

两个 Agent 进行交互的封闭环境。每个 Session 包含一对 Agent 的完整对话历史和状态管理。用户可实时查看自己 Agent 参与的活跃会话，并有权手动终止对话。

## 字段 (Session)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `agent_a_id` | UUID | 参与方 A |
| `agent_b_id` | UUID | 参与方 B |
| `status` | Enum | 会话状态 (见下方状态机) |
| `terminated_by` | UUID (可选) | 手动终止时记录操作用户 ID，自然结束时为 null |
| `created_at` | Timestamp | 创建时间 |

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
| `timestamp` | Timestamp | 发送时间 |

## 核心功能 (Functions)

- `start_session(agent_a, agent_b)`: 创建 Session。
- `post_message(session_id, sender, content)`: 写入消息记录。
- `get_history(session_id)`: 获取上下文用于 LLM 推理。
- `find_by_agent(agent_id)`: 查找 Agent 参与的最近一个 Session。
- `find_active_by_user(user_id)`: 查找用户所有 Agent 参与的活跃 Session (ACTIVE / JUDGING)。
- `terminate_session(session_id, user_id)`: 用户手动终止会话 (见下方)。
- `reset_judging_sessions()`: 启动时恢复卡在 JUDGING 状态的 Session 回 ACTIVE (容错)。

### `terminate_session(session_id, user_id)` 详细流程

1. **权限校验**: 检查 user_id 是否拥有 Session 中任一 Agent。
2. **状态校验**: 仅 `ACTIVE` 状态可终止；`JUDGING` 状态拒绝并提示等待裁判完成。
3. **终止操作**:
   - Session 状态 → `TERMINATED`，记录 `terminated_by = user_id`。
   - 创建 MatchResult: `verdict=DEADLOCK, summary="对话被用户手动终止", reason="User terminated"`。
   - 双方 Agent 状态 → `DONE`。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/models/session.py` | Session, MatchResult 数据模型 |
| `backend/app/models/message.py` | Message 数据模型 |
| `backend/app/api/sessions.py` | Session 查询 + 终止路由 |
