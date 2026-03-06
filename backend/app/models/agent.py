from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from app.models.enums import AgentStatus

class AgentBase(SQLModel):
    name: str
    system_prompt: str
    opening_remark: Optional[str] = Field(default=None)
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    tags: List[str] = Field(default=[], sa_column=Column(ARRAY(TEXT)))

class Agent(AgentBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(Vector(1536)))
    
    user: "User" = Relationship(back_populates="agents")
