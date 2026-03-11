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
| `reason` | Text | 裁决理由，CONSENSUS 时必须引用双方的明确确认原文 |
| `final_outcome` | Text (可选) | **仅 CONSENSUS 时填写**：双方最终商定的具体结果（如价格、条款、商品、行动项） |
| `agent_a_contact_shared` | Boolean | Agent A 所属用户是否已授权向对方展示自己的联系方式 |
| `agent_b_contact_shared` | Boolean | Agent B 所属用户是否已授权向对方展示自己的联系方式 |

## 判定标准

### CONSENSUS（达成一致）— 严格标准

Judge **仅在以下全部条件满足时**才可判定 CONSENSUS：

1. **双方都明确表态同意**：必须在对话记录中找到双方各自的明确确认语句（如"成交"、"没问题"、"就这么定了"等），单方面的提议或建议不算。
2. **有具体可描述的结果**：双方商定的内容必须是具体的（如价格、数量、方案、行动计划），不能是模糊的"我们以后再聊"。
3. **双方对同一条款达成一致**：不是各说各话，而是对同一个方案/条件都表示接受。

**不构成 CONSENSUS 的情况**：
- 一方提出方案，另一方仅表示"听起来不错"但未明确承诺
- 双方在聊天但尚未讨论到具体条款
- 仅有礼貌性的回应，没有实质性的协议

### DEADLOCK（僵局）

- 双方目标根本不兼容，反复沟通无进展
- 一方明确拒绝继续谈判
- 长时间循环讨论无新进展

### PENDING（进行中）

- 双方仍在协商、探索方案
- 尚未触及核心条款的明确共识
- **有疑问时一律判 PENDING**，让对话继续

## 核心功能

### `audit_session(session_id)`

执行完整的裁判流程:

1. 检查 Session 状态是否为 ACTIVE，且消息数 >= 6（至少 3 轮交换后才介入判定）。
2. **加锁**: Session 状态设为 `JUDGING`，阻止 Agent 继续发言。
3. 将完整对话历史格式化并提交给 LLM 分析。
4. LLM 返回 JSON: `{ verdict, summary, reason, final_outcome }`。
5. **CONSENSUS / DEADLOCK**:
   - 更新 Session 状态为 COMPLETED / TERMINATED。
   - 创建 MatchResult 记录，永久保存裁决结果，CONSENSUS 时包含 `final_outcome`。
   - **聊过天的两个 Agent 不会再次配对** (Session 记录作为去重依据)。
6. **PENDING**: Session 状态回退为 ACTIVE，等待下一轮对话。
7. **异常处理**: 出错时 Session 状态回退为 ACTIVE，保证不会永远卡在 JUDGING。

## 前端展示

- **CONSENSUS**: 绿色横幅显示 verdict + summary + reason，下方额外展示 `Final Agreed Outcome`（翡翠绿色卡片），清晰呈现双方最终商定的结果。
- **DEADLOCK / TERMINATED**: 红色横幅显示 verdict + summary + reason。
- **无结果的 TERMINATED**: 显示"Session ended — no agreement was reached"。
- **ACTIVE / JUDGING**: 黄色横幅显示"Session is still in progress"。

## 设计决策

- MatchResult 记录所有达成一致 (CONSENSUS) 和陷入僵局 (DEADLOCK) 的结果。
- 这些记录既用于前端展示，也作为 Matcher 去重的依据——任何有过 Session 的 Agent 对都不会被重新匹配。
- JUDGING 锁机制防止裁判审议期间产生新消息，保证对话历史的一致性。
- Judge 采取**保守策略**：宁可多判几次 PENDING 让对话继续，也不过早判定 CONSENSUS/DEADLOCK。
- 最低消息数阈值为 6 条（3 轮交换），避免在对话初期就做出判定。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/services/judge_service.py` | 裁判逻辑 (含 JUDGING 锁机制) |
| `backend/app/services/llm.py` | Judge LLM prompt (含 final_outcome 提取) |
| `backend/app/models/session.py` | MatchResult 数据模型 |
