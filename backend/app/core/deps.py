from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import get_session
from app.core.config import settings
from app.repositories.base import UserRepository, AgentRepository, SessionRepository, MessageRepository, MatcherRepository, MatchResultRepository, MediaRepository, ProductRepository, SkillRepository, TagCategoryRepository, TagRepository, AgentTagRepository
from app.repositories.db_repo import (
    DBUserRepository, DBAgentRepository, DBSessionRepository, DBMessageRepository,
    DBMatcherRepository, DBMatchResultRepository, DBMediaRepository, DBProductRepository,
    DBSkillRepository, DBTagCategoryRepository, DBTagRepository, DBAgentTagRepository,
)
from app.repositories.json_repo import (
    JSONUserRepository, JSONAgentRepository, JSONSessionRepository, JSONMessageRepository,
    JSONMatcherRepository, JSONMatchResultRepository, JSONMediaRepository, JSONProductRepository,
    JSONSkillRepository, JSONTagCategoryRepository, JSONTagRepository, JSONAgentTagRepository,
    JSONStore,
)

# Global JSON Store instance (uses storage/dev/ via config)
json_store = JSONStore()

async def get_db_session() -> AsyncGenerator[Optional[AsyncSession], None]:
    if settings.MODE == "dev":
        yield None
    else:
        async for session in get_session():
            yield session

async def get_user_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> UserRepository:
    if settings.MODE == "dev":
        return JSONUserRepository(json_store)
    return DBUserRepository(session)

async def get_agent_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> AgentRepository:
    if settings.MODE == "dev":
        return JSONAgentRepository(json_store)
    return DBAgentRepository(session)

async def get_session_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> SessionRepository:
    if settings.MODE == "dev":
        return JSONSessionRepository(json_store)
    return DBSessionRepository(session)

async def get_message_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> MessageRepository:
    if settings.MODE == "dev":
        return JSONMessageRepository(json_store)
    return DBMessageRepository(session)

async def get_matcher_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> MatcherRepository:
    if settings.MODE == "dev":
        return JSONMatcherRepository(json_store)
    return DBMatcherRepository(session)

async def get_match_result_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> MatchResultRepository:
    if settings.MODE == "dev":
        return JSONMatchResultRepository(json_store)
    return DBMatchResultRepository(session)

async def get_media_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> MediaRepository:
    if settings.MODE == "dev":
        return JSONMediaRepository(json_store)
    return DBMediaRepository(session)

async def get_product_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> ProductRepository:
    if settings.MODE == "dev":
        return JSONProductRepository(json_store)
    return DBProductRepository(session)

async def get_skill_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> SkillRepository:
    if settings.MODE == "dev":
        return JSONSkillRepository(json_store)
    return DBSkillRepository(session)

async def get_tag_category_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> TagCategoryRepository:
    if settings.MODE == "dev":
        return JSONTagCategoryRepository(json_store)
    return DBTagCategoryRepository(session)

async def get_tag_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> TagRepository:
    if settings.MODE == "dev":
        return JSONTagRepository(json_store)
    return DBTagRepository(session)

async def get_agent_tag_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> AgentTagRepository:
    if settings.MODE == "dev":
        return JSONAgentTagRepository(json_store)
    return DBAgentTagRepository(session)
