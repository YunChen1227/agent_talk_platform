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
│  │ 匹配意图 (Match Intent):                   │   │
│  │ [搜索意图标签...              ▼]            │   │
│  │  已选: [交友 ×] [买卖 ×]                   │   │
│  │                                            │   │
│  │ Tags (标签):                               │   │
│  │ [搜索标签...                  ▼]            │   │
│  │  已选: [科技 ×] [数码产品 ×] [专业 ×]      │   │
│  │                                            │   │
│  │ Linked Products: [multi-select ▼] [+]      │   │
│  │ Linked Skills:   [multi-select ▼] [+]      │   │
│  │                                            │   │
│  │ (有关联商品时显示，只读)                   │   │
│  │ 商品标签: 数码电子 · 全新 · 实物商品       │   │
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
| Match Intent | tag-dropdown-select | 否 | 匹配意图偏好，下拉多选，仅显示"意图"分类下的一级标签。支持搜索和新增。为空时不限制意图 |
| Tags | tag-dropdown-select | 是 (至少1个) | 下拉多选，展示全部预置标签目录。支持搜索和新增 |

#### PAID 用户

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Agent Name | input | 是 | Agent 对外名称 |
| Agent Description | textarea | 是 | 描述性格/喜好/需求/说话方式，平台 LLM 自动生成 system_prompt + opening_remark |
| Match Intent | tag-dropdown-select | 否 | 匹配意图偏好，下拉多选，仅显示"意图"分类下的一级标签。支持搜索和新增。LLM 可自动推荐，用户可微调 |
| Tags | tag-dropdown-select | 否 (LLM自动提取) | 下拉多选，展示全部预置标签目录。支持搜索和新增。LLM 自动提取并预选，用户可微调 |

### 标签下拉选择组件 (TagDropdownSelect)

Agent 页面的 **匹配意图 (Match Intent)** 和 **Tags (标签)** 均使用同一个通用下拉多选组件，与商品页标签选择器共享同一实现。

**组件结构:**

```
┌───────────────────────────────────┐
│ [搜索标签...                   ▼] │  ← 文本输入框 + 下拉触发
├───────────────────────────────────┤
│  意图                             │  ← 按 Category 分组标题
│  ☑ 交友                          │
│  ☐ 买卖                          │
│  ☐ 技术交流                      │
│  领域                             │
│  ☐ 科技                          │
│    ☐ 数码产品                    │  ← L2 子标签缩进
│    ☐ 软件开发                    │
│  ...                              │
├───────────────────────────────────┤
│  + 创建 "xxx"                     │  ← 输入文本无匹配时出现
└───────────────────────────────────┘
已选: [交友 ×] [科技 ×] [数码产品 ×]  ← pill 展示，可单个移除
```

**核心交互:**

1. **下拉列表**: 点击输入框展开下拉，按 Category 分组展示标签，两级层级缩进显示
2. **搜索过滤**: 输入文本实时过滤匹配的标签（按 name 子串匹配），高亮匹配项
3. **新增标签**: 输入文本无匹配结果时，下拉底部出现 `+ 创建 "xxx"` 选项，点击后调用 `POST /plaza/tags` 即时创建并自动选中
4. **多选**: 勾选/取消勾选切换，支持多个标签同时选中
5. **已选展示**: 输入框下方以 pill 标签展示已选项，每个 pill 带 `×` 可单独移除
6. **点击外部关闭**: 点击组件外区域收起下拉

**按场景配置:**

| 使用场景 | `filterCategorySlugs` 参数 | 新增标签归属 |
|---------|---------------------------|-------------|
| 匹配意图 (Match Intent) | `["intent"]` — 仅展示"意图"分类 | 归入"意图"分类，level 1 |
| Agent 标签 (Tags) | `null` — 展示全部分类 | 归入用户选择的分类 |
| 商品标签 (Product Tags) | `["category","condition","product_type","target"]` — 仅电商维度 | 归入对应电商分类 |

**数据流:**

- 页面加载时调用 `GET /plaza/tags` 获取标签目录
- 编辑时通过已有 ID 列表自动回显已选标签（pill 高亮）
- 选中的 tag ID 列表随表单一起提交（Match Intent → `match_intent_tag_ids`，Tags → `tag_ids`）
- **FREE 用户 Tags**: 必须手动选择至少 1 个标签，表单校验
- **PAID 用户 Tags**: LLM 自动提取并预选，用户可手动微调

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
│  │ 匹配意图 (Match Intent):                   │   │
│  │ [搜索意图标签...              ▼]            │   │
│  │  已选: [交友 ×] [买卖 ×]                   │   │
│  │                                            │   │
│  │ Tags (标签):                               │   │
│  │ [搜索标签...                  ▼]            │   │
│  │  已选: [科技 ×] [数码产品 ×] [专业 ×]      │   │
│  │                                            │   │
│  │ Linked Products: [multi-select ▼] [+]      │   │
│  │ Linked Skills:   [multi-select ▼] [+]      │   │
│  │                                            │   │
│  │ (有关联商品时显示，只读)                   │   │
│  │ 商品标签: 数码电子 · 全新 · 实物商品       │   │
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
| Match Intent | tag-dropdown-select | 下拉多选修改匹配意图偏好，加载时回显当前已选意图 |
| Tags | tag-dropdown-select | 下拉多选修改标签，加载时回显当前已关联标签 |

### 交互流程

1. 页面加载 → 调用 `GET /agents/{id}` 填充表单 + 调用 `GET /plaza/tags` 获取标签目录。
2. 匹配意图选择器自动回显 Agent 当前的 `match_intent_tag_ids`（高亮已选意图标签）。
3. 标签选择器自动回显 Agent 当前已关联的标签（通过 `AgentRead.catalog_tags` 中的 ID 匹配）。
4. 修改字段 / 标签 / 匹配意图后点击 "Save Changes" → 调用 `PUT /agents/{id}`（含 `tag_ids` + `match_intent_tag_ids`）。
5. 成功 → alert "Agent updated successfully!"。
6. 失败 → alert 错误信息。

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

### 商品标签只读展示

- 当 Linked Products 中选中了商品时，表单底部自动聚合展示这些商品自身的标签（分类/品质/类型/适用），以灰色 pill 只读呈现。
- 未关联任何商品时该区域隐藏。
- 仅供用户预览关联商品的属性，Agent 不存储这些商品标签，提交时也不包含在 `tag_ids` 中。

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
