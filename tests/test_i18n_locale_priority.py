"""
FASE 2.1: Locale Detection Priority Tests

Comprehensive tests to verify the strict Locale Detection Priority:
1. Query param (?locale=en) - HIGHEST PRIORITY
2. Cookie (preferred_locale)
3. User profile
4. Accept-Language header
5. Default (da) - LOWEST PRIORITY

These tests ensure the priority is "urokkelig" (immutable) as specified.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cirkelline.i18n import (
    get_locale,
    SUPPORTED_LOCALES,
    DEFAULT_LOCALE
)
from cirkelline.i18n.middleware import (
    LocaleContext,
    get_locale_context,
    I18nMiddleware
)


class TestLocaleDetectionPriority:
    """
    Tests for the strict Locale Detection Priority.
    Priority Order (immutable):
    1. Query param (?locale=en)
    2. Cookie (preferred_locale)
    3. User profile
    4. Accept-Language header
    5. Default (da)
    """

    def create_mock_request(
        self,
        query_locale: str = None,
        cookie_locale: str = None,
        user_locale: str = None,
        accept_language: str = None
    ) -> Request:
        """Create a mock request with specified locale sources."""
        request = MagicMock(spec=Request)

        # Query params
        request.query_params = {}
        if query_locale:
            request.query_params['locale'] = query_locale

        # Cookies
        request.cookies = {}
        if cookie_locale:
            request.cookies['preferred_locale'] = cookie_locale

        # User profile
        if user_locale:
            request.state = MagicMock()
            request.state.user = MagicMock()
            request.state.user.preferred_locale = user_locale
        else:
            request.state = MagicMock(spec=[])

        # Headers
        request.headers = {}
        if accept_language:
            request.headers['Accept-Language'] = accept_language

        return request

    # ================================================================
    # PRIORITY 1: Query Parameter Tests
    # ================================================================

    def test_priority1_query_param_overrides_all(self):
        """Query param should override cookie, user profile, and Accept-Language."""
        request = self.create_mock_request(
            query_locale='en',
            cookie_locale='sv',
            user_locale='de',
            accept_language='ar,da'
        )
        assert get_locale(request) == 'en', "Query param should have highest priority"

    def test_priority1_query_param_overrides_cookie(self):
        """Query param should override cookie."""
        request = self.create_mock_request(
            query_locale='de',
            cookie_locale='en'
        )
        assert get_locale(request) == 'de'

    def test_priority1_query_param_overrides_user_profile(self):
        """Query param should override user profile."""
        request = self.create_mock_request(
            query_locale='sv',
            user_locale='en'
        )
        assert get_locale(request) == 'sv'

    def test_priority1_query_param_overrides_accept_language(self):
        """Query param should override Accept-Language header."""
        request = self.create_mock_request(
            query_locale='ar',
            accept_language='en-US,en;q=0.9'
        )
        assert get_locale(request) == 'ar'

    def test_priority1_invalid_query_param_ignored(self):
        """Invalid query param should fall through to next priority."""
        request = self.create_mock_request(
            query_locale='invalid',
            cookie_locale='en'
        )
        assert get_locale(request) == 'en', "Invalid query param should be ignored"

    # ================================================================
    # PRIORITY 2: Cookie Tests
    # ================================================================

    def test_priority2_cookie_used_without_query(self):
        """Cookie should be used when no query param."""
        request = self.create_mock_request(
            cookie_locale='en',
            user_locale='de',
            accept_language='ar'
        )
        assert get_locale(request) == 'en'

    def test_priority2_cookie_overrides_user_profile(self):
        """Cookie should override user profile."""
        request = self.create_mock_request(
            cookie_locale='sv',
            user_locale='de'
        )
        assert get_locale(request) == 'sv'

    def test_priority2_cookie_overrides_accept_language(self):
        """Cookie should override Accept-Language header."""
        request = self.create_mock_request(
            cookie_locale='de',
            accept_language='en-US'
        )
        assert get_locale(request) == 'de'

    def test_priority2_invalid_cookie_ignored(self):
        """Invalid cookie should fall through to next priority."""
        request = self.create_mock_request(
            cookie_locale='invalid',
            user_locale='en'
        )
        assert get_locale(request) == 'en'

    # ================================================================
    # PRIORITY 3: User Profile Tests
    # ================================================================

    def test_priority3_user_profile_used_without_query_or_cookie(self):
        """User profile should be used when no query or cookie."""
        request = self.create_mock_request(
            user_locale='de',
            accept_language='en'
        )
        assert get_locale(request) == 'de'

    def test_priority3_user_profile_overrides_accept_language(self):
        """User profile should override Accept-Language."""
        request = self.create_mock_request(
            user_locale='sv',
            accept_language='ar,de'
        )
        assert get_locale(request) == 'sv'

    def test_priority3_none_user_locale_ignored(self):
        """None user locale should fall through."""
        request = self.create_mock_request(
            accept_language='en-US'
        )
        # User state exists but no preferred_locale
        request.state = MagicMock()
        request.state.user = MagicMock()
        request.state.user.preferred_locale = None

        assert get_locale(request) == 'en'

    def test_priority3_empty_user_locale_ignored(self):
        """Empty string user locale should fall through."""
        request = self.create_mock_request(
            accept_language='de-DE'
        )
        request.state = MagicMock()
        request.state.user = MagicMock()
        request.state.user.preferred_locale = ''

        assert get_locale(request) == 'de'

    # ================================================================
    # PRIORITY 4: Accept-Language Header Tests
    # ================================================================

    def test_priority4_accept_language_used_as_fallback(self):
        """Accept-Language should be used as fallback."""
        request = self.create_mock_request(
            accept_language='en-US,en;q=0.9,da;q=0.8'
        )
        assert get_locale(request) == 'en'

    def test_priority4_accept_language_first_supported_wins(self):
        """First supported locale in Accept-Language should win."""
        request = self.create_mock_request(
            accept_language='fr-FR,de-DE;q=0.9,en;q=0.8'
        )
        # fr not supported, de is, so de should win
        assert get_locale(request) == 'de'

    def test_priority4_accept_language_with_region(self):
        """Accept-Language with region codes should work."""
        request = self.create_mock_request(
            accept_language='sv-SE,sv;q=0.9'
        )
        assert get_locale(request) == 'sv'

    def test_priority4_accept_language_arabic(self):
        """Accept-Language with Arabic should work."""
        request = self.create_mock_request(
            accept_language='ar-SA,ar;q=0.9'
        )
        assert get_locale(request) == 'ar'

    def test_priority4_no_supported_accept_language_falls_to_default(self):
        """No supported Accept-Language should fall to default."""
        request = self.create_mock_request(
            accept_language='fr-FR,es-ES,pt-BR'
        )
        assert get_locale(request) == DEFAULT_LOCALE

    # ================================================================
    # PRIORITY 5: Default Locale Tests
    # ================================================================

    def test_priority5_default_used_when_nothing_else(self):
        """Default locale should be used when no other source."""
        request = self.create_mock_request()
        assert get_locale(request) == DEFAULT_LOCALE

    def test_priority5_default_is_danish(self):
        """Default locale should be Danish (da)."""
        assert DEFAULT_LOCALE == 'da'

    def test_priority5_empty_accept_language_uses_default(self):
        """Empty Accept-Language should use default."""
        request = self.create_mock_request(
            accept_language=''
        )
        assert get_locale(request) == 'da'

    # ================================================================
    # All Supported Locales Tests
    # ================================================================

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_all_locales_work_via_query_param(self, locale):
        """All supported locales should work via query param."""
        request = self.create_mock_request(query_locale=locale)
        assert get_locale(request) == locale

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_all_locales_work_via_cookie(self, locale):
        """All supported locales should work via cookie."""
        request = self.create_mock_request(cookie_locale=locale)
        assert get_locale(request) == locale

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_all_locales_work_via_user_profile(self, locale):
        """All supported locales should work via user profile."""
        request = self.create_mock_request(user_locale=locale)
        assert get_locale(request) == locale

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_all_locales_work_via_accept_language(self, locale):
        """All supported locales should work via Accept-Language."""
        request = self.create_mock_request(accept_language=locale)
        assert get_locale(request) == locale

    # ================================================================
    # Edge Cases and Security Tests
    # ================================================================

    def test_case_insensitive_query_param(self):
        """Query param locale detection should handle lowercase."""
        request = self.create_mock_request(query_locale='EN')
        # Should not match because we use lowercase comparison
        # and SUPPORTED_LOCALES uses lowercase
        # This tests current implementation behavior
        result = get_locale(request)
        # EN is not in SUPPORTED_LOCALES (en is), so should fall to default
        assert result == DEFAULT_LOCALE

    def test_injection_attempt_query_param(self):
        """SQL injection attempt in query param should be safe."""
        request = self.create_mock_request(
            query_locale="en'; DROP TABLE users;--"
        )
        assert get_locale(request) == DEFAULT_LOCALE

    def test_xss_attempt_query_param(self):
        """XSS attempt in query param should be safe."""
        request = self.create_mock_request(
            query_locale="<script>alert('xss')</script>"
        )
        assert get_locale(request) == DEFAULT_LOCALE

    def test_very_long_locale_query_param(self):
        """Very long locale string should be handled safely."""
        request = self.create_mock_request(
            query_locale="a" * 10000
        )
        assert get_locale(request) == DEFAULT_LOCALE

    def test_unicode_locale_query_param(self):
        """Unicode in locale should be handled safely."""
        request = self.create_mock_request(
            query_locale="日本語"
        )
        assert get_locale(request) == DEFAULT_LOCALE


class TestLocaleContext:
    """Tests for the LocaleContext dependency."""

    def test_locale_context_creation(self):
        """LocaleContext should be created correctly."""
        ctx = LocaleContext(locale='en', direction='ltr', is_rtl=False)
        assert ctx.locale == 'en'
        assert ctx.direction == 'ltr'
        assert ctx.is_rtl is False

    def test_locale_context_rtl(self):
        """LocaleContext should handle RTL correctly."""
        ctx = LocaleContext(locale='ar', direction='rtl', is_rtl=True)
        assert ctx.locale == 'ar'
        assert ctx.direction == 'rtl'
        assert ctx.is_rtl is True

    def test_locale_context_repr(self):
        """LocaleContext should have useful repr."""
        ctx = LocaleContext(locale='da', direction='ltr', is_rtl=False)
        assert 'da' in repr(ctx)
        assert 'ltr' in repr(ctx)


class TestPriorityOrderDocumentation:
    """
    Meta-tests to ensure the priority order is documented correctly.
    """

    def test_priority_documented_in_get_locale(self):
        """get_locale docstring should document priority order."""
        docstring = get_locale.__doc__
        assert 'Query parameter' in docstring or 'query' in docstring.lower()
        assert 'Cookie' in docstring or 'cookie' in docstring.lower()
        assert 'User profile' in docstring or 'user' in docstring.lower()
        assert 'Accept-Language' in docstring
        assert 'Default' in docstring or 'default' in docstring.lower()

    def test_supported_locales_complete(self):
        """All required locales should be supported."""
        required = ['da', 'en', 'sv', 'de', 'ar']
        for locale in required:
            assert locale in SUPPORTED_LOCALES, f"Missing required locale: {locale}"


# Run if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
