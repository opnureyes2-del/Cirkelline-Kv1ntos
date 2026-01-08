"""
Cirkelline Configuration Module
================================
Environment variables, logging setup, and constants.
"""

import logging
from datetime import datetime, timedelta
import time
import os
import uuid
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cirkelline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("Starting Cirkelline AgentOS...")
logger.info("Environment variables loaded from .env")

# DEBUG: Print DATABASE_URL to verify it's being set correctly (only in debug mode)
if os.getenv('AGNO_DEBUG', 'false').lower() == 'true':
    print(f"DEBUG: DATABASE_URL = {os.getenv('DATABASE_URL')}")
    logger.info(f"DEBUG: DATABASE_URL from environment = {os.getenv('DATABASE_URL')}")

# Force enable monitoring (environment variable not working)
os.environ["AGNO_MONITOR"] = "true"
logger.info("Monitoring forcefully enabled via code")

# ════════════════════════════════════════════════════════════════
# DEBUG MODE CONFIGURATION
# ════════════════════════════════════════════════════════════════
# Controls whether DEBUG print statements are shown in logs
# Set AGNO_DEBUG=true in .env for development (verbose logging)
# Set AGNO_DEBUG=false in .env for production (clean logs)
DEBUG_MODE = os.getenv('AGNO_DEBUG', 'false').lower() == 'true'
logger.info(f"Debug mode: {'ENABLED' if DEBUG_MODE else 'DISABLED'} (AGNO_DEBUG={os.getenv('AGNO_DEBUG', 'false')})")

# ════════════════════════════════════════════════════════════════
# ADMIN USER IDS FOR PERMISSION CHECKING
# ════════════════════════════════════════════════════════════════

# Admin user IDs for permission checking
# NOTE: Includes BOTH localhost and production IDs
ADMIN_USER_IDS = {
    # Localhost IDs
    "ee461076-8cbb-4626-947b-956f293cf7bf",  # Ivo - localhost
    "2c0a495c-3e56-4f12-ba68-a2d89e2deb71",  # Rasmus - localhost

    # Production IDs
    "fb149e8a-156d-4bf5-a11d-778df20fe171",  # Ivo - production (opnureyes2@gmail.com)
    "9cea0565-ce01-4d05-adf0-10897f9d2ff8",  # Rasmus - production (opnureyes2@gmail.com)
}

# ════════════════════════════════════════════════════════════════
# ACTIVITY LOGGING INFRASTRUCTURE
# ════════════════════════════════════════════════════════════════

# Global set to track SSE clients for activity log broadcasting
import asyncio
from typing import Set

activity_log_clients: Set[asyncio.Queue] = set()

logger.info("✅ Configuration module loaded")
