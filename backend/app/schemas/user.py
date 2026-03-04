from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

from uuid import UUID

class UserRead(BaseModel):
    id: UUID
    raw_demand: Optional[str] = None
    tags: list[str] = []
