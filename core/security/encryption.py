"""
Encryption Utilities

This module provides encryption utilities for the application.
"""

import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Fernet key for symmetric encryption
FERNET_KEY = settings.SECRET_KEY.encode()[:32]
if len(FERNET_KEY) < 32:
    # Pad the key if it's shorter than 32 bytes
    FERNET_KEY = FERNET_KEY.ljust(32, b'0')

# Use key derivation to get a proper Fernet key
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=settings.ENVIRONMENT.encode()[:16].ljust(16, b'0'),
    iterations=100000,
)
derived_key = base64.urlsafe_b64encode(kdf.derive(FERNET_KEY))
fernet = Fernet(derived_key)


def encrypt_text(text: str) -> str:
    """Encrypt a text string.
    
    Args:
        text: Text to encrypt
        
    Returns:
        str: Encrypted text
    """
    if not text:
        return ""
    try:
        encrypted = fernet.encrypt(text.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting text: {str(e)}")
        return text  # Fall back to plaintext if encryption fails


def decrypt_text(encrypted_text: str) -> str:
    """Decrypt an encrypted text string.
    
    Args:
        encrypted_text: Encrypted text
        
    Returns:
        str: Decrypted text
    """
    if not encrypted_text:
        return ""
    try:
        decrypted = fernet.decrypt(encrypted_text.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting text: {str(e)}")
        return encrypted_text  # Return the encrypted text if decryption fails 