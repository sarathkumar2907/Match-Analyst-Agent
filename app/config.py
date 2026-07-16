from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- API-Football ----
    api_football_key: str
    api_football_base_url: str = "https://v3.football.api-sports.io"

    # ---- OpenAI ----
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # ---- App config ----
    app_env: str = "development"
    log_level: str = "INFO"
    cache_ttl_seconds: int = 300

    # ---- FastAPI ----
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance - avoids re-reading .env on every import."""
    return Settings()
