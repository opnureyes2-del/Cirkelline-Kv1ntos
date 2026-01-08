-- FASE 2: Internationalization (i18n) Database Setup
-- Migration script for all Cirkelline databases
-- Version: 1.0.0
-- Date: 2025-12-09

-- =====================================================
-- 1. TRANSLATIONS TABLE
-- =====================================================
-- Stores dynamic content translations (not static UI strings)
-- Use cases: user-generated content, dynamic messages, emails

CREATE TABLE IF NOT EXISTS ai.translations (
    id SERIAL PRIMARY KEY,
    content_key TEXT NOT NULL,
    locale VARCHAR(10) NOT NULL,
    translated_text TEXT NOT NULL,
    context TEXT,                           -- Optional context for disambiguation
    category VARCHAR(50) DEFAULT 'general', -- 'ui', 'error', 'notification', 'email', 'system'
    is_auto_translated BOOLEAN DEFAULT FALSE,
    translator_id UUID,                     -- Reference to user who translated (if manual)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_translation UNIQUE(content_key, locale, context)
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_translations_locale ON ai.translations(locale);
CREATE INDEX IF NOT EXISTS idx_translations_key ON ai.translations(content_key);
CREATE INDEX IF NOT EXISTS idx_translations_category ON ai.translations(category);
CREATE INDEX IF NOT EXISTS idx_translations_key_locale ON ai.translations(content_key, locale);

-- =====================================================
-- 2. USER LOCALE PREFERENCES
-- =====================================================
-- Add preferred_locale column to users table

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS preferred_locale VARCHAR(10) DEFAULT 'da';

-- Index for efficient locale-based queries
CREATE INDEX IF NOT EXISTS idx_users_locale ON public.users(preferred_locale);

-- =====================================================
-- 3. SUPPORTED LOCALES TABLE
-- =====================================================
-- Master list of supported locales with metadata

CREATE TABLE IF NOT EXISTS ai.supported_locales (
    code VARCHAR(10) PRIMARY KEY,
    name_native VARCHAR(100) NOT NULL,
    name_english VARCHAR(100) NOT NULL,
    direction VARCHAR(3) DEFAULT 'ltr' CHECK (direction IN ('ltr', 'rtl')),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert supported locales
INSERT INTO ai.supported_locales (code, name_native, name_english, direction, is_active, is_default, sort_order)
VALUES
    ('da', 'Dansk', 'Danish', 'ltr', TRUE, TRUE, 1),
    ('en', 'English', 'English', 'ltr', TRUE, FALSE, 2),
    ('sv', 'Svenska', 'Swedish', 'ltr', TRUE, FALSE, 3),
    ('de', 'Deutsch', 'German', 'ltr', TRUE, FALSE, 4),
    ('ar', 'العربية', 'Arabic', 'rtl', TRUE, FALSE, 5)
ON CONFLICT (code) DO UPDATE SET
    name_native = EXCLUDED.name_native,
    name_english = EXCLUDED.name_english,
    direction = EXCLUDED.direction,
    is_active = EXCLUDED.is_active,
    sort_order = EXCLUDED.sort_order;

-- =====================================================
-- 4. TRANSLATION AUDIT LOG
-- =====================================================
-- Track changes to translations for compliance

CREATE TABLE IF NOT EXISTS ai.translation_audit_log (
    id SERIAL PRIMARY KEY,
    translation_id INTEGER REFERENCES ai.translations(id),
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'delete')),
    old_value TEXT,
    new_value TEXT,
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET
);

CREATE INDEX IF NOT EXISTS idx_audit_translation_id ON ai.translation_audit_log(translation_id);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON ai.translation_audit_log(changed_at);

-- =====================================================
-- 5. TRANSLATION FUNCTIONS
-- =====================================================

-- Function to get translated text with fallback
CREATE OR REPLACE FUNCTION ai.get_translation(
    p_key TEXT,
    p_locale VARCHAR(10) DEFAULT 'da',
    p_context TEXT DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    v_result TEXT;
BEGIN
    -- Try exact match
    SELECT translated_text INTO v_result
    FROM ai.translations
    WHERE content_key = p_key
      AND locale = p_locale
      AND (context = p_context OR (context IS NULL AND p_context IS NULL))
    LIMIT 1;

    -- Fallback to English if not found
    IF v_result IS NULL AND p_locale != 'en' THEN
        SELECT translated_text INTO v_result
        FROM ai.translations
        WHERE content_key = p_key
          AND locale = 'en'
          AND (context = p_context OR (context IS NULL AND p_context IS NULL))
        LIMIT 1;
    END IF;

    -- Return key if no translation found
    RETURN COALESCE(v_result, p_key);
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to upsert translation
CREATE OR REPLACE FUNCTION ai.upsert_translation(
    p_key TEXT,
    p_locale VARCHAR(10),
    p_text TEXT,
    p_context TEXT DEFAULT NULL,
    p_category VARCHAR(50) DEFAULT 'general',
    p_is_auto BOOLEAN DEFAULT FALSE,
    p_translator_id UUID DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO ai.translations (content_key, locale, translated_text, context, category, is_auto_translated, translator_id)
    VALUES (p_key, p_locale, p_text, p_context, p_category, p_is_auto, p_translator_id)
    ON CONFLICT (content_key, locale, context) DO UPDATE SET
        translated_text = EXCLUDED.translated_text,
        is_auto_translated = EXCLUDED.is_auto_translated,
        translator_id = EXCLUDED.translator_id,
        updated_at = NOW()
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6. TRIGGER FOR UPDATED_AT
-- =====================================================

CREATE OR REPLACE FUNCTION ai.update_translation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS translations_updated_at ON ai.translations;
CREATE TRIGGER translations_updated_at
    BEFORE UPDATE ON ai.translations
    FOR EACH ROW
    EXECUTE FUNCTION ai.update_translation_timestamp();

-- =====================================================
-- 7. INITIAL SYSTEM TRANSLATIONS
-- =====================================================
-- Common error messages that might be stored in DB

INSERT INTO ai.translations (content_key, locale, translated_text, category) VALUES
-- Danish
('system.error.internal', 'da', 'Der opstod en intern fejl. Prøv igen senere.', 'error'),
('system.error.unauthorized', 'da', 'Du har ikke adgang til denne ressource.', 'error'),
('system.error.not_found', 'da', 'Ressourcen blev ikke fundet.', 'error'),
('system.error.validation', 'da', 'Valideringsfejl. Tjek dine indtastninger.', 'error'),
('system.success.saved', 'da', 'Dine ændringer er gemt.', 'notification'),
('system.success.deleted', 'da', 'Elementet er slettet.', 'notification'),
-- English
('system.error.internal', 'en', 'An internal error occurred. Please try again later.', 'error'),
('system.error.unauthorized', 'en', 'You do not have access to this resource.', 'error'),
('system.error.not_found', 'en', 'Resource not found.', 'error'),
('system.error.validation', 'en', 'Validation error. Please check your input.', 'error'),
('system.success.saved', 'en', 'Your changes have been saved.', 'notification'),
('system.success.deleted', 'en', 'Item has been deleted.', 'notification')
ON CONFLICT (content_key, locale, context) DO NOTHING;

-- =====================================================
-- 8. VERIFICATION
-- =====================================================

-- Verify installation
DO $$
BEGIN
    RAISE NOTICE 'i18n Migration completed successfully!';
    RAISE NOTICE 'Tables created: ai.translations, ai.supported_locales, ai.translation_audit_log';
    RAISE NOTICE 'Functions created: ai.get_translation, ai.upsert_translation';
    RAISE NOTICE 'Supported locales: da, en, sv, de, ar';
END $$;
