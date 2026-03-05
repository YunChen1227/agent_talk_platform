import json
import os
from typing import Optional
from pydantic_settings import BaseSettings

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
    USE_LLM_MATCHER: bool = False # Use LLM to verify matches

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

    def load_from_json(self, config_path: str = "config.json"):
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    if data.get("openai_api_key"):
                        self.OPENAI_API_KEY = data["openai_api_key"]
                    if data.get("deepseek_api_key"):
                        self.DEEPSEEK_API_KEY = data["deepseek_api_key"]
                    if data.get("qwen_api_key"):
                        self.QWEN_API_KEY = data["qwen_api_key"]
                    if data.get("gemini_api_key"):
                        self.GEMINI_API_KEY = data["gemini_api_key"]
                    if data.get("ucloud_api_key"):
                        self.UCLOUD_API_KEY = data["ucloud_api_key"]
                    
                    # Auto-enable LLM matcher in dev mode if not explicitly set
                    if self.MODE == "dev":
                        self.USE_LLM_MATCHER = True
            except Exception as e:
                print(f"Error loading config.json: {e}")

settings = Settings()
settings.load_from_json() # Load JSON config on import
