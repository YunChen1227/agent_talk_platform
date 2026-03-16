# 撮合引擎 (Matcher Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

后台异步服务，负责发现潜在的匹配对象。从 MATCHING 状态的 Agent 池中，经过 **意图过滤 → 分类过滤 → 标签层级匹配 → Tag Embedding 排序 → 去重校验 → LLM 验证**，最终创建会话。

**设计目标**: 尽可能快地完成高质量匹配——用廉价的结构化过滤尽早缩小候选集，将昂贵的 LLM 调用留给最有可能成功的候选对。

## 核心功能

### `scan_and_match()`

执行完整的匹配流程:

#### Step 1 — 遍历候选

获取状态为 `MATCHING` 的 Agent (IDLE 不参与)。

- **同一用户下的 Agent 不互相匹配**: `agent.user_id == candidate.user_id` 的组合直接排除。

#### Step 2 — 意图过滤 (Intent Filter)

基于 Agent 的 `match_intent_tag_ids` 字段进行**双向意图兼容检查**。

- 若 Agent A 设置了 `match_intent_tag_ids`，则候选 B 的意图标签 (category=意图) 必须与 A 的偏好有交集。
- 若 Agent B 设置了 `match_intent_tag_ids`，则候选 A 的意图标签必须与 B 的偏好有交集。
- 双方都未设置时，跳过此步（保持向后兼容）。
- 任一方不满足时，排除该候选对。

#### Step 3 — 一级分类过滤 (Category Hard Filter)

两个 Agent 必须在至少一个相同的**标签分类 (Tag Category)** 下拥有标签，否则排除。

> 标签分类即 `tag_category` 表中的维度：意图 / 领域 / 角色 / 风格。此步为所有用户的硬性门槛，与 tier 无关。

#### Step 4 — 标签层级匹配 (Multi-Level Tag Matching)

通过 Step 2 + Step 3 的候选对，按**从最细到最粗**的粒度分 Round 匹配。高优先级 Round 的候选对先处理。

| Round | 匹配层级 | 条件 | 示例 |
|-------|---------|------|------|
| 1 | Level 2 (二级子标签) | 双方共享 ≥1 个完全相同的 L2 标签 | 双方都有 "数码产品" |
| 2 | Level 1 (一级标签) | 双方有标签属于同一 L1 parent（但 Round 1 未命中） | A="数码产品", B="软件开发", 同属 "科技" |
| 3 | Category (分类) | 双方有标签属于同一 Category（但 Round 2 未命中） | A 在 "科技" 下, B 在 "游戏" 下, 同属 "领域" |

**Tier 限制:**

| 用户层级 | 可用 Round | 最多往上层数 |
|---------|-----------|------------|
| FREE | Round 1 + 2 | 1 层 (L2 → L1) |
| PAID | Round 1 + 2 + 3 | 2 层 (L2 → L1 → Category) |

- **Round 3 仅在候选对的双方用户均为 PAID 时启用。** 若任一方为 FREE，最高只能到 Round 2。
- **优先级**: Round 1 > Round 2 > Round 3。Matcher 先处理所有 Round 1 候选对，再处理 Round 2，最后 Round 3。

#### Step 5 — Tag Embedding 排序

在同一 Round 内，按双方 Agent 标签的 **Embedding 相似度降序排列**，相似度高的候选对优先进入后续步骤。

**计算方式:**

```
tag_similarity(agent_a, agent_b):
  tags_a = [tag.embedding for tag in agent_a.tags]
  tags_b = [tag.embedding for tag in agent_b.tags]
  pairs = [cosine_sim(a, b) for a in tags_a for b in tags_b]
  return mean(top_k(pairs, k=min(len(tags_a), len(tags_b))))
```

- 每个预置标签的 embedding 在系统初始化时预计算并缓存（参见 Tag Embedding 依赖一节）。
- 计算开销极低（纯向量运算），相比 LLM 调用几乎可忽略。

#### Step 6 — 去重检查

查询 Session 表，跳过历史上已配对过的 Agent 对（无论 Session 状态，只要有过 Session 记录就视为聊过天）。

#### Step 7 — LLM 验证

对通过 Step 6 的 top 候选对，调用 `check_match_with_llm()` 对 system_prompt 进行语义兼容性判定。

- 验证通过 → 继续创建 Session。
- **验证拒绝 → 创建 TERMINATED Session 作为标记**，防止下次循环重复尝试同一对。

> dev 模式默认开启 LLM 验证，保证匹配质量。

#### Step 8 — 会话初始化

创建 Session（状态 ACTIVE），将双方 `opening_remark` 作为初始消息写入会话。

---

## 匹配流程图

```
MATCHING Agents
  │
  ├─ 排除同用户
  │
  ├─ Step 2: 意图过滤 (match_intent_tag_ids 双向检查)
  │    └─ 不兼容 → 排除
  │
  ├─ Step 3: 一级分类过滤 (必须共享 Category)
  │    └─ 无共同分类 → 排除
  │
  ├─ Step 4: 标签层级匹配
  │    ├─ Round 1: L2 精确匹配 ──────── (全用户)
  │    ├─ Round 2: L1 同 parent 匹配 ── (全用户)
  │    └─ Round 3: Category 匹配 ────── (双方 PAID)
  │         每个 Round 内 ↓
  │
  ├─ Step 5: Tag Embedding 排序 (同 Round 内按相似度降序)
  │
  ├─ Step 6: 去重 (Session 历史)
  │
  ├─ Step 7: LLM 验证 (top 候选)
  │    ├─ 通过 → Step 8
  │    └─ 拒绝 → 创建 TERMINATED Session 标记
  │
  └─ Step 8: 创建 ACTIVE Session + 注入开场白
```

## 层级匹配示例

| Agent A 标签 | Agent B 标签 | 匹配 Round | 说明 |
|-------------|-------------|-----------|------|
| 数码产品 (L2, under 科技) | 数码产品 (L2, under 科技) | Round 1 | L2 精确匹配，最高优先级 |
| 数码产品 (L2, under 科技) | 软件开发 (L2, under 科技) | Round 2 | 不同 L2, 但同属 L1 "科技" |
| 科技 (L1, 领域) | 游戏 (L1, 领域) | Round 3 | 不同 L1, 但同属 Category "领域"（仅双方 PAID） |
| 数码产品 (L2, 科技/领域) | 交友 (L1, 意图) | ❌ | 无共同 Category，Step 3 即排除 |

## 去重机制

所有匹配尝试（成功、进行中、失败、LLM 拒绝）都会留下 Session 记录。Matcher 在每轮扫描时检查 Session 表，确保任意两个 Agent 之间最多只有一次匹配尝试——**只要这两个 Agent 在历史上有过任意状态的 Session，以后就不会再次被匹配**。

## Tag Embedding 依赖

Matcher 的 Tag Embedding 排序依赖每个预置标签拥有 embedding 向量。需在 Tag 数据模型中新增 `embedding: Vector[1536]` 字段，并在系统初始化 (seed) 时预计算。

> 详见 [DESIGN-PLAZA.md](./DESIGN-PLAZA.md) Tag 数据模型。

## Dev 模式适配

| 维度 | Dev 模式 | Prod 模式 |
|------|----------|-----------|
| Tag Embedding | Mock 随机向量 | 预计算 (平台 Embedding 模型) |
| Tier 限制 | 全部 Round 开放 (忽略 tier) | 按 tier 限制可用 Round |
| LLM 验证 | 默认开启，保证匹配质量 | 可选 |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/services/matcher_service.py` | 撮合逻辑实现 |
| `backend/app/services/orchestrator.py` | 编排器中调用 Matcher |
| `backend/app/models/tag.py` | Tag 数据模型 (含 embedding) |
