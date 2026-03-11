from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class SkillCreate(BaseModel):
    user_id: UUID
    name: str
    description: Optional[str] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SkillRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
