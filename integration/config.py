"""
Project-specific integration configuration
"""

from pathlib import Path

# Project info
PROJECT_NAME = "cirkelline-kv1ntos"
PROJECT_ROOT = Path("/home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos")

# Database connections
DATABASES = {
    'intro_kb': {
        'host': 'localhost',
        'port': 5536,
        'user': 'intro_agent',
        'password': 'intro_secure_2025',
        'database': 'intro_knowledge'
    },
    'elle_kb': {
        'host': 'localhost',
        'port': 5537,
        'user': 'elle_agent',
        'password': 'elle_secure_2025',
        'database': 'elle_knowledge'
    },
    'agent_logs': {
        'host': 'localhost',
        'port': 5432,
        'user': 'agent_user',
        'password': 'agent_secure_2025',
        'database': 'agents'
    }
}

# Event Bus
RABBITMQ = {
    'host': 'localhost',
    'port': 5672,
    'username': 'elle',
    'password': 'elle_secure_2025'
}

# Cache
REDIS = {
    'host': 'localhost',
    'port': 6379
}

# File watching paths
WATCH_PATHS = [
    '/home/rasmus/Desktop/projekts/status opdaterings rapport/INTRO',
    '/home/rasmus/Desktop/ELLE.md'
]
