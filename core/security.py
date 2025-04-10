"""Shared security utilities (hashing, encryption)."""

import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext

# Note: Assuming core.config.settings is already initialized and imported
# If not, adjust the import accordingly.
# from core.config import settings # <-- Make sure settings is accessible
# For now, let's fetch it directly if needed, but ideally it should be passed or globally available
try:
    from core.config import settings
except ImportError:
    # Fallback or raise error if config is essential at import time
    logging.warning("core.config.settings not found during security module import.")
    settings = None # Or load a default mock

logger = logging.getLogger(__name__)

# --- Password Hashing (using passlib) ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate a hash for a password."""
    return pwd_context.hash(password)


# --- Symmetric Encryption (using cryptography.fernet) ---
_fernet_instance: Optional[Fernet] = None

def _get_fernet() -> Optional[Fernet]:
    """Initializes and returns the Fernet instance using settings."""
    global _fernet_instance
    if _fernet_instance:
        return _fernet_instance

    if not settings or not settings.SECRET_KEY:
        logger.error("SECRET_KEY not found in settings. Cannot initialize encryption.")
        return None

    secret_key_bytes = settings.SECRET_KEY.encode()
    # Ensure key is 32 bytes for Fernet by deriving it
    # Use a salt based on environment or a fixed salt stored securely
    # Using ENVIRONMENT as salt is simple but might change if env changes
    salt = (settings.ENVIRONMENT or "default_salt").encode()[:16].ljust(16, b'0')

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000, # Adjust iterations as needed
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(secret_key_bytes))

    try:
        _fernet_instance = Fernet(derived_key)
        logger.info("Fernet encryption initialized successfully.")
        return _fernet_instance
    except Exception as e:
        logger.error(f"Failed to initialize Fernet encryption: {e}")
        return None


def encrypt_data(data: bytes) -> Optional[bytes]:
    """Encrypts bytes using Fernet."""
    fernet = _get_fernet()
    if not fernet or not data:
        return None
    try:
        return fernet.encrypt(data)
    except Exception as e:
        logger.error(f"Error encrypting data: {e}")
        return None # Or raise custom exception

def decrypt_data(encrypted_data: bytes) -> Optional[bytes]:
    """Decrypts bytes using Fernet."""
    fernet = _get_fernet()
    if not fernet or not encrypted_data:
        return None
    try:
        return fernet.decrypt(encrypted_data)
    except InvalidToken:
        logger.error("Invalid token or key for decryption.")
        return None
    except Exception as e:
        logger.error(f"Error decrypting data: {e}")
        return None # Or raise custom exception


def encrypt_text(text: str) -> Optional[str]:
    """Encrypts a text string and returns base64 encoded string."""
    encrypted_bytes = encrypt_data(text.encode())
    return base64.urlsafe_b64encode(encrypted_bytes).decode() if encrypted_bytes else None

def decrypt_text(encrypted_text_b64: str) -> Optional[str]:
    """Decrypts a base64 encoded encrypted string."""
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_text_b64.encode())
        decrypted_bytes = decrypt_data(encrypted_bytes)
        return decrypted_bytes.decode() if decrypted_bytes else None
    except Exception as e:
        logger.error(f"Error base64 decoding or decrypting text: {e}")
        return None
