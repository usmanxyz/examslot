from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer


def _utc_instant(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _decimal_string(value: Decimal) -> str:
    return f"{value:.2f}"


UtcInstant = Annotated[datetime, PlainSerializer(_utc_instant, return_type=str)]
DecimalString = Annotated[Decimal, PlainSerializer(_decimal_string, return_type=str)]


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageOut(ResponseModel):
    message: str


class ListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    q: str | None = Field(default=None, min_length=1, max_length=100)


class Page[Item](BaseModel):
    items: list[Item]
    page: int
    page_size: int
    total: int
    total_pages: int


def normalized(normalizer: Callable[[str], str]) -> BeforeValidator:
    def validate(value: object) -> object:
        return normalizer(value) if isinstance(value, str) else value

    return BeforeValidator(validate)
