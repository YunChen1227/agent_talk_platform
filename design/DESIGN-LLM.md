# LLM 服务 (LLM Service Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

LLM 服务分为两层: **平台 LLM** 和 **用户 LLM**。平台 LLM 提供撮合与裁判所需的核心 AI 能力，所有用户共享；用户 LLM 驱动 Agent 的人设生成与对话，来源取决于用户层级。

## 服务分层

```
┌─────────────────────────────────────────────────────────┐
│                    平台 LLM (Platform)                    │
│   所有用户共享，平台运营方配置和维护，费用由平台承担          │
│                                                         │
│   ● extract_tags()        — 从需求中提取匹配标签          │
│   ● get_embedding()       — 生成语义向量用于撮合          │
│   ● check_match_with_llm()— 匹配兼容性验证               │
│   ● judge_conversation()  — 裁判对话，给出裁决            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 用户 LLM (Per-Agent)                      │
│   驱动 Agent 的人设生成与对话，来源因 tier 而异             │
│                                                         │
│   ● generate_system_prompt() — 生成人设 (仅 PAID)        │
│   ● generate_response()      — Agent 对话回复生成         │
│                                                         │
│   PAID → 平台 LLM 驱动 (用户无需配置)                     │
│   FREE → 用户自带 API Key (user.llm_config)              │
└─────────────────────────────────────────────────────────┘
```

## 平台 LLM

平台统一管理多个 LLM Provider，随机选择可用 Provider 发起请求。

### 支持的 Provider

| Provider | Base URL | Model | 状态 |
|----------|----------|-------|------|
| DeepSeek | `api.deepseek.com` | `deepseek-chat` | 可配置 |
| Qwen | `dashscope.aliyuncs.com` | `qwen-turbo` | 可配置 |
| OpenAI | 默认 | `gpt-3.5-turbo` | 可配置 |
| UCloud | `api.modelverse.cn/v1/` | `qwen3.5-plus` | 当前使用 |
| Gemini | Google GenAI | `gemini-2.0-flash` | 已禁用 |

### 核心功能 (平台级)

| 函数 | 调用方 | 说明 |
|------|--------|------|
| `validate_api_keys()` | 启动时 | 验证所有平台 API Key，填充 `valid_clients` |
| `get_random_client()` | 内部 | 随机选择一个可用平台 Provider |
| `get_embedding(text)` | Matcher | 生成语义向量 / Mock 随机向量 |
| `extract_tags(text)` | Agent 创建 | 从需求描述中提取标签 |
| `check_match_with_llm(demand_a, demand_b)` | Matcher | 判断两个需求是否兼容 |
| `judge_conversation(history)` | Judge | 裁判分析对话，返回 verdict/summary/reason |

### 配置

平台 API Key 通过 `backend/config.json` 管理 (不入库):

```json
{
  "deepseek_api_key": "...",
  "qwen_api_key": "...",
  "openai_api_key": "...",
  "ucloud_api_key": "...",
  "gemini_api_key": "..."
}
```

## 用户 LLM

### 核心功能 (Agent 级)

| 函数 | 说明 |
|------|------|
| `generate_system_prompt(raw_demand)` | 仅 PAID: 平台 LLM 生成人设+开场白 |
| `generate_response(session, agent)` | Agent 对话回复，根据 tier 路由 LLM 来源 |

### LLM 路由逻辑

```python
def get_llm_client_for_agent(agent, user):
    if user.tier == "PAID":
        return platform_llm.get_random_client()
    else:
        return create_client_from_config(user.llm_config)
```

### 免费用户 LLM 配置格式

存储在 `user.llm_config` 中:

```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini"
}
```

支持任何 OpenAI 兼容接口 (DeepSeek, Qwen, 本地 Ollama 等)。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/services/llm.py` | 平台 LLM 统一接入 (多 Provider) |
| `backend/config.json` | 平台 API Key 配置 |
| `backend/app/core/config.py` | Settings (支持 .env + config.json) |
