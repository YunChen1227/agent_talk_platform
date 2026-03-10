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
    username: str
    raw_demand: Optional[str] = None
    avatar_url: Optional[str] = None
