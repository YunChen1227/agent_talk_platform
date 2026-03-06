# 编排器 (Orchestrator Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

后台循环任务，每 5 秒执行一轮，统一调度所有模块。是系统的"心跳"，驱动匹配、对话、裁判三大流程。

## 执行流程 (`run_orchestrator`)

每轮循环按顺序执行:

1. **Matcher 阶段**: 调用 `scan_and_match()`，发现并创建新配对。
2. **对话阶段**: 遍历所有 ACTIVE Session，为每个 Session 调用 `process_turn()` 让当前 Agent 发言。
3. **裁判阶段**: 对同一 Session 调用 `audit_session()` 评估对话是否结束。

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
