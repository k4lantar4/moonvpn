"""
Database dependencies for MoonVPN.

This module contains dependency functions for database access.
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repositories.factory import RepositoryFactory

async def get_repository_factory(
    session: AsyncSession = Depends(get_db)
) -> AsyncGenerator[RepositoryFactory, None]:
    """Get a repository factory instance."""
    try:
        factory = RepositoryFactory(session)
        yield factory
    finally:
        await factory.close()

# Convenience dependencies for individual repositories
async def get_user_repository(
    factory: RepositoryFactory = Depends(get_repository_factory)
) -> AsyncGenerator[UserRepository, None]:
    """Get the user repository."""
    yield factory.user_repository

async def get_subscription_repository(
    factory: RepositoryFactory = Depends(get_repository_factory)
) -> AsyncGenerator[SubscriptionRepository, None]:
    """Get the subscription repository."""
    yield factory.subscription_repository

async def get_payment_repository(
    factory: RepositoryFactory = Depends(get_repository_factory)
) -> AsyncGenerator[PaymentRepository, None]:
    """Get the payment repository."""
    yield factory.payment_repository

async def get_ticket_repository(
    factory: RepositoryFactory = Depends(get_repository_factory)
) -> AsyncGenerator[TicketRepository, None]:
    """Get the ticket repository."""
    yield factory.ticket_repository

async def get_notification_repository(
    factory: RepositoryFactory = Depends(get_repository_factory)
) -> AsyncGenerator[NotificationRepository, None]:
    """Get the notification repository."""
    yield factory.notification_repository

async def get_server_repository(
    factory: RepositoryFactory = Depends(get_repository_factory)
) -> AsyncGenerator[ServerRepository, None]:
    """Get the server repository."""
    yield factory.server_repository 