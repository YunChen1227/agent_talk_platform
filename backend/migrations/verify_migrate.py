import asyncio
import asyncmy


async def verify():
    conn = await asyncmy.connect(
        host="localhost", port=3306,
        user="root", password="cy1234567",
        db="agentmatch", charset="utf8mb4"
    )
    cur = conn.cursor()

    await cur.execute("DESCRIBE tag_category")
    print("=== tag_category columns ===")
    for row in await cur.fetchall():
        print(f"  {row[0]:20s} {row[1]}")

    print()
    await cur.execute("DESCRIBE tag")
    print("=== tag columns ===")
    for row in await cur.fetchall():
        print(f"  {row[0]:20s} {row[1]}")

    print()
    await cur.execute("SELECT name, scope FROM tag_category ORDER BY scope, sort_order")
    print("=== scope verification ===")
    for row in await cur.fetchall():
        print(f"  {row[0]:10s} -> {row[1]}")

    await cur.close()
    await conn.ensure_closed()


asyncio.run(verify())
