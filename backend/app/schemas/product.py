from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.enums import ProductStatus


class ProductCreate(BaseModel):
    user_id: UUID
    name: str
    description: Optional[str] = None
    price: Decimal
    currency: str = "CNY"
    image_ids: List[UUID] = []
    cover_image_id: Optional[UUID] = None
    status: ProductStatus = ProductStatus.ACTIVE
    linked_agent_ids: List[UUID] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    image_ids: Optional[List[UUID]] = None
    cover_image_id: Optional[UUID] = None
    status: Optional[ProductStatus] = None
    linked_agent_ids: Optional[List[UUID]] = None


class ProductRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    price: Decimal
    currency: str
    images: List[UUID]
    cover_image_id: Optional[UUID] = None
    status: ProductStatus
    linked_agent_ids: List[UUID]
    created_at: datetime
    updated_at: datetime


class LinkAgentBody(BaseModel):
    user_id: UUID
    agent_id: UUID
