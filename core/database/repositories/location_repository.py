from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repo import BaseRepository
from core.database.models.location import Location # Assuming model location
from core.schemas.location import LocationCreate, LocationUpdate # Assuming schemas exist

class LocationRepository(BaseRepository[Location, LocationCreate, LocationUpdate]):
    def __init__(self):
        super().__init__(Location)

    async def get_active_locations(self, db_session: AsyncSession) -> List[Location]:
        statement = select(self.model).where(self.model.is_active == True)
        result = await db_session.execute(statement)
        return result.scalars().all()

    # Add other location-specific query methods if needed
    # e.g., find_by_country_code, etc. 