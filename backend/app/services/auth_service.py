from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import Unauthenticated, Unprocessable
from app.core.passwords import PasswordService, password_meets_policy
from app.core.tokens import TokenService
from app.models.admin import Admin
from app.models.student import Student
from app.services import student_service
from app.utils.normalize import normalize_email


def sign_in_student(
    session: Session,
    passwords: PasswordService,
    settings: Settings,
    email: str,
    password: str,
    honeypot: str,
) -> Student:
    student = session.scalar(select(Student).where(Student.email == normalize_email(email)))
    active = student is not None and student.status == "active"
    return _authenticate(session, passwords, settings, student, password, honeypot, active)


def sign_in_admin(
    session: Session,
    passwords: PasswordService,
    settings: Settings,
    email: str,
    password: str,
    honeypot: str,
) -> Admin:
    admin = session.scalar(select(Admin).where(Admin.email == normalize_email(email)))
    active = admin is not None and admin.is_active
    return _authenticate(session, passwords, settings, admin, password, honeypot, active)


def sign_out(session: Session, account: Student | Admin) -> None:
    account.token_version += 1
    account.updated_at = datetime.now(UTC)
    session.commit()


def change_password(
    session: Session,
    passwords: PasswordService,
    account: Student | Admin,
    current_password: str,
    new_password: str,
) -> None:
    verified, _ = passwords.verify_and_update(current_password, account.password_hash)
    if not verified:
        raise Unprocessable("CURRENT_PASSWORD_INCORRECT")
    if not password_meets_policy(new_password, account.email):
        raise Unprocessable("PASSWORD_TOO_WEAK")
    now = datetime.now(UTC)
    account.password_hash = passwords.hash(new_password)
    if isinstance(account, Student):
        account.password_set_at = now
    account.token_version += 1
    account.failed_login_count = 0
    account.locked_until = None
    account.updated_at = now
    session.commit()


def _authenticate(
    session: Session,
    passwords: PasswordService,
    settings: Settings,
    account: Student | Admin | None,
    password: str,
    honeypot: str,
    active: bool,
) -> Student | Admin:
    now = datetime.now(UTC)
    locked = (
        account is not None and account.locked_until is not None and account.locked_until > now
    )
    if honeypot or account is None or account.password_hash is None or locked:
        passwords.verify_and_update(password, None)
        raise Unauthenticated("INVALID_CREDENTIALS")

    verified, updated = passwords.verify_and_update(password, account.password_hash)
    if not verified:
        account.failed_login_count += 1
        if account.failed_login_count >= settings.LOGIN_MAX_FAILURES:
            account.locked_until = now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
        account.updated_at = now
        session.commit()
        raise Unauthenticated("INVALID_CREDENTIALS")

    if not active:
        raise Unauthenticated("INVALID_CREDENTIALS")

    account.failed_login_count = 0
    account.locked_until = None
    account.last_login_at = now
    if updated:
        account.password_hash = updated
    account.updated_at = now
    session.commit()
    return account


def student_token(session: Session, tokens: TokenService, student: Student) -> dict:
    return {
        "access_token": tokens.issue("student", student.id, student.token_version),
        "expires_in": tokens.lifetime_seconds("student"),
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "progress": student_service.load_state(session, student).progress,
        },
    }


def admin_token(tokens: TokenService, admin: Admin) -> dict:
    return {
        "access_token": tokens.issue("admin", admin.id, admin.token_version),
        "expires_in": tokens.lifetime_seconds("admin"),
        "admin": {"id": admin.id, "full_name": admin.full_name},
    }
