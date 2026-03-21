-- 002_tag_scope.sql
-- 将 agent tags 与 product tags 彻底分离
-- 在 tag_category 表中增加 scope 字段区分所属域

-- 1. 新增 scope 列，默认值为 'agent'
ALTER TABLE tag_category
    ADD COLUMN scope VARCHAR(10) NOT NULL DEFAULT 'agent';

-- 2. 将商品维度的4个分类设为 product scope
UPDATE tag_category SET scope = 'product'
WHERE slug IN ('category', 'condition', 'product_type', 'target');

-- 3. 确认一下 agent scope 的分类
-- SELECT id, name, slug, scope FROM tag_category ORDER BY scope, sort_order;

-- 4. (可选) 清理 agent_tag 中被错误同步进来的 product-scope tags
--    如果之前运行过 _sync_product_tags_to_agent，agent_tag 表可能包含
--    product 维度的 tag_id。下面的语句会清理这些脏数据。
DELETE at FROM agent_tag at
INNER JOIN tag t ON at.tag_id = t.id
INNER JOIN tag_category tc ON t.category_id = tc.id
WHERE tc.scope = 'product';

-- 5. 添加索引加速 scope 查询
CREATE INDEX idx_tag_category_scope ON tag_category(scope);
