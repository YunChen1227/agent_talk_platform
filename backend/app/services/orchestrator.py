import asyncio
from app.models.session import SessionStatus
from app.services.chat_service import process_turn
from app.services.judge_service import audit_session
from app.services.matcher_service import scan_and_match
from app.repositories.base import SessionRepository, MessageRepository, AgentRepository, MatcherRepository, MatchResultRepository

async def run_orchestrator(
    session_repo: SessionRepository,
    agent_repo: AgentRepository,
    matcher_repo: MatcherRepository,
    message_repo: MessageRepository,
    match_result_repo: MatchResultRepository
):
    # 1. Matcher
    # Pass agent_repo to scan_and_match for LLM verification
    await scan_and_match(matcher_repo, session_repo, agent_repo)
    
    # 2. Process Active Sessions
    active_sessions = await session_repo.list_active()
    
    for chat_session in active_sessions:
        # Agent turn
        await process_turn(session_repo, message_repo, agent_repo, chat_session.id)
        
        # Judge turn
        await audit_session(session_repo, message_repo, agent_repo, match_result_repo, chat_session.id)
