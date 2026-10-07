"""
Application domain exceptions and custom error types.
"""
from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid or missing authentication credentials", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
            details=details
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Insufficient permissions to perform this action", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="PERMISSION_DENIED",
            details=details
        )


class NotFoundError(AppException):
    def __init__(self, message: str = "Requested resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details=details
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict occurred", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="RESOURCE_CONFLICT",
            details=details
        )


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again later.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


class InvalidOTPError(AppException):
    def __init__(self, message: str = "Invalid or expired verification code", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_OTP",
            details=details
        )


class BadRequestError(AppException):
    def __init__(self, message: str = "Invalid request parameters", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BAD_REQUEST",
            details=details
        )


class AccountSuspendedError(AppException):
    def __init__(self, message: str = "Account is temporarily suspended due to community guidelines violations", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="ACCOUNT_SUSPENDED",
            details=details
        )


