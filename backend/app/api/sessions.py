from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_session_repo, get_message_repo, get_agent_repo, get_match_result_repo
from app.repositories.base import SessionRepository, MessageRepository, AgentRepository, MatchResultRepository
from app.models.session import Session, SessionStatus, MatchResult
from app.models.message import Message
from app.models.enums import Verdict
from app.models.agent import Agent
from app.schemas.session import DirectSessionCreate

router = APIRouter()


@router.get("/active")
async def get_active_sessions(
    user_id: UUID,
    session_repo: SessionRepository = Depends(get_session_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    """List all active sessions (ACTIVE/JUDGING) where the user's agents participate."""
    my_agents = await agent_repo.list_by_user(user_id)
    if not my_agents:
        return []

    active_statuses = (SessionStatus.ACTIVE, SessionStatus.JUDGING)
    result = []
    seen = set()
    my_agent_map = {a.id: a for a in my_agents}

    for my_agent in my_agents:
        sessions = await session_repo.find_all_by_agent(my_agent.id)
        for session_obj in sessions:
            if session_obj.status not in active_statuses:
                continue
            if session_obj.id in seen:
                continue
            seen.add(session_obj.id)

            my_agent_id = session_obj.agent_a_id if session_obj.agent_a_id in my_agent_map else session_obj.agent_b_id
            other_id = session_obj.agent_b_id if my_agent_id == session_obj.agent_a_id else session_obj.agent_a_id
            other_agent = await agent_repo.get(other_id)
            owner_agent = my_agent_map.get(my_agent_id)
            result.append({
                "session_id": str(session_obj.id),
                "my_agent_name": owner_agent.name if owner_agent else "Unknown",
                "my_agent_id": str(my_agent_id),
                "opponent_agent_name": other_agent.name if other_agent else "Unknown",
                "opponent_agent_id": str(other_id),
                "status": session_obj.status,
            })

    return result


@router.get("/completed")
async def get_completed_sessions(
    user_id: UUID,
    session_repo: SessionRepository = Depends(get_session_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repo),
):
    """List all completed/terminated sessions where the user's agents participate."""
    my_agents = await agent_repo.list_by_user(user_id)
    if not my_agents:
        return []

    completed_statuses = (SessionStatus.COMPLETED, SessionStatus.TERMINATED)
    result = []
    seen = set()
    my_agent_map = {a.id: a for a in my_agents}

    for my_agent in my_agents:
        sessions = await session_repo.find_all_by_agent(my_agent.id)
        for session_obj in sessions:
            if session_obj.status not in completed_statuses:
                continue
            if session_obj.id in seen:
                continue
            seen.add(session_obj.id)

            my_agent_id = session_obj.agent_a_id if session_obj.agent_a_id in my_agent_map else session_obj.agent_b_id
            other_id = session_obj.agent_b_id if my_agent_id == session_obj.agent_a_id else session_obj.agent_a_id
            other_agent = await agent_repo.get(other_id)
            owner_agent = my_agent_map.get(my_agent_id)
            match_result = await match_result_repo.get_by_session_id(session_obj.id)

            result.append({
                "session_id": str(session_obj.id),
                "my_agent_name": owner_agent.name if owner_agent else "Unknown",
                "my_agent_id": str(my_agent_id),
                "opponent_agent_name": other_agent.name if other_agent else "Unknown",
                "opponent_agent_id": str(other_id),
                "status": session_obj.status,
                "verdict": match_result.verdict if match_result else None,
            })

    return result


@router.post("/direct")
async def create_direct_session(
    body: DirectSessionCreate,
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    """Create a direct session between two agents (e.g. from Agent Plaza). Validates both exist, different users, no prior session."""
    my_agent = await agent_repo.get(body.my_agent_id)
    target_agent = await agent_repo.get(body.target_agent_id)
    if not my_agent:
        raise HTTPException(status_code=404, detail="My agent not found")
    if not target_agent:
        raise HTTPException(status_code=404, detail="Target agent not found")
    if my_agent.user_id == target_agent.user_id:
        raise HTTPException(status_code=400, detail="Cannot start chat with your own agent")
    # Dedup: any prior session between this pair
    my_sessions = await session_repo.find_all_by_agent(body.my_agent_id)
    for s in my_sessions:
        if s.agent_a_id == body.target_agent_id or s.agent_b_id == body.target_agent_id:
            raise HTTPException(status_code=400, detail="You have already had a conversation with this agent")
    session = Session(
        agent_a_id=body.my_agent_id,
        agent_b_id=body.target_agent_id,
        status=SessionStatus.ACTIVE,
    )
    session = await session_repo.create(session)
    if my_agent.opening_remark:
        msg_a = Message(session_id=session.id, sender_id=my_agent.id, content=my_agent.opening_remark)
        await message_repo.create(msg_a)
    if target_agent.opening_remark:
        msg_b = Message(session_id=session.id, sender_id=target_agent.id, content=target_agent.opening_remark)
        await message_repo.create(msg_b)
    return {
        "session_id": str(session.id),
        "my_agent_name": my_agent.name,
        "opponent_agent_name": target_agent.name,
        "status": session.status,
    }


@router.get("/{id}/latest-judge")
async def get_latest_judge(
    id: UUID,
    match_result_repo: MatchResultRepository = Depends(get_match_result_repo),
):
    """Get the latest judge result for a session. Returns null if none."""
    result = await match_result_repo.get_by_session_id(id)
    if not result:
        return None
    return {
        "verdict": result.verdict,
        "summary": result.summary,
        "reason": result.reason,
    }


@router.get("/{id}")
async def get_session_details(
    id: UUID, 
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo)
):
    session_obj = await session_repo.get(id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
        
    history = await message_repo.get_history(id)
    return {"session": session_obj, "history": history}


@router.post("/{id}/terminate")
async def terminate_session(
    id: UUID,
    user_id: UUID,
    session_repo: SessionRepository = Depends(get_session_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repo),
):
    """Manually terminate a session by user."""
    session_obj = await session_repo.get(id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1. Permission Check
    agent_a = await agent_repo.get(session_obj.agent_a_id)
    agent_b = await agent_repo.get(session_obj.agent_b_id)
    
    if not agent_a or not agent_b:
        raise HTTPException(status_code=500, detail="Agent data corrupted")

    if agent_a.user_id != user_id and agent_b.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to terminate this session")

    # 2. Status Check
    if session_obj.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Cannot terminate session in {session_obj.status} status. Wait for judgment if JUDGING.")

    # 3. Terminate
    session_obj.status = SessionStatus.TERMINATED
    await session_repo.update(session_obj)

    # Create Deadlock Result
    result = MatchResult(
        session_id=id,
        verdict=Verdict.DEADLOCK,
        summary="User manually terminated the conversation.",
        reason="User termination"
    )
    await match_result_repo.create(result)

    return {"status": "terminated"}
