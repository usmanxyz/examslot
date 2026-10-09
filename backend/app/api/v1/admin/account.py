from fastapi import APIRouter

from app.api.deps import AdminDep, PasswordsDep, SessionDep, TokensDep
from app.schemas.auth import AdminTokenOut, ChangePasswordRequest
from app.schemas.student import AdminProfileOut
from app.services import auth_service

router = APIRouter(tags=["admin"])


@router.get("/me", response_model=AdminProfileOut)
def read_me(admin: AdminDep) -> AdminProfileOut:
    return AdminProfileOut.model_validate(admin)


@router.post("/me/password", response_model=AdminTokenOut)
def change_my_password(
    body: ChangePasswordRequest,
    admin: AdminDep,
    db: SessionDep,
    passwords: PasswordsDep,
    tokens: TokensDep,
) -> AdminTokenOut:
    auth_service.change_password(db, passwords, admin, body.current_password, body.new_password)
    return AdminTokenOut(**auth_service.admin_token(tokens, admin))
