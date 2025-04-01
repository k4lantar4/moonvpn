import os
import uuid
from datetime import datetime
from typing import Optional, BinaryIO, Tuple
from fastapi import UploadFile, HTTPException, status
import aiofiles
from pathlib import Path

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FileStorageService:
    """
    Service for handling file storage operations.
    
    This service provides methods for storing and managing files,
    particularly focusing on payment proof images.
    """
    
    # Base directory for file storage
    BASE_UPLOAD_DIR = os.path.join(settings.STATIC_FILES_DIR, "uploads")
    
    # Subdirectories for different file types
    PAYMENT_PROOFS_DIR = os.path.join(BASE_UPLOAD_DIR, "payment_proofs")
    
    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    async def validate_image(cls, file: UploadFile, max_size: Optional[int] = None) -> None:
        """
        Validate image file format and size.
        
        Args:
            file: The uploaded file
            max_size: Maximum file size in bytes (default: cls.MAX_FILE_SIZE)
            
        Raises:
            HTTPException: If validation fails
        """
        if max_size is None:
            max_size = cls.MAX_FILE_SIZE
            
        # Check file size
        file_size = 0
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file position
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed ({max_size / 1024 / 1024:.1f}MB)"
            )
        
        # Check extension
        _, ext = os.path.splitext(file.filename.lower())
        if ext not in cls.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file format. Allowed formats: {', '.join(cls.ALLOWED_IMAGE_EXTENSIONS)}"
            )
    
    @classmethod
    async def save_payment_proof(cls, order_id: int, user_id: int, file: UploadFile) -> str:
        """
        Save a payment proof image.
        
        Args:
            order_id: The ID of the order this proof belongs to
            user_id: The ID of the user who uploaded the proof
            file: The uploaded file
            
        Returns:
            URL path to the saved file
            
        Raises:
            HTTPException: If file saving fails
        """
        # Validate file
        await cls.validate_image(file)
        
        # Ensure directory exists
        os.makedirs(cls.PAYMENT_PROOFS_DIR, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _, ext = os.path.splitext(file.filename.lower())
        unique_id = uuid.uuid4().hex[:8]
        filename = f"payment_proof_order_{order_id}_user_{user_id}_{timestamp}_{unique_id}{ext}"
        
        # Save file
        file_path = os.path.join(cls.PAYMENT_PROOFS_DIR, filename)
        
        try:
            # Write file to disk
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
                
            # Return URL path
            url_path = f"/static/uploads/payment_proofs/{filename}"
            return url_path
            
        except Exception as e:
            logger.error(f"Failed to save payment proof: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save payment proof"
            )
    
    @classmethod
    def get_file_path(cls, url_path: str) -> str:
        """
        Convert URL path to file system path.
        
        Args:
            url_path: URL path to the file
            
        Returns:
            File system path
        """
        # Remove /static prefix if present
        if url_path.startswith("/static/"):
            url_path = url_path[7:]  # Remove "/static/"
            
        return os.path.join(settings.STATIC_FILES_DIR, url_path)
    
    @classmethod
    async def delete_file(cls, url_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            url_path: URL path to the file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        file_path = cls.get_file_path(url_path)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False

# Create singleton instance
file_storage_service = FileStorageService() 