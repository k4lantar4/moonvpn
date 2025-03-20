"""
Ticket repository for MoonVPN.

This module contains the Ticket repository class that handles database operations for support tickets.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.db.models.ticket import Ticket
from app.models.ticket import Ticket as TicketSchema

class TicketRepository(BaseRepository[Ticket]):
    """Ticket repository class."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(Ticket, session)
    
    async def get_by_user_id(self, user_id: int) -> List[Ticket]:
        """Get all tickets for a user."""
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_open_tickets(self) -> List[Ticket]:
        """Get all open tickets."""
        query = select(self.model).where(self.model.status == "open")
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_tickets_by_status(self, status: str) -> List[Ticket]:
        """Get all tickets with a specific status."""
        query = select(self.model).where(self.model.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_from_schema(self, ticket: TicketSchema) -> Ticket:
        """Create a ticket from a Pydantic schema."""
        ticket_data = ticket.model_dump(exclude={"id"})
        return await self.create(ticket_data)
    
    async def update_status(
        self,
        ticket_id: int,
        status: str,
        admin_id: Optional[int] = None
    ) -> Optional[Ticket]:
        """Update a ticket's status."""
        ticket = await self.get(ticket_id)
        if ticket:
            update_data = {
                "status": status,
                "updated_by": admin_id
            }
            return await self.update(db_obj=ticket, obj_in=update_data)
        return None
    
    async def get_user_ticket_stats(self, user_id: int) -> dict:
        """Get ticket statistics for a user."""
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        tickets = list(result.scalars().all())
        
        total_tickets = len(tickets)
        open_tickets = sum(1 for ticket in tickets if ticket.status == "open")
        closed_tickets = sum(1 for ticket in tickets if ticket.status == "closed")
        
        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "closed_tickets": closed_tickets,
            "resolution_rate": (closed_tickets / total_tickets * 100) if total_tickets > 0 else 0
        } 