# 用户资料/媒体页 (`/profile`)

> 返回 [前端总览](./DESIGN-FRONTEND.md) | [主设计文档](./DESIGN.md)

## 概述

用户个人资料页，管理头像与媒体库（照片/视频），并提供进入 "My Shop" 的入口卡片。

## 技术框架

Next.js 14 (App Router) · React 18 `useState`/`useEffect` · Axios (`multipart/form-data` 上传) · `<input type="file">` · Tailwind CSS 网格布局

## 页面布局

```
┌──────────────────────────────────────────────────────────┐
│  Profile & Media                    [Back to Dashboard]   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  🛍 My Shop                                  →   │    │
│  │  Manage your products, set prices, link agents    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Avatar                                           │    │
│  │  [头像图片]                                       │    │
│  │  Set avatar by clicking "Set as avatar" below.    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  My Media                                         │    │
│  │  [Upload photo/video]                             │    │
│  │                                                   │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │    │
│  │  │ img    │ │ img    │ │ Video  │ │ img    │    │    │
│  │  │ name.. │ │ name.. │ │        │ │ name.. │    │    │
│  │  │[Avatar]│ │[Avatar]│ │        │ │[Avatar]│    │    │
│  │  │[Delete]│ │[Delete]│ │[Delete]│ │[Delete]│    │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘    │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

## 区域 1: My Shop 入口卡片

- 链接到 `/shop`，以卡片形式展示。
- hover 时边框变色 + 阴影，右侧箭头提示可点击。

## 区域 2: Avatar

- 若 `user.avatar_url` 存在，展示圆形头像图片。
- 提示文案："Set avatar by clicking 'Set as avatar' on an image below."

## 区域 3: My Media（媒体库）

### 上传

- 点击 "Upload photo/video" 按钮触发 file input (`accept="image/*,video/*"`)。
- 上传调用 `POST /media/upload` (multipart/form-data)。
- 上传中按钮文字变为 "Uploading..."，上传完成刷新列表。

### 媒体网格

每个媒体项展示:

| 元素 | 说明 |
|------|------|
| **预览** | 图片: 展示缩略图；视频: 灰色占位 "Video" |
| **文件名** | 截断展示 original_filename |
| **Set as avatar** | 仅图片类型显示；调用 `POST /media/avatar`，更新 localStorage 中的 user.avatar_url |
| **Delete** | 二次确认后调用 `DELETE /media/{id}` |

### 空状态

"No media yet. Upload a photo or video."

## API 依赖

| Method | Path | 说明 |
|--------|------|------|
| GET | `/media/?user_id=` | 获取用户媒体列表 |
| POST | `/media/upload` | 上传照片/视频 (multipart) |
| DELETE | `/media/{id}?user_id=` | 删除媒体 |
| POST | `/media/avatar` | 设置头像 (body: user_id, media_id) |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/app/profile/page.tsx` | 页面实现 |
