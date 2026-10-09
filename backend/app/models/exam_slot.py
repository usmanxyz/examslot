import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import TSTZRANGE, Range
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course


class ExamSlot(Base):
    __tablename__ = "exam_slots"
    __table_args__ = (
        CheckConstraint("seats_per_branch BETWEEN 1 AND 1000", name="seats_per_branch_range"),
        CheckConstraint("ends_at > starts_at", name="end_after_start"),
        UniqueConstraint("course_id", "starts_at", name="exam_slots_course_start_key"),
        UniqueConstraint("id", "course_id", "period", name="exam_slots_identity_key"),
        Index("exam_slots_starts_at_idx", "starts_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time_set: Mapped[bool] = mapped_column(Boolean, nullable=False)
    seats_per_branch: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[Range[datetime]] = mapped_column(
        TSTZRANGE,
        Computed("tstzrange(starts_at, ends_at, '[)')", persisted=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    course: Mapped["Course"] = relationship(lazy="raise")
