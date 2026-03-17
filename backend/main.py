import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.db import init_db, get_session
from app.core.es import init_es, close_es
from app.core.config import settings
from app.api import agents, sessions, auth, media, shop, skill, plaza
from app.services.orchestrator import run_orchestrator
from app.core.deps import get_session_repo, get_agent_repo, get_matcher_repo, get_message_repo, get_match_result_repo, get_product_repo
from app.services.llm import validate_api_keys, valid_clients

async def background_task():
    while True:
        try:
            async for session in get_session():
                session_repo = await get_session_repo(session)
                agent_repo = await get_agent_repo(session)
                matcher_repo = await get_matcher_repo(session)
                message_repo = await get_message_repo(session)
                match_result_repo = await get_match_result_repo(session)
                product_repo = await get_product_repo(session)

                await run_orchestrator(session_repo, agent_repo, matcher_repo, message_repo, match_result_repo, product_repo=product_repo)
                break
        except Exception as e:
            print(f"Error in background task: {e}")
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_api_keys()

    await init_db()
    await init_es()

    try:
        async for session in get_session():
            session_repo = await get_session_repo(session)
            await session_repo.reset_judging_sessions()
            break
        print("Reset any stuck JUDGING sessions to ACTIVE")
    except Exception as e:
        print(f"Error resetting sessions: {e}")

    asyncio.create_task(background_task())
    yield
    await close_es()

app = FastAPI(title="AgentMatch Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(media.router, prefix="/media", tags=["media"])
app.include_router(shop.router, prefix="/shop", tags=["shop"])
app.include_router(skill.router, prefix="/skills", tags=["skills"])
app.include_router(plaza.router, prefix="/plaza", tags=["plaza"])

@app.get("/")
async def root():
    return {"message": "Welcome to AgentMatch Platform API", "mode": settings.MODE}

@app.get("/api/status")
async def get_status():
    return {
        "valid_providers": list(valid_clients.keys()),
        "has_valid_key": len(valid_clients) > 0,
        "mode": settings.MODE,
        "use_llm_matcher": settings.USE_LLM_MATCHER
    }

@app.post("/api/config/llm-matcher")
async def toggle_llm_matcher(enabled: bool):
    settings.USE_LLM_MATCHER = enabled
    return {"use_llm_matcher": settings.USE_LLM_MATCHER}
