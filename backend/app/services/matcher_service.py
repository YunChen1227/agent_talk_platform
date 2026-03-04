from typing import List, Tuple
from uuid import UUID
from app.models.session import Session, SessionStatus
from app.models.message import Message
from app.repositories.base import MatcherRepository, SessionRepository, AgentRepository, MessageRepository

from app.core.config import settings
from app.services.llm import check_match_with_llm

async def scan_and_match(
    matcher_repo: MatcherRepository, 
    session_repo: SessionRepository, 
    agent_repo: AgentRepository,
    message_repo: MessageRepository,
    threshold: float = 0.2
) -> List[Tuple[UUID, UUID]]:
    # In dev mode, we use mock embeddings which are random.
    # Random vectors have distance ~1.0, so default threshold 0.2 is too strict.
    # We relax it to 2.0 to allow all matches, then filter by LLM.
    if settings.MODE == "dev":
        threshold = 2.0

    matched_pairs = await matcher_repo.find_matches(threshold)
    
    final_pairs = []
    for agent_id, candidate_id in matched_pairs:
        # If LLM matcher is enabled (e.g. in dev mode), verify the match
        if settings.USE_LLM_MATCHER:
            agent_a = await agent_repo.get(agent_id)
            agent_b = await agent_repo.get(candidate_id)
            
            if agent_a and agent_b:
                # We use system_prompt as a proxy for demand since it contains it
                # "System prompt for demand: ..."
                is_compatible = await check_match_with_llm(agent_a.system_prompt, agent_b.system_prompt)
                if not is_compatible:
                    print(f"LLM rejected match between {agent_a.name} and {agent_b.name}")
                    continue
                print(f"LLM approved match between {agent_a.name} and {agent_b.name}")

        new_session = Session(
            agent_a_id=agent_id,
            agent_b_id=candidate_id,
            status=SessionStatus.ACTIVE
        )
        await session_repo.create(new_session)
        
        # Add opening remarks
        agent_a = await agent_repo.get(agent_id)
        agent_b = await agent_repo.get(candidate_id)
        
        if agent_a and agent_a.opening_remark:
            msg_a = Message(
                session_id=new_session.id,
                sender_id=agent_a.id,
                content=agent_a.opening_remark
            )
            await message_repo.create(msg_a)
            
        if agent_b and agent_b.opening_remark:
            msg_b = Message(
                session_id=new_session.id,
                sender_id=agent_b.id,
                content=agent_b.opening_remark
            )
            await message_repo.create(msg_b)
            
        final_pairs.append((agent_id, candidate_id))
        
    return final_pairs
