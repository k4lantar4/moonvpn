"""Repository for PanelInbound model operations."""

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Sequence, List, Type, Any
from sqlalchemy.sql import insert

from core.database.models import PanelInbound
from core.schemas.panel_inbound import PanelInboundCreateSchema
from core.database.repositories.base_repo import BaseRepository, ModelType, CreateSchemaType, UpdateSchemaType

class PanelInboundRepository(BaseRepository[PanelInbound, Any, Any]):
    """
    Repository for PanelInbound model operations.
    Inherits basic CRUD operations from BaseRepository.
    """
    
    def __init__(self):
        super().__init__(model=PanelInbound)

    async def get_by_panel_id_and_tag(self, db_session: AsyncSession, panel_id: int, tag: str) -> Optional[PanelInbound]:
        """Get a specific inbound by its panel ID and tag."""
        stmt = select(self._model).where(
            self._model.panel_id == panel_id,
            self._model.tag == tag
        )
        result = await db_session.execute(stmt)
        return result.scalars().first()

    async def get_by_panel_id(self, db_session: AsyncSession, panel_id: int) -> Sequence[PanelInbound]:
        """Get all inbounds associated with a specific panel."""
        stmt = select(self._model).where(self._model.panel_id == panel_id).order_by(self._model.tag)
        result = await db_session.execute(stmt)
        return result.scalars().all()
    
    async def get_active_inbounds_by_panel(self, db_session: AsyncSession, panel_id: int) -> Sequence[PanelInbound]:
        """Get inbounds that are active both on the panel and in our system for a specific panel."""
        stmt = select(self._model).where(
            self._model.panel_id == panel_id,
            self._model.panel_enabled == True,
            self._model.is_active == True
        ).order_by(self._model.tag)
        result = await db_session.execute(stmt)
        return result.scalars().all()
    
    async def bulk_update_status_by_ids(self, db_session: AsyncSession, inbound_ids: List[int], panel_enabled: Optional[bool] = None, is_active: Optional[bool] = None) -> None:
        """Bulk update status fields for multiple inbounds by their primary key IDs."""
        if not inbound_ids:
            return
        
        values_to_update = {}
        if panel_enabled is not None:
            values_to_update['panel_enabled'] = panel_enabled
        if is_active is not None:
            values_to_update['is_active'] = is_active

        if not values_to_update:
            return

        stmt = (
            update(self._model)
            .where(self._model.id.in_(inbound_ids))
            .values(**values_to_update)
            # .execution_options(synchronize_session=False) # Use False for bulk updates
        )
        await db_session.execute(stmt)

    # Add other specific methods if needed, e.g., finding inbounds by protocol 

    # Example: Method to find by panel_id and tag (might be useful)
    # async def find_by_panel_and_tag(self, db_session: AsyncSession, panel_id: int, tag: str) -> Optional[PanelInbound]:
    #     stmt = select(self._model).where(
    #         self._model.panel_id == panel_id,
    #         self._model.tag == tag
    #     )
    #     result = await db_session.execute(stmt)
    #     return result.scalars().first()

    # Example: Upsert method (more complex, might need ON DUPLICATE KEY UPDATE logic)
    # async def upsert_many(self, db_session: AsyncSession, inbound_data: list[dict]):
    #     # This requires raw SQL or specific dialect features (like MySQL ON DUPLICATE KEY UPDATE)
    #     # Or, fetch existing, compare, and then batch insert/update.
    #     # For simplicity now, we might just delete existing for a panel and insert new ones.
    #     pass 

    async def delete_by_field(self, db_session: AsyncSession, field_name: str, value: Any) -> int:
        """Deletes records matching a specific field and value. Returns count of deleted rows."""
        if not hasattr(self._model, field_name):
            raise ValueError(f"Model {self._model.__name__} has no attribute {field_name}")
        
        stmt = delete(self._model).where(getattr(self._model, field_name) == value)
        result = await db_session.execute(stmt)
        # Note: Consider moving commit logic to the service layer
        # await db_session.commit() # Typically handled by service/middleware
        return result.rowcount # Return number of deleted rows 

    async def delete_by_panel_id(self, db_session: AsyncSession, panel_id: int) -> None:
        """Deletes all inbounds associated with a specific panel."""
        stmt = delete(self._model).where(self._model.panel_id == panel_id)
        await db_session.execute(stmt)
        # Note: We might want to commit here or let the service layer handle commits.
        # await db_session.commit() # Optional: Commit immediately

    async def bulk_add_inbounds(self, db_session: AsyncSession, panel_id: int, inbounds_data: List[PanelInboundCreateSchema]) -> Sequence[PanelInbound]:
        """Adds multiple inbounds for a specific panel in a single operation."""
        if not inbounds_data:
            return []

        values_to_insert = []
        for inbound in inbounds_data:
            data = inbound.dict()
            data['panel_id'] = panel_id  # Add the panel_id foreign key
            # Convert complex types if needed (e.g., dicts to JSON strings if model expects it)
            # Example: data['settings'] = json.dumps(data.get('settings'))
            # Example: data['stream_settings'] = json.dumps(data.get('stream_settings'))
            values_to_insert.append(data)

        # Using SQLAlchemy Core insert for bulk operation efficiency
        stmt = insert(self._model).values(values_to_insert).returning(self._model)
        result = await db_session.execute(stmt)
        inserted_rows = result.scalars().all()
        # await db_session.commit() # Optional: Commit immediately
        return inserted_rows

    async def get_by_panel_inbound_id(self, db_session: AsyncSession, panel_id: int, panel_inbound_id: int) -> PanelInbound | None:
        """Retrieves a specific inbound by its panel_id and panel_inbound_id."""
        stmt = select(self._model).where(
            self._model.panel_id == panel_id,
            self._model.panel_inbound_id == panel_inbound_id
        )
        result = await db_session.execute(stmt)
        return result.scalars().first() 