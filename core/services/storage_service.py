"""
Storage service for handling file operations across different storage providers.

This module provides functionality for managing file operations like saving,
reading, deleting, and verifying files across different storage providers.
"""

import os
import hashlib
import logging
from typing import Optional, BinaryIO, Dict, Any
from pathlib import Path
from datetime import datetime

from app.core.models.backup import StorageProvider
from app.core.exceptions.admin_exceptions import AdminError

logger = logging.getLogger(__name__)

class StorageService:
    """Service for managing file storage operations."""
    
    def __init__(self):
        """Initialize storage service."""
        self.providers: Dict[StorageProvider, Any] = {
            StorageProvider.LOCAL: LocalStorageProvider(),
            # Add other providers as needed:
            # StorageProvider.S3: S3StorageProvider(),
            # StorageProvider.GCS: GCSStorageProvider(),
            # StorageProvider.AZURE: AzureStorageProvider(),
        }
    
    async def save_file(
        self,
        provider: StorageProvider,
        path: str,
        content: str | bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save content to a file using the specified storage provider."""
        try:
            storage = self._get_provider(provider)
            return await storage.save_file(path, content, metadata)
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise AdminError(f"Failed to save file: {str(e)}")
    
    async def read_file(
        self,
        provider: StorageProvider,
        path: str
    ) -> bytes:
        """Read file content using the specified storage provider."""
        try:
            storage = self._get_provider(provider)
            return await storage.read_file(path)
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise AdminError(f"Failed to read file: {str(e)}")
    
    async def delete_file(
        self,
        provider: StorageProvider,
        path: str
    ) -> bool:
        """Delete a file using the specified storage provider."""
        try:
            storage = self._get_provider(provider)
            return await storage.delete_file(path)
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            raise AdminError(f"Failed to delete file: {str(e)}")
    
    async def exists(
        self,
        provider: StorageProvider,
        path: str
    ) -> bool:
        """Check if a file exists using the specified storage provider."""
        try:
            storage = self._get_provider(provider)
            return await storage.exists(path)
        except Exception as e:
            logger.error(f"Error checking file existence: {str(e)}")
            raise AdminError(f"Failed to check file existence: {str(e)}")
    
    async def get_checksum(
        self,
        provider: StorageProvider,
        path: str
    ) -> str:
        """Calculate file checksum using the specified storage provider."""
        try:
            storage = self._get_provider(provider)
            return await storage.get_checksum(path)
        except Exception as e:
            logger.error(f"Error calculating checksum: {str(e)}")
            raise AdminError(f"Failed to calculate checksum: {str(e)}")
    
    async def get_file_size(
        self,
        provider: StorageProvider,
        path: str
    ) -> int:
        """Get file size using the specified storage provider."""
        try:
            storage = self._get_provider(provider)
            return await storage.get_file_size(path)
        except Exception as e:
            logger.error(f"Error getting file size: {str(e)}")
            raise AdminError(f"Failed to get file size: {str(e)}")
    
    async def restore_file(
        self,
        provider: StorageProvider,
        source_path: str,
        target_path: str
    ) -> bool:
        """Restore a file from backup using the specified storage provider."""
        try:
            storage = self._get_provider(provider)
            return await storage.restore_file(source_path, target_path)
        except Exception as e:
            logger.error(f"Error restoring file: {str(e)}")
            raise AdminError(f"Failed to restore file: {str(e)}")
    
    def _get_provider(self, provider: StorageProvider) -> Any:
        """Get the storage provider instance."""
        if provider not in self.providers:
            raise AdminError(f"Unsupported storage provider: {provider}")
        return self.providers[provider]


class LocalStorageProvider:
    """Provider for local file system storage."""
    
    async def save_file(
        self,
        path: str,
        content: str | bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save content to a local file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Convert string content to bytes if needed
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            # Write content to file
            with open(path, 'wb') as f:
                f.write(content)
            
            # Save metadata if provided
            if metadata:
                metadata_path = f"{path}.metadata"
                with open(metadata_path, 'w') as f:
                    f.write(str(metadata))
            
            return True
        except Exception as e:
            logger.error(f"Error saving local file: {str(e)}")
            raise
    
    async def read_file(self, path: str) -> bytes:
        """Read content from a local file."""
        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading local file: {str(e)}")
            raise
    
    async def delete_file(self, path: str) -> bool:
        """Delete a local file."""
        try:
            # Delete metadata file if it exists
            metadata_path = f"{path}.metadata"
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            # Delete main file
            if os.path.exists(path):
                os.remove(path)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting local file: {str(e)}")
            raise
    
    async def exists(self, path: str) -> bool:
        """Check if a local file exists."""
        return os.path.exists(path)
    
    async def get_checksum(self, path: str) -> str:
        """Calculate MD5 checksum of a local file."""
        try:
            hash_md5 = hashlib.md5()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating local file checksum: {str(e)}")
            raise
    
    async def get_file_size(self, path: str) -> int:
        """Get size of a local file in bytes."""
        try:
            return os.path.getsize(path)
        except Exception as e:
            logger.error(f"Error getting local file size: {str(e)}")
            raise
    
    async def restore_file(self, source_path: str, target_path: str) -> bool:
        """Restore a local file to target path."""
        try:
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Copy file to target location
            with open(source_path, 'rb') as src, open(target_path, 'wb') as dst:
                dst.write(src.read())
            
            # Copy metadata if it exists
            source_metadata = f"{source_path}.metadata"
            target_metadata = f"{target_path}.metadata"
            if os.path.exists(source_metadata):
                with open(source_metadata, 'rb') as src, open(target_metadata, 'wb') as dst:
                    dst.write(src.read())
            
            return True
        except Exception as e:
            logger.error(f"Error restoring local file: {str(e)}")
            raise


# Additional storage providers can be implemented here:
# class S3StorageProvider:
#     """Provider for Amazon S3 storage."""
#     pass
# 
# class GCSStorageProvider:
#     """Provider for Google Cloud Storage."""
#     pass
# 
# class AzureStorageProvider:
#     """Provider for Azure Blob Storage."""
#     pass 