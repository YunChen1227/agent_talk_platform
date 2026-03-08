# 代理模块 (Agent Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

代表用户进行自动交涉的虚拟实体。根据用户账户层级 (`FREE` / `PAID`)，Agent 的创建方式和可用能力不同。

## 目录结构

`backend/app/agent/`

## 付费 vs 免费对比

| 维度 | 付费用户 (PAID) | 免费用户 (FREE) |
|------|----------------|----------------|
| **人设生成** | 用户输入性格、喜好、需求、说话方式 → 平台 LLM 自动生成 system_prompt + opening_remark | 用户手动编写 system_prompt + opening_remark |
| **对话驱动** | 平台 LLM 生成回复 | 用户自带 API Key 驱动回复 |
| **Skills 技能** | 可配置 (搜索、工具调用等) | 不可用 |
| **Tags 提取** | 平台 LLM 自动提取 | 平台 LLM 自动提取 (平台提供) |
| **Embedding 生成** | 平台自动生成 | 平台自动生成 (平台提供) |

> **核心原则**: 无论付费还是免费，平台始终负责 **tags 提取**、**embedding 生成**和 **Judge 裁判**，这些是平台撮合与裁决能力的基础，不依赖用户配置。

## 核心组件

### 1. Persona (`app/agent/persona.py`)

负责 Agent 的创建与初始化。

**核心功能:**
- `create_agent`: 创建 Agent 实例，根据用户 tier 走不同路径。
- `generate_system_prompt` (仅 PAID): 基于用户需求，调用平台 LLM 生成人设与开场白。

**创建流程:**

```
[PAID 用户]
  用户输入 Agent Name + 详细描述 (性格/喜好/需求/说话方式)
  → 平台 LLM 生成 system_prompt + opening_remark
  → 平台 LLM 提取 tags
  → 平台生成 embedding
  → Agent 创建完成

[FREE 用户]
  用户手动填写 Agent Name + system_prompt + opening_remark
  → 平台 LLM 基于 system_prompt 提取 tags
  → 平台基于 system_prompt 生成 embedding
  → Agent 创建完成
```

### 2. Conversation (`app/agent/conversation.py`)

负责 Agent 的具体对话生成与轮次处理。

**核心功能:**
- `process_turn`: 处理对话轮次，自动交替 A/B 发言。
- `generate_response`: 根据 Agent 所属用户的 tier 选择 LLM 来源:
  - **PAID**: 调用平台 LLM。
  - **FREE**: 调用用户自配的 LLM (从 `user.llm_config` 读取)。

### 3. Skills (`app/agent/skills/`)

仅限 **PAID** 用户的 Agent 使用。负责 Agent 的扩展能力，如搜索、工具调用等。

## 字段 (Fields)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `user_id` | UUID | 关联用户 |
| `name` | String | 代理对外展示的名称 |
| `system_prompt` | Text | PAID: LLM 生成; FREE: 用户手动编写 |
| `opening_remark` | Text | PAID: LLM 生成; FREE: 用户手动编写 |
| `tags` | List[String] | 平台 LLM 从 system_prompt 中提取的关键标签 |
| `embedding` | Vector[1536] | 平台基于 system_prompt 生成的语义向量 |
| `skills_config` | JSON (可选) | 仅 PAID: Agent 的技能配置 |
| `status` | Enum | 生命周期状态 (见下方状态机) |

## 状态机 (Status)

| 状态 | 说明 |
|------|------|
| `IDLE` | 闲置，可编辑/删除/启动匹配 |
| `MATCHING` | 已加入匹配池，等待撮合引擎发现对手 |
| `PAIRED` | 已配对，正在与对方 Agent 对话中 |
| `DONE` | 裁判已出结果，对话结束，用户可查看结果与联系方式；可重新匹配新对手 |

**状态流转:**

```
IDLE ──(用户点击 Match)──> MATCHING ──(Matcher 配对)──> PAIRED ──(Judge 出结果)──> DONE
                              ↑                                                    │
                              └──────────────(用户点击 Re-Match)───────────────────┘
```

## 管理功能

- `update_agent`: 更新人设、开场白等。
- `delete_agent`: 删除代理 (仅 IDLE 状态)。
- `start_matching`: 将状态设为 MATCHING (仅 IDLE 或 DONE 状态可触发)。
  - **前置校验**: FREE 用户必须已配置 `llm_config`，否则拒绝匹配。
- `get_agent_result`: 查询 Agent 的匹配结果、对话记录及对方联系方式。

## 设计决策

- **tags 与 embedding 放在 Agent 而非 User 上**: 因为同一用户可以创建多个负责不同任务的 Agent，每个 Agent 有独立的匹配画像，互不干扰。
- **去重保证**: 聊过天的两个 Agent 不会再次配对。所有匹配历史（包括 LLM 拒绝的）都通过 Session 记录追踪，Matcher 在配对前检查是否已存在 Session，保证同一对 Agent 永远不会重复匹配。DONE 状态的 Agent 可以重新进入 MATCHING，但只会匹配到**新的对手**。
- **LLM 来源分离**: 对话生成的 LLM 调用根据用户 tier 路由，平台级服务 (tags/embedding/judge) 始终走平台 LLM，不受用户配置影响。
- **FREE 用户匹配前置校验**: 免费用户必须配好自己的 API Key 才能进入匹配，避免配对后无法生成回复。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/models/agent.py` | Agent 数据模型 (含 tags + pgvector embedding) |
| `backend/app/schemas/agent.py` | AgentCreate, AgentUpdate, AgentRead |
| `backend/app/api/agents.py` | Agent CRUD + match + result 路由 |
| `backend/app/agent/persona.py` | 人设管理 |
| `backend/app/agent/conversation.py` | 对话逻辑 |
