import json
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
CONFIG_DIR = BASE_DIR / "config"
STORAGE_DIR = BASE_DIR / "storage"

class Settings(BaseSettings):
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "cy1234567"
    MYSQL_DB: str = "agentmatch"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306

    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    OPENAI_API_KEY: Optional[str] = ""
    DEEPSEEK_API_KEY: Optional[str] = ""
    QWEN_API_KEY: Optional[str] = ""
    GEMINI_API_KEY: Optional[str] = ""
    UCLOUD_API_KEY: Optional[str] = ""
    
    MODE: str = "prod"  # "dev_1" | "dev_2" | "prod"
    USE_LLM_MATCHER: bool = False

    # Local OpenAI-compatible embedding service (e.g. backend/embedding/embedding_server.py)
    EMBEDDING_API_URL: str = "http://127.0.0.1:8830/v1/embeddings"
    EMBEDDING_DIM: int = 1024  # Qwen3-Embedding-0.6B typical hidden size; align with model

    @property
    def is_dev(self) -> bool:
        return self.MODE in ("dev", "dev_1", "dev_2")

    @property
    def use_json_es(self) -> bool:
        return self.MODE == "dev_1"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+asyncmy://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    @property
    def ES_URL(self) -> str:
        return f"http://{self.ES_HOST}:{self.ES_PORT}"

    @property
    def STORAGE_DEV_DIR(self) -> Path:
        return STORAGE_DIR / "dev"

    @property
    def STORAGE_SEED_DIR(self) -> Path:
        return STORAGE_DIR / "seed"

    @property
    def UPLOADS_DIR(self) -> Path:
        return STORAGE_DIR / "uploads"

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
                
                self.USE_LLM_MATCHER = True
        except Exception as e:
            print(f"[config] Error loading secrets.json: {e}")

settings = Settings()
settings.load_secrets()
