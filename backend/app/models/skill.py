from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import Field, SQLModel


class SkillBase(SQLModel):
    user_id: UUID = Field(foreign_key="user.id")
    name: str = Field()
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Skill(SkillBase, table=True):
    __tablename__ = "skill"
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
