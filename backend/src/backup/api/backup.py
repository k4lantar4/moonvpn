from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models.backup import SystemBackup, BackupSchedule
from app.schemas.backup import (
    SystemBackupCreate,
    SystemBackupResponse,
    BackupScheduleCreate,
    BackupScheduleResponse,
    BackupRestoreRequest
)
from app.services.backup import BackupService

router = APIRouter()

@router.get("/backups", response_model=List[SystemBackupResponse])
async def list_backups(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    backup_type: Optional[str] = None,
    status: Optional[str] = None
):
    """List all system backups with optional filtering"""
    query = db.query(SystemBackup)
    
    if backup_type:
        query = query.filter(SystemBackup.type == backup_type)
    if status:
        query = query.filter(SystemBackup.status == status)
    
    return query.offset(skip).limit(limit).all()

@router.post("/backups", response_model=SystemBackupResponse)
async def create_backup(
    backup: SystemBackupCreate,
    db: Session = Depends(deps.get_db)
):
    """Create a new system backup"""
    backup_service = BackupService(db)
    return await backup_service.create_backup(backup.type)

@router.get("/backups/{backup_id}", response_model=SystemBackupResponse)
async def get_backup(
    backup_id: int,
    db: Session = Depends(deps.get_db)
):
    """Get a specific backup by ID"""
    backup = db.query(SystemBackup).filter(SystemBackup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return backup

@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: int,
    restore_request: BackupRestoreRequest,
    db: Session = Depends(deps.get_db)
):
    """Restore system from a backup"""
    backup_service = BackupService(db)
    try:
        success = await backup_service.restore_backup(backup_id)
        if success:
            return {"message": "Backup restored successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to restore backup")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/backups/{backup_id}")
async def delete_backup(
    backup_id: int,
    db: Session = Depends(deps.get_db)
):
    """Delete a backup"""
    backup = db.query(SystemBackup).filter(SystemBackup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    try:
        # Delete backup files
        if backup.path:
            import shutil
            import os
            if os.path.exists(backup.path):
                shutil.rmtree(backup.path)
        
        # Delete backup record
        db.delete(backup)
        db.commit()
        
        return {"message": "Backup deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules", response_model=List[BackupScheduleResponse])
async def list_schedules(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
):
    """List all backup schedules with optional filtering"""
    query = db.query(BackupSchedule)
    
    if is_active is not None:
        query = query.filter(BackupSchedule.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

@router.post("/schedules", response_model=BackupScheduleResponse)
async def create_schedule(
    schedule: BackupScheduleCreate,
    db: Session = Depends(deps.get_db)
):
    """Create a new backup schedule"""
    db_schedule = BackupSchedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/schedules/{schedule_id}", response_model=BackupScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(deps.get_db)
):
    """Get a specific schedule by ID"""
    schedule = db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@router.put("/schedules/{schedule_id}", response_model=BackupScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule: BackupScheduleCreate,
    db: Session = Depends(deps.get_db)
):
    """Update a backup schedule"""
    db_schedule = db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    for key, value in schedule.dict().items():
        setattr(db_schedule, key, value)
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(deps.get_db)
):
    """Delete a backup schedule"""
    schedule = db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}

@router.post("/schedules/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: int,
    db: Session = Depends(deps.get_db)
):
    """Toggle a backup schedule active status"""
    schedule = db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.is_active = not schedule.is_active
    db.commit()
    return {"message": f"Schedule {'activated' if schedule.is_active else 'deactivated'} successfully"} 