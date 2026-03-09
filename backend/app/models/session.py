from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
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
    summary: Optional[str] = None
    reason: Optional[str] = None
    agent_a_contact_shared: bool = Field(default=False)
    agent_b_contact_shared: bool = Field(default=False)

class MatchResult(MatchResultBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id")
    
    session: Session = Relationship(back_populates="result")
