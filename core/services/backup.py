"""
Backup service for MoonVPN.

This module contains the service class for managing system backups,
including backup creation, scheduling, and verification.
"""

import os
import shutil
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import apscheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.database.models.enhancements.backup import SystemBackup, BackupType, BackupStatus
from core.database.models.enhancements.backup_schedule import BackupSchedule, ScheduleType
from core.schemas.enhancements import (
    SystemBackupCreate, SystemBackupUpdate,
    BackupScheduleCreate, BackupScheduleUpdate
)

class BackupService:
    """Service for managing system backups."""
    
    def __init__(self, db: Session):
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
    
    async def create_backup(self, backup: SystemBackupCreate, user_id: int) -> SystemBackup:
        """Create a new backup."""
        db_backup = SystemBackup(
            **backup.dict(),
            created_by=user_id,
            updated_by=user_id,
            status=BackupStatus.PENDING
        )
        self.db.add(db_backup)
        self.db.commit()
        self.db.refresh(db_backup)
        
        # Start backup process
        await self._process_backup(db_backup)
        
        return db_backup
    
    async def update_backup(self, backup_id: int, backup: SystemBackupUpdate, user_id: int) -> Optional[SystemBackup]:
        """Update an existing backup."""
        db_backup = self.db.query(SystemBackup).filter(SystemBackup.id == backup_id).first()
        if not db_backup:
            return None
        
        update_data = backup.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_backup, field, value)
        
        db_backup.updated_by = user_id
        self.db.commit()
        self.db.refresh(db_backup)
        return db_backup
    
    def get_backup(self, backup_id: int) -> Optional[SystemBackup]:
        """Get a backup by ID."""
        return self.db.query(SystemBackup).filter(SystemBackup.id == backup_id).first()
    
    def get_backups(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[BackupStatus] = None,
        backup_type: Optional[BackupType] = None
    ) -> List[SystemBackup]:
        """Get backups with optional filtering."""
        query = self.db.query(SystemBackup)
        
        if status:
            query = query.filter(SystemBackup.status == status)
        if backup_type:
            query = query.filter(SystemBackup.backup_type == backup_type)
        
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
    
    async def verify_backup(self, backup_id: int) -> bool:
        """Verify a backup's integrity."""
        backup = self.get_backup(backup_id)
        if not backup:
            return False
        
        try:
            # Calculate checksum of backup file
            sha256_hash = hashlib.sha256()
            with open(backup.storage_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            calculated_checksum = sha256_hash.hexdigest()
            
            # Compare with stored checksum
            if calculated_checksum != backup.checksum:
                backup.status = BackupStatus.FAILED
                backup.error_message = "Backup verification failed: checksum mismatch"
                self.db.commit()
                return False
            
            backup.status = BackupStatus.VERIFIED
            backup.verified_at = datetime.utcnow()
            self.db.commit()
            return True
            
        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = f"Backup verification failed: {str(e)}"
            self.db.commit()
            return False
    
    async def create_schedule(self, schedule: BackupScheduleCreate, user_id: int) -> BackupSchedule:
        """Create a new backup schedule."""
        db_schedule = BackupSchedule(
            **schedule.dict(),
            created_by=user_id,
            updated_by=user_id
        )
        self.db.add(db_schedule)
        self.db.commit()
        self.db.refresh(db_schedule)
        
        # Schedule the backup job
        await self._schedule_backup_job(db_schedule)
        
        return db_schedule
    
    async def update_schedule(self, schedule_id: int, schedule: BackupScheduleUpdate, user_id: int) -> Optional[BackupSchedule]:
        """Update an existing backup schedule."""
        db_schedule = self.db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
        if not db_schedule:
            return None
        
        update_data = schedule.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)
        
        db_schedule.updated_by = user_id
        self.db.commit()
        self.db.refresh(db_schedule)
        
        # Reschedule the backup job
        await self._schedule_backup_job(db_schedule)
        
        return db_schedule
    
    def get_schedule(self, schedule_id: int) -> Optional[BackupSchedule]:
        """Get a schedule by ID."""
        return self.db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
    
    def get_active_schedules(self) -> List[BackupSchedule]:
        """Get all active backup schedules."""
        return self.db.query(BackupSchedule).filter(
            BackupSchedule.is_active == True
        ).all()
    
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
            sha256_hash = hashlib.sha256()
            with open(backup.storage_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            backup.checksum = sha256_hash.hexdigest()
            
            # Update backup status
            backup.status = BackupStatus.COMPLETED
            backup.completed_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            self.db.commit()
    
    async def _perform_full_backup(self, backup: SystemBackup) -> None:
        """Perform a full system backup."""
        # Implementation depends on what needs to be backed up
        # This is a placeholder for the actual backup logic
        pass
    
    async def _perform_incremental_backup(self, backup: SystemBackup) -> None:
        """Perform an incremental backup."""
        # Implementation depends on what needs to be backed up
        # This is a placeholder for the actual backup logic
        pass
    
    async def _perform_differential_backup(self, backup: SystemBackup) -> None:
        """Perform a differential backup."""
        # Implementation depends on what needs to be backed up
        # This is a placeholder for the actual backup logic
        pass
    
    async def _schedule_backup_job(self, schedule: BackupSchedule) -> None:
        """Schedule a backup job based on the schedule configuration."""
        # Remove existing job if any
        self.scheduler.remove_job(f"backup_{schedule.id}", ignore_if_not_exists=True)
        
        if not schedule.is_active:
            return
        
        # Create backup job
        trigger = CronTrigger.from_crontab(schedule.cron_expression)
        self.scheduler.add_job(
            self._run_scheduled_backup,
            trigger=trigger,
            id=f"backup_{schedule.id}",
            args=[schedule.id]
        )
    
    async def _run_scheduled_backup(self, schedule_id: int) -> None:
        """Run a scheduled backup."""
        schedule = self.get_schedule(schedule_id)
        if not schedule or not schedule.is_active:
            return
        
        # Create backup
        backup = SystemBackupCreate(
            name=f"Scheduled backup - {schedule.name}",
            description=f"Automated backup from schedule: {schedule.name}",
            backup_type=schedule.backup_type,
            storage_path=os.path.join(
                schedule.storage_path,
                f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.bak"
            )
        )
        
        await self.create_backup(backup, schedule.created_by)
        
        # Update schedule
        schedule.last_run_at = datetime.utcnow()
        self.db.commit()
    
    def cleanup_expired_backups(self) -> int:
        """Clean up expired backups."""
        expired_backups = self.get_expired_backups()
        cleaned_count = 0
        
        for backup in expired_backups:
            try:
                if os.path.exists(backup.storage_path):
                    os.remove(backup.storage_path)
                self.db.delete(backup)
                cleaned_count += 1
            except Exception as e:
                backup.error_message = f"Cleanup failed: {str(e)}"
                self.db.commit()
        
        self.db.commit()
        return cleaned_count
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics."""
        total_backups = self.db.query(func.count(SystemBackup.id)).scalar()
        completed_backups = self.db.query(func.count(SystemBackup.id)).filter(
            SystemBackup.status == BackupStatus.COMPLETED
        ).scalar()
        failed_backups = self.db.query(func.count(SystemBackup.id)).filter(
            SystemBackup.status == BackupStatus.FAILED
        ).scalar()
        total_size = self.db.query(func.sum(SystemBackup.size_bytes)).scalar() or 0
        
        return {
            "total_backups": total_backups,
            "completed_backups": completed_backups,
            "failed_backups": failed_backups,
            "success_rate": (completed_backups / total_backups * 100) if total_backups > 0 else 0,
            "total_size_bytes": total_size,
            "total_size_gb": total_size / (1024 * 1024 * 1024)
        } 