from uuid import UUID
from typing import Tuple, List, Union
from app.models.agent import Agent, AgentStatus
from app.models.user import User
from app.repositories.base import AgentRepository, UserRepository
from app.services.llm import get_random_client
import google.generativeai as genai

async def generate_system_prompt(user_demand: str, user_tags: List[str]) -> Tuple[str, str]:
    client_info = get_random_client()
    if not client_info:
        return f"System prompt for demand: {user_demand}", "Hello! I am looking for a match."

    prompt = f"""
    You are an AI agent representing a user with the following demand: "{user_demand}".
    Key tags: {', '.join(user_tags)}.
    
    Your goal is to negotiate with other agents to find the best match for your user.
    
    Please generate two things:
    1. A comprehensive **System Prompt** for yourself to act as this agent.
    2. A short **Opening Remark** (1-2 sentences) to start a conversation with another agent.
    
    The system prompt should include:
    - **Role Definition**: Define your persona based on the demand.
    - **Core Objective**: Clearly state what you want to achieve.
    - **Negotiation Strategy**: How will you approach the negotiation?
    - **Constraints**: What are your deal-breakers?
    - **Tone and Style**: How should you speak?
    
    Output format:
    ---SYSTEM_PROMPT---
    (Your generated system prompt here)
    ---OPENING_REMARK---
    (Your generated opening remark here)
    """
    
    try:
        content = ""
        if client_info["provider"] == "gemini":
            model = genai.GenerativeModel(client_info["model"])
            response = await model.generate_content_async(prompt)
            content = response.text.strip()
        else:
            client = client_info["client"]
            response = await client.chat.completions.create(
                model="gpt-4" if client_info["provider"] == "openai" else client_info["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            
        # Parse output
        parts = content.split("---OPENING_REMARK---")
        if len(parts) == 2:
            sys_prompt = parts[0].replace("---SYSTEM_PROMPT---", "").strip()
            opening = parts[1].strip()
            return sys_prompt, opening
        else:
            return content, "Hello! I am ready to negotiate."
            
    except Exception as e:
        print(f"Error generating system prompt: {e}")
        return f"System prompt for demand: {user_demand}", "Hello!"

async def create_agent(agent_repo: AgentRepository, user_repo: UserRepository, user_id: Union[str, UUID], name: str) -> Agent:
    if isinstance(user_id, str):
        user_id = UUID(user_id)
        
    user = await user_repo.get(user_id)
    if not user:
        raise ValueError("User not found")
        
    system_prompt, opening_remark = await generate_system_prompt(user.raw_demand, user.tags)
    
    agent = Agent(
        user_id=user_id,
        name=name,
        system_prompt=system_prompt,
        opening_remark=opening_remark,
        status=AgentStatus.IDLE
    )
    return await agent_repo.create(agent)
