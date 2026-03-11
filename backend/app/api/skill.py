from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.skill import SkillCreate, SkillUpdate, SkillRead
from app.models.skill import Skill
from app.repositories.base import SkillRepository
from app.core.deps import get_skill_repo

router = APIRouter()


@router.post("/", response_model=SkillRead)
async def create_skill(
    body: SkillCreate,
    repo: SkillRepository = Depends(get_skill_repo),
):
    skill = Skill(user_id=body.user_id, name=body.name, description=body.description)
    skill = await repo.create(skill)
    return skill


@router.get("/", response_model=List[SkillRead])
async def list_skills(
    user_id: UUID,
    repo: SkillRepository = Depends(get_skill_repo),
):
    return await repo.list_by_user(user_id)


@router.put("/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: UUID,
    user_id: UUID,
    body: SkillUpdate,
    repo: SkillRepository = Depends(get_skill_repo),
):
    skill = await repo.get(skill_id)
    if not skill or skill.user_id != user_id:
        raise HTTPException(status_code=404, detail="Skill not found")
    if body.name is not None:
        skill.name = body.name
    if body.description is not None:
        skill.description = body.description
    return await repo.update(skill)


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: UUID,
    user_id: UUID,
    repo: SkillRepository = Depends(get_skill_repo),
):
    skill = await repo.get(skill_id)
    if not skill or skill.user_id != user_id:
        raise HTTPException(status_code=404, detail="Skill not found")
    await repo.delete(skill_id)
    return
