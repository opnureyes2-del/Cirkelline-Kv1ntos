"""
Cirkelline i18n Module - Internationalization Support

Provides translation utilities for the Cirkelline System backend.
Supports: Danish (da), English (en), Swedish (sv), German (de), Arabic (ar)
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional
import json
import os

from fastapi import Request

# Configuration
SUPPORTED_LOCALES = ['da', 'en', 'sv', 'de', 'ar']
DEFAULT_LOCALE = 'da'
RTL_LOCALES = ['ar']

# Path to locale files
LOCALES_DIR = Path(__file__).parent.parent.parent / 'locales'


class TranslationManager:
    """Manages translations for the application."""

    def __init__(self):
        self._translations: dict[str, dict] = {}
        self._load_translations()

    def _load_translations(self):
        """Load all translation files."""
        for locale in SUPPORTED_LOCALES:
            locale_file = LOCALES_DIR / locale / 'messages.json'
            if locale_file.exists():
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self._translations[locale] = json.load(f)
            else:
                self._translations[locale] = {}

    def reload(self):
        """Reload translations from disk."""
        self._translations.clear()
        self._load_translations()

    def get(self, key: str, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
        """
        Get a translated string.

        Args:
            key: The translation key (dot-notation, e.g., 'errors.unauthorized')
            locale: The locale to use
            **kwargs: Variables to interpolate into the string

        Returns:
            The translated string, or the key if not found
        """
        if locale not in SUPPORTED_LOCALES:
            locale = DEFAULT_LOCALE

        translations = self._translations.get(locale, {})

        # Navigate nested keys
        value = translations
        for part in key.split('.'):
            if isinstance(value, dict):
                value = value.get(part, {})
            else:
                value = {}

        # If we got a string, use it; otherwise return the key
        if isinstance(value, str):
            if kwargs:
                try:
                    return value.format(**kwargs)
                except KeyError:
                    return value
            return value

        # Fallback to English if available
        if locale != 'en':
            return self.get(key, 'en', **kwargs)

        return key


# Global translation manager instance
_manager: Optional[TranslationManager] = None


def get_translation_manager() -> TranslationManager:
    """Get or create the global translation manager."""
    global _manager
    if _manager is None:
        _manager = TranslationManager()
    return _manager


def _(key: str, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
    """
    Translate a string.

    This is the primary translation function to use throughout the codebase.

    Examples:
        _('common.loading')  # Returns 'Indlæser...' for Danish
        _('errors.validation.required', field='Email')  # Returns 'Email er påkrævet'
    """
    return get_translation_manager().get(key, locale, **kwargs)


def get_locale(request: Request) -> str:
    """
    Determine the locale for a request.

    Priority:
    1. Query parameter (?locale=en)
    2. Cookie (preferred_locale)
    3. User profile preference (if authenticated)
    4. Accept-Language header
    5. Default locale (da)
    """
    # 1. Query parameter
    if locale := request.query_params.get('locale'):
        if locale in SUPPORTED_LOCALES:
            return locale

    # 2. Cookie
    if locale := request.cookies.get('preferred_locale'):
        if locale in SUPPORTED_LOCALES:
            return locale

    # 3. User profile (if authenticated)
    if hasattr(request.state, 'user'):
        user = request.state.user
        if hasattr(user, 'preferred_locale'):
            locale = user.preferred_locale
            if locale and locale in SUPPORTED_LOCALES:
                return locale

    # 4. Accept-Language header
    accept_language = request.headers.get('Accept-Language', '')
    for lang_part in accept_language.split(','):
        lang = lang_part.split(';')[0].strip()
        # Handle both 'da' and 'da-DK' formats
        locale = lang[:2].lower()
        if locale in SUPPORTED_LOCALES:
            return locale

    # 5. Default
    return DEFAULT_LOCALE


def get_direction(locale: str) -> str:
    """Get text direction for a locale."""
    return 'rtl' if locale in RTL_LOCALES else 'ltr'


def is_rtl(locale: str) -> bool:
    """Check if a locale is right-to-left."""
    return locale in RTL_LOCALES


# Export commonly used functions and constants
__all__ = [
    '_',
    'get_locale',
    'get_direction',
    'is_rtl',
    'get_translation_manager',
    'SUPPORTED_LOCALES',
    'DEFAULT_LOCALE',
    'RTL_LOCALES',
    'TranslationManager',
]
