from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import SessionDep, StudentDep
from app.core.rate_limit import rate_limit
from app.schemas.change_request import RequestCreate, RequestOut, StudentRequestListQuery
from app.schemas.common import Page
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["student"])


@router.get("", response_model=Page[RequestOut])
def list_requests(
    query: Annotated[StudentRequestListQuery, Query()], student: StudentDep, db: SessionDep
) -> Page[RequestOut]:
    return Page[RequestOut](
        **request_service.list_student_requests(db, student.id, query)
    )


@router.post(
    "",
    response_model=RequestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("requests"))],
)
def create_request(body: RequestCreate, student: StudentDep, db: SessionDep) -> RequestOut:
    return RequestOut(**request_service.create_request(db, student.id, body))
