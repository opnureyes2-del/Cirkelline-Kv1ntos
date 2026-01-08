"""
i18n-aware HTTP Exceptions

Provides localized error messages for API responses.
"""

from fastapi import HTTPException, Request
from typing import Optional, Any

from . import _, get_locale, SUPPORTED_LOCALES


class I18nHTTPException(HTTPException):
    """
    HTTPException with internationalized error messages.

    Usage:
        raise I18nHTTPException(
            request=request,
            status_code=401,
            message_key="errors.unauthorized"
        )
    """

    def __init__(
        self,
        request: Request,
        status_code: int,
        message_key: str,
        headers: Optional[dict[str, str]] = None,
        **kwargs
    ):
        locale = get_locale(request)
        detail = _(message_key, locale, **kwargs)

        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers
        )

        # Store additional info for logging
        self.message_key = message_key
        self.locale = locale
        self.kwargs = kwargs


def raise_i18n_error(
    request: Request,
    status_code: int,
    message_key: str,
    **kwargs
) -> None:
    """
    Raise an internationalized HTTP exception.

    Args:
        request: FastAPI Request object
        status_code: HTTP status code
        message_key: Translation key (e.g., 'errors.unauthorized')
        **kwargs: Variables to interpolate into the message
    """
    raise I18nHTTPException(
        request=request,
        status_code=status_code,
        message_key=message_key,
        **kwargs
    )


# Convenience functions for common errors

def raise_unauthorized(request: Request, message_key: str = "errors.unauthorized") -> None:
    """Raise 401 Unauthorized error."""
    raise_i18n_error(request, 401, message_key)


def raise_forbidden(request: Request, message_key: str = "errors.forbidden") -> None:
    """Raise 403 Forbidden error."""
    raise_i18n_error(request, 403, message_key)


def raise_not_found(request: Request, message_key: str = "errors.notFound") -> None:
    """Raise 404 Not Found error."""
    raise_i18n_error(request, 404, message_key)


def raise_validation_error(
    request: Request,
    field: str,
    error_type: str = "required"
) -> None:
    """
    Raise 422 Validation error.

    Args:
        request: FastAPI Request
        field: Field name that failed validation
        error_type: Type of validation error (required, email, minLength, etc.)
    """
    message_key = f"errors.validation.{error_type}"
    raise_i18n_error(request, 422, message_key, field=field)


def raise_server_error(request: Request, message_key: str = "errors.serverError") -> None:
    """Raise 500 Internal Server Error."""
    raise_i18n_error(request, 500, message_key)


def raise_rate_limited(request: Request, message_key: str = "errors.rateLimited") -> None:
    """Raise 429 Too Many Requests error."""
    raise_i18n_error(request, 429, message_key)


def raise_timeout(request: Request, message_key: str = "errors.timeout") -> None:
    """Raise 408 Request Timeout error."""
    raise_i18n_error(request, 408, message_key)


# Export
__all__ = [
    'I18nHTTPException',
    'raise_i18n_error',
    'raise_unauthorized',
    'raise_forbidden',
    'raise_not_found',
    'raise_validation_error',
    'raise_server_error',
    'raise_rate_limited',
    'raise_timeout',
]
