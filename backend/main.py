import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.db import init_db, get_session
from app.core.config import settings
from app.api import agents, sessions, auth
from app.services.orchestrator import run_orchestrator
from app.core.deps import get_session_repo, get_agent_repo, get_matcher_repo, get_message_repo, get_match_result_repo
from app.services.llm import validate_api_keys, valid_clients

async def background_task():
    while True:
        try:
            if settings.MODE == "dev":
                # In dev mode, we use JSON repos which are global/singleton-like
                session_repo = await get_session_repo(None)
                agent_repo = await get_agent_repo(None)
                matcher_repo = await get_matcher_repo(None)
                message_repo = await get_message_repo(None)
                match_result_repo = await get_match_result_repo(None)
                
                await run_orchestrator(session_repo, agent_repo, matcher_repo, message_repo, match_result_repo)
            else:
                # In prod mode, we need a DB session
                async for session in get_session():
                    session_repo = await get_session_repo(session)
                    agent_repo = await get_agent_repo(session)
                    matcher_repo = await get_matcher_repo(session)
                    message_repo = await get_message_repo(session)
                    match_result_repo = await get_match_result_repo(session)
                    
                    await run_orchestrator(session_repo, agent_repo, matcher_repo, message_repo, match_result_repo)
                    break # get_session yields once
        except Exception as e:
            print(f"Error in background task: {e}")
        await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate API keys on startup
    validate_api_keys()
    
    if settings.MODE != "dev":
        await init_db()
        
    # Reset stuck JUDGING sessions
    try:
        if settings.MODE == "dev":
            session_repo = await get_session_repo(None)
            await session_repo.reset_judging_sessions()
        else:
            async for session in get_session():
                session_repo = await get_session_repo(session)
                await session_repo.reset_judging_sessions()
                break
        print("Reset any stuck JUDGING sessions to ACTIVE")
    except Exception as e:
        print(f"Error resetting sessions: {e}")
    
    # Start background task
    asyncio.create_task(background_task())
    yield

app = FastAPI(title="AgentMatch Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

@app.get("/")
async def root():
    return {"message": "Welcome to AgentMatch Platform API", "mode": settings.MODE}

@app.get("/api/status")
async def get_status():
    return {
        "valid_providers": list(valid_clients.keys()),
        "has_valid_key": len(valid_clients) > 0,
        "mode": settings.MODE
    }
