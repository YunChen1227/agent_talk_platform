from uuid import UUID
from typing import Union
from app.models.agent import Agent, AgentStatus
from app.models.user import User
from app.services.llm import generate_system_prompt
from app.repositories.base import AgentRepository, UserRepository

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
