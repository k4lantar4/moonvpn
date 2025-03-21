"""
Backup service for MoonVPN.

This module provides functionality for managing system backups,
including backup creation, scheduling, verification, and storage management.
"""

import os
import shutil
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.models.backup import (
    SystemBackup, BackupSchedule,
    BackupType, BackupStatus, StorageProvider
)
from app.core.exceptions.admin_exceptions import (
    AdminError, AdminConfigError
)
from app.core.services.storage import StorageService
from app.core.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class BackupService:
    """Service for managing system backups."""
    
    def __init__(self, db: Session):
        """Initialize backup service."""
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.storage_service = StorageService()
        self.notification_service = NotificationService(db)
        self.scheduler.start()
        
        # Initialize backup schedules
        self._initialize_schedules()
    
    async def create_backup(
        self,
        name: str,
        description: Optional[str],
        backup_type: BackupType,
        storage_provider: StorageProvider,
        storage_path: str,
        user_id: int,
        schedule_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SystemBackup:
        """Create a new backup."""
        try:
            # Create backup record
            backup = SystemBackup(
                name=name,
                description=description,
                backup_type=backup_type,
                storage_provider=storage_provider,
                storage_path=storage_path,
                created_by=user_id,
                updated_by=user_id,
                schedule_id=schedule_id,
                metadata=metadata or {}
            )
            self.db.add(backup)
            self.db.commit()
            
            # Start backup process
            await self._process_backup(backup)
            
            return backup
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise AdminError(f"Failed to create backup: {str(e)}")
    
    async def verify_backup(
        self,
        backup_id: int,
        user_id: int
    ) -> SystemBackup:
        """Verify a backup's integrity."""
        try:
            backup = self.get_backup(backup_id)
            if not backup:
                raise AdminError(f"Backup {backup_id} not found")
            
            # Verify backup file exists
            if not await self.storage_service.exists(backup.storage_provider, backup.storage_path):
                raise AdminError(f"Backup file not found at {backup.storage_path}")
            
            # Calculate checksum
            file_checksum = await self.storage_service.get_checksum(
                backup.storage_provider,
                backup.storage_path
            )
            
            if file_checksum != backup.checksum:
                backup.status = BackupStatus.FAILED
                backup.error_message = "Checksum verification failed"
                self.db.commit()
                raise AdminError("Backup verification failed: checksum mismatch")
            
            # Update backup status
            backup.status = BackupStatus.VERIFIED
            backup.verified_at = datetime.utcnow()
            backup.verified_by = user_id
            self.db.commit()
            
            return backup
        except Exception as e:
            logger.error(f"Error verifying backup: {str(e)}")
            raise AdminError(f"Failed to verify backup: {str(e)}")
    
    async def restore_backup(
        self,
        backup_id: int,
        user_id: int,
        target_path: Optional[str] = None
    ) -> bool:
        """Restore a backup."""
        try:
            backup = self.get_backup(backup_id)
            if not backup:
                raise AdminError(f"Backup {backup_id} not found")
            
            # Verify backup first
            await self.verify_backup(backup_id, user_id)
            
            # Restore backup
            restored = await self.storage_service.restore_file(
                backup.storage_provider,
                backup.storage_path,
                target_path or backup.storage_path
            )
            
            if not restored:
                raise AdminError("Failed to restore backup")
            
            return True
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            raise AdminError(f"Failed to restore backup: {str(e)}")
    
    def get_backup(self, backup_id: int) -> Optional[SystemBackup]:
        """Get a backup by ID."""
        return self.db.query(SystemBackup).filter(
            SystemBackup.id == backup_id
        ).first()
    
    def get_backups(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BackupStatus] = None,
        backup_type: Optional[BackupType] = None,
        storage_provider: Optional[StorageProvider] = None
    ) -> List[SystemBackup]:
        """Get backups with optional filtering."""
        query = self.db.query(SystemBackup)
        
        if status:
            query = query.filter(SystemBackup.status == status)
        if backup_type:
            query = query.filter(SystemBackup.backup_type == backup_type)
        if storage_provider:
            query = query.filter(SystemBackup.storage_provider == storage_provider)
        
        return query.offset(skip).limit(limit).all()
    
    def get_failed_backups(self) -> List[SystemBackup]:
        """Get all failed backups."""
        return self.db.query(SystemBackup).filter(
            SystemBackup.status == BackupStatus.FAILED
        ).all()
    
    def get_expired_backups(self) -> List[SystemBackup]:
        """Get all expired backups."""
        return self.db.query(SystemBackup).filter(
            SystemBackup.expires_at <= datetime.utcnow()
        ).all()
    
    async def create_schedule(
        self,
        name: str,
        description: Optional[str],
        backup_type: BackupType,
        storage_provider: StorageProvider,
        storage_path: str,
        cron_expression: str,
        retention_days: int,
        max_backups: int,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BackupSchedule:
        """Create a new backup schedule."""
        try:
            # Validate cron expression
            try:
                CronTrigger.from_crontab(cron_expression)
            except Exception as e:
                raise AdminError(f"Invalid cron expression: {str(e)}")
            
            # Create schedule record
            schedule = BackupSchedule(
                name=name,
                description=description,
                backup_type=backup_type,
                storage_provider=storage_provider,
                storage_path=storage_path,
                cron_expression=cron_expression,
                retention_days=retention_days,
                max_backups=max_backups,
                created_by=user_id,
                updated_by=user_id,
                metadata=metadata or {}
            )
            self.db.add(schedule)
            self.db.commit()
            
            # Schedule the backup job
            await self._schedule_backup_job(schedule)
            
            return schedule
        except Exception as e:
            logger.error(f"Error creating backup schedule: {str(e)}")
            raise AdminError(f"Failed to create backup schedule: {str(e)}")
    
    async def _process_backup(self, backup: SystemBackup) -> None:
        """Process a backup operation."""
        try:
            backup.status = BackupStatus.IN_PROGRESS
            backup.started_at = datetime.utcnow()
            self.db.commit()
            
            # Create backup directory if it doesn't exist
            os.makedirs(os.path.dirname(backup.storage_path), exist_ok=True)
            
            # Perform backup based on type
            if backup.backup_type == BackupType.FULL:
                await self._perform_full_backup(backup)
            elif backup.backup_type == BackupType.INCREMENTAL:
                await self._perform_incremental_backup(backup)
            elif backup.backup_type == BackupType.DIFFERENTIAL:
                await self._perform_differential_backup(backup)
            
            # Calculate checksum
            backup.checksum = await self.storage_service.get_checksum(
                backup.storage_provider,
                backup.storage_path
            )
            
            # Get file size
            backup.file_size = await self.storage_service.get_file_size(
                backup.storage_provider,
                backup.storage_path
            )
            
            # Update backup status
            backup.status = BackupStatus.COMPLETED
            backup.completed_at = datetime.utcnow()
            self.db.commit()
            
            # Send notification
            await self.notification_service.send_backup_notification(
                backup_id=backup.id,
                status="success",
                message=f"Backup {backup.name} completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error processing backup: {str(e)}")
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            self.db.commit()
            
            # Send notification
            await self.notification_service.send_backup_notification(
                backup_id=backup.id,
                status="failed",
                message=f"Backup {backup.name} failed: {str(e)}"
            )
    
    async def _perform_full_backup(self, backup: SystemBackup) -> None:
        """Perform a full system backup."""
        try:
            # Get system configuration
            config = await self._get_system_config()
            
            # Save configuration to backup file
            await self.storage_service.save_file(
                backup.storage_provider,
                backup.storage_path,
                json.dumps(config, indent=2)
            )
            
        except Exception as e:
            logger.error(f"Error performing full backup: {str(e)}")
            raise
    
    async def _perform_incremental_backup(self, backup: SystemBackup) -> None:
        """Perform an incremental backup."""
        try:
            # Get last successful backup
            last_backup = self.db.query(SystemBackup).filter(
                SystemBackup.status == BackupStatus.COMPLETED,
                SystemBackup.backup_type.in_([BackupType.FULL, BackupType.INCREMENTAL]),
                SystemBackup.created_at < backup.created_at
            ).order_by(SystemBackup.created_at.desc()).first()
            
            if not last_backup:
                # No previous backup found, perform full backup instead
                await self._perform_full_backup(backup)
                return
            
            # Get changes since last backup
            changes = await self._get_system_changes(last_backup.completed_at)
            
            # Save changes to backup file
            await self.storage_service.save_file(
                backup.storage_provider,
                backup.storage_path,
                json.dumps(changes, indent=2)
            )
            
        except Exception as e:
            logger.error(f"Error performing incremental backup: {str(e)}")
            raise
    
    async def _perform_differential_backup(self, backup: SystemBackup) -> None:
        """Perform a differential backup."""
        try:
            # Get last full backup
            last_full = self.db.query(SystemBackup).filter(
                SystemBackup.status == BackupStatus.COMPLETED,
                SystemBackup.backup_type == BackupType.FULL,
                SystemBackup.created_at < backup.created_at
            ).order_by(SystemBackup.created_at.desc()).first()
            
            if not last_full:
                # No full backup found, perform full backup instead
                await self._perform_full_backup(backup)
                return
            
            # Get all changes since last full backup
            changes = await self._get_system_changes(last_full.completed_at)
            
            # Save changes to backup file
            await self.storage_service.save_file(
                backup.storage_provider,
                backup.storage_path,
                json.dumps(changes, indent=2)
            )
            
        except Exception as e:
            logger.error(f"Error performing differential backup: {str(e)}")
            raise
    
    async def _get_system_config(self) -> Dict[str, Any]:
        """Get complete system configuration."""
        # TODO: Implement actual system configuration gathering
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "config": {}
        }
    
    async def _get_system_changes(self, since: datetime) -> Dict[str, Any]:
        """Get system changes since specified time."""
        # TODO: Implement actual change detection
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "since": since.isoformat(),
            "changes": []
        }
    
    def _initialize_schedules(self) -> None:
        """Initialize all active backup schedules."""
        try:
            schedules = self.db.query(BackupSchedule).filter(
                BackupSchedule.is_active == True
            ).all()
            
            for schedule in schedules:
                self.scheduler.add_job(
                    self._run_scheduled_backup,
                    CronTrigger.from_crontab(schedule.cron_expression),
                    id=f"backup_{schedule.id}",
                    args=[schedule.id]
                )
                
        except Exception as e:
            logger.error(f"Error initializing backup schedules: {str(e)}")
    
    async def _run_scheduled_backup(self, schedule_id: int) -> None:
        """Run a scheduled backup."""
        try:
            schedule = self.db.query(BackupSchedule).filter(
                BackupSchedule.id == schedule_id
            ).first()
            
            if not schedule or not schedule.is_active:
                return
            
            # Generate backup path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                schedule.storage_path,
                f"backup_{timestamp}.json"
            )
            
            # Create backup
            await self.create_backup(
                name=f"Scheduled backup - {schedule.name}",
                description=f"Automated backup from schedule: {schedule.name}",
                backup_type=schedule.backup_type,
                storage_provider=schedule.storage_provider,
                storage_path=backup_path,
                user_id=schedule.created_by,
                schedule_id=schedule.id
            )
            
            # Update schedule
            schedule.last_run_at = datetime.utcnow()
            schedule.next_run_at = self.scheduler.get_job(f"backup_{schedule.id}").next_run_time
            self.db.commit()
            
            # Clean up old backups
            await self._cleanup_old_backups(schedule)
            
        except Exception as e:
            logger.error(f"Error running scheduled backup: {str(e)}")
            schedule.error_count += 1
            schedule.last_error = str(e)
            self.db.commit()
    
    async def _cleanup_old_backups(self, schedule: BackupSchedule) -> None:
        """Clean up old backups based on retention policy."""
        try:
            # Get all backups for this schedule
            backups = self.db.query(SystemBackup).filter(
                SystemBackup.schedule_id == schedule.id,
                SystemBackup.status == BackupStatus.COMPLETED
            ).order_by(SystemBackup.created_at.desc()).all()
            
            # Keep only the specified number of backups
            if len(backups) > schedule.max_backups:
                for backup in backups[schedule.max_backups:]:
                    # Delete backup file
                    await self.storage_service.delete_file(
                        backup.storage_provider,
                        backup.storage_path
                    )
                    
                    # Update backup status
                    backup.status = BackupStatus.DELETED
                    
            # Delete backups older than retention period
            retention_date = datetime.utcnow() - timedelta(days=schedule.retention_days)
            old_backups = self.db.query(SystemBackup).filter(
                SystemBackup.schedule_id == schedule.id,
                SystemBackup.created_at < retention_date,
                SystemBackup.status == BackupStatus.COMPLETED
            ).all()
            
            for backup in old_backups:
                # Delete backup file
                await self.storage_service.delete_file(
                    backup.storage_provider,
                    backup.storage_path
                )
                
                # Update backup status
                backup.status = BackupStatus.DELETED
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
            raise 