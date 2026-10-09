from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from sqlalchemy.orm import configure_mappers

from app.api.health import router as health_router
from app.api.v1.router import router as api_router
from app.core.config import Settings
from app.core.email import EmailGate, build_email_sender
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import add_middleware
from app.core.passwords import PasswordService
from app.core.rate_limit import build_rate_limiter
from app.core.tokens import TokenService
from app.db.session import build_engine, build_session_factory
from app.models.admin import Admin  # noqa: F401
from app.models.branch import Branch  # noqa: F401
from app.models.change_request import ChangeRequest  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.course_assignment import CourseAssignment  # noqa: F401
from app.models.date_sheet_entry import DateSheetEntry  # noqa: F401
from app.models.exam_slot import ExamSlot  # noqa: F401
from app.models.password_token import PasswordToken  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.student_photo import StudentPhoto  # noqa: F401

EMAIL_TIMEOUT_SECONDS = 10.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if app.state.email_client is not None:
        app.state.email_client.close()
    app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings)
    configure_mappers()
    docs_enabled = settings.APP_ENV != "production"
    app = FastAPI(
        title="ExamSlot API",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )
    engine = build_engine(settings)
    email_client = (
        httpx.Client(timeout=EMAIL_TIMEOUT_SECONDS)
        if settings.EMAIL_BACKEND == "resend"
        else None
    )
    email_sender = build_email_sender(settings, email_client)

    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    app.state.passwords = PasswordService(settings.HASH_CONCURRENCY)
    app.state.tokens = TokenService(settings)
    app.state.rate_limiter = build_rate_limiter(settings)
    app.state.email_client = email_client
    app.state.email_sender = email_sender
    app.state.email_gate = EmailGate(email_sender, settings)

    register_error_handlers(app)
    add_middleware(app, settings)
    app.include_router(health_router)
    app.include_router(api_router)
    return app
