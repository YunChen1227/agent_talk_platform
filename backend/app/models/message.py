from typing import Optional, List, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

class MessageBase(SQLModel):
    content: str
    sender_id: UUID = Field(foreign_key="agent.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attachments: Optional[List[Any]] = Field(default=None, sa_column=Column(JSONB))

class Message(MessageBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id")
    
    session: "Session" = Relationship(back_populates="messages")
