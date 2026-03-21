from datetime import date
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: UUID
    username: str
    raw_demand: Optional[str] = None
    avatar_url: Optional[str] = None
    display_name: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    personality: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None
    occupation: Optional[str] = None
    website: Optional[str] = None


class UserProfileUpdate(BaseModel):
    user_id: UUID
    display_name: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    personality: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None
    occupation: Optional[str] = None
    website: Optional[str] = None


class UserPreferencesRead(BaseModel):
    liked_tag_ids: List[str]
    disliked_tag_ids: List[str]


class UserPreferencesUpdate(BaseModel):
    user_id: UUID
    liked_tag_ids: List[str] = []
    disliked_tag_ids: List[str] = []
