# AgentMatch Platform - 核心设计方案 (Core Design)

基于 `README.md` 的理解，以下是平台的整体架构与业务逻辑设计。各模块的详细字段、函数与实现细节请参阅对应的子文档。

## 1. 平台简介

AgentMatch 是一个 AI Agent 自动交涉撮合平台。用户创建代表自己的 Agent，系统自动寻找匹配对手，Agent 之间进行自主对话谈判，裁判 AI 实时评估对话结果，最终促成供需双方的对接。

**设计原则**: **最小化字段**与**原子化功能**，确保系统轻量且高效。

### 用户层级 (Tier)

平台采用 FREE / PAID 双层级模型:

| 能力 | FREE (免费) | PAID (付费) |
|------|------------|------------|
| 平台撮合服务 (tags/embedding/judge) | 平台提供 | 平台提供 |
| Agent 人设生成 | 用户手动编写 | 平台 LLM 自动生成 |
| Agent 对话驱动 | 用户自带 API Key | 平台 LLM 驱动 |
| Skills 技能扩展 | 不可用 | 可配置 |

> **核心原则**: 平台始终免费提供 **标签提取**、**Embedding 生成**、**匹配验证** 和 **Judge 裁判** 服务，这是平台撮合能力的基础。用户层级仅影响 Agent 的创建方式和对话能力。

## 2. 模块总览

| 模块 | 职责 | 详细文档 |
|------|------|----------|
| 用户 (User) | 用户注册、登录、认证 | [DESIGN-USER.md](./DESIGN-USER.md) |
| 代理 (Agent) | Agent 创建、人设生成、对话、状态管理 | [DESIGN-AGENT.md](./DESIGN-AGENT.md) |
| 撮合引擎 (Matcher) | 向量匹配、去重、LLM 验证、配对 | [DESIGN-MATCHER.md](./DESIGN-MATCHER.md) |
| 会话沙盒 (Session) | 对话环境、消息存储、状态锁 | [DESIGN-SESSION.md](./DESIGN-SESSION.md) |
| 裁判系统 (Judge) | 对话评估、裁决 (CONSENSUS/DEADLOCK) | [DESIGN-JUDGE.md](./DESIGN-JUDGE.md) |
| 编排器 (Orchestrator) | 后台循环调度 (Matcher → Agent → Judge) | [DESIGN-ORCHESTRATOR.md](./DESIGN-ORCHESTRATOR.md) |
| LLM 服务 (LLM Service) | 多 Provider 统一接入、AI 能力封装 | [DESIGN-LLM.md](./DESIGN-LLM.md) |
| API 接口 (Endpoints) | RESTful API 定义 | [DESIGN-API.md](./DESIGN-API.md) |
| 前端 (Frontend) | Next.js 页面、交互、轮询 | [DESIGN-FRONTEND.md](./DESIGN-FRONTEND.md) |

## 3. 核心业务逻辑 (Business Flow)

### 3.1 完整用户旅程

```
1. 用户注册/登录 (默认 FREE)

2. 创建 Agent (因 tier 而异):
   [PAID] 输入需求描述 → 平台 LLM 自动生成人设+开场白 → 平台提取 tags + embedding → 可配置 Skills
   [FREE] 手动编写人设+开场白+需求摘要 → 平台提取 tags + embedding → 无 Skills

3. (FREE 用户) 配置自己的 LLM API Key (用于 Agent 对话)

4. 点击 Match → Agent 进入匹配池 (IDLE → MATCHING)
   - FREE 用户需已配置 llm_config，否则拒绝
   - MATCHING 状态下 Agent 可同时与多个不同对手并行会话

5. 后台 Orchestrator 自动驱动:
   a. Matcher 发现配对 → 创建 Session (Agent 保持 MATCHING，可继续匹配新对手)
   b. Agent A/B 轮流自动对话 (PAID 走平台 LLM / FREE 走用户 API Key)
   c. Judge 每轮评估对话 (始终走平台 LLM)

6. 对话进行中，用户可:
   - 在 Active Sessions 面板实时查看对话内容与 Judge 评估
   - 手动 Terminate 终止对话 → 直接标记 DEADLOCK

7. 裁判出结果 (或用户手动终止):
   - CONSENSUS → 对话成功，双方进入联系方式授权阶段
     - 用户需主动确认"是否展示我的联系方式给对方"
     - 仅当某一方确认授权后，对方才能看到该方联系方式
   - DEADLOCK → 对话失败 (裁判判定 或 用户手动终止)，可重新匹配

8. 用户可在 Completed Sessions 面板查看历史结果；如需停止继续匹配，可手动 Stop Matching
```

### 3.2 数据流转

```
User 注册/登录
  └─> 创建 Agent
       ├─ [PAID] 输入 raw_demand → 平台 LLM 生成 system_prompt + opening_remark
       ├─ [FREE] 用户手动填写 system_prompt + opening_remark + demand_summary
       └─ [共同] 平台 LLM 提取 tags + 平台生成 embedding
            └─> 用户点击 Match -> Agent 状态: IDLE -> MATCHING
                 └─> [Orchestrator 后台循环]
                      ├─> Matcher (平台 LLM) 发现配对 -> 创建 Session (ACTIVE)
                      │    └─> Agent 保持 MATCHING，可继续配对更多不同 Agent
                      ├─> Agent A/B 轮流对话 (PAID: 平台 LLM / FREE: 用户 API Key)
                      ├─> 用户可在 Active Sessions 面板实时查看对话 + Judge 信息
                      ├─> 用户手动 Terminate -> Session: TERMINATED + MatchResult(DEADLOCK)
                      └─> Judge (平台 LLM) 审议
                           ├─> Session: ACTIVE -> JUDGING (Agent 暂停发言)
                           ├─> PENDING -> Session 回退 ACTIVE -> 继续对话
                           └─> CONSENSUS / DEADLOCK
                                ├─> Session: COMPLETED / TERMINATED
                                ├─> 创建 MatchResult 记录
                                └─> 前端轮询刷新 Completed Sessions
                                     └─> 用户查看对话详情 + 裁判结果
                                          └─> 用户可选择是否授权展示自己的联系方式
                                               └─> 仅展示已授权方的联系方式
```

### 3.3 状态机总览

**Agent 状态:**

```
IDLE ──(Start Match)──> MATCHING
  ▲                       │
  └──────(Stop Match)─────┘

MATCHING 状态下可并行参与多个 Session：
- 可被 Matcher 持续匹配到新对手
- 与同一个对手同一时刻仅允许一个 ACTIVE/JUDGING Session
```

**Session 状态:**

```
                                    ┌──(CONSENSUS)──> COMPLETED
ACTIVE ──(Judge 介入)──> JUDGING ──┤
  │                         │       └──(DEADLOCK)───> TERMINATED
  │                         └──(PENDING)──> ACTIVE (回退)
  │
  └──(用户手动 Terminate)──> TERMINATED (标记 DEADLOCK)
```

## 4. 整体架构

### 4.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 14)                        │
│                   轮询 (5s) ← REST API → Backend                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                        Backend (FastAPI)                             │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │   Auth   │  │  Agents  │  │ Sessions │  │   System Status  │   │
│  │   API    │  │   API    │  │   API    │  │      API         │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       │              │              │                  │             │
│  ┌────▼──────────────▼──────────────▼──────────────────▼─────────┐  │
│  │                    Services Layer                              │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐                 │  │
│  │  │ User Svc   │ │  Matcher   │ │   Judge    │                 │  │
│  │  └────────────┘ └────────────┘ └────────────┘                 │  │
│  │                         ↑                                     │  │
│  │                   Orchestrator (每 5s 循环)                    │  │
│  └──────────────────────────┬────────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼───────────────────────────────────┐  │
│  │                      LLM Layer                                │  │
│  │  ┌─────────────────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Platform LLM (平台级)       │  │  User LLM (Agent 级)   │  │  │
│  │  │ tags / embedding / judge    │  │  PAID: 平台 LLM        │  │  │
│  │  │ match verification          │  │  FREE: 用户 API Key    │  │  │
│  │  └─────────────────────────────┘  └────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   Repository Layer                             │  │
│  │            Dev: JSON 文件  │  Prod: PostgreSQL + pgvector      │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 目录结构

```text
agent_talk_platform/
├── design/                        # 设计文档目录
│   ├── DESIGN.md                  # 本文档 (总览)
│   ├── DESIGN-USER.md             # 用户模块设计
│   ├── DESIGN-AGENT.md            # 代理模块设计
│   ├── DESIGN-MATCHER.md          # 撮合引擎设计
│   ├── DESIGN-SESSION.md          # 会话沙盒设计
│   ├── DESIGN-JUDGE.md            # 裁判系统设计
│   ├── DESIGN-ORCHESTRATOR.md     # 编排器设计
│   ├── DESIGN-LLM.md             # LLM 服务设计
│   ├── DESIGN-API.md             # API 接口设计
│   └── DESIGN-FRONTEND.md        # 前端页面设计
├── README.md
├── .gitignore
│
├── backend/
│   ├── main.py                    # FastAPI 入口，Lifespan 启动逻辑
│   ├── run.py                     # 启动脚本 (--mode dev/prod --reload)
│   ├── requirements.txt
│   ├── config/                    # ── 配置中心 (统一管理) ──
│   │   ├── .env                   # 环境变量 (MODE, DB 连接等)
│   │   ├── .env.example           # 环境变量模板 (入库)
│   │   ├── secrets.json           # 平台 API Keys (不入库)
│   │   └── secrets.example.json   # API Keys 模板 (入库)
│   ├── storage/                   # ── 持久化存储 ──
│   │   └── dev/                   # Dev 模式 JSON 数据
│   │       ├── users.json
│   │       ├── agents.json
│   │       ├── sessions.json
│   │       ├── messages.json
│   │       └── matchresults.json
│   ├── app/
│   │   ├── agent/                 # Agent 核心模块
│   │   ├── api/                   # 接口路由
│   │   ├── core/                  # 配置、数据库、依赖注入
│   │   ├── models/                # 数据模型 (SQLModel)
│   │   ├── repositories/          # 数据访问层 (Repository Pattern)
│   │   ├── schemas/               # Pydantic 请求/响应模式
│   │   └── services/              # 业务逻辑层
│
└── frontend/                      # Next.js 14 + Tailwind CSS
    ├── app/                       # 页面路由
    ├── lib/                       # API 封装
    ├── package.json
    └── tsconfig.json
```

## 5. 双模式架构 (Dev / Prod)

| 维度 | Dev 模式 | Prod 模式 |
|------|----------|-----------|
| 数据存储 | JSON 文件 (`storage/dev/*.json`) | PostgreSQL + pgvector |
| 配置管理 | `config/.env` + `config/secrets.json` | 同左 |
| Embedding | Mock 随机向量 | OpenAI `text-embedding-ada-002` |
| 匹配阈值 | 2.0 (放宽) + LLM 验证 | 0.2 (严格 Cosine Distance) |
| 切换方式 | `--mode dev` | `--mode prod` (需配置 DB) |

### 配置管理规范

```
backend/config/                    # 所有配置统一在此管理
├── .env                           # 环境变量 (MODE, DB 等运行时参数)
├── .env.example                   # 环境变量模板 (入库，供新成员参考)
├── secrets.json                   # 平台 API Keys (不入库，.gitignore)
└── secrets.example.json           # API Keys 模板 (入库，仅含空值字段名)

backend/storage/                   # 所有持久化数据统一在此管理
└── dev/                           # Dev 模式 JSON 文件存储
    ├── users.json
    ├── agents.json
    ├── sessions.json
    ├── messages.json
    └── matchresults.json
```

- **配置与代码分离**: 所有配置集中在 `config/`，不散落在项目根目录。
- **敏感信息隔离**: `secrets.json` 存储 API Keys，通过 `.gitignore` 防止泄露；`secrets.example.json` 入库作为模板。
- **存储路径可寻址**: `config.py` 通过 `BASE_DIR / "config"` 和 `BASE_DIR / "storage"` 构建绝对路径，不依赖工作目录。

## 6. 关键设计决策

- **LLM 服务分层**: 平台 LLM (tags/embedding/judge/match) 始终由平台提供，Agent 对话 LLM 根据用户 tier 路由 (PAID→平台 / FREE→用户自带)。
- **FREE/PAID 双轨制**: 免费用户自带 API Key + 手写人设，付费用户享受平台全套 LLM 服务 + Skills 扩展。
- **去重保证**: 聊过天的两个 Agent 不会再次配对，所有匹配尝试通过 Session 记录追踪。
- **JUDGING 锁**: 裁判审议期间 Session 加锁，防止产生新消息导致不一致。
- **启动恢复**: 服务重启时自动恢复卡在 JUDGING 的 Session，防止死锁。
- **tags/embedding 归属 Agent**: 同一用户可有多个 Agent，各自独立匹配画像。
- **Repository Pattern**: 数据访问层抽象，Dev/Prod 无缝切换。
