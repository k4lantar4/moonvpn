"""
Panel API Routes

This module defines API routes for managing panels and interacting with them.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.schemas import (
    PanelCreate, PanelUpdate, PanelResponse, PanelDetailResponse,
    HealthCheckRequest, HealthCheckResponse, PanelStatsResponse,
    ClientCreate, ClientResponse, User,
    PanelMigrationCreate, PanelMigrationComplete, PanelMigrationResponse,
    PanelDomainCreate, PanelDomainResponse
)
from api.services.panel_service import PanelService
from core.security.auth import get_current_admin_user, get_current_user


router = APIRouter(
    prefix="/panels",
    tags=["panels"],
    responses={404: {"description": "Panel not found"}},
)


@router.get("/", response_model=List[PanelResponse])
async def list_panels(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all panels."""
    service = PanelService(db)
    panels = await service.list_panels(skip=skip, limit=limit)
    return panels


@router.post("/", response_model=PanelResponse, status_code=status.HTTP_201_CREATED)
async def create_panel(
    panel_data: PanelCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new panel."""
    service = PanelService(db)
    panel = await service.create_panel(panel_data.dict())
    return panel


@router.get("/{panel_id}", response_model=PanelDetailResponse)
async def get_panel(
    panel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a panel by ID."""
    service = PanelService(db)
    panel = await service.get_panel(panel_id)
    if panel is None:
        raise HTTPException(status_code=404, detail="Panel not found")
    return panel


@router.put("/{panel_id}", response_model=PanelResponse)
async def update_panel(
    panel_id: int,
    panel_data: PanelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a panel."""
    service = PanelService(db)
    panel = await service.update_panel(panel_id, panel_data.dict(exclude_unset=True))
    if panel is None:
        raise HTTPException(status_code=404, detail="Panel not found")
    return panel


@router.delete("/{panel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_panel(
    panel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a panel."""
    service = PanelService(db)
    success = await service.delete_panel(panel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Panel not found")
    return None


@router.post("/health-check", response_model=List[HealthCheckResponse])
async def check_panels_health(
    request: HealthCheckRequest = HealthCheckRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """Check health of panels.
    
    If panel_id is provided, only check that panel.
    Otherwise, check all active panels.
    """
    service = PanelService(db)
    
    if request.panel_id is not None:
        # Check a specific panel
        panel = await service.get_panel(request.panel_id)
        if panel is None:
            raise HTTPException(status_code=404, detail="Panel not found")
        
        result = await service.check_panel_health(request.panel_id)
        return [{
            "panel_id": panel.id,
            "panel_name": panel.name,
            "health_check": result
        }]
    else:
        # Check all panels in the background
        background_tasks.add_task(service.check_all_panels_health)
        return [{"panel_id": 0, "panel_name": "All Panels", "health_check": {"status": "checking_in_background"}}]


@router.get("/stats", response_model=PanelStatsResponse)
async def get_panel_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get panel statistics."""
    service = PanelService(db)
    panels = await service.list_panels()
    
    # Calculate statistics
    total_panels = len(panels)
    active_panels = sum(1 for p in panels if p.is_active)
    inactive_panels = total_panels - active_panels
    
    healthy_panels = 0
    unhealthy_panels = 0
    last_checked = None
    
    for panel in panels:
        if panel.health_checks:
            latest_check = max(panel.health_checks, key=lambda hc: hc.checked_at)
            if latest_check.status == "healthy":
                healthy_panels += 1
            else:
                unhealthy_panels += 1
            
            if last_checked is None or latest_check.checked_at > last_checked:
                last_checked = latest_check.checked_at
    
    return {
        "total_panels": total_panels,
        "active_panels": active_panels,
        "inactive_panels": inactive_panels,
        "healthy_panels": healthy_panels,
        "unhealthy_panels": unhealthy_panels,
        "last_checked": last_checked
    }


# --- Panel operations ---

@router.get("/{panel_id}/status", response_model=Dict[str, Any])
async def get_panel_status(
    panel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get status of a panel."""
    service = PanelService(db)
    return await service.get_panel_status(panel_id)


@router.get("/{panel_id}/inbounds", response_model=List[Dict[str, Any]])
async def get_panel_inbounds(
    panel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all inbounds from a panel."""
    service = PanelService(db)
    return await service.get_panel_inbounds(panel_id)


@router.get("/{panel_id}/inbounds/{inbound_id}", response_model=Dict[str, Any])
async def get_panel_inbound(
    panel_id: int,
    inbound_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific inbound from a panel."""
    service = PanelService(db)
    return await service.get_panel_inbound(panel_id, inbound_id)


@router.post("/{panel_id}/inbounds/{inbound_id}/clients", response_model=Dict[str, Any])
async def add_client_to_inbound(
    panel_id: int,
    inbound_id: int,
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a client to an inbound on a panel."""
    service = PanelService(db)
    return await service.add_panel_client(panel_id, inbound_id, client_data.dict(exclude_unset=True))


@router.delete("/{panel_id}/inbounds/{inbound_id}/clients/{client_id}", response_model=Dict[str, Any])
async def delete_client_from_inbound(
    panel_id: int,
    inbound_id: int,
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a client from an inbound on a panel."""
    service = PanelService(db)
    return await service.delete_panel_client(panel_id, inbound_id, client_id)


@router.get("/{panel_id}/clients/{email}/traffic", response_model=Dict[str, Any])
async def get_client_traffic(
    panel_id: int,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Get traffic statistics for a client."""
    service = PanelService(db)
    return await service.get_client_traffic(panel_id, email)


@router.post("/{panel_id}/inbounds/{inbound_id}/clients/{email}/reset-traffic", response_model=Dict[str, Any])
async def reset_client_traffic(
    panel_id: int,
    inbound_id: int,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Reset traffic statistics for a client."""
    service = PanelService(db)
    return await service.reset_client_traffic(panel_id, inbound_id, email)


# --- Panel Server Migration Endpoints ---

@router.post("/{panel_id}/start-migration", response_model=PanelMigrationResponse)
async def start_panel_migration(
    panel_id: int,
    migration_data: PanelMigrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Start migration of a panel to a new server.
    
    Migration data should include:
    - new_server_ip: IP of the new server
    - new_url: New panel URL
    - new_geo_location: Optional new geo location
    - new_country_code: Optional new country code
    - reason: Reason for migration
    - notes: Optional notes
    """
    service = PanelService(db)
    result = await service.start_panel_migration(
        panel_id=panel_id,
        new_server_ip=migration_data.new_server_ip,
        new_url=migration_data.new_url,
        new_geo_location=migration_data.new_geo_location,
        new_country_code=migration_data.new_country_code,
        reason=migration_data.reason,
        notes=migration_data.notes,
        performed_by=current_user.id
    )
    return result

@router.get("/{panel_id}/migrations", response_model=List[PanelMigrationResponse])
async def get_panel_migrations(
    panel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get history of panel migrations."""
    service = PanelService(db)
    return await service.get_panel_migrations(panel_id)

@router.get("/migrations/{migration_id}", response_model=PanelMigrationResponse)
async def get_migration_details(
    migration_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get details of a specific panel migration."""
    service = PanelService(db)
    result = await service.get_migration_details(migration_id)
    if not result:
        raise HTTPException(status_code=404, detail="Migration record not found")
    return result

@router.post("/migrations/{migration_id}/complete", response_model=PanelMigrationResponse)
async def complete_panel_migration(
    migration_id: int,
    completion_data: PanelMigrationComplete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Mark a panel migration as completed.
    
    Completion data should include:
    - affected_clients_count: Number of clients affected
    - backup_file: Optional path to backup file
    - notes: Optional additional notes
    """
    service = PanelService(db)
    result = await service.complete_panel_migration(
        migration_id=migration_id,
        affected_clients_count=completion_data.affected_clients_count,
        backup_file=completion_data.backup_file,
        notes=completion_data.notes
    )
    if not result:
        raise HTTPException(status_code=404, detail="Migration record not found")
    return result

@router.post("/{panel_id}/domains", response_model=PanelDomainResponse)
async def add_panel_domain(
    panel_id: int,
    domain_data: PanelDomainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Add a domain to a panel.
    
    Domain data should include:
    - domain: Domain name
    - is_primary: Whether it's the primary domain
    """
    service = PanelService(db)
    result = await service.add_panel_domain(
        panel_id=panel_id,
        domain=domain_data.domain,
        is_primary=domain_data.is_primary
    )
    return result

@router.get("/{panel_id}/domains", response_model=List[PanelDomainResponse])
async def get_panel_domains(
    panel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all domains for a panel."""
    service = PanelService(db)
    return await service.get_panel_domains(panel_id)

@router.delete("/{panel_id}/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_panel_domain(
    panel_id: int,
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a domain from a panel."""
    service = PanelService(db)
    result = await service.delete_panel_domain(panel_id, domain_id)
    if not result:
        raise HTTPException(status_code=404, detail="Domain not found")
    return None 