# 技能模块 (Skill Module)

> 返回 [主设计文档](./DESIGN.md) | 参见 [Agent 模块](./DESIGN-AGENT.md)

## 概述

Skill 是 Agent 在对话过程中可使用的扩展能力。平台将 Skill 分为**内置技能 (Built-in)** 和**用户自定义技能 (User-defined)** 两类。

## 技术框架

| 技术 | 用途 |
|------|------|
| **FastAPI** | Skill CRUD API 路由 |
| **SQLModel** | Skill 数据模型 |
| **Pydantic** | SkillCreate / SkillUpdate / SkillRead Schema |
| **Prompt Engineering** | 内置技能通过 system_prompt 追加约束注入 LLM |
| **Python 字符串匹配** | 回复校验 (关键词 + 商品名白名单) |

- **内置技能**: 平台代码内置，根据 Agent 状态自动激活，**FREE + PAID 用户均可使用**，无需手动配置。
- **用户自定义技能**: 用户通过 API 创建 Skill 实体并关联到 Agent，**仅 PAID 用户**可用。

## 目录结构

```
backend/app/agent/skills/         # 内置技能实现
  ├── __init__.py
  └── product_salesman.py         # 内置: 商品推销员

backend/app/models/skill.py       # 用户自定义 Skill 数据模型
backend/app/schemas/skill.py      # Skill API Schema
backend/app/api/skill.py          # Skill CRUD 路由
```

## 两类 Skill 对比

| 维度 | 内置技能 (Built-in) | 用户自定义技能 (User-defined) |
|------|---------------------|------------------------------|
| **创建方式** | 平台代码内置，无需创建 | 用户通过 API 创建 Skill 实体 |
| **存储** | 不入数据库，纯代码逻辑 | 存入 `skill` 表 |
| **激活方式** | 根据 Agent 状态自动激活 | 用户手动关联到 Agent (`linked_skill_ids`) |
| **可用 Tier** | FREE + PAID | 仅 PAID |
| **配置** | 无需配置，满足条件即自动生效 | 用户自定义名称、描述等 |
| **执行机制** | Prompt 注入 + 回复校验 | Prompt 注入 + 回复校验 |

## 通用执行机制

无论内置还是用户自定义，所有 Skill 遵循统一的执行管线:

```
Orchestrator 调用 process_turn
  └─> 对话模块 (conversation.py) 接管
       ├─ 1. 判断当前 Agent 有哪些 Skill 应该激活
       ├─ 2. 对每个激活的 Skill:
       │       ├─ 加载 Skill 所需上下文 (商品数据、外部信息等)
       │       └─ 生成约束 Prompt 片段
       ├─ 3. 将所有 Skill 的 Prompt 片段追加到 Agent 的 system_prompt 后
       ├─ 4. 调用 LLM 生成回复
       └─ 5. 对每个激活的 Skill 执行回复校验
            ├─ [全部通过] → 正常发送消息
            └─ [有违规] → 追加更强约束后重试一次
```

### Skill 接口约定

每个 Skill (无论内置还是未来的自定义) 实现以下核心函数:

| 函数 | 签名 | 说明 |
|------|------|------|
| `is_active` | `(agent, **repos) -> bool` | 判断此 Skill 是否应在当前 Agent 上激活 |
| `build_*_prompt` | `(context) -> str` | 基于加载的上下文生成约束 Prompt 片段 |
| `validate_response` | `(response, context) -> (bool, reason?)` | 校验 LLM 回复是否合规 |

### Prompt 注入策略

所有 Skill 的约束通过**追加到 system_prompt 末尾**的方式注入:

```
{Agent 原始 system_prompt}

=== {Skill A 规则} ===
...
=== 规则结束 ===

=== {Skill B 规则} ===
...
=== 规则结束 ===
```

多个 Skill 的 Prompt 片段按激活顺序依次追加，互不干扰。

### 回复校验策略

- 每个 Skill 独立校验，任一 Skill 判定违规即触发重试。
- 重试时在 Prompt 中追加对应 Skill 的强化约束。
- 最多重试一次，避免无限循环。重试后仍违规则放行并记录日志。

---

## 内置技能 (Built-in Skills)

内置技能由平台提供，所有用户均可使用。根据 Agent 状态自动激活，用户无需任何额外操作。

### Product Salesman (商品推销员)

**定位**: 当 Agent 作为卖家身份时，严格限定 Agent 只能推销用户绑定的商品。

**激活条件**:

1. `agent.linked_product_ids` 非空
2. 其中至少有一个商品的 `status == ACTIVE`

不满足时，对话走正常流程，不注入任何约束。

**执行流程**:

```
process_turn 中检测到 Agent 有 linked_product_ids
  └─> is_active() 确认有 ACTIVE 商品
       └─> build_product_catalog() 从 ProductRepository 加载商品详情
            └─> build_salesman_prompt() 生成约束 Prompt:
                 ├─ 只推销目录中的商品
                 ├─ 允许对比竞品，但结论必须指向目录商品
                 ├─ 禁止推荐外部商品
                 ├─ 自然推销，根据对方需求匹配
                 └─ 诚实描述，不虚构功能
            └─> LLM 生成回复
            └─> validate_response() 校验回复合规性
                 ├─ [通过] → 发送消息
                 └─ [违规] → 追加强化约束后重试一次
```

**Prompt 注入模板**:

```
=== 商品推销规则 (强制) ===
你是一名专业销售代表。在本次对话中，你必须严格遵守以下规则:

1. **只推销目录中的商品**: 你只能推荐、介绍和推销下方「商品目录」中列出的商品。
2. **允许对比竞品**: 你可以提及或搜索市面上的竞品信息，但仅用于对比分析，目的是突出目录中商品的优势。
3. **禁止推荐外部商品**: 严禁建议对方购买任何不在目录中的商品，严禁提供外部购买链接。
4. **自然推销**: 在对话中自然地介绍商品，根据对方需求匹配目录中最合适的商品，不要生硬推销。
5. **诚实描述**: 基于商品目录中的信息如实描述商品，不虚构不存在的功能或特性。

【商品目录】
商品 1:
  - 名称: {name}
  - 价格: {price} {currency}
  - 描述: {description}
  - 商品ID: {id}
=== 规则结束 ===
```

**回复校验**: 基于推荐关键词 + 商品名白名单匹配，检测是否推荐了目录外的商品。

**联网搜索**: Prompt 中声明允许对比竞品。实际搜索能力取决于底层 LLM 是否原生支持 (如 GPT-4 with browsing、Gemini with grounding)。不支持时 Agent 基于训练数据中的竞品知识进行对比。未来可通过 function calling 提供统一搜索工具。

**核心函数**:

| 函数 | 位置 | 说明 |
|------|------|------|
| `is_active(agent, product_repo)` | `product_salesman.py` | 判断技能是否应激活 |
| `build_product_catalog(agent, product_repo)` | `product_salesman.py` | 加载 ACTIVE 商品，构建结构化目录 |
| `build_salesman_prompt(products)` | `product_salesman.py` | 生成约束 Prompt 片段 |
| `validate_response(response, products)` | `product_salesman.py` | 校验回复是否合规 |

---

## 用户自定义技能 (User-defined Skills)

仅 **PAID** 用户可用。用户创建 Skill 实体后关联到 Agent，Agent 在对话中可使用对应技能。

### 字段 (Skill Model)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `user_id` | UUID | 所属用户 |
| `name` | String | 技能名称 |
| `description` | Text (可选) | 技能描述 |
| `created_at` | Timestamp | 创建时间 |

### 与 Agent 的关联

- Agent 通过 `linked_skill_ids` 关联已创建的 Skill。
- 仅 Agent 所属用户创建的 Skill 可被关联。

### 核心功能 (API)

- `create_skill(user_id, name, description)`: 创建技能。
- `list_skills(user_id)`: 列出用户的全部技能。
- `update_skill(skill_id, user_id, ...)`: 更新技能信息。
- `delete_skill(skill_id, user_id)`: 删除技能。

---

## 设计决策

- **内置技能与用户 Skill 实体分离**: 内置技能不走 Skill CRUD 体系，不存入数据库，是代码层面的平台能力。避免修改 Skill 模型和权限体系的复杂度。
- **统一执行管线**: 所有 Skill 遵循 "激活判断 → 上下文加载 → Prompt 注入 → 回复校验" 的统一流程，便于新增 Skill。
- **Prompt 注入而非模型微调**: 通过追加指令约束 LLM 行为，成本低、灵活、兼容任意 LLM Provider (包括 FREE 用户自带的 API Key)。
- **按 Agent 状态自动激活**: 内置技能根据 Agent 上下文 (如是否绑定商品) 自动激活，用户无需额外操作。
- **回复校验作为安全网**: LLM 可能突破 Prompt 约束，因此增加 post-generation 校验层。轻量级实现用启发式匹配；若需更强保障可调用平台 LLM 做快速审查。
- **FREE/PAID 分层**: 内置技能是平台基础设施，所有用户可用；用户自定义技能是高级扩展能力，仅 PAID 用户可用。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/agent/skills/__init__.py` | Skills 包初始化 |
| `backend/app/agent/skills/product_salesman.py` | 内置技能: 商品推销员 |
| `backend/app/agent/conversation.py` | 对话模块 (集成 Skill 调用) |
| `backend/app/services/orchestrator.py` | 编排器 (传入依赖的 Repository) |
| `backend/app/models/skill.py` | 用户自定义 Skill 数据模型 |
| `backend/app/schemas/skill.py` | SkillCreate, SkillUpdate, SkillRead |
| `backend/app/api/skill.py` | Skill CRUD 路由 |
