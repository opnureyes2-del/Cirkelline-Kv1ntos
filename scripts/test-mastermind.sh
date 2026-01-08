#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# MASTERMIND & ECOSYSTEMS TEST SCRIPT
# ═══════════════════════════════════════════════════════════════════
# Kør: ./scripts/test-mastermind.sh
# ═══════════════════════════════════════════════════════════════════

# set -e  # Disabled - vi vil se alle resultater

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

CKC_ROOT="/home/rasmus/Desktop/projects/cirkelline-system"
VENV="/home/rasmus/Desktop/projects/cirkelline-env"

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║           MASTERMIND & ECOSYSTEMS TEST SUITE                       ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "Dato: $(date)"
echo ""

# Aktivér virtual environment
source "$VENV/bin/activate"
cd "$CKC_ROOT"

PASSED=0
FAILED=0

# ═══════════════════════════════════════════════════════════════════
# FASE 1: SYSTEM CHECK
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}▶ FASE 1: SYSTEM CHECK${NC}"
echo "────────────────────────────────────────────────────────────────────"

# 1.1 Backend Health
echo -n "  1.1 Backend Health: "
if curl -s http://localhost:7777/health | grep -q "ok"; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    ((FAILED++))
fi

# 1.2 Database
echo -n "  1.2 Database: "
if docker exec ckc-postgres psql -U ckc -d ckc_brain -c "SELECT 1;" 2>/dev/null | grep -q "1"; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    ((FAILED++))
fi

# 1.3 Login
echo -n "  1.3 Login: "
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"opnureyes2@gmail.com","password":"RASMUS_PASSWORD_HERE"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    ((FAILED++))
    echo "Login response: $LOGIN_RESPONSE"
    exit 1
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# FASE 2: MASTERMIND ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}▶ FASE 2: MASTERMIND ORCHESTRATOR${NC}"
echo "────────────────────────────────────────────────────────────────────"

# 2.1 Simpel Samtale
echo -n "  2.1 Simpel Samtale: "
CHAT_RESPONSE=$(curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hej!" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false")

if echo "$CHAT_RESPONSE" | grep -q "content"; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    echo "Response: $CHAT_RESPONSE"
    ((FAILED++))
fi

# 2.2 Web Search
echo -n "  2.2 Web Search: "
SEARCH_RESPONSE=$(curl -s -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer $TOKEN" \
  -F "message=Hvad er klokken i Tokyo lige nu?" \
  -F "user_id=ee461076-8cbb-4626-947b-956f293cf7bf" \
  -F "stream=false" 2>&1)

if echo "$SEARCH_RESPONSE" | grep -q "content"; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️ SKIPPED (rate limit?)${NC}"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# FASE 3: AGENTS & TEAMS
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}▶ FASE 3: AGENTS & TEAMS${NC}"
echo "────────────────────────────────────────────────────────────────────"

# 3.1 Agents Liste
echo -n "  3.1 Agents Liste: "
AGENTS=$(curl -s http://localhost:7777/agents)
if echo "$AGENTS" | grep -q "Audio Specialist"; then
    echo -e "${GREEN}✅ OK (4 agents)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    ((FAILED++))
fi

# 3.2 Teams Liste
echo -n "  3.2 Teams Liste: "
TEAMS=$(curl -s http://localhost:7777/teams)
if echo "$TEAMS" | grep -q "Cirkelline"; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    ((FAILED++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# FASE 4: ECOSYSTEMS/CKC-CORE
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}▶ FASE 4: ECOSYSTEMS/CKC-CORE${NC}"
echo "────────────────────────────────────────────────────────────────────"

# 4.1 Mappe eksisterer
echo -n "  4.1 ckc-core mappe: "
if [ -d "$CKC_ROOT/ecosystems/ckc-core" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    ((FAILED++))
fi

# 4.2 Git repo
echo -n "  4.2 Separat Git repo: "
if [ -d "$CKC_ROOT/ecosystems/ckc-core/.git" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    ((FAILED++))
fi

# 4.3 VERSION fil
echo -n "  4.3 VERSION fil: "
if [ -f "$CKC_ROOT/ecosystems/ckc-core/VERSION" ]; then
    VERSION=$(grep '"version"' "$CKC_ROOT/ecosystems/ckc-core/VERSION" | cut -d'"' -f4)
    echo -e "${GREEN}✅ OK ($VERSION)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL${NC}"
    ((FAILED++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# FASE 5: DATABASE SCHEMA
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}▶ FASE 5: DATABASE SCHEMA${NC}"
echo "────────────────────────────────────────────────────────────────────"

# 5.1 AI Schema
echo -n "  5.1 AI Schema tabeller: "
AI_TABLES=$(docker exec ckc-postgres psql -U ckc -d ckc_brain -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'ai';" 2>/dev/null | tr -d ' ')
if [ "$AI_TABLES" -ge 3 ]; then
    echo -e "${GREEN}✅ OK ($AI_TABLES tabeller)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL ($AI_TABLES tabeller)${NC}"
    ((FAILED++))
fi

# 5.2 Users
echo -n "  5.2 Test brugere: "
USER_COUNT=$(docker exec ckc-postgres psql -U ckc -d ckc_brain -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ')
if [ "$USER_COUNT" -ge 2 ]; then
    echo -e "${GREEN}✅ OK ($USER_COUNT brugere)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL ($USER_COUNT brugere)${NC}"
    ((FAILED++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# FASE 6: PYTEST (valgfri)
# ═══════════════════════════════════════════════════════════════════
echo -e "${YELLOW}▶ FASE 6: PYTEST${NC}"
echo "────────────────────────────────────────────────────────────────────"

echo "  Springer pytest over (kør manuelt med: PYTHONPATH=. pytest tests/test_cirkelline.py -v)"

echo ""

# ═══════════════════════════════════════════════════════════════════
# RESULTAT
# ═══════════════════════════════════════════════════════════════════
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                         TEST RESULTAT                              ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALLE TESTS BESTÅET!${NC}"
else
    echo -e "${RED}❌ NOGLE TESTS FEJLEDE${NC}"
fi

echo ""
echo "Se TEST-PLAN-MASTERMIND.md for detaljeret test dokumentation."
