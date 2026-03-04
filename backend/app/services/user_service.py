import hashlib
from typing import Optional
from app.models.user import User
from app.services.llm import get_embedding, extract_tags
from app.repositories.base import UserRepository

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

async def create_user(repo: UserRepository, username: str, password: str, raw_demand: str = "", contact: Optional[str] = None) -> User:
    # Check if user exists
    existing_user = await repo.get_by_username(username)
    if existing_user:
        raise ValueError("Username already exists")

    tags = []
    embedding = None
    
    if raw_demand:
        tags = await extract_tags(raw_demand)
        embedding = await get_embedding(raw_demand)
    
    hashed_password = hash_password(password)
    
    user = User(
        username=username,
        password_hash=hashed_password,
        raw_demand=raw_demand,
        contact=contact,
        tags=tags,
        embedding=embedding
    )
    return await repo.create(user)

async def authenticate_user(repo: UserRepository, username: str, password: str) -> Optional[User]:
    user = await repo.get_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
