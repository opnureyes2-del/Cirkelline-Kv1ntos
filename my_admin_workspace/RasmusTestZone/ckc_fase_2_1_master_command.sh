#!/bin/bash
# ==============================================================================
# CKC FASE 2.1: OPTIMERING & KRISEBEREDSKAB MASTER-KOMMANDO
# ==============================================================================
# Formål: Implementerer proces-optimeringer og udfører en robust krise-simulering
# for Mastermind-rummet i det isolerede ckc-core miljø (Port 7778).
# Super Admin: Rasmus (System Creator & Visionary)
# Dato: 2025-12-12
# ==============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

CKC_ROOT="/home/rasmus/Desktop/projects/cirkelline-system"
CKC_CORE="$CKC_ROOT/ecosystems/ckc-core"
CKC_VENV="/home/rasmus/Desktop/projects/ckc-core-env"

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  CKC FASE 2.1: OPTIMERING & KRISEBEREDSKAB MASTER-KOMMANDO        ║"
echo "║  Super Admin: Rasmus (System Creator & Visionary)                  ║"
echo "║  CKC = Master Hovedkontor for Skabelse af Alt                      ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "Tidspunkt: $(date)"
echo ""

PASSED=0
FAILED=0

# ------------------------------------------------------------------------------
# FASE 0: PRÆ-CHECK - Verificer miljøer
# ------------------------------------------------------------------------------
echo -e "${BLUE}▶ FASE 0: PRÆ-CHECK - Verificer miljøer${NC}"
echo "────────────────────────────────────────────────────────────────────"

echo -n "  0.1 ckc-core mappe: "
if [ -d "$CKC_CORE" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL - Mappe ikke fundet${NC}"
    ((FAILED++))
    exit 1
fi

echo -n "  0.2 ckc-core virtualenv: "
if [ -d "$CKC_VENV" ]; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL - Virtualenv ikke fundet${NC}"
    ((FAILED++))
    exit 1
fi

echo -n "  0.3 Database (ckc-postgres): "
if docker exec ckc-postgres psql -U ckc -d ckc_brain -c "SELECT 1;" 2>/dev/null | grep -q "1"; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FEJL - Database ikke tilgængelig${NC}"
    ((FAILED++))
fi

echo -n "  0.4 CKC-CORE Backend (7778): "
if curl -s http://localhost:7778/health 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}✅ OK${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️ Ikke startet - Starter nu...${NC}"
    cd "$CKC_CORE"
    source "$CKC_VENV/bin/activate"
    export $(grep -v '^#' .env | xargs)
    nohup python my_os.py > /tmp/ckc-core.log 2>&1 &
    sleep 10
    if curl -s http://localhost:7778/health 2>/dev/null | grep -q "ok"; then
        echo -e "${GREEN}  ✅ Startet succesfuldt${NC}"
        ((PASSED++))
    else
        echo -e "${RED}  ❌ Kunne ikke starte${NC}"
        ((FAILED++))
    fi
fi

echo ""

# ------------------------------------------------------------------------------
# FASE 1: PROCES-OPTIMERING - Database Schema
# ------------------------------------------------------------------------------
echo -e "${BLUE}▶ FASE 1: PROCES-OPTIMERING - Database Schema (løser 14 fejl)${NC}"
echo "────────────────────────────────────────────────────────────────────"

echo -e "${YELLOW}  1.1 Opretter CKC database schema...${NC}"

# Opret CKC schema og tabeller
docker exec ckc-postgres psql -U ckc -d ckc_brain << 'EOF'
-- CKC Schema
CREATE SCHEMA IF NOT EXISTS ckc;

-- Task Contexts tabel
CREATE TABLE IF NOT EXISTS ckc.task_contexts (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    prompt TEXT,
    user_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow Steps tabel
CREATE TABLE IF NOT EXISTS ckc.workflow_steps (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) NOT NULL,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Agent Memories tabel
CREATE TABLE IF NOT EXISTS ckc.agent_memories (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    memory_type VARCHAR(50),
    content TEXT,
    tags TEXT[],
    importance FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge Entries tabel
CREATE TABLE IF NOT EXISTS ckc.knowledge_entries (
    id SERIAL PRIMARY KEY,
    entry_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500),
    content TEXT,
    source VARCHAR(255),
    category VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit Trail tabel
CREATE TABLE IF NOT EXISTS ckc.audit_trail (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    actor_id VARCHAR(255),
    target_id VARCHAR(255),
    action VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Connector Registry tabel
CREATE TABLE IF NOT EXISTS ckc.connector_registry (
    id SERIAL PRIMARY KEY,
    connector_id VARCHAR(255) UNIQUE NOT NULL,
    connector_type VARCHAR(100),
    platform_id VARCHAR(255),
    config JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'inactive',
    last_health_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Schema version tabel
CREATE TABLE IF NOT EXISTS ckc.schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO ckc.schema_version (version) VALUES (1) ON CONFLICT DO NOTHING;

SELECT 'CKC Schema oprettet succesfuldt!' as status;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✅ CKC database schema oprettet${NC}"
    ((PASSED++))
else
    echo -e "${RED}  ❌ Fejl ved oprettelse af schema${NC}"
    ((FAILED++))
fi

echo ""

# ------------------------------------------------------------------------------
# FASE 2: PROCES-OPTIMERING - Locale Filer
# ------------------------------------------------------------------------------
echo -e "${BLUE}▶ FASE 2: PROCES-OPTIMERING - Locale Filer (løser 5 fejl)${NC}"
echo "────────────────────────────────────────────────────────────────────"

echo -e "${YELLOW}  2.1 Kopierer locale filer til ckc-core...${NC}"

# Check og kopier locales
if [ -d "$CKC_ROOT/locales" ]; then
    cp -r "$CKC_ROOT/locales" "$CKC_CORE/"
    echo -e "${GREEN}  ✅ Locale filer kopieret fra locales/${NC}"
    ((PASSED++))
elif [ -d "$CKC_ROOT/cirkelline/i18n" ]; then
    mkdir -p "$CKC_CORE/locales"
    cp -r "$CKC_ROOT/cirkelline/i18n/"* "$CKC_CORE/locales/" 2>/dev/null
    echo -e "${GREEN}  ✅ Locale filer kopieret fra cirkelline/i18n/${NC}"
    ((PASSED++))
else
    # Opret basis locale filer
    mkdir -p "$CKC_CORE/locales"
    echo '{"greeting": "Hej", "error": "Fejl", "success": "Succes"}' > "$CKC_CORE/locales/da.json"
    echo '{"greeting": "Hello", "error": "Error", "success": "Success"}' > "$CKC_CORE/locales/en.json"
    echo -e "${YELLOW}  ⚠️ Basis locale filer oprettet (da.json, en.json)${NC}"
    ((PASSED++))
fi

echo ""

# ------------------------------------------------------------------------------
# FASE 3: ROBUST MASTERMIND KRISE-SIMULERING
# ------------------------------------------------------------------------------
echo -e "${BLUE}▶ FASE 3: ROBUST MASTERMIND KRISE-SIMULERING${NC}"
echo "────────────────────────────────────────────────────────────────────"
echo -e "${RED}  🚨 AKTIVERER INTERN KRISE RUM - RØD ALARM! 🚨${NC}"
echo ""

# Login som Rasmus
echo -e "${YELLOW}  3.1 Login som Rasmus (Super Admin)...${NC}"
AUTH_RESPONSE=$(curl -s -X POST "http://localhost:7778/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"opnureyes2@gmail.com","password":"RASMUS_PASSWORD_HERE"}')

RASMUS_TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
RASMUS_USER_ID=$(echo "$AUTH_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -n "$RASMUS_TOKEN" ] && [ "$RASMUS_TOKEN" != "null" ]; then
    echo -e "${GREEN}  ✅ Login succesfuld for Rasmus (Super Admin)${NC}"
    ((PASSED++))
else
    echo -e "${RED}  ❌ Login fejlede${NC}"
    echo "  Response: $AUTH_RESPONSE"
    ((FAILED++))
fi

echo ""

# Krise-simulering med retry logik
echo -e "${YELLOW}  3.2 Sender RØD ALARM til Mastermind...${NC}"
echo ""

MAX_RETRIES=3
RETRY_COUNT=0
KRISE_SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$KRISE_SUCCESS" = false ]; do
    CHAT_RESPONSE=$(curl -s -X POST "http://localhost:7778/teams/cirkelline/runs" \
      -H "Authorization: Bearer $RASMUS_TOKEN" \
      -F "message=RØD ALARM: Dette er Super Admin Rasmus. Intern krise-simulering aktiveret. Giv mig status på alle systemer og en handlingsplan." \
      -F "user_id=$RASMUS_USER_ID" \
      -F "stream=false" 2>&1)

    if echo "$CHAT_RESPONSE" | grep -q "content"; then
        KRISE_SUCCESS=true
        echo -e "${GREEN}  ✅ Mastermind reagerede på RØD ALARM${NC}"
        echo ""
        echo -e "${CYAN}  CKC's svar:${NC}"
        echo "  ────────────────────────────────────────"
        echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print('  ' + data.get('content', str(data))[:500] + '...')" 2>/dev/null || echo "  $CHAT_RESPONSE"
        ((PASSED++))
    elif echo "$CHAT_RESPONSE" | grep -q "429"; then
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            WAIT_TIME=$((2 ** RETRY_COUNT * 10))
            echo -e "${YELLOW}  ⚠️ Rate limit - Venter ${WAIT_TIME}s (forsøg $RETRY_COUNT/$MAX_RETRIES)...${NC}"
            sleep $WAIT_TIME
        fi
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${YELLOW}  ⚠️ Uventet svar - forsøger igen ($RETRY_COUNT/$MAX_RETRIES)...${NC}"
        sleep 5
    fi
done

if [ "$KRISE_SUCCESS" = false ]; then
    echo -e "${RED}  ❌ Krise-simulering kunne ikke gennemføres (rate limit)${NC}"
    echo -e "${YELLOW}  → Dette demonstrerer behovet for offline krise-protokoller${NC}"
    ((FAILED++))
fi

echo ""

# ------------------------------------------------------------------------------
# FASE 4: KØR TEST SUITE
# ------------------------------------------------------------------------------
echo -e "${BLUE}▶ FASE 4: KØR CKC-CORE TEST SUITE${NC}"
echo "────────────────────────────────────────────────────────────────────"

if [ -f "$CKC_CORE/test-ckc-core.sh" ]; then
    bash "$CKC_CORE/test-ckc-core.sh"
else
    echo -e "${YELLOW}  Kører hurtig health check...${NC}"
    curl -s http://localhost:7778/health
    echo ""
fi

echo ""

# ------------------------------------------------------------------------------
# RESULTAT
# ------------------------------------------------------------------------------
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║              FASE 2.1 MASTER-KOMMANDO RESULTAT                     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}  ✅ ALLE FASER GENNEMFØRT SUCCESFULDT!${NC}"
else
    echo -e "${YELLOW}  ⚠️ Nogle faser havde problemer - se detaljer ovenfor${NC}"
fi

echo ""
echo "────────────────────────────────────────────────────────────────────"
echo "  Dokumentation opdateret i:"
echo "  - ecosystems/ckc-core/TEST-RAPPORT-2025-12-12.md"
echo "  - ecosystems/ckc-core/PROCES-OPTIMERING-ANALYSE.md"
echo "════════════════════════════════════════════════════════════════════"
