# Plaza 模块 (Plaza Module)

> 返回 [主设计文档](./DESIGN.md) | 页面设计见 [DESIGN-PAGE-PLAZA.md](./DESIGN-PAGE-PLAZA.md)

## 概述

Plaza（Agent 广场）是平台的核心发现与检索模块。

## 技术框架

| 技术 | 用途 |
|------|------|
| **FastAPI** | Plaza API 路由 (`/plaza/tags`, `/plaza/search`) |
| **SQLModel** | TagCategory / Tag / AgentTag 数据模型 (两级层级标签体系) |
| **Pydantic** | TagCategoryRead / TagRead / PlazaSearchResponse Schema |
| **RRF (Reciprocal Rank Fusion)** | 向量搜索 + 关键词搜索结果融合排序 (k=60) |
| **Cosine Similarity** | Dev 模式 Python 内存向量相似度计算 |
| **pgvector `<=>`** | Prod 模式 PostgreSQL 向量距离检索 |
| **本地 Embedding 服务** | Agent/Tag 向量与（可选）Plaza 关键词向量：`EMBEDDING_API_URL`，OpenAI 兼容 `POST /v1/embeddings` |

用户在此浏览、搜索其他用户的 Agent，通过结构化标签过滤与混合精度搜索找到合适的 Agent，发起直接会话。Plaza 同时展示当前用户与目标 Agent 之间的匹配状态，帮助用户快速了解历史交互。

**核心能力:**
- 结构化标签体系（类电商分面搜索）
- 混合精度搜索（Embedding + 关键词 + Reranking）
- 匹配状态追踪（四状态展示）

**不涉及:** 订单管理、库存管理、支付。平台业务核心是"找到对的 Agent → 聊天协商 → 达成一致后交换联系方式"。

## 目录结构

```
backend/app/models/tag.py            # TagCategory, Tag, AgentTag 数据模型
backend/app/schemas/plaza.py         # Plaza 搜索请求/响应 Schema
backend/app/api/plaza.py             # Plaza API 路由
backend/app/services/plaza_service.py # 混合搜索 + 匹配状态计算
```

---

## 一、标签体系 (Tag Taxonomy)

### 设计思路

类似电商产品的分面标签系统，支持**两级层级结构**。标签按**分类 (Category)** 组织维度（意图、领域、角色、风格），每个分类下有**一级标签 (Root Tag)**，一级标签下可有**二级子标签 (Child Tag)**。

层级设计原则：
- 一级标签覆盖大类（如"科技"、"美食"），适合粗粒度浏览
- 二级子标签提供细分（如"科技→数码产品"、"美食→中餐"），适合精确筛选
- 不做三级以上——更细粒度交给关键词 + Embedding 语义搜索
- 选中一级标签时，后端自动将其所有子标签也纳入过滤条件

### 数据库表

**tag_category** (标签分类 / 维度):

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `name` | String | 分类名称，如"意图"、"领域" |
| `slug` | String (unique) | URL 友好标识，如"intent"、"domain" |
| `description` | Text (可选) | 分类说明 |
| `scope` | String | `"agent"` 或 `"product"`，标识该分类维度所属域。Agent 维度 (意图/领域/角色/风格) 与 Product 维度 (商品分类/品质/类型/适用) 在数据源头彻底隔离 |
| `sort_order` | Integer | 排序权重，升序 |
| `is_active` | Boolean | 是否启用，默认 True |

**tag** (标签，支持两级层级):

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `category_id` | UUID (FK → tag_category) | 所属分类 |
| `name` | String | 标签名称，如"交友"、"科技"、"数码产品" |
| `slug` | String (unique) | URL 友好标识，如"dating"、"tech"、"tech-digital" |
| `parent_id` | UUID (FK → tag, 可选) | 父标签 ID；为 NULL 表示一级标签，非 NULL 表示二级子标签 |
| `sort_order` | Integer | 分类内排序权重 |
| `is_active` | Boolean | 是否启用，默认 True |
| `embedding` | JSON (float 数组，可选) | 标签名称的语义向量，维度 = `EMBEDDING_DIM`（与 Agent 向量一致），用于 Matcher Tag Embedding 排序等 |
| `is_user_defined` | Boolean | `true` 表示用户通过 Plaza 创建的自定义标签；预置 seed 标签为 `false` |

**agent_tag** (Agent-Tag 多对多关联):

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent_id` | UUID (FK → agent) | 复合主键之一 |
| `tag_id` | UUID (FK → tag) | 复合主键之二 |

### 预置标签目录（两级结构，按 scope 隔离）

**Agent scope** (`scope = "agent"`):

| 分类 | 一级标签 | 二级子标签 |
|------|----------|------------|
| 意图 | 交友, 买卖, 技术交流, 求职招聘, 咨询服务, 闲聊 | —（暂无子标签） |
| 领域 | 科技 | 数码产品, 软件开发, 人工智能, 互联网 |
| 领域 | 时尚 | 服饰, 美妆, 奢侈品 |
| 领域 | 美食 | 中餐, 西餐, 甜品饮品 |
| 领域 | 旅行 | 国内游, 出境游 |
| 领域 | 教育 | K12, 留学, 职业培训 |
| 领域 | 金融 | 投资理财, 保险, 贷款 |
| 领域 | 健康, 游戏, 文化, 音乐, 体育 | —（暂无子标签） |
| 领域 | 房产 | 新房, 二手房, 租房 |
| 领域 | 汽车 | 新车, 二手车 |
| 角色 | 买家, 卖家, 顾问, 求职者, 招聘方, 服务提供者, 服务需求者 | —（暂无子标签） |
| 风格 | 专业, 友好, 幽默, 严肃, 耐心, 高效 | —（暂无子标签） |

### 标签过滤行为

- **选中一级标签**: 后端自动展开，同时匹配该标签本身及其所有二级子标签
- **选中二级标签**: 仅精确匹配该子标签
- **混合选中**: 多个标签之间为 OR 关系（包含任一即匹配）
- **UI 展开**: 点击有子标签的一级标签时，下方展开显示子标签行，可进一步精选

### Agent 模型兼容策略

- **保留** `Agent.tags: List[str]` 作为反规范化缓存字段，不破坏现有代码
- **新增** `agent_tag` 关联表作为权威数据源
- 写入时：先写 `agent_tag`，再同步更新 `Agent.tags` 缓存
- 读取时：列表场景用缓存字段；搜索场景走关联查询

### Tag 提取流程

Agent 创建时，平台 LLM 从预置标签目录中选择匹配的标签（约束提取），而非自由生成。用户还可通过 Plaza **新增自定义标签**并绑定到自己的 Agent；自定义标签与预置标签一样写入 `agent_tag`，并具备 `embedding`（创建或批量补算时写入）。

```
Agent 创建/更新
  └─> 平台 LLM 分析 system_prompt（PAID 路径）
       └─> 从预置标签目录中选取匹配的 tag slugs
            └─> 写入 agent_tag 关联表
                 └─> 同步缓存到 Agent.tags (List[str])
  或 用户手动 tag_ids（含预置 + 自定义）
```

提取 Prompt 模板向 LLM 传入完整标签目录 (JSON)，要求 LLM 输出选中的 tag slug 列表。

### Agent 标签与 Product 标签彻底分离

通过 `tag_category.scope` 字段实现数据源头隔离：

- **Agent 标签** (`scope = "agent"`)：意图、领域、角色、风格四个维度。Agent 的 `tag_ids` 只接受 agent-scope 下的标签；用户可通过 `POST /plaza/tags` 创建自定义标签（`is_user_defined=true`），自定义标签始终属于 agent-scope。
- **Product 标签** (`scope = "product"`)：商品分类、品质、类型、适用四个维度。Product 的 `tag_ids` 只接受 product-scope 下的标签；不允许用户自定义。
- **无交叉同步**：Product 标签不会自动继承到 Agent 的 `agent_tag`，两套标签体系完全独立。
- **API 隔离**：`GET /plaza/tags` 仅返回 agent-scope 标签；`GET /shop/tags` 仅返回 product-scope 标签。
- **自定义标签的向量**：创建时调用本地 Embedding 服务，写入 `tag.embedding`；也可调用 `POST /plaza/tags/embed` 批量补算或全量重算。

---

## 二、混合精度搜索 (Hybrid Search)

### 搜索架构

当用户在 Plaza 中输入搜索关键词时，系统同时执行多条搜索路径并融合结果。

```
用户输入搜索关键词 q + 选择标签过滤
  │
  ├─> [路径 1] 标签过滤 (前置条件)
  │     通过 agent_tag 关联表过滤候选集
  │
  ├─> [路径 2] 向量搜索
  │     q → 生成 embedding → cosine_distance 排序
  │
  └─> [路径 3] 关键词搜索
        q → ILIKE 匹配 name + system_prompt
  │
  └─> RRF 融合路径 2 + 路径 3 的结果
        └─> (可选) Reranking
              └─> 附加匹配状态 → 返回结果
```

### 路径 1: 标签过滤 (Tag Filtering)

- 用户在 UI 选择一个或多个标签 → 后端通过 `agent_tag` 关联表过滤
- 多选逻辑: OR（包含任一选中标签即匹配）
- 标签过滤作为前置条件，缩小后续搜索的候选集
- 未选择任何标签时返回全部

### 路径 2: 向量搜索 (Embedding Search)

- 将搜索关键词 `q` 生成 embedding（使用平台 embedding 模型）
- 用 pgvector `cosine_distance` 计算与所有候选 Agent 的相似度
- 返回 top-K 结果（K=50）
- Dev 模式: Python 内存 cosine similarity

### 路径 3: 关键词搜索 (Keyword Search)

- 在 `Agent.name` 和 `Agent.system_prompt` 上执行关键词匹配
- Prod 模式: PostgreSQL `ILIKE` 或 `tsvector`
- Dev 模式: Python 内存子串匹配
- 返回 top-K 结果（K=50）

### 融合策略: Reciprocal Rank Fusion (RRF)

当 `q` 非空时，同时执行向量搜索和关键词搜索，使用 RRF 合并:

```
RRF_score(agent) = Σ 1/(k + rank_i)  对每条搜索路径 i
```

- `k = 60`（标准 RRF 常数）
- 按 RRF_score 降序排列
- 仅出现在一条路径中的 Agent 也参与排名（另一路径 rank 视为无穷大，贡献为 0）

### Reranking (可选增强)

- Dev 模式: 跳过，直接使用 RRF 分数
- Prod 模式: 可选调用平台 LLM 做 cross-encoder 式 reranking
  - 输入: (query, agent.system_prompt) pairs (取 top-20)
  - 输出: 0-1 relevance score
  - 按 score 重排

### 无 q 时的行为

当用户仅选择标签过滤而未输入搜索关键词:
- 跳过向量搜索和关键词搜索
- 仅按标签过滤，结果按创建时间或默认排序

### Dev vs Prod 实现差异

| 维度 | Dev 模式 | Prod 模式 |
|------|----------|-----------|
| 标签存储 (系统) | `storage/seed/` JSON 文件 (只读) | PostgreSQL 系统表 (迁移初始化) |
| Agent-Tag 关联 (用户) | `storage/dev/agent_tags.json` (读写) | PostgreSQL 业务表 |
| 向量搜索 | Python 内存 cosine similarity | pgvector `<=>` |
| 关键词搜索 | Python substring match | PostgreSQL `ILIKE` |
| RRF 融合 | Python 内存 | Python 内存 |
| Reranking | 跳过 | 可选 LLM rerank |

---

## 三、匹配状态 (Match Status)

### 业务场景

用户在 Plaza 浏览 Agent 时，需要知道某个 Agent 是否已经和自己的某个 Agent 交互过，以及交互结果如何。

### 四种状态

| 状态 | 枚举值 | 含义 |
|------|--------|------|
| 达成一致 | `CONSENSUS` | 我方某 Agent 与此 Agent 的 Session 已 COMPLETED 且 Judge 判定 CONSENSUS |
| 聊天中 | `CHATTING` | 我方某 Agent 与此 Agent 有 ACTIVE/JUDGING 状态的 Session |
| 未达成一致 | `DEADLOCK` | 所有相关 Session 均为 TERMINATED 或 DEADLOCK |
| 未匹配 | `NOT_MATCHED` | 我方所有 Agent 与此 Agent 之间无任何 Session 记录 |

### 优先级

当同一 Plaza Agent 与我方多个 Agent 存在不同状态时，取最高优先级:

`CONSENSUS > CHATTING > DEADLOCK > NOT_MATCHED`

### 计算方式

查询时计算（非存储字段）:

1. 获取当前用户所有 Agent ID 列表
2. 查询所有涉及这些 Agent 的 Session
3. 对每个 Plaza Agent，检查是否有关联的 Session
4. 根据 Session 状态和 MatchResult 判定匹配状态
5. 同时返回具体的配对详情列表

### 匹配详情 (Match Details)

除聚合状态外，返回每对 Agent 的具体交互详情:

| 字段 | 类型 | 说明 |
|------|------|------|
| `my_agent_id` | UUID | 我方 Agent ID |
| `my_agent_name` | String | 我方 Agent 名称 |
| `session_id` | UUID | Session ID |
| `status` | String | 此 Session 对应的匹配状态 |
| `created_at` | Datetime | Session 创建时间 |

---

## 四、API 设计

新增独立 Plaza 路由 `/plaza/`。现有 `/agents/plaza` 保留向后兼容。

### GET /plaza/tags

返回标签目录，按分类分组。

**响应:**

```json
[
  {
    "id": "uuid",
    "name": "意图",
    "slug": "intent",
    "tags": [
      { "id": "uuid", "name": "交友", "slug": "dating" },
      { "id": "uuid", "name": "买卖", "slug": "trading" }
    ]
  }
]
```

### POST /plaza/tags

在指定分类下创建**用户自定义标签**（`is_user_defined=true`）。创建成功后异步写入 `embedding`（标签名称作为输入文本）。若同名 slug 已存在则返回已有标签。

### POST /plaza/tags/embed

批量为标签生成/刷新 `embedding`（调用本地 Embedding 服务）。

| 参数（Body JSON） | 类型 | 说明 |
|------------------|------|------|
| `force_all` | Boolean | 默认 `false`：仅处理 `embedding` 为空的标签；`true`：重算所有活跃标签 |

### GET /plaza/search

混合搜索，返回 Agent 列表 + 匹配状态。

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | UUID | 是 | 当前用户 ID，排除自己 + 计算匹配状态 |
| `tag_ids` | String | 否 | 逗号分隔的 tag UUID，按标签过滤 |
| `q` | String | 否 | 搜索关键词，触发混合搜索 |
| `page` | Integer | 否 | 页码，默认 1 |
| `page_size` | Integer | 否 | 每页数量，默认 20 |

**响应:**

```json
{
  "total": 42,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "name": "AI 技术顾问",
      "tags": [
        { "id": "uuid", "name": "技术交流", "category": "意图" },
        { "id": "uuid", "name": "科技", "category": "领域" }
      ],
      "opening_remark": "你好，我是...",
      "match_status": "CHATTING",
      "match_details": [
        {
          "my_agent_id": "uuid",
          "my_agent_name": "我的买手 Agent",
          "session_id": "uuid",
          "status": "CHATTING",
          "created_at": "2026-03-10T12:00:00"
        }
      ],
      "search_score": 0.85
    }
  ]
}
```

---

## 五、设计决策

- **Agent/Product 标签通过 scope 彻底分离**: `tag_category.scope` 从数据层面隔离两套标签体系。Agent 侧允许用户扩展自定义标签；Product 侧仅使用平台预置标签，无交叉同步。
- **保留 Agent.tags 缓存字段**: 反规范化设计，避免每次读取都需要 JOIN 查询，同时保持向后兼容。
- **RRF 融合而非简单加权**: RRF 对不同量纲的分数天然免疫，无需人工调参。
- **匹配状态查询时计算**: 不存储冗余字段，直接从 Session 和 MatchResult 推导，避免数据不一致。
- **Plaza 独立路由**: 随着功能复杂度增长，独立于 Agent CRUD 路由，职责更清晰。
- **Dev/Prod 统一接口**: Repository 层抽象使搜索逻辑在 JSON 和 PostgreSQL 间无缝切换。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/models/tag.py` | TagCategory, Tag, AgentTag 数据模型 |
| `backend/app/schemas/plaza.py` | Plaza 搜索请求/响应 Schema |
| `backend/app/api/plaza.py` | Plaza API 路由 |
| `backend/app/services/plaza_service.py` | 混合搜索 + 匹配状态计算 |
| `backend/app/agent/persona.py` | Tag 提取逻辑（从目录选取） |
| `frontend/app/plaza/page.tsx` | Plaza 页面实现 |
