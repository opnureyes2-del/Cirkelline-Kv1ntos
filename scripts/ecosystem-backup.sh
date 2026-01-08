#!/bin/bash
# ============================================================
# CIRKELLINE ECOSYSTEM BACKUP SCRIPT
# ============================================================
# Version: 1.0.0
# Date: 2025-12-17
# Purpose: Backup Cosmic-Library og lib-admin (kode kun)
# ============================================================

set -e

# ════════════════════════════════════════════════════════════
# KONFIGURATION
# ════════════════════════════════════════════════════════════

BACKUP_BASE="/home/rasmus/backups/ecosystem"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE}/${TIMESTAMP}"
PROJECTS_DIR="/home/rasmus/Desktop/projekts/projects"
RETENTION_DAYS=7

# Projekter at backup
PROJECTS=(
    "Cosmic-Library-main"
    "lib-admin-main"
)

# ════════════════════════════════════════════════════════════
# FARVER
# ════════════════════════════════════════════════════════════

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ════════════════════════════════════════════════════════════
# FUNKTIONER
# ════════════════════════════════════════════════════════════

print_header() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           CIRKELLINE ECOSYSTEM BACKUP                        ║"
    echo "║           ${TIMESTAMP}                                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${YELLOW}[STEP] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ════════════════════════════════════════════════════════════
# EXCLUDE PATTERNS (regenerérbare filer)
# ════════════════════════════════════════════════════════════

EXCLUDES=(
    # Python virtual environments
    --exclude 'venv/'
    --exclude '.venv/'
    --exclude '*-env/'
    --exclude 'env/'
    --exclude 'ENV/'

    # Node.js
    --exclude 'node_modules/'
    --exclude '.next/'
    --exclude 'dist/'
    --exclude 'build/'

    # Python cache
    --exclude '__pycache__/'
    --exclude '*.pyc'
    --exclude '*.pyo'
    --exclude '.pytest_cache/'

    # Coverage reports (regenerérbar)
    --exclude 'htmlcov/'
    --exclude 'coverage/'
    --exclude '.coverage'

    # Logs
    --exclude 'logs/'
    --exclude '*.log'

    # AI Models (regenerérbar, langsom)
    --exclude 'models/'
    --exclude 'models--*/'

    # Environment files (sikkerhed)
    --exclude '.env'
    --exclude '.env.local'
    --exclude '.env.production'
    --exclude '.env.*.local'

    # IDE
    --exclude '.vscode/'
    --exclude '.idea/'

    # OS
    --exclude '.DS_Store'
    --exclude 'Thumbs.db'

    # Temporary
    --exclude '*.tmp'
    --exclude '*.bak'
    --exclude 'tmp/'
    --exclude 'temp/'
)

# ════════════════════════════════════════════════════════════
# MAIN SCRIPT
# ════════════════════════════════════════════════════════════

main() {
    print_header

    # Verificer source directory eksisterer
    if [ ! -d "$PROJECTS_DIR" ]; then
        print_error "Projects directory not found: $PROJECTS_DIR"
        exit 1
    fi

    # Opret backup mappe
    print_step "Creating backup directory..."
    mkdir -p "${BACKUP_DIR}"
    print_success "Created: ${BACKUP_DIR}"

    # Backup hvert projekt
    local count=0
    local total=${#PROJECTS[@]}

    for project in "${PROJECTS[@]}"; do
        count=$((count + 1))
        print_step "[$count/$total] Backing up $project..."

        SOURCE="${PROJECTS_DIR}/${project}"
        DEST="${BACKUP_DIR}/${project}"

        if [ ! -d "$SOURCE" ]; then
            print_error "Project not found: $SOURCE"
            continue
        fi

        # Kør rsync
        rsync -a "${EXCLUDES[@]}" "$SOURCE/" "$DEST/"

        # Vis størrelse
        SIZE=$(du -sh "$DEST" | cut -f1)
        print_success "$project backed up ($SIZE)"
    done

    # Vis total backup størrelse
    echo -e "\n${CYAN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}BACKUP COMPLETE${NC}"
    echo -e "${CYAN}════════════════════════════════════════${NC}"
    echo ""
    print_info "Location: ${BACKUP_DIR}"
    echo ""
    echo "Backup sizes:"
    du -sh "${BACKUP_DIR}"/*
    echo ""
    TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
    print_info "Total size: ${TOTAL_SIZE}"

    # Cleanup gamle backups
    print_step "Cleaning old backups (>${RETENTION_DAYS} days)..."
    OLD_COUNT=$(find "${BACKUP_BASE}" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} 2>/dev/null | wc -l)
    find "${BACKUP_BASE}" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} \; 2>/dev/null || true
    print_success "Removed $OLD_COUNT old backups"

    # Vis aktive backups
    ACTIVE_COUNT=$(find "${BACKUP_BASE}" -maxdepth 1 -type d -name "2*" 2>/dev/null | wc -l)
    print_info "Active backups: ${ACTIVE_COUNT}"

    echo -e "\n${GREEN}Done!${NC}"
}

# ════════════════════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════════════════════

main "$@"
