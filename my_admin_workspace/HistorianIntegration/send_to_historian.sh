#!/bin/bash
#
# CKC HISTORIAN INTEGRATION
# =========================
# Sender builds og deployments til Historikeren
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/home/rasmus/Desktop/projects/cirkelline-system"
BUILD_ARTIFACTS="$PROJECT_ROOT/ecosystems/build_artifacts"
DEPLOY_HISTORY="$PROJECT_ROOT/ecosystems/deploy_history"

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║     CKC HISTORIAN INTEGRATION                             ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

create_build_artifact() {
    print_header

    VERSION=$(date +"%Y%m%d_%H%M%S")
    ARTIFACT_NAME="ckc_build_$VERSION"
    ARTIFACT_PATH="$BUILD_ARTIFACTS/$ARTIFACT_NAME"

    echo "Creating build artifact: $ARTIFACT_NAME"
    mkdir -p "$ARTIFACT_PATH"

    # Kopier CKC core filer
    cp -r "$PROJECT_ROOT/cirkelline" "$ARTIFACT_PATH/"
    cp "$PROJECT_ROOT/my_os.py" "$ARTIFACT_PATH/"
    cp "$PROJECT_ROOT/requirements.txt" "$ARTIFACT_PATH/" 2>/dev/null || true

    # Gem metadata
    cat > "$ARTIFACT_PATH/BUILD_INFO.json" << EOF
{
    "version": "$VERSION",
    "created_at": "$(date -Iseconds)",
    "created_by": "Rasmus (Super Admin)",
    "git_commit": "$(cd $PROJECT_ROOT && git rev-parse HEAD 2>/dev/null || echo 'N/A')",
    "git_branch": "$(cd $PROJECT_ROOT && git branch --show-current 2>/dev/null || echo 'N/A')",
    "test_status": "pending"
}
EOF

    echo -e "${GREEN}✅ Build artifact created: $ARTIFACT_PATH${NC}"
    echo ""
    echo "Artifact indhold:"
    ls -la "$ARTIFACT_PATH"
}

record_deployment() {
    if [ -z "$1" ]; then
        echo -e "${RED}Fejl: Angiv build version${NC}"
        echo "Brug: ./send_to_historian.sh deploy <version>"
        exit 1
    fi

    print_header

    DEPLOY_TIME=$(date +"%Y%m%d_%H%M%S")
    DEPLOY_FILE="$DEPLOY_HISTORY/deploy_$DEPLOY_TIME.json"

    cat > "$DEPLOY_FILE" << EOF
{
    "deployment_id": "deploy_$DEPLOY_TIME",
    "build_version": "$1",
    "deployed_at": "$(date -Iseconds)",
    "deployed_by": "Rasmus (Super Admin)",
    "environment": "development",
    "status": "deployed",
    "notes": ""
}
EOF

    echo -e "${GREEN}✅ Deployment recorded: $DEPLOY_FILE${NC}"
}

list_builds() {
    print_header
    echo "Tilgængelige builds:"
    echo ""
    ls -la "$BUILD_ARTIFACTS" 2>/dev/null || echo "Ingen builds endnu"
}

list_deployments() {
    print_header
    echo "Deployment historik:"
    echo ""
    ls -la "$DEPLOY_HISTORY" 2>/dev/null || echo "Ingen deployments endnu"
}

show_help() {
    print_header
    echo "Brug: ./send_to_historian.sh [kommando] [args]"
    echo ""
    echo "Kommandoer:"
    echo "  build             - Opret ny build artifact"
    echo "  deploy <version>  - Registrer deployment"
    echo "  list-builds       - Vis alle builds"
    echo "  list-deploys      - Vis deployment historik"
    echo "  help              - Vis denne hjælp"
    echo ""
}

case "${1:-help}" in
    build)
        create_build_artifact
        ;;
    deploy)
        record_deployment "$2"
        ;;
    list-builds)
        list_builds
        ;;
    list-deploys)
        list_deployments
        ;;
    help|--help|-h|*)
        show_help
        ;;
esac
