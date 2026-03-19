"""
Auto-seed tag_categories and tags from storage/seed/ JSON files.
Idempotent: skips rows that already exist.
"""

import json
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from app.models.tag import TagCategory, Tag


async def seed_tags(session: AsyncSession):
    cat_file = settings.STORAGE_SEED_DIR / "tag_categories.json"
    tag_file = settings.STORAGE_SEED_DIR / "tags.json"

    if not cat_file.exists() or not tag_file.exists():
        print(f"[seed] Seed files not found at {settings.STORAGE_SEED_DIR}, skipping")
        return

    with open(cat_file, "r", encoding="utf-8") as f:
        categories = json.load(f)
    with open(tag_file, "r", encoding="utf-8") as f:
        tags = json.load(f)

    existing_cat_ids = {
        row.id for row in (await session.exec(select(TagCategory))).all()
    }
    existing_tag_ids = {
        row.id for row in (await session.exec(select(Tag))).all()
    }

    new_cats = 0
    for cat in categories:
        cid = UUID(cat["id"])
        if cid in existing_cat_ids:
            continue
        session.add(TagCategory(
            id=cid,
            name=cat["name"],
            slug=cat["slug"],
            description=cat.get("description"),
            sort_order=cat.get("sort_order", 0),
            is_active=cat.get("is_active", True),
        ))
        new_cats += 1
    if new_cats:
        await session.commit()

    parent_tags = [t for t in tags if not t.get("parent_id")]
    child_tags = [t for t in tags if t.get("parent_id")]

    new_tags = 0
    for tag in parent_tags:
        tid = UUID(tag["id"])
        if tid in existing_tag_ids:
            continue
        session.add(Tag(
            id=tid,
            category_id=UUID(tag["category_id"]),
            name=tag["name"],
            slug=tag["slug"],
            parent_id=None,
            sort_order=tag.get("sort_order", 0),
            is_active=tag.get("is_active", True),
        ))
        new_tags += 1
    if new_tags:
        await session.commit()

    new_children = 0
    for tag in child_tags:
        tid = UUID(tag["id"])
        if tid in existing_tag_ids:
            continue
        session.add(Tag(
            id=tid,
            category_id=UUID(tag["category_id"]),
            name=tag["name"],
            slug=tag["slug"],
            parent_id=UUID(tag["parent_id"]),
            sort_order=tag.get("sort_order", 0),
            is_active=tag.get("is_active", True),
        ))
        new_children += 1
    if new_children:
        await session.commit()

    total_new = new_cats + new_tags + new_children
    if total_new:
        print(f"[seed] Inserted {new_cats} categories, {new_tags + new_children} tags")
    else:
        print("[seed] All seed data already present, nothing to insert")
