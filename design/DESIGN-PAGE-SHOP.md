# 用户商店页 (`/shop`)

> 返回 [前端总览](./DESIGN-FRONTEND.md) | [主设计文档](./DESIGN.md) | [商店模块设计](./DESIGN-USERSHOP.md)

## 概述

用户个人商店，仅展示当前用户的商品，支持创建、删除商品。从 Profile 页面的 "My Shop" 卡片进入。

## 页面布局

```
┌──────────────────────────────────────────────────────────────┐
│  My Shop               [← Profile] [Dashboard] [+ New product] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  (创建表单 - 点击 + New product 时展开)                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Name:        [___________________]                         │  │
│  │ Description: [___________________]                         │  │
│  │ Price (CNY): [___________________]                         │  │
│  │                                                            │  │
│  │ Tags (标签):                                               │  │
│  │ [搜索标签...                                        ▼]     │  │
│  │  已选: [数码电子 ×] [全新 ×] [实物商品 ×]                  │  │
│  │                                                            │  │
│  │ [Create]                                                   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                             │
│  ── Your products ──────────────────────────────────────── │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Product A                                            │  │
│  │  描述文字...                                          │  │
│  │  99.00 CNY · Status: ACTIVE         [Edit] [Delete]   │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Product B                                            │  │
│  │  199.00 CNY · Status: ACTIVE        [Edit] [Delete]   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 顶栏

| 元素 | 说明 |
|------|------|
| **标题** | "My Shop" |
| **← 返回链接** | **列表模式**: 显示 "← Profile"，返回 `/profile`；**表单模式** (创建/编辑商品): 显示 "← My Shop"，关闭表单回到商品列表 |
| **Dashboard 链接** | 跳转 `/` |
| **+ New product 按钮** | 切换创建表单的展开/收起 |

## 创建商品表单

点击 "+ New product" 展开的表单。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Name | input | 是 | 商品名称 |
| Description | textarea | 否 | 商品介绍 |
| Price (CNY) | number (step=0.01) | 是 | 价格，默认货币 CNY |
| Tags (标签) | tag-dropdown-select | 否 | 下拉多选，展示电商相关标签（分类/品质/类型/适用）。支持搜索和新增 |

### Tags 标签选择器

- 使用通用 **TagDropdownSelect** 组件（详见 [DESIGN-PAGE-AGENT.md](./DESIGN-PAGE-AGENT.md) 标签下拉选择组件一节）。
- 配置 `filterCategorySlugs=["category","condition","product_type","target"]` 仅展示电商相关的四个维度。
- 页面加载时调用 `GET /plaza/tags` 获取标签目录。
- 下拉列表按 Category 分组展示，支持搜索过滤和新增标签。
- 已选标签以 pill 展示在输入框下方，可单个移除。
- 选中的 tag ID 列表随表单一起提交 (`tag_ids`)。
- 编辑商品时自动回显已选标签。
- 商品标签独立于 Agent 标签，不做自动继承。

提交 → 调用 `POST /shop/products`，成功后收起表单、刷新列表。

## 商品列表

每个商品卡片显示:

| 元素 | 说明 |
|------|------|
| **名称** | 粗体 |
| **描述** | 若有则展示 |
| **价格 + 货币** | 如 "99.00 CNY" |
| **状态** | ACTIVE / INACTIVE |
| **Edit 按钮** | 点击后将该商品信息填入顶部表单进入编辑模式，卡片高亮；提交后调用 `PUT /shop/products/{id}` |
| **Delete 按钮** | 二次确认后调用 `DELETE /shop/products/{id}` |

### 空状态

"No products. Create one to get started."

## 待扩展

- 从用户媒体库选择商品图片 (`images` 字段)
- 关联 Agent (link-agent / unlink-agent)
- 封面图指定 (`cover_image_id`)

## API 依赖

| Method | Path | 说明 |
|--------|------|------|
| GET | `/shop/products?user_id=` | 获取当前用户商品列表 |
| GET | `/plaza/tags` | 获取标签目录 (用于商品标签选择) |
| POST | `/shop/products` | 创建商品 (含 tag_ids) |
| PUT | `/shop/products/{id}` | 更新商品（待实现） |
| DELETE | `/shop/products/{id}` | 删除商品 |
| POST | `/shop/products/{id}/link-agent` | 关联 Agent（待实现） |
| POST | `/shop/products/{id}/unlink-agent` | 解绑 Agent（待实现） |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/app/shop/page.tsx` | 页面实现 |
