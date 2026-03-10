from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.enums import ProductStatus


class ProductBase(SQLModel):
    user_id: UUID = Field(foreign_key="user.id")
    name: str = Field()
    description: Optional[str] = Field(default=None)
    price: Decimal = Field(max_digits=12, decimal_places=2)
    currency: str = Field(default="CNY")
    images: List[UUID] = Field(default=[], sa_column=Column(JSONB))
    cover_image_id: Optional[UUID] = Field(default=None)
    status: ProductStatus = Field(default=ProductStatus.ACTIVE)
    linked_agent_ids: List[UUID] = Field(default=[], sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Product(ProductBase, table=True):
    __tablename__ = "product"
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
