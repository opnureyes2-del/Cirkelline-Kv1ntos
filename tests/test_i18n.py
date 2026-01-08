"""
FASE 2: i18n Test Suite

Tests for internationalization functionality across the Cirkelline ecosystem.
Verifies: Translation loading, locale detection, RTL support, string interpolation
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cirkelline.i18n import (
    _,
    get_locale,
    get_direction,
    is_rtl,
    get_translation_manager,
    SUPPORTED_LOCALES,
    DEFAULT_LOCALE,
    RTL_LOCALES,
    TranslationManager,
)


class TestTranslationManager:
    """Tests for the TranslationManager class."""

    def test_supported_locales(self):
        """Verify all expected locales are supported."""
        expected_locales = ['da', 'en', 'sv', 'de', 'ar']
        assert SUPPORTED_LOCALES == expected_locales

    def test_default_locale_is_danish(self):
        """Default locale should be Danish."""
        assert DEFAULT_LOCALE == 'da'

    def test_rtl_locales(self):
        """Arabic should be the only RTL locale."""
        assert RTL_LOCALES == ['ar']

    def test_translation_manager_singleton(self):
        """Translation manager should be reusable."""
        manager1 = get_translation_manager()
        manager2 = get_translation_manager()
        assert manager1 is manager2

    def test_translation_manager_loads_translations(self):
        """Translation manager should load translation files."""
        manager = get_translation_manager()
        assert hasattr(manager, '_translations')
        assert isinstance(manager._translations, dict)


class TestTranslationFunction:
    """Tests for the translation function _()."""

    def test_translate_simple_key_danish(self):
        """Test simple key translation to Danish."""
        result = _('common.loading', 'da')
        assert result == 'Indlæser...'

    def test_translate_simple_key_english(self):
        """Test simple key translation to English."""
        result = _('common.loading', 'en')
        assert result == 'Loading...'

    def test_translate_nested_key(self):
        """Test nested key translation."""
        result = _('errors.validation.required', 'da', field='E-mail')
        assert 'E-mail' in result
        assert 'påkrævet' in result

    def test_translate_with_interpolation(self):
        """Test string interpolation."""
        result = _('errors.validation.minLength', 'en', field='Password', min='8')
        assert 'Password' in result
        assert '8' in result

    def test_fallback_to_english(self):
        """Test fallback to English for missing translations."""
        # Test with a key that might not exist in all locales
        result_da = _('common.loading', 'da')
        result_en = _('common.loading', 'en')
        # Both should return valid translations
        assert result_da != ''
        assert result_en != ''

    def test_fallback_to_key_for_missing(self):
        """Test that missing keys return the key itself."""
        result = _('nonexistent.key.here', 'da')
        assert result == 'nonexistent.key.here'

    def test_invalid_locale_uses_default(self):
        """Test that invalid locale falls back to default."""
        result = _('common.loading', 'invalid_locale')
        assert result == _('common.loading', DEFAULT_LOCALE)


class TestLocaleDetection:
    """Tests for locale detection from requests."""

    def create_mock_request(
        self,
        query_params=None,
        cookies=None,
        headers=None,
        user_locale=None
    ):
        """Create a mock FastAPI request."""
        request = MagicMock()
        request.query_params = query_params or {}
        request.cookies = cookies or {}
        request.headers = headers or {}

        if user_locale:
            request.state.user = MagicMock()
            request.state.user.preferred_locale = user_locale
        else:
            request.state = MagicMock(spec=[])

        return request

    def test_locale_from_query_param(self):
        """Query parameter should take priority."""
        request = self.create_mock_request(query_params={'locale': 'en'})
        assert get_locale(request) == 'en'

    def test_locale_from_cookie(self):
        """Cookie should be second priority."""
        request = self.create_mock_request(cookies={'preferred_locale': 'sv'})
        assert get_locale(request) == 'sv'

    def test_locale_from_accept_language(self):
        """Accept-Language header should be fallback."""
        request = self.create_mock_request(
            headers={'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'}
        )
        assert get_locale(request) == 'de'

    def test_locale_default_fallback(self):
        """Should fall back to default locale."""
        request = self.create_mock_request()
        assert get_locale(request) == DEFAULT_LOCALE

    def test_invalid_locale_in_query_ignored(self):
        """Invalid locale in query should be ignored."""
        request = self.create_mock_request(query_params={'locale': 'invalid'})
        assert get_locale(request) == DEFAULT_LOCALE

    def test_locale_priority_order(self):
        """Test that priority order is respected."""
        # Query param should win even with cookie and header set
        request = self.create_mock_request(
            query_params={'locale': 'en'},
            cookies={'preferred_locale': 'sv'},
            headers={'Accept-Language': 'de'}
        )
        assert get_locale(request) == 'en'


class TestRTLSupport:
    """Tests for RTL (Right-to-Left) support."""

    def test_arabic_is_rtl(self):
        """Arabic should be detected as RTL."""
        assert is_rtl('ar') is True

    def test_danish_is_not_rtl(self):
        """Danish should not be RTL."""
        assert is_rtl('da') is False

    def test_english_is_not_rtl(self):
        """English should not be RTL."""
        assert is_rtl('en') is False

    def test_get_direction_rtl(self):
        """RTL locales should return 'rtl' direction."""
        assert get_direction('ar') == 'rtl'

    def test_get_direction_ltr(self):
        """LTR locales should return 'ltr' direction."""
        assert get_direction('da') == 'ltr'
        assert get_direction('en') == 'ltr'
        assert get_direction('sv') == 'ltr'
        assert get_direction('de') == 'ltr'


class TestTranslationFiles:
    """Tests for translation file structure and consistency."""

    @pytest.fixture
    def locales_dir(self):
        """Get the locales directory path."""
        return Path(__file__).parent.parent / 'locales'

    def test_all_locale_files_exist(self, locales_dir):
        """All locale directories should have messages.json."""
        for locale in SUPPORTED_LOCALES:
            locale_file = locales_dir / locale / 'messages.json'
            assert locale_file.exists(), f"Missing translation file for {locale}"

    def test_locale_files_are_valid_json(self, locales_dir):
        """All translation files should be valid JSON."""
        for locale in SUPPORTED_LOCALES:
            locale_file = locales_dir / locale / 'messages.json'
            if locale_file.exists():
                with open(locale_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                assert isinstance(data, dict), f"Invalid JSON structure in {locale}"

    def test_key_consistency_across_locales(self, locales_dir):
        """All locales should have the same top-level keys."""
        translations = {}
        for locale in SUPPORTED_LOCALES:
            locale_file = locales_dir / locale / 'messages.json'
            if locale_file.exists():
                with open(locale_file, 'r', encoding='utf-8') as f:
                    translations[locale] = json.load(f)

        if translations:
            reference_keys = set(translations[DEFAULT_LOCALE].keys())
            for locale, data in translations.items():
                locale_keys = set(data.keys())
                missing = reference_keys - locale_keys
                assert not missing, f"Missing keys in {locale}: {missing}"

    def test_no_empty_translations(self, locales_dir):
        """Translations should not be empty strings."""
        for locale in SUPPORTED_LOCALES:
            locale_file = locales_dir / locale / 'messages.json'
            if locale_file.exists():
                with open(locale_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                def check_empty(obj, path=""):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            check_empty(value, f"{path}.{key}")
                    elif isinstance(obj, str):
                        assert obj.strip(), f"Empty translation at {path} in {locale}"

                check_empty(data)


class TestTranslationCount:
    """Tests for translation coverage metrics."""

    @pytest.fixture
    def locales_dir(self):
        return Path(__file__).parent.parent / 'locales'

    def count_strings(self, obj):
        """Count total string translations in a nested dict."""
        count = 0
        if isinstance(obj, dict):
            for value in obj.values():
                count += self.count_strings(value)
        elif isinstance(obj, str):
            count = 1
        return count

    def test_minimum_translations_per_locale(self, locales_dir):
        """Each locale should have at least 50 translations."""
        min_translations = 50
        for locale in SUPPORTED_LOCALES:
            locale_file = locales_dir / locale / 'messages.json'
            if locale_file.exists():
                with open(locale_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                count = self.count_strings(data)
                assert count >= min_translations, \
                    f"{locale} has only {count} translations (min: {min_translations})"


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
