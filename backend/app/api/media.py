from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form
from fastapi.responses import FileResponse

from app.schemas.media import MediaRead, AvatarSet
from app.repositories.base import MediaRepository, UserRepository
from app.core.deps import get_media_repo, get_user_repo
from app.services.media_service import upload_media, delete_media, list_media, set_avatar
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=MediaRead)
async def api_upload_media(
    user_id: UUID = Form(...),
    file: UploadFile = None,
    media_repo: MediaRepository = Depends(get_media_repo),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    try:
        media = await upload_media(media_repo, user_id, file)
        # Expose URL for client to fetch file
        return MediaRead(
            id=media.id,
            user_id=media.user_id,
            file_type=media.file_type,
            url=f"/media/{media.id}/file",
            thumbnail_url=media.thumbnail_url,
            original_filename=media.original_filename,
            created_at=media.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[MediaRead])
async def api_list_media(
    user_id: UUID,
    media_repo: MediaRepository = Depends(get_media_repo),
):
    items = await list_media(media_repo, user_id)
    return [
        MediaRead(
            id=m.id,
            user_id=m.user_id,
            file_type=m.file_type,
            url=f"/media/{m.id}/file",
            thumbnail_url=m.thumbnail_url,
            original_filename=m.original_filename,
            created_at=m.created_at,
        )
        for m in items
    ]


@router.delete("/{media_id}", status_code=204)
async def api_delete_media(
    media_id: UUID,
    user_id: UUID,
    media_repo: MediaRepository = Depends(get_media_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    ok = await delete_media(media_repo, user_repo, media_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Media not found or not owned by user")
    return


@router.post("/avatar")
async def api_set_avatar(
    body: AvatarSet,
    user_repo: UserRepository = Depends(get_user_repo),
    media_repo: MediaRepository = Depends(get_media_repo),
):
    try:
        await set_avatar(user_repo, media_repo, body.user_id, body.media_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{media_id}/file")
async def api_get_media_file(
    media_id: UUID,
    media_repo: MediaRepository = Depends(get_media_repo),
):
    media = await media_repo.get(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    path = settings.UPLOADS_DIR / media.url
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type=None, filename=media.original_filename)
