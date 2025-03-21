from datetime import datetime, timedelta
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from core.config import settings
from core.database.models import SystemBackup, SystemMetrics, SystemLogs
from core.services.notification import NotificationService

logger = logging.getLogger(__name__)

class CleanupService:
    """Service for managing system-wide cleanup operations."""

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    async def cleanup_all(self) -> Dict[str, Any]:
        """Run all cleanup operations."""
        results = {
            "backups": await self.cleanup_old_backups(),
            "metrics": await self.cleanup_old_metrics(),
            "logs": await self.cleanup_old_logs(),
            "temp_files": await self.cleanup_temp_files(),
            "timestamp": datetime.utcnow()
        }
        
        # Send notification about cleanup results
        await self.notification_service.send_admin_notification(
            "System Cleanup Complete",
            f"Cleanup results:\n{results}"
        )
        
        return results

    async def cleanup_old_backups(self, retention_days: int = 30) -> Dict[str, Any]:
        """Clean up old backups."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            removed_count = 0
            freed_space = 0
            
            old_backups = self.db.query(SystemBackup).filter(
                SystemBackup.created_at < cutoff_date
            ).all()
            
            for backup in old_backups:
                try:
                    if backup.storage_path and os.path.exists(backup.storage_path):
                        size = os.path.getsize(backup.storage_path)
                        os.remove(backup.storage_path)
                        freed_space += size
                        removed_count += 1
                        self.db.delete(backup)
                except Exception as e:
                    logger.error(f"Error cleaning up backup {backup.id}: {str(e)}")
            
            self.db.commit()
            
            return {
                "removed_count": removed_count,
                "freed_space_bytes": freed_space,
                "cutoff_date": cutoff_date
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_backups: {str(e)}")
            raise

    async def cleanup_old_metrics(self, retention_days: int = 7) -> Dict[str, Any]:
        """Clean up old system metrics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            result = self.db.query(SystemMetrics).filter(
                SystemMetrics.timestamp < cutoff_date
            ).delete()
            
            self.db.commit()
            
            return {
                "removed_count": result,
                "cutoff_date": cutoff_date
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_metrics: {str(e)}")
            raise

    async def cleanup_old_logs(self, retention_days: int = 30) -> Dict[str, Any]:
        """Clean up old system logs."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            result = self.db.query(SystemLogs).filter(
                SystemLogs.timestamp < cutoff_date
            ).delete()
            
            self.db.commit()
            
            return {
                "removed_count": result,
                "cutoff_date": cutoff_date
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_logs: {str(e)}")
            raise

    async def cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files."""
        try:
            temp_dir = Path(settings.TEMP_DIR)
            removed_count = 0
            freed_space = 0
            
            if temp_dir.exists():
                for item in temp_dir.glob("*"):
                    try:
                        if item.is_file():
                            size = item.stat().st_size
                            item.unlink()
                            freed_space += size
                            removed_count += 1
                        elif item.is_dir():
                            size = sum(f.stat().st_size for f in item.glob("**/*") if f.is_file())
                            shutil.rmtree(item)
                            freed_space += size
                            removed_count += 1
                    except Exception as e:
                        logger.error(f"Error cleaning up {item}: {str(e)}")
            
            return {
                "removed_count": removed_count,
                "freed_space_bytes": freed_space
            }
            
        except Exception as e:
            logger.error(f"Error in cleanup_temp_files: {str(e)}")
            raise 