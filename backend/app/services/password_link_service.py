import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.email import EmailGate
from app.core.errors import BadRequest, Unprocessable
from app.core.passwords import PasswordService, password_meets_policy
from app.emails.templates import reset_email, setup_email
from app.models.password_token import PasswordToken
from app.models.student import Student
from app.utils.normalize import normalize_email

SECRET_BYTES = 32


def issue(
    session: Session,
    passwords: PasswordService,
    settings: Settings,
    student: Student,
    purpose: str,
) -> tuple[uuid.UUID, str, datetime]:
    now = datetime.now(UTC)
    revoke_live(session, student.id)
    secret = secrets.token_urlsafe(SECRET_BYTES)
    expires_at = now + _lifetime(settings, purpose)
    token = PasswordToken(
        student_id=student.id,
        purpose=purpose,
        secret_hash=passwords.hash(secret),
        expires_at=expires_at,
    )
    session.add(token)
    session.flush()
    return token.id, secret, expires_at


def revoke_live(session: Session, student_id: uuid.UUID) -> None:
    session.execute(
        update(PasswordToken)
        .where(
            PasswordToken.student_id == student_id,
            PasswordToken.used_at.is_(None),
            PasswordToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )


def build_link(settings: Settings, token_id: uuid.UUID, secret: str) -> str:
    return f"{settings.FRONTEND_ORIGIN}/set-password#token={token_id}.{secret}"


def deliver(
    session: Session,
    settings: Settings,
    gate: EmailGate,
    student: Student,
    purpose: str,
    token_id: uuid.UUID,
    secret: str,
    expires_at: datetime,
) -> str:
    link = build_link(settings, token_id, secret)
    builder = setup_email if purpose == "setup" else reset_email
    message = builder(
        student.full_name, student.email, link, expires_at, settings.APP_TIMEZONE
    )
    status = gate.send(purpose, message)
    session.execute(
        update(PasswordToken).where(PasswordToken.id == token_id).values(delivery_status=status)
    )
    session.commit()
    return status


def verify_link(session: Session, passwords: PasswordService, token: str) -> PasswordToken:
    row, _ = _load_live(session, passwords, token, lock=False)
    return row


def set_password(
    session: Session, passwords: PasswordService, token: str, password: str
) -> None:
    row, student = _load_live(session, passwords, token, lock=True)
    if not password_meets_policy(password, student.email):
        raise Unprocessable("PASSWORD_TOO_WEAK")
    now = datetime.now(UTC)
    student.password_hash = passwords.hash(password)
    student.password_set_at = now
    student.token_version += 1
    student.failed_login_count = 0
    student.locked_until = None
    student.updated_at = now
    row.used_at = now
    session.execute(
        update(PasswordToken)
        .where(
            PasswordToken.student_id == student.id,
            PasswordToken.id != row.id,
            PasswordToken.used_at.is_(None),
            PasswordToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    session.commit()


def forgot_password(
    session: Session,
    passwords: PasswordService,
    settings: Settings,
    gate: EmailGate,
    email: str,
    honeypot: str,
) -> None:
    if honeypot:
        return
    student = session.scalar(select(Student).where(Student.email == normalize_email(email)))
    if student is None or student.status != "active":
        return
    purpose = "setup" if student.password_hash is None else "reset"
    if purpose == "reset" and _recent_resets(session, student.id) >= settings.RESET_EMAILS_PER_HOUR:
        return
    token_id, secret, expires_at = issue(session, passwords, settings, student, purpose)
    session.commit()
    deliver(session, settings, gate, student, purpose, token_id, secret, expires_at)


def _lifetime(settings: Settings, purpose: str) -> timedelta:
    if purpose == "setup":
        return timedelta(hours=settings.SETUP_LINK_HOURS)
    return timedelta(minutes=settings.RESET_LINK_MINUTES)


def _recent_resets(session: Session, student_id: uuid.UUID) -> int:
    since = datetime.now(UTC) - timedelta(hours=1)
    return session.scalar(
        select(func.count())
        .select_from(PasswordToken)
        .where(
            PasswordToken.student_id == student_id,
            PasswordToken.purpose == "reset",
            PasswordToken.created_at > since,
        )
    )


def _load_live(
    session: Session, passwords: PasswordService, token: str, lock: bool
) -> tuple[PasswordToken, Student]:
    token_id, secret = _parse(token)
    statement = select(PasswordToken).where(PasswordToken.id == token_id)
    if lock:
        statement = statement.with_for_update()
    row = session.scalar(statement)
    if row is None:
        passwords.verify_and_update(secret, None)
        raise BadRequest("LINK_INVALID")
    student = session.get(Student, row.student_id)
    now = datetime.now(UTC)
    if (
        row.used_at is not None
        or row.revoked_at is not None
        or row.expires_at <= now
        or student.status != "active"
    ):
        passwords.verify_and_update(secret, None)
        raise BadRequest("LINK_INVALID")
    verified, _ = passwords.verify_and_update(secret, row.secret_hash)
    if not verified:
        raise BadRequest("LINK_INVALID")
    return row, student


def _parse(token: str) -> tuple[uuid.UUID, str]:
    raw_id, _, secret = token.partition(".")
    if not secret:
        raise BadRequest("LINK_INVALID")
    try:
        return uuid.UUID(raw_id), secret
    except ValueError as error:
        raise BadRequest("LINK_INVALID") from error
