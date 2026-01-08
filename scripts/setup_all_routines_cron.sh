#!/bin/bash
#
# CIRKELLINE RUTINER CRON SETUP
# =============================
# Installerer alle 3 automatiske rutiner:
#   - 03:33 Sorting Routine
#   - 09:00 Morning Sync
#   - 21:21 Evening Optimization
#
# Brug: ./setup_all_routines_cron.sh [--remove]
#

set -e

# Farver
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Find script directory og project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Find Python
PYTHON_PATH=$(which python3 2>/dev/null || which python 2>/dev/null)
if [ -z "$PYTHON_PATH" ]; then
    echo -e "${RED}Python ikke fundet!${NC}"
    exit 1
fi

# Scripts
SORTING_SCRIPT="$SCRIPT_DIR/sorting_0333.py"
MORNING_SCRIPT="$SCRIPT_DIR/morning_sync_0900.py"
EVENING_SCRIPT="$SCRIPT_DIR/evening_opt_2121.py"

# Log directory
LOG_DIR="/var/log/ckc"

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║           CIRKELLINE RUTINER CRON SETUP                                   ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║  03:33  Sorting Routine      - System cleanup & optimization              ║"
echo "║  09:00  Morning Sync         - Daily health check & metrics               ║"
echo "║  21:21  Evening Optimization - Prepare for next day                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for --remove flag
if [ "$1" == "--remove" ]; then
    echo -e "${YELLOW}▶️ REMOVING CRON JOBS${NC}"
    echo "------------------------------------------------------------------------"

    # Get current crontab
    CURRENT_CRON=$(crontab -l 2>/dev/null || true)

    # Remove our entries
    NEW_CRON=$(echo "$CURRENT_CRON" | grep -v "sorting_0333.py" | grep -v "morning_sync_0900.py" | grep -v "evening_opt_2121.py" || true)

    # Apply new crontab
    echo "$NEW_CRON" | crontab -

    echo -e "${GREEN}✅ All routine cron jobs removed${NC}"
    exit 0
fi

# Verify scripts exist
echo -e "${YELLOW}▶️ VERIFYING SCRIPTS${NC}"
echo "------------------------------------------------------------------------"

for script in "$SORTING_SCRIPT" "$MORNING_SCRIPT" "$EVENING_SCRIPT"; do
    if [ -f "$script" ]; then
        echo -e "  ${GREEN}✓${NC} $(basename $script)"
    else
        echo -e "  ${RED}✗${NC} $(basename $script) - IKKE FUNDET"
        exit 1
    fi
done

# Create log directory
echo ""
echo -e "${YELLOW}▶️ CREATING LOG DIRECTORY${NC}"
echo "------------------------------------------------------------------------"

if [ ! -d "$LOG_DIR" ]; then
    sudo mkdir -p "$LOG_DIR"
    sudo chown $USER:$USER "$LOG_DIR"
    echo -e "  ${GREEN}✓${NC} Created $LOG_DIR"
else
    echo -e "  ${GREEN}✓${NC} $LOG_DIR already exists"
fi

# Backup current crontab
echo ""
echo -e "${YELLOW}▶️ BACKING UP CRONTAB${NC}"
echo "------------------------------------------------------------------------"

BACKUP_FILE="/tmp/crontab_backup_$(date +%Y%m%d_%H%M%S)"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "" > "$BACKUP_FILE"
echo -e "  ${GREEN}✓${NC} Backup saved to $BACKUP_FILE"

# Build cron entries
CRON_SORTING="33 3 * * * $PYTHON_PATH $SORTING_SCRIPT >> $LOG_DIR/sorting_0333.log 2>&1"
CRON_MORNING="0 9 * * * $PYTHON_PATH $MORNING_SCRIPT >> $LOG_DIR/morning_sync.log 2>&1"
CRON_EVENING="21 21 * * * $PYTHON_PATH $EVENING_SCRIPT >> $LOG_DIR/evening_opt.log 2>&1"

# Show what will be installed
echo ""
echo -e "${YELLOW}▶️ CRON ENTRIES TO INSTALL${NC}"
echo "------------------------------------------------------------------------"
echo ""
echo -e "${CYAN}# Cirkelline Daily Routines${NC}"
echo "$CRON_SORTING"
echo "$CRON_MORNING"
echo "$CRON_EVENING"
echo ""

# Ask for confirmation
echo -e "${YELLOW}Install these cron jobs? [y/N]${NC}"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installation cancelled${NC}"
    exit 0
fi

# Install cron jobs
echo ""
echo -e "${YELLOW}▶️ INSTALLING CRON JOBS${NC}"
echo "------------------------------------------------------------------------"

# Get current crontab (without our old entries)
CURRENT_CRON=$(crontab -l 2>/dev/null | grep -v "sorting_0333.py" | grep -v "morning_sync_0900.py" | grep -v "evening_opt_2121.py" || true)

# Build new crontab
NEW_CRON="$CURRENT_CRON

# Cirkelline Daily Routines (installed $(date +%Y-%m-%d))
$CRON_SORTING
$CRON_MORNING
$CRON_EVENING"

# Apply new crontab
echo "$NEW_CRON" | crontab -

echo -e "  ${GREEN}✓${NC} Cron jobs installed"

# Verify installation
echo ""
echo -e "${YELLOW}▶️ VERIFYING INSTALLATION${NC}"
echo "------------------------------------------------------------------------"

crontab -l | grep -E "(sorting_0333|morning_sync|evening_opt)" | while read line; do
    echo -e "  ${GREEN}✓${NC} $line"
done

# Summary
echo ""
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║           INSTALLATION COMPLETE                                           ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║  ✅ 03:33 - Sorting Routine                                               ║"
echo "║  ✅ 09:00 - Morning Sync                                                  ║"
echo "║  ✅ 21:21 - Evening Optimization                                          ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║  Logs:    $LOG_DIR/                                           ║"
echo "║  Remove:  ./setup_all_routines_cron.sh --remove                           ║"
echo "║  Status:  crontab -l                                                      ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${YELLOW}Quick Commands:${NC}"
echo "  Test sorting:  python3 $SORTING_SCRIPT --dry-run --verbose"
echo "  Test morning:  python3 $MORNING_SCRIPT --dry-run --verbose"
echo "  Test evening:  python3 $EVENING_SCRIPT --dry-run --verbose"
echo ""
