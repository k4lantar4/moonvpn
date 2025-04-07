"""
Panel Service

This module provides a service layer for managing 3x-ui panels,
including panel registration, health checks, and operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from core.database import get_db
from core.config import get_settings
from core.security import encrypt_text, decrypt_text
from integrations.panels.client import XuiPanelClient, test_panel_connection
from api.models import Panel, PanelHealthCheck

logger = logging.getLogger(__name__)
settings = get_settings()


class PanelService:
    """Service for managing 3x-ui panels.
    
    This service provides methods for:
    - Panel registration and management (CRUD operations)
    - Panel health checking
    - Proxying operations to panels
    - Managing panel credentials securely
    """
    
    def __init__(self, db: AsyncSession = None):
        """Initialize panel service.
        
        Args:
            db: Database session (optional, will be created if needed)
        """
        self.db = db
        self._clients: Dict[int, XuiPanelClient] = {}  # Cache for active clients
    
    async def _get_db(self) -> AsyncSession:
        """Get database session, creating one if not provided in constructor.
        
        Returns:
            AsyncSession: Database session
        """
        if self.db is None:
            self.db = await anext(get_db())
        return self.db
    
    async def list_panels(self, skip: int = 0, limit: int = 100) -> List[Panel]:
        """List all registered panels.
        
        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List[Panel]: List of panels
        """
        db = await self._get_db()
        result = await db.execute(
            select(Panel)
            .options(selectinload(Panel.health_checks))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_panel(self, panel_id: int) -> Optional[Panel]:
        """Get a panel by ID.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            Optional[Panel]: Panel if found, None otherwise
        """
        db = await self._get_db()
        result = await db.execute(
            select(Panel)
            .options(selectinload(Panel.health_checks))
            .filter(Panel.id == panel_id)
        )
        return result.scalars().first()
    
    async def get_panel_by_name(self, name: str) -> Optional[Panel]:
        """Get a panel by name.
        
        Args:
            name: Panel name
            
        Returns:
            Optional[Panel]: Panel if found, None otherwise
        """
        db = await self._get_db()
        result = await db.execute(
            select(Panel)
            .options(selectinload(Panel.health_checks))
            .filter(Panel.name == name)
        )
        return result.scalars().first()
    
    async def create_panel(self, panel_data: Dict[str, Any]) -> Panel:
        """Create a new panel.
        
        Args:
            panel_data: Panel data
            
        Returns:
            Panel: Created panel
            
        Raises:
            HTTPException: If panel with the same name already exists
        """
        db = await self._get_db()
        
        # Check if panel with same name exists
        if await self.get_panel_by_name(panel_data["name"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Panel with name '{panel_data['name']}' already exists"
            )
        
        # Test connection to panel before creating
        test_result = await test_panel_connection(
            url=panel_data["url"],
            username=panel_data["username"],
            password=panel_data["password"],
            login_path=panel_data.get("login_path", "/login")
        )
        
        if not test_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to panel: {test_result['error']}"
            )
        
        # Create panel
        panel = Panel(
            name=panel_data["name"],
            url=panel_data["url"],
            username=panel_data["username"],
            password=panel_data["password"],  # In a real app, encrypt this
            login_path=panel_data.get("login_path", "/login"),
            notes=panel_data.get("notes", ""),
            is_active=panel_data.get("is_active", True),
            timeout=panel_data.get("timeout", 10.0),
            max_retries=panel_data.get("max_retries", 3),
            retry_delay=panel_data.get("retry_delay", 1.0),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(panel)
        await db.commit()
        await db.refresh(panel)
        
        # Create initial health check
        health_check = PanelHealthCheck(
            panel_id=panel.id,
            status=test_result["status"],
            response_time_ms=test_result["response_time_ms"],
            details=json.dumps(test_result),
            checked_at=datetime.utcnow()
        )
        
        db.add(health_check)
        await db.commit()
        
        return panel
    
    async def update_panel(self, panel_id: int, panel_data: Dict[str, Any]) -> Optional[Panel]:
        """Update a panel.
        
        Args:
            panel_id: Panel ID
            panel_data: Panel data to update
            
        Returns:
            Optional[Panel]: Updated panel if found, None otherwise
            
        Raises:
            HTTPException: If panel with new name already exists
        """
        db = await self._get_db()
        panel = await self.get_panel(panel_id)
        
        if not panel:
            return None
        
        # Check if panel with new name exists (if name is being updated)
        if "name" in panel_data and panel_data["name"] != panel.name:
            existing = await self.get_panel_by_name(panel_data["name"])
            if existing and existing.id != panel_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Panel with name '{panel_data['name']}' already exists"
                )
        
        # Update fields
        for key, value in panel_data.items():
            if hasattr(panel, key):
                setattr(panel, key, value)
        
        panel.updated_at = datetime.utcnow()
        
        # If credentials changed, test connection
        if ("url" in panel_data or "username" in panel_data or 
            "password" in panel_data or "login_path" in panel_data):
            
            # Close existing client if present
            if panel.id in self._clients:
                await self._clients[panel.id].close()
                del self._clients[panel.id]
            
            # Test new connection
            test_result = await test_panel_connection(
                url=panel.url,
                username=panel.username,
                password=panel.password,
                login_path=panel.login_path
            )
            
            # Create health check for the test
            health_check = PanelHealthCheck(
                panel_id=panel.id,
                status=test_result["status"],
                response_time_ms=test_result.get("response_time_ms", 0),
                details=json.dumps(test_result),
                checked_at=datetime.utcnow()
            )
            
            db.add(health_check)
        
        await db.commit()
        await db.refresh(panel)
        return panel
    
    async def delete_panel(self, panel_id: int) -> bool:
        """Delete a panel.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            bool: True if panel was deleted, False if not found
        """
        db = await self._get_db()
        panel = await self.get_panel(panel_id)
        
        if not panel:
            return False
        
        # Close client if active
        if panel_id in self._clients:
            await self._clients[panel_id].close()
            del self._clients[panel_id]
        
        # Delete panel and its health checks (cascade delete should handle this)
        await db.execute(delete(Panel).where(Panel.id == panel_id))
        await db.commit()
        
        return True
    
    async def check_panel_health(self, panel_id: int) -> Dict[str, Any]:
        """Check health of a panel.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            Dict[str, Any]: Health check result
            
        Raises:
            HTTPException: If panel not found
        """
        db = await self._get_db()
        panel = await self.get_panel(panel_id)
        
        if not panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Panel with ID {panel_id} not found"
            )
        
        # Test connection
        test_result = await test_panel_connection(
            url=panel.url,
            username=panel.username,
            password=panel.password,
            login_path=panel.login_path
        )
        
        # Create health check record
        health_check = PanelHealthCheck(
            panel_id=panel.id,
            status=test_result["status"],
            response_time_ms=test_result.get("response_time_ms", 0),
            details=json.dumps(test_result),
            checked_at=datetime.utcnow()
        )
        
        db.add(health_check)
        await db.commit()
        
        # If client exists and test failed, close it so it will be recreated
        if not test_result["success"] and panel_id in self._clients:
            await self._clients[panel_id].close()
            del self._clients[panel_id]
        
        return test_result
    
    async def check_all_panels_health(self) -> List[Dict[str, Any]]:
        """Check health of all active panels.
        
        Returns:
            List[Dict[str, Any]]: List of health check results
        """
        db = await self._get_db()
        panels = await self.list_panels()
        
        # Only check active panels
        active_panels = [p for p in panels if p.is_active]
        results = []
        
        # Check each panel
        for panel in active_panels:
            result = await self.check_panel_health(panel.id)
            results.append({
                "panel_id": panel.id,
                "panel_name": panel.name,
                "health_check": result
            })
        
        return results
    
    async def get_client(self, panel_id: int) -> Tuple[XuiPanelClient, Panel]:
        """Get or create a panel client.
        
        This method returns a cached client if available, or creates a new one
        if necessary. It also updates the panel's last_connected_at timestamp.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            Tuple[XuiPanelClient, Panel]: Tuple containing the client and panel
            
        Raises:
            HTTPException: If the panel is not found or inactive
        """
        # Check if we have a cached client
        if panel_id in self._clients:
            # Get the panel to return it
            db = await self._get_db()
            result = await db.execute(
                select(Panel).filter(Panel.id == panel_id)
            )
            panel = result.scalars().first()
            
            if not panel:
                # Panel was deleted but client is still cached
                if panel_id in self._clients:
                    await self._clients[panel_id].close()
                    del self._clients[panel_id]
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Panel not found"
                )
            
            if not panel.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Panel is inactive"
                )
            
            return self._clients[panel_id], panel
        
        # No cached client, create a new one
        db = await self._get_db()
        result = await db.execute(
            select(Panel).filter(Panel.id == panel_id)
        )
        panel = result.scalars().first()
        
        if not panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Panel not found"
            )
        
        if not panel.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Panel is inactive"
            )
        
        # Create a new client
        # Use the decrypted password from the panel model
        client = XuiPanelClient(
            base_url=panel.url,
            username=panel.username,
            password=panel.decrypted_password,  # Use decrypted password here
            login_path=panel.login_path,
            timeout=panel.timeout,
            max_retries=panel.max_retries,
            retry_delay=panel.retry_delay
        )
        
        # Try to login
        if not await client.login():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect to panel"
            )
        
        # Update last_connected_at
        panel.last_connected_at = datetime.utcnow()
        await db.commit()
        
        # Cache the client
        self._clients[panel_id] = client
        
        return client, panel
    
    async def close_all_clients(self):
        """Close all panel clients."""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
    
    # --- Panel operations proxying methods ---
    
    async def get_panel_status(self, panel_id: int) -> Dict[str, Any]:
        """Get status of a panel.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            Dict[str, Any]: Panel status
            
        Raises:
            HTTPException: If panel not found, inactive, or request fails
        """
        client, panel = await self.get_client(panel_id)
        
        success, status_data = await client.get_status()
        
        if not success:
            error_msg = status_data.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get status from panel '{panel.name}': {error_msg}"
            )
        
        return status_data
    
    async def get_panel_inbounds(self, panel_id: int) -> List[Dict[str, Any]]:
        """Get all inbounds from a panel.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            List[Dict[str, Any]]: List of inbounds
            
        Raises:
            HTTPException: If panel not found, inactive, or request fails
        """
        client, panel = await self.get_client(panel_id)
        
        success, inbounds_data = await client.get_inbounds()
        
        if not success:
            error_msg = inbounds_data.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get inbounds from panel '{panel.name}': {error_msg}"
            )
        
        return inbounds_data
    
    async def get_panel_inbound(self, panel_id: int, inbound_id: int) -> Dict[str, Any]:
        """Get an inbound from a panel.
        
        Args:
            panel_id: Panel ID
            inbound_id: Inbound ID
            
        Returns:
            Dict[str, Any]: Inbound data
            
        Raises:
            HTTPException: If panel not found, inactive, or request fails
        """
        client, panel = await self.get_client(panel_id)
        
        success, inbound_data = await client.get_inbound(inbound_id)
        
        if not success:
            error_msg = inbound_data.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get inbound from panel '{panel.name}': {error_msg}"
            )
        
        return inbound_data
    
    async def add_panel_client(
        self, 
        panel_id: int, 
        inbound_id: int, 
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a client to an inbound on a panel.
        
        Args:
            panel_id: Panel ID
            inbound_id: Inbound ID
            client_data: Client configuration
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            HTTPException: If panel not found, inactive, or request fails
        """
        client, panel = await self.get_client(panel_id)
        
        # Prepare client config with inbound ID
        config = {
            "id": inbound_id,
            "settings": client_data
        }
        
        success, result = await client.add_client(config)
        
        if not success:
            error_msg = result.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to add client to panel '{panel.name}': {error_msg}"
            )
        
        return result
    
    async def delete_panel_client(
        self, 
        panel_id: int, 
        inbound_id: int, 
        client_id: str
    ) -> Dict[str, Any]:
        """Delete a client from an inbound on a panel.
        
        Args:
            panel_id: Panel ID
            inbound_id: Inbound ID
            client_id: Client ID (UUID)
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            HTTPException: If panel not found, inactive, or request fails
        """
        client, panel = await self.get_client(panel_id)
        
        success, result = await client.delete_client(inbound_id, client_id)
        
        if not success:
            error_msg = result.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to delete client from panel '{panel.name}': {error_msg}"
            )
        
        return result
    
    async def get_client_traffic(
        self, 
        panel_id: int, 
        email: str
    ) -> Dict[str, Any]:
        """Get traffic statistics for a client by email.
        
        Args:
            panel_id: Panel ID
            email: Client email
            
        Returns:
            Dict[str, Any]: Traffic statistics
            
        Raises:
            HTTPException: If panel not found, inactive, or request fails
        """
        client, panel = await self.get_client(panel_id)
        
        success, result = await client.get_client_traffics(email)
        
        if not success:
            error_msg = result.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get client traffic from panel '{panel.name}': {error_msg}"
            )
        
        return result
    
    async def reset_client_traffic(
        self, 
        panel_id: int, 
        inbound_id: int, 
        email: str
    ) -> Dict[str, Any]:
        """Reset traffic statistics for a client.
        
        Args:
            panel_id: Panel ID
            inbound_id: Inbound ID
            email: Client email
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            HTTPException: If panel not found, inactive, or request fails
        """
        client, panel = await self.get_client(panel_id)
        
        success, result = await client.reset_client_traffic(inbound_id, email)
        
        if not success:
            error_msg = result.get("error", "Unknown error")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to reset client traffic on panel '{panel.name}': {error_msg}"
            )
        
        return result 