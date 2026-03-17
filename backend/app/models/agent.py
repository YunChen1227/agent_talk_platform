from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON, Text
from app.models.enums import AgentStatus

class AgentBase(SQLModel):
    name: str
    system_prompt: str = Field(sa_column=Column(Text, nullable=False))
    opening_remark: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    tags: List[str] = Field(default=[], sa_column=Column(JSON))
    linked_product_ids: Optional[List[UUID]] = Field(default=None, sa_column=Column(JSON))
    linked_skill_ids: Optional[List[UUID]] = Field(default=None, sa_column=Column("linked_skill_ids", JSON))

class Agent(AgentBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    
    user: "User" = Relationship(back_populates="agents")
