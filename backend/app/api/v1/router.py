from fastapi import APIRouter, Depends

from app.api.v1 import auth
from app.api.v1.admin import router as admin
from app.api.v1.student import router as student
from app.core.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1", dependencies=[Depends(rate_limit("api"))])
router.include_router(auth.router)
router.include_router(student.router)
router.include_router(admin.router)
