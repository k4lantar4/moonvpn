"""
VPN account endpoints for VPN account management.
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.security import get_current_active_user, get_current_admin_user
from core.database import get_db
from core.database.models import User
from core.schemas.vpn import VPNAccountCreate, VPNAccountResponse, VPNAccountUpdate
from core.services.vpn_service import VPNService

router = APIRouter()


@router.get("/", response_model=List[VPNAccountResponse])
async def read_vpn_accounts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    server_id: Optional[int] = None,
    location_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    is_trial: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve VPN accounts with filtering options.
    
    Args:
        db: Database session
        skip: Number of accounts to skip for pagination
        limit: Maximum number of accounts to return
        user_id: Filter by user ID
        server_id: Filter by server ID
        location_id: Filter by location ID
        is_active: Filter by active status
        is_trial: Filter by trial status
        current_user: Current authenticated user
        
    Returns:
        List of VPN accounts
    """
    # Build query with filters
    query = db.query(db.VPNAccount)
    
    # Apply filters
    if user_id is not None:
        # Regular users can only see their own accounts
        if not current_user.is_admin and user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        query = query.filter(db.VPNAccount.user_id == user_id)
    elif not current_user.is_admin:
        # Non-admins can only see their own accounts
        query = query.filter(db.VPNAccount.user_id == current_user.id)
    
    if server_id is not None:
        query = query.filter(db.VPNAccount.server_id == server_id)
    
    if is_active is not None:
        query = query.filter(db.VPNAccount.is_active.is_(is_active))
    
    if is_trial is not None:
        query = query.filter(db.VPNAccount.is_trial.is_(is_trial))
    
    # Apply pagination
    vpn_accounts = query.offset(skip).limit(limit).all()
    
    return vpn_accounts


@router.post("/", response_model=VPNAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_vpn_account(
    *,
    db: Session = Depends(get_db),
    account_in: VPNAccountCreate,
    user_id: Optional[int] = None,
    server_id: Optional[int] = None,
    location_id: Optional[int] = None,
    vpn_service: VPNService = Depends(),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new VPN account.
    
    Args:
        db: Database session
        account_in: VPN account creation data
        user_id: User ID (required for admins creating accounts for other users)
        server_id: Optional specific server ID to use
        location_id: Optional location ID for server selection
        vpn_service: VPN service dependency
        current_user: Current authenticated user
        
    Returns:
        Created VPN account
        
    Raises:
        HTTPException: If parameters are invalid
    """
    # Determine for which user to create the account
    target_user_id = user_id if user_id and current_user.is_admin else current_user.id
    
    # Ensure admins can create accounts for others
    if user_id and not current_user.is_admin and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create account for another user",
        )
    
    # Create the account
    try:
        vpn_account = await vpn_service.create_account(
            user_id=target_user_id,
            account_data=account_in,
            server_id=server_id,
            location_id=location_id,
        )
        return vpn_account
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating VPN account: {str(e)}",
        )


@router.get("/{account_id}", response_model=VPNAccountResponse)
async def read_vpn_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get VPN account by ID.
    
    Args:
        account_id: VPN account ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        VPN account
        
    Raises:
        HTTPException: If account not found or access denied
    """
    # Get the account
    vpn_account = db.query(db.VPNAccount).filter(db.VPNAccount.id == account_id).first()
    if not vpn_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found",
        )
    
    # Check permissions
    if not current_user.is_admin and vpn_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return vpn_account


@router.put("/{account_id}", response_model=VPNAccountResponse)
async def update_vpn_account(
    *,
    account_id: int,
    account_in: VPNAccountUpdate,
    vpn_service: VPNService = Depends(),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a VPN account.
    
    Args:
        account_id: VPN account ID
        account_in: VPN account update data
        vpn_service: VPN service dependency
        current_user: Current authenticated user
        
    Returns:
        Updated VPN account
        
    Raises:
        HTTPException: If account not found or access denied
    """
    # Get the account to check permissions
    db = vpn_service.db
    vpn_account = db.query(db.VPNAccount).filter(db.VPNAccount.id == account_id).first()
    if not vpn_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found",
        )
    
    # Check permissions
    if not current_user.is_admin and vpn_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Update the account
    try:
        updated_account = await vpn_service.update_account(
            account_id=account_id,
            update_data=account_in,
        )
        return updated_account
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating VPN account: {str(e)}",
        )


@router.delete("/{account_id}", response_model=bool)
async def delete_vpn_account(
    *,
    account_id: int,
    vpn_service: VPNService = Depends(),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a VPN account.
    
    Args:
        account_id: VPN account ID
        vpn_service: VPN service dependency
        current_user: Current authenticated user
        
    Returns:
        True if account was deleted
        
    Raises:
        HTTPException: If account not found or access denied
    """
    # Get the account to check permissions
    db = vpn_service.db
    vpn_account = db.query(db.VPNAccount).filter(db.VPNAccount.id == account_id).first()
    if not vpn_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found",
        )
    
    # Only admins can delete accounts
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Delete the account
    try:
        result = await vpn_service.delete_account(account_id=account_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting VPN account: {str(e)}",
        )


@router.post("/{account_id}/sync", response_model=VPNAccountResponse)
async def sync_vpn_account(
    *,
    account_id: int,
    vpn_service: VPNService = Depends(),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Sync VPN account statistics from panel.
    
    Args:
        account_id: VPN account ID
        vpn_service: VPN service dependency
        current_user: Current authenticated user
        
    Returns:
        Updated VPN account
        
    Raises:
        HTTPException: If account not found or access denied
    """
    # Get the account to check permissions
    db = vpn_service.db
    vpn_account = db.query(db.VPNAccount).filter(db.VPNAccount.id == account_id).first()
    if not vpn_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN account not found",
        )
    
    # Check permissions
    if not current_user.is_admin and vpn_account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Sync the account
    try:
        synced_account = await vpn_service.sync_account_traffic(account_id=account_id)
        return synced_account
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing VPN account: {str(e)}",
        ) 