"""
CLI Configuration
=================
Configuration management for Cirkelline Terminal CLI.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CLIConfig:
    """Configuration for CLI."""

    # API endpoints
    api_base_url: str = "http://localhost:7777"
    ws_url: str = "ws://localhost:7777/ws/terminal"

    # Authentication
    token_file: str = "~/.cirkelline/token.json"

    # Git integration
    auto_detect_git: bool = True
    include_git_diff: bool = False

    # Display settings
    color_output: bool = True
    verbose: bool = False

    # Timeouts (seconds)
    request_timeout: int = 30
    ws_ping_interval: int = 15

    # Logging
    log_file: str = "~/.cirkelline/cli.log"
    log_level: str = "INFO"


def get_config_dir() -> Path:
    """Get Cirkelline config directory."""
    config_dir = Path.home() / ".cirkelline"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_config() -> CLIConfig:
    """Load CLI configuration from file or defaults."""
    config_file = get_config_dir() / "config.json"

    if config_file.exists():
        try:
            with open(config_file) as f:
                data = json.load(f)
            return CLIConfig(**data)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")

    return CLIConfig()


def save_config(config: CLIConfig) -> None:
    """Save CLI configuration to file."""
    config_file = get_config_dir() / "config.json"

    with open(config_file, "w") as f:
        json.dump(asdict(config), f, indent=2)


def get_token_path() -> Path:
    """Get path to token file."""
    return Path(os.path.expanduser(load_config().token_file))


def get_log_path() -> Path:
    """Get path to log file."""
    return Path(os.path.expanduser(load_config().log_file))
