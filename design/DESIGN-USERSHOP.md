# 用户商店模块 (User Shop Module)

> 返回 [主设计文档](./DESIGN.md)

## 概述

每个用户拥有一个个人商店 (Shop)。用户可在商店中创建商品、定价、上传商品图片等。**所有用户的商品界面仅可看到自己的商品**，即列表与详情接口均按 `user_id` 过滤，仅返回当前用户拥有的商品。在买卖场景下，Agent 可将商品以「商品卡片」形式发送给对方。创建 Agent 时可绑定用户的一个或多个商品；创建商品时也可关联到已有 Agent，形成双向绑定。

## 字段 (Product)

### 用户填写字段

创建/编辑商品时，用户需要填写以下核心字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | String | 是 | 商品名称 |
| `images` | List[UUID] | 是 | 商品图片，从用户媒体库中选取，引用 UserMedia.id；第一张默认作为封面 |
| `description` | Text | 否 | 商品介绍，描述商品详情、卖点等 |
| `price` | Decimal | 是 | 商品价格 (默认货币 CNY) |
| `tag_ids` | List[UUID] | 否 | 商品标签，从预置标签目录中选择 (意图/领域/角色)，与 Agent 标签体系对齐 |

### 系统与关联字段

以下字段由系统自动管理或在特定操作时写入，用户无需手动填写：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键，系统自动生成 |
| `user_id` | UUID | 所属用户，创建时由系统写入 |
| `currency` | String | 货币，默认 `CNY` |
| `cover_image_id` | UUID (可选) | 封面图，默认为 `images` 的第一张，用户可手动指定 |
| `status` | Enum | `ACTIVE` / `INACTIVE`，仅 ACTIVE 可被 Agent 发送；默认 ACTIVE |
| `tag_ids` | List[UUID] | 商品标签 ID 列表，用户选择并存储，与 Agent 标签体系共用预置目录 |
| `linked_agent_ids` | List[UUID] | 已关联的 Agent，通过关联操作维护 |
| `created_at` | Timestamp | 创建时间 |
| `updated_at` | Timestamp | 更新时间 |

## 隐私与可见性

- **商品列表与详情**：所有商品相关 API 均需传入或鉴权得到 `user_id`，且只返回该用户拥有的商品。其他用户的商品不可见、不可查。
- 在会话中，当 Agent 发送商品卡片给对方时，对方看到的是该商品的展示信息（名称、价格、封面图等），而非跨用户访问商品库。

## Agent–Product 双向绑定

- **创建/编辑商品时**：用户可勾选已有 Agent，将商品关联到这些 Agent（写入 `Product.linked_agent_ids`）。
- **创建/编辑 Agent 时**：用户可勾选已有商品，将 Agent 关联到这些商品（写入 `Agent.linked_product_ids`）。
- 双向一致：若商品 A 的 `linked_agent_ids` 包含 Agent X，则 Agent X 的 `linked_product_ids` 应包含商品 A，反之亦然。实现时需在「关联/解绑」接口中同时维护 Product 与 Agent 两侧。

## 商品标签与 Agent 标签自动同步

商品和 Agent 共用同一套预置标签目录（参见 [DESIGN-PLAZA.md](./DESIGN-PLAZA.md)）。创建商品时可选择意图 (intent)、领域 (domain)、角色 (role) 三个维度的标签。

**标签自动继承规则:**

- **商品绑定 Agent 时** (创建商品时选择关联 Agent，或通过 `link_agent_to_product`)：系统自动将商品的 `tag_ids` 合并到 Agent 的 `agent_tag` 关联表中（仅追加，不覆盖 Agent 原有标签）。
- **Agent 绑定商品时** (创建/编辑 Agent 时选择关联商品)：系统自动将所有已关联商品的 `tag_ids` 合并到 Agent 的 `agent_tag` 关联表中。
- **追加不删除**: 标签同步为单向追加——商品标签会自动添加到 Agent 上，但解绑商品时不会自动移除 Agent 上的标签（避免误删用户手动选择的标签）。

```
商品创建 (带 tag_ids + linked_agent_ids)
  └─> 对每个关联的 Agent，追加商品的 tag_ids 到 agent_tag

商品绑定 Agent (link_agent_to_product)
  └─> 追加该商品的 tag_ids 到目标 Agent 的 agent_tag

Agent 创建/编辑 (带 linked_product_ids)
  └─> 查询所有关联商品的 tag_ids，追加到该 Agent 的 agent_tag
```

## 商品在对话中的使用

- 在买卖场景下，Agent 可将**已关联的商品**以消息附件形式发送给对方。
- 消息附件类型为 `product`，包含 `product_id`、名称、价格、封面图 URL 等，用于前端渲染商品卡片。详见 [DESIGN-SESSION.md](./DESIGN-SESSION.md) 中 Message 的 `attachments` 设计。

## 核心功能 (Functions)

- `create_product(user_id, name, description, price, currency, image_ids, cover_image_id, linked_agent_ids?, tag_ids?)`: 创建商品，可选标签和关联 Agent；若关联了 Agent，自动将商品标签追加到 Agent。
- `update_product(product_id, user_id, ...)`: 更新商品信息（含图片、关联 Agent），仅允许所属用户。
- `delete_product(product_id, user_id)`: 删除商品，仅允许所属用户；删除时解除与所有 Agent 的关联。
- `list_products(user_id)`: 列出该用户的全部商品（仅本人可见）。
- `get_product(product_id, user_id)`: 获取商品详情，仅允许所属用户。
- `link_agent_to_product(product_id, agent_id, user_id)`: 将 Agent 与商品关联，需校验 Agent 与 Product 均属于该用户；自动将商品 `tag_ids` 追加到 Agent 的 `agent_tag`。
- `unlink_agent_from_product(product_id, agent_id, user_id)`: 解除 Agent 与商品的关联。

## 相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/models/product.py` | Product 数据模型 |
| `backend/app/schemas/product.py` | ProductCreate, ProductUpdate, ProductRead |
| `backend/app/api/shop.py` | 商品 CRUD 及关联/解绑路由 |
| `backend/app/services/shop_service.py` | 商品与关联业务逻辑 |
