"""
Recovery API endpoints for system health monitoring.

This module provides the FastAPI endpoints for managing automated recovery actions
in the system.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models.recovery import RecoveryAction, RecoveryStatus
from app.core.schemas.recovery import RecoveryActionCreate, RecoveryActionUpdate, RecoveryAction as RecoveryActionSchema
from app.core.services.recovery import RecoveryService

router = APIRouter()

@router.post("/actions/", response_model=RecoveryActionSchema)
async def create_recovery_action(
    action: RecoveryActionCreate,
    db: Session = Depends(get_db)
):
    """Create a new recovery action.
    
    Args:
        action: The recovery action to create
        db: Database session
        
    Returns:
        RecoveryAction: The created recovery action
    """
    recovery_service = RecoveryService(db)
    return await recovery_service.create_recovery_action(
        component=action.component,
        failure_type=action.failure_type,
        strategy=action.strategy,
        parameters=action.parameters
    )

@router.get("/actions/", response_model=List[RecoveryActionSchema])
async def get_recovery_actions(
    component: Optional[str] = Query(None, description="Filter by component"),
    status: Optional[RecoveryStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of actions to return"),
    db: Session = Depends(get_db)
):
    """Get recovery actions with optional filtering.
    
    Args:
        component: Filter by component
        status: Filter by status
        limit: Maximum number of actions to return
        db: Database session
        
    Returns:
        List[RecoveryAction]: List of matching recovery actions
    """
    recovery_service = RecoveryService(db)
    return recovery_service.get_recovery_actions(component, status, limit)

@router.get("/actions/{action_id}", response_model=RecoveryActionSchema)
async def get_recovery_action(
    action_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific recovery action.
    
    Args:
        action_id: ID of the recovery action
        db: Database session
        
    Returns:
        RecoveryAction: The recovery action if found
        
    Raises:
        HTTPException: If the recovery action is not found
    """
    recovery_service = RecoveryService(db)
    action = recovery_service.get_recovery_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Recovery action not found")
    return action

@router.put("/actions/{action_id}", response_model=RecoveryActionSchema)
async def update_recovery_action(
    action_id: int,
    update_data: RecoveryActionUpdate,
    db: Session = Depends(get_db)
):
    """Update a recovery action.
    
    Args:
        action_id: ID of the recovery action
        update_data: Data to update
        db: Database session
        
    Returns:
        RecoveryAction: The updated recovery action
        
    Raises:
        HTTPException: If the recovery action is not found
    """
    recovery_service = RecoveryService(db)
    try:
        return recovery_service.update_recovery_action(action_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/actions/{action_id}/execute", response_model=RecoveryActionSchema)
async def execute_recovery_action(
    action_id: int,
    db: Session = Depends(get_db)
):
    """Execute a recovery action.
    
    Args:
        action_id: ID of the recovery action to execute
        db: Database session
        
    Returns:
        RecoveryAction: The updated recovery action
        
    Raises:
        HTTPException: If the recovery action is not found or execution fails
    """
    recovery_service = RecoveryService(db)
    try:
        return await recovery_service.execute_recovery_action(action_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 