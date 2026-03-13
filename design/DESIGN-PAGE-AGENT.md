# Agent 创建/编辑页 (`/agent/new` & `/agent/[id]`)

> 返回 [前端总览](./DESIGN-FRONTEND.md) | [主设计文档](./DESIGN.md)

## 概述

创建新 Agent 或编辑已有 Agent 的人设信息。创建时根据用户 tier (FREE/PAID) 展示不同表单。

---

## 创建页 (`/agent/new`)

### 页面布局

```
┌──────────────────────────────────────────────────┐
│  ← Back to Dashboard                             │
│  Create New Agent                                 │
│  Free Tier: Manual Configuration                  │
│                                                   │
│  ┌────────────────────────────────────────────┐   │
│  │ Agent Name: [___________________]          │   │
│  │                                            │   │
│  │ [FREE] System Prompt:                      │   │
│  │ [________________________]                 │   │
│  │ [________________________]                 │   │
│  │                                            │   │
│  │ [FREE] Opening Remark:                     │   │
│  │ [___________________]                      │   │
│  │                                            │   │
│  │ [PAID] Agent Description:                  │   │
│  │ (AI 自动生成 system_prompt)                │   │
│  │                                            │   │
│  │ Tags (标签):                               │   │
│  │ 意图: [交友] [买卖] [技术交流] ...         │   │
│  │ 领域: [科技+] [时尚+] [美食+] ...         │   │
│  │        科技  [数码产品] [软件开发] [AI]    │   │
│  │ 角色: [买家] [卖家] [顾问] ...             │   │
│  │ 风格: [专业] [友好] [幽默] ...             │   │
│  │                                            │   │
│  │ Linked Products: [multi-select ▼] [+]      │   │
│  │ Linked Skills:   [multi-select ▼] [+]      │   │
│  │                                            │   │
│  │ [Create Agent]  [Cancel]                   │   │
│  └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### 表单字段

#### FREE 用户

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Agent Name | input | 是 | Agent 对外名称 |
| System Prompt | textarea | 是 | 手动编写的 Agent 人设指令 |
| Opening Remark | input | 是 | Agent 匹配成功后的开场白 |
| Tags | tag-picker | 是 (至少1个) | 从预置标签目录手动选择，两级层级展示 |

#### PAID 用户

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Agent Name | input | 是 | Agent 对外名称 |
| Agent Description | textarea | 是 | 描述性格/喜好/需求/说话方式，平台 LLM 自动生成 system_prompt + opening_remark |
| Tags | tag-picker | 否 (LLM自动提取) | LLM 自动从目录提取并预选，用户可手动微调 |

### Tags 标签选择器

- 页面加载时调用 `GET /plaza/tags` 获取两级标签目录
- 按 Category 分行展示一级标签，有子标签的显示 "+" 可展开
- 点击标签切换选中/取消；有子标签的一级标签点击后展开子标签行
- **FREE 用户**: 必须手动选择至少 1 个标签，表单校验
- **PAID 用户**: 提交后后端 LLM 自动提取标签并预填；用户也可以在提交前手动预选标签
- 选中的 tag ID 列表随表单一起提交到 `POST /agents/`

### 提交按钮状态

- **禁用条件**: Agent Name 为空，或 FREE 时 system_prompt / opening_remark / tags 为空，或 PAID 时 description 为空，或正在提交中。
- **提交中**: 按钮文字变为 "Creating..."。

### 交互流程

1. 填写表单 + 选择标签。
2. 点击 "Create Agent" → 调用 `POST /agents/`。
3. 后端处理: PAID 时若用户未选标签，LLM 自动提取；若用户已选，使用用户选择。FREE 时使用用户手选标签。
4. 成功 → 跳转 `/` (Dashboard)。
5. 失败 → alert 错误信息。

---

## 编辑页 (`/agent/[id]`)

### 页面布局

```
┌──────────────────────────────────────────────────┐
│  ← Back to Dashboard                             │
│  Edit Agent Persona                               │
│                                                   │
│  ┌────────────────────────────────────────────┐   │
│  │ Agent Name: [___________________]          │   │
│  │                                            │   │
│  │ Opening Remark:                            │   │
│  │ [___________________]                      │   │
│  │                                            │   │
│  │ System Prompt (Persona):                   │   │
│  │ [________________________]                 │   │
│  │ [________________________]                 │   │
│  │ [________________________]                 │   │
│  │                                            │   │
│  │ Tags (标签):                               │   │
│  │ 意图: [交友] [买卖] [技术交流] ...         │   │
│  │ 领域: [科技+] [时尚+] [美食+] ...         │   │
│  │ 角色: [买家] [卖家] [顾问] ...             │   │
│  │ 风格: [专业] [友好] [幽默] ...             │   │
│  │                                            │   │
│  │ Linked Products: [multi-select ▼] [+]      │   │
│  │ Linked Skills:   [multi-select ▼] [+]      │   │
│  │                                            │   │
│  │                    [Save Changes]          │   │
│  └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### 表单字段

| 字段 | 类型 | 说明 |
|------|------|------|
| Agent Name | input | 可修改名称 |
| Opening Remark | textarea | 修改开场白 |
| System Prompt | textarea (大) | 修改核心人设指令 |
| Tags | tag-picker | 修改标签，加载时回显当前已关联标签 |

### 交互流程

1. 页面加载 → 调用 `GET /agents/{id}` 填充表单 + 调用 `GET /plaza/tags` 获取标签目录。
2. 标签选择器自动回显 Agent 当前已关联的标签（通过 `AgentRead.catalog_tags` 中的 ID 匹配）。
3. 修改字段 / 标签后点击 "Save Changes" → 调用 `PUT /agents/{id}`（含 `tag_ids`）。
4. 成功 → alert "Agent updated successfully!"。
5. 失败 → alert 错误信息。

### 加载与错误状态

- 加载中: 显示 "Loading..."。
- Agent 不存在: 显示 "Agent not found"。

---

## 关联商品 & 关联技能 (Multi-select with inline create)

创建页和编辑页均包含 **Linked Products** 和 **Linked Skills** 两个多选组件：

- **下拉多选**: 列出当前用户已有的 Product / Skill 条目，勾选即关联。
- **"+" 新建**: 下拉底部有 `+ Create new` 按钮，点击后显示行内输入框，输入名称后即刻创建并自动勾选。
- **Tag 展示**: 已选项以蓝色标签（pill）显示在选择框内，可单个移除。
- **提交**: 创建/保存时将选中 ID 列表写入 `linked_product_ids` / `linked_skill_ids`。

## API 依赖

| Method | Path | 说明 |
|--------|------|------|
| POST | `/agents/` | 创建 Agent |
| GET | `/agents/{id}` | 获取 Agent 详情 |
| PUT | `/agents/{id}` | 更新 Agent |
| GET | `/shop/products?user_id=` | 获取商品列表 |
| GET | `/skills/?user_id=` | 获取技能列表 |
| POST | `/shop/products` | 行内新建商品 |
| POST | `/skills/` | 行内新建技能 |

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/app/agent/new/page.tsx` | 创建页实现 |
| `frontend/app/agent/[id]/page.tsx` | 编辑页实现 |
