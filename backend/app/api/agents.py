from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.models.agent import Agent, AgentStatus
from app.schemas.agent import AgentCreate, AgentRead
from app.agent.persona import create_agent
from app.repositories.base import AgentRepository, UserRepository
from app.core.deps import get_agent_repo, get_user_repo

router = APIRouter()

@router.post("/", response_model=AgentRead)
async def create_new_agent(
    agent_in: AgentCreate, 
    agent_repo: AgentRepository = Depends(get_agent_repo),
    user_repo: UserRepository = Depends(get_user_repo)
):
    agent = await create_agent(agent_repo, user_repo, agent_in.user_id, agent_in.name)
    return agent

@router.get("/", response_model=List[AgentRead])
async def list_agents(
    user_id: UUID, 
    repo: AgentRepository = Depends(get_agent_repo)
):
    return await repo.list_by_user(user_id)

@router.post("/{id}/match", response_model=AgentRead)
async def start_matching(id: UUID, repo: AgentRepository = Depends(get_agent_repo)):
    agent = await repo.update_status(id, AgentStatus.MATCHING)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
