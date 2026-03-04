from typing import List, Dict
from uuid import UUID
from app.models.message import Message
from app.models.session import Session, SessionStatus
from app.models.agent import Agent
from app.services.llm import generate_response
from app.repositories.base import SessionRepository, MessageRepository, AgentRepository

async def process_turn(session_repo: SessionRepository, message_repo: MessageRepository, agent_repo: AgentRepository, session_id: UUID):
    session_obj = await session_repo.get(session_id)
    if not session_obj or session_obj.status != SessionStatus.ACTIVE:
        return

    history = await message_repo.get_history(session_id)
    
    # Determine whose turn it is
    if not history:
        current_agent_id = session_obj.agent_a_id
        other_agent_id = session_obj.agent_b_id
    else:
        last_sender_id = history[-1].sender_id
        if last_sender_id == session_obj.agent_a_id:
            current_agent_id = session_obj.agent_b_id
            other_agent_id = session_obj.agent_a_id
        else:
            current_agent_id = session_obj.agent_a_id
            other_agent_id = session_obj.agent_b_id
            
    current_agent = await agent_repo.get(current_agent_id)
    
    # Format history for LLM
    llm_history = []
    for msg in history:
        role = "assistant" if msg.sender_id == current_agent_id else "user"
        llm_history.append({"role": role, "content": msg.content})
        
    # Generate response
    response_content = await generate_response(current_agent.system_prompt, llm_history)
    
    # Save message
    message = Message(session_id=session_id, sender_id=current_agent_id, content=response_content)
    await message_repo.create(message)
