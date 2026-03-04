from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserCreate, UserRead, UserLogin
from app.services.user_service import create_user, authenticate_user
from app.repositories.base import UserRepository
from app.core.deps import get_user_repo

router = APIRouter()

@router.post("/register", response_model=UserRead)
async def register(user_in: UserCreate, repo: UserRepository = Depends(get_user_repo)):
    try:
        user = await create_user(
            repo, 
            user_in.username, 
            user_in.password
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=UserRead)
async def login(user_in: UserLogin, repo: UserRepository = Depends(get_user_repo)):
    user = await authenticate_user(repo, user_in.username, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
