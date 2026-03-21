# 用户资料/媒体页 (`/profile`)

> 返回 [前端总览](./DESIGN-FRONTEND.md) | [主设计文档](./DESIGN.md)

## 概述

用户个人资料页，管理个人信息（昵称、性别、生日、地址、职业、简介、性格、爱好等）、头像与媒体库（照片/视频）、Agent 标签偏好（喜欢/不喜欢），并提供进入 "My Shop" 的入口卡片。

## 技术框架

Next.js 14 (App Router) · React 18 `useState`/`useEffect`/`useCallback` · Axios · Tailwind CSS 网格布局

## 页面布局

```
┌──────────────────────────────────────────────────────────┐
│  Profile                              [Back to Dashboard] │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  [Avatar]  Display Name                           │    │
│  │            @username                              │    │
│  │            Bio text here...                       │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  基本信息                                         │    │
│  │  昵称: [input]         性别: [select]             │    │
│  │  生日: [date]          所在地: [input]            │    │
│  │  职业: [input]         个人网站: [input]          │    │
│  │  个人简介: [textarea]                             │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  性格 & 兴趣                                      │    │
│  │  性格标签: [tag] [tag] [+ Add input]              │    │
│  │  兴趣爱好: [tag] [tag] [+ Add input]              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│                              [保存个人信息]               │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Agent 标签偏好                                    │    │
│  │  提示: 点击切换 喜欢 → 不喜欢 → 中立              │    │
│  │                                                   │    │
│  │  意图: [tag♥] [tag✗] [tag] ...                    │    │
│  │  领域: [tag] [tag♥] ...                           │    │
│  │  角色: [tag✗] [tag] ...                           │    │
│  │  风格: [tag] [tag♥] ...                           │    │
│  │                                                   │    │
│  │  Summary: 3 个喜欢, 2 个不喜欢                    │    │
│  │                              [保存标签偏好]        │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  🛍 My Shop                                  →   │    │
│  │  Manage your products, set prices, link agents    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  My Media                                         │    │
│  │  [Upload photo/video]                             │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │    │
│  │  │ img    │ │ img    │ │ Video  │ │ img    │    │    │
│  │  │ name.. │ │ name.. │ │        │ │ name.. │    │    │
│  │  │[Avatar]│ │[Avatar]│ │        │ │[Avatar]│    │    │
│  │  │[Delete]│ │[Delete]│ │[Delete]│ │[Delete]│    │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘    │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

## 用户 Profile 数据模型

| 字段 | 类型 | 说明 |
|------|------|------|
| `display_name` | `Optional[str]` | 昵称 |
| `gender` | `Optional[str]` | "male" / "female" / "other" / "prefer_not_to_say" |
| `birthday` | `Optional[date]` | 生日 |
| `location` | `Optional[str]` | 所在地（城市/地区） |
| `bio` | `Optional[str]` | 个人简介 (Text) |
| `personality` | `Optional[List[str]]` | 性格标签 (JSON, 如 ["外向", "乐观"]) |
| `hobbies` | `Optional[List[str]]` | 兴趣爱好 (JSON, 如 ["摄影", "旅行"]) |
| `occupation` | `Optional[str]` | 职业 |
| `website` | `Optional[str]` | 个人网站/社交链接 |

## 用户标签偏好

### 数据模型

`user_tag_preference` 表:

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `UUID` | 用户 ID (PK, FK -> user) |
| `tag_id` | `UUID` | 标签 ID (PK, FK -> tag) |
| `preference` | `str` | "like" 或 "dislike" |

### 交互逻辑

- 使用 agent-scope 标签分类（意图、领域、角色、风格）
- 每个标签三态切换：中立 → 喜欢(绿色♥) → 不喜欢(红色✗删除线) → 中立
- 带子标签的父标签点击时展开子标签行

### Plaza 集成

- 喜欢的标签：对应 Agent 在广场搜索中获得排序加分，优先展示
- 不喜欢的标签：拥有该标签的 Agent 从搜索结果中完全过滤掉
- 偏好在服务端自动应用，前端 Plaza 页面无需修改

## 区域说明

### 区域 1: Header Card

- 显示头像（圆形）、昵称/用户名、个人简介预览
- 无头像时显示昵称首字母

### 区域 2: 基本信息

- 昵称、性别（下拉选择）、生日（日期选择器）、所在地、职业、个人网站、个人简介
- 2 列网格布局，简介占满 2 列

### 区域 3: 性格 & 兴趣

- 性格标签和兴趣爱好：使用 tag-input 组件，可添加/删除自定义标签
- 输入框 + 按钮或回车添加，× 按钮删除

### 区域 4: Agent 标签偏好

- 从 `GET /plaza/tags` 加载 agent-scope 标签分类
- 按分类分组展示，支持二级展开
- 三态切换交互，实时显示喜欢/不喜欢计数
- 独立保存按钮

### 区域 5: My Shop 入口卡片

- 链接到 `/shop`，hover 时边框变色 + 阴影

### 区域 6: My Media（媒体库）

- 上传：点击按钮触发 file input，调用 `POST /media/upload`
- 媒体网格：图片缩略图/视频占位、文件名、Set as avatar（仅图片）、Delete
- 空状态提示文案

## API 依赖

| Method | Path | 说明 |
|--------|------|------|
| GET | `/user/profile?user_id=` | 获取用户完整 profile |
| PUT | `/user/profile` | 更新用户 profile 字段 |
| GET | `/user/preferences?user_id=` | 获取用户标签偏好 |
| PUT | `/user/preferences` | 设置用户标签偏好 (liked + disliked) |
| GET | `/plaza/tags` | 获取 agent-scope 标签分类（用于偏好选择） |
| GET | `/media/?user_id=` | 获取用户媒体列表 |
| POST | `/media/upload` | 上传照片/视频 (multipart) |
| DELETE | `/media/{id}?user_id=` | 删除媒体 |
| POST | `/media/avatar` | 设置头像 (body: user_id, media_id) |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/app/profile/page.tsx` | 页面实现 |
| `frontend/lib/api.ts` | API 函数 (getUserProfile, updateUserProfile, getUserPreferences, updateUserPreferences) |
| `backend/app/api/user.py` | 用户 profile 和偏好 CRUD 端点 |
| `backend/app/models/user.py` | User 模型（含 profile 字段） |
| `backend/app/models/tag.py` | UserTagPreference 模型 |
| `backend/app/schemas/user.py` | UserProfileUpdate, UserPreferencesRead/Update schema |
| `backend/app/repositories/base.py` | UserTagPreferenceRepository 抽象类 |
| `backend/app/repositories/db_repo.py` | DBUserTagPreferenceRepository 实现 |
| `backend/app/services/plaza_service.py` | search_plaza（集成偏好过滤/排序） |
| `backend/app/api/plaza.py` | Plaza search 端点（自动加载偏好） |
| `backend/migrations/003_user_profile_and_preferences.py` | 数据库迁移脚本 |
