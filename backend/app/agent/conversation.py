from typing import List, Dict
from uuid import UUID
import google.generativeai as genai
from app.models.message import Message
from app.models.session import SessionStatus
from app.repositories.base import SessionRepository, MessageRepository, AgentRepository
from app.services.llm import get_random_client

async def generate_response(system_prompt: str, history: List[Dict[str, str]]) -> str:
    client_info = get_random_client()
    if not client_info:
        return f"Mock response based on history length {len(history)}"

    try:
        if client_info["provider"] == "gemini":
            gemini_history = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})
            
            model = genai.GenerativeModel(client_info["model"], system_instruction=system_prompt)
            
            if not gemini_history:
                 response = await model.generate_content_async("Hello!")
                 return response.text.strip()

            if gemini_history[-1]['role'] == 'user':
                last_msg = gemini_history.pop()
                chat = model.start_chat(history=gemini_history)
                response = await chat.send_message_async(last_msg['parts'][0])
                return response.text.strip()
            else:
                 chat = model.start_chat(history=gemini_history)
                 response = await chat.send_message_async("Please continue.")
                 return response.text.strip()
                 
        else:
            messages = [{"role": "system", "content": system_prompt}] + history
            client = client_info["client"]
            response = await client.chat.completions.create(
                model=client_info["model"],
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
            
    except Exception as e:
        print(f"Error generating response: {e}")
        return "..."

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
