from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer


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
