"""
VPN service for handling VPN-related operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func

from core.database.models import Server, VPNAccount, User
from core.schemas.vpn import (
    ServerCreate, ServerUpdate, VPNAccountCreate,
    VPNAccountUpdate, VPNAccountStats
)

class VPNService:
    """Service for handling VPN operations."""
    
    def __init__(self, db: Session):
        """Initialize the VPN service."""
        self.db = db
    
    def get_server(self, server_id: int) -> Optional[Server]:
        """Get server by ID."""
        return self.db.query(Server).filter(Server.id == server_id).first()
    
    def get_servers(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        location: Optional[str] = None,
        protocol: Optional[str] = None
    ) -> List[Server]:
        """Get list of servers with filtering."""
        query = self.db.query(Server)
        
        if search:
            query = query.filter(
                (Server.name.ilike(f"%{search}%")) |
                (Server.host.ilike(f"%{search}%"))
            )
        
        if status:
            query = query.filter(Server.status == status)
        
        if is_active is not None:
            query = query.filter(Server.is_active == is_active)
        
        if location:
            query = query.filter(Server.location == location)
        
        if protocol:
            query = query.filter(Server.protocol == protocol)
        
        return query.offset(skip).limit(limit).all()
    
    def get_servers_count(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        location: Optional[str] = None,
        protocol: Optional[str] = None
    ) -> int:
        """Get total count of servers with filtering."""
        query = self.db.query(Server)
        
        if search:
            query = query.filter(
                (Server.name.ilike(f"%{search}%")) |
                (Server.host.ilike(f"%{search}%"))
            )
        
        if status:
            query = query.filter(Server.status == status)
        
        if is_active is not None:
            query = query.filter(Server.is_active == is_active)
        
        if location:
            query = query.filter(Server.location == location)
        
        if protocol:
            query = query.filter(Server.protocol == protocol)
        
        return query.count()
    
    def create_server(self, data: ServerCreate) -> Server:
        """Create a new server."""
        server = Server(**data.model_dump())
        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)
        return server
    
    def update_server(self, server_id: int, data: ServerUpdate) -> Server:
        """Update server information."""
        server = self.get_server(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(server, field, value)
        
        server.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(server)
        return server
    
    def delete_server(self, server_id: int) -> bool:
        """Delete a server."""
        server = self.get_server(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        self.db.delete(server)
        self.db.commit()
        return True
    
    def get_vpn_account(self, account_id: int) -> Optional[VPNAccount]:
        """Get VPN account by ID."""
        return self.db.query(VPNAccount).filter(VPNAccount.id == account_id).first()
    
    def get_user_vpn_accounts(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[VPNAccount]:
        """Get list of user's VPN accounts with filtering."""
        query = self.db.query(VPNAccount).filter(VPNAccount.user_id == user_id)
        
        if status:
            query = query.filter(VPNAccount.status == status)
        
        if is_active is not None:
            query = query.filter(VPNAccount.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_user_vpn_accounts_count(
        self,
        user_id: int,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Get total count of user's VPN accounts with filtering."""
        query = self.db.query(VPNAccount).filter(VPNAccount.user_id == user_id)
        
        if status:
            query = query.filter(VPNAccount.status == status)
        
        if is_active is not None:
            query = query.filter(VPNAccount.is_active == is_active)
        
        return query.count()
    
    def create_vpn_account(self, data: VPNAccountCreate) -> VPNAccount:
        """Create a new VPN account."""
        # Check if server exists
        server = self.get_server(data.server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )
        
        # Check if user exists
        user = self.db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create new VPN account
        account = VPNAccount(**data.model_dump())
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def update_vpn_account(self, account_id: int, data: VPNAccountUpdate) -> VPNAccount:
        """Update VPN account information."""
        account = self.get_vpn_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VPN account not found"
            )
        
        # Update fields
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(account, field, value)
        
        account.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def delete_vpn_account(self, account_id: int) -> bool:
        """Delete a VPN account."""
        account = self.get_vpn_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VPN account not found"
            )
        
        self.db.delete(account)
        self.db.commit()
        return True
    
    def get_vpn_account_stats(self, account_id: int) -> VPNAccountStats:
        """Get VPN account statistics."""
        account = self.get_vpn_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VPN account not found"
            )
        
        # TODO: Implement actual statistics gathering
        return VPNAccountStats(
            account_id=account.id,
            traffic_used=account.traffic_used,
            traffic_limit=account.traffic_limit,
            connection_count=0,
            last_24h_traffic=0,
            last_7d_traffic=0,
            last_30d_traffic=0,
            uptime=None,
            last_connect=account.last_connect,
            last_disconnect=account.last_disconnect,
            current_ip=None,
            current_location=None,
            current_protocol=None,
            current_port=None,
            current_server=account.server.name,
            current_server_location=account.server.location,
            current_server_load=account.server.load,
            current_server_status=account.server.status,
            current_server_protocol=account.server.protocol,
            current_server_port=account.server.port,
            current_server_bandwidth_limit=account.server.bandwidth_limit,
            current_server_current_connections=account.server.current_connections,
            current_server_max_connections=account.server.max_connections,
            current_server_last_check=account.server.last_check,
            current_server_metadata=account.server.metadata,
            metadata=account.metadata
        )
    
    def update_traffic_usage(
        self,
        account_id: int,
        bytes_used: int
    ) -> VPNAccount:
        """Update VPN account traffic usage."""
        account = self.get_vpn_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VPN account not found"
            )
        
        account.traffic_used += bytes_used
        
        # Check if traffic limit exceeded
        if account.traffic_limit > 0 and account.traffic_used >= account.traffic_limit:
            account.status = "expired"
            account.is_active = False
        
        account.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def update_connection_status(
        self,
        account_id: int,
        is_connected: bool,
        ip_address: Optional[str] = None,
        location: Optional[str] = None
    ) -> VPNAccount:
        """Update VPN account connection status."""
        account = self.get_vpn_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="VPN account not found"
            )
        
        if is_connected:
            account.last_connect = datetime.utcnow()
            account.status = "connected"
        else:
            account.last_disconnect = datetime.utcnow()
            account.status = "active"
        
        if ip_address:
            account.metadata = account.metadata or {}
            account.metadata["last_ip"] = ip_address
        
        if location:
            account.metadata = account.metadata or {}
            account.metadata["last_location"] = location
        
        account.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(account)
        return account 