"""
Backup service for MoonVPN Telegram Bot.

This module provides functionality for managing system backups and notifications.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
import json
import shutil
import hashlib
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException

from app.core.database.models import Server, Backup, BackupSchedule
from app.bot.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

class BackupService:
    """Service for managing system backups and notifications."""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.retention_days = 30  # Keep backups for 30 days
        self.max_backups_per_server = 10  # Maximum number of backups per server
        self.compression_level = 9  # Maximum compression level
        self.encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY")  # Encryption key for sensitive data
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup status emojis
        self.status_emojis = {
            "success": "✅",
            "failed": "❌",
            "in_progress": "⏳",
            "scheduled": "📅"
        }
    
    async def create_backup(self, server_id: int, db: Session, schedule_id: Optional[int] = None) -> Dict[str, Any]:
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
            
            # Calculate checksum
            config_str = json.dumps(config, ensure_ascii=False, sort_keys=True)
            checksum = hashlib.sha256(config_str.encode()).hexdigest()
            
            # Save backup with encryption if key is available
            if self.encryption_key:
                encrypted_data = self._encrypt_data(config_str)
                with open(backup_file, 'wb') as f:
                    f.write(encrypted_data)
            else:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
            
            # Create backup record
            backup = Backup(
                server_id=server_id,
                file_path=str(backup_file),
                file_size=backup_file.stat().st_size,
                checksum=checksum,
                created_at=datetime.now(),
                status="success",
                schedule_id=schedule_id
            )
            db.add(backup)
            db.commit()
            
            logger.info(f"Created backup for server {server_id}: {backup_file}")
            
            return {
                "id": backup.id,
                "server_id": server_id,
                "file_path": str(backup_file),
                "file_size": backup_file.stat().st_size,
                "checksum": checksum,
                "created_at": backup.created_at,
                "status": backup.status,
                "status_emoji": self.status_emojis.get(backup.status, "⚪")
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
            
            # Calculate statistics
            total_size = sum(backup.file_size for backup in backups)
            success_count = sum(1 for backup in backups if backup.status == "success")
            failed_count = sum(1 for backup in backups if backup.status == "failed")
            
            # Get scheduled backups
            schedules = db.query(BackupSchedule).filter(
                BackupSchedule.server_id == server_id
            ).all()
            
            return {
                "server_id": server_id,
                "server_name": server.name,
                "total_backups": len(backups),
                "total_size": total_size,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": (success_count / len(backups) * 100) if backups else 0,
                "latest_backup": {
                    "id": backups[0].id,
                    "file_path": backups[0].file_path,
                    "file_size": backups[0].file_size,
                    "checksum": backups[0].checksum,
                    "created_at": backups[0].created_at,
                    "status": backups[0].status,
                    "status_emoji": self.status_emojis.get(backups[0].status, "⚪")
                } if backups else None,
                "scheduled_backups": [
                    {
                        "id": schedule.id,
                        "frequency": schedule.frequency,
                        "last_run": schedule.last_run,
                        "next_run": schedule.next_run,
                        "status": schedule.status,
                        "status_emoji": self.status_emojis.get(schedule.status, "⚪")
                    }
                    for schedule in schedules
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting backup status for server {server_id}: {str(e)}")
            raise
    
    async def cleanup_old_backups(self, db: Session) -> Dict[str, Any]:
        """Clean up old backups based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            freed_space = 0
            failed_deletions = []
            
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
                        failed_deletions.append({
                            "backup_id": backup.id,
                            "error": str(e)
                        })
            
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
                        failed_deletions.append({
                            "backup_id": backup.id,
                            "error": str(e)
                        })
            
            db.commit()
            
            return {
                "removed_count": removed_count,
                "freed_space": freed_space,
                "failed_deletions": failed_deletions,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
            raise
    
    async def get_backup_stats(self, db: Session) -> Dict[str, Any]:
        """Get backup statistics."""
        try:
            # Get all backup records
            backups = db.query(Backup).all()
            
            # Calculate statistics
            total_files = len(backups)
            total_size = sum(backup.file_size for backup in backups)
            success_count = sum(1 for backup in backups if backup.status == "success")
            failed_count = sum(1 for backup in backups if backup.status == "failed")
            
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
                        "size": 0,
                        "success_count": 0,
                        "failed_count": 0
                    }
                backups_by_server[backup.server_id]["count"] += 1
                backups_by_server[backup.server_id]["size"] += backup.file_size
                if backup.status == "success":
                    backups_by_server[backup.server_id]["success_count"] += 1
                elif backup.status == "failed":
                    backups_by_server[backup.server_id]["failed_count"] += 1
            
            # Get daily backup counts
            daily_counts = db.query(
                func.date(Backup.created_at).label('date'),
                func.count(Backup.id).label('count'),
                func.sum(case((Backup.status == 'success', 1), else_=0)).label('success_count'),
                func.sum(case((Backup.status == 'failed', 1), else_=0)).label('failed_count')
            ).group_by(
                func.date(Backup.created_at)
            ).all()
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": (success_count / total_files * 100) if total_files > 0 else 0,
                "oldest_backup": oldest_backup,
                "newest_backup": newest_backup,
                "retention_days": self.retention_days,
                "max_backups_per_server": self.max_backups_per_server,
                "backups_by_server": backups_by_server,
                "daily_counts": [
                    {
                        "date": count.date,
                        "total": count.count,
                        "success": count.success_count,
                        "failed": count.failed_count,
                        "success_rate": (count.success_count / count.count * 100) if count.count > 0 else 0
                    }
                    for count in daily_counts
                ]
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
    
    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt data using the encryption key."""
        try:
            # TODO: Implement proper encryption
            # This is a placeholder that should be replaced with actual encryption
            return data.encode()
            
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            raise 