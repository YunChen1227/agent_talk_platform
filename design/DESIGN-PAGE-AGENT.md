# Agent 创建/编辑页 (`/agent/new` & `/agent/[id]`)

> 返回 [前端总览](./DESIGN-FRONTEND.md) | [主设计文档](./DESIGN.md)

## 概述

创建新 Agent 或编辑已有 Agent 的人设信息。创建时根据用户 tier (FREE/PAID) 展示不同表单。

---

## 创建页 (`/agent/new`)

### 页面布局

```
┌──────────────────────────────────────────────┐
│  ← Back to Dashboard                         │
│  Create New Agent                             │
│  Free Tier: Manual Configuration              │
│                                               │
│  ┌────────────────────────────────────────┐   │
│  │ Agent Name: [___________________]      │   │
│  │                                        │   │
│  │ [FREE] System Prompt:                  │   │
│  │ [________________________]             │   │
│  │ [________________________]             │   │
│  │                                        │   │
│  │ [FREE] Opening Remark:                 │   │
│  │ [___________________]                  │   │
│  │                                        │   │
│  │ [PAID] Agent Description:              │   │
│  │ (AI 自动生成 system_prompt)            │   │
│  │                                        │   │
│  │ Linked Products: [multi-select ▼] [+]  │   │
│  │ Linked Skills:   [multi-select ▼] [+]  │   │
│  │                                        │   │
│  │ [Create Agent]  [Cancel]               │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

### 表单字段

#### FREE 用户

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Agent Name | input | 是 | Agent 对外名称 |
| System Prompt | textarea | 是 | 手动编写的 Agent 人设指令 |
| Opening Remark | input | 是 | Agent 匹配成功后的开场白 |

#### PAID 用户

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Agent Name | input | 是 | Agent 对外名称 |
| Agent Description | textarea | 是 | 描述性格/喜好/需求/说话方式，平台 LLM 自动生成 system_prompt + opening_remark |

### 提交按钮状态

- **禁用条件**: Agent Name 为空，或 FREE 时 system_prompt / opening_remark 为空，或 PAID 时 description 为空，或正在提交中。
- **提交中**: 按钮文字变为 "Creating..."。

### 交互流程

1. 填写表单。
2. 点击 "Create Agent" → 调用 `POST /agents/`。
3. 成功 → 跳转 `/` (Dashboard)。
4. 失败 → alert 错误信息。

---

## 编辑页 (`/agent/[id]`)

### 页面布局

```
┌──────────────────────────────────────────────┐
│  ← Back to Dashboard                         │
│  Edit Agent Persona                           │
│                                               │
│  ┌────────────────────────────────────────┐   │
│  │ Agent Name: [___________________]      │   │
│  │                                        │   │
│  │ Opening Remark:                        │   │
│  │ [___________________]                  │   │
│  │                                        │   │
│  │ System Prompt (Persona):               │   │
│  │ [________________________]             │   │
│  │ [________________________]             │   │
│  │ [________________________]             │   │
│  │                                        │   │
│  │                                        │   │
│  │ Linked Products: [multi-select ▼] [+]  │   │
│  │ Linked Skills:   [multi-select ▼] [+]  │   │
│  │                                        │   │
│  │                    [Save Changes]      │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

### 表单字段

| 字段 | 类型 | 说明 |
|------|------|------|
| Agent Name | input | 可修改名称 |
| Opening Remark | textarea | 修改开场白 |
| System Prompt | textarea (大) | 修改核心人设指令 |

### 交互流程

1. 页面加载 → 调用 `GET /agents/{id}` 填充表单。
2. 修改字段后点击 "Save Changes" → 调用 `PUT /agents/{id}`。
3. 成功 → alert "Agent updated successfully!"。
4. 失败 → alert 错误信息。

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
