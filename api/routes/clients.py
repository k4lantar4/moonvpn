"""
Client API Routes

This module defines API routes for managing clients.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security.auth import get_current_user, get_current_admin_user
from api.models import User
from api.schemas import (
    ClientBase, ClientCreate, ClientResponse, ClientDetailResponse, 
    ClientConfigResponse, ClientTrafficUpdate, ClientLocationChange,
    MessageResponse
)
from api.services.client_service import ClientService
from api.dependencies import get_client_service

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    responses={404: {"description": "Client not found"}},
)


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    skip: int = 0, 
    limit: int = 100,
    user_id: Optional[int] = None,
    panel_id: Optional[int] = None,
    location_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List clients with optional filtering."""
    service = ClientService(db)
    # Implement list method in service
    return []


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new client."""
    service = ClientService(db)
    client = await service.create_client(client_data.dict())
    return client


@router.get("/{client_id}", response_model=ClientDetailResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a client by ID."""
    service = ClientService(db)
    client = await service.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check permissions - user can only access their own clients
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this client")
    
    return client


@router.get("/{client_id}/config", response_model=ClientConfigResponse)
async def get_client_config(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get client configuration details including connection information."""
    service = ClientService(db)
    client = await service.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check permissions - user can only access their own clients
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this client")
    
    config = await service.get_client_config(client_id)
    return config


@router.get("/by-remark/{remark}", response_model=ClientDetailResponse)
async def get_client_by_remark(
    remark: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get a client by remark (admin only)."""
    service = ClientService(db)
    client = await service.get_client_by_remark(remark)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return client


@router.get("/by-remark/{remark}/config", response_model=ClientConfigResponse)
async def get_client_config_by_remark(
    remark: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get client configuration by remark (admin only)."""
    service = ClientService(db)
    client = await service.get_client_by_remark(remark)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    config = await service.get_client_config(client.id)
    return config


@router.post("/{client_id}/update-traffic", response_model=ClientResponse)
async def update_client_traffic(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update client traffic usage from panel."""
    service = ClientService(db)
    client = await service.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check permissions - user can only update their own clients
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this client")
    
    updated_client = await service.update_client_traffic(client_id)
    return updated_client


@router.post("/{client_id}/reset-traffic", response_model=ClientResponse)
async def reset_client_traffic(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Reset client traffic (admin only)."""
    service = ClientService(db)
    updated_client = await service.reset_client_traffic(client_id)
    if updated_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return updated_client


@router.delete("/{client_id}", response_model=MessageResponse)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    # ... existing method body ...


@router.post("/{client_id}/change-location", response_model=ClientResponse)
async def change_client_location(
    client_id: int,
    data: ClientLocationChange,
    current_user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    """
    تغییر لوکیشن سرویس کاربر با حفظ اطلاعات حساب

    این اندپوینت امکان جابجایی سرویس را از یک لوکیشن به لوکیشن دیگر فراهم می‌کند
    با حفظ ترافیک و زمان باقیمانده و تاریخچه تغییرات
    """
    # بررسی مجوز (ادمین یا مالک سرویس بودن)
    client = await client_service.get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="سرویس یافت نشد"
        )
    
    # کاربران عادی فقط می‌توانند سرویس‌های خودشان را تغییر دهند
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما مجوز تغییر این سرویس را ندارید"
        )
    
    # تغییر لوکیشن با استفاده از سرویس مربوطه
    client = await client_service.change_location(
        client_id=client_id,
        new_location_id=data.new_location_id,
        reason=data.reason,
        performed_by=current_user.id,
        force=current_user.role == "admin" and data.force
    )
    
    return client


@router.get("/{client_id}/migration-history", response_model=List[Dict[str, Any]])
async def get_client_migration_history(
    client_id: int,
    current_user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service)
):
    """
    دریافت تاریخچه تغییرات لوکیشن کلاینت

    این اندپوینت تاریخچه کامل تغییرات لوکیشن یک سرویس را برمی‌گرداند
    شامل زمان تغییر، لوکیشن قدیم و جدید، و ریمارک‌های قدیم و جدید
    """
    # بررسی مجوز (ادمین یا مالک سرویس بودن)
    client = await client_service.get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="سرویس یافت نشد"
        )
    
    # کاربران عادی فقط می‌توانند تاریخچه سرویس‌های خودشان را ببینند
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما مجوز مشاهده تاریخچه این سرویس را ندارید"
        )
    
    # دریافت تاریخچه تغییرات
    migrations = await client_service.get_client_migrations(client_id)
    
    return migrations 