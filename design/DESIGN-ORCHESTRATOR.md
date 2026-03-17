# 编排器 (Orchestrator Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

后台循环任务，每 5 秒执行一轮，统一调度所有模块。是系统的"心跳"，驱动匹配、对话、裁判三大流程。

## 技术框架

| 技术 | 用途 |
|------|------|
| **Python asyncio** | `asyncio.create_task()` 启动后台循环，`asyncio.sleep(5)` 控制调度间隔 |
| **FastAPI lifespan** | `@asynccontextmanager` 管理应用启动/关闭生命周期，启动时恢复卡住的 Session |
| **Repository Pattern** | 依赖注入 Matcher / Session / Agent / Message / MatchResult / Product Repository |

## 执行流程 (`run_orchestrator`)

每轮循环按顺序执行:

1. **Matcher 阶段**: 调用 `scan_and_match()`，发现并创建新配对（不修改 Agent 状态）。
2. **对话阶段**: 遍历所有 ACTIVE Session，为每个 Session 调用 `process_turn()` 让当前 Agent 发言。
3. **裁判阶段**: 对同一 Session 调用 `audit_session()` 评估对话是否结束。

> **状态解耦**: Orchestrator 仅驱动 Session 流程。Agent 处于 MATCHING 时可并行参与多个 Session，Session 结束不会将 Agent 强制置为 DONE。

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator 循环 (每 5s)                  │
│                                                             │
│  1. Matcher ──> 2. Agent 对话 ──> 3. Judge 裁判 ──> 等待 5s  │
│       │              │                  │                    │
│       ▼              ▼                  ▼                    │
│  发现新配对     轮流发言生成       审议对话结果                │
└─────────────────────────────────────────────────────────────┘
```

## 启动恢复 (Lifespan)

- 服务启动时验证所有 API Key。
- 重置卡在 JUDGING 状态的 Session 回 ACTIVE (防止上次崩溃导致的死锁)。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/services/orchestrator.py` | 编排器主循环实现 |
| `backend/main.py` | FastAPI 入口，Lifespan 启动逻辑 |
