from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.models.agent import Agent, AgentStatus
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
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

@router.get("/{id}", response_model=AgentRead)
async def get_agent(
    id: UUID, 
    repo: AgentRepository = Depends(get_agent_repo)
):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{id}", response_model=AgentRead)
async def update_agent(
    id: UUID,
    agent_in: AgentUpdate,
    repo: AgentRepository = Depends(get_agent_repo)
):
    agent = await repo.get(id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent_in.name is not None:
        agent.name = agent_in.name
    if agent_in.system_prompt is not None:
        agent.system_prompt = agent_in.system_prompt
    if agent_in.opening_remark is not None:
        agent.opening_remark = agent_in.opening_remark
        
    updated_agent = await repo.update(agent)
    return updated_agent

@router.delete("/{id}", status_code=204)
async def delete_agent(
    id: UUID,
    repo: AgentRepository = Depends(get_agent_repo)
):
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return

@router.post("/{id}/match", response_model=AgentRead)
async def start_matching(id: UUID, repo: AgentRepository = Depends(get_agent_repo)):
    agent = await repo.update_status(id, AgentStatus.MATCHING)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
