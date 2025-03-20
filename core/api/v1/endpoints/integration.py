"""
Integration API endpoints for managing system integrations.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....database.session import get_db
from ....services.integration_manager import IntegrationManager
from ....core.security import get_current_user
from ....models.user import User

router = APIRouter()

@router.get("/status", response_model=Dict[str, Any])
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the overall status of the system."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    return await integration_manager.get_system_status()

@router.get("/health", response_model=bool)
async def check_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if the entire system is healthy."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    return await integration_manager.check_system_health()

@router.post("/components/{component}/restart", response_model=bool)
async def restart_component(
    component: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restart a specific component."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    success = await integration_manager.restart_component(component)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to restart component {component}")
    return success

@router.post("/databases/backup", response_model=bool)
async def backup_database(
    source_db: str,
    target_db: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Backup data from one database to another."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    success = await integration_manager.backup_database(source_db, target_db)
    if not success:
        raise HTTPException(status_code=500, 
                          detail=f"Failed to backup database from {source_db} to {target_db}")
    return success

@router.post("/databases/sync", response_model=bool)
async def sync_databases(
    source_db: str,
    target_db: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Synchronize data between two databases."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    success = await integration_manager.sync_databases(source_db, target_db)
    if not success:
        raise HTTPException(status_code=500, 
                          detail=f"Failed to sync databases {source_db} and {target_db}")
    return success

@router.post("/security/authenticate", response_model=Dict[str, Any])
async def authenticate_user(
    credentials: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Authenticate a user using the security service."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    result = await integration_manager.authenticate_user(credentials)
    if not result:
        raise HTTPException(status_code=401, detail="Authentication failed")
    return result

@router.post("/security/authorize", response_model=bool)
async def authorize_access(
    user_id: int,
    resource: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Authorize user access to a resource."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    return await integration_manager.authorize_access(user_id, resource)

@router.post("/security/encrypt", response_model=str)
async def encrypt_data(
    data: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Encrypt data using the security service."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    result = await integration_manager.encrypt_data(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to encrypt data")
    return result

@router.post("/security/decrypt", response_model=str)
async def decrypt_data(
    encrypted_data: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Decrypt data using the security service."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    result = await integration_manager.decrypt_data(encrypted_data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to decrypt data")
    return result

@router.post("/security/events", response_model=bool)
async def log_security_event(
    event: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log a security event using the security service."""
    integration_manager = IntegrationManager(db)
    await integration_manager.initialize()
    success = await integration_manager.log_security_event(event)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to log security event")
    return success 