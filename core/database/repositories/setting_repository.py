"""Repository for Setting model operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Any

from core.database.models.setting import Setting # Assuming model exists
from core.database.repositories.base_repo import BaseRepository
from core.schemas.setting import SettingCreate, SettingUpdate # Assuming schemas exist

class SettingRepository(BaseRepository[Setting, Any, Any]):
    """Provides data access methods for Setting entities."""

    def __init__(self):
        # Do NOT store session here
        super().__init__(model=Setting)
        # self.session = session <-- Remove this

    # Add db_session argument to methods
    async def get_by_key(self, db_session: AsyncSession, key: str) -> Optional[Setting]:
        """Get a setting by its key."""
        stmt = select(self._model).where(self._model.key == key)
        result = await db_session.execute(stmt) # Use passed session
        return result.scalars().first()

    async def get_value(self, db_session: AsyncSession, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get the value of a setting by its key, return default if not found."""
        # Pass session to the helper method
        setting = await self.get_by_key(db_session, key)
        return setting.value if setting else default

    async def set_value(self, db_session: AsyncSession, key: str, value: str) -> Setting:
        """Create or update a setting value."""
        # Pass session to helper method
        existing_setting = await self.get_by_key(db_session, key)
        if existing_setting:
            # Update existing setting
            update_schema = SettingUpdate(value=value) # Assuming SettingUpdate only needs value
            # Pass session to base update method
            updated_setting = await self.update(db_session=db_session, db_obj=existing_setting, obj_in=update_schema)
        else:
            # Create new setting
            create_schema = SettingCreate(key=key, value=value) # Assuming SettingCreate needs key and value
            # Pass session to base create method
            updated_setting = await self.create(db_session=db_session, obj_in=create_schema)
        return updated_setting

# You might need to create core/schemas/setting.py similar to other schemas
# Example core/schemas/setting.py:
# from pydantic import BaseModel
#
# class SettingBase(BaseModel):
#     key: str
#     value: str
#
# class SettingCreate(SettingBase):
#     pass
#
# class SettingUpdate(BaseModel):
#     value: str # Only value is updatable typically
#
# class SettingInDB(SettingBase):
#     id: int
#     class Config:
#         from_attributes = True 