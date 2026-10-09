import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("code"),
        CheckConstraint(r"code ~ '^[A-Z0-9][A-Z0-9-]{1,11}$'", name="code_format"),
        CheckConstraint("char_length(btrim(title)) >= 2", name="title_length"),
        CheckConstraint("credit_hours BETWEEN 1 AND 6", name="credit_hours_range"),
        CheckConstraint("char_length(btrim(department)) >= 2", name="department_length"),
        CheckConstraint("status IN ('active','inactive')", name="status_allowed"),
        Index(
            "courses_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(String(12), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    credit_hours: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'active'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )