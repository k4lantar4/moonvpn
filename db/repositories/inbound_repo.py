from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from db.models import Inbound, Panel, InboundStatus
from db.repositories.base_repository import BaseRepository
from typing import List, Optional

class InboundRepository(BaseRepository[Inbound]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Inbound)

    async def get_by_remote_id_and_panel(self, remote_id: int, panel_id: int) -> Optional[Inbound]:
        """
        دریافت inbound بر اساس remote_id و panel_id.
        فقط inbound‌های غیرحذف‌شده را برمی‌گرداند.
        """
        query = select(self.model).where(
            self.model.remote_id == remote_id,
            self.model.panel_id == panel_id,
            self.model.status != InboundStatus.DELETED
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_inbounds(self) -> List[Inbound]:
        """
        Fetches all active inbounds.
        (Placeholder implementation)
        """
        # query = select(self.model).where(self.model.is_active == True)
        # result = await self.session.execute(query)
        # return result.scalars().all()
        print("Fetching all active inbounds - Placeholder")
        return []

    async def get_active_inbounds_by_panel(self, panel_id: int) -> List[Inbound]:
        """
        Fetches active inbounds associated with a specific panel.
        (Placeholder implementation - adjust query as needed)
        """
        # TODO: Implement the actual query logic based on your model relationships
        # This is a placeholder assuming a 'panel_id' and 'is_active' field exists
        # query = select(self.model).join(Panel).where(Panel.id == panel_id, self.model.is_active == True)
        # result = await self.session.execute(query)
        # return result.scalars().all()
        print(f"Fetching active inbounds for panel_id: {panel_id} - Placeholder")
        return [] # Return an empty list for now

    async def get_by_panel_id(self, panel_id: int) -> List[Inbound]:
        """ Fetches all inbounds for a specific panel ID (Placeholder) """
        # query = select(self.model).join(Panel).where(Panel.id == panel_id)
        # result = await self.session.execute(query)
        # return result.scalars().all()
        print(f"Fetching all inbounds for panel_id: {panel_id} - Placeholder")
        return [] 