from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON


class TagCategoryBase(SQLModel):
    name: str
    slug: str = Field(unique=True, index=True)
    description: Optional[str] = None
    scope: str = Field(default="agent", index=True)  # "agent" | "product"
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class TagCategory(TagCategoryBase, table=True):
    __tablename__ = "tag_category"
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)


class TagBase(SQLModel):
    category_id: UUID = Field(foreign_key="tag_category.id")
    name: str
    slug: str = Field(unique=True, index=True)
    parent_id: Optional[UUID] = Field(default=None, foreign_key="tag.id")
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(JSON))
    is_user_defined: bool = Field(default=False)


class Tag(TagBase, table=True):
    __tablename__ = "tag"
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)


class AgentTag(SQLModel, table=True):
    __tablename__ = "agent_tag"
    agent_id: UUID = Field(foreign_key="agent.id", primary_key=True)
    tag_id: UUID = Field(foreign_key="tag.id", primary_key=True)


class UserTagPreference(SQLModel, table=True):
    __tablename__ = "user_tag_preference"
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    tag_id: UUID = Field(foreign_key="tag.id", primary_key=True)
    preference: str = Field(index=True)  # "like" | "dislike"
