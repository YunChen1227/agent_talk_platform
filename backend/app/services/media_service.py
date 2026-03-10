import os
import uuid
from pathlib import Path
from typing import Optional, List
from uuid import UUID
from fastapi import UploadFile

from app.models.media import Media
from app.models.enums import MediaFileType
from app.repositories.base import MediaRepository, UserRepository
from app.core.config import settings


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _get_file_type(content_type: str) -> Optional[MediaFileType]:
    if content_type in ALLOWED_IMAGE_TYPES:
        return MediaFileType.IMAGE
    if content_type in ALLOWED_VIDEO_TYPES:
        return MediaFileType.VIDEO
    return None


async def upload_media(
    media_repo: MediaRepository,
    user_id: UUID,
    file: UploadFile,
) -> Media:
    content_type = file.content_type or ""
    file_type = _get_file_type(content_type)
    if not file_type:
        raise ValueError("Unsupported file type. Use image (jpeg, png, gif, webp) or video (mp4, webm).")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File too large. Max 20 MB.")

    uploads_dir = settings.UPLOADS_DIR
    uploads_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "file").suffix or (".jpg" if file_type == MediaFileType.IMAGE else ".mp4")
    media_id = uuid.uuid4()
    filename = f"{media_id}{ext}"
    path = uploads_dir / filename
    with open(path, "wb") as f:
        f.write(content)

    # url: filename for disk lookup; API will expose /media/{id}/file for client
    media = Media(
        id=media_id,
        user_id=user_id,
        file_type=file_type,
        url=filename,
        original_filename=file.filename or "file",
    )
    return await media_repo.create(media)


async def delete_media(media_repo: MediaRepository, user_repo: UserRepository, media_id: UUID, user_id: UUID) -> bool:
    media = await media_repo.get(media_id)
    if not media or media.user_id != user_id:
        return False
    user = await user_repo.get(user_id)
    if user and user.avatar_url and f"/media/{media_id}/file" in user.avatar_url:
        user.avatar_url = None
        await user_repo.update(user)
    return await media_repo.delete(media_id)


async def list_media(media_repo: MediaRepository, user_id: UUID) -> List[Media]:
    return await media_repo.list_by_user(user_id)


async def set_avatar(
    user_repo: UserRepository,
    media_repo: MediaRepository,
    user_id: UUID,
    media_id: UUID,
) -> None:
    media = await media_repo.get(media_id)
    if not media or media.user_id != user_id:
        raise ValueError("Media not found or not owned by user")
    if media.file_type != MediaFileType.IMAGE:
        raise ValueError("Avatar must be an image")
    user = await user_repo.get(user_id)
    if not user:
        raise ValueError("User not found")
    user.avatar_url = f"/media/{media.id}/file"
    await user_repo.update(user)

