from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.models.agent import Agent, AgentStatus
from app.models.session import SessionStatus, MatchResult
from app.models.enums import Verdict
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.agent.persona import create_agent
from app.repositories.base import AgentRepository, UserRepository, SessionRepository, MessageRepository, MatchResultRepository, TagRepository, AgentTagRepository, EmbeddingRepository
from app.core.deps import get_agent_repo, get_user_repo, get_session_repo, get_message_repo, get_match_result_repo, get_tag_repo, get_agent_tag_repo, get_embedding_repo

router = APIRouter()


async def _enrich_with_catalog_tags(
    agent: Agent,
    agent_tag_repo: AgentTagRepository,
) -> dict:
    """Convert Agent model to dict with structured catalog_tags."""
    data = {
        "id": agent.id,
        "name": agent.name,
        "status": agent.status,
        "system_prompt": agent.system_prompt,
        "opening_remark": agent.opening_remark,
        "tags": agent.tags,
        "linked_product_ids": agent.linked_product_ids,
        "linked_skill_ids": agent.linked_skill_ids,
    }
    tags = await agent_tag_repo.get_tags_for_agent(agent.id)
    data["catalog_tags"] = [
        {
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "category_id": str(t.category_id),
            "parent_id": str(t.parent_id) if t.parent_id else None,
        }
        for t in tags
    ]
    return data


@router.post("/", response_model=AgentRead)
async def create_new_agent(
    agent_in: AgentCreate,
    agent_repo: AgentRepository = Depends(get_agent_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    tag_repo: TagRepository = Depends(get_tag_repo),
    agent_tag_repo: AgentTagRepository = Depends(get_agent_tag_repo),
    embedding_repo: EmbeddingRepository = Depends(get_embedding_repo),
):
    agent = await create_agent(
        agent_repo,
        user_repo,
        agent_in.user_id,
        agent_in.name,
        description=agent_in.description,
        system_prompt=agent_in.system_prompt,
        opening_remark=agent_in.opening_remark,
        linked_product_ids=agent_in.linked_product_ids,
        linked_skill_ids=agent_in.linked_skill_ids,
        tag_repo=tag_repo,
        agent_tag_repo=agent_tag_repo,
        tag_ids=agent_in.tag_ids,
        embedding_repo=embedding_repo,
    )
    return await _enrich_with_catalog_tags(agent, agent_tag_repo)

@router.get("/", response_model=List[AgentRead])
async def list_agents(
    user_id: UUID,
    repo: AgentRepository = Depends(get_agent_repo),
    agent_tag_repo: AgentTagRepository = Depends(get_agent_tag_repo),
):
    agents = await repo.list_by_user(user_id)
    return [await _enrich_with_catalog_tags(a, agent_tag_repo) for a in agents]


@router.get("/plaza", response_model=List[AgentRead])
async def list_plaza_agents(
    user_id: UUID,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    repo: AgentRepository = Depends(get_agent_repo),
):
    """List all agents except the current user's; optional filter by tags (comma-separated) and name search (substring)."""
    all_agents = await repo.list_all()
    candidates = [a for a in all_agents if a.user_id != user_id]
    if tags:
        tag_set = {t.strip().lower() for t in tags.split(",") if t.strip()}
        if tag_set:
            candidates = [a for a in candidates if a.tags and any(t.lower() in tag_set for t in a.tags)]
    if search and search.strip():
        q = search.strip().lower()
        candidates = [a for a in candidates if q in (a.name or "").lower()]
    return candidates


@router.get("/{id}", response_model=AgentRead)
async def get_agent(
    id: UUID,
    repo: AgentRepository = Depends(get_agent_repo),
    agent_tag_repo: AgentTagRepository = Depends(get_agent_tag_repo),
):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await _enrich_with_catalog_tags(agent, agent_tag_repo)

@router.put("/{id}", response_model=AgentRead)
async def update_agent(
    id: UUID,
    agent_in: AgentUpdate,
    repo: AgentRepository = Depends(get_agent_repo),
    tag_repo: TagRepository = Depends(get_tag_repo),
    agent_tag_repo: AgentTagRepository = Depends(get_agent_tag_repo),
):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent_in.name is not None:
        agent.name = agent_in.name
    if agent_in.system_prompt is not None:
        agent.system_prompt = agent_in.system_prompt
    if agent_in.opening_remark is not None:
        agent.opening_remark = agent_in.opening_remark
    if agent_in.linked_product_ids is not None:
        agent.linked_product_ids = agent_in.linked_product_ids
    if agent_in.linked_skill_ids is not None:
        agent.linked_skill_ids = agent_in.linked_skill_ids

    if agent_in.tag_ids is not None:
        agent_tags = await tag_repo.list_active_by_scope("agent")
        valid_ids = {t.id for t in agent_tags}
        filtered_ids = [tid for tid in agent_in.tag_ids if tid in valid_ids]
        await agent_tag_repo.set_tags(id, filtered_ids)

    updated_agent = await repo.update(agent)

    final_tags = await agent_tag_repo.get_tags_for_agent(id)
    updated_agent.tags = [t.name for t in final_tags]
    updated_agent = await repo.update(updated_agent)

    return await _enrich_with_catalog_tags(updated_agent, agent_tag_repo)

@router.delete("/{id}", status_code=204)
async def delete_agent(
    id: UUID,
    repo: AgentRepository = Depends(get_agent_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repo),
    embedding_repo: EmbeddingRepository = Depends(get_embedding_repo),
):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    sessions = await session_repo.find_all_by_agent(id)
    for session_obj in sessions:
        if session_obj.status not in (SessionStatus.ACTIVE, SessionStatus.JUDGING):
            continue

        session_obj.status = SessionStatus.TERMINATED
        await session_repo.update(session_obj)

        existing_result = await match_result_repo.get_by_session_id(session_obj.id)
        if existing_result:
            continue

        result = MatchResult(
            session_id=session_obj.id,
            verdict=Verdict.DEADLOCK,
            summary="Agent was deleted by user.",
            reason="Agent deletion"
        )
        await match_result_repo.create(result)

    await embedding_repo.delete(str(id))

    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return

@router.post("/{id}/match", response_model=AgentRead)
async def start_matching(
    id: UUID,
    repo: AgentRepository = Depends(get_agent_repo),
    agent_tag_repo: AgentTagRepository = Depends(get_agent_tag_repo),
):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.status == AgentStatus.MATCHING:
        raise HTTPException(status_code=400, detail=f"Agent is currently {agent.status}, cannot start matching")
    agent = await repo.update_status(id, AgentStatus.MATCHING)
    return await _enrich_with_catalog_tags(agent, agent_tag_repo)


@router.post("/{id}/stop-matching", response_model=AgentRead)
async def stop_matching(
    id: UUID,
    repo: AgentRepository = Depends(get_agent_repo),
    agent_tag_repo: AgentTagRepository = Depends(get_agent_tag_repo),
):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.status != AgentStatus.MATCHING:
        raise HTTPException(status_code=400, detail=f"Agent is currently {agent.status}, cannot stop matching")
    agent = await repo.update_status(id, AgentStatus.IDLE)
    return await _enrich_with_catalog_tags(agent, agent_tag_repo)

@router.get("/{id}/result")
async def get_agent_result(
    id: UUID,
    session_id: Optional[UUID] = None,
    agent_repo: AgentRepository = Depends(get_agent_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    agent = await agent_repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    session_obj = await session_repo.get(session_id) if session_id else await session_repo.find_by_agent(id)
    if not session_obj:
        return {"status": agent.status, "session": None}
    if session_obj.agent_a_id != id and session_obj.agent_b_id != id:
        raise HTTPException(status_code=400, detail="Session does not belong to this agent")

    other_agent_id = session_obj.agent_b_id if session_obj.agent_a_id == id else session_obj.agent_a_id
    other_agent = await agent_repo.get(other_agent_id)

    history = await message_repo.get_history(session_obj.id)
    messages = [
        {"sender": "self" if m.sender_id == id else "other", "content": m.content, "timestamp": str(m.timestamp)}
        for m in history
    ]

    result = await match_result_repo.get_by_session_id(session_obj.id)

    contact = None
    my_contact_shared = False
    other_agent_name = other_agent.name if other_agent else None
    is_agent_a = session_obj.agent_a_id == id
    if result and result.verdict == Verdict.CONSENSUS:
        my_contact_shared = result.agent_a_contact_shared if is_agent_a else result.agent_b_contact_shared
        other_contact_shared = result.agent_b_contact_shared if is_agent_a else result.agent_a_contact_shared
        if other_contact_shared and other_agent:
            other_user = await user_repo.get(other_agent.user_id)
            if other_user:
                contact = other_user.contact

    return {
        "status": agent.status,
        "session": {
            "id": str(session_obj.id),
            "status": session_obj.status,
            "created_at": str(session_obj.created_at),
        },
        "other_agent_name": other_agent_name,
        "messages": messages,
        "result": {
            "verdict": result.verdict,
            "summary": result.summary,
            "reason": result.reason,
            "final_outcome": result.final_outcome,
        } if result else None,
        "contact": contact,
        "my_contact_shared": my_contact_shared,
    }


@router.post("/{id}/share-contact")
async def share_contact(
    id: UUID,
    session_id: Optional[UUID] = None,
    agent_repo: AgentRepository = Depends(get_agent_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repo),
):
    agent = await agent_repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    session_obj = await session_repo.get(session_id) if session_id else await session_repo.find_by_agent(id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.agent_a_id != id and session_obj.agent_b_id != id:
        raise HTTPException(status_code=400, detail="Session does not belong to this agent")

    result = await match_result_repo.get_by_session_id(session_obj.id)
    if not result:
        raise HTTPException(status_code=400, detail="No match result yet")

    if result.verdict != Verdict.CONSENSUS:
        raise HTTPException(status_code=400, detail="Contact sharing is only available after CONSENSUS")

    is_agent_a = session_obj.agent_a_id == id
    if is_agent_a:
        result.agent_a_contact_shared = True
        my_contact_shared = result.agent_a_contact_shared
    else:
        result.agent_b_contact_shared = True
        my_contact_shared = result.agent_b_contact_shared

    await match_result_repo.update(result)

    return {
        "ok": True,
        "my_contact_shared": my_contact_shared,
    }
