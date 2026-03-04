# AgentMatch Platform - 核心设计方案 (Core Design)

基于 `README.md` 的理解，以下是精简后的模块、字段与核心功能设计。设计原则为**最小化字段**与**原子化功能**，确保系统轻量且高效。

## 1. 模块定义 (Modules)

### 1.1 用户与画像 (User & Profile)
负责存储用户基础信息及用于匹配的核心数据。

**字段 (Fields):**
- `id`: UUID (主键)
- `contact`: String (联系方式，仅在达成一致后展示)
- `raw_demand`: Text (用户输入的原始需求描述)
- `tags`: List[String] (LLM 提取的关键标签，用于硬过滤，如行业、城市)
- `embedding`: Vector (基于需求生成的向量，用于语义匹配)

**核心功能 (Functions):**
- `create_profile(input_data)`: 创建用户 -> 调用 LLM 提取标签 -> 生成向量。
- `update_demand(text)`: 更新需求 -> 重新生成标签与向量。

---

### 1.2 代理 (Agent)
代表用户进行自动交涉的虚拟实体。

**字段 (Fields):**
- `id`: UUID (主键)
- `user_id`: UUID (关联用户)
- `name`: String (代理对外展示的名称)
- `system_prompt`: Text (基于用户需求生成的系统指令，包含人设与谈判策略)
- `status`: Enum (IDLE-闲置, MATCHING-匹配中, BUSY-交涉中)

**核心功能 (Functions):**
- `initialize(user_profile)`: 根据用户画像生成 `system_prompt`。
- `set_status(new_status)`: 状态流转控制。

---

### 1.3 撮合引擎 (Matcher)
后台异步服务，负责发现潜在的匹配对象。

**字段 (Fields):**
- *无持久化字段，主要操作 Redis/VectorDB*

**核心功能 (Functions):**
- `scan_pool()`: 遍历状态为 `MATCHING` 的 Agent。
- `find_candidates(agent_id)`: 
    1. **硬过滤**: 匹配 `tags` (可选)。
    2. **软匹配**: 计算 `embedding` 相似度 (Cosine Similarity)。
    3. **阈值判定**: 相似度 > Threshold 则触发会话。

---

### 1.4 会话沙盒 (Chat Session)
两个 Agent 进行交互的封闭环境。

**字段 (Fields):**
- `id`: UUID (主键)
- `agent_a_id`: UUID
- `agent_b_id`: UUID
- `status`: Enum (ACTIVE, COMPLETED, TERMINATED)
- `created_at`: Timestamp

**子模块: 消息 (Message)**
- `session_id`: UUID
- `sender_id`: UUID (发送方 Agent)
- `content`: Text (消息内容)
- `timestamp`: Timestamp

**核心功能 (Functions):**
- `start_session(agent_a, agent_b)`: 创建 Session。
- `post_message(session_id, sender, content)`: 写入消息记录。
- `get_history(session_id)`: 获取上下文用于 LLM 推理。

---

### 1.5 裁判系统 (Judge)
旁观者 AI，负责监控与裁决。

**字段 (Fields):**
- `session_id`: UUID (关联会话)
- `verdict`: Enum (CONSENSUS-达成一致, DEADLOCK-僵局, PENDING-进行中)
- `summary`: Text (对话摘要/结论)
- `reason`: Text (裁决理由)

**核心功能 (Functions):**
- `audit_conversation(history)`: 分析最新对话，判断是否结束。
- `finalize_result(session_id, verdict)`: 
    1. 生成摘要 `summary`。
    2. 更新 Session 状态。
    3. (可选) 更新 Session 状态。
    4. 若 `CONSENSUS`，触发用户通知。

## 2. 数据流转逻辑 (Data Flow)

1.  **User** 提交需求 -> 生成 **Profile** (Tags/Embedding) -> 初始化 **Agent**。
2.  **Matcher** 扫描 Agent -> 向量检索发现高匹配度对象 -> 创建 **Session**。
3.  **Agent A** & **Agent B** 在 **Session** 中轮流发言 (基于 `system_prompt` + `history`)。
4.  **Judge** 每轮对话后介入 -> 评估意图 -> 若达成 **CONSENSUS** -> 生成摘要 -> 通知 **User**。
