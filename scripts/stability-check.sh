#!/bin/bash
# =============================================================================
# CIRKELLINE STABILITY CHECK
# =============================================================================
# Verificerer at alle systemer er stabile før kritiske ændringer
# Brugt som gate for CLAUDE.md password removal
# =============================================================================

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         CIRKELLINE STABILITY VERIFICATION                       ║"
echo "║         'Kompromisløs komplethed og fejlfri præcision'          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

FAILED=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    local port=$3

    printf "%-30s" "$name (port $port):"

    # First check if port is listening
    if ! nc -z localhost $port 2>/dev/null; then
        echo -e " ${RED}❌ NOT RUNNING${NC}"
        FAILED=$((FAILED+1))
        return 1
    fi

    # Then check health endpoint
    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)

    if [ "$response" = "200" ]; then
        local time=$(curl -s -o /dev/null -w "%{time_total}" "$url" 2>/dev/null)
        echo -e " ${GREEN}✅ OK${NC} (${time}s)"
        return 0
    else
        echo -e " ${RED}❌ FAIL (HTTP $response)${NC}"
        FAILED=$((FAILED+1))
        return 1
    fi
}

check_database() {
    local name=$1
    local cmd=$2

    printf "%-30s" "$name:"

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e " ${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e " ${RED}❌ FAIL${NC}"
        FAILED=$((FAILED+1))
        return 1
    fi
}

# =============================================================================
# SERVICE HEALTH CHECKS
# =============================================================================
echo "┌──────────────────────────────────────────────────────────────────┐"
echo "│ SERVICE HEALTH CHECKS                                           │"
echo "└──────────────────────────────────────────────────────────────────┘"

check_service "lib-admin (CKC)" "http://localhost:8001/health" 8001
check_service "Cosmic Library" "http://localhost:7778/health" 7778
check_service "Cirkelline Main" "http://localhost:7777/health" 7777
check_service "CKC Gateway" "http://localhost:7779/health" 7779

echo ""

# =============================================================================
# DATABASE CHECKS
# =============================================================================
echo "┌──────────────────────────────────────────────────────────────────┐"
echo "│ DATABASE CHECKS                                                 │"
echo "└──────────────────────────────────────────────────────────────────┘"

check_database "PostgreSQL (Docker)" "docker exec cirkelline-postgres pg_isready -U cirkelline"
check_database "Redis (Docker)" "docker exec cirkelline-redis redis-cli ping | grep -q PONG"

echo ""

# =============================================================================
# TEST SUITE VERIFICATION
# =============================================================================
echo "┌──────────────────────────────────────────────────────────────────┐"
echo "│ TEST SUITE VERIFICATION                                         │"
echo "└──────────────────────────────────────────────────────────────────┘"

printf "%-30s" "lib-admin pytest:"
cd /home/rasmus/Desktop/projects/lib-admin-main/backend
if source venv/bin/activate && PYTHONPATH=. pytest tests/ --tb=no -q 2>&1 | tail -1 | grep -q "passed"; then
    PASSED=$(source venv/bin/activate && PYTHONPATH=. pytest tests/ --tb=no -q 2>&1 | tail -1 | grep -oP '\d+(?= passed)')
    echo -e " ${GREEN}✅ $PASSED tests passed${NC}"
else
    echo -e " ${RED}❌ TESTS FAILING${NC}"
    FAILED=$((FAILED+1))
fi

echo ""

# =============================================================================
# PROCESS CHECKS
# =============================================================================
echo "┌──────────────────────────────────────────────────────────────────┐"
echo "│ PROCESS CHECKS                                                  │"
echo "└──────────────────────────────────────────────────────────────────┘"

printf "%-30s" "Python processes:"
PYTHON_COUNT=$(pgrep -c python 2>/dev/null || echo "0")
if [ "$PYTHON_COUNT" -gt 0 ]; then
    echo -e " ${GREEN}✅ $PYTHON_COUNT running${NC}"
else
    echo -e " ${YELLOW}⚠️  None running${NC}"
    WARNINGS=$((WARNINGS+1))
fi

printf "%-30s" "Docker containers:"
DOCKER_COUNT=$(docker ps -q 2>/dev/null | wc -l)
if [ "$DOCKER_COUNT" -gt 0 ]; then
    echo -e " ${GREEN}✅ $DOCKER_COUNT running${NC}"
else
    echo -e " ${RED}❌ None running${NC}"
    FAILED=$((FAILED+1))
fi

echo ""

# =============================================================================
# MEMORY & CPU CHECK
# =============================================================================
echo "┌──────────────────────────────────────────────────────────────────┐"
echo "│ RESOURCE CHECKS                                                 │"
echo "└──────────────────────────────────────────────────────────────────┘"

printf "%-30s" "Memory usage:"
MEM_USED=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')
if (( $(echo "$MEM_USED < 90" | bc -l) )); then
    echo -e " ${GREEN}✅ ${MEM_USED}% used${NC}"
else
    echo -e " ${YELLOW}⚠️  ${MEM_USED}% used (high)${NC}"
    WARNINGS=$((WARNINGS+1))
fi

printf "%-30s" "CPU load (1min avg):"
LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
CORES=$(nproc)
LOAD_PCT=$(echo "scale=1; $LOAD / $CORES * 100" | bc)
if (( $(echo "$LOAD_PCT < 80" | bc -l) )); then
    echo -e " ${GREEN}✅ ${LOAD_PCT}% (${LOAD}/${CORES} cores)${NC}"
else
    echo -e " ${YELLOW}⚠️  ${LOAD_PCT}% (high)${NC}"
    WARNINGS=$((WARNINGS+1))
fi

echo ""

# =============================================================================
# RESULTS SUMMARY
# =============================================================================
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                      RESULTS SUMMARY                            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✅ ALL CHECKS PASSED - SYSTEM IS STABLE                        ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "System is ready for:"
        echo "  - Production deployment"
        echo "  - CLAUDE.md password removal (after 48h stability)"
        echo "  - Critical configuration changes"
        exit 0
    else
        echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║  ⚠️  ALL CRITICAL CHECKS PASSED - $WARNINGS WARNING(S)                  ║${NC}"
        echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "System is mostly stable but has warnings."
        echo "Review warnings before proceeding with critical changes."
        exit 0
    fi
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ $FAILED CHECK(S) FAILED - SYSTEM NOT STABLE                      ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "DO NOT proceed with:"
    echo "  - Production deployment"
    echo "  - CLAUDE.md password removal"
    echo "  - Critical configuration changes"
    echo ""
    echo "Fix failing checks first!"
    exit 1
fi
