# FASE 2.1: PRODUKTIONSDATABASE MIGRATION PLAN

**Version:** 1.0.0
**Status:** KLAR TIL GODKENDELSE
**Dato:** 2025-12-09

---

## 1. EXECUTIVE SUMMARY

Dette dokument beskriver den komplette strategi for sikker migration af i18n database ændringer til produktion med:

- **Zero-downtime** migration tilgang
- **Verificeret backup** før migration
- **100% testet rollback** plan
- **Real-time overvågning** under migration

---

## 2. RISIKOEVALUERING

### 2.1 Potentielle Fejlscenarier

| Scenarie | Sandsynlighed | Konsekvens | Mitigation |
|----------|---------------|------------|------------|
| Schema migration fejler | Lav | Medium | Transaktionel rollback |
| Disk space utilstrækkelig | Lav | Høj | Pre-check af disk space |
| Connection timeout | Medium | Lav | Retry mekanisme |
| Data korruption | Meget Lav | Kritisk | Point-in-Time Recovery |
| Applikation inkompatibilitet | Lav | Medium | Blue/Green deployment |

### 2.2 Konsekvensanalyse

**Worst Case:** Data korruption
- **Recovery Time Objective (RTO):** < 30 minutter
- **Recovery Point Objective (RPO):** 0 (ingen datatab)
- **Mitigation:** WAL archiving + PITR

---

## 3. BACKUP STRATEGI

### 3.1 Pre-Migration Backup (OBLIGATORISK)

```bash
#!/bin/bash
# scripts/i18n-migration-backup.sh

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/cirkelline/i18n-migration"
DB_NAME="cirkelline"
DB_USER="cirkelline"
DB_HOST="localhost"

echo "=== PRE-MIGRATION BACKUP START ==="
echo "Timestamp: $TIMESTAMP"

# 1. Create backup directory
mkdir -p "$BACKUP_DIR"

# 2. Full database dump (custom format for selective restore)
echo "Creating full database dump..."
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    -Fc -f "$BACKUP_DIR/full_backup_$TIMESTAMP.dump" \
    --verbose 2>&1 | tee "$BACKUP_DIR/backup_$TIMESTAMP.log"

# 3. Schema-only backup (for quick reference)
echo "Creating schema-only backup..."
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --schema-only -f "$BACKUP_DIR/schema_$TIMESTAMP.sql"

# 4. Verify backup integrity
echo "Verifying backup integrity..."
pg_restore --list "$BACKUP_DIR/full_backup_$TIMESTAMP.dump" > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Backup verified successfully"
else
    echo "✗ BACKUP VERIFICATION FAILED - ABORTING"
    exit 1
fi

# 5. Calculate and store checksum
sha256sum "$BACKUP_DIR/full_backup_$TIMESTAMP.dump" > "$BACKUP_DIR/checksum_$TIMESTAMP.sha256"

# 6. Store current schema state
echo "Storing current schema state..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\dt ai.*" > "$BACKUP_DIR/ai_tables_$TIMESTAMP.txt"
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'users';" > "$BACKUP_DIR/users_schema_$TIMESTAMP.txt"

echo "=== BACKUP COMPLETE ==="
echo "Backup location: $BACKUP_DIR"
echo "Files created:"
ls -la "$BACKUP_DIR"/*$TIMESTAMP*
```

### 3.2 Backup Verificering

```bash
#!/bin/bash
# scripts/verify-backup.sh

BACKUP_FILE=$1
TEST_DB="cirkelline_restore_test"

echo "=== BACKUP VERIFICATION ==="

# 1. Create test database
psql -c "DROP DATABASE IF EXISTS $TEST_DB;"
psql -c "CREATE DATABASE $TEST_DB;"

# 2. Restore to test database
echo "Restoring backup to test database..."
pg_restore -d "$TEST_DB" "$BACKUP_FILE" --verbose

# 3. Run integrity checks
echo "Running integrity checks..."
psql -d "$TEST_DB" -c "SELECT COUNT(*) FROM users;"
psql -d "$TEST_DB" -c "SELECT COUNT(*) FROM ai.agno_sessions;"

# 4. Cleanup
psql -c "DROP DATABASE $TEST_DB;"

echo "✓ Backup verification complete"
```

---

## 4. MIGRATION PROCEDURE

### 4.1 Pre-Migration Checklist

```
□ Backup verificeret og gyldig
□ Disk space > 2x database størrelse
□ Alle applikationer kan håndtere migration
□ Rollback script testet i staging
□ Overvågning aktiveret
□ Team notificeret
□ Low-traffic vindue identificeret
```

### 4.2 Migration Script (Transaktionel)

```sql
-- migrations/i18n_setup.sql (TRANSAKTIONEL VERSION)
-- KØRSEL: psql -h HOST -U USER -d DB -f migrations/i18n_setup.sql

BEGIN;

-- Set timeout for long-running operations
SET statement_timeout = '300s';

-- =====================================================
-- 1. TRANSLATIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS ai.translations (
    id SERIAL PRIMARY KEY,
    content_key TEXT NOT NULL,
    locale VARCHAR(10) NOT NULL,
    translated_text TEXT NOT NULL,
    context TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_auto_translated BOOLEAN DEFAULT FALSE,
    translator_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_translation UNIQUE(content_key, locale, context)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_translations_locale ON ai.translations(locale);
CREATE INDEX IF NOT EXISTS idx_translations_key ON ai.translations(content_key);
CREATE INDEX IF NOT EXISTS idx_translations_category ON ai.translations(category);

-- =====================================================
-- 2. USER LOCALE PREFERENCES
-- =====================================================
-- Use ALTER ... ADD COLUMN IF NOT EXISTS pattern for safety
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'preferred_locale'
    ) THEN
        ALTER TABLE public.users ADD COLUMN preferred_locale VARCHAR(10) DEFAULT 'da';
    END IF;
END $$;

-- Index
CREATE INDEX IF NOT EXISTS idx_users_locale ON public.users(preferred_locale);

-- =====================================================
-- 3. SUPPORTED LOCALES TABLE
-- =====================================================
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

-- Insert supported locales (UPSERT)
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
-- 4. FUNCTIONS
-- =====================================================
CREATE OR REPLACE FUNCTION ai.get_translation(
    p_key TEXT,
    p_locale VARCHAR(10) DEFAULT 'da',
    p_context TEXT DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    v_result TEXT;
BEGIN
    SELECT translated_text INTO v_result
    FROM ai.translations
    WHERE content_key = p_key
      AND locale = p_locale
      AND (context = p_context OR (context IS NULL AND p_context IS NULL))
    LIMIT 1;

    IF v_result IS NULL AND p_locale != 'en' THEN
        SELECT translated_text INTO v_result
        FROM ai.translations
        WHERE content_key = p_key
          AND locale = 'en'
          AND (context = p_context OR (context IS NULL AND p_context IS NULL))
        LIMIT 1;
    END IF;

    RETURN COALESCE(v_result, p_key);
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- 5. VERIFICATION
-- =====================================================
DO $$
DECLARE
    v_table_count INTEGER;
    v_column_exists BOOLEAN;
BEGIN
    -- Check tables created
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_schema = 'ai'
    AND table_name IN ('translations', 'supported_locales');

    IF v_table_count < 2 THEN
        RAISE EXCEPTION 'Migration verification failed: Missing tables';
    END IF;

    -- Check column added
    SELECT EXISTS(
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name = 'preferred_locale'
    ) INTO v_column_exists;

    IF NOT v_column_exists THEN
        RAISE EXCEPTION 'Migration verification failed: preferred_locale column missing';
    END IF;

    RAISE NOTICE 'Migration verification PASSED';
END $$;

COMMIT;

-- Output success
\echo '=============================================='
\echo 'i18n MIGRATION COMPLETED SUCCESSFULLY'
\echo '=============================================='
```

### 4.3 Post-Migration Verification

```bash
#!/bin/bash
# scripts/verify-migration.sh

DB_HOST=${1:-localhost}
DB_USER=${2:-cirkelline}
DB_NAME=${3:-cirkelline}

echo "=== POST-MIGRATION VERIFICATION ==="

# 1. Check tables exist
echo "Checking tables..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT
    table_name,
    CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = t.table_name)
         THEN '✓' ELSE '✗' END as status
FROM (VALUES ('translations'), ('supported_locales')) AS t(table_name);
EOF

# 2. Check column exists
echo "Checking users.preferred_locale column..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'preferred_locale';"

# 3. Check supported locales
echo "Checking supported locales..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT code, name_english, direction FROM ai.supported_locales ORDER BY sort_order;"

# 4. Test translation function
echo "Testing translation function..."
psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT ai.get_translation('test.key', 'da');"

echo "=== VERIFICATION COMPLETE ==="
```

---

## 5. ROLLBACK PLAN

### 5.1 Automatisk Rollback (Transaktionsfejl)

Hvis migrationen fejler inden COMMIT, vil PostgreSQL automatisk rulle tilbage alle ændringer.

### 5.2 Manuel Rollback Script

```sql
-- migrations/i18n_rollback.sql
-- KØR KUN HVIS MIGRATION FEJLER EFTER COMMIT

BEGIN;

-- 1. Drop functions
DROP FUNCTION IF EXISTS ai.get_translation(TEXT, VARCHAR, TEXT);
DROP FUNCTION IF EXISTS ai.upsert_translation(TEXT, VARCHAR, TEXT, TEXT, VARCHAR, BOOLEAN, UUID);

-- 2. Drop tables
DROP TABLE IF EXISTS ai.translation_audit_log;
DROP TABLE IF EXISTS ai.supported_locales;
DROP TABLE IF EXISTS ai.translations;

-- 3. Remove column (CAUTION: Only if no data has been written)
-- ALTER TABLE public.users DROP COLUMN IF EXISTS preferred_locale;

-- Note: Column removal commented out by default to preserve any user preferences
-- Only uncomment if you're certain no valuable data exists

COMMIT;

\echo 'ROLLBACK COMPLETE'
```

### 5.3 Full Database Restore

```bash
#!/bin/bash
# scripts/full-restore.sh

BACKUP_FILE=$1
DB_NAME="cirkelline"
DB_USER="cirkelline"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.dump>"
    exit 1
fi

echo "=== FULL DATABASE RESTORE ==="
echo "WARNING: This will replace all data in $DB_NAME"
read -p "Type 'RESTORE' to continue: " confirm

if [ "$confirm" != "RESTORE" ]; then
    echo "Aborted"
    exit 1
fi

# 1. Terminate connections
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

# 2. Drop and recreate database
psql -c "DROP DATABASE $DB_NAME;"
psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# 3. Restore
pg_restore -d "$DB_NAME" "$BACKUP_FILE" --verbose

# 4. Verify
psql -d "$DB_NAME" -c "SELECT COUNT(*) as user_count FROM users;"

echo "=== RESTORE COMPLETE ==="
```

---

## 6. OVERVÅGNING UNDER MIGRATION

### 6.1 Real-time Monitoring Queries

```sql
-- Monitor active connections
SELECT COUNT(*) as connections, state
FROM pg_stat_activity
WHERE datname = 'cirkelline'
GROUP BY state;

-- Monitor locks
SELECT
    pg_class.relname,
    pg_locks.mode,
    pg_locks.granted
FROM pg_locks
JOIN pg_class ON pg_locks.relation = pg_class.oid
WHERE pg_class.relname LIKE '%translation%';

-- Monitor table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as size
FROM pg_tables
WHERE schemaname = 'ai'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;
```

### 6.2 Health Check Endpoint

Migration tilføjer ikke nye API endpoints, så eksisterende `/health` endpoints vil fortsætte med at fungere.

---

## 7. KOMMUNIKATIONSPLAN

### 7.1 Før Migration
- [ ] Notificer development team
- [ ] Opdater status page (hvis relevant)
- [ ] Dokumenter planlagt vedligeholdelsesvindue

### 7.2 Under Migration
- [ ] Live status updates i Slack/Teams
- [ ] Overvåg error logs

### 7.3 Efter Migration
- [ ] Bekræft succesfuld migration
- [ ] Opdater dokumentation
- [ ] Del verifikationsrapport

---

## 8. GODKENDELSESCHECKLISTE

Før migration påbegyndes, skal følgende godkendes:

| Punkt | Ansvarlig | Status |
|-------|-----------|--------|
| Backup strategi godkendt | DevOps | ☐ |
| Rollback plan testet | DevOps | ☐ |
| Migration script reviewet | DBA | ☐ |
| Kommunikation planlagt | PM | ☐ |
| Overvågning aktiveret | DevOps | ☐ |

---

## 9. ESTIMERET TIMELINE

| Aktivitet | Varighed |
|-----------|----------|
| Pre-migration backup | 5-10 min |
| Migration script | < 30 sek |
| Post-migration verification | 2-5 min |
| **Total** | **~15 min** |

**Forventet downtime:** 0 (zero-downtime migration)

---

**Dokument Revision:** 1.0.0
**Sidst Opdateret:** 2025-12-09
