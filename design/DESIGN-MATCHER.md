# 撮合引擎 (Matcher Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

后台异步服务，负责发现潜在的匹配对象。从 MATCHING 状态的 Agent 池中进行向量匹配、去重校验、LLM 验证，最终创建会话。

## 核心功能

### `scan_and_match(threshold)`

执行完整的匹配流程:

1. **遍历候选**: 获取状态为 `MATCHING` 的 Agent (PAIRED/DONE/IDLE 不参与)。
2. **向量匹配**: 计算 Agent `embedding` 的 Cosine Distance，筛选低于阈值的候选对。
3. **去重检查**: 查询所有已有 Session，跳过已配对过的 Agent 对 (无论 Session 状态)。
4. **LLM 验证** (可选，dev 模式默认开启): 调用 `check_match_with_llm()` 对 system_prompt 进行语义兼容性判定。
   - 验证通过 → 继续创建 Session。
   - **验证拒绝 → 创建 TERMINATED Session 作为标记**，防止下次循环重复尝试同一对。
5. **会话初始化**: 创建 Session (状态 ACTIVE)。
6. **标记 Agent**: 双方 Agent 状态从 `MATCHING` 更新为 `PAIRED`。
7. **注入开场白**: 将双方 `opening_remark` 作为初始消息写入会话。

## 去重机制

所有匹配尝试（成功、进行中、失败、LLM 拒绝）都会留下 Session 记录。Matcher 在每轮扫描时检查 Session 表，确保任意两个 Agent 之间最多只有一次匹配尝试。

## Dev 模式适配

| 维度 | Dev 模式 | Prod 模式 |
|------|----------|-----------|
| Embedding | Mock 随机向量 | OpenAI `text-embedding-ada-002` |
| 匹配阈值 | 2.0 (放宽) | 0.2 (严格 Cosine Distance) |
| LLM 验证 | 默认开启，保证匹配质量 | 可选 |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/services/matcher_service.py` | 撮合逻辑实现 |
| `backend/app/services/orchestrator.py` | 编排器中调用 Matcher |
