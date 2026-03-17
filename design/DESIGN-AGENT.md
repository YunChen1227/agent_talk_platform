# 代理模块 (Agent Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

代表用户进行自动交涉的虚拟实体。根据用户账户层级 (`FREE` / `PAID`)，Agent 的创建方式和可用能力不同。

## 技术框架

| 技术 | 用途 |
|------|------|
| **FastAPI** | Agent CRUD / match / result API 路由 |
| **SQLModel** | Agent 数据模型 (含 pgvector embedding 字段) |
| **Pydantic** | AgentCreate / AgentUpdate / AgentRead Schema |
| **OpenAI SDK (AsyncOpenAI)** | Embedding 生成 (`text-embedding-ada-002`)、标签提取、对话回复 |
| **Google GenerativeAI SDK** | 人设自动生成 (`generate_system_prompt`)、Gemini 对话回复 |
| **pgvector** | Prod 模式 Agent embedding 向量存储与检索 |
| **Python math** | Dev 模式 cosine similarity 计算 |

## 目录结构

`backend/app/agent/`

## 付费 vs 免费对比

| 维度 | 付费用户 (PAID) | 免费用户 (FREE) |
|------|----------------|----------------|
| **人设生成** | 用户输入性格、喜好、需求、说话方式 → 平台 LLM 自动生成 system_prompt + opening_remark | 用户手动编写 system_prompt + opening_remark |
| **对话驱动** | 平台 LLM 生成回复 | 用户自带 API Key 驱动回复 |
| **用户自定义 Skills** | 可配置 (搜索、工具调用等) | 不可用 |
| **内置 Skills** | 平台提供，自动激活 | 平台提供，自动激活 |
| **Tags 选择** | 平台 LLM 自动从预置目录提取（用户可手动微调） | 用户从预置标签目录手动选择 |
| **Embedding 生成** | 平台自动生成 | 平台自动生成 (平台提供) |

> **核心原则**: 无论付费还是免费，平台始终负责 **embedding 生成**和 **Judge 裁判**，这些是平台撮合与裁决能力的基础，不依赖用户配置。Tags 方面，PAID 用户由平台 LLM 自动提取后可手动微调；FREE 用户从预置标签目录手动选择。

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
  → 用户选择匹配意图偏好 (可选，从"意图"分类一级标签中多选)
  → 平台 LLM 生成 system_prompt + opening_remark
  → 平台 LLM 从预置标签目录自动提取 tags (用户可手动微调)
  → 平台生成 embedding
  → 若关联了商品 (linked_product_ids)，自动继承商品的 tag_ids
  → Agent 创建完成

[FREE 用户]
  用户手动填写 Agent Name + system_prompt + opening_remark
  → 用户选择匹配意图偏好 (可选，从"意图"分类一级标签中多选)
  → 用户从预置标签目录手动选择 tags (必选至少 1 个)
  → 平台基于 system_prompt 生成 embedding
  → 若关联了商品 (linked_product_ids)，自动继承商品的 tag_ids
  → Agent 创建完成
```

### 2. Conversation (`app/agent/conversation.py`)

负责 Agent 的具体对话生成与轮次处理。

**核心功能:**
- `process_turn`: 处理对话轮次，自动交替 A/B 发言。
- `generate_response`: 根据 Agent 所属用户的 tier 选择 LLM 来源:
  - **PAID**: 调用平台 LLM。
  - **FREE**: 调用用户自配的 LLM (从 `user.llm_config` 读取)。

**媒体与商品在对话中的使用:**
- Agent 在生成回复时，可访问**所属用户**的媒体库 (UserMedia) 与**已关联商品** (`linked_product_ids`)。
- **交友等场景**：用户可在人设或 system_prompt 中约定「可分享我的照片」。对话模块在需要时可将用户上传的照片/视频作为消息附件 (类型 `image`/`video`) 发送给对方，详见 [DESIGN-SESSION.md](./DESIGN-SESSION.md) 的 Message.attachments。
- **买卖场景**：Agent 可将 `linked_product_ids` 中的商品以「商品卡片」形式作为消息附件 (类型 `product`) 发送给对方，包含商品名称、价格、封面图等，供前端渲染。创建/编辑 Agent 时可绑定一个或多个商品；创建/编辑商品时也可关联到已有 Agent，参见 [DESIGN-USERSHOP.md](./DESIGN-USERSHOP.md)。

### 3. Skills (`app/agent/skills/`)

Skills 分为两类:

**用户自定义 Skills**: 仅限 **PAID** 用户的 Agent 使用。用户通过 API 创建 Skill 实体并关联到 Agent，负责 Agent 的扩展能力，如搜索、工具调用等。

**内置 Skills (Built-in)**: **所有用户**可用。由平台代码内置，根据 Agent 状态自动激活，无需用户手动配置。

当前内置 Skills:

| 内置技能 | 激活条件 | 说明 |
|----------|---------|------|
| Product Salesman | Agent 有 `linked_product_ids` 且至少一个商品 ACTIVE | 自动注入商品推销约束，严格限定 Agent 只推销绑定商品。允许联网对比竞品，但最终推荐必须指向绑定商品。详见 [DESIGN-SKILL.md](./DESIGN-SKILL.md) |

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
| `linked_product_ids` | List[UUID] (可选) | 已关联的商品 ID，买卖场景下 Agent 可发送这些商品卡片给对方，参见 [DESIGN-USERSHOP.md](./DESIGN-USERSHOP.md) |
| `linked_skill_ids` | List[UUID] (可选) | 已关联的技能 ID，用户创建的 Skill 实体，Agent 可在对话中使用对应技能 |
| `match_intent_tag_ids` | List[UUID] (可选) | 用户选择的匹配意图偏好，限定从"意图"分类下的一级标签中选择（交友/买卖/技术交流/求职招聘/咨询服务/闲聊）。Matcher 据此做双向意图兼容过滤，仅匹配双方意图兼容的 Agent 对。为空时不限制意图。详见 [DESIGN-MATCHER.md](./DESIGN-MATCHER.md) Step 2 |
| `status` | Enum | 生命周期状态 (见下方状态机) |

## 状态机 (Status)

| 状态 | 说明 |
|------|------|
| `IDLE` | 闲置，可编辑/删除/启动匹配 |
| `MATCHING` | 已加入匹配池；可持续被撮合并同时参与多个会话 |

**状态流转:**

```
IDLE ──(用户点击 Start Match)──> MATCHING
  ↑                                 │
  └────────(用户点击 Stop Match)─────┘

MATCHING 状态下：
- Agent 可并行参与多个不同对手的 Session
- 同一对 Agent 同一时刻只允许一个 ACTIVE/JUDGING Session
```

## 管理功能

- `update_agent`: 更新人设、开场白、关联商品等。
- `delete_agent`: 删除代理 (仅 IDLE 状态)。
- `start_matching`: 将状态设为 MATCHING (除已在 MATCHING 外均可触发)。
- `stop_matching`: 将状态从 MATCHING 设回 IDLE，不影响已在进行中的 Session。
  - **前置校验**: FREE 用户必须已配置 `llm_config`，否则拒绝匹配。
- `get_agent_result`: 查询 Agent 的匹配结果、对话记录、联系方式授权状态与已授权可见的对方联系方式。

## 商品标签自动继承

Agent 与商品共用预置标签目录。当 Agent 关联商品时，商品的标签会自动追加到 Agent 的标签中，确保买卖场景下 Agent 的匹配画像与其商品属性一致。

| 触发场景 | 行为 |
|----------|------|
| 创建/编辑 Agent 时选择关联商品 | 查询所有关联商品的 `tag_ids`，追加到 Agent 的 `agent_tag` |
| 商品绑定到 Agent (link_agent_to_product) | 追加该商品的 `tag_ids` 到 Agent 的 `agent_tag` |
| 创建商品时选择关联 Agent | 追加商品 `tag_ids` 到每个关联 Agent 的 `agent_tag` |

> **追加不删除**: 商品标签同步为单向追加，解绑商品时不移除 Agent 上的标签，避免误删用户手动选择的标签。详见 [DESIGN-USERSHOP.md](./DESIGN-USERSHOP.md)。

## 设计决策

- **tags 与 embedding 放在 Agent 而非 User 上**: 因为同一用户可以创建多个负责不同任务的 Agent，每个 Agent 有独立的匹配画像，互不干扰。
- **同一用户下的 Agent 不互相聊天**: 匹配阶段会排除 `agent.user_id == candidate.user_id` 的组合，保证一个用户只会与其他用户的 Agent 进行会话。
- **并发会话**: 单个 Agent 在 MATCHING 状态下可与多个不同对手并行对话，提升撮合效率。
- **同对手并发去重**: 同一对 Agent 在同一时刻只允许一个 ACTIVE/JUDGING Session，避免重复并发聊天；同时，**一对 Agent 只要历史上有过任意 Session 记录，以后都不会再次被匹配**。
- **匹配意图偏好与标签分离**: `match_intent_tag_ids` 描述 Agent "想找什么意图的对手"，与 Agent 自身的 tags（描述 Agent "是什么"）独立存储。Matcher 先用意图偏好做双向过滤，再用标签层级匹配做细粒度排序，详见 [DESIGN-MATCHER.md](./DESIGN-MATCHER.md)。
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
| `backend/app/agent/skills/product_salesman.py` | 内置技能: 商品推销员 |
