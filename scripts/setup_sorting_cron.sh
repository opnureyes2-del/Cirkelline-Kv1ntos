#!/bin/bash
# ==============================================================================
# 3:33 SORTERING RUTINE - CRON JOB SETUP
# ==============================================================================
# Installerer automatiseret 03:33 sortering rutine
# Super Admin: Rasmus (System Creator & Visionary)
# Agent: Kommandor #4
# Version: v1.3.5
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH="/home/rasmus/Desktop/projekts/projects/cirkelline-env/bin/python"
SORTING_SCRIPT="$SCRIPT_DIR/sorting_0333.py"
LOG_DIR="/var/log/ckc"

# Header
echo -e "${CYAN}"
echo "========================================================================"
echo "      3:33 SORTERING RUTINE - CRON JOB SETUP"
echo "========================================================================"
echo -e "${NC}"
echo ""

# Verify script exists
if [ ! -f "$SORTING_SCRIPT" ]; then
    echo -e "${RED}ERROR: Sorting script not found at: $SORTING_SCRIPT${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Sorting script found"

# Verify Python environment
if [ ! -f "$PYTHON_PATH" ]; then
    echo -e "${YELLOW}WARNING: Custom Python not found, using system python${NC}"
    PYTHON_PATH="python3"
fi
echo -e "${GREEN}[OK]${NC} Python: $PYTHON_PATH"

# Create log directory
echo ""
echo -e "${BLUE}Creating log directory...${NC}"
sudo mkdir -p "$LOG_DIR" 2>/dev/null || mkdir -p "$LOG_DIR" 2>/dev/null || true
echo -e "${GREEN}[OK]${NC} Log directory: $LOG_DIR"

# Backup existing crontab
echo ""
echo -e "${BLUE}Backing up existing crontab...${NC}"
BACKUP_FILE="/tmp/crontab_backup_$(date +%Y%m%d_%H%M%S)"
crontab -l > "$BACKUP_FILE" 2>/dev/null || echo "# Empty crontab" > "$BACKUP_FILE"
echo -e "${GREEN}[OK]${NC} Backup: $BACKUP_FILE"

# Check existing 03:33 jobs
echo ""
echo -e "${BLUE}Checking for existing 03:33 jobs...${NC}"
EXISTING=$(crontab -l 2>/dev/null | grep "33 3" || true)
if [ -n "$EXISTING" ]; then
    echo -e "${YELLOW}Found existing 03:33 jobs:${NC}"
    echo "$EXISTING"
    echo ""
fi

# Display planned job
echo -e "${BLUE}Planned cron job:${NC}"
echo "------------------------------------------------------------------------"
echo "33 3 * * * $PYTHON_PATH $SORTING_SCRIPT >> $LOG_DIR/sorting_0333.log 2>&1"
echo "------------------------------------------------------------------------"
echo ""

# Confirm
echo -e "${YELLOW}Install this cron job? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    # Create new crontab
    TEMP_CRON=$(mktemp)

    # Keep existing jobs (except old sorting jobs)
    crontab -l 2>/dev/null | grep -v "sorting_0333" > "$TEMP_CRON" || true

    # Add new job
    cat >> "$TEMP_CRON" << EOF

# ==============================================================================
# 3:33 SORTERING RUTINE - Daglig automatiseret sortering
# Installeret: $(date)
# Agent: Kommandor #4
# ==============================================================================
33 3 * * * $PYTHON_PATH $SORTING_SCRIPT >> $LOG_DIR/sorting_0333.log 2>&1
EOF

    # Install crontab
    crontab "$TEMP_CRON"
    rm -f "$TEMP_CRON"

    echo ""
    echo -e "${GREEN}========================================================================"
    echo "                    CRON JOB INSTALLERET"
    echo "========================================================================${NC}"
    echo ""

    # Verify
    echo -e "${BLUE}Verificering:${NC}"
    crontab -l | grep -A 5 "3:33 SORTERING" || crontab -l | grep "sorting_0333"

    echo ""
    echo -e "${CYAN}Nyttige kommandoer:${NC}"
    echo "  Vis jobs:     crontab -l | grep sorting"
    echo "  Test nu:      $PYTHON_PATH $SORTING_SCRIPT --dry-run"
    echo "  Live run:     $PYTHON_PATH $SORTING_SCRIPT"
    echo "  Vis log:      tail -f $LOG_DIR/sorting_0333.log"
else
    echo ""
    echo -e "${YELLOW}Installation afbrudt${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Done!${NC}"
