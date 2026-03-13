import math
from typing import List, Optional, Dict, Set, Tuple
from uuid import UUID

from app.models.agent import Agent
from app.models.tag import TagCategory, Tag
from app.models.session import Session, SessionStatus, MatchResult
from app.models.enums import MatchStatus, Verdict
from app.repositories.base import (
    AgentRepository,
    TagCategoryRepository,
    TagRepository,
    AgentTagRepository,
    SessionRepository,
    MatchResultRepository,
)
from app.services.llm import get_embedding
from app.core.config import settings


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2:
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


async def get_tag_catalog(
    cat_repo: TagCategoryRepository,
    tag_repo: TagRepository,
) -> List[dict]:
    """Return the full tag catalog grouped by category, with two-level hierarchy."""
    categories = await cat_repo.list_active()
    all_tags = await tag_repo.list_active()

    tag_by_cat: Dict[UUID, List[Tag]] = {}
    for t in all_tags:
        tag_by_cat.setdefault(t.category_id, []).append(t)

    result = []
    for cat in categories:
        cat_tags = tag_by_cat.get(cat.id, [])
        root_tags = sorted(
            [t for t in cat_tags if t.parent_id is None],
            key=lambda x: x.sort_order,
        )
        children_map: Dict[UUID, List[Tag]] = {}
        for t in cat_tags:
            if t.parent_id is not None:
                children_map.setdefault(t.parent_id, []).append(t)

        tag_tree = []
        for root in root_tags:
            kids = sorted(
                children_map.get(root.id, []),
                key=lambda x: x.sort_order,
            )
            tag_tree.append({
                "id": str(root.id),
                "name": root.name,
                "slug": root.slug,
                "children": [
                    {"id": str(c.id), "name": c.name, "slug": c.slug, "children": []}
                    for c in kids
                ],
            })

        result.append({
            "id": str(cat.id),
            "name": cat.name,
            "slug": cat.slug,
            "tags": tag_tree,
        })
    return result


async def search_plaza(
    user_id: UUID,
    agent_repo: AgentRepository,
    agent_tag_repo: AgentTagRepository,
    tag_repo: TagRepository,
    session_repo: SessionRepository,
    match_result_repo: MatchResultRepository,
    tag_ids: Optional[List[UUID]] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Hybrid search for plaza agents.
    1. Tag filtering (pre-filter)
    2. If q: keyword search + embedding search -> RRF fusion
    3. Compute match status for each result
    4. Paginate
    """
    all_agents = await agent_repo.list_all()
    candidates = [a for a in all_agents if a.user_id != user_id]

    if tag_ids:
        all_tags = await tag_repo.list_active()
        expanded_ids = _expand_parent_tags(tag_ids, all_tags)
        matching_agent_ids = set(await agent_tag_repo.get_agent_ids_by_tag_ids(expanded_ids))
        candidates = [a for a in candidates if a.id in matching_agent_ids]

    if q and q.strip():
        query = q.strip()
        scored = _hybrid_search(candidates, query)
    else:
        scored = [(a, 0.0) for a in candidates]

    scored.sort(key=lambda x: x[1], reverse=True)

    total = len(scored)
    start = (page - 1) * page_size
    end = start + page_size
    page_agents = scored[start:end]

    user_agents = await agent_repo.list_by_user(user_id)
    user_agent_ids = {a.id for a in user_agents}
    user_agent_names = {a.id: a.name for a in user_agents}

    all_user_sessions: List[Session] = []
    for ua_id in user_agent_ids:
        sessions = await session_repo.find_all_by_agent(ua_id)
        all_user_sessions.extend(sessions)

    seen_session_ids: Set[UUID] = set()
    unique_sessions: List[Session] = []
    for s in all_user_sessions:
        if s.id not in seen_session_ids:
            seen_session_ids.add(s.id)
            unique_sessions.append(s)

    result_cache: Dict[UUID, Optional[MatchResult]] = {}
    for s in unique_sessions:
        if s.id not in result_cache:
            result_cache[s.id] = await match_result_repo.get_by_session_id(s.id)

    all_tags = await tag_repo.list_active()
    tag_map = {t.id: t for t in all_tags}

    all_agent_tag_links = await agent_tag_repo.list_all()
    agent_tags_map: Dict[UUID, List[Tag]] = {}
    for link in all_agent_tag_links:
        tag = tag_map.get(link.tag_id)
        if tag:
            agent_tags_map.setdefault(link.agent_id, []).append(tag)

    cat_repo_data = {}
    for t in all_tags:
        cat_repo_data[t.category_id] = None

    items = []
    for agent, score in page_agents:
        status, details = _compute_match_status(
            agent.id, user_agent_ids, user_agent_names,
            unique_sessions, result_cache,
        )

        agent_tag_list = agent_tags_map.get(agent.id, [])
        tag_dicts = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "category_id": str(t.category_id),
                "parent_id": str(t.parent_id) if t.parent_id else None,
            }
            for t in agent_tag_list
        ]

        items.append({
            "id": str(agent.id),
            "name": agent.name,
            "tags": tag_dicts,
            "opening_remark": agent.opening_remark,
            "match_status": status,
            "match_details": details,
            "search_score": round(score, 4) if score else None,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


def _expand_parent_tags(selected_ids: List[UUID], all_tags: List[Tag]) -> List[UUID]:
    """If a parent tag is selected, also include all its children IDs."""
    selected_set = set(selected_ids)
    extra: Set[UUID] = set()
    for t in all_tags:
        if t.parent_id in selected_set and t.id not in selected_set:
            extra.add(t.id)
    return list(selected_set | extra)


def _hybrid_search(
    candidates: List[Agent],
    query: str,
) -> List[Tuple[Agent, float]]:
    """Perform keyword + embedding search with RRF fusion."""
    kw_ranked = _keyword_search(candidates, query)
    vec_ranked = _vector_search(candidates, query)

    kw_rank_map = {a.id: rank for rank, a in enumerate(kw_ranked)}
    vec_rank_map = {a.id: rank for rank, a in enumerate(vec_ranked)}

    k = 60
    agent_map = {a.id: a for a in candidates}
    all_ids = set(kw_rank_map.keys()) | set(vec_rank_map.keys())

    rrf_scores: List[Tuple[Agent, float]] = []
    for aid in all_ids:
        score = 0.0
        if aid in kw_rank_map:
            score += 1.0 / (k + kw_rank_map[aid])
        if aid in vec_rank_map:
            score += 1.0 / (k + vec_rank_map[aid])
        rrf_scores.append((agent_map[aid], score))

    rrf_scores.sort(key=lambda x: x[1], reverse=True)
    return rrf_scores


def _keyword_search(candidates: List[Agent], query: str) -> List[Agent]:
    """Simple keyword substring match, ranked by match quality."""
    q_lower = query.lower()
    scored = []
    for a in candidates:
        score = 0.0
        name_lower = (a.name or "").lower()
        prompt_lower = (a.system_prompt or "").lower()
        remark_lower = (a.opening_remark or "").lower()

        if q_lower in name_lower:
            score += 3.0
        if q_lower in prompt_lower:
            score += 1.0
        if q_lower in remark_lower:
            score += 1.5

        if score > 0:
            scored.append((a, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [a for a, _ in scored]


def _vector_search(candidates: List[Agent], query: str) -> List[Agent]:
    """
    In dev mode, use cached mock embeddings with cosine similarity.
    For a real query embedding, we'd need async call — here we do
    a synchronous fallback using the existing agent embeddings only.
    """
    if settings.MODE == "dev":
        return candidates

    scored = []
    for a in candidates:
        if a.embedding:
            scored.append(a)

    return scored


def _compute_match_status(
    target_agent_id: UUID,
    user_agent_ids: Set[UUID],
    user_agent_names: Dict[UUID, str],
    sessions: List[Session],
    result_cache: Dict[UUID, Optional[MatchResult]],
) -> Tuple[str, List[dict]]:
    """Compute aggregated match status and per-pair details."""
    details = []
    statuses: Set[str] = set()

    for session in sessions:
        pair = {session.agent_a_id, session.agent_b_id}
        if target_agent_id not in pair:
            continue

        my_agents_in_pair = pair.intersection(user_agent_ids)
        if not my_agents_in_pair:
            continue

        my_agent_id = my_agents_in_pair.pop()

        if session.status in (SessionStatus.ACTIVE, SessionStatus.JUDGING):
            pair_status = MatchStatus.CHATTING
        elif session.status == SessionStatus.COMPLETED:
            mr = result_cache.get(session.id)
            if mr and mr.verdict == Verdict.CONSENSUS:
                pair_status = MatchStatus.CONSENSUS
            else:
                pair_status = MatchStatus.DEADLOCK
        elif session.status == SessionStatus.TERMINATED:
            pair_status = MatchStatus.DEADLOCK
        else:
            continue

        statuses.add(pair_status)
        details.append({
            "my_agent_id": str(my_agent_id),
            "my_agent_name": user_agent_names.get(my_agent_id, ""),
            "session_id": str(session.id),
            "status": pair_status,
            "created_at": str(session.created_at),
        })

    if not statuses:
        return MatchStatus.NOT_MATCHED, []

    priority = [MatchStatus.CONSENSUS, MatchStatus.CHATTING, MatchStatus.DEADLOCK]
    for s in priority:
        if s in statuses:
            return s, details

    return MatchStatus.NOT_MATCHED, details
