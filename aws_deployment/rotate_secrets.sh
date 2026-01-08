#!/bin/bash
# ============================================================================
# CIRKELLINE SECRETS ROTATION SCRIPT
# ============================================================================
# Beskrivelse: Roterer secrets i AWS Secrets Manager
# Version: 1.0.0
# Oprettet: 2025-12-13
# ============================================================================

set -e

# Konfiguration
AWS_REGION="${AWS_REGION:-eu-north-1}"
AWS_ACCOUNT_ID="710504360116"
ROTATION_DAYS=90

# Farver til output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   CIRKELLINE SECRETS ROTATION MANAGER     ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Funktion: Check AWS credentials
check_aws_credentials() {
    echo -e "${YELLOW}🔐 Tjekker AWS credentials...${NC}"
    if ! aws sts get-caller-identity --region $AWS_REGION > /dev/null 2>&1; then
        echo -e "${RED}❌ AWS credentials ikke konfigureret korrekt${NC}"
        echo "   Kør: aws configure"
        exit 1
    fi
    echo -e "${GREEN}✅ AWS credentials OK${NC}"
    echo ""
}

# Funktion: List alle secrets
list_secrets() {
    echo -e "${YELLOW}📋 Aktive Secrets i Secrets Manager:${NC}"
    echo ""

    aws secretsmanager list-secrets \
        --region $AWS_REGION \
        --query 'SecretList[?starts_with(Name, `cirkelline`)].{Name:Name,LastRotated:LastRotatedDate,LastChanged:LastChangedDate}' \
        --output table

    echo ""
}

# Funktion: Generer ny JWT secret
rotate_jwt_secret() {
    echo -e "${YELLOW}🔄 Roterer JWT Secret Key...${NC}"

    NEW_JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')

    aws secretsmanager update-secret \
        --secret-id cirkelline-system/jwt-secret-key \
        --secret-string "$NEW_JWT_SECRET" \
        --region $AWS_REGION

    echo -e "${GREEN}✅ JWT Secret Key roteret${NC}"
    echo -e "${YELLOW}⚠️  VIGTIGT: Genstart ECS service for at anvende ny secret${NC}"
}

# Funktion: Generer nye encryption keys
rotate_encryption_keys() {
    echo -e "${YELLOW}🔄 Roterer Token Encryption Keys...${NC}"

    # Google Token Encryption Key
    NEW_GOOGLE_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    aws secretsmanager update-secret \
        --secret-id cirkelline/GOOGLE_TOKEN_ENCRYPTION_KEY \
        --secret-string "$NEW_GOOGLE_KEY" \
        --region $AWS_REGION 2>/dev/null || echo "Skipping Google key"

    # Notion Token Encryption Key
    NEW_NOTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    aws secretsmanager update-secret \
        --secret-id cirkelline/NOTION_TOKEN_ENCRYPTION_KEY \
        --secret-string "$NEW_NOTION_KEY" \
        --region $AWS_REGION 2>/dev/null || echo "Skipping Notion key"

    echo -e "${GREEN}✅ Encryption Keys roteret${NC}"
    echo -e "${RED}⚠️  VIGTIGT: Eksisterende OAuth tokens bliver ugyldige!${NC}"
}

# Funktion: Verificer secret health
check_secret_health() {
    echo -e "${YELLOW}🏥 Tjekker Secret Health...${NC}"
    echo ""

    SECRETS=(
        "cirkelline-system/database-url"
        "cirkelline-system/google-api-key"
        "cirkelline-system/jwt-secret-key"
        "cirkelline-system/exa-api-key"
        "cirkelline-system/tavily-api-key"
    )

    for secret in "${SECRETS[@]}"; do
        LAST_CHANGED=$(aws secretsmanager describe-secret \
            --secret-id "$secret" \
            --region $AWS_REGION \
            --query 'LastChangedDate' \
            --output text 2>/dev/null || echo "N/A")

        if [ "$LAST_CHANGED" != "N/A" ]; then
            DAYS_OLD=$(( ($(date +%s) - $(date -d "$LAST_CHANGED" +%s)) / 86400 ))

            if [ $DAYS_OLD -gt $ROTATION_DAYS ]; then
                echo -e "${RED}⚠️  $secret: $DAYS_OLD dage gammel (> $ROTATION_DAYS)${NC}"
            else
                echo -e "${GREEN}✅ $secret: $DAYS_OLD dage gammel${NC}"
            fi
        else
            echo -e "${YELLOW}❓ $secret: Kunne ikke hente info${NC}"
        fi
    done
    echo ""
}

# Funktion: Force deploy til ECS
force_ecs_deploy() {
    echo -e "${YELLOW}🚀 Tvinger ECS service genstart...${NC}"

    aws ecs update-service \
        --cluster cirkelline-system-cluster \
        --service cirkelline-system-backend-service \
        --force-new-deployment \
        --region $AWS_REGION > /dev/null

    echo -e "${GREEN}✅ ECS deployment startet${NC}"
    echo "   Følg status: aws ecs describe-services --cluster cirkelline-system-cluster --services cirkelline-system-backend-service --query 'services[0].deployments'"
}

# Hovedmenu
show_menu() {
    echo -e "${BLUE}Vælg handling:${NC}"
    echo ""
    echo "  1) List alle secrets"
    echo "  2) Tjek secret health"
    echo "  3) Roter JWT Secret Key"
    echo "  4) Roter Encryption Keys (VIGTIGT: Invaliderer OAuth tokens!)"
    echo "  5) Force ECS redeploy (anvend nye secrets)"
    echo "  6) Fuld rotation (JWT + Encryption + Redeploy)"
    echo "  0) Afslut"
    echo ""
    read -p "Valg: " choice

    case $choice in
        1) list_secrets ;;
        2) check_secret_health ;;
        3) rotate_jwt_secret ;;
        4)
            echo -e "${RED}⚠️  ADVARSEL: Dette invaliderer alle eksisterende OAuth tokens!${NC}"
            read -p "Er du sikker? (ja/nej): " confirm
            if [ "$confirm" = "ja" ]; then
                rotate_encryption_keys
            fi
            ;;
        5) force_ecs_deploy ;;
        6)
            echo -e "${RED}⚠️  FULD ROTATION: JWT + Encryption Keys + ECS Redeploy${NC}"
            read -p "Er du sikker? (ja/nej): " confirm
            if [ "$confirm" = "ja" ]; then
                rotate_jwt_secret
                rotate_encryption_keys
                force_ecs_deploy
            fi
            ;;
        0) exit 0 ;;
        *) echo -e "${RED}Ugyldigt valg${NC}" ;;
    esac
}

# Main
check_aws_credentials

if [ "$1" = "--health" ]; then
    check_secret_health
    exit 0
elif [ "$1" = "--list" ]; then
    list_secrets
    exit 0
elif [ "$1" = "--force-deploy" ]; then
    force_ecs_deploy
    exit 0
else
    while true; do
        show_menu
        echo ""
    done
fi
