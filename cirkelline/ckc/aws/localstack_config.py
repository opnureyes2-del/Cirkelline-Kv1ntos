"""
CKC AWS LocalStack Configuration
=================================

Helper modul til at arbejde med LocalStack under lokal udvikling og test.
Dette sikrer at CKC kan testes mod simulerede AWS services før deployment.

Usage:
    from cirkelline.ckc.aws.localstack_config import (
        get_localstack_client,
        get_localstack_resource,
        is_localstack_available,
    )

    # Check om LocalStack kører
    if is_localstack_available():
        s3 = get_localstack_client('s3')
        buckets = s3.list_buckets()
"""

import os
from typing import Optional, Any

# Conditional boto3 import - kun nødvendig når AWS services bruges
try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError, EndpointConnectionError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    Config = None
    ClientError = Exception
    EndpointConnectionError = Exception


# =============================================================================
# CONFIGURATION
# =============================================================================

LOCALSTACK_ENDPOINT = os.environ.get(
    "LOCALSTACK_ENDPOINT",
    "http://localhost:4566"
)

AWS_REGION = os.environ.get("AWS_REGION", "eu-north-1")

# Test credentials for LocalStack
LOCALSTACK_ACCESS_KEY = "test"
LOCALSTACK_SECRET_KEY = "test"

# Retry configuration (kun hvis boto3 er tilgængelig)
RETRY_CONFIG = None
if BOTO3_AVAILABLE and Config:
    RETRY_CONFIG = Config(
        signature_version='v4',
        retries={
            'max_attempts': 3,
            'mode': 'standard'
        },
        connect_timeout=5,
        read_timeout=30
    )


# =============================================================================
# CLIENT FACTORIES
# =============================================================================

def get_localstack_client(
    service_name: str,
    endpoint_url: Optional[str] = None,
    region_name: Optional[str] = None
) -> Any:
    """
    Opret en boto3 client der peger på LocalStack.

    Args:
        service_name: AWS service navn (s3, sqs, dynamodb, etc.)
        endpoint_url: Custom endpoint URL (default: LOCALSTACK_ENDPOINT)
        region_name: AWS region (default: eu-north-1)

    Returns:
        boto3 client konfigureret til LocalStack

    Raises:
        ImportError: Hvis boto3 ikke er installeret

    Example:
        s3 = get_localstack_client('s3')
        s3.list_buckets()
    """
    if not BOTO3_AVAILABLE:
        raise ImportError("boto3 er ikke installeret. Kør: pip install boto3")

    return boto3.client(
        service_name,
        endpoint_url=endpoint_url or LOCALSTACK_ENDPOINT,
        region_name=region_name or AWS_REGION,
        aws_access_key_id=LOCALSTACK_ACCESS_KEY,
        aws_secret_access_key=LOCALSTACK_SECRET_KEY,
        config=RETRY_CONFIG
    )


def get_localstack_resource(
    service_name: str,
    endpoint_url: Optional[str] = None,
    region_name: Optional[str] = None
) -> Any:
    """
    Opret en boto3 resource der peger på LocalStack.

    Args:
        service_name: AWS service navn (s3, dynamodb, etc.)
        endpoint_url: Custom endpoint URL (default: LOCALSTACK_ENDPOINT)
        region_name: AWS region (default: eu-north-1)

    Returns:
        boto3 resource konfigureret til LocalStack

    Raises:
        ImportError: Hvis boto3 ikke er installeret

    Example:
        s3 = get_localstack_resource('s3')
        bucket = s3.Bucket('my-bucket')
    """
    if not BOTO3_AVAILABLE:
        raise ImportError("boto3 er ikke installeret. Kør: pip install boto3")

    return boto3.resource(
        service_name,
        endpoint_url=endpoint_url or LOCALSTACK_ENDPOINT,
        region_name=region_name or AWS_REGION,
        aws_access_key_id=LOCALSTACK_ACCESS_KEY,
        aws_secret_access_key=LOCALSTACK_SECRET_KEY
    )


# =============================================================================
# HEALTH CHECKS
# =============================================================================

def is_localstack_available() -> bool:
    """
    Check om LocalStack er tilgængelig og kører.

    Returns:
        True hvis LocalStack svarer, False ellers
    """
    try:
        import urllib.request
        import urllib.error

        url = f"{LOCALSTACK_ENDPOINT}/_localstack/health"
        request = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, ConnectionRefusedError):
        return False
    except Exception:
        return False


def get_localstack_health() -> dict:
    """
    Hent detaljeret health status fra LocalStack.

    Returns:
        Dict med service status, eller tom dict hvis ikke tilgængelig
    """
    try:
        import urllib.request
        import json

        url = f"{LOCALSTACK_ENDPOINT}/_localstack/health"
        request = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        return {}


def check_service_available(service_name: str) -> bool:
    """
    Check om en specifik AWS service er tilgængelig i LocalStack.

    Args:
        service_name: Service navn (s3, sqs, dynamodb, etc.)

    Returns:
        True hvis servicen er tilgængelig og kører
    """
    health = get_localstack_health()
    services = health.get('services', {})
    return services.get(service_name, '') in ('running', 'available')


# =============================================================================
# SERVICE HELPERS
# =============================================================================

class LocalStackS3:
    """Helper klasse for S3 operationer med LocalStack."""

    def __init__(self):
        self.client = get_localstack_client('s3')
        self.resource = get_localstack_resource('s3')

    def create_bucket(self, bucket_name: str) -> bool:
        """Opret en S3 bucket."""
        try:
            self.client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': AWS_REGION
                }
            )
            return True
        except (ClientError, Exception):
            return False

    def list_buckets(self) -> list:
        """List alle buckets."""
        response = self.client.list_buckets()
        return [b['Name'] for b in response.get('Buckets', [])]

    def upload_file(self, bucket: str, key: str, data: bytes) -> bool:
        """Upload data til S3."""
        try:
            self.client.put_object(Bucket=bucket, Key=key, Body=data)
            return True
        except ClientError:
            return False


class LocalStackSQS:
    """Helper klasse for SQS operationer med LocalStack."""

    def __init__(self):
        self.client = get_localstack_client('sqs')

    def create_queue(self, queue_name: str) -> Optional[str]:
        """Opret en SQS queue. Returnerer queue URL."""
        try:
            response = self.client.create_queue(QueueName=queue_name)
            return response.get('QueueUrl')
        except (ClientError, Exception):
            return None

    def list_queues(self) -> list:
        """List alle queues."""
        response = self.client.list_queues()
        return response.get('QueueUrls', [])

    def send_message(self, queue_url: str, message: str) -> bool:
        """Send besked til queue."""
        try:
            self.client.send_message(QueueUrl=queue_url, MessageBody=message)
            return True
        except ClientError:
            return False


class LocalStackDynamoDB:
    """Helper klasse for DynamoDB operationer med LocalStack."""

    def __init__(self):
        self.client = get_localstack_client('dynamodb')
        self.resource = get_localstack_resource('dynamodb')

    def create_table(
        self,
        table_name: str,
        key_schema: list,
        attribute_definitions: list,
        billing_mode: str = 'PAY_PER_REQUEST'
    ) -> bool:
        """Opret en DynamoDB tabel."""
        try:
            self.client.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                BillingMode=billing_mode
            )
            return True
        except (ClientError, Exception):
            return False

    def list_tables(self) -> list:
        """List alle tabeller."""
        response = self.client.list_tables()
        return response.get('TableNames', [])


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def setup_test_infrastructure():
    """
    Opsæt standard test infrastruktur i LocalStack.

    Opretter:
    - S3 bucket: cirkelline-test-assets
    - SQS queue: cirkelline-test-queue
    - DynamoDB table: CirkellineTestSessions
    """
    if not is_localstack_available():
        print("❌ LocalStack er ikke tilgængelig!")
        print("   Start med: docker-compose -f docker-compose.localstack.yml up -d")
        return False

    print("🚀 Opsætter CKC test infrastruktur i LocalStack...")

    # S3
    s3 = LocalStackS3()
    if s3.create_bucket('cirkelline-test-assets'):
        print("  ✅ S3 bucket: cirkelline-test-assets")
    else:
        print("  ⚠️  S3 bucket eksisterer allerede")

    # SQS
    sqs = LocalStackSQS()
    queue_url = sqs.create_queue('cirkelline-test-queue')
    if queue_url:
        print(f"  ✅ SQS queue: {queue_url}")
    else:
        print("  ⚠️  SQS queue eksisterer allerede")

    # DynamoDB
    dynamo = LocalStackDynamoDB()
    if dynamo.create_table(
        table_name='CirkellineTestSessions',
        key_schema=[{'AttributeName': 'session_id', 'KeyType': 'HASH'}],
        attribute_definitions=[{'AttributeName': 'session_id', 'AttributeType': 'S'}]
    ):
        print("  ✅ DynamoDB table: CirkellineTestSessions")
    else:
        print("  ⚠️  DynamoDB table eksisterer allerede")

    print("\n✅ CKC test infrastruktur klar!")
    return True


def teardown_test_infrastructure():
    """Ryd op i test infrastruktur."""
    if not is_localstack_available():
        return False

    print("🧹 Rydder op i CKC test infrastruktur...")

    # S3
    s3 = get_localstack_client('s3')
    try:
        # Slet objekter først
        objects = s3.list_objects_v2(Bucket='cirkelline-test-assets')
        for obj in objects.get('Contents', []):
            s3.delete_object(Bucket='cirkelline-test-assets', Key=obj['Key'])
        s3.delete_bucket(Bucket='cirkelline-test-assets')
        print("  ✅ S3 bucket slettet")
    except ClientError:
        pass

    # SQS
    sqs = get_localstack_client('sqs')
    try:
        queues = sqs.list_queues(QueueNamePrefix='cirkelline-test')
        for queue_url in queues.get('QueueUrls', []):
            sqs.delete_queue(QueueUrl=queue_url)
        print("  ✅ SQS queues slettet")
    except ClientError:
        pass

    # DynamoDB
    dynamo = get_localstack_client('dynamodb')
    try:
        dynamo.delete_table(TableName='CirkellineTestSessions')
        print("  ✅ DynamoDB table slettet")
    except ClientError:
        pass

    print("\n✅ Oprydning komplet!")
    return True


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("CKC LocalStack Configuration Test")
    print("=" * 60)

    # Check availability
    print("\n📡 Checker LocalStack forbindelse...")
    if is_localstack_available():
        print("✅ LocalStack er tilgængelig!")

        # Get health
        health = get_localstack_health()
        print(f"\n📊 LocalStack Health:")
        for service, status in health.get('services', {}).items():
            emoji = "✅" if status in ('running', 'available') else "❌"
            print(f"   {emoji} {service}: {status}")

        # Test services
        print("\n🧪 Tester AWS services...")

        # S3
        s3 = get_localstack_client('s3')
        buckets = s3.list_buckets()
        print(f"   S3 Buckets: {[b['Name'] for b in buckets['Buckets']]}")

        # SQS
        sqs = get_localstack_client('sqs')
        queues = sqs.list_queues()
        print(f"   SQS Queues: {queues.get('QueueUrls', [])}")

        # DynamoDB
        dynamodb = get_localstack_client('dynamodb')
        tables = dynamodb.list_tables()
        print(f"   DynamoDB Tables: {tables['TableNames']}")

        print("\n✅ Alle services fungerer!")

        # Setup test infrastructure if requested
        if len(sys.argv) > 1 and sys.argv[1] == '--setup':
            print("\n" + "=" * 60)
            setup_test_infrastructure()

        if len(sys.argv) > 1 and sys.argv[1] == '--teardown':
            print("\n" + "=" * 60)
            teardown_test_infrastructure()

    else:
        print("❌ LocalStack er IKKE tilgængelig!")
        print("\nStart LocalStack med:")
        print("  docker-compose -f docker-compose.localstack.yml up -d")
        sys.exit(1)
