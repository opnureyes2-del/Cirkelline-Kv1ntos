#!/bin/bash
# i18n Migration Backup Script
# Pre-migration backup with verification

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-/tmp/cirkelline-backups}"
DB_NAME="${DB_NAME:-cirkelline}"
DB_USER="${DB_USER:-cirkelline}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5532}"

echo "======================================================================"
echo "         i18n MIGRATION BACKUP - $(date)"
echo "======================================================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full database dump
echo "[1/4] Creating full database dump..."
PGPASSWORD=${PGPASSWORD:-cirkelline123} pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -Fc -f "$BACKUP_DIR/full_backup_$TIMESTAMP.dump" 2>&1

if [ $? -eq 0 ]; then
    echo "      ✓ Full backup created"
else
    echo "      ✗ BACKUP FAILED"
    exit 1
fi

# Schema-only backup
echo "[2/4] Creating schema backup..."
PGPASSWORD=${PGPASSWORD:-cirkelline123} pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --schema-only -f "$BACKUP_DIR/schema_$TIMESTAMP.sql" 2>&1
echo "      ✓ Schema backup created"

# Verify backup
echo "[3/4] Verifying backup..."
pg_restore --list "$BACKUP_DIR/full_backup_$TIMESTAMP.dump" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "      ✓ Backup verified"
else
    echo "      ✗ BACKUP VERIFICATION FAILED"
    exit 1
fi

# Checksum
echo "[4/4] Creating checksum..."
sha256sum "$BACKUP_DIR/full_backup_$TIMESTAMP.dump" > "$BACKUP_DIR/checksum_$TIMESTAMP.sha256"
echo "      ✓ Checksum created"

echo ""
echo "======================================================================"
echo "BACKUP COMPLETE"
echo "Location: $BACKUP_DIR"
echo "Files:"
ls -lh "$BACKUP_DIR"/*$TIMESTAMP* 2>/dev/null
echo "======================================================================"
