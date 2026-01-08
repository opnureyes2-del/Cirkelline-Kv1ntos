"""
CKC AWS Integration Module
===========================

AWS service integration for CKC MASTERMIND.
Inkluderer LocalStack konfiguration til lokal test og development.

Note: boto3 er en optional dependency. Modulet kan importeres uden boto3,
men AWS-funktionalitet kræver at boto3 er installeret.

Usage:
    from cirkelline.ckc.aws import (
        get_localstack_client,
        get_localstack_resource,
        is_localstack_available,
        setup_test_infrastructure,
    )

    # Check om boto3 er tilgængelig
    from cirkelline.ckc.aws import BOTO3_AVAILABLE
    if BOTO3_AVAILABLE:
        s3 = get_localstack_client('s3')
"""

from .localstack_config import (
    # Configuration
    LOCALSTACK_ENDPOINT,
    AWS_REGION,
    BOTO3_AVAILABLE,

    # Client factories
    get_localstack_client,
    get_localstack_resource,

    # Health checks
    is_localstack_available,
    get_localstack_health,
    check_service_available,

    # Helper classes
    LocalStackS3,
    LocalStackSQS,
    LocalStackDynamoDB,

    # Setup/Teardown
    setup_test_infrastructure,
    teardown_test_infrastructure,
)

__all__ = [
    # Configuration
    'LOCALSTACK_ENDPOINT',
    'AWS_REGION',
    'BOTO3_AVAILABLE',

    # Client factories
    'get_localstack_client',
    'get_localstack_resource',

    # Health checks
    'is_localstack_available',
    'get_localstack_health',
    'check_service_available',

    # Helper classes
    'LocalStackS3',
    'LocalStackSQS',
    'LocalStackDynamoDB',

    # Setup/Teardown
    'setup_test_infrastructure',
    'teardown_test_infrastructure',
]
