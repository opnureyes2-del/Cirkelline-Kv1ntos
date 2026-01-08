#!/bin/bash
# DAGLIG CHECK SCRIPT - Cirkelline System v1.3.5
# Kør: ./scripts/daily-check.sh

set -e

echo "================================================"
echo "  CIRKELLINE DAILY CHECK v1.3.5"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to project
cd ~/Desktop/projekts/projects/cirkelline-system

echo ""
echo "1. CHECKING DOCKER SERVICES..."
echo "--------------------------------"
DOCKER_COUNT=$(docker ps --format '{{.Names}}' | wc -l)
if [ "$DOCKER_COUNT" -ge 10 ]; then
    echo -e "${GREEN}✅ Docker: $DOCKER_COUNT containers running${NC}"
else
    echo -e "${YELLOW}⚠️ Docker: Only $DOCKER_COUNT containers (expected 10)${NC}"
fi

echo ""
echo "2. CHECKING BACKEND..."
echo "--------------------------------"
if curl -s http://localhost:7777/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend: Running on port 7777${NC}"
else
    echo -e "${RED}❌ Backend: Not responding${NC}"
    echo "   Start with: python my_os.py"
fi

echo ""
echo "3. CHECKING CKC VERSION..."
echo "--------------------------------"
source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null
CKC_VERSION=$(python -c "from cirkelline.ckc import __version__; print(__version__)" 2>/dev/null || echo "unknown")
echo "   CKC Version: $CKC_VERSION"
if [ "$CKC_VERSION" == "1.3.5" ]; then
    echo -e "${GREEN}✅ CKC: Version correct${NC}"
else
    echo -e "${YELLOW}⚠️ CKC: Expected v1.3.5, got $CKC_VERSION${NC}"
fi

echo ""
echo "4. CHECKING SYNC FOLDER..."
echo "--------------------------------"
SYNC_DIR=~/Desktop/projekts/projects/cirkelline-system/my_admin_workspace/SYNKRONISERING
if [ -d "$SYNC_DIR" ]; then
    SNAPSHOT_COUNT=$(ls -1 "$SYNC_DIR/snapshots/" 2>/dev/null | wc -l)
    echo -e "${GREEN}✅ Sync folder exists${NC}"
    echo "   Snapshots: $SNAPSHOT_COUNT"
else
    echo -e "${YELLOW}⚠️ Sync folder not found${NC}"
fi

echo ""
echo "5. RUNNING QUICK TESTS..."
echo "--------------------------------"
pytest tests/test_cirkelline.py -v --tb=no -q 2>/dev/null || echo -e "${YELLOW}⚠️ Tests need attention${NC}"

echo ""
echo "================================================"
echo "  CHECK COMPLETE"
echo "================================================"
