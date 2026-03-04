from uuid import UUID
from typing import Union, List
from app.models.agent import Agent, AgentStatus
from app.models.user import User
from app.repositories.base import AgentRepository, UserRepository
from app.services.llm import get_random_client
import google.generativeai as genai

async def generate_system_prompt(user_demand: str, user_tags: List[str]) -> str:
    client_info = get_random_client()
    if not client_info:
        return f"System prompt for demand: {user_demand}"

    prompt = f"""
    You are an AI agent representing a user with the following demand: "{user_demand}".
    Key tags: {', '.join(user_tags)}.
    
    Your goal is to negotiate with other agents to find the best match for your user.
    - Be professional but firm on your user's requirements.
    - Ask clarifying questions if the other party's offer is vague.
    - Do not agree to anything that contradicts the user's core demand.
    - If the match seems good, express interest and try to reach a consensus.
    
    Output your system prompt instructions for yourself.
    """
    
    try:
        if client_info["provider"] == "gemini":
            model = genai.GenerativeModel(client_info["model"])
            response = await model.generate_content_async(prompt)
            return response.text.strip()
        else:
            client = client_info["client"]
            response = await client.chat.completions.create(
                model="gpt-4" if client_info["provider"] == "openai" else client_info["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating system prompt: {e}")
        return f"System prompt for demand: {user_demand}"

async def create_agent(agent_repo: AgentRepository, user_repo: UserRepository, user_id: Union[str, UUID], name: str) -> Agent:
    if isinstance(user_id, str):
        user_id = UUID(user_id)
        
    user = await user_repo.get(user_id)
    if not user:
        raise ValueError("User not found")
        
    system_prompt = await generate_system_prompt(user.raw_demand, user.tags)
    
    agent = Agent(
        user_id=user_id,
        name=name,
        system_prompt=system_prompt,
        status=AgentStatus.IDLE
    )
    return await agent_repo.create(agent)
