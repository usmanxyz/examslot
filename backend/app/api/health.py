from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.errors import ServiceUnavailable

router = APIRouter()


@router.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def read_ready(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise ServiceUnavailable("SERVICE_UNAVAILABLE") from error
    return {"status": "ok", "database": "ok"}
