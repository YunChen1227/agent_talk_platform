from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    raw_demand: str
    contact: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

from uuid import UUID

class UserRead(BaseModel):
    id: UUID
    raw_demand: str
    tags: list[str]
