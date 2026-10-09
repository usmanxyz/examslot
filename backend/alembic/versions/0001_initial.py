"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-09 14:57:23.474917

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ASSIGNMENT_COUNT_FUNCTION = """
CREATE FUNCTION enforce_assignment_count() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  target uuid := COALESCE(NEW.student_id, OLD.student_id);
  total integer;
BEGIN
  SELECT count(*) INTO total FROM course_assignments WHERE student_id = target;
  IF total <> 0 AND (total < 4 OR total > 6) THEN
    RAISE EXCEPTION 'assignment count % is outside 4 to 6', total
      USING ERRCODE = 'check_violation', CONSTRAINT = 'course_assignments_count';
  END IF;
  RETURN NULL;
END;
$$;
"""

ASSIGNMENT_COUNT_TRIGGER = """
CREATE CONSTRAINT TRIGGER course_assignments_count
AFTER INSERT OR DELETE ON course_assignments
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION enforce_assignment_count();
"""


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "admins",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("token_version", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("failed_login_count", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("char_length(btrim(full_name)) >= 2", name=op.f("admins_full_name_length")),
        sa.CheckConstraint("email = lower(email)", name=op.f("admins_email_lowercase")),
        sa.CheckConstraint("failed_login_count >= 0", name=op.f("admins_failed_login_count_non_negative")),
        sa.CheckConstraint("token_version >= 0", name=op.f("admins_token_version_non_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("admins_pkey")),
        sa.UniqueConstraint("email", name=op.f("admins_email_key")),
    )
    op.create_table(
        "branches",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("contact_phone", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=10), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("code ~ '^[A-Z0-9][A-Z0-9-]{1,9}$'", name=op.f("branches_code_format")),
        sa.CheckConstraint(
            "contact_phone ~ '^\\+92[0-9]{9,10}$'", name=op.f("branches_contact_phone_format")
        ),
        sa.CheckConstraint("status IN ('active','inactive')", name=op.f("branches_status_allowed")),
        sa.CheckConstraint("char_length(btrim(address)) >= 5", name=op.f("branches_address_length")),
        sa.CheckConstraint("char_length(btrim(city)) >= 2", name=op.f("branches_city_length")),
        sa.CheckConstraint("char_length(btrim(name)) >= 2", name=op.f("branches_name_length")),
        sa.PrimaryKeyConstraint("id", name=op.f("branches_pkey")),
        sa.UniqueConstraint("code", name=op.f("branches_code_key")),
    )
    op.create_index(
        "branches_city_trgm",
        "branches",
        ["city"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"city": "gin_trgm_ops"},
    )
    op.create_index(
        "branches_name_trgm",
        "branches",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_table(
        "courses",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("credit_hours", sa.SmallInteger(), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=10), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("code ~ '^[A-Z0-9][A-Z0-9-]{1,11}$'", name=op.f("courses_code_format")),
        sa.CheckConstraint("status IN ('active','inactive')", name=op.f("courses_status_allowed")),
        sa.CheckConstraint("char_length(btrim(department)) >= 2", name=op.f("courses_department_length")),
        sa.CheckConstraint("char_length(btrim(title)) >= 2", name=op.f("courses_title_length")),
        sa.CheckConstraint("credit_hours BETWEEN 1 AND 6", name=op.f("courses_credit_hours_range")),
        sa.PrimaryKeyConstraint("id", name=op.f("courses_pkey")),
        sa.UniqueConstraint("code", name=op.f("courses_code_key")),
    )
    op.create_index(
        "courses_title_trgm",
        "courses",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_table(
        "exam_slots",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time_set", sa.Boolean(), nullable=False),
        sa.Column("seats_per_branch", sa.Integer(), nullable=False),
        sa.Column(
            "period",
            postgresql.TSTZRANGE(),
            sa.Computed("tstzrange(starts_at, ends_at, '[)')", persisted=True),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name=op.f("exam_slots_end_after_start")),
        sa.CheckConstraint(
            "seats_per_branch BETWEEN 1 AND 1000", name=op.f("exam_slots_seats_per_branch_range")
        ),
        sa.ForeignKeyConstraint(
            ["course_id"], ["courses.id"], name=op.f("exam_slots_course_id_fkey"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("exam_slots_pkey")),
        sa.UniqueConstraint("course_id", "starts_at", name="exam_slots_course_start_key"),
        sa.UniqueConstraint("id", "course_id", "period", name="exam_slots_identity_key"),
    )
    op.create_index("exam_slots_starts_at_idx", "exam_slots", ["starts_at"], unique=False)
    op.create_table(
        "students",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("registration_no", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=16), nullable=False),
        sa.Column("cnic", sa.CHAR(length=13), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("guardian_name", sa.String(length=120), nullable=False),
        sa.Column("guardian_cnic", sa.CHAR(length=13), nullable=False),
        sa.Column("guardian_occupation", sa.String(length=100), nullable=False),
        sa.Column("guardian_phone", sa.String(length=16), nullable=False),
        sa.Column("emergency_phone", sa.String(length=16), nullable=False),
        sa.Column("program", sa.String(length=120), nullable=False),
        sa.Column("semester", sa.SmallInteger(), nullable=False),
        sa.Column("session", sa.String(length=30), nullable=False),
        sa.Column("previous_qualification", sa.String(length=120), nullable=False),
        sa.Column("previous_institute", sa.String(length=150), nullable=False),
        sa.Column("previous_score_type", sa.String(length=10), nullable=False),
        sa.Column("previous_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("password_set_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=10), server_default=sa.text("'active'"), nullable=False),
        sa.Column("token_version", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("failed_login_count", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("branch_id", sa.Uuid(), nullable=True),
        sa.Column("branch_selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_sheet_saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(previous_score_type = 'percentage' AND previous_score BETWEEN 0 AND 100)"
            " OR (previous_score_type = 'cgpa' AND previous_score BETWEEN 0 AND 4)",
            name=op.f("students_previous_score_range"),
        ),
        sa.CheckConstraint("cnic ~ '^[0-9]{13}$'", name=op.f("students_cnic_format")),
        sa.CheckConstraint("date_of_birth >= DATE '1940-01-01'", name=op.f("students_date_of_birth_floor")),
        sa.CheckConstraint(
            "emergency_phone ~ '^\\+92[0-9]{9,10}$'", name=op.f("students_emergency_phone_format")
        ),
        sa.CheckConstraint(
            "gender IN ('female','male','transgender','prefer_not_to_say')",
            name=op.f("students_gender_allowed"),
        ),
        sa.CheckConstraint("guardian_cnic ~ '^[0-9]{13}$'", name=op.f("students_guardian_cnic_format")),
        sa.CheckConstraint(
            "guardian_phone ~ '^\\+923[0-9]{9}$'", name=op.f("students_guardian_phone_format")
        ),
        sa.CheckConstraint("phone ~ '^\\+923[0-9]{9}$'", name=op.f("students_phone_format")),
        sa.CheckConstraint(
            "previous_score_type IN ('percentage','cgpa')", name=op.f("students_previous_score_type_allowed")
        ),
        sa.CheckConstraint(
            "registration_no ~ '^[A-Z0-9][A-Z0-9-]{3,29}$'", name=op.f("students_registration_no_format")
        ),
        sa.CheckConstraint("status IN ('active','inactive')", name=op.f("students_status_allowed")),
        sa.CheckConstraint(
            "(branch_id IS NULL) = (branch_selected_at IS NULL)", name=op.f("students_branch_pair")
        ),
        sa.CheckConstraint(
            "(password_hash IS NULL) = (password_set_at IS NULL)", name=op.f("students_password_pair")
        ),
        sa.CheckConstraint("char_length(btrim(address)) >= 5", name=op.f("students_address_length")),
        sa.CheckConstraint("char_length(btrim(full_name)) >= 2", name=op.f("students_full_name_length")),
        sa.CheckConstraint(
            "char_length(btrim(guardian_name)) >= 2", name=op.f("students_guardian_name_length")
        ),
        sa.CheckConstraint(
            "char_length(btrim(guardian_occupation)) >= 2", name=op.f("students_guardian_occupation_length")
        ),
        sa.CheckConstraint(
            "char_length(btrim(previous_institute)) >= 2", name=op.f("students_previous_institute_length")
        ),
        sa.CheckConstraint(
            "char_length(btrim(previous_qualification)) >= 2",
            name=op.f("students_previous_qualification_length"),
        ),
        sa.CheckConstraint("char_length(btrim(program)) >= 2", name=op.f("students_program_length")),
        sa.CheckConstraint("char_length(btrim(session)) >= 4", name=op.f("students_session_length")),
        sa.CheckConstraint(
            "date_sheet_saved_at IS NULL OR branch_id IS NOT NULL", name=op.f("students_saved_needs_branch")
        ),
        sa.CheckConstraint("email = lower(email)", name=op.f("students_email_lowercase")),
        sa.CheckConstraint("failed_login_count >= 0", name=op.f("students_failed_login_count_non_negative")),
        sa.CheckConstraint("semester BETWEEN 1 AND 12", name=op.f("students_semester_range")),
        sa.CheckConstraint("token_version >= 0", name=op.f("students_token_version_non_negative")),
        sa.ForeignKeyConstraint(
            ["branch_id"], ["branches.id"], name=op.f("students_branch_id_fkey"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("students_pkey")),
        sa.UniqueConstraint("cnic", name=op.f("students_cnic_key")),
        sa.UniqueConstraint("email", name=op.f("students_email_key")),
        sa.UniqueConstraint("id", "branch_id", name="students_id_branch_key"),
        sa.UniqueConstraint("registration_no", name=op.f("students_registration_no_key")),
    )
    op.create_index("students_branch_id_idx", "students", ["branch_id"], unique=False)
    op.create_index(
        "students_created_at_idx", "students", [sa.literal_column("created_at DESC")], unique=False
    )
    op.create_index(
        "students_email_trgm",
        "students",
        ["email"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"email": "gin_trgm_ops"},
    )
    op.create_index(
        "students_full_name_trgm",
        "students",
        ["full_name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"full_name": "gin_trgm_ops"},
    )
    op.create_index(
        "students_registration_no_trgm",
        "students",
        ["registration_no"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"registration_no": "gin_trgm_ops"},
    )
    op.create_table(
        "change_requests",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=10), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("admin_remark", sa.String(length=500), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.Uuid(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(status = 'pending') = (decided_at IS NULL)", name=op.f("change_requests_decision_pair")
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected')", name=op.f("change_requests_status_allowed")
        ),
        sa.CheckConstraint(
            "type IN ('branch_change','date_sheet_change')", name=op.f("change_requests_type_allowed")
        ),
        sa.CheckConstraint(
            "used_at IS NULL OR status = 'approved'", name=op.f("change_requests_used_only_approved")
        ),
        sa.CheckConstraint("char_length(btrim(reason)) >= 10", name=op.f("change_requests_reason_length")),
        sa.ForeignKeyConstraint(
            ["decided_by"], ["admins.id"], name=op.f("change_requests_decided_by_fkey"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], name=op.f("change_requests_student_id_fkey"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("change_requests_pkey")),
    )
    op.create_index(
        "change_requests_one_open_reopening",
        "change_requests",
        ["student_id", "type"],
        unique=True,
        postgresql_where=sa.text("status = 'approved' AND used_at IS NULL"),
    )
    op.create_index(
        "change_requests_one_pending",
        "change_requests",
        ["student_id", "type"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index(
        "change_requests_status_created_idx",
        "change_requests",
        ["status", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index("change_requests_student_id_idx", "change_requests", ["student_id"], unique=False)
    op.create_table(
        "course_assignments",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["courses.id"], name=op.f("course_assignments_course_id_fkey"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("course_assignments_student_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("student_id", "course_id", name=op.f("course_assignments_pkey")),
    )
    op.create_index("course_assignments_course_id_idx", "course_assignments", ["course_id"], unique=False)
    op.execute(ASSIGNMENT_COUNT_FUNCTION)
    op.execute(ASSIGNMENT_COUNT_TRIGGER)
    op.create_table(
        "password_tokens",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=10), nullable=False),
        sa.Column("secret_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_status", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "delivery_status IN ('sent','failed')", name=op.f("password_tokens_delivery_status_allowed")
        ),
        sa.CheckConstraint("purpose IN ('setup','reset')", name=op.f("password_tokens_purpose_allowed")),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], name=op.f("password_tokens_student_id_fkey"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("password_tokens_pkey")),
    )
    op.create_index(
        "password_tokens_one_live",
        "password_tokens",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("used_at IS NULL AND revoked_at IS NULL"),
    )
    op.create_index(
        "password_tokens_student_created_idx",
        "password_tokens",
        ["student_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "student_photos",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("media_type", sa.String(length=20), server_default=sa.text("'image/webp'"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("media_type = 'image/webp'", name=op.f("student_photos_media_type_allowed")),
        sa.CheckConstraint("octet_length(content) <= 204800", name=op.f("student_photos_content_size")),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], name=op.f("student_photos_student_id_fkey"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("student_id", name=op.f("student_photos_pkey")),
    )
    op.create_table(
        "date_sheet_entries",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("slot_id", sa.Uuid(), nullable=False),
        sa.Column("branch_id", sa.Uuid(), nullable=False),
        sa.Column("period", postgresql.TSTZRANGE(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        postgresql.ExcludeConstraint(
            (sa.column("student_id"), "="),
            (sa.column("period"), "&&"),
            using="gist",
            name="date_sheet_entries_no_overlap",
        ),
        sa.ForeignKeyConstraint(
            ["slot_id", "course_id", "period"],
            ["exam_slots.id", "exam_slots.course_id", "exam_slots.period"],
            name="date_sheet_entries_slot_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["student_id", "branch_id"],
            ["students.id", "students.branch_id"],
            name="date_sheet_entries_student_branch_fkey",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id", "course_id"],
            ["course_assignments.student_id", "course_assignments.course_id"],
            name="date_sheet_entries_assignment_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("date_sheet_entries_pkey")),
        sa.UniqueConstraint("student_id", "course_id", name="date_sheet_entries_student_course_key"),
    )
    op.create_index(
        "date_sheet_entries_slot_branch_idx", "date_sheet_entries", ["slot_id", "branch_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("date_sheet_entries_slot_branch_idx", table_name="date_sheet_entries")
    op.drop_table("date_sheet_entries")
    op.drop_table("student_photos")
    op.drop_index("password_tokens_student_created_idx", table_name="password_tokens")
    op.drop_index(
        "password_tokens_one_live",
        table_name="password_tokens",
        postgresql_where=sa.text("used_at IS NULL AND revoked_at IS NULL"),
    )
    op.drop_table("password_tokens")
    op.execute("DROP TRIGGER IF EXISTS course_assignments_count ON course_assignments")
    op.drop_index("course_assignments_course_id_idx", table_name="course_assignments")
    op.drop_table("course_assignments")
    op.drop_index("change_requests_student_id_idx", table_name="change_requests")
    op.drop_index("change_requests_status_created_idx", table_name="change_requests")
    op.drop_index(
        "change_requests_one_pending",
        table_name="change_requests",
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.drop_index(
        "change_requests_one_open_reopening",
        table_name="change_requests",
        postgresql_where=sa.text("status = 'approved' AND used_at IS NULL"),
    )
    op.drop_table("change_requests")
    op.drop_index(
        "students_registration_no_trgm",
        table_name="students",
        postgresql_using="gin",
        postgresql_ops={"registration_no": "gin_trgm_ops"},
    )
    op.drop_index(
        "students_full_name_trgm",
        table_name="students",
        postgresql_using="gin",
        postgresql_ops={"full_name": "gin_trgm_ops"},
    )
    op.drop_index(
        "students_email_trgm",
        table_name="students",
        postgresql_using="gin",
        postgresql_ops={"email": "gin_trgm_ops"},
    )
    op.drop_index("students_created_at_idx", table_name="students")
    op.drop_index("students_branch_id_idx", table_name="students")
    op.drop_table("students")
    op.drop_index("exam_slots_starts_at_idx", table_name="exam_slots")
    op.drop_table("exam_slots")
    op.drop_index(
        "courses_title_trgm",
        table_name="courses",
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.drop_table("courses")
    op.drop_index(
        "branches_name_trgm",
        table_name="branches",
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.drop_index(
        "branches_city_trgm",
        table_name="branches",
        postgresql_using="gin",
        postgresql_ops={"city": "gin_trgm_ops"},
    )
    op.drop_table("branches")
    op.drop_table("admins")
    op.execute("DROP FUNCTION IF EXISTS enforce_assignment_count()")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
