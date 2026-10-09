import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import SessionDep
from app.schemas.branch import BranchCreate, BranchListQuery, BranchOut, BranchUpdate
from app.schemas.common import Page
from app.services import branch_service

router = APIRouter(prefix="/branches", tags=["admin"])


@router.get("", response_model=Page[BranchOut])
def list_branches(
    query: Annotated[BranchListQuery, Query()], db: SessionDep
) -> Page[BranchOut]:
    return Page[BranchOut](**branch_service.list_branches(db, query))


@router.post("", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(body: BranchCreate, db: SessionDep) -> BranchOut:
    return BranchOut(**branch_service.create_branch(db, body))


@router.get("/{branch_id}", response_model=BranchOut)
def read_branch(branch_id: uuid.UUID, db: SessionDep) -> BranchOut:
    return BranchOut(**branch_service.read_branch(db, branch_id))


@router.patch("/{branch_id}", response_model=BranchOut)
def update_branch(branch_id: uuid.UUID, body: BranchUpdate, db: SessionDep) -> BranchOut:
    return BranchOut(**branch_service.update_branch(db, branch_id, body))


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(branch_id: uuid.UUID, db: SessionDep) -> Response:
    branch_service.delete_branch(db, branch_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
