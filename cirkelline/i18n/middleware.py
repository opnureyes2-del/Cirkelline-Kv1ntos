"""
i18n Middleware for FastAPI

Provides automatic locale detection and injection for all API requests.
Implements the strict Locale Detection Priority:
1. Query param (?locale=en)
2. Cookie (preferred_locale)
3. User profile
4. Accept-Language header
5. Default (da)
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

from . import get_locale, get_direction, SUPPORTED_LOCALES, DEFAULT_LOCALE

logger = logging.getLogger(__name__)


class I18nMiddleware(BaseHTTPMiddleware):
    """
    Middleware that detects locale and adds it to request state.
    Also sets appropriate response headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Detect locale using priority order
        locale = get_locale(request)
        direction = get_direction(locale)

        # Store in request state for use in endpoints
        request.state.locale = locale
        request.state.text_direction = direction

        # Log locale detection for debugging
        logger.debug(f"Request locale detected: {locale} (dir: {direction})")

        # Process request
        response = await call_next(request)

        # Add locale headers to response
        response.headers["Content-Language"] = locale
        response.headers["X-Locale"] = locale
        response.headers["X-Text-Direction"] = direction

        # Add Vary header for proper caching
        vary = response.headers.get("Vary", "")
        if "Accept-Language" not in vary:
            if vary:
                response.headers["Vary"] = f"{vary}, Accept-Language"
            else:
                response.headers["Vary"] = "Accept-Language"

        return response


class LocaleContext:
    """
    Context class for locale information.
    Used as a dependency in FastAPI endpoints.
    """

    def __init__(
        self,
        locale: str,
        direction: str,
        is_rtl: bool
    ):
        self.locale = locale
        self.direction = direction
        self.is_rtl = is_rtl

    def __repr__(self) -> str:
        return f"LocaleContext(locale='{self.locale}', direction='{self.direction}')"


def get_locale_context(request: Request) -> LocaleContext:
    """
    FastAPI dependency to get locale context.

    Usage:
        @router.get("/api/example")
        async def example(locale_ctx: LocaleContext = Depends(get_locale_context)):
            return {"locale": locale_ctx.locale}
    """
    locale = getattr(request.state, 'locale', None)

    # If middleware hasn't run, detect locale now
    if locale is None:
        locale = get_locale(request)

    direction = get_direction(locale)
    is_rtl = direction == 'rtl'

    return LocaleContext(
        locale=locale,
        direction=direction,
        is_rtl=is_rtl
    )


def set_locale_cookie(response: Response, locale: str) -> Response:
    """
    Set locale preference cookie.

    Args:
        response: FastAPI Response object
        locale: Locale code to set

    Returns:
        Response with cookie set
    """
    if locale in SUPPORTED_LOCALES:
        response.set_cookie(
            key="preferred_locale",
            value=locale,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=False,  # Allow JS access for client-side detection
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )
    return response


def clear_locale_cookie(response: Response) -> Response:
    """Clear locale preference cookie."""
    response.delete_cookie(key="preferred_locale")
    return response


# Export for easy importing
__all__ = [
    'I18nMiddleware',
    'LocaleContext',
    'get_locale_context',
    'set_locale_cookie',
    'clear_locale_cookie',
]
