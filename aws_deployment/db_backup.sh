#!/bin/bash
# ============================================================================
# CIRKELLINE DATABASE BACKUP & RESTORE SCRIPT
# ============================================================================
# Beskrivelse: Håndterer RDS backups, snapshots og restore
# Version: 1.0.0
# Oprettet: 2025-12-13
# ============================================================================

set -e

# Konfiguration
AWS_REGION="${AWS_REGION:-eu-north-1}"
RDS_INSTANCE="cirkelline-system-db"
S3_BACKUP_BUCKET="cirkelline-backups-eu-north-1"
LOCAL_BACKUP_DIR="/home/rasmus/Desktop/projects/cirkelline-system/backups"
RETENTION_DAYS=30

# Database connection (hentes fra .env eller environment)
DB_HOST="${DB_HOST:-cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-cirkelline}"
DB_USER="${DB_USER:-postgres}"

# Farver
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   CIRKELLINE DATABASE BACKUP MANAGER      ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Funktion: Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Tjekker forudsætninger...${NC}"

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI ikke installeret${NC}"
        exit 1
    fi

    # Check pg_dump
    if ! command -v pg_dump &> /dev/null; then
        echo -e "${YELLOW}⚠️  pg_dump ikke fundet - installer postgresql-client${NC}"
        echo "   sudo apt install postgresql-client"
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity --region $AWS_REGION > /dev/null 2>&1; then
        echo -e "${RED}❌ AWS credentials ikke konfigureret${NC}"
        exit 1
    fi

    # Create local backup dir
    mkdir -p "$LOCAL_BACKUP_DIR"

    echo -e "${GREEN}✅ Forudsætninger OK${NC}"
    echo ""
}

# Funktion: Vis RDS status
show_rds_status() {
    echo -e "${YELLOW}📊 RDS Instance Status:${NC}"
    echo ""

    aws rds describe-db-instances \
        --db-instance-identifier $RDS_INSTANCE \
        --region $AWS_REGION \
        --query 'DBInstances[0].{Status:DBInstanceStatus,Engine:Engine,EngineVersion:EngineVersion,Class:DBInstanceClass,Storage:AllocatedStorage,MultiAZ:MultiAZ,BackupRetention:BackupRetentionPeriod,LatestRestorableTime:LatestRestorableTime}' \
        --output table 2>/dev/null || echo "RDS instance ikke fundet"

    echo ""
}

# Funktion: List eksisterende snapshots
list_snapshots() {
    echo -e "${YELLOW}📸 Eksisterende Snapshots:${NC}"
    echo ""

    aws rds describe-db-snapshots \
        --db-instance-identifier $RDS_INSTANCE \
        --region $AWS_REGION \
        --query 'DBSnapshots[*].{Snapshot:DBSnapshotIdentifier,Status:Status,Created:SnapshotCreateTime,Size:AllocatedStorage}' \
        --output table 2>/dev/null || echo "Ingen snapshots fundet"

    echo ""
}

# Funktion: Opret manuel snapshot
create_snapshot() {
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    SNAPSHOT_ID="cirkelline-manual-${TIMESTAMP}"

    echo -e "${YELLOW}📸 Opretter snapshot: $SNAPSHOT_ID${NC}"

    aws rds create-db-snapshot \
        --db-instance-identifier $RDS_INSTANCE \
        --db-snapshot-identifier $SNAPSHOT_ID \
        --region $AWS_REGION \
        --tags Key=Environment,Value=production Key=CreatedBy,Value=backup-script

    echo -e "${GREEN}✅ Snapshot oprettet: $SNAPSHOT_ID${NC}"
    echo "   Status: aws rds describe-db-snapshots --db-snapshot-identifier $SNAPSHOT_ID"
}

# Funktion: Lokal pg_dump backup
local_backup() {
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    BACKUP_FILE="$LOCAL_BACKUP_DIR/cirkelline-backup-${TIMESTAMP}.sql.gz"

    echo -e "${YELLOW}💾 Opretter lokal backup...${NC}"

    # Hent password fra Secrets Manager
    DB_PASSWORD=$(aws secretsmanager get-secret-value \
        --secret-id cirkelline-system/database-url \
        --region $AWS_REGION \
        --query 'SecretString' \
        --output text | grep -oP '(?<=:)[^@]+(?=@)')

    if [ -z "$DB_PASSWORD" ]; then
        echo -e "${RED}❌ Kunne ikke hente database password${NC}"
        return 1
    fi

    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h $DB_HOST \
        -p $DB_PORT \
        -U $DB_USER \
        -d $DB_NAME \
        --format=plain \
        --no-owner \
        --no-acl \
        2>/dev/null | gzip > "$BACKUP_FILE"

    SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo -e "${GREEN}✅ Backup oprettet: $BACKUP_FILE ($SIZE)${NC}"
}

# Funktion: Upload til S3
upload_to_s3() {
    echo -e "${YELLOW}☁️  Uploader backups til S3...${NC}"

    # Check if bucket exists, create if not
    if ! aws s3 ls "s3://$S3_BACKUP_BUCKET" --region $AWS_REGION 2>/dev/null; then
        echo "Opretter S3 bucket: $S3_BACKUP_BUCKET"
        aws s3 mb "s3://$S3_BACKUP_BUCKET" --region $AWS_REGION

        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket $S3_BACKUP_BUCKET \
            --versioning-configuration Status=Enabled \
            --region $AWS_REGION

        # Set lifecycle policy
        aws s3api put-bucket-lifecycle-configuration \
            --bucket $S3_BACKUP_BUCKET \
            --lifecycle-configuration '{
                "Rules": [{
                    "ID": "DeleteOldBackups",
                    "Status": "Enabled",
                    "Filter": {"Prefix": ""},
                    "Expiration": {"Days": 90},
                    "NoncurrentVersionExpiration": {"NoncurrentDays": 30}
                }]
            }' \
            --region $AWS_REGION
    fi

    # Upload backups
    aws s3 sync "$LOCAL_BACKUP_DIR" "s3://$S3_BACKUP_BUCKET/database/" \
        --region $AWS_REGION \
        --storage-class STANDARD_IA

    echo -e "${GREEN}✅ Backups uploadet til S3${NC}"
}

# Funktion: Cleanup gamle lokale backups
cleanup_local() {
    echo -e "${YELLOW}🧹 Rydder gamle lokale backups (> $RETENTION_DAYS dage)...${NC}"

    find "$LOCAL_BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

    REMAINING=$(ls -1 "$LOCAL_BACKUP_DIR"/*.sql.gz 2>/dev/null | wc -l || echo "0")
    echo -e "${GREEN}✅ $REMAINING backups bevaret lokalt${NC}"
}

# Funktion: Verificer RDS automated backups
verify_automated_backups() {
    echo -e "${YELLOW}🔄 Verificerer RDS Automated Backups...${NC}"
    echo ""

    BACKUP_RETENTION=$(aws rds describe-db-instances \
        --db-instance-identifier $RDS_INSTANCE \
        --region $AWS_REGION \
        --query 'DBInstances[0].BackupRetentionPeriod' \
        --output text 2>/dev/null || echo "0")

    BACKUP_WINDOW=$(aws rds describe-db-instances \
        --db-instance-identifier $RDS_INSTANCE \
        --region $AWS_REGION \
        --query 'DBInstances[0].PreferredBackupWindow' \
        --output text 2>/dev/null || echo "N/A")

    LATEST_RESTORABLE=$(aws rds describe-db-instances \
        --db-instance-identifier $RDS_INSTANCE \
        --region $AWS_REGION \
        --query 'DBInstances[0].LatestRestorableTime' \
        --output text 2>/dev/null || echo "N/A")

    echo "  Backup Retention: $BACKUP_RETENTION dage"
    echo "  Backup Window: $BACKUP_WINDOW UTC"
    echo "  Latest Restorable: $LATEST_RESTORABLE"

    if [ "$BACKUP_RETENTION" -lt 7 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Anbefaling: Øg backup retention til mindst 7 dage${NC}"
        echo "   aws rds modify-db-instance --db-instance-identifier $RDS_INSTANCE --backup-retention-period 7"
    else
        echo ""
        echo -e "${GREEN}✅ Automated backups konfigureret korrekt${NC}"
    fi
    echo ""
}

# Funktion: Komplet backup rutine
full_backup() {
    echo -e "${BLUE}=== FULD BACKUP RUTINE ===${NC}"
    echo ""

    # 1. Create RDS snapshot
    create_snapshot

    # 2. Wait for snapshot
    echo "Venter på snapshot completion..."
    sleep 10

    # 3. Local pg_dump backup
    local_backup

    # 4. Upload to S3
    upload_to_s3

    # 5. Cleanup
    cleanup_local

    echo ""
    echo -e "${GREEN}✅ Fuld backup komplet!${NC}"
}

# Hovedmenu
show_menu() {
    echo -e "${BLUE}Vælg handling:${NC}"
    echo ""
    echo "  1) Vis RDS status"
    echo "  2) List snapshots"
    echo "  3) Verificer automated backups"
    echo "  4) Opret manuel snapshot"
    echo "  5) Opret lokal pg_dump backup"
    echo "  6) Upload backups til S3"
    echo "  7) Cleanup gamle lokale backups"
    echo "  8) FULD BACKUP (snapshot + local + S3)"
    echo "  0) Afslut"
    echo ""
    read -p "Valg: " choice

    case $choice in
        1) show_rds_status ;;
        2) list_snapshots ;;
        3) verify_automated_backups ;;
        4) create_snapshot ;;
        5) local_backup ;;
        6) upload_to_s3 ;;
        7) cleanup_local ;;
        8) full_backup ;;
        0) exit 0 ;;
        *) echo -e "${RED}Ugyldigt valg${NC}" ;;
    esac
}

# Main
check_prerequisites

if [ "$1" = "--status" ]; then
    show_rds_status
    verify_automated_backups
    exit 0
elif [ "$1" = "--snapshot" ]; then
    create_snapshot
    exit 0
elif [ "$1" = "--local" ]; then
    local_backup
    exit 0
elif [ "$1" = "--full" ]; then
    full_backup
    exit 0
else
    while true; do
        show_menu
        echo ""
    done
fi
