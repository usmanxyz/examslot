from fastapi import APIRouter

from app.api.deps import PasswordsDep, SessionDep, StudentDep, TokensDep
from app.schemas.auth import ChangePasswordRequest, StudentTokenOut
from app.schemas.student import StudentProfileOut
from app.services import auth_service, student_service

router = APIRouter(tags=["student"])


@router.get("/me", response_model=StudentProfileOut)
def read_me(student: StudentDep, db: SessionDep) -> StudentProfileOut:
    return StudentProfileOut(**student_service.read_profile(db, student))


@router.post("/me/password", response_model=StudentTokenOut)
def change_my_password(
    body: ChangePasswordRequest,
    student: StudentDep,
    db: SessionDep,
    passwords: PasswordsDep,
    tokens: TokensDep,
) -> StudentTokenOut:
    auth_service.change_password(
        db, passwords, student, body.current_password, body.new_password
    )
    return StudentTokenOut(**auth_service.student_token(db, tokens, student))
