from fastapi import APIRouter

from app.api.deps import SessionDep, SettingsDep, StudentDep
from app.schemas.planner import BranchOptionsOut, BranchSelect, BranchSelectionOut
from app.services import branch_selection_service

router = APIRouter(tags=["student"])


@router.get("/branches", response_model=BranchOptionsOut)
def list_branches(
    student: StudentDep, db: SessionDep, settings: SettingsDep
) -> BranchOptionsOut:
    return BranchOptionsOut(
        **branch_selection_service.list_branches(db, settings, student)
    )


@router.put("/branch", response_model=BranchSelectionOut)
def select_branch(
    body: BranchSelect, student: StudentDep, db: SessionDep, settings: SettingsDep
) -> BranchSelectionOut:
    return BranchSelectionOut(
        **branch_selection_service.select_branch(db, settings, student.id, body.branch_id)
    )
