"""
Backup service for MoonVPN Telegram Bot.

This module provides functionality for managing system backups and notifications.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
import json
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException

from app.core.database.models import Server, Backup
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class BackupService:
    """Service for managing system backups and notifications."""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.retention_days = 30  # Keep backups for 30 days
        self.max_backups_per_server = 10  # Maximum number of backups per server
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, server_id: int, db: Session) -> Dict[str, Any]:
        """Create a backup of the server configuration."""
        try:
            # Get server info
            server = db.query(Server).filter(Server.id == server_id).first()
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            # Create server-specific backup directory
            server_dir = self.backup_dir / str(server_id)
            server_dir.mkdir(exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = server_dir / f"backup_{timestamp}.json"
            
            # Get server configuration from panel
            config = await self._get_server_config(server)
            
            # Save backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # Create backup record
            backup = Backup(
                server_id=server_id,
                file_path=str(backup_file),
                file_size=backup_file.stat().st_size,
                created_at=datetime.now()
            )
            db.add(backup)
            db.commit()
            
            logger.info(f"Created backup for server {server_id}: {backup_file}")
            
            return {
                "id": backup.id,
                "server_id": server_id,
                "file_path": str(backup_file),
                "file_size": backup_file.stat().st_size,
                "created_at": backup.created_at
            }
            
        except Exception as e:
            logger.error(f"Error creating backup for server {server_id}: {str(e)}")
            raise
    
    async def get_backup_status(self, server_id: int, db: Session) -> Dict[str, Any]:
        """Get backup status for a specific server."""
        try:
            # Get server info
            server = db.query(Server).filter(Server.id == server_id).first()
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            
            # Get backup records
            backups = db.query(Backup).filter(
                Backup.server_id == server_id
            ).order_by(
                Backup.created_at.desc()
            ).all()
            
            # Calculate total size
            total_size = sum(backup.file_size for backup in backups)
            
            return {
                "server_id": server_id,
                "server_name": server.name,
                "total_backups": len(backups),
                "total_size": total_size,
                "latest_backup": {
                    "id": backups[0].id,
                    "file_path": backups[0].file_path,
                    "file_size": backups[0].file_size,
                    "created_at": backups[0].created_at
                } if backups else None
            }
            
        except Exception as e:
            logger.error(f"Error getting backup status for server {server_id}: {str(e)}")
            raise
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """Clean up old backups based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            freed_space = 0
            
            # Get all backup records
            backups = db.query(Backup).all()
            
            for backup in backups:
                # Check if backup is too old
                if backup.created_at < cutoff_date:
                    try:
                        # Delete file
                        backup_path = Path(backup.file_path)
                        if backup_path.exists():
                            freed_space += backup_path.stat().st_size
                            backup_path.unlink()
                        
                        # Delete record
                        db.delete(backup)
                        removed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error deleting backup {backup.id}: {str(e)}")
            
            # Clean up per-server limit
            servers = db.query(Server).all()
            for server in servers:
                server_backups = db.query(Backup).filter(
                    Backup.server_id == server.id
                ).order_by(
                    Backup.created_at.desc()
                ).all()
                
                # Remove excess backups
                for backup in server_backups[self.max_backups_per_server:]:
                    try:
                        backup_path = Path(backup.file_path)
                        if backup_path.exists():
                            freed_space += backup_path.stat().st_size
                            backup_path.unlink()
                        
                        db.delete(backup)
                        removed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error deleting excess backup {backup.id}: {str(e)}")
            
            db.commit()
            
            return {
                "removed_count": removed_count,
                "freed_space": freed_space,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
            raise
    
    async def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics."""
        try:
            # Get all backup records
            backups = db.query(Backup).all()
            
            # Calculate statistics
            total_files = len(backups)
            total_size = sum(backup.file_size for backup in backups)
            
            if backups:
                oldest_backup = min(backup.created_at for backup in backups)
                newest_backup = max(backup.created_at for backup in backups)
            else:
                oldest_backup = None
                newest_backup = None
            
            # Get backups by server
            backups_by_server = {}
            for backup in backups:
                if backup.server_id not in backups_by_server:
                    backups_by_server[backup.server_id] = {
                        "count": 0,
                        "size": 0
                    }
                backups_by_server[backup.server_id]["count"] += 1
                backups_by_server[backup.server_id]["size"] += backup.file_size
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "oldest_backup": oldest_backup,
                "newest_backup": newest_backup,
                "retention_days": self.retention_days,
                "max_backups_per_server": self.max_backups_per_server,
                "backups_by_server": backups_by_server
            }
            
        except Exception as e:
            logger.error(f"Error getting backup stats: {str(e)}")
            raise
    
    async def _get_server_config(self, server: Server) -> Dict[str, Any]:
        """Get server configuration from panel."""
        try:
            # TODO: Implement panel API call to get server configuration
            # This is a placeholder that should be replaced with actual panel API integration
            return {
                "server_id": server.id,
                "name": server.name,
                "ip": server.ip,
                "port": server.port,
                "protocol": server.protocol,
                "settings": server.settings,
                "backup_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting server config for server {server.id}: {str(e)}")
            raise 