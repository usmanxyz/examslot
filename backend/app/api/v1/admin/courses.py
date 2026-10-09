import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import SessionDep
from app.schemas.common import Page
from app.schemas.course import CourseCreate, CourseListQuery, CourseOut, CourseUpdate
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["admin"])


@router.get("", response_model=Page[CourseOut])
def list_courses(
    query: Annotated[CourseListQuery, Query()], db: SessionDep
) -> Page[CourseOut]:
    return Page[CourseOut](**course_service.list_courses(db, query))


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(body: CourseCreate, db: SessionDep) -> CourseOut:
    return CourseOut(**course_service.create_course(db, body))


@router.get("/{course_id}", response_model=CourseOut)
def read_course(course_id: uuid.UUID, db: SessionDep) -> CourseOut:
    return CourseOut(**course_service.read_course(db, course_id))


@router.patch("/{course_id}", response_model=CourseOut)
def update_course(course_id: uuid.UUID, body: CourseUpdate, db: SessionDep) -> CourseOut:
    return CourseOut(**course_service.update_course(db, course_id, body))


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: uuid.UUID, db: SessionDep) -> Response:
    course_service.delete_course(db, course_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
