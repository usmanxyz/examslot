import uuid
from collections.abc import Iterator
from typing import Annotated

import jwt
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.email import EmailGate
from app.core.errors import Unauthenticated
from app.core.passwords import PasswordService
from app.core.tokens import TokenService
from app.models.admin import Admin
from app.models.student import Student


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_passwords(request: Request) -> PasswordService:
    return request.app.state.passwords


def get_tokens(request: Request) -> TokenService:
    return request.app.state.tokens


def get_email_gate(request: Request) -> EmailGate:
    return request.app.state.email_gate


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[Session, Depends(get_db)]
PasswordsDep = Annotated[PasswordService, Depends(get_passwords)]
TokensDep = Annotated[TokenService, Depends(get_tokens)]
EmailGateDep = Annotated[EmailGate, Depends(get_email_gate)]


def current_student(request: Request, db: SessionDep, tokens: TokensDep) -> Student:
    subject, version = _decode(tokens, "student", request)
    student = db.get(Student, subject)
    if (
        student is None
        or student.status != "active"
        or student.password_hash is None
        or student.token_version != version
    ):
        raise Unauthenticated("UNAUTHENTICATED")
    return student


def current_admin(request: Request, db: SessionDep, tokens: TokensDep) -> Admin:
    subject, version = _decode(tokens, "admin", request)
    admin = db.get(Admin, subject)
    if admin is None or not admin.is_active or admin.token_version != version:
        raise Unauthenticated("UNAUTHENTICATED")
    return admin


StudentDep = Annotated[Student, Depends(current_student)]
AdminDep = Annotated[Admin, Depends(current_admin)]


def _decode(tokens: TokenService, area: str, request: Request) -> tuple[uuid.UUID, int]:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise Unauthenticated("UNAUTHENTICATED")
    try:
        return tokens.decode(area, token)
    except (jwt.InvalidTokenError, ValueError) as error:
        raise Unauthenticated("UNAUTHENTICATED") from error
