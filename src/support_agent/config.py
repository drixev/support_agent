from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")
    
    env: Literal["local","dev","staging","prod"] = "local"
    log_level: str = "INFO"
    llm_provider: Literal["ollama","anthropic","openai","bedrock"] = "ollama"
    llm_model: str = "llama3.1:8b"
    
@lru_cache # singleton
def get_settings() -> Settings:
    return Settings()