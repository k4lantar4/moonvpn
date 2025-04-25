"""
Panel repository for database operations
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.panel import Panel, PanelStatus
from db.models.inbound import Inbound

class PanelRepository:
    """Repository for panel-related database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all_panels(self) -> List[Panel]:
        """Get all panels"""
        result = await self.session.execute(select(Panel))
        return list(result.scalars().all())
    
    async def get_active_panels(self) -> List[Panel]:
        """Get all active panels"""
        query = select(Panel).where(Panel.status == PanelStatus.ACTIVE)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_panel_by_id(self, panel_id: int) -> Optional[Panel]:
        """Get panel by ID"""
        return await self.session.get(Panel, panel_id)
    
    async def get_panel_by_url(self, url: str) -> Optional[Panel]:
        """Get panel by URL"""
        query = select(Panel).where(Panel.url == url)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_panel(self, panel_data: dict) -> Panel:
        """Create a new panel"""
        panel = Panel(**panel_data)
        self.session.add(panel)
        await self.session.flush()
        await self.session.refresh(panel)
        return panel
    
    async def update_panel(self, panel_id: int, panel_data: dict) -> Optional[Panel]:
        """Update panel data"""
        panel = await self.get_panel_by_id(panel_id)
        if panel:
            for key, value in panel_data.items():
                setattr(panel, key, value)
            await self.session.commit()
            await self.session.refresh(panel)
        return panel
    
    async def delete_panel(self, panel_id: int) -> bool:
        """Delete a panel"""
        panel = await self.get_panel_by_id(panel_id)
        if panel:
            await self.session.delete(panel)
            await self.session.commit()
            return True
        return False
    
    async def get_panel_inbounds(self, panel_id: int) -> List[Inbound]:
        """Get all inbounds for a panel"""
        result = await self.session.execute(
            select(Inbound).where(Inbound.panel_id == panel_id)
        )
        return list(result.scalars().all()) 