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
from api.models import Panel, PanelHealthCheck, PanelServerMigration, PanelDomain, Location, Settings

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
    
    # --- Server Migration Methods ---
    
    async def start_panel_migration(self, panel_id: int, new_server_ip: str, new_url: str, 
                                    new_geo_location: Optional[str] = None, 
                                    new_country_code: Optional[str] = None,
                                    reason: Optional[str] = None, 
                                    notes: Optional[str] = None,
                                    performed_by: Optional[int] = None) -> Dict[str, Any]:
        """
        Start the panel migration process.
        
        Args:
            panel_id: Panel ID
            new_server_ip: New server IP
            new_url: New panel URL
            new_geo_location: New geo location (optional)
            new_country_code: New country code (optional)
            reason: Reason for migration (optional)
            notes: Additional notes (optional)
            performed_by: User ID who initiated the migration (optional)
            
        Returns:
            Dict containing migration details
            
        Raises:
            HTTPException: If panel not found or already in migration
        """
        db = await self._get_db()
        
        # Get panel
        panel = await self.get_panel(panel_id)
        if not panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Panel with ID {panel_id} not found"
            )
        
        # Check if panel is already in migration
        if panel.is_migrated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Panel is already marked as migrated"
            )
        
        # Create migration record
        migration = PanelServerMigration(
            panel_id=panel_id,
            old_server_ip=panel.server_ip or "",
            new_server_ip=new_server_ip,
            old_url=panel.url,
            new_url=new_url,
            old_geo_location=panel.geo_location,
            new_geo_location=new_geo_location,
            old_country_code=panel.location.country_code if panel.location else None,
            new_country_code=new_country_code,
            migration_status="PENDING",
            performed_by=performed_by,
            reason=reason,
            notes=notes,
            started_at=datetime.now()
        )
        
        db.add(migration)
        
        # Update panel with previous data
        panel.previous_server_ip = panel.server_ip
        panel.previous_url = panel.url
        panel.is_migrated = True
        panel.migration_date = datetime.now()
        panel.migration_notes = notes
        
        await db.commit()
        await db.refresh(migration)
        
        # Format response
        result = {
            "migration_id": migration.id,
            "panel_id": panel_id,
            "panel_name": panel.name,
            "status": migration.migration_status,
            "old_server_ip": migration.old_server_ip,
            "new_server_ip": migration.new_server_ip,
            "old_url": migration.old_url,
            "new_url": migration.new_url,
            "started_at": migration.started_at,
            "message": "Panel migration initiated successfully"
        }
        
        return result
    
    async def complete_panel_migration(self, migration_id: int, affected_clients_count: int = 0,
                                       backup_file: Optional[str] = None, 
                                       notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete a panel migration.
        
        Args:
            migration_id: Migration ID
            affected_clients_count: Number of clients affected
            backup_file: Path to backup file (optional)
            notes: Additional notes (optional)
            
        Returns:
            Dict containing migration details
            
        Raises:
            HTTPException: If migration not found
        """
        db = await self._get_db()
        
        # Get migration
        stmt = select(PanelServerMigration).where(PanelServerMigration.id == migration_id)
        result = await db.execute(stmt)
        migration = result.scalars().first()
        
        if not migration:
            return None
        
        # Update migration record
        migration.migration_status = "COMPLETED"
        migration.completed_at = datetime.now()
        migration.affected_clients_count = affected_clients_count
        migration.backup_file = backup_file
        
        if notes:
            migration.notes = notes if not migration.notes else migration.notes + "\n\n" + notes
        
        # Get panel
        panel = await self.get_panel(migration.panel_id)
        if panel:
            # Update panel with new details
            panel.url = migration.new_url
            panel.server_ip = migration.new_server_ip
            if migration.new_geo_location:
                panel.geo_location = migration.new_geo_location
            
            # Handle the remark transition mapping
            await self.handle_panel_remark_transition(panel)
            
            # Handle notification if enabled
            settings = await self.get_settings()
            if settings.get("PANEL_MIGRATION_NOTIFICATION", "true").lower() == "true":
                # This would integrate with your notification system
                # Handled elsewhere - notification to users about the migration
                pass
        
        await db.commit()
        await db.refresh(migration)
        
        # Format response
        result = {
            "migration_id": migration.id,
            "panel_id": migration.panel_id,
            "status": migration.migration_status,
            "affected_clients_count": migration.affected_clients_count,
            "started_at": migration.started_at,
            "completed_at": migration.completed_at,
            "message": "Panel migration completed successfully"
        }
        
        return result
    
    async def handle_panel_remark_transition(self, panel: Panel) -> None:
        """
        مدیریت انتقال ریمارک‌های پنل در زمان مهاجرت به سرور جدید
        
        این متد یک نگاشت بین ریمارک‌های قبلی و آدرس سرور جدید ایجاد می‌کند
        تا کاربران بتوانند بدون تغییر ریمارک، به سرور جدید متصل شوند
        
        Args:
            panel: پنل در حال مهاجرت
            
        Returns:
            None
        """
        db = await self._get_db()
        settings = await self.get_settings()
        
        # دریافت لوکیشن پنل
        stmt = select(Location).where(Location.id == panel.location_id)
        result = await db.execute(stmt)
        location = result.scalars().first()
        
        if not location:
            logger.error(f"Location not found for panel {panel.id}")
            return
        
        # ایجاد یک نگاشت در تنظیمات برای ریدایرکت ریمارک‌های قدیمی به سرور جدید
        remark_map_key = f"REMARK_REDIRECT_MAP_{location.name}"
        
        # بررسی وجود نگاشت قبلی
        stmt = select(Settings).where(Settings.key == remark_map_key)
        result = await db.execute(stmt)
        remark_map_setting = result.scalars().first()
        
        # ساخت یا به‌روزرسانی نگاشت
        remark_map = {}
        
        if remark_map_setting:
            try:
                remark_map = json.loads(remark_map_setting.value)
            except:
                remark_map = {}
        
        # افزودن نگاشت جدید برای این پنل
        # ساختار: {
        #    "old_prefix": {
        #        "server_ip": "new_server_ip",
        #        "url": "new_url",
        #        "panel_id": panel_id
        #    }
        # }
        
        old_prefix = location.default_remark_prefix or location.name
        
        remark_map[old_prefix] = {
            "server_ip": panel.server_ip,
            "url": panel.url,
            "panel_id": panel.id,
            "migrated_at": datetime.now().isoformat()
        }
        
        # ذخیره نگاشت جدید
        if remark_map_setting:
            remark_map_setting.value = json.dumps(remark_map)
        else:
            new_setting = Settings(
                key=remark_map_key,
                value=json.dumps(remark_map),
                description=f"Remark redirect map for {location.name} location",
                is_public=False,
                group="system"
            )
            db.add(new_setting)
        
        # اضافه کردن تنظیم که آیا برای کلاینت‌های جدید از پیشوند جدید استفاده شود یا نه
        use_new_prefix_key = f"USE_NEW_PREFIX_FOR_{location.name}"
        stmt = select(Settings).where(Settings.key == use_new_prefix_key)
        result = await db.execute(stmt)
        use_new_prefix_setting = result.scalars().first()
        
        if not use_new_prefix_setting:
            new_setting = Settings(
                key=use_new_prefix_key,
                value="true",
                description=f"Use new prefix for newly created clients in {location.name}",
                is_public=False,
                group="system"
            )
            db.add(new_setting)
        
        # لاگ گزارش موفقیت
        logger.info(f"Remark transition mapping created for panel {panel.id} at location {location.name}")
        
        await db.commit()
    
    # ایجاد متد جدید برای دریافت سرور صحیح بر اساس ریمارک
    async def get_server_for_remark(self, remark: str) -> Dict[str, Any]:
        """
        تعیین سرور مناسب برای یک ریمارک
        
        این متد بررسی می‌کند که آیا ریمارک مربوط به سرور قدیمی است که نیاز به ریدایرکت دارد
        
        Args:
            remark: ریمارک کلاینت
            
        Returns:
            دیکشنری شامل اطلاعات سرور (server_ip و url)
        """
        db = await self._get_db()
        
        # استخراج پیشوند ریمارک (معمولاً قبل از اولین خط تیره)
        prefix = remark.split('-')[0] if '-' in remark else remark
        
        # بررسی تمام نگاشت‌های ریدایرکت موجود
        stmt = select(Settings).where(Settings.key.like("REMARK_REDIRECT_MAP_%"))
        result = await db.execute(stmt)
        redirect_maps = result.scalars().all()
        
        for redirect_map_setting in redirect_maps:
            try:
                redirect_map = json.loads(redirect_map_setting.value)
                if prefix in redirect_map:
                    # این ریمارک نیاز به ریدایرکت دارد
                    return redirect_map[prefix]
            except:
                continue
        
        # اگر نگاشتی پیدا نشد، باید اطلاعات را از روی ریمارک پیدا کنیم
        # معمولاً پیشوند نشان‌دهنده لوکیشن است
        stmt = select(Location).where(
            (Location.default_remark_prefix == prefix) | 
            (Location.name == prefix)
        )
        result = await db.execute(stmt)
        location = result.scalars().first()
        
        if location:
            # پیدا کردن اولین پنل فعال در این لوکیشن
            stmt = select(Panel).where(
                (Panel.location_id == location.id) &
                (Panel.is_active == True)
            ).order_by(Panel.priority.desc())
            result = await db.execute(stmt)
            panel = result.scalars().first()
            
            if panel:
                return {
                    "server_ip": panel.server_ip,
                    "url": panel.url,
                    "panel_id": panel.id
                }
        
        # اگر هیچ اطلاعاتی پیدا نشد، None برگردان
        return None
    
    async def get_panel_migrations(self, panel_id: int) -> List[Dict[str, Any]]:
        """
        Get migration history for a panel.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            List of migration records
        """
        db = await self._get_db()
        
        # Get migrations
        stmt = select(PanelServerMigration).where(
            PanelServerMigration.panel_id == panel_id
        ).order_by(PanelServerMigration.started_at.desc())
        
        result = await db.execute(stmt)
        migrations = result.scalars().all()
        
        # Format response
        formatted_migrations = [{
            "id": m.id,
            "panel_id": m.panel_id,
            "status": m.migration_status,
            "old_server_ip": m.old_server_ip,
            "new_server_ip": m.new_server_ip, 
            "old_url": m.old_url,
            "new_url": m.new_url,
            "affected_clients_count": m.affected_clients_count,
            "started_at": m.started_at,
            "completed_at": m.completed_at,
            "reason": m.reason
        } for m in migrations]
        
        return formatted_migrations
    
    async def get_migration_details(self, migration_id: int) -> Dict[str, Any]:
        """
        Get details of a specific migration.
        
        Args:
            migration_id: Migration ID
            
        Returns:
            Migration details
        """
        db = await self._get_db()
        
        # Get migration
        stmt = select(PanelServerMigration).where(PanelServerMigration.id == migration_id)
        result = await db.execute(stmt)
        migration = result.scalars().first()
        
        if not migration:
            return None
        
        # Format response
        formatted_migration = {
            "id": migration.id,
            "panel_id": migration.panel_id,
            "status": migration.migration_status,
            "old_server_ip": migration.old_server_ip,
            "new_server_ip": migration.new_server_ip,
            "old_url": migration.old_url,
            "new_url": migration.new_url,
            "old_geo_location": migration.old_geo_location,
            "new_geo_location": migration.new_geo_location,
            "old_country_code": migration.old_country_code,
            "new_country_code": migration.new_country_code,
            "backup_file": migration.backup_file,
            "affected_clients_count": migration.affected_clients_count,
            "started_at": migration.started_at,
            "completed_at": migration.completed_at,
            "reason": migration.reason,
            "notes": migration.notes
        }
        
        return formatted_migration
    
    # --- Panel Domain Methods ---
    
    async def add_panel_domain(self, panel_id: int, domain: str, 
                               is_primary: bool = False) -> Dict[str, Any]:
        """
        Add a domain to a panel.
        
        Args:
            panel_id: Panel ID
            domain: Domain name
            is_primary: Whether this is the primary domain
            
        Returns:
            Dict containing domain details
            
        Raises:
            HTTPException: If panel not found or domain already exists
        """
        db = await self._get_db()
        
        # Get panel
        panel = await self.get_panel(panel_id)
        if not panel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Panel with ID {panel_id} not found"
            )
        
        # Check if domain already exists
        stmt = select(PanelDomain).where(
            (PanelDomain.panel_id == panel_id) & 
            (PanelDomain.domain == domain)
        )
        result = await db.execute(stmt)
        existing_domain = result.scalars().first()
        
        if existing_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Domain {domain} already exists for this panel"
            )
        
        # If setting as primary, clear other primary domains
        if is_primary:
            await db.execute(
                update(PanelDomain)
                .where(PanelDomain.panel_id == panel_id)
                .values(is_primary=False)
            )
        
        # Create domain
        panel_domain = PanelDomain(
            panel_id=panel_id,
            domain=domain,
            is_primary=is_primary,
            is_active=True,
            created_at=datetime.now()
        )
        
        db.add(panel_domain)
        await db.commit()
        await db.refresh(panel_domain)
        
        # Format response
        result = {
            "id": panel_domain.id,
            "panel_id": panel_domain.panel_id,
            "domain": panel_domain.domain,
            "is_primary": panel_domain.is_primary,
            "is_active": panel_domain.is_active,
            "created_at": panel_domain.created_at
        }
        
        return result
    
    async def get_panel_domains(self, panel_id: int) -> List[Dict[str, Any]]:
        """
        Get all domains for a panel.
        
        Args:
            panel_id: Panel ID
            
        Returns:
            List of domain records
        """
        db = await self._get_db()
        
        # Get domains
        stmt = select(PanelDomain).where(PanelDomain.panel_id == panel_id)
        result = await db.execute(stmt)
        domains = result.scalars().all()
        
        # Format response
        formatted_domains = [{
            "id": d.id,
            "panel_id": d.panel_id,
            "domain": d.domain,
            "is_primary": d.is_primary,
            "is_active": d.is_active,
            "created_at": d.created_at,
            "updated_at": d.updated_at
        } for d in domains]
        
        return formatted_domains
    
    async def delete_panel_domain(self, panel_id: int, domain_id: int) -> bool:
        """
        Delete a domain from a panel.
        
        Args:
            panel_id: Panel ID
            domain_id: Domain ID
            
        Returns:
            True if domain was deleted, False otherwise
        """
        db = await self._get_db()
        
        # Check if domain exists and belongs to panel
        stmt = select(PanelDomain).where(
            (PanelDomain.id == domain_id) & 
            (PanelDomain.panel_id == panel_id)
        )
        result = await db.execute(stmt)
        domain = result.scalars().first()
        
        if not domain:
            return False
        
        # Don't allow deletion of primary domain if it's the only domain
        if domain.is_primary:
            # Check if this is the only domain
            stmt = select(func.count(PanelDomain.id)).where(PanelDomain.panel_id == panel_id)
            result = await db.execute(stmt)
            count = result.scalar()
            
            if count == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the only primary domain for a panel"
                )
        
        # Delete domain
        await db.execute(delete(PanelDomain).where(PanelDomain.id == domain_id))
        await db.commit()
        
        return True
        
    # --- Helper Methods ---
    
    async def get_settings(self) -> Dict[str, str]:
        """Get settings from database."""
        db = await self._get_db()
        
        # This assumes you have a Settings model/table
        stmt = select(Settings)
        result = await db.execute(stmt)
        settings_list = result.scalars().all()
        
        # Convert to dictionary
        settings = {s.key: s.value for s in settings_list}
        
        return settings 