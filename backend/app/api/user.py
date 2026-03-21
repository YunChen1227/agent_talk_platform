from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.user import UserRead, UserProfileUpdate, UserPreferencesRead, UserPreferencesUpdate
from app.repositories.base import UserRepository, UserTagPreferenceRepository
from app.core.deps import get_user_repo, get_user_tag_pref_repo

router = APIRouter()


@router.get("/profile", response_model=UserRead)
async def get_profile(
    user_id: UUID,
    repo: UserRepository = Depends(get_user_repo),
):
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/profile", response_model=UserRead)
async def update_profile(
    body: UserProfileUpdate,
    repo: UserRepository = Depends(get_user_repo),
):
    user = await repo.get(body.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = body.model_dump(exclude={"user_id"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user = await repo.update(user)
    return user


@router.get("/preferences", response_model=UserPreferencesRead)
async def get_preferences(
    user_id: UUID,
    pref_repo: UserTagPreferenceRepository = Depends(get_user_tag_pref_repo),
):
    prefs = await pref_repo.get_by_user(user_id)
    liked = [str(p.tag_id) for p in prefs if p.preference == "like"]
    disliked = [str(p.tag_id) for p in prefs if p.preference == "dislike"]
    return UserPreferencesRead(liked_tag_ids=liked, disliked_tag_ids=disliked)


@router.put("/preferences", response_model=UserPreferencesRead)
async def update_preferences(
    body: UserPreferencesUpdate,
    pref_repo: UserTagPreferenceRepository = Depends(get_user_tag_pref_repo),
):
    liked_uuids = [UUID(tid) for tid in body.liked_tag_ids]
    disliked_uuids = [UUID(tid) for tid in body.disliked_tag_ids]
    await pref_repo.set_preferences(body.user_id, liked_uuids, disliked_uuids)

    prefs = await pref_repo.get_by_user(body.user_id)
    liked = [str(p.tag_id) for p in prefs if p.preference == "like"]
    disliked = [str(p.tag_id) for p in prefs if p.preference == "dislike"]
    return UserPreferencesRead(liked_tag_ids=liked, disliked_tag_ids=disliked)
