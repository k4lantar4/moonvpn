"""
VPN service manager implementation.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from app.core.managers.base import ResourceManager
from app.core.exceptions import PanelError, ResourceError
from app.core.models.vpn import VPNAccount, Server, Location
from app.core.schemas.vpn import VPNAccountCreate, VPNAccountUpdate, ServerCreate, ServerUpdate

class VPNManager(ResourceManager):
    """Manager for VPN service operations."""
    
    def __init__(self):
        super().__init__()
        self.resource_type = "vpn"
        
    async def _create_resource(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create VPN account or server."""
        try:
            if "type" not in data:
                raise ValidationError("Resource type not specified")
                
            if data["type"] == "account":
                account = VPNAccountCreate(**data)
                vpn_account = await VPNAccount.create(account)
                await self.metrics.record_resource_operation(
                    resource_type="vpn_account",
                    operation="create",
                    success=True
                )
                return vpn_account.dict()
                
            elif data["type"] == "server":
                server = ServerCreate(**data)
                vpn_server = await Server.create(server)
                await self.metrics.record_resource_operation(
                    resource_type="vpn_server",
                    operation="create",
                    success=True
                )
                return vpn_server.dict()
                
            else:
                raise ValidationError(f"Invalid resource type: {data['type']}")
                
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="create",
                success=False
            )
            raise ResourceError(f"Failed to create {self.resource_type}: {str(e)}")
            
    async def _get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get VPN account or server by ID."""
        try:
            # Try to get from cache first
            cache_key = f"vpn:{resource_id}"
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return cached_data
                
            # Get from database
            resource = await VPNAccount.get_by_id(resource_id) or await Server.get_by_id(resource_id)
            if not resource:
                return None
                
            # Cache the result
            await self.cache.set(cache_key, resource.dict(), ttl=300)
            return resource.dict()
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="get",
                success=False
            )
            raise ResourceError(f"Failed to get {self.resource_type}: {str(e)}")
            
    async def _update_resource(
        self,
        resource_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update VPN account or server."""
        try:
            # Get existing resource
            resource = await VPNAccount.get_by_id(resource_id) or await Server.get_by_id(resource_id)
            if not resource:
                raise ResourceError(f"{self.resource_type} not found: {resource_id}")
                
            # Update based on type
            if isinstance(resource, VPNAccount):
                update_data = VPNAccountUpdate(**data)
                updated = await VPNAccount.update(resource_id, update_data)
            else:
                update_data = ServerUpdate(**data)
                updated = await Server.update(resource_id, update_data)
                
            # Invalidate cache
            await self.cache.delete(f"vpn:{resource_id}")
            
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="update",
                success=True
            )
            return updated.dict()
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="update",
                success=False
            )
            raise ResourceError(f"Failed to update {self.resource_type}: {str(e)}")
            
    async def _delete_resource(self, resource_id: str) -> None:
        """Delete VPN account or server."""
        try:
            # Get resource type
            resource = await VPNAccount.get_by_id(resource_id) or await Server.get_by_id(resource_id)
            if not resource:
                raise ResourceError(f"{self.resource_type} not found: {resource_id}")
                
            # Delete based on type
            if isinstance(resource, VPNAccount):
                await VPNAccount.delete(resource_id)
            else:
                await Server.delete(resource_id)
                
            # Invalidate cache
            await self.cache.delete(f"vpn:{resource_id}")
            
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="delete",
                success=True
            )
            
        except Exception as e:
            await self.metrics.record_resource_operation(
                resource_type=self.resource_type,
                operation="delete",
                success=False
            )
            raise ResourceError(f"Failed to delete {self.resource_type}: {str(e)}")
            
    async def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """Get VPN account status."""
        try:
            account = await VPNAccount.get_by_id(account_id)
            if not account:
                raise ResourceError(f"VPN account not found: {account_id}")
                
            # Get status from panel
            status = await self.execute_with_retry(
                operation="get_account_status",
                func=self._get_panel_account_status,
                account_id=account_id
            )
            
            # Update account status
            await VPNAccount.update_status(account_id, status)
            
            return status
            
        except Exception as e:
            await self.metrics.record_error("get_account_status", str(e))
            raise PanelError(f"Failed to get account status: {str(e)}")
            
    async def _get_panel_account_status(self, account_id: str) -> Dict[str, Any]:
        """Get account status from VPN panel."""
        # Implementation depends on specific panel API
        pass
        
    async def reset_account_traffic(self, account_id: str) -> Dict[str, Any]:
        """Reset VPN account traffic."""
        try:
            account = await VPNAccount.get_by_id(account_id)
            if not account:
                raise ResourceError(f"VPN account not found: {account_id}")
                
            # Reset traffic in panel
            result = await self.execute_with_retry(
                operation="reset_account_traffic",
                func=self._reset_panel_account_traffic,
                account_id=account_id
            )
            
            # Update account traffic
            await VPNAccount.reset_traffic(account_id)
            
            return result
            
        except Exception as e:
            await self.metrics.record_error("reset_account_traffic", str(e))
            raise PanelError(f"Failed to reset account traffic: {str(e)}")
            
    async def _reset_panel_account_traffic(self, account_id: str) -> Dict[str, Any]:
        """Reset account traffic in VPN panel."""
        # Implementation depends on specific panel API
        pass
        
    async def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """Get VPN server status."""
        try:
            server = await Server.get_by_id(server_id)
            if not server:
                raise ResourceError(f"VPN server not found: {server_id}")
                
            # Get status from panel
            status = await self.execute_with_retry(
                operation="get_server_status",
                func=self._get_panel_server_status,
                server_id=server_id
            )
            
            # Update server status
            await Server.update_status(server_id, status)
            
            return status
            
        except Exception as e:
            await self.metrics.record_error("get_server_status", str(e))
            raise PanelError(f"Failed to get server status: {str(e)}")
            
    async def _get_panel_server_status(self, server_id: str) -> Dict[str, Any]:
        """Get server status from VPN panel."""
        # Implementation depends on specific panel API
        pass
        
    async def get_available_locations(self) -> List[Dict[str, Any]]:
        """Get available VPN server locations."""
        try:
            # Try to get from cache first
            cache_key = "vpn:locations"
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                return cached_data
                
            # Get from database
            locations = await Location.get_all_active()
            
            # Cache the result
            await self.cache.set(cache_key, [loc.dict() for loc in locations], ttl=3600)
            return [loc.dict() for loc in locations]
            
        except Exception as e:
            await self.metrics.record_error("get_available_locations", str(e))
            raise ResourceError(f"Failed to get available locations: {str(e)}")
            
    async def change_account_location(
        self,
        account_id: str,
        location_id: str
    ) -> Dict[str, Any]:
        """Change VPN account server location."""
        try:
            account = await VPNAccount.get_by_id(account_id)
            if not account:
                raise ResourceError(f"VPN account not found: {account_id}")
                
            location = await Location.get_by_id(location_id)
            if not location:
                raise ResourceError(f"Location not found: {location_id}")
                
            # Change location in panel
            result = await self.execute_with_retry(
                operation="change_account_location",
                func=self._change_panel_account_location,
                account_id=account_id,
                location_id=location_id
            )
            
            # Update account location
            await VPNAccount.update_location(account_id, location_id)
            
            return result
            
        except Exception as e:
            await self.metrics.record_error("change_account_location", str(e))
            raise PanelError(f"Failed to change account location: {str(e)}")
            
    async def _change_panel_account_location(
        self,
        account_id: str,
        location_id: str
    ) -> Dict[str, Any]:
        """Change account location in VPN panel."""
        # Implementation depends on specific panel API
        pass 