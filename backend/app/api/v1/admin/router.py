from fastapi import APIRouter, Depends

from app.api.deps import current_admin
from app.api.v1.admin import account
from app.core.rate_limit import admin_write_limit

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(current_admin), Depends(admin_write_limit)],
)
router.include_router(account.router)
