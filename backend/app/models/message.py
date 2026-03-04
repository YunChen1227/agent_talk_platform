from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

class MessageBase(SQLModel):
    content: str
    sender_id: UUID = Field(foreign_key="agent.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Message(MessageBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.id")
    
    session: "Session" = Relationship(back_populates="messages")
