from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, pool

from alembic import context
from app.db.base import Base
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

target_metadata = Base.metadata


class MigrationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MIGRATION_DATABASE_URL: str


def run_migrations_online() -> None:
    settings = MigrationSettings()
    engine = create_engine(settings.MIGRATION_DATABASE_URL, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations_online()
