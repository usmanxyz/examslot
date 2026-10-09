import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.student import Student


class ChangeRequest(Base):
    __tablename__ = "change_requests"
    __table_args__ = (
        CheckConstraint("type IN ('branch_change','date_sheet_change')", name="type_allowed"),
        CheckConstraint("char_length(btrim(reason)) >= 10", name="reason_length"),
        CheckConstraint("status IN ('pending','approved','rejected')", name="status_allowed"),
        CheckConstraint(
            "(status = 'pending') = (decided_at IS NULL)", name="decision_pair"
        ),
        CheckConstraint(
            "used_at IS NULL OR status = 'approved'", name="used_only_approved"
        ),
        Index("change_requests_student_id_idx", "student_id"),
        Index("change_requests_status_created_idx", "status", text("created_at DESC")),
        Index(
            "change_requests_one_pending",
            "student_id",
            "type",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        Index(
            "change_requests_one_open_reopening",
            "student_id",
            "type",
            unique=True,
            postgresql_where=text("status = 'approved' AND used_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'pending'")
    )
    admin_remark: Mapped[str | None] = mapped_column(String(500))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("admins.id", ondelete="SET NULL")
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    student: Mapped["Student"] = relationship(lazy="raise")
