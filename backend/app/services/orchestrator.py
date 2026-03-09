import asyncio
from app.agent.conversation import process_turn
from app.services.judge_service import audit_session
from app.services.matcher_service import scan_and_match
from app.repositories.base import SessionRepository, MessageRepository, AgentRepository, MatcherRepository, MatchResultRepository
from app.core.config import settings

SESSION_STEP_TIMEOUT_SECONDS = getattr(settings, "SESSION_STEP_TIMEOUT_SECONDS", 45)


async def _run_session_step(
    session_repo: SessionRepository,
    message_repo: MessageRepository,
    agent_repo: AgentRepository,
    match_result_repo: MatchResultRepository,
    session_id,
):
    try:
        # Prevent one slow LLM call from blocking all other sessions.
        await asyncio.wait_for(
            process_turn(session_repo, message_repo, agent_repo, session_id),
            timeout=SESSION_STEP_TIMEOUT_SECONDS
        )
        await asyncio.wait_for(
            audit_session(session_repo, message_repo, agent_repo, match_result_repo, session_id),
            timeout=SESSION_STEP_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        print(f"Session step timed out: {session_id}")
    except Exception as e:
        print(f"Session step failed {session_id}: {e}")

async def run_orchestrator(
    session_repo: SessionRepository,
    agent_repo: AgentRepository,
    matcher_repo: MatcherRepository,
    message_repo: MessageRepository,
    match_result_repo: MatchResultRepository
):
    # 1. Matcher
    # Pass agent_repo to scan_and_match for LLM verification
    await scan_and_match(matcher_repo, session_repo, agent_repo, message_repo)
    
    # 2. Process Active Sessions
    active_sessions = await session_repo.list_active()
    if not active_sessions:
        return

    await asyncio.gather(*[
        _run_session_step(
            session_repo,
            message_repo,
            agent_repo,
            match_result_repo,
            chat_session.id
        )
        for chat_session in active_sessions
    ])
