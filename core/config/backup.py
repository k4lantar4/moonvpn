"""
Backup API endpoints.

This module contains the FastAPI router for handling backup-related API endpoints,
including backup creation, scheduling, and management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.api import deps
from core.schemas.enhancements import (
    SystemBackupCreate, SystemBackupUpdate, SystemBackupInDB,
    BackupScheduleCreate, BackupScheduleUpdate, BackupScheduleInDB,
    BackupStatistics
)
from core.services.backup import BackupService

router = APIRouter()

@router.post("/", response_model=SystemBackupInDB)
async def create_backup(
    backup: SystemBackupCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Create a new backup."""
    backup_service = BackupService(db)
    return await backup_service.create_backup(backup, current_user.id)

@router.put("/{backup_id}", response_model=SystemBackupInDB)
async def update_backup(
    backup_id: int,
    backup: SystemBackupUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Update an existing backup."""
    backup_service = BackupService(db)
    db_backup = await backup_service.update_backup(backup_id, backup, current_user.id)
    if not db_backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return db_backup

@router.get("/{backup_id}", response_model=SystemBackupInDB)
def get_backup(
    backup_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get a backup by ID."""
    backup_service = BackupService(db)
    db_backup = backup_service.get_backup(backup_id)
    if not db_backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return db_backup

@router.get("/", response_model=List[SystemBackupInDB])
def get_backups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    backup_type: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get list of backups with optional filtering."""
    backup_service = BackupService(db)
    return backup_service.get_backups(skip, limit, status, backup_type)

@router.post("/{backup_id}/verify")
async def verify_backup(
    backup_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Verify a backup's integrity."""
    backup_service = BackupService(db)
    success = await backup_service.verify_backup(backup_id)
    if not success:
        raise HTTPException(status_code=400, detail="Backup verification failed")
    return {"message": "Backup verified successfully"}

@router.post("/schedules/", response_model=BackupScheduleInDB)
async def create_schedule(
    schedule: BackupScheduleCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Create a new backup schedule."""
    backup_service = BackupService(db)
    return await backup_service.create_schedule(schedule, current_user.id)

@router.put("/schedules/{schedule_id}", response_model=BackupScheduleInDB)
async def update_schedule(
    schedule_id: int,
    schedule: BackupScheduleUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Update an existing backup schedule."""
    backup_service = BackupService(db)
    db_schedule = await backup_service.update_schedule(schedule_id, schedule, current_user.id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db_schedule

@router.get("/schedules/{schedule_id}", response_model=BackupScheduleInDB)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get a schedule by ID."""
    backup_service = BackupService(db)
    db_schedule = backup_service.get_schedule(schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db_schedule

@router.get("/schedules/", response_model=List[BackupScheduleInDB])
def get_schedules(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get list of active backup schedules."""
    backup_service = BackupService(db)
    return backup_service.get_active_schedules()

@router.post("/cleanup")
def cleanup_expired_backups(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Clean up expired backups."""
    backup_service = BackupService(db)
    cleaned_count = backup_service.cleanup_expired_backups()
    return {"message": f"Cleaned up {cleaned_count} expired backups"}

@router.get("/statistics", response_model=BackupStatistics)
def get_backup_statistics(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get backup statistics."""
    backup_service = BackupService(db)
    return backup_service.get_backup_statistics() 