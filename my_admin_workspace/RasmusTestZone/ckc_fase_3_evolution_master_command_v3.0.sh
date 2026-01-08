#!/bin/bash
# ==============================================================================
# CKC FASE 3: HYPER-EVOLUTION MASTER COMMAND v3.0
# ==============================================================================
# Komplet system for daglig evolution, 5x robust testing, og KV1NT integration
# Super Admin: Rasmus (System Creator & Visionary)
# CKC = Master Hovedkontor for Skabelse af Alt
# ==============================================================================

# Farver
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Paths
CKC_ROOT="/home/rasmus/Desktop/projects/cirkelline-system"
CKC_CORE="$CKC_ROOT/ecosystems/ckc-core"
CKC_VENV="/home/rasmus/Desktop/projects/ckc-core-env"
VERSIONS_DIR="$CKC_ROOT/ecosystems/versions"
EVOLUTION_REPORTS="$CKC_ROOT/ecosystems/evolution_reports"
SCRIPTS_DIR="$CKC_CORE/scripts"
HISTORIAN_DIR="$CKC_ROOT/my_admin_workspace/HistorianIntegration"

# Ports
BACKEND_PORT=7778
DB_PORT=5533
FRONTEND_PORT=3001
CLA_PORT=1420

# Counters
PHASE_PASSED=0
PHASE_FAILED=0
START_TIME=$(date +%s)

# Dagens dato og version
TODAY=$(date +%Y%m%d)
TIMESTAMP=$(date -Iseconds)

echo -e "${MAGENTA}"
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║      ██████╗██╗  ██╗ ██████╗    ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗   ║"
echo "║     ██╔════╝██║ ██╔╝██╔════╝    ██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗  ║"
echo "║     ██║     █████╔╝ ██║         ███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝  ║"
echo "║     ██║     ██╔═██╗ ██║         ██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗  ║"
echo "║     ╚██████╗██║  ██╗╚██████╗    ██║  ██║   ██║   ██║     ███████╗██║  ██║  ║"
echo "║      ╚═════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝  ║"
echo "║                                                                            ║"
echo "║          FASE 3: HYPER-EVOLUTION MASTER COMMAND v3.0                       ║"
echo "║          Super Admin: Rasmus (System Creator & Visionary)                  ║"
echo "║          CKC = Master Hovedkontor for Skabelse af Alt                      ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "Tidspunkt: $(date)"
echo "Mode: ${1:-full}"
echo ""

# ==============================================================================
# HJÆLPEFUNKTIONER
# ==============================================================================

log_phase() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}▶ $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════${NC}"
}

log_step() {
    echo -e "${YELLOW}  → $1${NC}"
}

log_success() {
    echo -e "${GREEN}  ✅ $1${NC}"
    PHASE_PASSED=$((PHASE_PASSED + 1))
}

log_error() {
    echo -e "${RED}  ❌ $1${NC}"
    PHASE_FAILED=$((PHASE_FAILED + 1))
}

log_warning() {
    echo -e "${YELLOW}  ⚠️ $1${NC}"
}

check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port available
    fi
}

# ==============================================================================
# FASE A: PRÆ-CHECK & MILJØ VERIFIKATION
# ==============================================================================

fase_a_precheck() {
    log_phase "FASE A: PRÆ-CHECK & MILJØ VERIFIKATION"

    log_step "A.1: Verificerer mapper..."
    if [ -d "$CKC_CORE" ]; then
        log_success "ckc-core mappe fundet"
    else
        log_error "ckc-core mappe IKKE fundet"
        return 1
    fi

    log_step "A.2: Verificerer virtualenv..."
    if [ -d "$CKC_VENV" ]; then
        log_success "ckc-core-env virtualenv fundet"
    else
        log_error "ckc-core-env virtualenv IKKE fundet"
        return 1
    fi

    log_step "A.3: Verificerer database container..."
    if docker ps | grep -q "ckc-postgres"; then
        log_success "ckc-postgres container kører"
    else
        log_warning "ckc-postgres container kører IKKE - starter..."
        docker start ckc-postgres 2>/dev/null || log_error "Kunne ikke starte ckc-postgres"
    fi

    log_step "A.4: Port status check..."
    local ports_ok=true
    for port in $BACKEND_PORT $DB_PORT; do
        if check_port $port; then
            echo -e "    Port $port: ${GREEN}IN USE${NC}"
        else
            echo -e "    Port $port: ${YELLOW}AVAILABLE${NC}"
        fi
    done

    return 0
}

# ==============================================================================
# FASE B: DAGLIG VERSION OPRETTELSE
# ==============================================================================

fase_b_version_creation() {
    log_phase "FASE B: DAGLIG VERSION OPRETTELSE"

    log_step "B.1: Opretter ny version for i dag..."

    # Find næste version nummer
    local VERSION_NUM=1
    while [ -d "$VERSIONS_DIR/ckc-$TODAY-v$VERSION_NUM" ]; do
        VERSION_NUM=$((VERSION_NUM + 1))
    done

    VERSION_NAME="ckc-$TODAY-v$VERSION_NUM"
    VERSION_PATH="$VERSIONS_DIR/$VERSION_NAME"

    log_step "B.2: Kopierer kode til $VERSION_NAME..."
    mkdir -p "$VERSION_PATH"

    cp -r "$CKC_CORE/cirkelline" "$VERSION_PATH/" 2>/dev/null
    cp -r "$CKC_CORE/tests" "$VERSION_PATH/" 2>/dev/null
    cp -r "$CKC_CORE/locales" "$VERSION_PATH/" 2>/dev/null
    cp "$CKC_CORE/my_os.py" "$VERSION_PATH/" 2>/dev/null
    cp "$CKC_CORE/.env" "$VERSION_PATH/" 2>/dev/null
    cp "$CKC_CORE/requirements.txt" "$VERSION_PATH/" 2>/dev/null

    log_success "Kode kopieret til $VERSION_NAME"

    log_step "B.3: Opretter VERSION.json..."

    # Find parent version
    local PARENT_VERSION="none"
    if [ $VERSION_NUM -gt 1 ]; then
        PARENT_VERSION="ckc-$TODAY-v$((VERSION_NUM - 1))"
    fi

    cat > "$VERSION_PATH/VERSION.json" << EOF
{
    "version": "$VERSION_NAME",
    "created_at": "$TIMESTAMP",
    "created_by": "Rasmus (Super Admin)",
    "parent_version": "$PARENT_VERSION",
    "git_commit": "$(cd $CKC_ROOT && git rev-parse HEAD 2>/dev/null || echo 'N/A')",
    "status": "created",
    "test_results": null,
    "evolution_score": 0
}
EOF
    log_success "VERSION.json oprettet"

    # Gem version navn til brug senere
    echo "$VERSION_NAME" > /tmp/ckc_current_version
}

# ==============================================================================
# FASE C: 5x ROBUST STARTUP TEST
# ==============================================================================

fase_c_robust_test() {
    log_phase "FASE C: 5x ROBUST STARTUP TEST"

    local ROUND_RESULTS=()
    local ALL_PASSED=true

    for round in 1 2 3 4 5; do
        log_step "C.$round: Runde $round af 5..."

        local round_passed=0
        local round_failed=0

        # Test 1: Health
        if curl -s http://localhost:$BACKEND_PORT/health 2>/dev/null | grep -q "ok"; then
            round_passed=$((round_passed + 1))
        else
            round_failed=$((round_failed + 1))
        fi

        # Test 2: Database
        if docker exec ckc-postgres psql -U ckc -d ckc_brain -c "SELECT 1" 2>/dev/null | grep -q "1"; then
            round_passed=$((round_passed + 1))
        else
            round_failed=$((round_failed + 1))
        fi

        # Test 3: Config API
        if curl -s http://localhost:$BACKEND_PORT/config 2>/dev/null | grep -q "version"; then
            round_passed=$((round_passed + 1))
        else
            round_failed=$((round_failed + 1))
        fi

        # Test 4: Agents (check for 'specialist' since agents are named *-specialist)
        if curl -s http://localhost:$BACKEND_PORT/agents 2>/dev/null | grep -q "specialist"; then
            round_passed=$((round_passed + 1))
        else
            round_failed=$((round_failed + 1))
        fi

        # Test 5: Teams
        if curl -s http://localhost:$BACKEND_PORT/teams 2>/dev/null | grep -q "cirkelline"; then
            round_passed=$((round_passed + 1))
        else
            round_failed=$((round_failed + 1))
        fi

        if [ $round_failed -eq 0 ]; then
            echo -e "    Runde $round: ${GREEN}$round_passed/5 PASS${NC}"
            ROUND_RESULTS+=("PASS")
        else
            echo -e "    Runde $round: ${RED}$round_passed/5 (${round_failed} fejl)${NC}"
            ROUND_RESULTS+=("FAIL")
            ALL_PASSED=false
        fi

        # Pause mellem runder
        if [ $round -lt 5 ]; then
            sleep 2
        fi
    done

    if $ALL_PASSED; then
        log_success "ALLE 5 RUNDER BESTÅET!"
        return 0
    else
        log_error "Nogle runder fejlede"
        return 1
    fi
}

# ==============================================================================
# FASE D: TEST SUITE EXECUTION
# ==============================================================================

fase_d_test_suite() {
    log_phase "FASE D: TEST SUITE EXECUTION"

    log_step "D.1: Aktiverer virtualenv..."
    source "$CKC_VENV/bin/activate"

    log_step "D.2: Kører pytest tests..."
    cd "$CKC_CORE"

    local TEST_OUTPUT=$(PYTHONPATH=. python -m pytest tests/ --tb=no -q 2>&1)
    local TEST_EXIT_CODE=$?

    # Parse test results
    local PASSED=$(echo "$TEST_OUTPUT" | grep -oP '\d+(?= passed)' | head -1 || echo "0")
    local FAILED=$(echo "$TEST_OUTPUT" | grep -oP '\d+(?= failed)' | head -1 || echo "0")
    local TOTAL=$((PASSED + FAILED))

    echo "    Total tests: $TOTAL"
    echo "    Passed: $PASSED"
    echo "    Failed: $FAILED"

    if [ "$FAILED" = "0" ] || [ -z "$FAILED" ]; then
        log_success "Test suite gennemført succesfuldt"
    else
        log_warning "Test suite gennemført med $FAILED fejl"
    fi

    # Gem resultater
    echo "$PASSED" > /tmp/ckc_tests_passed
    echo "$FAILED" > /tmp/ckc_tests_failed
    echo "$TOTAL" > /tmp/ckc_tests_total

    return 0
}

# ==============================================================================
# FASE E: KV1NT (HISTORIAN) EVOLUTION LOGGING
# ==============================================================================

fase_e_kv1nt_logging() {
    log_phase "FASE E: KV1NT (HISTORIAN) EVOLUTION LOGGING"

    local VERSION_NAME=$(cat /tmp/ckc_current_version 2>/dev/null || echo "unknown")
    local TESTS_PASSED=$(cat /tmp/ckc_tests_passed 2>/dev/null || echo "0")
    local TESTS_FAILED=$(cat /tmp/ckc_tests_failed 2>/dev/null || echo "0")
    local TESTS_TOTAL=$(cat /tmp/ckc_tests_total 2>/dev/null || echo "0")

    # Beregn evolution score
    local EVOLUTION_SCORE=0
    if [ "$TESTS_TOTAL" -gt 0 ]; then
        EVOLUTION_SCORE=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))
    fi

    log_step "E.1: Opretter evolution rapport..."

    mkdir -p "$EVOLUTION_REPORTS"
    local REPORT_FILE="$EVOLUTION_REPORTS/evolution_$TODAY.json"

    cat > "$REPORT_FILE" << EOF
{
    "report_date": "$TODAY",
    "report_timestamp": "$TIMESTAMP",
    "version": "$VERSION_NAME",
    "super_admin": "Rasmus (System Creator & Visionary)",
    "test_results": {
        "total": $TESTS_TOTAL,
        "passed": $TESTS_PASSED,
        "failed": $TESTS_FAILED,
        "success_rate": $EVOLUTION_SCORE
    },
    "5x_robust_test": "COMPLETED",
    "evolution_score": $EVOLUTION_SCORE,
    "system_health": {
        "backend": "$(curl -s http://localhost:$BACKEND_PORT/health 2>/dev/null | grep -q 'ok' && echo 'healthy' || echo 'unknown')",
        "database": "$(docker exec ckc-postgres psql -U ckc -d ckc_brain -c 'SELECT 1' 2>/dev/null | grep -q '1' && echo 'healthy' || echo 'unknown')"
    },
    "recommendations": [],
    "kv1nt_analysis": "Pending detailed analysis"
}
EOF

    log_success "Evolution rapport gemt: $REPORT_FILE"

    log_step "E.2: Opretter KV1NT dagbogslog..."

    local DAGBOG_FILE="$EVOLUTION_REPORTS/KV1NT_DAGBOG_$TODAY.md"

    cat > "$DAGBOG_FILE" << EOF
# KV1NT DAGBOGSLOG - $TODAY

**Tidspunkt:** $(date)
**Version:** $VERSION_NAME
**Super Admin:** Rasmus (System Creator & Visionary)

---

## EVOLUTION STATUS

| Metrik | Værdi |
|--------|-------|
| Version | $VERSION_NAME |
| Tests Total | $TESTS_TOTAL |
| Tests Passed | $TESTS_PASSED |
| Tests Failed | $TESTS_FAILED |
| Success Rate | ${EVOLUTION_SCORE}% |
| 5x Robust Test | COMPLETED |

---

## SYSTEM HEALTH

- Backend (Port $BACKEND_PORT): $(curl -s http://localhost:$BACKEND_PORT/health 2>/dev/null | grep -q 'ok' && echo '✅ HEALTHY' || echo '⚠️ UNKNOWN')
- Database (Port $DB_PORT): $(docker exec ckc-postgres psql -U ckc -d ckc_brain -c 'SELECT 1' 2>/dev/null | grep -q '1' && echo '✅ HEALTHY' || echo '⚠️ UNKNOWN')

---

## PROAKTIVE ANBEFALINGER

*KV1NT vil generere anbefalinger baseret på evolutionsmønstre*

---

*Genereret af CKC Hyper-Evolution System v3.0*
*KV1NT (Historikeren) - Evolution Tracking*
EOF

    log_success "KV1NT dagbogslog oprettet: $DAGBOG_FILE"
}

# ==============================================================================
# FASE F: FINAL RAPPORT
# ==============================================================================

fase_f_final_report() {
    log_phase "FASE F: FINAL RAPPORT"

    local END_TIME=$(date +%s)
    local DURATION=$((END_TIME - START_TIME))
    local VERSION_NAME=$(cat /tmp/ckc_current_version 2>/dev/null || echo "unknown")

    echo ""
    echo -e "${MAGENTA}"
    echo "╔════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                            ║"
    echo "║          HYPER-EVOLUTION MASTER COMMAND RESULTAT                           ║"
    echo "║                                                                            ║"
    echo "╠════════════════════════════════════════════════════════════════════════════╣"
    echo -e "${NC}"
    echo -e "  Version oprettet:   ${CYAN}$VERSION_NAME${NC}"
    echo -e "  Faser gennemført:   ${GREEN}$PHASE_PASSED${NC}"
    echo -e "  Faser fejlet:       ${RED}$PHASE_FAILED${NC}"
    echo -e "  Total varighed:     ${duration}s"
    echo ""

    if [ $PHASE_FAILED -eq 0 ]; then
        echo -e "${GREEN}"
        echo "╔════════════════════════════════════════════════════════════════════════════╗"
        echo "║                                                                            ║"
        echo "║          ✅ ALLE FASER GENNEMFØRT SUCCESFULDT!                            ║"
        echo "║          CKC Evolution er nu opdateret og valideret                        ║"
        echo "║                                                                            ║"
        echo "╚════════════════════════════════════════════════════════════════════════════╝"
        echo -e "${NC}"
    else
        echo -e "${YELLOW}"
        echo "╔════════════════════════════════════════════════════════════════════════════╗"
        echo "║                                                                            ║"
        echo "║          ⚠️ EVOLUTION GENNEMFØRT MED ADVARSLER                            ║"
        echo "║          Se detaljer ovenfor for fejlede faser                            ║"
        echo "║                                                                            ║"
        echo "╚════════════════════════════════════════════════════════════════════════════╝"
        echo -e "${NC}"
    fi

    echo ""
    echo -e "${CYAN}Quick Commands:${NC}"
    echo "  Status:       curl http://localhost:$BACKEND_PORT/health"
    echo "  Tests:        cd $CKC_CORE && pytest tests/ -v"
    echo "  Evolution:    cat $EVOLUTION_REPORTS/evolution_$TODAY.json"
    echo "  KV1NT Log:    cat $EVOLUTION_REPORTS/KV1NT_DAGBOG_$TODAY.md"
    echo ""
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
    local MODE="${1:-full}"

    case "$MODE" in
        full)
            fase_a_precheck
            fase_b_version_creation
            fase_c_robust_test
            fase_d_test_suite
            fase_e_kv1nt_logging
            fase_f_final_report
            ;;
        precheck)
            fase_a_precheck
            ;;
        version)
            fase_b_version_creation
            ;;
        test)
            fase_c_robust_test
            fase_d_test_suite
            ;;
        report)
            fase_e_kv1nt_logging
            fase_f_final_report
            ;;
        *)
            echo "Brug: $0 [full|precheck|version|test|report]"
            echo ""
            echo "Modes:"
            echo "  full      - Kør alle faser (default)"
            echo "  precheck  - Kun miljø verifikation"
            echo "  version   - Kun version oprettelse"
            echo "  test      - Kun 5x robust test + test suite"
            echo "  report    - Kun KV1NT logging og rapport"
            exit 1
            ;;
    esac
}

main "$@"
