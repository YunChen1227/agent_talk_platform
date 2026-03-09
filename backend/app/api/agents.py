from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.models.agent import Agent, AgentStatus
from app.models.session import SessionStatus, MatchResult
from app.models.enums import Verdict
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.agent.persona import create_agent
from app.repositories.base import AgentRepository, UserRepository, SessionRepository, MessageRepository, MatchResultRepository
from app.core.deps import get_agent_repo, get_user_repo, get_session_repo, get_message_repo, get_match_result_repo

router = APIRouter()

@router.post("/", response_model=AgentRead)
async def create_new_agent(
    agent_in: AgentCreate, 
    agent_repo: AgentRepository = Depends(get_agent_repo),
    user_repo: UserRepository = Depends(get_user_repo)
):
    # Pass optional fields to create_agent
    agent = await create_agent(
        agent_repo, 
        user_repo, 
        agent_in.user_id, 
        agent_in.name,
        description=agent_in.description,
        system_prompt=agent_in.system_prompt,
        opening_remark=agent_in.opening_remark
    )
    return agent

@router.get("/", response_model=List[AgentRead])
async def list_agents(
    user_id: UUID, 
    repo: AgentRepository = Depends(get_agent_repo)
):
    return await repo.list_by_user(user_id)

@router.get("/{id}", response_model=AgentRead)
async def get_agent(
    id: UUID, 
    repo: AgentRepository = Depends(get_agent_repo)
):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{id}", response_model=AgentRead)
async def update_agent(
    id: UUID,
    agent_in: AgentUpdate,
    repo: AgentRepository = Depends(get_agent_repo)
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
        
    updated_agent = await repo.update(agent)
    return updated_agent

@router.delete("/{id}", status_code=204)
async def delete_agent(
    id: UUID,
    repo: AgentRepository = Depends(get_agent_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repo)
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

    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return

@router.post("/{id}/match", response_model=AgentRead)
async def start_matching(id: UUID, repo: AgentRepository = Depends(get_agent_repo)):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.status == AgentStatus.MATCHING:
        raise HTTPException(status_code=400, detail=f"Agent is currently {agent.status}, cannot start matching")
    agent = await repo.update_status(id, AgentStatus.MATCHING)
    return agent


@router.post("/{id}/stop-matching", response_model=AgentRead)
async def stop_matching(id: UUID, repo: AgentRepository = Depends(get_agent_repo)):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.status != AgentStatus.MATCHING:
        raise HTTPException(status_code=400, detail=f"Agent is currently {agent.status}, cannot stop matching")
    agent = await repo.update_status(id, AgentStatus.IDLE)
    return agent

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
