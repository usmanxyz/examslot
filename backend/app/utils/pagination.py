from math import ceil

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement


def paginate(session: Session, statement: Select, page: int, page_size: int) -> tuple[Result, int]:
    total = session.scalar(
        select(func.count()).select_from(statement.order_by(None).subquery())
    )
    window = statement.limit(page_size).offset((page - 1) * page_size)
    return session.execute(window), total


def sorted_by(
    statement: Select, column: ColumnElement, order: str, tiebreaker: ColumnElement
) -> Select:
    direction = desc if order == "desc" else asc
    return statement.order_by(direction(column), tiebreaker)


def page_out(items: list, page: int, page_size: int, total: int) -> dict:
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }
