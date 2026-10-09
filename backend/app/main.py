from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import Settings
from app.core.passwords import PasswordService
from app.db.session import build_engine, build_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    docs_enabled = settings.APP_ENV != "production"
    app = FastAPI(
        title="ExamSlot API",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    engine = build_engine(settings)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    app.state.passwords = PasswordService(settings.HASH_CONCURRENCY)
    app.include_router(health_router)
    return app
