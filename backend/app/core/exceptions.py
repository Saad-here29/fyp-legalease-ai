"""Application-level exceptions — every error has a code, message, and hint
so the frontend can render USE-04 compliant error toasts."""


class AppException(Exception):
    status_code: int = 500
    code: str = "internal_error"
    message: str = "Something went wrong."
    hint: str = "Please try again. If the problem continues, contact support."

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        status_code: int | None = None,
        hint: str | None = None,
    ):
        if message:
            self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        if hint:
            self.hint = hint
        super().__init__(self.message)


class InvalidCredentials(AppException):
    status_code = 401
    code = "invalid_credentials"
    message = "Invalid email or password."
    hint = "Double-check your email and password."


class AccountLocked(AppException):
    status_code = 423
    code = "account_locked"
    message = "Account locked after multiple failed attempts."
    hint = "Reset your password or wait before trying again."


class NotAuthenticated(AppException):
    status_code = 401
    code = "not_authenticated"
    message = "Authentication required."
    hint = "Sign in to continue."


class NotAuthorized(AppException):
    status_code = 403
    code = "not_authorized"
    message = "You don't have permission to perform this action."
    hint = "Contact your lawyer or admin if you think this is a mistake."


class NotFound(AppException):
    status_code = 404
    code = "not_found"
    message = "Resource not found."
    hint = "Check the URL or refresh the page."


class ValidationFailed(AppException):
    status_code = 422
    code = "validation_failed"
    message = "Some fields are invalid."
    hint = "Review the highlighted fields and try again."


class IllegalStateTransition(AppException):
    status_code = 409
    code = "illegal_state_transition"
    message = "The requested status change is not allowed."
    hint = "Refresh the case to see its current status."


class FileTooLarge(AppException):
    status_code = 413
    code = "file_too_large"
    message = "File exceeds the maximum allowed size."
    hint = "Try compressing the file or splitting it into smaller documents."


class UnsupportedMediaType(AppException):
    status_code = 415
    code = "unsupported_media_type"
    message = "This file format is not supported."
    hint = "Allowed formats are PDF, DOCX, TXT, PNG, and JPG."


class AIServiceUnavailable(AppException):
    status_code = 503
    code = "ai_unavailable"
    message = "The AI service is temporarily unavailable."
    hint = "Try again in a few seconds. Core features still work without AI."
