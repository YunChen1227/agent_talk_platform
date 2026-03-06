from typing import List, Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship

class UserBase(SQLModel):
    contact: Optional[str] = Field(default=None)
    raw_demand: Optional[str] = Field(default="")
    username: str = Field(unique=True, index=True)
    password_hash: str

class User(UserBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)

    agents: List["Agent"] = Relationship(back_populates="user")
