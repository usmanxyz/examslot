import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("code"),
        CheckConstraint(r"code ~ '^[A-Z0-9][A-Z0-9-]{1,9}$'", name="code_format"),
        CheckConstraint("char_length(btrim(name)) >= 2", name="name_length"),
        CheckConstraint("char_length(btrim(city)) >= 2", name="city_length"),
        CheckConstraint("char_length(btrim(address)) >= 5", name="address_length"),
        CheckConstraint(r"contact_phone ~ '^\+92[0-9]{9,10}$'", name="contact_phone_format"),
        CheckConstraint("status IN ('active','inactive')", name="status_allowed"),
        Index(
            "branches_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "branches_city_trgm",
            "city",
            postgresql_using="gin",
            postgresql_ops={"city": "gin_trgm_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'active'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
