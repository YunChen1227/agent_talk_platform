from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import Field, SQLModel
from app.models.enums import MediaFileType


class MediaBase(SQLModel):
    user_id: UUID
    file_type: MediaFileType = Field()
    url: str = Field()
    thumbnail_url: Optional[str] = Field(default=None)
    original_filename: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Media(MediaBase, table=True):
    __tablename__ = "media"
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
