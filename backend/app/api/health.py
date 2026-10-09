from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter()

SERVICE_UNAVAILABLE = {
    "error": {
        "code": "SERVICE_UNAVAILABLE",
        "message": "The service is temporarily unavailable. Try again in a moment.",
        "details": {},
    }
}


@router.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def read_ready(db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content=SERVICE_UNAVAILABLE)
    return JSONResponse(status_code=200, content={"status": "ok", "database": "ok"})
