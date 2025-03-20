"""
Server API endpoints for MoonVPN.

This module contains the FastAPI router for server-related endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.db.repositories.factory import RepositoryFactory
from app.services.server import ServerService
from app.models.server import Server, ServerCreate, ServerUpdate, ServerResponse
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[ServerResponse])
async def get_servers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ServerResponse]:
    """Get all active servers."""
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    servers = await service.get_active_servers()
    
    return [ServerResponse.from_orm(server) for server in servers]

@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ServerResponse:
    """Get server by ID."""
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    server = await service.get_by_id(server_id)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return ServerResponse.from_orm(server)

@router.get("/host/{host}", response_model=ServerResponse)
async def get_server_by_host(
    host: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ServerResponse:
    """Get server by host address."""
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    server = await service.get_by_host(host)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return ServerResponse.from_orm(server)

@router.get("/protocol/{protocol}", response_model=List[ServerResponse])
async def get_servers_by_protocol(
    protocol: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ServerResponse]:
    """Get all servers with a specific protocol."""
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    servers = await service.get_servers_by_protocol(protocol)
    
    return [ServerResponse.from_orm(server) for server in servers]

@router.get("/load/{max_load}", response_model=List[ServerResponse])
async def get_servers_by_load(
    max_load: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ServerResponse]:
    """Get all servers with load below the specified threshold."""
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    servers = await service.get_servers_by_load(max_load)
    
    return [ServerResponse.from_orm(server) for server in servers]

@router.post("/", response_model=ServerResponse)
async def create_server(
    server_data: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ServerResponse:
    """Create a new server (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    server = await service.create(server_data)
    
    return ServerResponse.from_orm(server)

@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    server_data: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ServerResponse:
    """Update a server (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    server = await service.update(server_id, server_data)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return ServerResponse.from_orm(server)

@router.delete("/{server_id}")
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a server (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    success = await service.delete(server_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return {"message": "Server deleted successfully"}

@router.post("/{server_id}/status")
async def update_server_status(
    server_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ServerResponse:
    """Update a server's status (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    server = await service.update_status(server_id, status)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return ServerResponse.from_orm(server)

@router.post("/{server_id}/load")
async def update_server_load(
    server_id: int,
    load: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ServerResponse:
    """Update a server's load (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    server = await service.update_load(server_id, load)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return ServerResponse.from_orm(server)

@router.get("/stats")
async def get_server_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get server statistics (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    return await service.get_server_stats()

@router.get("/best/{protocol}")
async def get_best_server(
    protocol: str,
    max_load: float = 0.8,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ServerResponse:
    """Get the best available server based on load and protocol."""
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    server = await service.get_best_server(protocol, max_load)
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No suitable server found"
        )
    
    return ServerResponse.from_orm(server)

@router.get("/{server_id}/config")
async def get_server_config(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get server configuration."""
    factory = RepositoryFactory(db)
    service = ServerService(factory.server_repository)
    return await service.get_server_config(server_id) 