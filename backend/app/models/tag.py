from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship


class TagCategoryBase(SQLModel):
    name: str
    slug: str = Field(unique=True, index=True)
    description: Optional[str] = None
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


class Tag(TagBase, table=True):
    __tablename__ = "tag"
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)


class AgentTag(SQLModel, table=True):
    __tablename__ = "agent_tag"
    agent_id: UUID = Field(foreign_key="agent.id", primary_key=True)
    tag_id: UUID = Field(foreign_key="tag.id", primary_key=True)
