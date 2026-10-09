import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentPhoto(Base):
    __tablename__ = "student_photos"
    __table_args__ = (
        CheckConstraint("octet_length(content) <= 204800", name="content_size"),
        CheckConstraint("media_type = 'image/webp'", name="media_type_allowed"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    media_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'image/webp'")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
