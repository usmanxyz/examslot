import argparse
import getpass
import sys
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.passwords import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    PasswordService,
    password_meets_policy,
)
from app.db.session import build_engine, build_session_factory
from app.models.admin import Admin
from app.services.seed_service import SeedBlockedError, SeedSettings, seed_demo
from app.utils.normalize import normalize_email, normalize_name

POLICY_MESSAGE = (
    f"Use {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters"
    " and do not include your email address."
)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings = Settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    passwords = PasswordService(settings.HASH_CONCURRENCY)
    try:
        with session_factory() as session:
            return args.handler(args, session, settings, passwords)
    finally:
        engine.dispose()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subparsers = parser.add_subparsers(required=True)

    create_admin = subparsers.add_parser("create-admin")
    create_admin.add_argument("--email", required=True)
    create_admin.add_argument("--name", required=True)
    create_admin.set_defaults(handler=_create_admin)

    reset_password = subparsers.add_parser("reset-admin-password")
    reset_password.add_argument("--email", required=True)
    reset_password.set_defaults(handler=_reset_admin_password)

    deactivate = subparsers.add_parser("deactivate-admin")
    deactivate.add_argument("--email", required=True)
    deactivate.set_defaults(handler=_deactivate_admin)

    seed = subparsers.add_parser("seed-demo")
    seed.add_argument("--reset", action="store_true")
    seed.set_defaults(handler=_seed_demo)

    return parser


def _create_admin(
    args: argparse.Namespace, session: Session, settings: Settings, passwords: PasswordService
) -> int:
    email = normalize_email(args.email)
    if session.scalar(select(Admin.id).where(Admin.email == email)) is not None:
        print("An admin with that email already exists.")
        return 1
    password = _read_password(confirm=True)
    if password is None:
        print("The passwords did not match.")
        return 1
    if not password_meets_policy(password, email):
        print(POLICY_MESSAGE)
        return 1
    session.add(
        Admin(
            email=email,
            full_name=normalize_name(args.name),
            password_hash=passwords.hash(password),
        )
    )
    session.commit()
    print("Admin created.")
    return 0


def _reset_admin_password(
    args: argparse.Namespace, session: Session, settings: Settings, passwords: PasswordService
) -> int:
    admin = _load_admin(session, args.email)
    if admin is None:
        print("No admin uses that email.")
        return 1
    password = _read_password(confirm=False)
    if not password_meets_policy(password, admin.email):
        print(POLICY_MESSAGE)
        return 1
    admin.password_hash = passwords.hash(password)
    admin.token_version += 1
    admin.failed_login_count = 0
    admin.locked_until = None
    admin.updated_at = datetime.now(UTC)
    session.commit()
    print("Admin password reset.")
    return 0


def _deactivate_admin(
    args: argparse.Namespace, session: Session, settings: Settings, passwords: PasswordService
) -> int:
    admin = _load_admin(session, args.email)
    if admin is None:
        print("No admin uses that email.")
        return 1
    admin.is_active = False
    admin.token_version += 1
    admin.updated_at = datetime.now(UTC)
    session.commit()
    print("Admin deactivated.")
    return 0


def _seed_demo(
    args: argparse.Namespace, session: Session, settings: Settings, passwords: PasswordService
) -> int:
    try:
        counts = seed_demo(session, passwords, settings, SeedSettings(), reset=args.reset)
    except SeedBlockedError as error:
        print(str(error))
        return 1
    for name, count in counts.items():
        print(f"{name}: {count}")
    return 0


def _load_admin(session: Session, email: str) -> Admin | None:
    return session.scalar(select(Admin).where(Admin.email == normalize_email(email)))


def _read_password(confirm: bool) -> str | None:
    if not sys.stdin.isatty():
        return sys.stdin.readline().rstrip("\n")
    password = getpass.getpass("Password: ")
    if confirm and getpass.getpass("Confirm password: ") != password:
        return None
    return password


if __name__ == "__main__":
    raise SystemExit(main())
