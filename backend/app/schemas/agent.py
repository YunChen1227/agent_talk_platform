from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List


class AgentCreate(BaseModel):
    user_id: UUID
    name: str
    description: Optional[str] = None  # For PAID users
    system_prompt: Optional[str] = None  # For FREE users
    opening_remark: Optional[str] = None  # For FREE users
    linked_product_ids: Optional[List[UUID]] = None
    linked_skill_ids: Optional[List[UUID]] = None
    tag_ids: Optional[List[UUID]] = None  # FREE: required manual pick; PAID: optional override


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    opening_remark: Optional[str] = None
    linked_product_ids: Optional[List[UUID]] = None
    linked_skill_ids: Optional[List[UUID]] = None
    tag_ids: Optional[List[UUID]] = None


class CatalogTagRead(BaseModel):
    id: str
    name: str
    slug: str
    category_id: str
    parent_id: Optional[str] = None


class AgentRead(BaseModel):
    id: UUID
    name: str
    status: str
    system_prompt: str
    opening_remark: Optional[str] = None
    tags: Optional[List[str]] = None
    catalog_tags: Optional[List[CatalogTagRead]] = None
    linked_product_ids: Optional[List[UUID]] = None
    linked_skill_ids: Optional[List[UUID]] = None
