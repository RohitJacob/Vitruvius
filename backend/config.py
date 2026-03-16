from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    vision_model: str = "google/gemini-2.0-flash-001"
    text_model: str = "google/gemini-2.0-flash-001"
    max_concurrent_llm_calls: int = 5
    session_ttl_seconds: int = 3600
    max_upload_size_mb: int = 100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
