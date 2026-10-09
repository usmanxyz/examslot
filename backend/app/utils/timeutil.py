from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

DATE_FORMAT = "%a %d %b %Y"
TIME_FORMAT = "%I:%M %p"


def to_utc(day: date, moment: time, timezone: str) -> datetime:
    return datetime.combine(day, moment, tzinfo=ZoneInfo(timezone)).astimezone(UTC)


def to_local(moment: datetime, timezone: str) -> datetime:
    return moment.astimezone(ZoneInfo(timezone))


def format_date(moment: datetime, timezone: str) -> str:
    return to_local(moment, timezone).strftime(DATE_FORMAT)


def format_time(moment: datetime, timezone: str) -> str:
    return to_local(moment, timezone).strftime(TIME_FORMAT)
