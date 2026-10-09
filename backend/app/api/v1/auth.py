from fastapi import APIRouter, Depends, Response, status

from app.api.deps import (
    AdminDep,
    EmailGateDep,
    PasswordsDep,
    SessionDep,
    SettingsDep,
    StudentDep,
    TokensDep,
)
from app.core.rate_limit import rate_limit
from app.schemas.auth import (
    AdminTokenOut,
    ForgotPasswordRequest,
    LoginRequest,
    SetPasswordRequest,
    StudentTokenOut,
    VerifyLinkOut,
    VerifyLinkRequest,
)
from app.schemas.common import MessageOut
from app.services import auth_service, password_link_service

FORGOT_MESSAGE = (
    "If that email belongs to a student account, a reset link is on its way."
    " It expires in 60 minutes."
)
SET_PASSWORD_MESSAGE = "Your password is set. Sign in with your email and new password."

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/student/login", response_model=StudentTokenOut, dependencies=[Depends(rate_limit("login"))]
)
def student_login(
    body: LoginRequest,
    db: SessionDep,
    passwords: PasswordsDep,
    settings: SettingsDep,
    tokens: TokensDep,
) -> StudentTokenOut:
    student = auth_service.sign_in_student(
        db, passwords, settings, body.email, body.password, body.website
    )
    return StudentTokenOut(**auth_service.student_token(db, tokens, student))


@router.post(
    "/admin/login", response_model=AdminTokenOut, dependencies=[Depends(rate_limit("login"))]
)
def admin_login(
    body: LoginRequest,
    db: SessionDep,
    passwords: PasswordsDep,
    settings: SettingsDep,
    tokens: TokensDep,
) -> AdminTokenOut:
    admin = auth_service.sign_in_admin(
        db, passwords, settings, body.email, body.password, body.website
    )
    return AdminTokenOut(**auth_service.admin_token(tokens, admin))


@router.post("/student/logout", status_code=status.HTTP_204_NO_CONTENT)
def student_logout(student: StudentDep, db: SessionDep) -> Response:
    auth_service.sign_out(db, student)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/admin/logout", status_code=status.HTTP_204_NO_CONTENT)
def admin_logout(admin: AdminDep, db: SessionDep) -> Response:
    auth_service.sign_out(db, admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/password/forgot",
    response_model=MessageOut,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit("password"))],
)
def forgot_password(
    body: ForgotPasswordRequest,
    db: SessionDep,
    passwords: PasswordsDep,
    settings: SettingsDep,
    gate: EmailGateDep,
) -> MessageOut:
    password_link_service.forgot_password(
        db, passwords, settings, gate, body.email, body.website
    )
    return MessageOut(message=FORGOT_MESSAGE)


@router.post(
    "/password/verify-link",
    response_model=VerifyLinkOut,
    dependencies=[Depends(rate_limit("password"))],
)
def verify_link(
    body: VerifyLinkRequest, db: SessionDep, passwords: PasswordsDep
) -> VerifyLinkOut:
    token = password_link_service.verify_link(db, passwords, body.token)
    return VerifyLinkOut(purpose=token.purpose, expires_at=token.expires_at)


@router.post(
    "/password/set", response_model=MessageOut, dependencies=[Depends(rate_limit("password"))]
)
def set_password(
    body: SetPasswordRequest, db: SessionDep, passwords: PasswordsDep
) -> MessageOut:
    if not body.website:
        password_link_service.set_password(db, passwords, body.token, body.password)
    return MessageOut(message=SET_PASSWORD_MESSAGE)
