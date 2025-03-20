from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
import os
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.backup import SystemBackup, BackupSchedule
from app.services.notification import NotificationService
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.storage_service = StorageService()
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(self, backup_type: str = "full") -> SystemBackup:
        """Create a new system backup"""
        try:
            logger.info(f"Starting {backup_type} backup")
            start_time = datetime.utcnow()
            
            # Create backup record
            backup = SystemBackup(
                type=backup_type,
                status="in_progress",
                start_time=start_time,
                size=0,
                path=""
            )
            self.db.add(backup)
            self.db.commit()
            
            # Perform backup based on type
            if backup_type == "full":
                await self._create_full_backup(backup)
            elif backup_type == "incremental":
                await self._create_incremental_backup(backup)
            elif backup_type == "differential":
                await self._create_differential_backup(backup)
            
            # Update backup record
            backup.status = "completed"
            backup.end_time = datetime.utcnow()
            backup.size = self._get_backup_size(backup.path)
            self.db.commit()
            
            # Notify administrators
            await self.notification_service.send_admin_alert(
                "Backup Completed",
                f"{backup_type.capitalize()} backup completed successfully"
            )
            
            return backup
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            if backup:
                backup.status = "failed"
                backup.error_message = str(e)
                backup.end_time = datetime.utcnow()
                self.db.commit()
            
            await self.notification_service.send_admin_alert(
                "Backup Failed",
                f"{backup_type.capitalize()} backup failed: {str(e)}"
            )
            raise

    async def _create_full_backup(self, backup: SystemBackup):
        """Create a full system backup"""
        try:
            # Create backup directory
            backup_dir = self.backup_dir / f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup database
            await self._backup_database(backup_dir)
            
            # Backup configuration files
            await self._backup_configurations(backup_dir)
            
            # Backup user data
            await self._backup_user_data(backup_dir)
            
            # Update backup path
            backup.path = str(backup_dir)
            
        except Exception as e:
            logger.error(f"Full backup failed: {str(e)}")
            raise

    async def _create_incremental_backup(self, backup: SystemBackup):
        """Create an incremental backup"""
        try:
            # Get last full backup
            last_full = self.db.query(SystemBackup).filter(
                SystemBackup.type == "full",
                SystemBackup.status == "completed"
            ).order_by(SystemBackup.start_time.desc()).first()
            
            if not last_full:
                raise ValueError("No full backup found for incremental backup")
            
            # Create backup directory
            backup_dir = self.backup_dir / f"incremental_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup only changed files since last full backup
            await self._backup_changes(backup_dir, last_full.start_time)
            
            # Update backup path
            backup.path = str(backup_dir)
            
        except Exception as e:
            logger.error(f"Incremental backup failed: {str(e)}")
            raise

    async def _create_differential_backup(self, backup: SystemBackup):
        """Create a differential backup"""
        try:
            # Get last full backup
            last_full = self.db.query(SystemBackup).filter(
                SystemBackup.type == "full",
                SystemBackup.status == "completed"
            ).order_by(SystemBackup.start_time.desc()).first()
            
            if not last_full:
                raise ValueError("No full backup found for differential backup")
            
            # Create backup directory
            backup_dir = self.backup_dir / f"differential_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup all changes since last full backup
            await self._backup_all_changes(backup_dir, last_full.start_time)
            
            # Update backup path
            backup.path = str(backup_dir)
            
        except Exception as e:
            logger.error(f"Differential backup failed: {str(e)}")
            raise

    async def _backup_database(self, backup_dir: Path):
        """Backup database"""
        try:
            # Implement database backup logic
            # This could include:
            # - pg_dump for PostgreSQL
            # - mysqldump for MySQL
            # - mongodump for MongoDB
            pass
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise

    async def _backup_configurations(self, backup_dir: Path):
        """Backup configuration files"""
        try:
            # Implement configuration backup logic
            # This could include:
            # - Environment files
            # - Application configs
            # - Service configs
            pass
        except Exception as e:
            logger.error(f"Configuration backup failed: {str(e)}")
            raise

    async def _backup_user_data(self, backup_dir: Path):
        """Backup user data"""
        try:
            # Implement user data backup logic
            # This could include:
            # - User files
            # - User settings
            # - User preferences
            pass
        except Exception as e:
            logger.error(f"User data backup failed: {str(e)}")
            raise

    async def _backup_changes(self, backup_dir: Path, since: datetime):
        """Backup only changed files since specified time"""
        try:
            # Implement incremental backup logic
            # This could include:
            # - File system changes
            # - Database changes
            # - Configuration changes
            pass
        except Exception as e:
            logger.error(f"Changes backup failed: {str(e)}")
            raise

    async def _backup_all_changes(self, backup_dir: Path, since: datetime):
        """Backup all changes since specified time"""
        try:
            # Implement differential backup logic
            # This could include:
            # - All file changes
            # - All database changes
            # - All configuration changes
            pass
        except Exception as e:
            logger.error(f"All changes backup failed: {str(e)}")
            raise

    def _get_backup_size(self, backup_path: str) -> int:
        """Calculate total size of backup in bytes"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(backup_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            return total_size
        except Exception as e:
            logger.error(f"Error calculating backup size: {str(e)}")
            return 0

    async def restore_backup(self, backup_id: int) -> bool:
        """Restore system from backup"""
        try:
            # Get backup record
            backup = self.db.query(SystemBackup).filter(
                SystemBackup.id == backup_id,
                SystemBackup.status == "completed"
            ).first()
            
            if not backup:
                raise ValueError(f"Backup {backup_id} not found or not completed")
            
            # Start restoration
            backup.restore_status = "in_progress"
            backup.restore_start_time = datetime.utcnow()
            self.db.commit()
            
            # Restore based on backup type
            if backup.type == "full":
                await self._restore_full_backup(backup)
            elif backup.type == "incremental":
                await self._restore_incremental_backup(backup)
            elif backup.type == "differential":
                await self._restore_differential_backup(backup)
            
            # Update restore status
            backup.restore_status = "completed"
            backup.restore_end_time = datetime.utcnow()
            self.db.commit()
            
            # Notify administrators
            await self.notification_service.send_admin_alert(
                "Backup Restored",
                f"System restored from {backup.type} backup {backup_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            if backup:
                backup.restore_status = "failed"
                backup.restore_error_message = str(e)
                backup.restore_end_time = datetime.utcnow()
                self.db.commit()
            
            await self.notification_service.send_admin_alert(
                "Restore Failed",
                f"Failed to restore from backup {backup_id}: {str(e)}"
            )
            raise

    async def _restore_full_backup(self, backup: SystemBackup):
        """Restore from full backup"""
        try:
            # Implement full restore logic
            # This could include:
            # - Database restore
            # - Configuration restore
            # - User data restore
            pass
        except Exception as e:
            logger.error(f"Full restore failed: {str(e)}")
            raise

    async def _restore_incremental_backup(self, backup: SystemBackup):
        """Restore from incremental backup"""
        try:
            # Implement incremental restore logic
            # This could include:
            # - Restore base backup
            # - Apply incremental changes
            pass
        except Exception as e:
            logger.error(f"Incremental restore failed: {str(e)}")
            raise

    async def _restore_differential_backup(self, backup: SystemBackup):
        """Restore from differential backup"""
        try:
            # Implement differential restore logic
            # This could include:
            # - Restore base backup
            # - Apply differential changes
            pass
        except Exception as e:
            logger.error(f"Differential restore failed: {str(e)}")
            raise

    async def cleanup_old_backups(self, retention_days: int = 30):
        """Clean up old backups based on retention policy"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Get old backups
            old_backups = self.db.query(SystemBackup).filter(
                SystemBackup.start_time < cutoff_date,
                SystemBackup.status == "completed"
            ).all()
            
            for backup in old_backups:
                try:
                    # Delete backup files
                    if backup.path and os.path.exists(backup.path):
                        shutil.rmtree(backup.path)
                    
                    # Delete backup record
                    self.db.delete(backup)
                    
                except Exception as e:
                    logger.error(f"Error cleaning up backup {backup.id}: {str(e)}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            raise

    async def start_backup_scheduler(self):
        """Start the backup scheduler"""
        while True:
            try:
                # Get active schedules
                schedules = self.db.query(BackupSchedule).filter(
                    BackupSchedule.is_active == True
                ).all()
                
                for schedule in schedules:
                    # Check if backup is due
                    if self._is_backup_due(schedule):
                        await self.create_backup(schedule.backup_type)
                
                # Wait before next check
                await asyncio.sleep(settings.BACKUP_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in backup scheduler: {str(e)}")
                await asyncio.sleep(settings.BACKUP_CHECK_INTERVAL)

    def _is_backup_due(self, schedule: BackupSchedule) -> bool:
        """Check if backup is due based on schedule"""
        try:
            last_backup = self.db.query(SystemBackup).filter(
                SystemBackup.type == schedule.backup_type,
                SystemBackup.status == "completed"
            ).order_by(SystemBackup.start_time.desc()).first()
            
            if not last_backup:
                return True
            
            # Check schedule type
            if schedule.schedule_type == "daily":
                return (datetime.utcnow() - last_backup.start_time).days >= 1
            elif schedule.schedule_type == "weekly":
                return (datetime.utcnow() - last_backup.start_time).days >= 7
            elif schedule.schedule_type == "monthly":
                return (datetime.utcnow() - last_backup.start_time).days >= 30
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking backup schedule: {str(e)}")
            return False 