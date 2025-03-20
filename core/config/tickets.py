"""
Ticket API endpoints for MoonVPN.

This module contains the FastAPI router for ticket-related endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.db.repositories.factory import RepositoryFactory
from app.services.ticket import TicketService
from app.models.ticket import Ticket, TicketCreate, TicketUpdate, TicketResponse
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=List[TicketResponse])
async def get_current_user_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TicketResponse]:
    """Get current user's tickets."""
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    tickets = await service.get_by_user_id(current_user.id)
    
    return [TicketResponse.from_orm(ticket) for ticket in tickets]

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Get ticket by ID."""
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    ticket = await service.get_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if not current_user.is_admin and ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return TicketResponse.from_orm(ticket)

@router.get("/open", response_model=List[TicketResponse])
async def get_open_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TicketResponse]:
    """Get all open tickets (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    tickets = await service.get_open_tickets()
    
    return [TicketResponse.from_orm(ticket) for ticket in tickets]

@router.get("/status/{status}", response_model=List[TicketResponse])
async def get_tickets_by_status(
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TicketResponse]:
    """Get all tickets with a specific status (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    tickets = await service.get_tickets_by_status(status)
    
    return [TicketResponse.from_orm(ticket) for ticket in tickets]

@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Create a new ticket."""
    # Set the user_id to the current user
    ticket_data.user_id = current_user.id
    
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    ticket = await service.create(ticket_data)
    
    return TicketResponse.from_orm(ticket)

@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Update a ticket."""
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    ticket = await service.get_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if not current_user.is_admin and ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    updated_ticket = await service.update(ticket_id, ticket_data)
    return TicketResponse.from_orm(updated_ticket)

@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a ticket (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    success = await service.delete(ticket_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return {"message": "Ticket deleted successfully"}

@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    admin_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Assign a ticket to an admin (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    ticket = await service.assign_ticket(ticket_id, admin_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return TicketResponse.from_orm(ticket)

@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """Close a ticket (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    ticket = await service.close_ticket(ticket_id, current_user.id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return TicketResponse.from_orm(ticket)

@router.get("/{ticket_id}/stats")
async def get_ticket_stats(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get ticket statistics."""
    factory = RepositoryFactory(db)
    service = TicketService(factory.ticket_repository, factory.user_repository)
    ticket = await service.get_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if not current_user.is_admin and ticket.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await service.get_ticket_stats(ticket.user_id) 