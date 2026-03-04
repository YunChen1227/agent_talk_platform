from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_session_repo, get_message_repo
from app.repositories.base import SessionRepository, MessageRepository

router = APIRouter()

@router.get("/{id}")
async def get_session_details(
    id: UUID, 
    session_repo: SessionRepository = Depends(get_session_repo),
    message_repo: MessageRepository = Depends(get_message_repo)
):
    session_obj = await session_repo.get(id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
        
    history = await message_repo.get_history(id)
    return {"session": session_obj, "history": history}
