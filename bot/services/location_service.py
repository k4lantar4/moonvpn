"""Service layer for managing locations."""

import logging
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.location import Location
from core.database.repositories.location_repository import LocationRepository
from core.database.repositories.panel_repository import PanelRepository
from core.schemas.location import LocationCreate, LocationUpdate
from core.exceptions import NotFoundError, ServiceError

logger = logging.getLogger(__name__)

class LocationService:
    """Encapsulates business logic for locations."""

    def __init__(self):
        self.location_repo = LocationRepository()
        self.panel_repo = PanelRepository()

    async def get_all_locations(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[Location]:
        """Retrieve all locations with pagination."""
        logger.debug("Fetching all locations")
        return await self.location_repo.get_multi(session, skip=skip, limit=limit)
    
    async def get_active_locations(self, session: AsyncSession) -> Sequence[Location]:
        """Retrieve all active locations."""
        logger.debug("Fetching active locations")
        return await self.location_repo.get_active_locations(session)

    async def get_location_by_id(self, session: AsyncSession, location_id: int) -> Location | None:
        """Get a single location by its ID."""
        logger.debug(f"Fetching location with id={location_id}")
        return await self.location_repo.get(session, id=location_id)

    async def create_location(self, session: AsyncSession, location_in: LocationCreate) -> Location:
        """Create a new location."""
        logger.info(f"Creating new location")
        return await self.location_repo.create(session, obj_in=location_in)

    async def update_location(self, session: AsyncSession, location_id: int, location_in: LocationUpdate) -> Location | None:
        """Update an existing location."""
        logger.info(f"Updating location with id={location_id}")
        db_location = await self.location_repo.get(session, id=location_id)
        if not db_location:
            logger.warning(f"Location with id={location_id} not found for update.")
            return None
        return await self.location_repo.update(session, db_obj=db_location, obj_in=location_in)

    async def delete_location(self, session: AsyncSession, location_id: int) -> Location | None:
        """Delete a location. Raises ServiceError if associated panels exist."""
        logger.info(f"Attempting to delete location with id={location_id}")
        
        # Check for associated active panels first
        associated_panels = await self.panel_repo.get_active_panels_by_location(session, location_id=location_id)
        if associated_panels:
            panel_names = ", ".join([p.name for p in associated_panels])
            error_msg = f"Location ID {location_id} cannot be deleted because it is associated with active panel(s): {panel_names}"
            logger.warning(error_msg)
            raise ServiceError(error_msg) # Raise error to prevent deletion

        # Proceed with deletion if no active panels are associated
        deleted_location = await self.location_repo.delete(session, id=location_id)
        if not deleted_location:
             raise NotFoundError(f"Location with id={location_id} not found for deletion.")
        # Commit should happen in the handler after successful deletion
        # await session.commit() 
        return deleted_location 