"""
Scheduler API endpoints for system health monitoring.

This module provides the FastAPI endpoints for managing scheduled recovery actions
and system maintenance tasks.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.services.scheduler import SchedulerService
from app.core.schemas.scheduler import (
    ScheduleParams,
    CronScheduleParams,
    IntervalScheduleParams,
    DateScheduleParams,
    ScheduledAction,
    ScheduleResponse
)

router = APIRouter()

@router.post("/actions/{action_id}/schedule", response_model=ScheduleResponse)
async def schedule_recovery_action(
    action_id: int,
    schedule: ScheduleParams,
    db: Session = Depends(get_db)
):
    """Schedule a recovery action.
    
    Args:
        action_id: ID of the recovery action to schedule
        schedule: Schedule parameters
        db: Database session
        
    Returns:
        ScheduleResponse: Details of the scheduled job
        
    Raises:
        HTTPException: If scheduling fails
    """
    scheduler_service = SchedulerService(db)
    try:
        job_id = await scheduler_service.schedule_recovery_action(
            action_id=action_id,
            schedule_type=schedule.schedule_type,
            schedule_params=schedule.schedule_params
        )
        
        job = scheduler_service.scheduler.get_job(job_id)
        return ScheduleResponse(
            job_id=job_id,
            message="Recovery action scheduled successfully",
            next_run_time=job.next_run_time if job else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/actions/scheduled", response_model=List[ScheduledAction])
async def get_scheduled_actions(
    db: Session = Depends(get_db)
):
    """Get all scheduled recovery actions.
    
    Args:
        db: Database session
        
    Returns:
        List[ScheduledAction]: List of scheduled actions
        
    Raises:
        HTTPException: If retrieval fails
    """
    scheduler_service = SchedulerService(db)
    try:
        return await scheduler_service.get_scheduled_actions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/actions/scheduled/{job_id}", response_model=ScheduleResponse)
async def cancel_scheduled_action(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a scheduled recovery action.
    
    Args:
        job_id: ID of the scheduled job
        db: Database session
        
    Returns:
        ScheduleResponse: Result of the cancellation
        
    Raises:
        HTTPException: If cancellation fails
    """
    scheduler_service = SchedulerService(db)
    try:
        success = await scheduler_service.cancel_scheduled_action(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Scheduled job not found")
        return ScheduleResponse(
            job_id=job_id,
            message="Scheduled job cancelled successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/actions/scheduled/{job_id}/reschedule", response_model=ScheduleResponse)
async def reschedule_action(
    job_id: str,
    schedule: ScheduleParams,
    db: Session = Depends(get_db)
):
    """Reschedule a recovery action.
    
    Args:
        job_id: ID of the scheduled job
        schedule: New schedule parameters
        db: Database session
        
    Returns:
        ScheduleResponse: Details of the rescheduled job
        
    Raises:
        HTTPException: If rescheduling fails
    """
    scheduler_service = SchedulerService(db)
    try:
        success = await scheduler_service.reschedule_action(
            job_id=job_id,
            schedule_type=schedule.schedule_type,
            schedule_params=schedule.schedule_params
        )
        if not success:
            raise HTTPException(status_code=404, detail="Scheduled job not found")
            
        job = scheduler_service.scheduler.get_job(job_id)
        return ScheduleResponse(
            job_id=job_id,
            message="Recovery action rescheduled successfully",
            next_run_time=job.next_run_time if job else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 