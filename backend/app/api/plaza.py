from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.plaza import TagCategoryRead, TagCreate, PlazaSearchResponse, TagRead
from app.repositories.base import (
    AgentRepository,
    TagCategoryRepository,
    TagRepository,
    AgentTagRepository,
    SessionRepository,
    MatchResultRepository,
)
from app.core.deps import (
    get_agent_repo,
    get_tag_category_repo,
    get_tag_repo,
    get_agent_tag_repo,
    get_session_repo,
    get_match_result_repo,
)
from app.models.tag import Tag
from app.services.plaza_service import get_tag_catalog, search_plaza
import re
from uuid import uuid4 as _uuid4

router = APIRouter()


@router.get("/tags", response_model=List[TagCategoryRead])
async def list_tags(
    cat_repo: TagCategoryRepository = Depends(get_tag_category_repo),
    tag_repo: TagRepository = Depends(get_tag_repo),
):
    """Return the full tag catalog grouped by category."""
    return await get_tag_catalog(cat_repo, tag_repo)


@router.post("/tags", response_model=TagRead)
async def create_tag(
    body: TagCreate,
    tag_repo: TagRepository = Depends(get_tag_repo),
    cat_repo: TagCategoryRepository = Depends(get_tag_category_repo),
):
    """Create a new user-defined tag in a given category."""
    cats = await cat_repo.list_active()
    if not any(c.id == body.category_id for c in cats):
        raise HTTPException(status_code=400, detail="Category not found")

    slug = re.sub(r"[^a-z0-9]+", "-", body.name.lower()).strip("-")
    if not slug:
        slug = f"user-tag-{_uuid4().hex[:8]}"
    existing = await tag_repo.get_by_slug(slug)
    if existing:
        return TagRead(id=str(existing.id), name=existing.name, slug=existing.slug, children=[])

    tag = Tag(
        category_id=body.category_id,
        name=body.name,
        slug=slug,
        sort_order=999,
        is_active=True,
    )
    tag = await tag_repo.create(tag)
    return TagRead(id=str(tag.id), name=tag.name, slug=tag.slug, children=[])


@router.get("/search", response_model=PlazaSearchResponse)
async def search(
    user_id: UUID,
    tag_ids: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    agent_repo: AgentRepository = Depends(get_agent_repo),
    agent_tag_repo: AgentTagRepository = Depends(get_agent_tag_repo),
    tag_repo: TagRepository = Depends(get_tag_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repo),
):
    """Hybrid search for plaza agents with match status."""
    parsed_tag_ids = None
    if tag_ids:
        parsed_tag_ids = [
            UUID(tid.strip()) for tid in tag_ids.split(",") if tid.strip()
        ]

    result = await search_plaza(
        user_id=user_id,
        agent_repo=agent_repo,
        agent_tag_repo=agent_tag_repo,
        tag_repo=tag_repo,
        session_repo=session_repo,
        match_result_repo=match_result_repo,
        tag_ids=parsed_tag_ids,
        q=q,
        page=page,
        page_size=page_size,
    )
    return result
