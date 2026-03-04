from typing import List, Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

class UserBase(SQLModel):
    contact: Optional[str] = Field(default=None)
    raw_demand: str
    tags: List[str] = Field(sa_column=Column(ARRAY(TEXT)))
    username: str = Field(unique=True, index=True)
    password_hash: str

class User(UserBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    embedding: Optional[List[float]] = Field(sa_column=Column(Vector(1536)))  # Assuming OpenAI embeddings

    agents: List["Agent"] = Relationship(back_populates="user")
