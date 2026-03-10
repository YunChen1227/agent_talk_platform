# 用户模块 (User Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

负责存储用户基础信息、认证数据与账户层级。用户是 Agent 的所有者，一个用户可拥有多个不同任务的 Agent。页面与交互设计参见 [DESIGN-FRONTEND.md](./DESIGN-FRONTEND.md)。

## 字段 (Fields)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `username` | String | 唯一，用于登录 |
| `password_hash` | String | 密码哈希 |
| `tier` | Enum | 账户层级: `FREE` / `PAID` |
| `contact` | String (可选) | 联系方式，仅在 CONSENSUS 后向对方展示 |
| `avatar_url` | String (可选) | 用户头像图片 URL，由用户上传后设置 |
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

## 用户媒体 (User Media)

用户可上传照片、视频到自己的界面，并设置一张照片作为头像。在交友等场景下，Agent 可在对话中发送用户上传的媒体给对方。

### UserMedia 模型

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `user_id` | UUID | 所属用户 |
| `file_type` | Enum | `image` / `video` |
| `url` | String | 访问 URL (Dev: 本地路径; Prod: 云存储 URL) |
| `thumbnail_url` | String (可选) | 缩略图 URL，视频可选 |
| `original_filename` | String | 原始文件名 |
| `created_at` | Timestamp | 上传时间 |

### 存储模式

| 模式 | 文件存储 | 说明 |
|------|----------|------|
| Dev | `backend/storage/uploads/` + `storage/dev/media.json` | 本地文件 + 元数据 JSON |
| Prod | 云存储 (S3/MinIO 等) | 元数据存 DB，文件存对象存储 |

### 上传限制

- 单文件大小、总数量、允许格式 (如 image/jpeg, image/png, video/mp4) 由配置或策略限定。
- 头像为特殊用例：用户可选一张已上传的图片设为头像，对应 User 的 `avatar_url`。

### 媒体相关功能

- `upload_media(user_id, file)`: 上传照片或视频，返回 UserMedia 记录。
- `delete_media(media_id, user_id)`: 删除媒体 (校验归属)。
- `list_media(user_id)`: 列出该用户所有媒体。
- `set_avatar(user_id, media_id)`: 将指定媒体设为头像，更新 User.avatar_url。

## 核心功能 (Functions)

- `register(username, password)`: 注册用户，默认 `tier=FREE`。
- `login(username, password)`: 登录认证，返回用户信息 (含 tier)。
- `update_llm_config(user_id, llm_config)`: 免费用户配置自己的 LLM 接入信息。
- `upgrade_tier(user_id)`: 升级为付费用户。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/models/user.py` | User 数据模型 (SQLModel) |
| `backend/app/models/media.py` | UserMedia 数据模型 |
| `backend/app/schemas/user.py` | UserCreate, UserLogin, UserRead |
| `backend/app/schemas/media.py` | Media 请求/响应模式 |
| `backend/app/api/auth.py` | 注册/登录路由 |
| `backend/app/api/media.py` | 媒体上传/列表/删除/头像路由 |
| `backend/app/services/user_service.py` | 用户注册/认证业务逻辑 |
| `backend/app/services/media_service.py` | 媒体上传与存储逻辑 |
