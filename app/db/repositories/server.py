"""
Server repository for MoonVPN.

This module contains the Server repository class that handles database operations for VPN servers.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.db.models.server import Server
from app.models.server import Server as ServerSchema

class ServerRepository(BaseRepository[Server]):
    """Server repository class."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(Server, session)
    
    async def get_by_host(self, host: str) -> Optional[Server]:
        """Get a server by host address."""
        query = select(self.model).where(self.model.host == host)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_servers(self) -> List[Server]:
        """Get all active servers."""
        query = select(self.model).where(self.model.status == "active")
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_servers_by_protocol(self, protocol: str) -> List[Server]:
        """Get all servers with a specific protocol."""
        query = select(self.model).where(self.model.protocol == protocol)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_servers_by_load(self, max_load: float) -> List[Server]:
        """Get all servers with load below the specified threshold."""
        query = select(self.model).where(
            self.model.status == "active",
            self.model.load <= max_load
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_from_schema(self, server: ServerSchema) -> Server:
        """Create a server from a Pydantic schema."""
        server_data = server.model_dump(exclude={"id"})
        return await self.create(server_data)
    
    async def update_status(self, server_id: int, status: str) -> Optional[Server]:
        """Update a server's status."""
        server = await self.get(server_id)
        if server:
            return await self.update(db_obj=server, obj_in={"status": status})
        return None
    
    async def update_load(self, server_id: int, load: float) -> Optional[Server]:
        """Update a server's load."""
        server = await self.get(server_id)
        if server:
            return await self.update(db_obj=server, obj_in={"load": load})
        return None
    
    async def get_server_stats(self) -> dict:
        """Get server statistics."""
        query = select(self.model)
        result = await self.session.execute(query)
        servers = list(result.scalars().all())
        
        total_servers = len(servers)
        active_servers = sum(1 for server in servers if server.status == "active")
        total_load = sum(server.load for server in servers if server.status == "active")
        average_load = total_load / active_servers if active_servers > 0 else 0
        
        protocols = {}
        for server in servers:
            protocols[server.protocol] = protocols.get(server.protocol, 0) + 1
        
        return {
            "total_servers": total_servers,
            "active_servers": active_servers,
            "average_load": average_load,
            "protocols": protocols
        } 