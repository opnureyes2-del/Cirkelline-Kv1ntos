#!/bin/bash
# i18n Migration Execution Script
# Runs the migration with pre/post verification

set -euo pipefail

DB_NAME="${DB_NAME:-cirkelline}"
DB_USER="${DB_USER:-cirkelline}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5532}"
MIGRATION_FILE="${1:-migrations/i18n_setup.sql}"

echo "======================================================================"
echo "         i18n MIGRATION EXECUTION - $(date)"
echo "======================================================================"

# Pre-flight checks
echo "[1/5] Pre-flight checks..."
PGPASSWORD=${PGPASSWORD:-cirkelline123} psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "      ✓ Database connection OK"
else
    echo "      ✗ Cannot connect to database"
    exit 1
fi

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "      ✗ Migration file not found: $MIGRATION_FILE"
    exit 1
fi
echo "      ✓ Migration file found"

# Check current state
echo "[2/5] Checking current state..."
TRANSLATIONS_EXISTS=$(PGPASSWORD=${PGPASSWORD:-cirkelline123} psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='ai' AND table_name='translations');")
if [ "$TRANSLATIONS_EXISTS" = "t" ]; then
    echo "      ! ai.translations already exists - migration may have run before"
    read -p "      Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ]; then
        echo "      Aborted"
        exit 0
    fi
fi

# Run migration
echo "[3/5] Running migration..."
PGPASSWORD=${PGPASSWORD:-cirkelline123} psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE"
if [ $? -eq 0 ]; then
    echo "      ✓ Migration completed"
else
    echo "      ✗ MIGRATION FAILED - Check logs"
    exit 1
fi

# Post-migration verification
echo "[4/5] Post-migration verification..."
PGPASSWORD=${PGPASSWORD:-cirkelline123} psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT 'ai.translations' as table_name, COUNT(*) as row_count FROM ai.translations
UNION ALL
SELECT 'ai.supported_locales', COUNT(*) FROM ai.supported_locales;
EOF

# Test translation function
echo "[5/5] Testing translation function..."
PGPASSWORD=${PGPASSWORD:-cirkelline123} psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT ai.get_translation('test.key', 'da');"

echo ""
echo "======================================================================"
echo "MIGRATION COMPLETE"
echo "======================================================================"
