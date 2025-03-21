"""
Repository factory for MoonVPN.

This module contains the repository factory class that manages repository instances.
"""

from typing import Dict, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.db.repositories.user import UserRepository
from app.db.repositories.subscription import SubscriptionRepository
from app.db.repositories.payment import PaymentRepository
from app.db.repositories.ticket import TicketRepository
from app.db.repositories.notification import NotificationRepository
from app.db.repositories.server import ServerRepository

T = TypeVar("T", bound=BaseRepository)

class RepositoryFactory:
    """Repository factory class."""
    
    def __init__(self, session: AsyncSession):
        """Initialize factory."""
        self.session = session
        self._repositories: Dict[Type[BaseRepository], BaseRepository] = {}
    
    def get_repository(self, repository_type: Type[T]) -> T:
        """Get a repository instance."""
        if repository_type not in self._repositories:
            self._repositories[repository_type] = repository_type(self.session)
        return self._repositories[repository_type]
    
    @property
    def user_repository(self) -> UserRepository:
        """Get the user repository."""
        return self.get_repository(UserRepository)
    
    @property
    def subscription_repository(self) -> SubscriptionRepository:
        """Get the subscription repository."""
        return self.get_repository(SubscriptionRepository)
    
    @property
    def payment_repository(self) -> PaymentRepository:
        """Get the payment repository."""
        return self.get_repository(PaymentRepository)
    
    @property
    def ticket_repository(self) -> TicketRepository:
        """Get the ticket repository."""
        return self.get_repository(TicketRepository)
    
    @property
    def notification_repository(self) -> NotificationRepository:
        """Get the notification repository."""
        return self.get_repository(NotificationRepository)
    
    @property
    def server_repository(self) -> ServerRepository:
        """Get the server repository."""
        return self.get_repository(ServerRepository)
    
    async def close(self) -> None:
        """Close all repositories."""
        self._repositories.clear()
        await self.session.close() 