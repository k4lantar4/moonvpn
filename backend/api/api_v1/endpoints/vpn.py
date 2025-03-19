"""
VPN endpoints.

This module provides API endpoints for VPN management, including servers,
locations, and user VPN accounts.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, get_current_active_superuser
from app.db.session import get_db
from app.models.user.user import User
from app.models.vpn.location import Location
from app.models.vpn.server import Server
from app.models.vpn.vpn_account import VPNAccount
from app.schemas.vpn.location import LocationCreate, LocationResponse, LocationUpdate
from app.schemas.vpn.server import ServerCreate, ServerResponse, ServerUpdate
from app.schemas.vpn.vpn_account import VPNAccountCreate, VPNAccountResponse, VPNAccountUpdate
from app.services.panel.api import PanelClient

router = APIRouter()


# VPN Accounts endpoints
@router.get("/accounts/me", response_model=List[VPNAccountResponse])
def read_user_vpn_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[VPNAccountResponse]:
    """
    Get current user VPN accounts.
    
    Retrieve all VPN accounts belonging to the current user.
    """
    accounts = db.query(VPNAccount).filter(VPNAccount.user_id == current_user.id).all()
    return [VPNAccountResponse.from_orm(account) for account in accounts]


@router.post("/accounts", response_model=VPNAccountResponse)
def create_vpn_account(
    account_in: VPNAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VPNAccountResponse:
    """
    Create VPN account.
    
    Create a new VPN account for the current user.
    """
    # Check server exists
    server = db.query(Server).filter(Server.id == account_in.server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    # Create VPN account on the panel
    panel_client = PanelClient(
        host=server.host,
        port=server.api_port,
        username=server.api_username,
        password=server.api_password,
    )
    
    # Generate a unique email or username for the VPN account
    email = f"{current_user.email}-{account_in.name}"
    
    try:
        # Create account on the panel
        panel_account = panel_client.create_account(
            email=email,
            password=account_in.password,
            traffic_limit=account_in.traffic_limit,
            expiry_time=account_in.expiry_time,
        )
        
        # Create account in database
        db_account = VPNAccount(
            user_id=current_user.id,
            server_id=server.id,
            name=account_in.name,
            username=email,
            password=account_in.password,
            status="active",
            traffic_limit=account_in.traffic_limit,
            data_used=0,
            expiry_date=account_in.expiry_time,
            panel_id=panel_account.get("id"),
        )
        
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        
        return VPNAccountResponse.from_orm(db_account)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create VPN account: {str(e)}",
        )


@router.get("/accounts/{account_id}", response_model=VPNAccountResponse)
def read_vpn_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VPNAccountResponse:
    """
    Get VPN account.
    
    Retrieve a specific VPN account by ID.
    """
    account = db.query(VPNAccount).filter(
        VPNAccount.id == account_id,
        VPNAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found",
        )
    
    return VPNAccountResponse.from_orm(account)


@router.put("/accounts/{account_id}", response_model=VPNAccountResponse)
def update_vpn_account(
    account_id: int,
    account_in: VPNAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VPNAccountResponse:
    """
    Update VPN account.
    
    Update a specific VPN account by ID.
    """
    account = db.query(VPNAccount).filter(
        VPNAccount.id == account_id,
        VPNAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found",
        )
    
    # Update account on panel if needed
    if account_in.password or account_in.traffic_limit or account_in.expiry_time:
        server = db.query(Server).filter(Server.id == account.server_id).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server for this account not found",
            )
        
        panel_client = PanelClient(
            host=server.host,
            port=server.api_port,
            username=server.api_username,
            password=server.api_password,
        )
        
        try:
            # Update on panel
            panel_client.update_account(
                account_id=account.panel_id,
                password=account_in.password,
                traffic_limit=account_in.traffic_limit,
                expiry_time=account_in.expiry_time,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update VPN account on panel: {str(e)}",
            )
    
    # Update account in database
    for key, value in account_in.dict(exclude_unset=True).items():
        if hasattr(account, key):
            setattr(account, key, value)
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return VPNAccountResponse.from_orm(account)


@router.delete("/accounts/{account_id}", response_model=VPNAccountResponse)
def delete_vpn_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VPNAccountResponse:
    """
    Delete VPN account.
    
    Delete a specific VPN account by ID.
    """
    account = db.query(VPNAccount).filter(
        VPNAccount.id == account_id,
        VPNAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found",
        )
    
    # Delete from panel
    server = db.query(Server).filter(Server.id == account.server_id).first()
    if server:
        panel_client = PanelClient(
            host=server.host,
            port=server.api_port,
            username=server.api_username,
            password=server.api_password,
        )
        
        try:
            panel_client.delete_account(account_id=account.panel_id)
        except Exception as e:
            # Log the error but continue with deletion from database
            print(f"Error deleting account from panel: {str(e)}")
    
    # Instead of hard delete, we mark the account as inactive
    account.status = "inactive"
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return VPNAccountResponse.from_orm(account)


# Server endpoints (admin only)
@router.get("/servers", response_model=List[ServerResponse])
def read_servers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[ServerResponse]:
    """
    List servers.
    
    Retrieve a list of available VPN servers.
    """
    servers = db.query(Server).filter(Server.is_active == True).offset(skip).limit(limit).all()
    return [ServerResponse.from_orm(server) for server in servers]


@router.get("/servers/{server_id}", response_model=ServerResponse)
def read_server(
    server_id: int,
    db: Session = Depends(get_db),
) -> ServerResponse:
    """
    Get server.
    
    Retrieve a specific server by ID.
    """
    server = db.query(Server).filter(
        Server.id == server_id,
        Server.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    return ServerResponse.from_orm(server)


@router.post("/servers", response_model=ServerResponse)
def create_server(
    server_in: ServerCreate,
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> ServerResponse:
    """
    Create server.
    
    Create a new VPN server (admin only).
    """
    # Check if location exists
    location = db.query(Location).filter(Location.id == server_in.location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    # Create server in database
    db_server = Server(
        name=server_in.name,
        host=server_in.host,
        location_id=server_in.location_id,
        ip_address=server_in.ip_address,
        api_port=server_in.api_port,
        api_username=server_in.api_username,
        api_password=server_in.api_password,
        status="active",
        is_active=True,
    )
    
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    return ServerResponse.from_orm(db_server)


@router.put("/servers/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int,
    server_in: ServerUpdate,
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> ServerResponse:
    """
    Update server.
    
    Update a specific server by ID (admin only).
    """
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    # Update location if provided
    if server_in.location_id:
        location = db.query(Location).filter(Location.id == server_in.location_id).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found",
            )
    
    # Update server attributes
    for key, value in server_in.dict(exclude_unset=True).items():
        if hasattr(server, key):
            setattr(server, key, value)
    
    db.add(server)
    db.commit()
    db.refresh(server)
    
    return ServerResponse.from_orm(server)


@router.delete("/servers/{server_id}", response_model=ServerResponse)
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> ServerResponse:
    """
    Delete server.
    
    Delete a specific server by ID (admin only).
    """
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        )
    
    # Instead of hard delete, we mark the server as inactive
    server.is_active = False
    server.status = "inactive"
    
    db.add(server)
    db.commit()
    db.refresh(server)
    
    return ServerResponse.from_orm(server)


# Location endpoints (mostly admin only)
@router.get("/locations", response_model=List[LocationResponse])
def read_locations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[LocationResponse]:
    """
    List locations.
    
    Retrieve a list of available VPN server locations.
    """
    locations = db.query(Location).filter(Location.is_active == True).offset(skip).limit(limit).all()
    return [LocationResponse.from_orm(location) for location in locations]


@router.get("/locations/{location_id}", response_model=LocationResponse)
def read_location(
    location_id: int,
    db: Session = Depends(get_db),
) -> LocationResponse:
    """
    Get location.
    
    Retrieve a specific location by ID.
    """
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.is_active == True
    ).first()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    return LocationResponse.from_orm(location)


@router.post("/locations", response_model=LocationResponse)
def create_location(
    location_in: LocationCreate,
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> LocationResponse:
    """
    Create location.
    
    Create a new VPN server location (admin only).
    """
    # Create location in database
    db_location = Location(
        name=location_in.name,
        country=location_in.country,
        country_code=location_in.country_code,
        city=location_in.city,
        flag_emoji=location_in.flag_emoji,
        is_active=True,
    )
    
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return LocationResponse.from_orm(db_location)


@router.put("/locations/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    location_in: LocationUpdate,
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> LocationResponse:
    """
    Update location.
    
    Update a specific location by ID (admin only).
    """
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    # Update location attributes
    for key, value in location_in.dict(exclude_unset=True).items():
        if hasattr(location, key):
            setattr(location, key, value)
    
    db.add(location)
    db.commit()
    db.refresh(location)
    
    return LocationResponse.from_orm(location)


@router.delete("/locations/{location_id}", response_model=LocationResponse)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_active_superuser),
) -> LocationResponse:
    """
    Delete location.
    
    Delete a specific location by ID (admin only).
    """
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    
    # Check if there are any active servers in this location
    servers = db.query(Server).filter(
        Server.location_id == location_id,
        Server.is_active == True
    ).count()
    
    if servers > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete location with active servers",
        )
    
    # Instead of hard delete, we mark the location as inactive
    location.is_active = False
    
    db.add(location)
    db.commit()
    db.refresh(location)
    
    return LocationResponse.from_orm(location) 