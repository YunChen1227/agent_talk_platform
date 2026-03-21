from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.plaza import (
    TagCategoryRead,
    TagCreate,
    PlazaSearchResponse,
    TagRead,
    TagEmbedRequest,
    TagEmbedResponse,
)
from app.repositories.base import (
    AgentRepository,
    TagCategoryRepository,
    TagRepository,
    AgentTagRepository,
    SessionRepository,
    MatchResultRepository,
    UserTagPreferenceRepository,
)
from app.core.deps import (
    get_agent_repo,
    get_tag_category_repo,
    get_tag_repo,
    get_agent_tag_repo,
    get_session_repo,
    get_match_result_repo,
    get_user_tag_pref_repo,
)
from app.models.tag import Tag
from app.services.plaza_service import get_tag_catalog, search_plaza, embed_tag_vectors
from app.services.llm import get_embedding
import re
from uuid import uuid4 as _uuid4

router = APIRouter()


@router.get("/tags", response_model=List[TagCategoryRead])
async def list_tags(
    cat_repo: TagCategoryRepository = Depends(get_tag_category_repo),
    tag_repo: TagRepository = Depends(get_tag_repo),
):
    """Return agent-scope tag catalog grouped by category."""
    return await get_tag_catalog(cat_repo, tag_repo, scope="agent")


@router.post("/tags", response_model=TagRead)
async def create_tag(
    body: TagCreate,
    tag_repo: TagRepository = Depends(get_tag_repo),
    cat_repo: TagCategoryRepository = Depends(get_tag_category_repo),
):
    """Create a new user-defined tag in an agent-scope category."""
    cats = await cat_repo.list_active_by_scope("agent")
    if not any(c.id == body.category_id for c in cats):
        raise HTTPException(status_code=400, detail="Category not found or not agent-scope")

    slug = re.sub(r"[^a-z0-9]+", "-", body.name.lower()).strip("-")
    if not slug:
        slug = f"user-tag-{_uuid4().hex[:8]}"
    existing = await tag_repo.get_by_slug(slug)
    if existing:
        if not existing.embedding:
            existing.embedding = await get_embedding(existing.name)
            await tag_repo.update(existing)
        return TagRead(id=str(existing.id), name=existing.name, slug=existing.slug, children=[])

    tag = Tag(
        category_id=body.category_id,
        name=body.name,
        slug=slug,
        sort_order=999,
        is_active=True,
        is_user_defined=True,
    )
    tag = await tag_repo.create(tag)
    tag.embedding = await get_embedding(tag.name)
    tag = await tag_repo.update(tag)
    return TagRead(id=str(tag.id), name=tag.name, slug=tag.slug, children=[])


@router.post("/tags/embed", response_model=TagEmbedResponse)
async def embed_tags(
    body: TagEmbedRequest,
    tag_repo: TagRepository = Depends(get_tag_repo),
):
    """Batch compute tag embeddings (missing only, or all if force_all)."""
    n = await embed_tag_vectors(tag_repo, force_all=body.force_all)
    return TagEmbedResponse(updated=n)


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
    pref_repo: UserTagPreferenceRepository = Depends(get_user_tag_pref_repo),
):
    """Hybrid search for plaza agents with match status and user preferences."""
    parsed_tag_ids = None
    if tag_ids:
        parsed_tag_ids = [
            UUID(tid.strip()) for tid in tag_ids.split(",") if tid.strip()
        ]

    # Load user tag preferences
    prefs = await pref_repo.get_by_user(user_id)
    liked = {p.tag_id for p in prefs if p.preference == "like"}
    disliked = {p.tag_id for p in prefs if p.preference == "dislike"}

    # When the user explicitly selects tag filters, show all matching agents
    # (including disliked) so the filter result is complete.
    # Dislike filtering only applies to the default browsing view.
    has_explicit_filters = bool(parsed_tag_ids)

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
        liked_tag_ids=liked or None,
        disliked_tag_ids=None if has_explicit_filters else (disliked or None),
    )
    return result
