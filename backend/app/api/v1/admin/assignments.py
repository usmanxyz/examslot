import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.schemas.assignment import (
    AssignmentListItem,
    AssignmentListQuery,
    AssignmentsUpdate,
    StudentAssignmentsOut,
)
from app.schemas.common import Page
from app.services import assignment_service

router = APIRouter(tags=["admin"])


@router.get("/assignments", response_model=Page[AssignmentListItem])
def list_assignments(
    query: Annotated[AssignmentListQuery, Query()], db: SessionDep
) -> Page[AssignmentListItem]:
    return Page[AssignmentListItem](**assignment_service.list_assignments(db, query))


@router.get("/students/{student_id}/assignments", response_model=StudentAssignmentsOut)
def read_assignments(student_id: uuid.UUID, db: SessionDep) -> StudentAssignmentsOut:
    return StudentAssignmentsOut(**assignment_service.read_assignments(db, student_id))


@router.put("/students/{student_id}/assignments", response_model=StudentAssignmentsOut)
def replace_assignments(
    student_id: uuid.UUID, body: AssignmentsUpdate, db: SessionDep
) -> StudentAssignmentsOut:
    return StudentAssignmentsOut(
        **assignment_service.replace_assignments(db, student_id, body)
    )
