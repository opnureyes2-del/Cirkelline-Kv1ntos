"""
Google OAuth Token Encryption Utilities

This module provides AES-256-GCM encryption for securely storing Google OAuth tokens
in the database. Uses the cryptography library for FIPS-compliant encryption.

Security Features:
- AES-256-GCM (Galois/Counter Mode) - Authenticated encryption
- Unique nonce (96-bit) for each encryption operation
- Authentication tag to detect tampering
- Base64 encoding for database storage

Environment Variables Required:
- GOOGLE_TOKEN_ENCRYPTION_KEY: 64-character hex string (32 bytes when decoded)

Created: 2025-10-24
Part of: Google Integration - Phase 1 (Backend OAuth Infrastructure)
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


def get_encryption_key() -> bytes:
    """
    Retrieve and validate the encryption key from environment variables.

    Returns:
        bytes: 32-byte encryption key for AES-256

    Raises:
        ValueError: If GOOGLE_TOKEN_ENCRYPTION_KEY is missing or invalid
    """
    key_hex = os.getenv("GOOGLE_TOKEN_ENCRYPTION_KEY")

    if not key_hex:
        raise ValueError(
            "GOOGLE_TOKEN_ENCRYPTION_KEY not found in environment variables. "
            "Generate one with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
        )

    try:
        key_bytes = bytes.fromhex(key_hex)
    except ValueError:
        raise ValueError(
            "GOOGLE_TOKEN_ENCRYPTION_KEY must be a valid 64-character hexadecimal string"
        )

    if len(key_bytes) != 32:
        raise ValueError(
            f"GOOGLE_TOKEN_ENCRYPTION_KEY must be 32 bytes (64 hex chars), got {len(key_bytes)} bytes"
        )

    return key_bytes


def encrypt_token(plaintext: str) -> str:
    """
    Encrypt a token using AES-256-GCM.

    Process:
    1. Generate random 96-bit nonce
    2. Encrypt plaintext with AES-256-GCM
    3. Combine nonce + ciphertext (includes auth tag)
    4. Base64 encode for database storage

    Args:
        plaintext: The token to encrypt (access_token or refresh_token)

    Returns:
        str: Base64-encoded string containing nonce + encrypted data

    Example:
        >>> encrypted = encrypt_token("ya29.a0AfH6SMB...")
        >>> print(encrypted)
        'aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890+/='
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty token")

    # Get encryption key
    key = get_encryption_key()

    # Initialize AES-GCM cipher
    aesgcm = AESGCM(key)

    # Generate random nonce (96 bits = 12 bytes)
    nonce = os.urandom(12)

    # Encrypt the token (GCM automatically adds authentication tag)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

    # Combine nonce + ciphertext for storage
    encrypted_data = nonce + ciphertext

    # Base64 encode for database storage
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_token(encrypted_b64: str) -> str:
    """
    Decrypt a token encrypted with AES-256-GCM.

    Process:
    1. Base64 decode the stored value
    2. Extract nonce (first 12 bytes)
    3. Extract ciphertext (remaining bytes)
    4. Decrypt and verify authentication tag

    Args:
        encrypted_b64: Base64-encoded string from database

    Returns:
        str: Decrypted plaintext token

    Raises:
        cryptography.exceptions.InvalidTag: If token has been tampered with
        ValueError: If encrypted data is invalid format

    Example:
        >>> token = decrypt_token('aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890+/=')
        >>> print(token)
        'ya29.a0AfH6SMB...'
    """
    if not encrypted_b64:
        raise ValueError("Cannot decrypt empty string")

    # Get encryption key
    key = get_encryption_key()

    # Initialize AES-GCM cipher
    aesgcm = AESGCM(key)

    try:
        # Base64 decode
        encrypted_data = base64.b64decode(encrypted_b64)
    except Exception as e:
        raise ValueError(f"Invalid base64 encoding: {e}")

    if len(encrypted_data) < 12:
        raise ValueError("Encrypted data too short - must contain nonce (12 bytes minimum)")

    # Extract nonce and ciphertext
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]

    try:
        # Decrypt and verify authentication tag
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as e:
        raise ValueError(f"Decryption failed - token may be corrupted or tampered: {e}")

    return plaintext_bytes.decode('utf-8')


def test_encryption():
    """
    Test encryption and decryption functionality.

    This function is useful for verifying the encryption setup works correctly
    before using it with real tokens.

    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        # Test data
        test_token = "ya29.a0AfH6SMBxL9vF4kMc7wZq2hJpR3nK8tYuI1oP6sA"

        print("Testing encryption utilities...")
        print(f"Original token: {test_token}")

        # Encrypt
        encrypted = encrypt_token(test_token)
        print(f"Encrypted (base64): {encrypted[:50]}...")

        # Decrypt
        decrypted = decrypt_token(encrypted)
        print(f"Decrypted token: {decrypted}")

        # Verify match
        if test_token == decrypted:
            print("✅ Encryption test PASSED")
            return True
        else:
            print("❌ Encryption test FAILED - tokens don't match")
            return False

    except Exception as e:
        print(f"❌ Encryption test FAILED with error: {e}")
        return False


if __name__ == "__main__":
    """
    Run encryption tests when module is executed directly.

    Usage:
        python utils/encryption.py
    """
    print("=" * 70)
    print("GOOGLE TOKEN ENCRYPTION - TEST MODE")
    print("=" * 70)
    print()

    # Check for encryption key
    if not os.getenv("GOOGLE_TOKEN_ENCRYPTION_KEY"):
        print("❌ ERROR: GOOGLE_TOKEN_ENCRYPTION_KEY not found in environment")
        print()
        print("To generate a key:")
        print('  python3 -c "import secrets; print(secrets.token_hex(32))"')
        print()
        print("Then add to .env file:")
        print("  GOOGLE_TOKEN_ENCRYPTION_KEY=<generated-key>")
        exit(1)

    # Run tests
    success = test_encryption()
    print()
    print("=" * 70)

    exit(0 if success else 1)
