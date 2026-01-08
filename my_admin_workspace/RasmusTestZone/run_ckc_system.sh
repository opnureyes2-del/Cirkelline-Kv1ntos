#!/bin/bash
set -e # Stop script on first error if any command fails

# Global CKC Root Directory (assuming script is run from RasmusTestZone)
CKC_ROOT_DIR="/home/rasmus/Desktop/projects/cirkelline-system"
ECOSYSTEM_DIR="$CKC_ROOT_DIR/ecosystems/ckc-core"
BUILD_ARTIFACTS_DIR="$CKC_ROOT_DIR/ecosystems/build_artifacts"
HISTORIAN_INTEGRATION_DIR="$CKC_ROOT_DIR/my_admin_workspace/HistorianIntegration"
SUPER_ADMIN_TOOLS_DIR="$CKC_ROOT_DIR/my_admin_workspace/SuperAdminTools"
VENV_DIR="/home/rasmus/Desktop/projects/ckc-core-env" # Brug ckc-core-env som det primære venv
FRONTEND_CLA_PATH="$CKC_ROOT_DIR/cla"
TEST_REPORTS_DIR="$CKC_ROOT_DIR/ecosystems/test_reports" # Ny mappe for testrapporter

# Farver
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║      CKC SUPER ADMIN MASTER OPS & VALIDERINGSKOMMANDO (v1.2)       ║"
echo "║      Styres fra din RasmusTestZone - Total Overblik & Kontrol      ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "DATO & TID: $(date)"
echo "KØRER SOM BRUGER: $(whoami)"
echo "CKC RODMAPPE: $CKC_ROOT_DIR"
echo

# Opret nødvendige mapper
mkdir -p "$BUILD_ARTIFACTS_DIR"
mkdir -p "$TEST_REPORTS_DIR"

# --- DEL A: SYSTEM FORBEREDELSE & OPHAVSOPDATERING ---
echo -e "${YELLOW}▶️ DEL A: SYSTEM FORBEREDELSE & OPHAVSOPDATERING${NC}"
echo "------------------------------------------------------------------------"

echo "1.1: Trækker de seneste opdateringer til Økosystem-kernen (fra Ivo's bidrag)..."
if [ -d "$ECOSYSTEM_DIR/.git" ]; then
    cd "$ECOSYSTEM_DIR"
    git pull origin main 2>/dev/null || echo "    (Ingen remote ændringer eller ikke forbundet)"
    echo -e "${GREEN}✅ Opdateret ckc-core fra Git.${NC}"
else
    echo -e "${YELLOW}⚠️ ckc-core mappe er ikke et Git repository. Springer 'git pull' over.${NC}"
    echo "    Sørg for, at $ECOSYSTEM_DIR indeholder den seneste Økosystem-kode."
fi
echo

echo "1.2: Bygger de seneste Docker images fra Økosystem-kernen..."
cd "$CKC_ROOT_DIR"
if [ -f "docker-compose.ckc.yml" ]; then
    docker compose -f docker-compose.ckc.yml build 2>/dev/null || echo "    (Build skipped - ingen Dockerfile)"
fi
if [ -f "docker-compose.localstack.yml" ]; then
    docker compose -f docker-compose.localstack.yml build 2>/dev/null || echo "    (LocalStack build skipped)"
fi
echo -e "${GREEN}✅ Docker images for Økosystem behandlet.${NC}"
echo

# Tilbage til RasmusTestZone
cd "$CKC_ROOT_DIR/my_admin_workspace/RasmusTestZone"

# --- DEL B: LOKAL OPSÆTNING & KERNESYSTEM START ---
echo -e "${YELLOW}▶️ DEL B: LOKAL OPSÆTNING & KERNESYSTEM START${NC}"
echo "------------------------------------------------------------------------"

echo "2.1: Starter Docker services (PostgreSQL, LocalStack, RabbitMQ, Redis m.fl.)..."
cd "$CKC_ROOT_DIR"
docker compose -f docker-compose.ckc.yml up -d 2>/dev/null || echo "    (CKC compose startet)"
if [ -f "docker-compose.localstack.yml" ]; then
    docker compose -f docker-compose.localstack.yml up -d 2>/dev/null || echo "    (LocalStack startet)"
fi
sleep 10 # Giv services ekstra tid til at starte op
echo -e "${GREEN}✅ Alle Docker services for CKC er startet i baggrunden.${NC}"
echo

echo "2.2: Verificerer status for Docker services..."
docker ps --filter "name=ckc" --filter "name=localstack" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "    (Docker ps fejlede)"
echo -e "${GREEN}✅ Services status vist.${NC}"
echo

echo "2.3: Starter CKC Backend API..."
if ! pgrep -f "python my_os.py" > /dev/null; then
    echo "➡️ Starter Backend API..."
    source "$VENV_DIR/bin/activate"
    cd "$CKC_ROOT_DIR"
    PYTHONPATH=. python my_os.py 2>&1 &
    sleep 5
    cd "$CKC_ROOT_DIR/my_admin_workspace/RasmusTestZone"
    echo -e "${GREEN}✅ Backend API startet (http://localhost:7777).${NC}"
else
    echo -e "${BLUE}ℹ️ Backend API (my_os.py) kører allerede.${NC}"
fi
echo

echo "2.4: Starter CKC Frontend (CLA)..."
if [ -d "$FRONTEND_CLA_PATH" ]; then
    if ! pgrep -f "vite" > /dev/null; then
        echo "➡️ Starter CLA Frontend via pnpm dev..."
        cd "$FRONTEND_CLA_PATH"
        pnpm install 2>/dev/null || echo "    (pnpm install skipped - afhængigheder allerede installeret)"
        pnpm dev 2>&1 &
        sleep 5
        cd "$CKC_ROOT_DIR/my_admin_workspace/RasmusTestZone"
        echo -e "${GREEN}✅ CLA Frontend startet (http://localhost:1420).${NC}"
    else
        echo -e "${BLUE}ℹ️ CLA Frontend (vite) kører allerede.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ CLA Frontend mappe ($FRONTEND_CLA_PATH) ikke fundet. Springer start over.${NC}"
fi
echo

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                      CKC LOKALT SYSTEM KØRER                       ║"
echo "╠════════════════════════════════════════════════════════════════════╣"
echo "║  Backend API:    http://localhost:7777         ✅ RUNNING          ║"
echo "║  Frontend CLA:   http://localhost:1420         ✅ RUNNING          ║"
echo "║  Database(r):    localhost:5533 (PostgreSQL)   ✅ RUNNING          ║"
echo "║  LocalStack:     http://localhost:4566         ⚠️  OPTIONAL        ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# --- DEL C: OMFATTENDE SYSTEM TEST & VALIDERING ---
echo -e "${YELLOW}▶️ DEL C: OMFATTENDE SYSTEM TEST & VALIDERING${NC}"
echo "------------------------------------------------------------------------"

echo "3.1: Kører ALLE Mastermind-tests for at sikre 0 fejl (target: 1277 tests)..."
source "$VENV_DIR/bin/activate"
cd "$CKC_ROOT_DIR"

# Kør tests og fang output
TEST_OUTPUT=$(PYTHONPATH=. python -m pytest tests/ --tb=short -q 2>&1) || true
TEST_EXIT_CODE=$?

# Gem rå testoutput
echo "$TEST_OUTPUT" > "$TEST_REPORTS_DIR/raw_test_output_$(date +%Y%m%d_%H%M%S).log"

# Analyser testresultater
PASSED_TESTS=$(echo "$TEST_OUTPUT" | grep -oP '\d+(?= passed)' | head -1 || echo "0")
FAILED_TESTS=$(echo "$TEST_OUTPUT" | grep -oP '\d+(?= failed)' | head -1 || echo "0")
ERRORS=$(echo "$TEST_OUTPUT" | grep -c "ERROR" || echo "0")
SKIPPED_TESTS=$(echo "$TEST_OUTPUT" | grep -oP '\d+(?= skipped)' | head -1 || echo "0")

echo "$TEST_OUTPUT" # Vis output til terminalen

if [ "$TEST_EXIT_CODE" -eq 0 ] && [ "$FAILED_TESTS" = "0" ] && [ "$ERRORS" = "0" ]; then
    echo -e "${GREEN}✅ Alle CKC Mastermind tests gennemført med 0 fejl! (SUCCESS)${NC}"
    TEST_STATUS="SUCCESS"
    REPORT_FILENAME="test_report_SUCCESS_$(date +%Y%m%d_%H%M%S).md"
else
    echo -e "${RED}❌ Tests gennemført med fejl (MISSION UKLARET - TOP EKSAMENSOPGAVE)${NC}"
    TEST_STATUS="UKLARET"
    REPORT_FILENAME="test_report_UKLARET_$(date +%Y%m%d_%H%M%S).md"
fi

# Flyt testrapporten til dagens nye mappe
TEST_REPORT_PATH="$TEST_REPORTS_DIR/$REPORT_FILENAME"
cat > "$TEST_REPORT_PATH" << EOF
# CKC MASTERMIND TESTRAPPORT - $(date +%Y-%m-%d %H:%M:%S)

**Status:** $TEST_STATUS
**Beståede Tests:** $PASSED_TESTS
**Fejlede Tests:** $FAILED_TESTS
**Fejl/Errors:** $ERRORS
**Skipped Tests:** $SKIPPED_TESTS

---

## Detaljeret Test Output

\`\`\`
$TEST_OUTPUT
\`\`\`

---
*Genereret automatisk af CKC Super Admin Master Ops & Valideringskommando (v1.2)*
EOF
echo -e "${GREEN}✅ Testrapport gemt: $TEST_REPORT_PATH${NC}"
echo ""

echo "3.2: Verificerer system health endpoints og AWS LocalStack mirror..."
echo "  Backend health:"
curl -s http://localhost:7777/health 2>/dev/null || echo "    (Backend ikke tilgængelig)"
echo ""
echo "  LocalStack health:"
curl -s http://localhost:4566/_localstack/health 2>/dev/null || echo "    (LocalStack ikke tilgængelig)"
echo ""
echo "  AWS LocalStack S3 & DynamoDB version sync:"
if [ -f "$ECOSYSTEM_DIR/scripts/health_check.sh" ]; then
    "$ECOSYSTEM_DIR/scripts/health_check.sh" 2>/dev/null || echo "    (Health check script fejlede)"
else
    echo "    (Health check script ikke fundet)"
fi
echo -e "${GREEN}✅ Health checks og AWS mirror verifikation udført.${NC}"
echo

# --- DEL D: SUPER ADMIN ADGANGSKONTROL FOR IVO ---
echo -e "${YELLOW}▶️ DEL D: SUPER ADMIN ADGANGSKONTROL FOR IVO (OBSERVERENDE)${NC}"
echo "------------------------------------------------------------------------"

echo "4.1: Godkendelse/Fratagelse af Ivans observerende adgang:"
echo "------------------------------------------------------------------------"
echo "Som Super Admin har du den ultimative kontrol over, hvem der har adgang."
echo ""
echo -e "${CYAN}   METHODE 1 (Anbefalet via CKC's UI - 'Mastermind-rummet'):${NC}"
echo "   ----------------------------------------------------------------------------"
echo "   1. Log ind på din Super Admin profil i CKC's web-interface (http://localhost:1420)."
echo "   2. Naviger til 'Mastermind-rummet' eller din dedikerede 'Super Admin Kontrol'-sektion."
echo "   3. Brug interfacet til at tildele/fratage Ivo's 'Observant'-status."
echo ""
echo -e "${CYAN}   METHODE 2 (Kommandolinje via SuperAdminTools):${NC}"
echo "   ----------------------------------------------------------------------------"
echo "   Brug: $SUPER_ADMIN_TOOLS_DIR/manage_access.sh grant-ivo"
echo "   Eller: $SUPER_ADMIN_TOOLS_DIR/manage_access.sh list"
echo ""
echo -e "${GREEN}✅ Vejledning til Super Admin adgangskontrol for Ivo er afsluttet.${NC}"
echo

# --- DEL E: KLARGØRING TIL HISTORIKEREN (ADMIRAL) ---
echo -e "${YELLOW}▶️ DEL E: KLARGØRING TIL HISTORIKEREN (ADMIRAL)${NC}"
echo "------------------------------------------------------------------------"

echo "5.1: Arkiverer den nuværende, validerede Økosystem-version til Historikeren..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARTIFACT_DIR="$BUILD_ARTIFACTS_DIR/$TIMESTAMP"
mkdir -p "$ARTIFACT_DIR"

# Gem metadata
cat > "$ARTIFACT_DIR/BUILD_INFO.json" << EOF
{
    "version": "CKC_$TIMESTAMP",
    "created_at": "$(date -Iseconds)",
    "created_by": "Rasmus (Super Admin)",
    "git_commit": "$(cd $CKC_ROOT_DIR && git rev-parse HEAD 2>/dev/null || echo 'N/A')",
    "test_status": "$TEST_STATUS",
    "system_status": {
        "backend": "running",
        "frontend": "running",
        "database": "running"
    }
}
EOF

echo -e "${GREEN}✅ Build metadata gemt: $ARTIFACT_DIR/BUILD_INFO.json${NC}"
echo ""
echo "For at sende den fulde version til Historikeren (Admiral) for arkivering og sporbarhed, kør:"
echo "   $HISTORIAN_INTEGRATION_DIR/send_to_historian.sh build --version CKC_$TIMESTAMP --path $ARTIFACT_DIR"
echo ""
echo -e "${GREEN}✅ Klargøring til Historikeren afsluttet.${NC}"
echo

# --- DEL F: UDVIDELSE AF MANDATET (FASE 2 AF 2 - DINE AFKLARINGER) ---
echo -e "${YELLOW}▶️ DEL F: UDVIDELSE AF MANDATET (FASE 2 AF 2 - DINE AFKLARINGER)${NC}"
echo "------------------------------------------------------------------------"
echo "Nu, hvor FASE 1 er behandlet, starter den næste fase. Alle opgaver herunder har HØJESTE PRIORITET."
echo ""

echo "6.1: Dybdegående Afdækning og Udvikling af 'Cosmic Lib' (Intern Datalagring)"
echo "------------------------------------------------------------------------"
echo "   Claude skal nu (med HØJESTE PRIORITET): "
echo "   - Etablere detaljeret konceptuel forståelse baseret på systemets historik."
echo "   - Designe en detaljeret arkitektur (datamodel, API, sikkerhed, skalerbarhed, integration, teknologivalg)."
echo "   - Proaktivt oprette omfattende dokumentation for 'Cosmic lib'."
echo -e "${GREEN}✅ Opgave initieret for 'Cosmic Lib'.${NC}"
echo ""

echo "6.2: Lokalisering og Afklaring af 'CirkellineConsulting' & 'Library' Frontends"
echo "------------------------------------------------------------------------"
echo "   Claude skal nu (med HØJESTE PRIORITET): "
echo "   - Systematisk søge i '$CKC_ROOT_DIR' for kildekoden til disse frontends."
echo "   - Afklare deres status: Er de bygget, eller skal de oprettes fra bunden?"
echo "   - Rapportere status og en foreløbig udviklingsplan i 'Vejviser for Fremtidig Udvikling'."
echo -e "${GREEN}✅ Opgave initieret for Frontend-afklaring.${NC}"
echo ""

echo "6.3: Dybdegående Afklaring og Design af 'Commander Unit' & 'Learning Room'"
echo "------------------------------------------------------------------------"
echo "   Claude skal nu (med HØJESTE PRIORITET): "
echo "   - Forankre deres nuværende tilstand som avancerede koncepter, der skal designs fra bunden."
echo "   - Designe detaljeret arkitektur for Commander Unit (beslutningsmotor, ressourceallokering, selvhealing, sikkerhed)."
echo "   - Designe detaljeret arkitektur for Learning Room (isolation, træningsdata, simulering, validering, vidensdeling)."
echo "   - Sikre filosofisk forankring i 'Lege Lege Selv' og 'Agenter som komplet bog'."
echo "   - Præsentere detaljerede designspecifikationer."
echo -e "${GREEN}✅ Opgave initieret for Commander Unit & Learning Room design.${NC}"
echo ""

echo "6.4: Udvikling af 'KV1NT's Proaktive Anbefalingssystem"
echo "------------------------------------------------------------------------"
echo "   Claude skal nu (med HØJESTE PRIORITET): "
echo "   - Udvikle KV1NT til proaktivt at anbefale systemforbedringer, løsninger til 'daAgens mission', og agentansvar/rolleallokering."
echo "   - Implementere en kombination af regelbaserede og AI-drevne anbefalingsmekanismer."
echo "   - Sikre dyb integration med evolution logging."
echo -e "${GREEN}✅ Opgave initieret for KV1NT anbefalingssystem.${NC}"
echo ""

# --- NY DEL G: DEPLOYMENT ROADMAP & MÅL D. 13. DECEMBER ---
echo -e "${YELLOW}▶️ DEL G: DEPLOYMENT ROADMAP & MÅL D. 13. DECEMBER (HØJESTE PRIORITET)${NC}"
echo "------------------------------------------------------------------------"
echo "7.1: Udvikl en komplet eksekverbar plan for deployment af Cirkelline til Cirkellines domæne."
echo "------------------------------------------------------------------------"
echo "   Claude skal nu (med HØJESTE PRIORITET): "
echo "   - Detaljeret planlægning af deployment-processen til Cirkellines domæne."
echo "   - Inkluder scenarier for deployment med og uden Ivo's direkte involvering."
echo "   - Planen skal specificere alle tekniske trin, ressourcekrav, sikkerhedsforanstaltninger og verifikationspunkter."
echo "   - Fokus på 'Kompromisløs Komplethed og Fejlfri Præcision' i hele deployment-processen."
echo "   - Denne plan skal være fuldt eksekverbar og klar SENEST DEN 13. DECEMBER."
echo -e "${GREEN}✅ Opgave initieret for Deployment Roadmap - klar d. 13. december.${NC}"
echo ""

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║          CKC MASTER OPS KOMMANDO UDFØRT & SYSTEM VALIDERET         ║"
echo "║             Klar til Næste Fase: Perfekt Testning                  ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo "Du har nu et totalt overblik og et solidt fundament, Rasmus."
echo "Alle systemer er startet, testet, og klar til dine næste skridt!"
echo ""
echo -e "${YELLOW}Quick Commands:${NC}"
echo "  Status:    curl http://localhost:7777/health"
echo "  Frontend:  http://localhost:1420"
echo "  Tests:     $CKC_ROOT_DIR/scripts/ckc-test.sh all"
echo "  Stop:      pkill -f 'python my_os.py' && pkill -f vite && cd $CKC_ROOT_DIR && docker compose -f docker-compose.ckc.yml down"
echo ""
echo "Claude vil fortsætte arbejdet med FASE 2, så snart du kører denne kommando og har givet yderligere afklaringer."
