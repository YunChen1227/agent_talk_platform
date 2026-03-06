from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_session_repo, get_message_repo, get_agent_repo, get_match_result_repo
from app.repositories.base import SessionRepository, MessageRepository, AgentRepository, MatchResultRepository
from app.models.session import SessionStatus

router = APIRouter()


@router.get("/active")
async def get_active_sessions(
    user_id: UUID,
    session_repo: SessionRepository = Depends(get_session_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    """List all active sessions (ACTIVE/JUDGING) where the user's agents participate."""
    my_agents = await agent_repo.list_by_user(user_id)
    paired_agents = [a for a in my_agents if a.status == "PAIRED"]
    if not paired_agents:
        return []

    active_statuses = (SessionStatus.ACTIVE, SessionStatus.JUDGING)
    result = []
    seen = set()

    for agent in paired_agents:
        session_obj = await session_repo.find_by_agent(agent.id)
        if not session_obj or session_obj.status not in active_statuses:
            continue
        if session_obj.id in seen:
            continue
        seen.add(session_obj.id)
        other_id = session_obj.agent_b_id if agent.id == session_obj.agent_a_id else session_obj.agent_a_id
        other_agent = await agent_repo.get(other_id)
        result.append({
            "session_id": str(session_obj.id),
            "my_agent_name": agent.name,
            "my_agent_id": str(agent.id),
            "opponent_agent_name": other_agent.name if other_agent else "Unknown",
            "opponent_agent_id": str(other_id),
            "status": session_obj.status,
        })

    return result


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
