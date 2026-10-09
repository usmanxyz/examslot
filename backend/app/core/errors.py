from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException

MESSAGES = {
    "LINK_INVALID": "This link is no longer valid. Request a new one from the sign-in page.",
    "INVALID_CREDENTIALS": "Email or password is incorrect.",
    "UNAUTHENTICATED": "Your session has ended. Sign in again.",
    "NOT_FOUND": "We could not find that.",
    "METHOD_NOT_ALLOWED": "This action is not supported here.",
    "EMAIL_TAKEN": "Another student already uses this email.",
    "REGISTRATION_NO_TAKEN": "This registration number is already in use.",
    "CNIC_TAKEN": "Another student already has this CNIC or B-Form number.",
    "BRANCH_CODE_TAKEN": "Another branch already uses this code.",
    "COURSE_CODE_TAKEN": "Another course already uses this code.",
    "BRANCH_IN_USE": (
        "Students have chosen this branch, so it cannot be deleted."
        " Set it to inactive instead."
    ),
    "COURSE_IN_USE": (
        "This course is assigned to students or has exam slots, so it cannot be deleted."
        " Set it to inactive instead."
    ),
    "SLOT_IN_USE": (
        "Students have chosen this slot, so its date and time cannot change"
        " and it cannot be deleted."
    ),
    "SLOT_DUPLICATE": "This course already has a slot starting at that date and time.",
    "SLOT_CONFLICT": "Two of your exams overlap. Choose a different time for one of them.",
    "REQUEST_PENDING_EXISTS": "You already have a pending request of this type.",
    "REOPENING_OPEN": "Your earlier request was approved and is waiting to be used.",
    "PAYLOAD_TOO_LARGE": "The photo must be 2 MB or smaller.",
    "VALIDATION_ERROR": "Some fields need attention.",
    "ASSIGNMENT_COUNT_INVALID": "Assign between 4 and 6 courses.",
    "PASSWORD_TOO_WEAK": "Use at least 10 characters, and do not include your email address.",
    "CURRENT_PASSWORD_INCORRECT": "Your current password is incorrect.",
    "RATE_LIMITED": "Too many requests. Try again later.",
    "INTERNAL_ERROR": "Something went wrong on our side. Try again in a moment.",
    "SERVICE_UNAVAILABLE": "The service is temporarily unavailable. Try again in a moment.",
}

CONSTRAINT_ERRORS = {
    "students_email_key": "EMAIL_TAKEN",
    "students_registration_no_key": "REGISTRATION_NO_TAKEN",
    "students_cnic_key": "CNIC_TAKEN",
    "branches_code_key": "BRANCH_CODE_TAKEN",
    "courses_code_key": "COURSE_CODE_TAKEN",
    "students_branch_id_fkey": "BRANCH_IN_USE",
    "course_assignments_course_id_fkey": "COURSE_IN_USE",
    "exam_slots_course_id_fkey": "COURSE_IN_USE",
    "exam_slots_course_start_key": "SLOT_DUPLICATE",
    "date_sheet_entries_slot_fkey": "SLOT_IN_USE",
    "date_sheet_entries_no_overlap": "SLOT_CONFLICT",
    "course_assignments_count": "ASSIGNMENT_COUNT_INVALID",
    "change_requests_one_pending": "REQUEST_PENDING_EXISTS",
    "change_requests_one_open_reopening": "REOPENING_OPEN",
}

UNPROCESSABLE_CONSTRAINT_CODES = frozenset({"ASSIGNMENT_COUNT_INVALID"})

UNAUTHENTICATED_HEADERS = {"WWW-Authenticate": "Bearer"}


class AppError(Exception):
    status_code = 500

    def __init__(
        self,
        code: str,
        message: str | None = None,
        details: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = message or MESSAGES[code]
        self.details = details or {}
        self.headers = headers
        super().__init__(code)


class BadRequest(AppError):
    status_code = 400


class Unauthenticated(AppError):
    status_code = 401

    def __init__(self, code: str, message: str | None = None, details: dict | None = None) -> None:
        super().__init__(code, message, details, UNAUTHENTICATED_HEADERS)


class NotFound(AppError):
    status_code = 404


class MethodNotAllowed(AppError):
    status_code = 405


class Conflict(AppError):
    status_code = 409


class PayloadTooLarge(AppError):
    status_code = 413


class UnsupportedMediaType(AppError):
    status_code = 415


class Unprocessable(AppError):
    status_code = 422


class RateLimited(AppError):
    status_code = 429

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            "RATE_LIMITED",
            details={"retry_after_seconds": retry_after_seconds},
            headers={"Retry-After": str(retry_after_seconds)},
        )


class ServiceUnavailable(AppError):
    status_code = 503


def envelope(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def error_response(error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=envelope(error.code, error.message, error.details),
        headers=error.headers,
    )


def internal_error_response() -> JSONResponse:
    return error_response(AppError("INTERNAL_ERROR"))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(HTTPException, _handle_http_exception)
    app.add_exception_handler(IntegrityError, _handle_integrity_error)
    app.add_exception_handler(OperationalError, _handle_operational_error)


def _handle_app_error(request: Request, error: Exception) -> JSONResponse:
    return error_response(error)


def _handle_validation_error(request: Request, error: Exception) -> JSONResponse:
    fields = [
        {"field": _field_name(item["loc"]), "message": _field_message(item["msg"])}
        for item in error.errors()
    ]
    return error_response(Unprocessable("VALIDATION_ERROR", details={"fields": fields}))


def _handle_http_exception(request: Request, error: Exception) -> JSONResponse:
    if error.status_code == 405:
        return error_response(MethodNotAllowed("METHOD_NOT_ALLOWED"))
    if error.status_code == 404:
        return error_response(NotFound("NOT_FOUND"))
    return error_response(AppError("INTERNAL_ERROR"))


def _handle_integrity_error(request: Request, error: Exception) -> JSONResponse:
    constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
    code = CONSTRAINT_ERRORS.get(constraint)
    if code is None:
        return internal_error_response()
    if code in UNPROCESSABLE_CONSTRAINT_CODES:
        return error_response(Unprocessable(code))
    return error_response(Conflict(code))


def _handle_operational_error(request: Request, error: Exception) -> JSONResponse:
    return error_response(ServiceUnavailable("SERVICE_UNAVAILABLE"))


def _field_name(location: tuple) -> str:
    parts = [str(part) for part in location if part != "body"]
    return ".".join(parts) or "body"


def _field_message(message: str) -> str:
    return message.removeprefix("Value error, ")
