from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: Literal["development", "test", "production"] = "development"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+psycopg://examslot_app:local-app-password@localhost:5434/examslot"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5

    APP_TIMEZONE: str = "Asia/Karachi"
    DEFAULT_EXAM_MINUTES: int = 180
    HASH_CONCURRENCY: int = 4

    JWT_SECRET: str = "development-secret-not-for-production-use-only"
    JWT_ISSUER: str = "examslot-api"
    JWT_STUDENT_AUDIENCE: str = "examslot-student"
    JWT_ADMIN_AUDIENCE: str = "examslot-admin"
    STUDENT_TOKEN_MINUTES: int = 60
    ADMIN_TOKEN_MINUTES: int = 30

    EMAIL_BACKEND: Literal["resend", "memory"] = "memory"
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "ExamSlot <no-reply@mail.solvirapk.com>"
    EMAIL_REPLY_TO: str = "f2024266406@umt.edu.pk"
    EMAIL_HOURLY_CAP: int = 30
    EMAIL_DAILY_CAP: int = 90
    EMAIL_RECIPIENT_ALLOWLIST: str = ""

    SETUP_LINK_HOURS: int = 24
    RESET_LINK_MINUTES: int = 60
    RESET_EMAILS_PER_HOUR: int = 3

    LOGIN_MAX_FAILURES: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    RATE_LOGIN_LIMIT: int = 30
    RATE_LOGIN_WINDOW_SECONDS: int = 900
    RATE_PASSWORD_LIMIT: int = 10
    RATE_PASSWORD_WINDOW_SECONDS: int = 900
    RATE_REQUESTS_LIMIT: int = 10
    RATE_REQUESTS_WINDOW_SECONDS: int = 3600
    RATE_ADMIN_WRITE_LIMIT: int = 120
    RATE_ADMIN_WRITE_WINDOW_SECONDS: int = 600
    RATE_API_LIMIT: int = 300
    RATE_API_WINDOW_SECONDS: int = 60

    @model_validator(mode="after")
    def check_production(self) -> "Settings":
        if self.APP_ENV != "production":
            return self
        problems = []
        if len(self.JWT_SECRET) < 32:
            problems.append("JWT_SECRET must be at least 32 characters")
        if not self.FRONTEND_ORIGIN.startswith("https://"):
            problems.append("FRONTEND_ORIGIN must start with https://")
        if self.EMAIL_BACKEND != "resend":
            problems.append("EMAIL_BACKEND must be resend")
        elif not self.RESEND_API_KEY or not self.EMAIL_FROM:
            problems.append("RESEND_API_KEY and EMAIL_FROM must be set")
        if problems:
            raise ValueError("; ".join(problems))
        return self
