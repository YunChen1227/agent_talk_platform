from typing import AsyncGenerator
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import get_session
from app.repositories.base import (
    UserRepository, AgentRepository, SessionRepository, MessageRepository,
    MatcherRepository, MatchResultRepository, MediaRepository, ProductRepository,
    SkillRepository, TagCategoryRepository, TagRepository, AgentTagRepository,
)
from app.repositories.db_repo import (
    DBUserRepository, DBAgentRepository, DBSessionRepository, DBMessageRepository,
    DBMatcherRepository, DBMatchResultRepository, DBMediaRepository, DBProductRepository,
    DBSkillRepository, DBTagCategoryRepository, DBTagRepository, DBAgentTagRepository,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return DBUserRepository(session)

async def get_agent_repo(session: AsyncSession = Depends(get_db_session)) -> AgentRepository:
    return DBAgentRepository(session)

async def get_session_repo(session: AsyncSession = Depends(get_db_session)) -> SessionRepository:
    return DBSessionRepository(session)

async def get_message_repo(session: AsyncSession = Depends(get_db_session)) -> MessageRepository:
    return DBMessageRepository(session)

async def get_matcher_repo(session: AsyncSession = Depends(get_db_session)) -> MatcherRepository:
    return DBMatcherRepository(session)

async def get_match_result_repo(session: AsyncSession = Depends(get_db_session)) -> MatchResultRepository:
    return DBMatchResultRepository(session)

async def get_media_repo(session: AsyncSession = Depends(get_db_session)) -> MediaRepository:
    return DBMediaRepository(session)

async def get_product_repo(session: AsyncSession = Depends(get_db_session)) -> ProductRepository:
    return DBProductRepository(session)

async def get_skill_repo(session: AsyncSession = Depends(get_db_session)) -> SkillRepository:
    return DBSkillRepository(session)

async def get_tag_category_repo(session: AsyncSession = Depends(get_db_session)) -> TagCategoryRepository:
    return DBTagCategoryRepository(session)

async def get_tag_repo(session: AsyncSession = Depends(get_db_session)) -> TagRepository:
    return DBTagRepository(session)

async def get_agent_tag_repo(session: AsyncSession = Depends(get_db_session)) -> AgentTagRepository:
    return DBAgentTagRepository(session)
