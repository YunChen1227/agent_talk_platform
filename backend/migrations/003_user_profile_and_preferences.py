"""Migration: add user profile fields and user_tag_preference table."""
import asyncio
import asyncmy


async def migrate():
    conn = await asyncmy.connect(
        host="localhost", port=3306,
        user="root", password="cy1234567",
        db="agentmatch", charset="utf8mb4"
    )
    cur = conn.cursor()

    # 1. user: add profile columns
    profile_columns = [
        ("display_name", "VARCHAR(100) DEFAULT NULL"),
        ("gender", "VARCHAR(20) DEFAULT NULL"),
        ("birthday", "DATE DEFAULT NULL"),
        ("location", "VARCHAR(255) DEFAULT NULL"),
        ("bio", "TEXT DEFAULT NULL"),
        ("personality", "JSON DEFAULT NULL"),
        ("hobbies", "JSON DEFAULT NULL"),
        ("occupation", "VARCHAR(100) DEFAULT NULL"),
        ("website", "VARCHAR(255) DEFAULT NULL"),
    ]

    for col_name, col_def in profile_columns:
        try:
            await cur.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_def}")
            print(f"[OK] user.{col_name} added")
        except Exception as e:
            print(f"[SKIP] user.{col_name}: {e}")

    # 2. Create user_tag_preference table
    try:
        await cur.execute("""
            CREATE TABLE user_tag_preference (
                user_id CHAR(36) NOT NULL,
                tag_id CHAR(36) NOT NULL,
                preference VARCHAR(10) NOT NULL,
                PRIMARY KEY (user_id, tag_id),
                INDEX idx_utp_preference (preference),
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("[OK] user_tag_preference table created")
    except Exception as e:
        print(f"[SKIP] user_tag_preference table: {e}")

    await conn.commit()

    # Verify
    await cur.execute("DESCRIBE user")
    rows = await cur.fetchall()
    print("\n=== user table columns ===")
    for r in rows:
        print(f"  {r[0]:20s} {r[1]}")

    await cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='agentmatch' AND table_name='user_tag_preference'")
    count = (await cur.fetchone())[0]
    print(f"\nuser_tag_preference table exists: {bool(count)}")

    await cur.close()
    await conn.ensure_closed()
    print("\n[DONE] Migration 003 completed successfully!")


asyncio.run(migrate())
