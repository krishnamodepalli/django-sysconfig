"""
Encryption utilities for sensitive configuration values.

Uses Fernet symmetric encryption (AES-128-CBC + HMAC) with a key
derived from Django's SECRET_KEY.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

# Minimum size of a Fernet token in bytes (version + timestamp + IV + ciphertext + HMAC)
MIN_FERNET_TOKEN_SIZE = 57


def _get_fernet() -> Fernet:
    """
    Get a Fernet instance with a key derived from Django's SECRET_KEY.

    The key is derived using SHA-256 to ensure a consistent 32-byte key
    regardless of the SECRET_KEY length.
    """
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(value: str) -> str:
    """
    Encrypt a string value.

    Args:
        value: The plaintext string to encrypt

    Returns:
        The encrypted value as a base64-encoded string
    """
    if not value:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(value.encode()).decode()


def decrypt(encrypted_value: str) -> str:
    """
    Decrypt an encrypted string value.

    Args:
        encrypted_value: The encrypted base64-encoded string

    Returns:
        The decrypted plaintext string

    Raises:
        InvalidToken: If the value cannot be decrypted (wrong key or corrupted)
    """
    if not encrypted_value:
        return ""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_value.encode()).decode()


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be a Fernet-encrypted token.

    Uses two heuristics: minimum decoded length and the Fernet version
    byte (0x80), which is always the first byte of a valid Fernet token.
    This eliminates false positives from other long base64-encoded values
    such as JWTs, hashed passwords, or long API keys.

    Args:
        value: The value to check

    Returns:
        True if the value looks like a Fernet token
    """
    if not value:
        return False
    try:
        decoded = base64.urlsafe_b64decode(value.encode())
        return len(decoded) >= MIN_FERNET_TOKEN_SIZE and decoded[0] == 0x80
    except (ValueError, TypeError, UnicodeDecodeError):
        return False


def safe_decrypt(encrypted_value: str, default: str = "") -> str:
    """
    Safely decrypt a value, returning a default if decryption fails.

    Args:
        encrypted_value: The encrypted value to decrypt
        default: The default value to return if decryption fails

    Returns:
        The decrypted value or the default
    """
    if not encrypted_value:
        return default
    try:
        return decrypt(encrypted_value)
    except InvalidToken:
        # Decryption failed (wrong key or corrupted data)
        return default
    except (ValueError, TypeError, UnicodeDecodeError):
        # Invalid format or encoding issues
        return default
