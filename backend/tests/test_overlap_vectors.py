import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.utils.overlap import overlaps

VECTORS = json.loads((Path(__file__).resolve().parents[2] / "shared" / "overlap-cases.json").read_text())
DEFAULT_MINUTES = VECTORS["default_exam_minutes"]


def window(case: dict) -> tuple[datetime, datetime]:
    start = datetime.fromisoformat(case["start"])
    if case["end"] is None:
        return start, start + timedelta(minutes=DEFAULT_MINUTES)
    return start, datetime.fromisoformat(case["end"])


@pytest.mark.parametrize("case", VECTORS["cases"], ids=lambda case: case["name"])
def test_shared_overlap_vectors(case):
    first_start, first_end = window(case["first"])
    second_start, second_end = window(case["second"])

    assert overlaps(first_start, first_end, second_start, second_end) is case["overlaps"]
    assert overlaps(second_start, second_end, first_start, first_end) is case["overlaps"]
