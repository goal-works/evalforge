from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EvalForge"
    environment: str = "development"
    database_url: str = "sqlite:///./evalforge.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000"]
    inline_jobs: bool = True

    model_config = SettingsConfigDict(env_prefix="EVALFORGE_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
