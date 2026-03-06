# 用户模块 (User Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

负责存储用户基础信息、认证数据与账户层级。用户是 Agent 的所有者，一个用户可拥有多个不同任务的 Agent。

## 字段 (Fields)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `username` | String | 唯一，用于登录 |
| `password_hash` | String | 密码哈希 |
| `tier` | Enum | 账户层级: `FREE` / `PAID` |
| `contact` | String (可选) | 联系方式，仅在 CONSENSUS 后向对方展示 |
| `llm_config` | JSON (可选) | 免费用户自行配置的 LLM 接入信息 (见下方) |

## 账户层级 (Tier)

| 层级 | Agent 人设 | Agent 对话 | Skills | 平台服务 (tags/embedding/judge) |
|------|-----------|-----------|--------|-------------------------------|
| `FREE` | 用户手动编写 system_prompt + opening_remark | 用户自带 API Key 驱动 | 不可用 | 平台免费提供 |
| `PAID` | 平台 LLM 自动生成 | 平台 LLM 驱动 | 可配置 | 平台提供 |

### 免费用户 LLM 配置 (`llm_config`)

免费用户需在账户中配置自己的 LLM 接入信息，用于 Agent 对话生成:

```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini"
}
```

> **安全**: `api_key` 加密存储，仅用于该用户 Agent 的对话生成，平台不作它用。

## 核心功能 (Functions)

- `register(username, password)`: 注册用户，默认 `tier=FREE`。
- `login(username, password)`: 登录认证，返回用户信息 (含 tier)。
- `update_llm_config(user_id, llm_config)`: 免费用户配置自己的 LLM 接入信息。
- `upgrade_tier(user_id)`: 升级为付费用户。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/models/user.py` | User 数据模型 (SQLModel) |
| `backend/app/schemas/user.py` | UserCreate, UserLogin, UserRead |
| `backend/app/api/auth.py` | 注册/登录路由 |
| `backend/app/services/user_service.py` | 用户注册/认证业务逻辑 |
