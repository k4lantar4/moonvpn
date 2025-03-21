"""
VPN endpoints for handling VPN-related operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.database.models import User
from core.schemas.vpn import (
    Server, ServerCreate, ServerUpdate,
    VPNAccount, VPNAccountCreate, VPNAccountUpdate,
    VPNAccountList, VPNAccountStats
)
from core.services.vpn import VPNService
from core.services.auth import get_current_user

router = APIRouter()

# Server endpoints
@router.get("/servers", response_model=List[Server])
async def get_servers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    location: Optional[str] = None,
    protocol: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of servers."""
    vpn_service = VPNService(db)
    return vpn_service.get_servers(skip, limit, search, status, is_active, location, protocol)

@router.post("/servers", response_model=Server)
async def create_server(
    data: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new server (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    vpn_service = VPNService(db)
    return vpn_service.create_server(data)

@router.get("/servers/{server_id}", response_model=Server)
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get server by ID."""
    vpn_service = VPNService(db)
    server = vpn_service.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    return server

@router.put("/servers/{server_id}", response_model=Server)
async def update_server(
    server_id: int,
    data: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update server information (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    vpn_service = VPNService(db)
    return vpn_service.update_server(server_id, data)

@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a server (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    vpn_service = VPNService(db)
    vpn_service.delete_server(server_id)
    return {"message": "Server deleted successfully"}

# VPN Account endpoints
@router.get("/accounts", response_model=VPNAccountList)
async def get_user_vpn_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of user's VPN accounts."""
    vpn_service = VPNService(db)
    accounts = vpn_service.get_user_vpn_accounts(
        current_user.id, skip, limit, status, is_active
    )
    total = vpn_service.get_user_vpn_accounts_count(
        current_user.id, status, is_active
    )
    
    return VPNAccountList(
        total=total,
        accounts=accounts,
        page=skip // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@router.post("/accounts", response_model=VPNAccount)
async def create_vpn_account(
    data: VPNAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new VPN account (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    vpn_service = VPNService(db)
    return vpn_service.create_vpn_account(data)

@router.get("/accounts/{account_id}", response_model=VPNAccount)
async def get_vpn_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get VPN account by ID."""
    vpn_service = VPNService(db)
    account = vpn_service.get_vpn_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found"
        )
    
    # Check if user has access to this account
    if not current_user.is_superuser and account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return account

@router.put("/accounts/{account_id}", response_model=VPNAccount)
async def update_vpn_account(
    account_id: int,
    data: VPNAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update VPN account information."""
    vpn_service = VPNService(db)
    account = vpn_service.get_vpn_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found"
        )
    
    # Check if user has access to this account
    if not current_user.is_superuser and account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return vpn_service.update_vpn_account(account_id, data)

@router.delete("/accounts/{account_id}")
async def delete_vpn_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a VPN account (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    vpn_service = VPNService(db)
    vpn_service.delete_vpn_account(account_id)
    return {"message": "VPN account deleted successfully"}

@router.get("/accounts/{account_id}/stats", response_model=VPNAccountStats)
async def get_vpn_account_stats(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get VPN account statistics."""
    vpn_service = VPNService(db)
    account = vpn_service.get_vpn_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found"
        )
    
    # Check if user has access to this account
    if not current_user.is_superuser and account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return vpn_service.get_vpn_account_stats(account_id)

@router.post("/accounts/{account_id}/connect")
async def connect_vpn(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect to VPN."""
    vpn_service = VPNService(db)
    account = vpn_service.get_vpn_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found"
        )
    
    # Check if user has access to this account
    if not current_user.is_superuser and account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # TODO: Implement actual VPN connection logic
    return {"message": "VPN connection initiated"}

@router.post("/accounts/{account_id}/disconnect")
async def disconnect_vpn(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect from VPN."""
    vpn_service = VPNService(db)
    account = vpn_service.get_vpn_account(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found"
        )
    
    # Check if user has access to this account
    if not current_user.is_superuser and account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # TODO: Implement actual VPN disconnection logic
    return {"message": "VPN disconnection initiated"} 