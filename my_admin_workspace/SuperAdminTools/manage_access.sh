#!/bin/bash
#
# CKC SUPER ADMIN - Access Management
# ====================================
# Værktøjer til styring af brugeradgang
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="/home/rasmus/Desktop/projects/cirkelline-system"
DB_HOST="localhost"
DB_PORT="5533"
DB_NAME="ckc_brain"
DB_USER="ckc"
DB_PASS="ckc_secure_password_2025"

print_header() {
    echo -e "${YELLOW}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║     CKC SUPER ADMIN - ACCESS MANAGEMENT                   ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

list_users() {
    print_header
    echo "Aktive brugere i systemet:"
    echo ""
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
        "SELECT id, email, created_at, is_active FROM users ORDER BY created_at DESC LIMIT 20;"
}

grant_admin() {
    if [ -z "$1" ]; then
        echo -e "${RED}Fejl: Angiv email${NC}"
        echo "Brug: ./manage_access.sh grant-admin <email>"
        exit 1
    fi

    print_header
    echo "Giver admin rettigheder til: $1"
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
        "UPDATE users SET is_admin = true WHERE email = '$1';"
    echo -e "${GREEN}✅ Admin rettigheder givet!${NC}"
}

revoke_admin() {
    if [ -z "$1" ]; then
        echo -e "${RED}Fejl: Angiv email${NC}"
        exit 1
    fi

    print_header
    echo "Fjerner admin rettigheder fra: $1"
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
        "UPDATE users SET is_admin = false WHERE email = '$1';"
    echo -e "${GREEN}✅ Admin rettigheder fjernet!${NC}"
}

grant_ivo_access() {
    print_header
    echo "Konfigurerer Ivo's adgang..."

    # Ivo's email fra config
    IVO_EMAIL="opnureyes2@gmail.com"

    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
        "INSERT INTO users (email, is_admin, is_active)
         VALUES ('$IVO_EMAIL', true, true)
         ON CONFLICT (email) DO UPDATE SET is_admin = true, is_active = true;"

    echo -e "${GREEN}✅ Ivo's adgang konfigureret!${NC}"
}

show_help() {
    print_header
    echo "Brug: ./manage_access.sh [kommando] [args]"
    echo ""
    echo "Kommandoer:"
    echo "  list              - Vis alle brugere"
    echo "  grant-admin <email> - Giv admin rettigheder"
    echo "  revoke-admin <email> - Fjern admin rettigheder"
    echo "  grant-ivo         - Konfigurer Ivo's adgang"
    echo "  help              - Vis denne hjælp"
    echo ""
}

case "${1:-help}" in
    list)
        list_users
        ;;
    grant-admin)
        grant_admin "$2"
        ;;
    revoke-admin)
        revoke_admin "$2"
        ;;
    grant-ivo)
        grant_ivo_access
        ;;
    help|--help|-h|*)
        show_help
        ;;
esac
