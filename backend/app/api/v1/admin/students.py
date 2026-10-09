import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import EmailGateDep, PasswordsDep, SessionDep, SettingsDep
from app.schemas.change_request import RequestOut, StudentRequestListQuery
from app.schemas.common import Page
from app.schemas.planner import DateSheetOut
from app.schemas.student import (
    SetupLinkOut,
    StudentCreate,
    StudentDetailOut,
    StudentListItem,
    StudentListQuery,
    StudentUpdate,
)
from app.services import date_sheet_service, request_service, student_service

router = APIRouter(prefix="/students", tags=["admin"])


@router.get("", response_model=Page[StudentListItem])
def list_students(
    query: Annotated[StudentListQuery, Query()], db: SessionDep
) -> Page[StudentListItem]:
    return Page[StudentListItem](**student_service.list_students(db, query))


@router.post("", response_model=StudentDetailOut, status_code=status.HTTP_201_CREATED)
def create_student(
    body: StudentCreate,
    db: SessionDep,
    passwords: PasswordsDep,
    settings: SettingsDep,
    gate: EmailGateDep,
) -> StudentDetailOut:
    return StudentDetailOut(
        **student_service.create_student(db, passwords, settings, gate, body)
    )


@router.get("/{student_id}", response_model=StudentDetailOut)
def read_student(student_id: uuid.UUID, db: SessionDep) -> StudentDetailOut:
    return StudentDetailOut(**student_service.read_student(db, student_id))


@router.patch("/{student_id}", response_model=StudentDetailOut)
def update_student(
    student_id: uuid.UUID, body: StudentUpdate, db: SessionDep
) -> StudentDetailOut:
    return StudentDetailOut(**student_service.update_student(db, student_id, body))


@router.post("/{student_id}/deactivate", response_model=StudentDetailOut)
def deactivate_student(student_id: uuid.UUID, db: SessionDep) -> StudentDetailOut:
    return StudentDetailOut(**student_service.set_student_status(db, student_id, "inactive"))


@router.post("/{student_id}/reactivate", response_model=StudentDetailOut)
def reactivate_student(student_id: uuid.UUID, db: SessionDep) -> StudentDetailOut:
    return StudentDetailOut(**student_service.set_student_status(db, student_id, "active"))


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: uuid.UUID,
    confirm: Annotated[str, Query(min_length=1, max_length=30)],
    db: SessionDep,
) -> Response:
    student_service.delete_student(db, student_id, confirm)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{student_id}/setup-email", response_model=SetupLinkOut)
def resend_setup_email(
    student_id: uuid.UUID,
    db: SessionDep,
    passwords: PasswordsDep,
    settings: SettingsDep,
    gate: EmailGateDep,
) -> SetupLinkOut:
    return SetupLinkOut(
        **student_service.resend_setup_email(db, passwords, settings, gate, student_id)
    )


@router.get("/{student_id}/date-sheet", response_model=DateSheetOut)
def read_student_date_sheet(
    student_id: uuid.UUID, db: SessionDep, settings: SettingsDep
) -> DateSheetOut:
    student_service.read_student(db, student_id)
    return DateSheetOut(**date_sheet_service.read_date_sheet(db, settings, student_id))


@router.get("/{student_id}/requests", response_model=Page[RequestOut])
def read_student_requests(
    student_id: uuid.UUID,
    query: Annotated[StudentRequestListQuery, Query()],
    db: SessionDep,
) -> Page[RequestOut]:
    return Page[RequestOut](
        **request_service.list_requests_for_student(db, student_id, query)
    )
