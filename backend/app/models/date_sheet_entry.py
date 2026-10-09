import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import TSTZRANGE, ExcludeConstraint, Range
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.exam_slot import ExamSlot


class DateSheetEntry(Base):
    __tablename__ = "date_sheet_entries"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="date_sheet_entries_student_course_key"),
        ForeignKeyConstraint(
            ["student_id", "course_id"],
            ["course_assignments.student_id", "course_assignments.course_id"],
            ondelete="CASCADE",
            name="date_sheet_entries_assignment_fkey",
        ),
        ForeignKeyConstraint(
            ["slot_id", "course_id", "period"],
            ["exam_slots.id", "exam_slots.course_id", "exam_slots.period"],
            name="date_sheet_entries_slot_fkey",
        ),
        ForeignKeyConstraint(
            ["student_id", "branch_id"],
            ["students.id", "students.branch_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
            name="date_sheet_entries_student_branch_fkey",
        ),
        ExcludeConstraint(
            ("student_id", "="),
            ("period", "&&"),
            using="gist",
            name="date_sheet_entries_no_overlap",
        ),
        Index("date_sheet_entries_slot_branch_idx", "slot_id", "branch_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    slot_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    period: Mapped[Range[datetime]] = mapped_column(TSTZRANGE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    course: Mapped["Course"] = relationship(
        primaryjoin="foreign(DateSheetEntry.course_id) == Course.id",
        viewonly=True,
        lazy="raise",
    )
    slot: Mapped["ExamSlot"] = relationship(
        primaryjoin="foreign(DateSheetEntry.slot_id) == ExamSlot.id",
        viewonly=True,
        lazy="raise",
    )
