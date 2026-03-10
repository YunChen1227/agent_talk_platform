import json
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
CONFIG_DIR = BASE_DIR / "config"
STORAGE_DIR = BASE_DIR / "storage"

class Settings(BaseSettings):
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "agentmatch"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    OPENAI_API_KEY: Optional[str] = ""
    DEEPSEEK_API_KEY: Optional[str] = ""
    QWEN_API_KEY: Optional[str] = ""
    GEMINI_API_KEY: Optional[str] = ""
    UCLOUD_API_KEY: Optional[str] = ""
    
    MODE: str = "prod"  # "dev" or "prod"
    USE_LLM_MATCHER: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def STORAGE_DEV_DIR(self) -> Path:
        return STORAGE_DIR / "dev"

    @property
    def UPLOADS_DIR(self) -> Path:
        return STORAGE_DIR / "uploads"
        env_file = str(CONFIG_DIR / ".env")

    def load_secrets(self):
        secrets_path = CONFIG_DIR / "secrets.json"
        if not secrets_path.exists():
            print(f"[config] secrets.json not found at {secrets_path}, skipping")
            return
        try:
            with open(secrets_path, "r") as f:
                data = json.load(f)
                for key in ("openai", "deepseek", "qwen", "gemini", "ucloud"):
                    value = data.get(f"{key}_api_key")
                    if value:
                        setattr(self, f"{key.upper()}_API_KEY", value)
                
                if self.MODE == "dev":
                    self.USE_LLM_MATCHER = True
        except Exception as e:
            print(f"[config] Error loading secrets.json: {e}")

settings = Settings()
settings.load_secrets()
