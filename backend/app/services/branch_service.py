import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound
from app.models.branch import Branch
from app.models.student import Student
from app.schemas.branch import BranchCreate, BranchListQuery, BranchUpdate
from app.utils.pagination import page_out, paginate, sorted_by
from app.utils.search import like_pattern

SORTS = {
    "code": Branch.code,
    "name": Branch.name,
    "city": Branch.city,
    "created_at": Branch.created_at,
}

FIELDS = (
    "id",
    "code",
    "name",
    "city",
    "address",
    "contact_phone",
    "status",
    "created_at",
    "updated_at",
)


def list_branches(session: Session, query: BranchListQuery) -> dict:
    statement = _base_statement()
    if query.q:
        pattern = like_pattern(query.q)
        statement = statement.where(
            or_(
                Branch.code.ilike(pattern, escape="\\"),
                Branch.name.ilike(pattern, escape="\\"),
                Branch.city.ilike(pattern, escape="\\"),
            )
        )
    if query.status:
        statement = statement.where(Branch.status == query.status)
    statement = sorted_by(statement, SORTS[query.sort], query.order, Branch.id)
    result, total = paginate(session, statement, query.page, query.page_size)
    items = [_out(branch, student_count) for branch, student_count in result.all()]
    return page_out(items, query.page, query.page_size, total)


def create_branch(session: Session, data: BranchCreate) -> dict:
    branch = Branch(**data.model_dump())
    session.add(branch)
    session.commit()
    return read_branch(session, branch.id)


def read_branch(session: Session, branch_id: uuid.UUID) -> dict:
    branch = _load(session, branch_id)
    return _out(branch, _student_count(session, branch_id))


def update_branch(session: Session, branch_id: uuid.UUID, data: BranchUpdate) -> dict:
    branch = _load(session, branch_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(branch, field, value)
    branch.updated_at = datetime.now(UTC)
    session.commit()
    return read_branch(session, branch_id)


def delete_branch(session: Session, branch_id: uuid.UUID) -> None:
    branch = _load(session, branch_id)
    student_count = _student_count(session, branch_id)
    if student_count:
        raise Conflict("BRANCH_IN_USE", details={"student_count": student_count})
    session.delete(branch)
    session.commit()


def _base_statement() -> Select:
    student_count = (
        select(func.count())
        .select_from(Student)
        .where(Student.branch_id == Branch.id)
        .scalar_subquery()
    )
    return select(Branch, student_count)


def _load(session: Session, branch_id: uuid.UUID) -> Branch:
    branch = session.get(Branch, branch_id)
    if branch is None:
        raise NotFound("NOT_FOUND")
    return branch


def _student_count(session: Session, branch_id: uuid.UUID) -> int:
    return session.scalar(
        select(func.count()).select_from(Student).where(Student.branch_id == branch_id)
    )


def _out(branch: Branch, student_count: int) -> dict:
    return {
        **{field: getattr(branch, field) for field in FIELDS},
        "student_count": student_count,
    }
