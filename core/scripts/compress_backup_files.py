"""
Compression script for large backup files.

This script identifies and compresses large backup files to optimize storage usage.
It supports multiple compression algorithms and maintains file integrity through checksums.
"""

import logging
import os
import gzip
import lzma
import zlib
import hashlib
from typing import Tuple
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models.backup import SystemBackup, BackupStatus
from app.core.services.storage_service import StorageService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Compression settings
COMPRESSION_THRESHOLD = 100 * 1024 * 1024  # 100MB
COMPRESSION_ALGORITHMS = {
    'gzip': {
        'compress': lambda data: gzip.compress(data, compresslevel=9),
        'extension': '.gz'
    },
    'lzma': {
        'compress': lambda data: lzma.compress(data, preset=9),
        'extension': '.xz'
    },
    'zlib': {
        'compress': lambda data: zlib.compress(data, level=9),
        'extension': '.zz'
    }
}

def calculate_checksum(data: bytes) -> str:
    """Calculate SHA-256 checksum of data."""
    return hashlib.sha256(data).hexdigest()

def compress_file(file_path: str, algorithm: str = 'gzip') -> Tuple[str, int, str]:
    """
    Compress a file using the specified algorithm.
    
    Returns:
        Tuple[str, int, str]: (compressed_path, compressed_size, checksum)
    """
    if algorithm not in COMPRESSION_ALGORITHMS:
        raise ValueError(f"Unsupported compression algorithm: {algorithm}")
    
    compressed_path = file_path + COMPRESSION_ALGORITHMS[algorithm]['extension']
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Compress data
        compressed_data = COMPRESSION_ALGORITHMS[algorithm]['compress'](data)
        
        # Calculate checksum of compressed data
        checksum = calculate_checksum(compressed_data)
        
        # Write compressed file
        with open(compressed_path, 'wb') as f:
            f.write(compressed_data)
        
        compressed_size = len(compressed_data)
        
        return compressed_path, compressed_size, checksum
    except Exception as e:
        logger.error(f"Error compressing file {file_path}: {str(e)}")
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
        raise

def compress_large_backups(db: Session):
    """Compress large backup files that exceed the threshold."""
    try:
        # Get uncompressed backups exceeding threshold
        large_backups = (
            db.query(SystemBackup)
            .filter(
                SystemBackup.status.in_([BackupStatus.COMPLETED, BackupStatus.VERIFIED]),
                SystemBackup.file_size > COMPRESSION_THRESHOLD,
                ~SystemBackup.storage_path.endswith(('.gz', '.xz', '.zz'))
            )
            .order_by(SystemBackup.file_size.desc())
            .all()
        )
        
        storage_service = StorageService()
        
        for backup in large_backups:
            try:
                logger.info(f"Processing backup: {backup.name} (Size: {backup.file_size} bytes)")
                
                # Get original file
                original_path = backup.storage_path
                if not os.path.exists(original_path):
                    logger.warning(f"Backup file not found: {original_path}")
                    continue
                
                # Choose compression algorithm based on file size
                algorithm = 'gzip'  # Default
                if backup.file_size > 1024 * 1024 * 1024:  # 1GB
                    algorithm = 'lzma'  # Better compression for very large files
                
                # Compress file
                compressed_path, compressed_size, checksum = compress_file(
                    original_path,
                    algorithm
                )
                
                # Verify compression resulted in savings
                if compressed_size >= backup.file_size:
                    logger.info(f"Compression did not reduce file size for {backup.name}")
                    os.remove(compressed_path)
                    continue
                
                # Update backup record
                old_path = backup.storage_path
                backup.storage_path = compressed_path
                backup.file_size = compressed_size
                backup.checksum = checksum
                db.add(backup)
                
                # Delete original file
                os.remove(old_path)
                
                # Commit changes
                db.commit()
                
                logger.info(
                    f"Compressed {backup.name}: "
                    f"Original size: {backup.file_size} bytes, "
                    f"Compressed size: {compressed_size} bytes"
                )
                
            except Exception as e:
                logger.error(f"Error processing backup {backup.id}: {str(e)}")
                db.rollback()
                continue
        
        logger.info("Compression process completed successfully")
        
    except Exception as e:
        logger.error(f"Error during compression process: {str(e)}")
        raise

def main():
    """Main entry point for the compression script."""
    logger.info("Starting backup compression process...")
    
    try:
        db = next(get_db())
        compress_large_backups(db)
    except Exception as e:
        logger.error(f"Compression failed: {str(e)}")
        raise
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    main() 