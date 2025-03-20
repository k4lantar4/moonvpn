"""
Performance tuning API endpoints for MoonVPN.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database.session import get_db
from ...models.performance import TuningType
from ...schemas.performance import (
    TuningConfig,
    TuningCreate,
    TuningRead,
    TuningStatus
)
from ...services.performance_tuning import PerformanceTuningService

router = APIRouter()

@router.post("/database", response_model=str)
async def start_database_tuning(
    config: TuningConfig,
    db: Session = Depends(get_db)
):
    """Start database performance tuning."""
    service = PerformanceTuningService(db)
    tuning_id = await service.start_database_tuning(config)
    return tuning_id

@router.post("/cache", response_model=str)
async def start_cache_tuning(
    config: TuningConfig,
    db: Session = Depends(get_db)
):
    """Start cache performance tuning."""
    service = PerformanceTuningService(db)
    tuning_id = await service.start_cache_tuning(config)
    return tuning_id

@router.post("/network", response_model=str)
async def start_network_tuning(
    config: TuningConfig,
    db: Session = Depends(get_db)
):
    """Start network performance tuning."""
    service = PerformanceTuningService(db)
    tuning_id = await service.start_network_tuning(config)
    return tuning_id

@router.post("/application", response_model=str)
async def start_application_tuning(
    config: TuningConfig,
    db: Session = Depends(get_db)
):
    """Start application performance tuning."""
    service = PerformanceTuningService(db)
    tuning_id = await service.start_application_tuning(config)
    return tuning_id

@router.post("/{tuning_id}/stop", response_model=bool)
async def stop_tuning(
    tuning_id: str,
    db: Session = Depends(get_db)
):
    """Stop a running tuning process."""
    service = PerformanceTuningService(db)
    success = await service.stop_tuning(tuning_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tuning process not found")
    return success

@router.get("/{tuning_id}/status", response_model=TuningStatus)
async def get_tuning_status(
    tuning_id: str,
    db: Session = Depends(get_db)
):
    """Get the status of a tuning process."""
    service = PerformanceTuningService(db)
    status = await service.get_tuning_status(tuning_id)
    if not status:
        raise HTTPException(status_code=404, detail="Tuning process not found")
    return status

@router.get("/{tuning_id}", response_model=TuningRead)
async def get_tuning(
    tuning_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a tuning process."""
    service = PerformanceTuningService(db)
    tuning = await service.get_tuning(tuning_id)
    if not tuning:
        raise HTTPException(status_code=404, detail="Tuning process not found")
    return tuning

@router.get("/", response_model=List[TuningRead])
async def list_tunings(
    type: TuningType = None,
    db: Session = Depends(get_db)
):
    """List all tuning processes."""
    service = PerformanceTuningService(db)
    tunings = await service.list_tunings(type)
    return tunings 