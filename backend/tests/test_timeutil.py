import os
import time as system_time
from datetime import UTC, date, datetime, time

import pytest

from app.utils.timeutil import format_date, format_time, to_local, to_utc

KARACHI = "Asia/Karachi"


@pytest.fixture(autouse=True)
def machine_timezone():
    previous = os.environ.get("TZ")
    os.environ["TZ"] = "America/New_York"
    system_time.tzset()
    yield
    if previous is None:
        del os.environ["TZ"]
    else:
        os.environ["TZ"] = previous
    system_time.tzset()


def test_to_utc_reads_the_input_as_pakistan_time():
    assert to_utc(date(2026, 10, 27), time(9, 0), KARACHI) == datetime(
        2026, 10, 27, 4, 0, tzinfo=UTC
    )


def test_to_utc_crosses_midnight_backwards():
    assert to_utc(date(2026, 10, 27), time(2, 0), KARACHI) == datetime(
        2026, 10, 26, 21, 0, tzinfo=UTC
    )


def test_to_local_returns_pakistan_time():
    local = to_local(datetime(2026, 10, 27, 4, 0, tzinfo=UTC), KARACHI)

    assert (local.year, local.month, local.day, local.hour, local.minute) == (2026, 10, 27, 9, 0)
    assert local.utcoffset().total_seconds() == 5 * 3600


def test_a_round_trip_keeps_the_instant():
    moment = to_utc(date(2026, 10, 27), time(14, 30), KARACHI)

    assert to_local(moment, KARACHI).timetz().isoformat().startswith("14:30")


def test_format_date():
    assert format_date(datetime(2026, 10, 27, 4, 0, tzinfo=UTC), KARACHI) == "Tue 27 Oct 2026"


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 10, 27, 4, 0, tzinfo=UTC), "09:00 AM"),
        (datetime(2026, 10, 27, 7, 0, tzinfo=UTC), "12:00 PM"),
        (datetime(2026, 10, 27, 12, 0, tzinfo=UTC), "05:00 PM"),
    ],
)
def test_format_time(moment, expected):
    assert format_time(moment, KARACHI) == expected


def test_formatting_ignores_the_machine_timezone():
    moment = datetime(2026, 10, 26, 20, 0, tzinfo=UTC)

    assert format_date(moment, KARACHI) == "Tue 27 Oct 2026"
    assert format_time(moment, KARACHI) == "01:00 AM"
