import uuid

from pydantic import EmailStr, Field

from app.schemas.common import RequestModel, ResponseModel, UtcInstant

PASSWORD_HINT = "Use at least 10 characters, and do not include your email address."


class LoginRequest(RequestModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)
    website: str = Field(default="", max_length=200)


class StudentAccountOut(ResponseModel):
    id: uuid.UUID
    full_name: str
    progress: str


class AdminAccountOut(ResponseModel):
    id: uuid.UUID
    full_name: str


class StudentTokenOut(ResponseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    student: StudentAccountOut


class AdminTokenOut(ResponseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin: AdminAccountOut


class ForgotPasswordRequest(RequestModel):
    email: EmailStr = Field(max_length=254)
    website: str = Field(default="", max_length=200)


class VerifyLinkRequest(RequestModel):
    token: str = Field(min_length=1, max_length=200)


class VerifyLinkOut(ResponseModel):
    purpose: str
    expires_at: UtcInstant


class SetPasswordRequest(RequestModel):
    token: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=128)
    website: str = Field(default="", max_length=200)


class ChangePasswordRequest(RequestModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)
