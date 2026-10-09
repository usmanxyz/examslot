from datetime import datetime


def overlaps(
    first_start: datetime, first_end: datetime, second_start: datetime, second_end: datetime
) -> bool:
    return first_start < second_end and second_start < first_end
