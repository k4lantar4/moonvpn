"""
Ticket service for MoonVPN.

This module contains the ticket service implementation using the repository pattern.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status

from app.db.repositories.ticket import TicketRepository
from app.db.repositories.user import UserRepository
from app.models.ticket import Ticket, TicketCreate, TicketUpdate

class TicketService:
    """Ticket service class."""
    
    def __init__(
        self,
        ticket_repository: TicketRepository,
        user_repository: UserRepository
    ):
        """Initialize service."""
        self.ticket_repository = ticket_repository
        self.user_repository = user_repository
    
    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Get a ticket by ID."""
        return await self.ticket_repository.get(ticket_id)
    
    async def get_by_user_id(self, user_id: int) -> List[Ticket]:
        """Get all tickets for a user."""
        return await self.ticket_repository.get_by_user_id(user_id)
    
    async def get_open_tickets(self) -> List[Ticket]:
        """Get all open tickets."""
        return await self.ticket_repository.get_open_tickets()
    
    async def get_tickets_by_status(self, status: str) -> List[Ticket]:
        """Get all tickets with a specific status."""
        return await self.ticket_repository.get_tickets_by_status(status)
    
    async def create(self, ticket_data: TicketCreate) -> Ticket:
        """Create a new ticket."""
        # Check if user exists
        user = await self.user_repository.get(ticket_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create ticket
        ticket_dict = ticket_data.model_dump()
        ticket_dict["created_at"] = datetime.utcnow()
        ticket_dict["status"] = "open"
        
        return await self.ticket_repository.create(ticket_dict)
    
    async def update(self, ticket_id: int, ticket_data: TicketUpdate) -> Optional[Ticket]:
        """Update a ticket."""
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        update_data = ticket_data.model_dump(exclude_unset=True)
        return await self.ticket_repository.update(db_obj=ticket, obj_in=update_data)
    
    async def delete(self, ticket_id: int) -> bool:
        """Delete a ticket."""
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        return await self.ticket_repository.delete(ticket)
    
    async def update_status(
        self,
        ticket_id: int,
        status: str,
        admin_id: Optional[int] = None
    ) -> Optional[Ticket]:
        """Update a ticket's status."""
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        return await self.ticket_repository.update_status(ticket_id, status, admin_id)
    
    async def get_ticket_stats(self, user_id: int) -> dict:
        """Get ticket statistics for a user."""
        return await self.ticket_repository.get_user_ticket_stats(user_id)
    
    async def assign_ticket(self, ticket_id: int, admin_id: int) -> Optional[Ticket]:
        """Assign a ticket to an admin."""
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Check if admin exists
        admin = await self.user_repository.get(admin_id)
        if not admin or not admin.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admin ID"
            )
        
        return await self.update_status(ticket_id, "assigned", admin_id)
    
    async def close_ticket(self, ticket_id: int, admin_id: int) -> Optional[Ticket]:
        """Close a ticket."""
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Check if admin exists
        admin = await self.user_repository.get(admin_id)
        if not admin or not admin.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admin ID"
            )
        
        return await self.update_status(ticket_id, "closed", admin_id) 