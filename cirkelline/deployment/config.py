"""
Configuration Manager
=====================
Environment and configuration management.

Responsibilities:
- Load configuration from multiple sources
- Support environment-specific configs
- Validate configuration values
- Provide typed access to config
"""

import logging
import os
import json
from typing import Optional, Dict, Any, List, Union, TypeVar, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class ConfigSource(Enum):
    """Configuration sources."""
    DEFAULT = "default"
    FILE = "file"
    ENVIRONMENT = "environment"
    OVERRIDE = "override"


@dataclass
class ConfigValue:
    """A configuration value with metadata."""
    key: str
    value: Any
    source: ConfigSource
    default: Any = None
    required: bool = False
    sensitive: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": "[REDACTED]" if self.sensitive else self.value,
            "source": self.source.value,
            "has_default": self.default is not None,
            "required": self.required,
            "sensitive": self.sensitive,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION SCHEMA
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG_SCHEMA = {
    # System
    "CIRKELLINE_ENV": {
        "default": "development",
        "required": False,
        "sensitive": False,
        "description": "Deployment environment",
    },
    "CIRKELLINE_DEBUG": {
        "default": "false",
        "required": False,
        "sensitive": False,
        "description": "Debug mode",
    },
    "CIRKELLINE_LOG_LEVEL": {
        "default": "INFO",
        "required": False,
        "sensitive": False,
        "description": "Logging level",
    },

    # Server
    "CIRKELLINE_HOST": {
        "default": "0.0.0.0",
        "required": False,
        "sensitive": False,
        "description": "Server host",
    },
    "CIRKELLINE_PORT": {
        "default": "8000",
        "required": False,
        "sensitive": False,
        "description": "Server port",
    },

    # Database
    "CIRKELLINE_DATABASE_URL": {
        "default": None,
        "required": False,
        "sensitive": True,
        "description": "Database connection URL",
    },
    "CIRKELLINE_REDIS_URL": {
        "default": "redis://localhost:6379",
        "required": False,
        "sensitive": True,
        "description": "Redis connection URL",
    },

    # Security
    "CIRKELLINE_SECRET_KEY": {
        "default": None,
        "required": True,
        "sensitive": True,
        "description": "Secret key for encryption",
    },
    "CIRKELLINE_JWT_SECRET": {
        "default": None,
        "required": False,
        "sensitive": True,
        "description": "JWT signing secret",
    },

    # AI
    "CIRKELLINE_AI_MODEL": {
        "default": "gemini-2.5-flash",
        "required": False,
        "sensitive": False,
        "description": "Default AI model",
    },
    "CIRKELLINE_AI_API_KEY": {
        "default": None,
        "required": False,
        "sensitive": True,
        "description": "AI API key",
    },

    # Performance
    "CIRKELLINE_CACHE_TTL": {
        "default": "300",
        "required": False,
        "sensitive": False,
        "description": "Default cache TTL in seconds",
    },
    "CIRKELLINE_MAX_CONNECTIONS": {
        "default": "100",
        "required": False,
        "sensitive": False,
        "description": "Maximum connections",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """
    Centralized configuration management.

    Loads configuration from multiple sources with priority:
    1. Overrides (highest)
    2. Environment variables
    3. Config files
    4. Defaults (lowest)
    """

    def __init__(self, env: Optional[Environment] = None):
        self._env = env or self._detect_environment()
        self._values: Dict[str, ConfigValue] = {}
        self._overrides: Dict[str, Any] = {}
        self._loaded = False

    def _detect_environment(self) -> Environment:
        """Detect environment from env var."""
        env_str = os.getenv("CIRKELLINE_ENV", "development").lower()
        try:
            return Environment(env_str)
        except ValueError:
            return Environment.DEVELOPMENT

    # ═══════════════════════════════════════════════════════════════════════════
    # LOADING
    # ═══════════════════════════════════════════════════════════════════════════

    def load(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from all sources.

        Args:
            config_path: Optional path to config file
        """
        self._values.clear()

        # Load defaults
        for key, schema in CONFIG_SCHEMA.items():
            self._values[key] = ConfigValue(
                key=key,
                value=schema["default"],
                source=ConfigSource.DEFAULT,
                default=schema["default"],
                required=schema["required"],
                sensitive=schema["sensitive"],
                description=schema["description"],
            )

        # Load from file
        if config_path:
            self._load_file(config_path)
        else:
            # Try standard paths
            for path in self._get_config_paths():
                if Path(path).exists():
                    self._load_file(path)
                    break

        # Load from environment
        self._load_environment()

        # Apply overrides
        self._apply_overrides()

        # Validate required
        self._validate()

        self._loaded = True
        logger.info(f"Configuration loaded for environment: {self._env.value}")

    def _get_config_paths(self) -> List[str]:
        """Get standard config file paths."""
        paths = [
            f".cirkelline.{self._env.value}.json",
            ".cirkelline.json",
            f"/etc/cirkelline/config.{self._env.value}.json",
            "/etc/cirkelline/config.json",
        ]
        return paths

    def _load_file(self, path: str) -> None:
        """Load configuration from file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)

            for key, value in data.items():
                if key in self._values:
                    self._values[key].value = value
                    self._values[key].source = ConfigSource.FILE
                else:
                    self._values[key] = ConfigValue(
                        key=key,
                        value=value,
                        source=ConfigSource.FILE,
                    )

            logger.debug(f"Loaded config from: {path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {path}: {e}")

    def _load_environment(self) -> None:
        """Load configuration from environment variables."""
        for key in self._values:
            env_value = os.getenv(key)
            if env_value is not None:
                self._values[key].value = env_value
                self._values[key].source = ConfigSource.ENVIRONMENT

    def _apply_overrides(self) -> None:
        """Apply manual overrides."""
        for key, value in self._overrides.items():
            if key in self._values:
                self._values[key].value = value
                self._values[key].source = ConfigSource.OVERRIDE

    def _validate(self) -> None:
        """Validate required configuration."""
        missing = []
        for key, config in self._values.items():
            if config.required and config.value is None:
                missing.append(key)

        if missing:
            # Only warn in development, error in production
            if self._env == Environment.PRODUCTION:
                raise ValueError(f"Missing required configuration: {missing}")
            else:
                logger.warning(f"Missing configuration (non-production): {missing}")

    # ═══════════════════════════════════════════════════════════════════════════
    # ACCESS
    # ═══════════════════════════════════════════════════════════════════════════

    def get(
        self,
        key: str,
        default: Any = None,
        type_cast: Optional[Type[T]] = None,
    ) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default if not found
            type_cast: Optional type to cast to

        Returns:
            Configuration value
        """
        if not self._loaded:
            self.load()

        config = self._values.get(key)
        if config is None:
            return default

        value = config.value
        if value is None:
            value = config.default if config.default is not None else default

        if type_cast and value is not None:
            try:
                if type_cast == bool:
                    value = str(value).lower() in ('true', '1', 'yes')
                elif type_cast == int:
                    value = int(value)
                elif type_cast == float:
                    value = float(value)
                elif type_cast == str:
                    value = str(value)
                elif type_cast == list:
                    if isinstance(value, str):
                        value = value.split(',')
                    else:
                        value = list(value)
            except (ValueError, TypeError):
                pass

        return value

    def get_str(self, key: str, default: str = "") -> str:
        """Get string value."""
        return self.get(key, default, str)

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer value."""
        return self.get(key, default, int)

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float value."""
        return self.get(key, default, float)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value."""
        return self.get(key, default, bool)

    def get_list(self, key: str, default: Optional[List] = None) -> List:
        """Get list value."""
        return self.get(key, default or [], list)

    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access."""
        return self.get(key)

    # ═══════════════════════════════════════════════════════════════════════════
    # MODIFICATION
    # ═══════════════════════════════════════════════════════════════════════════

    def set(self, key: str, value: Any) -> None:
        """Set an override value."""
        self._overrides[key] = value
        if key in self._values:
            self._values[key].value = value
            self._values[key].source = ConfigSource.OVERRIDE

    def override(self, **kwargs) -> None:
        """Set multiple override values."""
        for key, value in kwargs.items():
            self.set(key, value)

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def environment(self) -> Environment:
        """Get current environment."""
        return self._env

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self._env == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self._env == Environment.DEVELOPMENT

    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get_bool("CIRKELLINE_DEBUG", False)

    def get_all(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Get all configuration values."""
        if not self._loaded:
            self.load()

        result = {}
        for key, config in self._values.items():
            if config.sensitive and not include_sensitive:
                result[key] = "[REDACTED]"
            else:
                result[key] = config.value

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get configuration statistics."""
        if not self._loaded:
            self.load()

        sources = {}
        for config in self._values.values():
            source = config.source.value
            sources[source] = sources.get(source, 0) + 1

        return {
            "environment": self._env.value,
            "total_keys": len(self._values),
            "sources": sources,
            "overrides_count": len(self._overrides),
            "loaded": self._loaded,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_config_instance: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the singleton ConfigManager instance."""
    global _config_instance

    if _config_instance is None:
        _config_instance = ConfigManager()
        _config_instance.load()

    return _config_instance


def get_config(key: str, default: Any = None) -> Any:
    """Quick access to configuration value."""
    return get_config_manager().get(key, default)
