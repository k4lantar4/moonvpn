"""
Encryption service for handling sensitive data encryption and decryption.
"""
from typing import Optional, Dict, Any
from datetime import datetime
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.exceptions import SecurityError

class EncryptionService:
    def __init__(self, db: Session):
        self.db = db
        self.key = self._generate_key()
        self.cipher_suite = Fernet(self.key)

    def _generate_key(self) -> bytes:
        """Generate encryption key using PBKDF2."""
        try:
            # Use the encryption key from settings as salt
            salt = settings.ENCRYPTION_KEY.encode()
            
            # Generate key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(salt))
            
            return key

        except Exception as e:
            raise SecurityError(f"Failed to generate encryption key: {str(e)}")

    async def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            # Convert string to bytes
            data_bytes = data.encode()
            
            # Encrypt data
            encrypted_data = self.cipher_suite.encrypt(data_bytes)
            
            # Convert to base64 for storage
            return base64.urlsafe_b64encode(encrypted_data).decode()

        except Exception as e:
            raise SecurityError(f"Failed to encrypt data: {str(e)}")

    async def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            # Convert base64 to bytes
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt data
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            
            # Convert back to string
            return decrypted_data.decode()

        except Exception as e:
            raise SecurityError(f"Failed to decrypt data: {str(e)}")

    async def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a dictionary."""
        try:
            encrypted_dict = {}
            
            for key, value in data.items():
                if isinstance(value, str):
                    # Only encrypt string values
                    encrypted_dict[key] = await self.encrypt_data(value)
                else:
                    encrypted_dict[key] = value
            
            return encrypted_dict

        except Exception as e:
            raise SecurityError(f"Failed to encrypt dictionary: {str(e)}")

    async def decrypt_dict(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in a dictionary."""
        try:
            decrypted_dict = {}
            
            for key, value in encrypted_data.items():
                if isinstance(value, str):
                    # Only decrypt string values
                    decrypted_dict[key] = await self.decrypt_data(value)
                else:
                    decrypted_dict[key] = value
            
            return decrypted_dict

        except Exception as e:
            raise SecurityError(f"Failed to decrypt dictionary: {str(e)}")

    async def rotate_key(self) -> bool:
        """Rotate the encryption key."""
        try:
            # Generate new key
            new_key = self._generate_key()
            new_cipher_suite = Fernet(new_key)
            
            # Update key in settings
            settings.ENCRYPTION_KEY = new_key.decode()
            
            # Update cipher suite
            self.key = new_key
            self.cipher_suite = new_cipher_suite
            
            return True

        except Exception as e:
            raise SecurityError(f"Failed to rotate encryption key: {str(e)}")

    async def encrypt_file(self, file_path: str) -> str:
        """Encrypt a file."""
        try:
            # Read file content
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            # Encrypt file data
            encrypted_data = self.cipher_suite.encrypt(file_data)
            
            # Save encrypted data
            encrypted_path = f"{file_path}.encrypted"
            with open(encrypted_path, 'wb') as file:
                file.write(encrypted_data)
            
            return encrypted_path

        except Exception as e:
            raise SecurityError(f"Failed to encrypt file: {str(e)}")

    async def decrypt_file(self, encrypted_path: str) -> str:
        """Decrypt a file."""
        try:
            # Read encrypted data
            with open(encrypted_path, 'rb') as file:
                encrypted_data = file.read()
            
            # Decrypt data
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # Save decrypted data
            decrypted_path = encrypted_path.replace('.encrypted', '.decrypted')
            with open(decrypted_path, 'wb') as file:
                file.write(decrypted_data)
            
            return decrypted_path

        except Exception as e:
            raise SecurityError(f"Failed to decrypt file: {str(e)}")

    async def encrypt_field(self, field_name: str, value: str) -> str:
        """Encrypt a specific field value."""
        try:
            # Add field name to value for context
            field_data = f"{field_name}:{value}"
            
            # Encrypt data
            return await self.encrypt_data(field_data)

        except Exception as e:
            raise SecurityError(f"Failed to encrypt field: {str(e)}")

    async def decrypt_field(self, field_name: str, encrypted_value: str) -> str:
        """Decrypt a specific field value."""
        try:
            # Decrypt data
            decrypted_data = await self.decrypt_data(encrypted_value)
            
            # Extract value from field data
            field_data = decrypted_data.split(':', 1)
            if field_data[0] != field_name:
                raise SecurityError("Field name mismatch")
            
            return field_data[1]

        except Exception as e:
            raise SecurityError(f"Failed to decrypt field: {str(e)}") 