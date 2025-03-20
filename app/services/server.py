"""
Server service for MoonVPN.

This module contains the server service implementation using the repository pattern.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status

from app.db.repositories.server import ServerRepository
from app.models.server import Server, ServerCreate, ServerUpdate

class ServerService:
    """Server service class."""
    
    def __init__(self, repository: ServerRepository):
        """Initialize service."""
        self.repository = repository
    
    async def get_by_id(self, server_id: int) -> Optional[Server]:
        """Get a server by ID."""
        return await self.repository.get(server_id)
    
    async def get_by_host(self, host: str) -> Optional[Server]:
        """Get a server by host address."""
        return await self.repository.get_by_host(host)
    
    async def get_active_servers(self) -> List[Server]:
        """Get all active servers."""
        return await self.repository.get_active_servers()
    
    async def get_servers_by_protocol(self, protocol: str) -> List[Server]:
        """Get all servers with a specific protocol."""
        return await self.repository.get_servers_by_protocol(protocol)
    
    async def get_servers_by_load(self, max_load: float) -> List[Server]:
        """Get all servers with load below the specified threshold."""
        return await self.repository.get_servers_by_load(max_load)
    
    async def create(self, server_data: ServerCreate) -> Server:
        """Create a new server."""
        # Check if server with same host already exists
        existing_server = await self.get_by_host(server_data.host)
        if existing_server:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Server with this host already exists"
            )
        
        # Create server
        server_dict = server_data.model_dump()
        server_dict["created_at"] = datetime.utcnow()
        server_dict["status"] = "active"
        server_dict["load"] = 0.0
        
        return await self.repository.create(server_dict)
    
    async def update(self, server_id: int, server_data: ServerUpdate) -> Optional[Server]:
        """Update a server."""
        server = await self.get_by_id(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Check host uniqueness if being updated
        if server_data.host and server_data.host != server.host:
            if await self.get_by_host(server_data.host):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Host already in use"
                )
        
        update_data = server_data.model_dump(exclude_unset=True)
        return await self.repository.update(db_obj=server, obj_in=update_data)
    
    async def delete(self, server_id: int) -> bool:
        """Delete a server."""
        server = await self.get_by_id(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        return await self.repository.delete(server)
    
    async def update_status(self, server_id: int, status: str) -> Optional[Server]:
        """Update a server's status."""
        server = await self.get_by_id(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        return await self.repository.update_status(server_id, status)
    
    async def update_load(self, server_id: int, load: float) -> Optional[Server]:
        """Update a server's load."""
        server = await self.get_by_id(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        return await self.repository.update_load(server_id, load)
    
    async def get_server_stats(self) -> dict:
        """Get server statistics."""
        return await self.repository.get_server_stats()
    
    async def get_best_server(self, protocol: str, max_load: float = 0.8) -> Optional[Server]:
        """Get the best available server based on load and protocol."""
        servers = await self.get_servers_by_load(max_load)
        protocol_servers = [s for s in servers if s.protocol == protocol]
        
        if not protocol_servers:
            return None
        
        # Return server with lowest load
        return min(protocol_servers, key=lambda s: s.load)
    
    async def get_server_config(self, server_id: int) -> dict:
        """Get server configuration."""
        server = await self.get_by_id(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        return {
            "id": server.id,
            "host": server.host,
            "port": server.port,
            "protocol": server.protocol,
            "config": server.config,
            "status": server.status,
            "load": server.load
        } 