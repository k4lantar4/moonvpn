from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.health import HealthStatus, HealthCheck, RecoveryAction
from app.schemas.health import (
    HealthStatusResponse,
    HealthCheckResponse,
    RecoveryActionResponse,
    HealthCheckCreate,
    RecoveryActionCreate
)
from app.services.health import HealthCheckService
from datetime import datetime

router = APIRouter()

@router.get("/status", response_model=List[HealthStatusResponse])
async def get_health_status(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    component: Optional[str] = None
):
    """Get health status of system components"""
    query = db.query(HealthStatus)
    if component:
        query = query.filter(HealthStatus.component == component)
    return query.offset(skip).limit(limit).all()

@router.get("/checks", response_model=List[HealthCheckResponse])
async def get_health_checks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """Get health check history"""
    query = db.query(HealthCheck)
    if status:
        query = query.filter(HealthCheck.overall_status == status)
    return query.offset(skip).limit(limit).all()

@router.get("/recovery-actions", response_model=List[RecoveryActionResponse])
async def get_recovery_actions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    component: Optional[str] = None,
    status: Optional[str] = None
):
    """Get recovery action history"""
    query = db.query(RecoveryAction)
    if component:
        query = query.filter(RecoveryAction.component == component)
    if status:
        query = query.filter(RecoveryAction.status == status)
    return query.offset(skip).limit(limit).all()

@router.post("/checks", response_model=HealthCheckResponse)
async def create_health_check(
    check: HealthCheckCreate,
    db: Session = Depends(deps.get_db)
):
    """Create a new health check"""
    db_check = HealthCheck(**check.dict())
    db.add(db_check)
    db.commit()
    db.refresh(db_check)
    return db_check

@router.post("/recovery-actions", response_model=RecoveryActionResponse)
async def create_recovery_action(
    action: RecoveryActionCreate,
    db: Session = Depends(deps.get_db)
):
    """Create a new recovery action"""
    db_action = RecoveryAction(**action.dict())
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action

@router.get("/current-status", response_model=dict)
async def get_current_health_status(
    db: Session = Depends(deps.get_db)
):
    """Get current health status of all components"""
    health_service = HealthCheckService(db)
    return await health_service.check_health()

@router.post("/recover/{component}")
async def trigger_recovery(
    component: str,
    db: Session = Depends(deps.get_db)
):
    """Manually trigger recovery for a component"""
    health_service = HealthCheckService(db)
    try:
        await health_service.handle_unhealthy_component(
            component,
            HealthStatus(
                status="unhealthy",
                message="Manual recovery triggered",
                timestamp=datetime.utcnow()
            )
        )
        return {"message": f"Recovery triggered for {component}"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recovery failed for {component}: {str(e)}"
        ) 