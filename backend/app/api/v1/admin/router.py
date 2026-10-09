from fastapi import APIRouter, Depends

from app.api.deps import current_admin
from app.api.v1.admin import account, assignments, branches, courses, students
from app.core.rate_limit import admin_write_limit

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(current_admin), Depends(admin_write_limit)],
)
router.include_router(account.router)
router.include_router(branches.router)
router.include_router(courses.router)
router.include_router(students.router)
router.include_router(assignments.router)
