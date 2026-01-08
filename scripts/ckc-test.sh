#!/bin/bash
#
# CKC MASTERMIND Test & Management Script
# Brug: ./scripts/ckc-test.sh [kommando]
#

set -e

# Farver
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
PROJECT_DIR="/home/rasmus/Desktop/projects/cirkelline-system"
VENV_DIR="/home/rasmus/Desktop/projects/cirkelline-env"

# Aktivér virtual environment
activate_env() {
    source "$VENV_DIR/bin/activate"
    cd "$PROJECT_DIR"
    export PYTHONPATH="$PROJECT_DIR"
}

# Print header
print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════╗"
    echo "║       CKC MASTERMIND TEST RUNNER           ║"
    echo "╚════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Hjælp
show_help() {
    print_header
    echo -e "${YELLOW}Brug:${NC} ./scripts/ckc-test.sh [kommando]"
    echo ""
    echo -e "${GREEN}Tilgængelige kommandoer:${NC}"
    echo ""
    echo "  all         - Kør ALLE 773 MASTERMIND tests"
    echo "  quick       - Hurtig smoke test (kun coordinator)"
    echo "  aws         - Kør AWS integration tests (kræver LocalStack)"
    echo "  module NAME - Kør tests for specifikt modul"
    echo ""
    echo "  localstack-up   - Start LocalStack container"
    echo "  localstack-down - Stop LocalStack container"
    echo "  localstack-status - Check LocalStack health"
    echo ""
    echo "  imports     - Verificér alle imports virker"
    echo "  coverage    - Kør tests med coverage rapport"
    echo ""
    echo -e "${YELLOW}Eksempler:${NC}"
    echo "  ./scripts/ckc-test.sh all"
    echo "  ./scripts/ckc-test.sh module session"
    echo "  ./scripts/ckc-test.sh module ethics"
    echo "  ./scripts/ckc-test.sh aws"
    echo ""
}

# Kør alle tests
run_all_tests() {
    print_header
    echo -e "${GREEN}Kører ALLE MASTERMIND tests...${NC}"
    echo ""
    activate_env

    python -m pytest \
        tests/test_mastermind.py \
        tests/test_context.py \
        tests/test_messaging.py \
        tests/test_roles.py \
        tests/test_feedback.py \
        tests/test_resources.py \
        tests/test_optimization.py \
        tests/test_os_dirigent.py \
        tests/test_ethics.py \
        tests/test_ux.py \
        tests/test_economics.py \
        tests/test_marketplace.py \
        tests/test_training_room.py \
        tests/test_self_optimization.py \
        tests/test_aws_integration.py \
        tests/test_session.py \
        tests/test_output_integrity.py \
        --tb=short -q

    echo ""
    echo -e "${GREEN}✅ Alle tests afsluttet!${NC}"
}

# Hurtig smoke test
run_quick_test() {
    print_header
    echo -e "${YELLOW}Kører hurtig smoke test...${NC}"
    echo ""
    activate_env

    python -m pytest tests/test_mastermind.py -q --tb=short

    echo ""
    echo -e "${GREEN}✅ Smoke test afsluttet!${NC}"
}

# AWS tests
run_aws_tests() {
    print_header
    echo -e "${BLUE}Kører AWS integration tests...${NC}"
    echo ""
    activate_env

    # Check om LocalStack kører
    if curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
        echo -e "${GREEN}LocalStack kører - kører live tests${NC}"
        LOCALSTACK_AVAILABLE=true python -m pytest tests/test_aws_integration.py -v --tb=short
    else
        echo -e "${YELLOW}LocalStack kører IKKE - kører kun mock tests${NC}"
        python -m pytest tests/test_aws_integration.py -v --tb=short
    fi

    echo ""
    echo -e "${GREEN}✅ AWS tests afsluttet!${NC}"
}

# Test specifikt modul
run_module_test() {
    local module=$1
    print_header
    echo -e "${BLUE}Kører tests for modul: ${YELLOW}$module${NC}"
    echo ""
    activate_env

    local test_file="tests/test_${module}.py"

    if [ -f "$test_file" ]; then
        python -m pytest "$test_file" -v --tb=short
        echo ""
        echo -e "${GREEN}✅ Module test afsluttet!${NC}"
    else
        echo -e "${RED}❌ Testfil ikke fundet: $test_file${NC}"
        echo ""
        echo "Tilgængelige moduler:"
        ls tests/test_*.py | sed 's/tests\/test_/  - /g' | sed 's/.py//g'
        exit 1
    fi
}

# Start LocalStack
localstack_up() {
    print_header
    echo -e "${BLUE}Starter LocalStack...${NC}"
    cd "$PROJECT_DIR"

    docker compose -f docker-compose.localstack.yml up -d

    echo "Venter på LocalStack er klar..."
    sleep 5

    if curl -s http://localhost:4566/_localstack/health | grep -q "running"; then
        echo -e "${GREEN}✅ LocalStack kører!${NC}"
        curl -s http://localhost:4566/_localstack/health | python -m json.tool
    else
        echo -e "${YELLOW}⏳ LocalStack starter stadig...${NC}"
    fi
}

# Stop LocalStack
localstack_down() {
    print_header
    echo -e "${YELLOW}Stopper LocalStack...${NC}"
    cd "$PROJECT_DIR"

    docker compose -f docker-compose.localstack.yml down

    echo -e "${GREEN}✅ LocalStack stoppet!${NC}"
}

# LocalStack status
localstack_status() {
    print_header
    echo -e "${BLUE}LocalStack Status:${NC}"
    echo ""

    if curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ LocalStack KØRER${NC}"
        echo ""
        curl -s http://localhost:4566/_localstack/health | python -m json.tool
    else
        echo -e "${RED}❌ LocalStack kører IKKE${NC}"
        echo ""
        echo "Start med: ./scripts/ckc-test.sh localstack-up"
    fi
}

# Verificér imports
check_imports() {
    print_header
    echo -e "${BLUE}Verificerer alle MASTERMIND imports...${NC}"
    echo ""
    activate_env

    python -c "
from cirkelline.ckc.mastermind import (
    # Coordinator (DEL A)
    MastermindCoordinator,
    # Session (DEL B)
    SessionManager,
    InMemorySessionStore,
    FileSessionStore,
    # Messaging
    InMemoryMessageBus,
    MastermindMessage,
    # Roles
    ParticipantRole,
    AgentParticipation,
    # Feedback (DEL C)
    FeedbackAggregator,
    FeedbackItem,
    # Resources
    ResourceAllocator,
    ResourcePool,
    # Context (DEL D)
    ContextBundle,
    DirigentContextManager,
    # Optimization (DEL F)
    OptimizationRun,
    OptimizationSchedule,
    # OS Dirigent (DEL E)
    OSDirigent,
    SystemsDirigent,
    # Ethics (DEL G)
    EthicsGuardrails,
    BiasDetector,
    TransparencyLogger,
    # UX (DEL H)
    AdaptiveUI,
    UserFeedbackCollector,
    PreferenceManager,
    # Economics (DEL I)
    RevenueTracker,
    SubscriptionManager,
    UsageMetering,
    # Marketplace (DEL J)
    MarketplaceConnector,
    CommunityHub,
    DiscoveryEngine,
    # Training Room (DEL K)
    CommanderTrainingRoom,
    # Self Optimization
    SelfOptimizationScheduler,
    # Output Integrity
    OutputIntegritySystem,
    OutputValidationGateway,
    # Super Admin
    SuperAdminControlSystem
)
print('✅ DEL A: MastermindCoordinator')
print('✅ DEL B: SessionManager, InMemoryMessageBus, Roles')
print('✅ DEL C: FeedbackAggregator, ResourceAllocator')
print('✅ DEL D: ContextBundle, DirigentContextManager')
print('✅ DEL E: OSDirigent, SystemsDirigent')
print('✅ DEL F: OptimizationRun, OptimizationSchedule')
print('✅ DEL G: EthicsGuardrails, BiasDetector, TransparencyLogger')
print('✅ DEL H: AdaptiveUI, UserFeedbackCollector, PreferenceManager')
print('✅ DEL I: RevenueTracker, SubscriptionManager, UsageMetering')
print('✅ DEL J: MarketplaceConnector, CommunityHub, DiscoveryEngine')
print('✅ DEL K: CommanderTrainingRoom')
print('✅ EXTRA: SelfOptimizationScheduler, OutputIntegritySystem')
print('✅ EXTRA: SuperAdminControlSystem')
print()
print('═' * 50)
print('ALLE MASTERMIND MODULER IMPORTERET KORREKT!')
print('═' * 50)
"
}

# Coverage rapport
run_coverage() {
    print_header
    echo -e "${BLUE}Kører tests med coverage...${NC}"
    echo ""
    activate_env

    python -m pytest tests/ \
        --cov=cirkelline.ckc.mastermind \
        --cov-report=html \
        --cov-report=term-missing \
        -q --tb=short

    echo ""
    echo -e "${GREEN}✅ Coverage rapport genereret: htmlcov/index.html${NC}"
}

# Main
case "${1:-help}" in
    all)
        run_all_tests
        ;;
    quick)
        run_quick_test
        ;;
    aws)
        run_aws_tests
        ;;
    module)
        if [ -z "$2" ]; then
            echo -e "${RED}Fejl: Angiv modulnavn${NC}"
            echo "Brug: ./scripts/ckc-test.sh module [navn]"
            exit 1
        fi
        run_module_test "$2"
        ;;
    localstack-up)
        localstack_up
        ;;
    localstack-down)
        localstack_down
        ;;
    localstack-status)
        localstack_status
        ;;
    imports)
        check_imports
        ;;
    coverage)
        run_coverage
        ;;
    help|--help|-h|*)
        show_help
        ;;
esac
