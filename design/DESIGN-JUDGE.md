# 裁判系统 (Judge Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

**每个 Chat Session 配有独立的 Judge**，作为旁观者 AI 负责监控与裁决。每轮对话结束后自动介入评估，判定对话是否达成共识或陷入僵局。

> **LLM 来源**: Judge 始终使用**平台 LLM**，不受用户层级 (FREE/PAID) 影响。裁判的公正性和一致性由平台统一保障。

## 字段 (MatchResult)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `session_id` | UUID | 关联会话，一对一 |
| `verdict` | Enum | CONSENSUS-达成一致, DEADLOCK-僵局, PENDING-进行中 |
| `summary` | Text | 对话摘要/结论 |
| `reason` | Text | 裁决理由 |
| `agent_a_contact_shared` | Boolean | Agent A 所属用户是否已授权向对方展示自己的联系方式 |
| `agent_b_contact_shared` | Boolean | Agent B 所属用户是否已授权向对方展示自己的联系方式 |

## 核心功能

### `audit_session(session_id)`

执行完整的裁判流程:

1. 检查 Session 状态是否为 ACTIVE，且消息数 >= 2。
2. **加锁**: Session 状态设为 `JUDGING`，阻止 Agent 继续发言。
3. 将完整对话历史格式化并提交给 LLM 分析。
4. LLM 返回 JSON: `{ verdict, summary, reason }`。
5. **CONSENSUS / DEADLOCK**:
   - 更新 Session 状态为 COMPLETED / TERMINATED。
   - 创建 MatchResult 记录，永久保存裁决结果。
   - 将双方 Agent 状态设为 `DONE`。
   - **聊过天的两个 Agent 不会再次配对** (Session 记录作为去重依据)。
6. **PENDING**: Session 状态回退为 ACTIVE，等待下一轮对话。
7. **异常处理**: 出错时 Session 状态回退为 ACTIVE，保证不会永远卡在 JUDGING。

## 设计决策

- MatchResult 记录所有达成一致 (CONSENSUS) 和陷入僵局 (DEADLOCK) 的结果。
- 这些记录既用于前端展示，也作为 Matcher 去重的依据——任何有过 Session 的 Agent 对都不会被重新匹配。
- JUDGING 锁机制防止裁判审议期间产生新消息，保证对话历史的一致性。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/services/judge_service.py` | 裁判逻辑 (含 JUDGING 锁机制) |
| `backend/app/models/session.py` | MatchResult 数据模型 |
