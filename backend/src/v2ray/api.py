"""
3x-UI API Client for MoonVPN.
This module provides a client for interacting with 3x-UI panel API.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

import httpx
from django.conf import settings
from django.utils import timezone

from .models import V2RayServer, V2RayInbound, V2RayTraffic

logger = logging.getLogger(__name__)


class ThreeXUIClient:
    """Client for interacting with 3x-UI panel API."""
    
    def __init__(self, server: V2RayServer):
        """Initialize client with server details."""
        self.server = server
        self.base_url = server.api_url
        self.session = httpx.Client(
            base_url=self.base_url,
            timeout=10.0,
            verify=settings.VERIFY_SSL
        )
        self._token = None
    
    async def _login(self) -> bool:
        """Login to 3x-UI panel and get session token."""
        try:
            response = await self.session.post(
                "/login",
                json={
                    "username": self.server.username,
                    "password": self.server.password
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                self._token = data.get("token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self._token}"
                })
                return True
            
            return False
        
        except httpx.HTTPError as e:
            logger.error(f"Login failed for server {self.server}: {str(e)}")
            return False
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid session token."""
        if not self._token:
            return await self._login()
        return True
    
    async def get_inbounds(self) -> List[Dict]:
        """Get all inbounds from the server."""
        if not await self._ensure_authenticated():
            return []
        
        try:
            response = await self.session.get("/panel/api/inbounds/list")
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                return data.get("obj", [])
            
            return []
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to get inbounds from {self.server}: {str(e)}")
            return []
    
    async def sync_inbounds(self) -> bool:
        """Sync inbounds from server to database."""
        inbounds = await self.get_inbounds()
        
        if not inbounds:
            return False
        
        try:
            # Get existing inbounds for this server
            existing_inbounds = {
                i.inbound_id: i
                for i in self.server.inbounds.all()
            }
            
            # Process each inbound
            for inbound_data in inbounds:
                inbound_id = inbound_data.get("id")
                
                if inbound_id in existing_inbounds:
                    # Update existing inbound
                    inbound = existing_inbounds[inbound_id]
                    inbound.tag = inbound_data.get("remark", "")
                    inbound.protocol = inbound_data.get("protocol", "")
                    inbound.port = inbound_data.get("port", 0)
                    inbound.settings = inbound_data.get("settings", {})
                    inbound.stream_settings = inbound_data.get("streamSettings", {})
                    inbound.sniffing_enabled = inbound_data.get("sniffing", {}).get("enabled", True)
                    inbound.sniffing_dest_override = inbound_data.get("sniffing", {}).get("destOverride", [])
                    inbound.save()
                else:
                    # Create new inbound
                    V2RayInbound.objects.create(
                        server=self.server,
                        inbound_id=inbound_id,
                        tag=inbound_data.get("remark", ""),
                        protocol=inbound_data.get("protocol", ""),
                        port=inbound_data.get("port", 0),
                        settings=inbound_data.get("settings", {}),
                        stream_settings=inbound_data.get("streamSettings", {}),
                        sniffing_enabled=inbound_data.get("sniffing", {}).get("enabled", True),
                        sniffing_dest_override=inbound_data.get("sniffing", {}).get("destOverride", [])
                    )
            
            # Mark server as healthy
            self.server.is_healthy = True
            self.server.health_check_failures = 0
            self.server.last_check = timezone.now()
            self.server.save()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to sync inbounds for {self.server}: {str(e)}")
            
            # Update server health status
            self.server.is_healthy = False
            self.server.health_check_failures += 1
            self.server.last_check = timezone.now()
            self.server.save()
            
            return False
    
    async def get_traffic_stats(self) -> Dict[str, Dict[str, int]]:
        """Get traffic statistics for all inbounds."""
        if not await self._ensure_authenticated():
            return {}
        
        try:
            response = await self.session.get("/panel/api/inbounds/stats")
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                return data.get("obj", {})
            
            return {}
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to get traffic stats from {self.server}: {str(e)}")
            return {}
    
    async def sync_traffic(self) -> bool:
        """Sync traffic statistics from server to database."""
        stats = await self.get_traffic_stats()
        
        if not stats:
            return False
        
        try:
            # Get all inbounds for this server
            inbounds = {
                i.inbound_id: i
                for i in self.server.inbounds.all()
            }
            
            # Process traffic stats
            for inbound_id, traffic_data in stats.items():
                if inbound_id not in inbounds:
                    continue
                
                inbound = inbounds[inbound_id]
                
                # Create traffic record
                V2RayTraffic.objects.create(
                    server=self.server,
                    inbound=inbound,
                    upload=traffic_data.get("up", 0),
                    download=traffic_data.get("down", 0)
                )
            
            # Update server total traffic
            self.server.total_upload = sum(s.get("up", 0) for s in stats.values())
            self.server.total_download = sum(s.get("down", 0) for s in stats.values())
            self.server.save()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to sync traffic for {self.server}: {str(e)}")
            return False
    
    async def create_client(
        self,
        inbound_id: int,
        email: str,
        uuid: str = None,
        enable: bool = True,
        tls_settings: Dict = None,
        total_gb: int = 0,
        expire_days: int = 0
    ) -> Optional[Dict]:
        """Create a new client in an inbound."""
        if not await self._ensure_authenticated():
            return None
        
        try:
            client_data = {
                "email": email,
                "enable": enable,
                "expiryTime": int(timezone.now().timestamp() * 1000) + (expire_days * 86400 * 1000) if expire_days else 0,
                "total": total_gb * 1024 * 1024 * 1024 if total_gb else 0  # Convert GB to bytes
            }
            
            # Add UUID if provided
            if uuid:
                client_data["uuid"] = uuid
            
            # Add TLS settings if provided
            if tls_settings:
                client_data.update(tls_settings)
            
            response = await self.session.post(
                f"/panel/api/inbounds/{inbound_id}/clients",
                json=client_data
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                return data.get("obj")
            
            return None
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to create client in {self.server}: {str(e)}")
            return None
    
    async def delete_client(self, inbound_id: int, email: str) -> bool:
        """Delete a client from an inbound."""
        if not await self._ensure_authenticated():
            return False
        
        try:
            response = await self.session.delete(
                f"/panel/api/inbounds/{inbound_id}/clients/{email}"
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("success", False)
        
        except httpx.HTTPError as e:
            logger.error(f"Failed to delete client from {self.server}: {str(e)}")
            return False 