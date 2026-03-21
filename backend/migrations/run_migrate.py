"""Execute database migration: add embedding, is_user_defined, scope columns."""
import asyncio
import asyncmy


async def migrate():
    conn = await asyncmy.connect(
        host="localhost", port=3306,
        user="root", password="cy1234567",
        db="agentmatch", charset="utf8mb4"
    )
    cur = conn.cursor()

    # 1. tag: add embedding column
    try:
        await cur.execute("ALTER TABLE tag ADD COLUMN embedding JSON DEFAULT NULL")
        print("[OK] tag.embedding added")
    except Exception as e:
        print(f"[SKIP] tag.embedding: {e}")

    # 2. tag: add is_user_defined column
    try:
        await cur.execute("ALTER TABLE tag ADD COLUMN is_user_defined TINYINT(1) NOT NULL DEFAULT 0")
        print("[OK] tag.is_user_defined added")
    except Exception as e:
        print(f"[SKIP] tag.is_user_defined: {e}")

    # 3. tag_category: add scope column
    try:
        await cur.execute("ALTER TABLE tag_category ADD COLUMN scope VARCHAR(10) NOT NULL DEFAULT 'agent'")
        print("[OK] tag_category.scope added")
    except Exception as e:
        print(f"[SKIP] tag_category.scope: {e}")

    # 4. Set product scope for product categories
    await cur.execute(
        "UPDATE tag_category SET scope = 'product' "
        "WHERE slug IN ('category', 'condition', 'product_type', 'target')"
    )
    print(f"[OK] Updated {cur.rowcount} categories to product scope")

    # 5. Clean product-scope tags from agent_tag (if any dirty data)
    await cur.execute(
        "DELETE at_ FROM agent_tag at_ "
        "INNER JOIN tag t ON at_.tag_id = t.id "
        "INNER JOIN tag_category tc ON t.category_id = tc.id "
        "WHERE tc.scope = 'product'"
    )
    print(f"[OK] Cleaned {cur.rowcount} product-scope entries from agent_tag")

    # 6. Add index on scope
    try:
        await cur.execute("CREATE INDEX idx_tag_category_scope ON tag_category(scope)")
        print("[OK] Index idx_tag_category_scope created")
    except Exception as e:
        print(f"[SKIP] Index: {e}")

    await conn.commit()

    # Verify
    await cur.execute("SELECT id, name, slug, scope FROM tag_category ORDER BY scope, sort_order")
    rows = await cur.fetchall()
    print()
    print("=== tag_category verification ===")
    for r in rows:
        print(f"  {r[1]:8s}  scope={r[3]}  slug={r[2]}")

    await cur.execute("SELECT COUNT(*) FROM tag WHERE embedding IS NOT NULL")
    emb_count = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM tag")
    total = (await cur.fetchone())[0]
    print(f"\nTags with embedding: {emb_count}/{total}")

    await cur.close()
    await conn.ensure_closed()
    print("\n[DONE] Migration completed successfully!")


asyncio.run(migrate())
