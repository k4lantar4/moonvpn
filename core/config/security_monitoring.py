"""
Security monitoring API endpoints.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, WebSocket, Query
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.security_monitoring import SecurityMonitoringService
from ...core.auth import get_current_admin_user

router = APIRouter()

@router.websocket("/ws/security")
async def security_monitoring_ws(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time security monitoring."""
    monitoring_service = SecurityMonitoringService(db)
    await monitoring_service.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            # Process any client messages if needed
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await monitoring_service.disconnect(websocket)

@router.get("/security/stats")
async def get_security_stats(
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get security statistics for the dashboard."""
    monitoring_service = SecurityMonitoringService(db)
    return await monitoring_service.get_security_stats()

@router.get("/security/events")
async def get_security_events(
    severity: Optional[str] = Query(None, description="Filter by event severity"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    limit: int = Query(100, description="Maximum number of events to return"),
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get filtered security event history."""
    monitoring_service = SecurityMonitoringService(db)
    return await monitoring_service.get_event_history(
        severity=severity,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    ) 