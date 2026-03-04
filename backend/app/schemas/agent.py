from pydantic import BaseModel
from uuid import UUID

class AgentCreate(BaseModel):
    user_id: UUID
    name: str

class AgentRead(BaseModel):
    id: UUID
    name: str
    status: str
    system_prompt: str
