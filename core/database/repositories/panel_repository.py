"""Repository for Panel model operations."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # Use selectinload for eager loading
from typing import Optional, Sequence, Any, Dict, List, Type, Union
from sqlalchemy.exc import SQLAlchemyError
import logging
import asyncio

from core.database.models.panel import Panel, PanelType
from core.schemas.panel import PanelCreate, PanelUpdate
from core.database.repositories.base_repo import BaseRepository

logger = logging.getLogger(__name__)

class PanelRepository(BaseRepository[Panel, Any, Any]):
    """Repository for interacting with Panel data in the database."""

    def __init__(self):
        # BaseRepository only takes model in its __init__
        super().__init__(model=Panel)
        # Do NOT store session here

    async def get_by_url(self, db_session: AsyncSession, *, url: str) -> Optional[Panel]:
        """Get a panel by its URL."""
        stmt = select(self.model).where(self.model.url == url)
        # Use the passed-in session
        result = await db_session.execute(stmt) 
        return result.scalars().first()

    # Override the base 'get' method correctly
    async def get(self, db_session: AsyncSession, id: Any, *, options: Optional[List] = None) -> Optional[Panel]:
        """Retrieve a single panel by its primary key, optionally applying loading options."""
        try:
            statement = select(self._model).where(self._model.id == id)
            if options:
                statement = statement.options(*options)
            result = await db_session.execute(statement)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while getting {self._model.__name__} by ID {id} with options: {e}", exc_info=True)
            return None  # Or raise a custom exception
        except Exception as e:
            logger.error(
                f"Unexpected error while getting {self._model.__name__} by ID {id} with options: {e}", exc_info=True)
            return None

    # Add db_session argument to all custom methods
    async def get_active_panels(self, db_session: AsyncSession, *, eager_load_location: bool = False) -> Sequence[Panel]:
        """Get all active panels, optionally eager loading location."""
        stmt = select(self.model).where(self.model.is_active == True).order_by(self.model.name)
        if eager_load_location:
            stmt = stmt.options(selectinload(self.model.location))
        # Use the passed-in session
        result = await db_session.execute(stmt)
        return result.scalars().all()
    
    async def get_active_panels_by_location(self, db_session: AsyncSession, *, location_id: int) -> Sequence[Panel]:
        """Get all active panels for a specific location."""
        stmt = select(self.model).where(
            self.model.is_active == True,
            self.model.location_id == location_id
        ).order_by(self.model.name)
        # Use the passed-in session
        result = await db_session.execute(stmt)
        return result.scalars().all()

    async def update_panel_health(self, db_session: AsyncSession, *, panel_id: int, is_healthy: bool) -> None:
        """Update the health status of a specific panel."""
        stmt = (
            update(self.model)
            .where(self.model.id == panel_id)
            .values(is_healthy=is_healthy)
        )
        # Use the passed-in session
        await db_session.execute(stmt)

    async def get_all_with_location(self, db_session: AsyncSession, *, skip: int = 0, limit: int = 100) -> Sequence[Panel]:
        """Gets all panels with pagination, always eager loading the location."""
        try:
            stmt = (
                select(self._model)
                .options(selectinload(self._model.location))
                .order_by(self._model.id)
                .offset(skip)
                .limit(limit)
            )
            result = await db_session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while getting all panels with location: {e}", exc_info=True)
            return []  # Or raise
        except Exception as e:
            logger.error(
                f"Unexpected error while getting all panels with location: {e}", exc_info=True)
            return []

    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[Panel]:
        """Retrieve a Panel by its name."""
        try:
            statement = select(self._model).where(self._model.name == name)
            result = await session.execute(statement)
            return result.scalars().one_or_none()
        except NoResultFound:
            return None
        except Exception as e:
            logger.error(
                f"Error retrieving {self._model.__name__} with name {name}: {e}", exc_info=True
            )
            raise ServiceError(f"Database error while retrieving panel with name {name}") from e

    async def get_all_active(self, session: AsyncSession, options: Optional[Sequence] = None) -> Sequence[Panel]:
        """Retrieve all active Panels."""
        try:
            query_options = options if options is not None else []
            statement = select(self._model).where(self._model.is_active == True).options(*query_options)
            result = await session.execute(statement)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving all active {self._model.__name__}s: {e}", exc_info=True)
            raise ServiceError("Database error while retrieving active panels") from e

# Add other specific methods as needed, e.g.:
# async def find_by_type(self, panel_type: PanelType) -> Sequence[Panel]:
#     ... 