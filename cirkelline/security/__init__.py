"""
Security Module
===============
Security hardening components for the Cirkelline system.

Components:
- Input Validation: Sanitize and validate all inputs
- Rate Limiter: Protect against abuse and DoS
- Audit Logger: Comprehensive audit trail
"""

__version__ = "1.0.0"

from cirkelline.security.validation import (
    InputValidator,
    ValidationResult,
    ValidationError,
    SanitizationLevel,
    validate_input,
    sanitize_string,
    get_validator,
)

from cirkelline.security.rate_limiter import (
    RateLimiter,
    RateLimitResult,
    RateLimitStrategy,
    RateLimitConfig,
    get_rate_limiter,
)

from cirkelline.security.audit import (
    AuditLogger,
    AuditEvent,
    AuditLevel,
    AuditCategory,
    get_audit_logger,
)

__all__ = [
    # Validation
    'InputValidator',
    'ValidationResult',
    'ValidationError',
    'SanitizationLevel',
    'validate_input',
    'sanitize_string',
    'get_validator',
    # Rate Limiter
    'RateLimiter',
    'RateLimitResult',
    'RateLimitStrategy',
    'RateLimitConfig',
    'get_rate_limiter',
    # Audit
    'AuditLogger',
    'AuditEvent',
    'AuditLevel',
    'AuditCategory',
    'get_audit_logger',
]
