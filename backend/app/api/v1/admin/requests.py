import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminDep, SessionDep
from app.schemas.change_request import (
    AdminRequestListQuery,
    AdminRequestOut,
    DecisionIn,
)
from app.schemas.common import Page
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["admin"])


@router.get("", response_model=Page[AdminRequestOut])
def list_requests(
    query: Annotated[AdminRequestListQuery, Query()], db: SessionDep
) -> Page[AdminRequestOut]:
    return Page[AdminRequestOut](**request_service.list_requests(db, query))


@router.get("/{request_id}", response_model=AdminRequestOut)
def read_request(request_id: uuid.UUID, db: SessionDep) -> AdminRequestOut:
    return AdminRequestOut(**request_service.read_request(db, request_id))


@router.post("/{request_id}/approve", response_model=AdminRequestOut)
def approve_request(
    request_id: uuid.UUID, body: DecisionIn, admin: AdminDep, db: SessionDep
) -> AdminRequestOut:
    return AdminRequestOut(
        **request_service.decide_request(db, request_id, admin, "approved", body)
    )


@router.post("/{request_id}/reject", response_model=AdminRequestOut)
def reject_request(
    request_id: uuid.UUID, body: DecisionIn, admin: AdminDep, db: SessionDep
) -> AdminRequestOut:
    return AdminRequestOut(
        **request_service.decide_request(db, request_id, admin, "rejected", body)
    )
