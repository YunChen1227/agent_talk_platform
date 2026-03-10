from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.models.enums import MediaFileType


class MediaRead(BaseModel):
    id: UUID
    user_id: UUID
    file_type: MediaFileType
    url: str
    thumbnail_url: Optional[str] = None
    original_filename: str
    created_at: datetime


class AvatarSet(BaseModel):
    user_id: UUID
    media_id: UUID
