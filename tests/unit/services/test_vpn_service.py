"""Unit tests for VPN service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vpn import VPNService
from app.schemas.vpn import (
    ServerCreate,
    ServerUpdate,
    VPNAccountCreate,
    VPNAccountUpdate
)
from app.models.vpn import Server, VPNAccount

class TestVPNServer:
    """Test VPN server operations."""
    
    @pytest.mark.asyncio
    async def test_create_server(self, db: AsyncSession):
        """Test creating a new VPN server."""
        vpn_service = VPNService(db)
        server_data = ServerCreate(
            name="Test Server",
            host="test.example.com",
            port=1194,
            protocol="udp",
            country="US",
            city="New York",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="Test server description"
        )
        
        server = await vpn_service.create_server(server_data)
        
        assert server.name == server_data.name
        assert server.host == server_data.host
        assert server.port == server_data.port
        assert server.protocol == server_data.protocol
        assert server.country == server_data.country
        assert server.city == server_data.city
        assert server.is_active == server_data.is_active
        assert server.max_connections == server_data.max_connections
        assert server.current_connections == server_data.current_connections
        assert server.bandwidth_limit == server_data.bandwidth_limit
        assert server.description == server_data.description
        assert server.id is not None
    
    @pytest.mark.asyncio
    async def test_get_servers(self, db: AsyncSession):
        """Test getting list of VPN servers."""
        vpn_service = VPNService(db)
        
        # Create multiple servers
        server_data1 = ServerCreate(
            name="Server 1",
            host="server1.example.com",
            port=1194,
            protocol="udp",
            country="US",
            city="New York",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="First test server"
        )
        
        server_data2 = ServerCreate(
            name="Server 2",
            host="server2.example.com",
            port=1194,
            protocol="udp",
            country="UK",
            city="London",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="Second test server"
        )
        
        await vpn_service.create_server(server_data1)
        await vpn_service.create_server(server_data2)
        
        servers = await vpn_service.get_servers()
        assert len(servers) == 2
        assert any(s.name == "Server 1" for s in servers)
        assert any(s.name == "Server 2" for s in servers)
    
    @pytest.mark.asyncio
    async def test_update_server(self, db: AsyncSession):
        """Test updating a VPN server."""
        vpn_service = VPNService(db)
        
        # Create a server
        server_data = ServerCreate(
            name="Test Server",
            host="test.example.com",
            port=1194,
            protocol="udp",
            country="US",
            city="New York",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="Test server description"
        )
        
        server = await vpn_service.create_server(server_data)
        
        # Update the server
        update_data = ServerUpdate(
            name="Updated Server",
            description="Updated description"
        )
        
        updated_server = await vpn_service.update_server(server.id, update_data)
        
        assert updated_server.name == update_data.name
        assert updated_server.description == update_data.description
        assert updated_server.host == server.host  # Unchanged
        assert updated_server.port == server.port  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_server(self, db: AsyncSession):
        """Test deleting a VPN server."""
        vpn_service = VPNService(db)
        
        # Create a server
        server_data = ServerCreate(
            name="Test Server",
            host="test.example.com",
            port=1194,
            protocol="udp",
            country="US",
            city="New York",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="Test server description"
        )
        
        server = await vpn_service.create_server(server_data)
        
        # Delete the server
        await vpn_service.delete_server(server.id)
        
        # Verify server is deleted
        deleted_server = await vpn_service.get_server(server.id)
        assert deleted_server is None

class TestVPNAccount:
    """Test VPN account operations."""
    
    @pytest.mark.asyncio
    async def test_create_account(self, db: AsyncSession):
        """Test creating a new VPN account."""
        vpn_service = VPNService(db)
        
        # Create a server first
        server_data = ServerCreate(
            name="Test Server",
            host="test.example.com",
            port=1194,
            protocol="udp",
            country="US",
            city="New York",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="Test server description"
        )
        
        server = await vpn_service.create_server(server_data)
        
        # Create account
        account_data = VPNAccountCreate(
            username="testuser",
            password="testpass123",
            server_id=server.id,
            is_active=True,
            bandwidth_limit=1000,
            expiry_date=None
        )
        
        account = await vpn_service.create_account(account_data)
        
        assert account.username == account_data.username
        assert account.server_id == account_data.server_id
        assert account.is_active == account_data.is_active
        assert account.bandwidth_limit == account_data.bandwidth_limit
        assert account.id is not None
    
    @pytest.mark.asyncio
    async def test_get_accounts(self, db: AsyncSession):
        """Test getting list of VPN accounts."""
        vpn_service = VPNService(db)
        
        # Create a server
        server_data = ServerCreate(
            name="Test Server",
            host="test.example.com",
            port=1194,
            protocol="udp",
            country="US",
            city="New York",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="Test server description"
        )
        
        server = await vpn_service.create_server(server_data)
        
        # Create multiple accounts
        account_data1 = VPNAccountCreate(
            username="user1",
            password="pass123",
            server_id=server.id,
            is_active=True,
            bandwidth_limit=1000,
            expiry_date=None
        )
        
        account_data2 = VPNAccountCreate(
            username="user2",
            password="pass456",
            server_id=server.id,
            is_active=True,
            bandwidth_limit=1000,
            expiry_date=None
        )
        
        await vpn_service.create_account(account_data1)
        await vpn_service.create_account(account_data2)
        
        accounts = await vpn_service.get_accounts()
        assert len(accounts) == 2
        assert any(a.username == "user1" for a in accounts)
        assert any(a.username == "user2" for a in accounts)
    
    @pytest.mark.asyncio
    async def test_update_account(self, db: AsyncSession):
        """Test updating a VPN account."""
        vpn_service = VPNService(db)
        
        # Create a server and account
        server_data = ServerCreate(
            name="Test Server",
            host="test.example.com",
            port=1194,
            protocol="udp",
            country="US",
            city="New York",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="Test server description"
        )
        
        server = await vpn_service.create_server(server_data)
        
        account_data = VPNAccountCreate(
            username="testuser",
            password="testpass123",
            server_id=server.id,
            is_active=True,
            bandwidth_limit=1000,
            expiry_date=None
        )
        
        account = await vpn_service.create_account(account_data)
        
        # Update the account
        update_data = VPNAccountUpdate(
            is_active=False,
            bandwidth_limit=2000
        )
        
        updated_account = await vpn_service.update_account(account.id, update_data)
        
        assert updated_account.is_active == update_data.is_active
        assert updated_account.bandwidth_limit == update_data.bandwidth_limit
        assert updated_account.username == account.username  # Unchanged
        assert updated_account.server_id == account.server_id  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_account(self, db: AsyncSession):
        """Test deleting a VPN account."""
        vpn_service = VPNService(db)
        
        # Create a server and account
        server_data = ServerCreate(
            name="Test Server",
            host="test.example.com",
            port=1194,
            protocol="udp",
            country="US",
            city="New York",
            is_active=True,
            max_connections=100,
            current_connections=0,
            bandwidth_limit=1000,
            description="Test server description"
        )
        
        server = await vpn_service.create_server(server_data)
        
        account_data = VPNAccountCreate(
            username="testuser",
            password="testpass123",
            server_id=server.id,
            is_active=True,
            bandwidth_limit=1000,
            expiry_date=None
        )
        
        account = await vpn_service.create_account(account_data)
        
        # Delete the account
        await vpn_service.delete_account(account.id)
        
        # Verify account is deleted
        deleted_account = await vpn_service.get_account(account.id)
        assert deleted_account is None 