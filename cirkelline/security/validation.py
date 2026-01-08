"""
Input Validation
================
Comprehensive input validation and sanitization.

Responsibilities:
- Validate all user inputs against schemas
- Sanitize strings to prevent injection attacks
- Provide consistent validation errors
- Support custom validation rules
"""

import logging
import re
import html
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES AND ERRORS
# ═══════════════════════════════════════════════════════════════════════════════

class SanitizationLevel(Enum):
    """Levels of input sanitization."""
    NONE = "none"  # No sanitization
    BASIC = "basic"  # HTML escape only
    STRICT = "strict"  # Full sanitization
    PARANOID = "paranoid"  # Maximum sanitization


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, code: str = "validation_error"):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "field": self.field,
        }


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    value: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "sanitized": self.sanitized,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION RULES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationRule:
    """A single validation rule."""
    name: str
    validator: Callable[[Any], bool]
    message: str
    severity: str = "error"  # error, warning


# Common patterns
PATTERNS = {
    "email": re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    "uuid": re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I),
    "slug": re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$'),
    "alphanumeric": re.compile(r'^[a-zA-Z0-9]+$'),
    "phone": re.compile(r'^\+?[0-9]{8,15}$'),
    "url": re.compile(r'^https?://[^\s<>"{}|\\^`\[\]]+$'),
    "ip_v4": re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'),
    "safe_string": re.compile(r'^[a-zA-Z0-9\s\-_.,!?@#$%&*()+=:;\'"]+$'),
}

# Dangerous patterns to detect
DANGEROUS_PATTERNS = [
    re.compile(r'<script[^>]*>.*?</script>', re.I | re.S),
    re.compile(r'javascript:', re.I),
    re.compile(r'on\w+\s*=', re.I),
    re.compile(r'eval\s*\(', re.I),
    re.compile(r'expression\s*\(', re.I),
    re.compile(r'data:\s*text/html', re.I),
]

# SQL injection patterns
SQL_PATTERNS = [
    re.compile(r"('\s*OR\s*'1'\s*=\s*'1)", re.I),
    re.compile(r"(;\s*DROP\s+TABLE)", re.I),
    re.compile(r"(UNION\s+SELECT)", re.I),
    re.compile(r"(INSERT\s+INTO)", re.I),
    re.compile(r"(DELETE\s+FROM)", re.I),
    re.compile(r"(--\s*$)", re.M),
]


# ═══════════════════════════════════════════════════════════════════════════════
# SANITIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def sanitize_string(
    value: str,
    level: SanitizationLevel = SanitizationLevel.BASIC,
    max_length: Optional[int] = None,
) -> str:
    """
    Sanitize a string based on security level.

    Args:
        value: String to sanitize
        level: Sanitization level
        max_length: Optional maximum length

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)

    result = value

    if level == SanitizationLevel.NONE:
        pass

    elif level == SanitizationLevel.BASIC:
        # HTML escape
        result = html.escape(result)

    elif level == SanitizationLevel.STRICT:
        # HTML escape
        result = html.escape(result)
        # Remove null bytes
        result = result.replace('\x00', '')
        # Normalize whitespace
        result = ' '.join(result.split())

    elif level == SanitizationLevel.PARANOID:
        # HTML escape
        result = html.escape(result)
        # Remove null bytes
        result = result.replace('\x00', '')
        # Remove control characters
        result = ''.join(c for c in result if ord(c) >= 32 or c in '\n\r\t')
        # Normalize whitespace
        result = ' '.join(result.split())
        # Only allow safe characters
        result = ''.join(c for c in result if PATTERNS['safe_string'].match(c) or c.isspace())

    # Apply max length
    if max_length and len(result) > max_length:
        result = result[:max_length]

    return result


def remove_dangerous_content(value: str) -> str:
    """Remove potentially dangerous content from a string."""
    result = value

    for pattern in DANGEROUS_PATTERNS:
        result = pattern.sub('', result)

    return result


def detect_sql_injection(value: str) -> bool:
    """Check if string contains SQL injection patterns."""
    for pattern in SQL_PATTERNS:
        if pattern.search(value):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════════

class InputValidator:
    """
    Comprehensive input validation engine.

    Validates and sanitizes inputs against defined schemas
    and rules.
    """

    def __init__(self, default_level: SanitizationLevel = SanitizationLevel.BASIC):
        self._default_level = default_level
        self._custom_rules: Dict[str, ValidationRule] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}

    # ═══════════════════════════════════════════════════════════════════════════
    # SCHEMA REGISTRATION
    # ═══════════════════════════════════════════════════════════════════════════

    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """
        Register a validation schema.

        Schema format:
        {
            "field_name": {
                "type": "string|int|float|bool|list|dict|email|uuid|url",
                "required": True/False,
                "min_length": int,
                "max_length": int,
                "min_value": number,
                "max_value": number,
                "pattern": "regex",
                "choices": [...],
                "sanitize": "none|basic|strict|paranoid",
            }
        }
        """
        self._schemas[name] = schema
        logger.debug(f"Registered schema: {name}")

    def register_rule(self, name: str, rule: ValidationRule) -> None:
        """Register a custom validation rule."""
        self._custom_rules[name] = rule

    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDATION
    # ═══════════════════════════════════════════════════════════════════════════

    def validate(
        self,
        data: Dict[str, Any],
        schema_name: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate data against a schema.

        Args:
            data: Data to validate
            schema_name: Name of registered schema
            schema: Inline schema (overrides schema_name)

        Returns:
            ValidationResult
        """
        if schema is None:
            if schema_name and schema_name in self._schemas:
                schema = self._schemas[schema_name]
            else:
                return ValidationResult(valid=True, value=data)

        errors = []
        warnings = []
        sanitized_data = {}
        was_sanitized = False

        for field_name, rules in schema.items():
            value = data.get(field_name)

            # Required check
            if rules.get('required', False) and value is None:
                errors.append(f"Field '{field_name}' is required")
                continue

            if value is None:
                continue

            # Type validation
            field_type = rules.get('type', 'string')
            type_result = self._validate_type(value, field_type, field_name)
            if not type_result.valid:
                errors.extend(type_result.errors)
                continue

            # Apply sanitization
            sanitize_level = rules.get('sanitize', self._default_level.value)
            if isinstance(sanitize_level, str):
                sanitize_level = SanitizationLevel(sanitize_level)

            if isinstance(value, str) and sanitize_level != SanitizationLevel.NONE:
                original = value
                value = sanitize_string(value, sanitize_level, rules.get('max_length'))
                if value != original:
                    was_sanitized = True

            # Length validation
            if 'min_length' in rules and len(str(value)) < rules['min_length']:
                errors.append(f"Field '{field_name}' must be at least {rules['min_length']} characters")

            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                errors.append(f"Field '{field_name}' must be at most {rules['max_length']} characters")

            # Value range validation
            if 'min_value' in rules and value < rules['min_value']:
                errors.append(f"Field '{field_name}' must be at least {rules['min_value']}")

            if 'max_value' in rules and value > rules['max_value']:
                errors.append(f"Field '{field_name}' must be at most {rules['max_value']}")

            # Pattern validation
            if 'pattern' in rules:
                pattern = re.compile(rules['pattern'])
                if not pattern.match(str(value)):
                    errors.append(f"Field '{field_name}' does not match required pattern")

            # Choices validation
            if 'choices' in rules and value not in rules['choices']:
                errors.append(f"Field '{field_name}' must be one of: {rules['choices']}")

            # SQL injection check
            if isinstance(value, str) and detect_sql_injection(value):
                errors.append(f"Field '{field_name}' contains potentially dangerous content")

            sanitized_data[field_name] = value

        return ValidationResult(
            valid=len(errors) == 0,
            value=sanitized_data if len(errors) == 0 else None,
            errors=errors,
            warnings=warnings,
            sanitized=was_sanitized,
        )

    def _validate_type(
        self,
        value: Any,
        expected_type: str,
        field_name: str,
    ) -> ValidationResult:
        """Validate value type."""
        type_validators = {
            'string': lambda v: isinstance(v, str),
            'int': lambda v: isinstance(v, int) and not isinstance(v, bool),
            'float': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            'bool': lambda v: isinstance(v, bool),
            'list': lambda v: isinstance(v, list),
            'dict': lambda v: isinstance(v, dict),
            'email': lambda v: isinstance(v, str) and PATTERNS['email'].match(v),
            'uuid': lambda v: isinstance(v, str) and PATTERNS['uuid'].match(v),
            'url': lambda v: isinstance(v, str) and PATTERNS['url'].match(v),
            'slug': lambda v: isinstance(v, str) and PATTERNS['slug'].match(v),
            'phone': lambda v: isinstance(v, str) and PATTERNS['phone'].match(v),
            'ip': lambda v: isinstance(v, str) and PATTERNS['ip_v4'].match(v),
        }

        validator = type_validators.get(expected_type, lambda v: True)

        if not validator(value):
            return ValidationResult(
                valid=False,
                errors=[f"Field '{field_name}' must be of type {expected_type}"]
            )

        return ValidationResult(valid=True, value=value)

    # ═══════════════════════════════════════════════════════════════════════════
    # SINGLE VALUE VALIDATION
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_string(
        self,
        value: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        sanitize: SanitizationLevel = SanitizationLevel.BASIC,
    ) -> ValidationResult:
        """Validate and sanitize a single string."""
        errors = []

        if not isinstance(value, str):
            return ValidationResult(valid=False, errors=["Value must be a string"])

        # Sanitize
        sanitized = sanitize_string(value, sanitize, max_length)
        was_sanitized = sanitized != value

        # Length checks
        if min_length and len(sanitized) < min_length:
            errors.append(f"String must be at least {min_length} characters")

        if max_length and len(sanitized) > max_length:
            errors.append(f"String must be at most {max_length} characters")

        # Pattern check
        if pattern:
            if not re.match(pattern, sanitized):
                errors.append("String does not match required pattern")

        # SQL injection check
        if detect_sql_injection(sanitized):
            errors.append("String contains potentially dangerous content")

        return ValidationResult(
            valid=len(errors) == 0,
            value=sanitized if len(errors) == 0 else None,
            errors=errors,
            sanitized=was_sanitized,
        )

    def validate_email(self, value: str) -> ValidationResult:
        """Validate an email address."""
        if not isinstance(value, str):
            return ValidationResult(valid=False, errors=["Email must be a string"])

        value = value.strip().lower()

        if not PATTERNS['email'].match(value):
            return ValidationResult(valid=False, errors=["Invalid email format"])

        return ValidationResult(valid=True, value=value)

    def validate_uuid(self, value: str) -> ValidationResult:
        """Validate a UUID."""
        if not isinstance(value, str):
            return ValidationResult(valid=False, errors=["UUID must be a string"])

        value = value.strip().lower()

        if not PATTERNS['uuid'].match(value):
            return ValidationResult(valid=False, errors=["Invalid UUID format"])

        return ValidationResult(valid=True, value=value)

    def validate_url(self, value: str) -> ValidationResult:
        """Validate a URL."""
        if not isinstance(value, str):
            return ValidationResult(valid=False, errors=["URL must be a string"])

        value = value.strip()

        if not PATTERNS['url'].match(value):
            return ValidationResult(valid=False, errors=["Invalid URL format"])

        # Check for dangerous content
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(value):
                return ValidationResult(valid=False, errors=["URL contains dangerous content"])

        return ValidationResult(valid=True, value=value)

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get validator statistics."""
        return {
            "registered_schemas": len(self._schemas),
            "custom_rules": len(self._custom_rules),
            "default_sanitization_level": self._default_level.value,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_input(
    data: Dict[str, Any],
    schema: Dict[str, Any],
) -> ValidationResult:
    """Quick validation function."""
    validator = get_validator()
    return validator.validate(data, schema=schema)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_validator_instance: Optional[InputValidator] = None


def get_validator() -> InputValidator:
    """Get the singleton InputValidator instance."""
    global _validator_instance

    if _validator_instance is None:
        _validator_instance = InputValidator()

        # Register common schemas
        _validator_instance.register_schema("user_input", {
            "message": {
                "type": "string",
                "required": True,
                "min_length": 1,
                "max_length": 10000,
                "sanitize": "basic",
            },
            "session_id": {
                "type": "uuid",
                "required": False,
            },
            "user_id": {
                "type": "uuid",
                "required": True,
            },
        })

        _validator_instance.register_schema("agent_request", {
            "agent_id": {
                "type": "slug",
                "required": True,
                "min_length": 1,
                "max_length": 100,
            },
            "task": {
                "type": "string",
                "required": True,
                "min_length": 1,
                "max_length": 50000,
                "sanitize": "basic",
            },
            "priority": {
                "type": "int",
                "required": False,
                "min_value": 0,
                "max_value": 10,
            },
        })

    return _validator_instance
