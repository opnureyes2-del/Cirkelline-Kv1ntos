"""
i18n API Endpoints

Provides REST endpoints for locale management and translation retrieval.
"""

from fastapi import APIRouter, Request, Response, Depends, Query
from typing import Optional
from pydantic import BaseModel

from . import (
    _,
    get_locale,
    get_direction,
    is_rtl,
    get_translation_manager,
    SUPPORTED_LOCALES,
    DEFAULT_LOCALE,
    RTL_LOCALES
)
from .middleware import (
    LocaleContext,
    get_locale_context,
    set_locale_cookie,
    clear_locale_cookie
)

router = APIRouter(prefix="/api/i18n", tags=["i18n"])


# Response models
class LocaleInfo(BaseModel):
    code: str
    name: str
    native_name: str
    direction: str
    is_default: bool
    is_active: bool


class CurrentLocaleResponse(BaseModel):
    locale: str
    direction: str
    is_rtl: bool
    supported_locales: list[str]


class SetLocaleRequest(BaseModel):
    locale: str


class SetLocaleResponse(BaseModel):
    success: bool
    locale: str
    message: str


class TranslationsResponse(BaseModel):
    locale: str
    translations: dict


# Locale names mapping
LOCALE_NAMES = {
    'da': ('Danish', 'Dansk'),
    'en': ('English', 'English'),
    'sv': ('Swedish', 'Svenska'),
    'de': ('German', 'Deutsch'),
    'ar': ('Arabic', 'العربية'),
}


@router.get("/locales", response_model=list[LocaleInfo])
async def get_supported_locales():
    """
    Get list of all supported locales.

    Returns:
        List of locale information objects
    """
    locales = []
    for code in SUPPORTED_LOCALES:
        english_name, native_name = LOCALE_NAMES.get(code, (code, code))
        locales.append(LocaleInfo(
            code=code,
            name=english_name,
            native_name=native_name,
            direction=get_direction(code),
            is_default=code == DEFAULT_LOCALE,
            is_active=True
        ))
    return locales


@router.get("/current", response_model=CurrentLocaleResponse)
async def get_current_locale(
    locale_ctx: LocaleContext = Depends(get_locale_context)
):
    """
    Get the current detected locale for the request.

    The locale is determined by the following priority:
    1. Query parameter (?locale=en)
    2. Cookie (preferred_locale)
    3. User profile preference
    4. Accept-Language header
    5. Default locale (da)
    """
    return CurrentLocaleResponse(
        locale=locale_ctx.locale,
        direction=locale_ctx.direction,
        is_rtl=locale_ctx.is_rtl,
        supported_locales=SUPPORTED_LOCALES
    )


@router.post("/set", response_model=SetLocaleResponse)
async def set_locale_preference(
    request: Request,
    response: Response,
    data: SetLocaleRequest,
    locale_ctx: LocaleContext = Depends(get_locale_context)
):
    """
    Set locale preference via cookie.

    This sets a persistent cookie that will be used in future requests
    (priority 2 in the detection order).
    """
    if data.locale not in SUPPORTED_LOCALES:
        return SetLocaleResponse(
            success=False,
            locale=locale_ctx.locale,
            message=_('errors.validation.invalidFormat', locale_ctx.locale)
        )

    set_locale_cookie(response, data.locale)

    return SetLocaleResponse(
        success=True,
        locale=data.locale,
        message=_('common.success', data.locale)
    )


@router.delete("/preference")
async def clear_locale_preference(
    response: Response,
    locale_ctx: LocaleContext = Depends(get_locale_context)
):
    """
    Clear locale preference cookie.

    After clearing, locale detection will fall back to
    Accept-Language header or default locale.
    """
    clear_locale_cookie(response)

    return {
        "success": True,
        "message": _('common.success', locale_ctx.locale)
    }


@router.get("/translations", response_model=TranslationsResponse)
async def get_translations(
    locale_ctx: LocaleContext = Depends(get_locale_context),
    namespace: Optional[str] = Query(None, description="Specific namespace to retrieve (e.g., 'common', 'errors')")
):
    """
    Get translations for the current locale.

    Args:
        namespace: Optional namespace to filter translations

    Returns:
        Translation dictionary for the detected locale
    """
    manager = get_translation_manager()
    translations = manager._translations.get(locale_ctx.locale, {})

    if namespace and namespace in translations:
        translations = {namespace: translations[namespace]}

    return TranslationsResponse(
        locale=locale_ctx.locale,
        translations=translations
    )


@router.get("/translate")
async def translate_key(
    key: str = Query(..., description="Translation key (dot-notation, e.g., 'common.loading')"),
    locale_ctx: LocaleContext = Depends(get_locale_context)
):
    """
    Translate a specific key.

    Args:
        key: Translation key in dot-notation

    Returns:
        Translated string
    """
    translated = _(key, locale_ctx.locale)

    return {
        "key": key,
        "locale": locale_ctx.locale,
        "translation": translated,
        "is_fallback": translated == key
    }


@router.get("/direction/{locale}")
async def get_text_direction(locale: str):
    """
    Get text direction for a specific locale.

    Args:
        locale: Locale code

    Returns:
        Text direction information
    """
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    return {
        "locale": locale,
        "direction": get_direction(locale),
        "is_rtl": is_rtl(locale)
    }


# Export router
__all__ = ['router']
