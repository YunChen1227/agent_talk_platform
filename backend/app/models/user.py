from datetime import date
from typing import List, Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Text, JSON

class UserBase(SQLModel):
    contact: Optional[str] = Field(default=None)
    raw_demand: Optional[str] = Field(default="", sa_column=Column(Text, nullable=True))
    username: str = Field(unique=True, index=True)
    password_hash: str
    avatar_url: Optional[str] = Field(default=None)
    display_name: Optional[str] = Field(default=None)
    gender: Optional[str] = Field(default=None)
    birthday: Optional[date] = Field(default=None)
    location: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    personality: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    hobbies: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    occupation: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)

class User(UserBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)

    agents: List["Agent"] = Relationship(back_populates="user")
