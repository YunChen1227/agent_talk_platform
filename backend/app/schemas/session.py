from uuid import UUID
from pydantic import BaseModel


class DirectSessionCreate(BaseModel):
    my_agent_id: UUID
    target_agent_id: UUID
