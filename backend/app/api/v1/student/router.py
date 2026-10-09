from fastapi import APIRouter, Depends

from app.api.deps import current_student
from app.api.v1.student import branch, date_sheet, profile

router = APIRouter(prefix="/student", dependencies=[Depends(current_student)])
router.include_router(profile.router)
router.include_router(branch.router)
router.include_router(date_sheet.router)
