from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from app.models.enums import AgentStatus

class AgentBase(SQLModel):
    name: str
    system_prompt: str
    status: AgentStatus = Field(default=AgentStatus.IDLE)

class Agent(AgentBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    
    user: "User" = Relationship(back_populates="agents")
