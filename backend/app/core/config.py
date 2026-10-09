from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: Literal["development", "test", "production"] = "development"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    DATABASE_URL: str = "postgresql+psycopg://examslot_app:local-app-password@localhost:5432/examslot"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    APP_TIMEZONE: str = "Asia/Karachi"
    DEFAULT_EXAM_MINUTES: int = 180
    HASH_CONCURRENCY: int = 4
