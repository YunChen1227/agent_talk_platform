from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import get_session
from app.core.config import settings
from app.repositories.base import UserRepository, AgentRepository, SessionRepository, MessageRepository, MatcherRepository, MatchResultRepository, MediaRepository, ProductRepository
from app.repositories.db_repo import DBUserRepository, DBAgentRepository, DBSessionRepository, DBMessageRepository, DBMatcherRepository, DBMatchResultRepository
from app.repositories.json_repo import JSONUserRepository, JSONAgentRepository, JSONSessionRepository, JSONMessageRepository, JSONMatcherRepository, JSONMatchResultRepository, JSONMediaRepository, JSONProductRepository, JSONStore

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
    return JSONMediaRepository(json_store)

async def get_product_repo(session: Optional[AsyncSession] = Depends(get_db_session)) -> ProductRepository:
    return JSONProductRepository(json_store)
