#!/bin/bash
#
# CIRKELLINE UNIFIED DATABASE MIGRATION SCRIPT v2.0.0
# ====================================================
# Handles migrations for both cirkelline-system and lib-admin
#
# Usage:
#   ./scripts/migrate.sh                    # Show status
#   ./scripts/migrate.sh status             # Show status for all projects
#   ./scripts/migrate.sh upgrade            # Upgrade all to head
#   ./scripts/migrate.sh downgrade          # Rollback one revision (with confirmation)
#   ./scripts/migrate.sh history            # Show migration history
#   ./scripts/migrate.sh create NAME        # Create new migration (interactive)
#   ./scripts/migrate.sh stamp [REV]        # Stamp at revision
#   ./scripts/migrate.sh --cirkelline CMD   # Run only for cirkelline-system
#   ./scripts/migrate.sh --lib-admin CMD    # Run only for lib-admin
#
# Author: Claude Code
# Updated: 2025-12-13 (FASE 1.5 Migration Strategy)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
PROJECTS_ROOT="/home/rasmus/Desktop/projects"
CIRKELLINE_DIR="$PROJECTS_ROOT/cirkelline-system"
CIRKELLINE_ENV="$PROJECTS_ROOT/cirkelline-env"
LIB_ADMIN_DIR="$PROJECTS_ROOT/lib-admin-main/backend"
LIB_ADMIN_ENV="$LIB_ADMIN_DIR/venv"

# Banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║       CIRKELLINE DATABASE MIGRATION TOOL v2.0.0                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check database
check_database() {
    if ! docker ps 2>/dev/null | grep -q cirkelline-postgres; then
        echo -e "${RED}ERROR: Database is not running!${NC}"
        echo "Start it with: docker start cirkelline-postgres"
        exit 1
    fi
}

# Run migration command for cirkelline-system
run_cirkelline() {
    local cmd=$1
    local arg=$2

    echo -e "\n${BLUE}━━━ CIRKELLINE-SYSTEM ━━━${NC}"

    if [ ! -f "$CIRKELLINE_DIR/alembic.ini" ]; then
        echo -e "${YELLOW}⚠ No alembic.ini found${NC}"
        return
    fi

    cd "$CIRKELLINE_DIR"
    source "$CIRKELLINE_ENV/bin/activate"

    case $cmd in
        current|status)
            alembic current 2>&1 | grep -v "^INFO" || true
            ;;
        upgrade)
            alembic upgrade head
            echo -e "${GREEN}✓ Upgraded to head${NC}"
            ;;
        downgrade)
            alembic downgrade -1
            echo -e "${GREEN}✓ Downgraded -1${NC}"
            ;;
        history)
            alembic history --verbose 2>&1 | head -30
            ;;
        create)
            alembic revision --autogenerate -m "$arg"
            echo -e "${GREEN}✓ Created migration: $arg${NC}"
            ;;
        stamp)
            alembic stamp ${arg:-head}
            echo -e "${GREEN}✓ Stamped at ${arg:-head}${NC}"
            ;;
    esac

    deactivate 2>/dev/null || true
}

# Run migration command for lib-admin
run_lib_admin() {
    local cmd=$1
    local arg=$2

    echo -e "\n${BLUE}━━━ LIB-ADMIN ━━━${NC}"

    if [ ! -f "$LIB_ADMIN_DIR/alembic.ini" ]; then
        echo -e "${YELLOW}⚠ No alembic.ini found${NC}"
        return
    fi

    cd "$LIB_ADMIN_DIR"
    source "$LIB_ADMIN_ENV/bin/activate"

    case $cmd in
        current|status)
            alembic current 2>&1 | grep -v "^INFO" || true
            ;;
        upgrade)
            alembic upgrade head
            echo -e "${GREEN}✓ Upgraded to head${NC}"
            ;;
        downgrade)
            alembic downgrade -1
            echo -e "${GREEN}✓ Downgraded -1${NC}"
            ;;
        history)
            alembic history --verbose 2>&1 | head -30
            ;;
        create)
            alembic revision --autogenerate -m "$arg"
            echo -e "${GREEN}✓ Created migration: $arg${NC}"
            ;;
        stamp)
            alembic stamp ${arg:-head}
            echo -e "${GREEN}✓ Stamped at ${arg:-head}${NC}"
            ;;
    esac

    deactivate 2>/dev/null || true
}

# Main
show_banner
check_database

# Parse arguments
PROJECT="all"
COMMAND="status"
ARG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --cirkelline)
            PROJECT="cirkelline"
            shift
            ;;
        --lib-admin)
            PROJECT="lib-admin"
            shift
            ;;
        status|current|upgrade|downgrade|history|create|stamp)
            COMMAND=$1
            shift
            ARG=$1
            shift || true
            ;;
        *)
            ARG=$1
            shift
            ;;
    esac
done

# Handle downgrade confirmation
if [ "$COMMAND" = "downgrade" ]; then
    echo -e "${YELLOW}⚠ WARNING: This will rollback database changes!${NC}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Handle create interactively
if [ "$COMMAND" = "create" ] && [ -z "$ARG" ]; then
    echo -e "${RED}ERROR: Migration name required${NC}"
    echo "Usage: ./scripts/migrate.sh create 'add_new_feature'"
    exit 1
fi

if [ "$COMMAND" = "create" ] && [ "$PROJECT" = "all" ]; then
    echo "Which project?"
    echo "  1) cirkelline-system"
    echo "  2) lib-admin"
    read -p "Choose (1/2): " choice
    case $choice in
        1) PROJECT="cirkelline" ;;
        2) PROJECT="lib-admin" ;;
        *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
    esac
fi

# Execute
case $PROJECT in
    all)
        run_cirkelline "$COMMAND" "$ARG"
        run_lib_admin "$COMMAND" "$ARG"
        ;;
    cirkelline)
        run_cirkelline "$COMMAND" "$ARG"
        ;;
    lib-admin)
        run_lib_admin "$COMMAND" "$ARG"
        ;;
esac

echo -e "\n${GREEN}✅ Done!${NC}"
