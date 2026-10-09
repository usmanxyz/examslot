import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.branch import Branch
    from app.models.course_assignment import CourseAssignment
    from app.models.date_sheet_entry import DateSheetEntry
    from app.models.student_photo import StudentPhoto


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("registration_no"),
        UniqueConstraint("email"),
        UniqueConstraint("cnic"),
        UniqueConstraint("id", "branch_id", name="students_id_branch_key"),
        CheckConstraint(r"registration_no ~ '^[A-Z0-9][A-Z0-9-]{3,29}$'", name="registration_no_format"),
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint("char_length(btrim(full_name)) >= 2", name="full_name_length"),
        CheckConstraint(r"phone ~ '^\+923[0-9]{9}$'", name="phone_format"),
        CheckConstraint("cnic ~ '^[0-9]{13}$'", name="cnic_format"),
        CheckConstraint("date_of_birth >= DATE '1940-01-01'", name="date_of_birth_floor"),
        CheckConstraint(
            "gender IN ('female','male','transgender','prefer_not_to_say')", name="gender_allowed"
        ),
        CheckConstraint("char_length(btrim(address)) >= 5", name="address_length"),
        CheckConstraint("char_length(btrim(guardian_name)) >= 2", name="guardian_name_length"),
        CheckConstraint("guardian_cnic ~ '^[0-9]{13}$'", name="guardian_cnic_format"),
        CheckConstraint(
            "char_length(btrim(guardian_occupation)) >= 2", name="guardian_occupation_length"
        ),
        CheckConstraint(r"guardian_phone ~ '^\+923[0-9]{9}$'", name="guardian_phone_format"),
        CheckConstraint(r"emergency_phone ~ '^\+92[0-9]{9,10}$'", name="emergency_phone_format"),
        CheckConstraint("char_length(btrim(program)) >= 2", name="program_length"),
        CheckConstraint("semester BETWEEN 1 AND 12", name="semester_range"),
        CheckConstraint("char_length(btrim(session)) >= 4", name="session_length"),
        CheckConstraint(
            "char_length(btrim(previous_qualification)) >= 2", name="previous_qualification_length"
        ),
        CheckConstraint(
            "char_length(btrim(previous_institute)) >= 2", name="previous_institute_length"
        ),
        CheckConstraint(
            "previous_score_type IN ('percentage','cgpa')", name="previous_score_type_allowed"
        ),
        CheckConstraint(
            "(previous_score_type = 'percentage' AND previous_score BETWEEN 0 AND 100)"
            " OR (previous_score_type = 'cgpa' AND previous_score BETWEEN 0 AND 4)",
            name="previous_score_range",
        ),
        CheckConstraint("status IN ('active','inactive')", name="status_allowed"),
        CheckConstraint("token_version >= 0", name="token_version_non_negative"),
        CheckConstraint("failed_login_count >= 0", name="failed_login_count_non_negative"),
        CheckConstraint(
            "(branch_id IS NULL) = (branch_selected_at IS NULL)", name="branch_pair"
        ),
        CheckConstraint(
            "date_sheet_saved_at IS NULL OR branch_id IS NOT NULL", name="saved_needs_branch"
        ),
        CheckConstraint(
            "(password_hash IS NULL) = (password_set_at IS NULL)", name="password_pair"
        ),
        Index(
            "students_full_name_trgm",
            "full_name",
            postgresql_using="gin",
            postgresql_ops={"full_name": "gin_trgm_ops"},
        ),
        Index(
            "students_email_trgm",
            "email",
            postgresql_using="gin",
            postgresql_ops={"email": "gin_trgm_ops"},
        ),
        Index(
            "students_registration_no_trgm",
            "registration_no",
            postgresql_using="gin",
            postgresql_ops={"registration_no": "gin_trgm_ops"},
        ),
        Index("students_branch_id_idx", "branch_id"),
        Index("students_created_at_idx", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    registration_no: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(16), nullable=False)
    cnic: Mapped[str] = mapped_column(CHAR(13), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    guardian_name: Mapped[str] = mapped_column(String(120), nullable=False)
    guardian_cnic: Mapped[str] = mapped_column(CHAR(13), nullable=False)
    guardian_occupation: Mapped[str] = mapped_column(String(100), nullable=False)
    guardian_phone: Mapped[str] = mapped_column(String(16), nullable=False)
    emergency_phone: Mapped[str] = mapped_column(String(16), nullable=False)
    program: Mapped[str] = mapped_column(String(120), nullable=False)
    semester: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    session: Mapped[str] = mapped_column(String(30), nullable=False)
    previous_qualification: Mapped[str] = mapped_column(String(120), nullable=False)
    previous_institute: Mapped[str] = mapped_column(String(150), nullable=False)
    previous_score_type: Mapped[str] = mapped_column(String(10), nullable=False)
    previous_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text)
    password_set_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'active'"))
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    failed_login_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("branches.id", ondelete="RESTRICT")
    )
    branch_selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_sheet_saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    branch: Mapped["Branch | None"] = relationship(lazy="raise")
    photo: Mapped["StudentPhoto | None"] = relationship(lazy="raise")
    assignments: Mapped[list["CourseAssignment"]] = relationship(
        back_populates="student", lazy="raise"
    )
    entries: Mapped[list["DateSheetEntry"]] = relationship(
        primaryjoin="Student.id == foreign(DateSheetEntry.student_id)",
        viewonly=True,
        lazy="raise",
    )
