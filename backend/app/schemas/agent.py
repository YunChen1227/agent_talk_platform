from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class AgentCreate(BaseModel):
    user_id: UUID
    name: str

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    opening_remark: Optional[str] = None

class AgentRead(BaseModel):
    id: UUID
    name: str
    status: str
    system_prompt: str
    opening_remark: Optional[str] = None
