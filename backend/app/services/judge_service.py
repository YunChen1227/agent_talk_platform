from uuid import UUID
from app.models.session import SessionStatus, MatchResult, Verdict
from app.services.llm import judge_conversation
from app.repositories.base import SessionRepository, MessageRepository, AgentRepository, MatchResultRepository

async def audit_session(session_repo: SessionRepository, message_repo: MessageRepository, agent_repo: AgentRepository, match_result_repo: MatchResultRepository, session_id: UUID):
    session_obj = await session_repo.get(session_id)
    if not session_obj or session_obj.status != SessionStatus.ACTIVE:
        return

    history = await message_repo.get_history(session_id)
    if len(history) < 6:
        return

    # Set status to JUDGING to prevent agents from talking
    session_obj.status = SessionStatus.JUDGING
    await session_repo.update(session_obj)

    try:
        # Format history for Judge
        llm_history = []
        agent_a = await agent_repo.get(session_obj.agent_a_id)
        agent_b = await agent_repo.get(session_obj.agent_b_id)
        
        for msg in history:
            role = f"Agent {agent_a.name}" if msg.sender_id == agent_a.id else f"Agent {agent_b.name}"
            llm_history.append({"role": role, "content": msg.content})
            
        result = await judge_conversation(llm_history)
        
        verdict = result.get("verdict")
        
        if verdict in ["CONSENSUS", "DEADLOCK"]:
            session_obj.status = SessionStatus.COMPLETED if verdict == "CONSENSUS" else SessionStatus.TERMINATED
            await session_repo.update(session_obj)
            
            match_result = MatchResult(
                session_id=session_id,
                verdict=Verdict(verdict),
                summary=result.get("summary"),
                reason=result.get("reason"),
                final_outcome=result.get("final_outcome"),
            )
            await match_result_repo.create(match_result)
            
        else:
            # Revert to ACTIVE
            session_obj.status = SessionStatus.ACTIVE
            await session_repo.update(session_obj)
            
    except Exception as e:
        print(f"Error in audit_session: {e}")
        # Revert to ACTIVE on error
        session_obj.status = SessionStatus.ACTIVE
        await session_repo.update(session_obj)
