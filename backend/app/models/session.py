from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Text
from app.models.enums import SessionStatus, Verdict

class SessionBase(SQLModel):
    agent_a_id: UUID = Field(foreign_key="agent.id")
    agent_b_id: UUID = Field(foreign_key="agent.id")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Session(SessionBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    
    messages: List["Message"] = Relationship(back_populates="session")
    result: Optional["MatchResult"] = Relationship(back_populates="session")

class MatchResultBase(SQLModel):
    verdict: Verdict
    summary: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    reason: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    final_outcome: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    agent_a_contact_shared: bool = Field(default=False)
    agent_b_contact_shared: bool = Field(default=False)

class MatchResult(MatchResultBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id")
    
    session: Session = Relationship(back_populates="result")
