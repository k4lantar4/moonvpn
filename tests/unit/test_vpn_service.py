"""Unit tests for VPN service."""
import pytest
from sqlalchemy.orm import Session
from core.services.vpn import VPNService
from core.schemas.vpn import ServerCreate, ServerUpdate, VPNAccountCreate, VPNAccountUpdate
from core.database.models import Server, VPNAccount, User

def test_create_server(db: Session):
    """Test creating a new server."""
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
    
    server = vpn_service.create_server(server_data)
    
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

def test_get_server(db: Session):
    """Test getting a server by ID."""
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
    
    created_server = vpn_service.create_server(server_data)
    retrieved_server = vpn_service.get_server(created_server.id)
    
    assert retrieved_server is not None
    assert retrieved_server.id == created_server.id
    assert retrieved_server.name == created_server.name

def test_get_servers(db: Session):
    """Test getting list of servers."""
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
    
    vpn_service.create_server(server_data1)
    vpn_service.create_server(server_data2)
    
    servers = vpn_service.get_servers()
    assert len(servers) == 2
    assert any(s.name == "Server 1" for s in servers)
    assert any(s.name == "Server 2" for s in servers)

def test_update_server(db: Session):
    """Test updating a server."""
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
    
    created_server = vpn_service.create_server(server_data)
    update_data = ServerUpdate(
        name="Updated Server",
        description="Updated description"
    )
    updated_server = vpn_service.update_server(created_server.id, update_data)
    
    assert updated_server.name == "Updated Server"
    assert updated_server.description == "Updated description"
    assert updated_server.host == created_server.host
    assert updated_server.port == created_server.port

def test_create_vpn_account(db: Session, test_user_data):
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
    server = vpn_service.create_server(server_data)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create VPN account
    account_data = VPNAccountCreate(
        user_id=user.id,
        server_id=server.id,
        username="testvpn",
        password="testpass123",
        is_active=True,
        bandwidth_limit=1000,
        traffic_limit=10000
    )
    
    account = vpn_service.create_vpn_account(account_data)
    
    assert account.user_id == user.id
    assert account.server_id == server.id
    assert account.username == account_data.username
    assert account.is_active == account_data.is_active
    assert account.bandwidth_limit == account_data.bandwidth_limit
    assert account.traffic_limit == account_data.traffic_limit
    assert account.id is not None

def test_get_vpn_account(db: Session, test_user_data):
    """Test getting a VPN account by ID."""
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
    server = vpn_service.create_server(server_data)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create VPN account
    account_data = VPNAccountCreate(
        user_id=user.id,
        server_id=server.id,
        username="testvpn",
        password="testpass123",
        is_active=True,
        bandwidth_limit=1000,
        traffic_limit=10000
    )
    created_account = vpn_service.create_vpn_account(account_data)
    
    retrieved_account = vpn_service.get_vpn_account(created_account.id)
    
    assert retrieved_account is not None
    assert retrieved_account.id == created_account.id
    assert retrieved_account.user_id == created_account.user_id
    assert retrieved_account.server_id == created_account.server_id

def test_get_user_vpn_accounts(db: Session, test_user_data):
    """Test getting VPN accounts for a user."""
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
    server = vpn_service.create_server(server_data)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create multiple VPN accounts for the user
    account_data1 = VPNAccountCreate(
        user_id=user.id,
        server_id=server.id,
        username="testvpn1",
        password="testpass123",
        is_active=True,
        bandwidth_limit=1000,
        traffic_limit=10000
    )
    
    account_data2 = VPNAccountCreate(
        user_id=user.id,
        server_id=server.id,
        username="testvpn2",
        password="testpass123",
        is_active=True,
        bandwidth_limit=1000,
        traffic_limit=10000
    )
    
    vpn_service.create_vpn_account(account_data1)
    vpn_service.create_vpn_account(account_data2)
    
    accounts = vpn_service.get_user_vpn_accounts(user.id)
    assert len(accounts) == 2
    assert any(a.username == "testvpn1" for a in accounts)
    assert any(a.username == "testvpn2" for a in accounts)

def test_update_vpn_account(db: Session, test_user_data):
    """Test updating a VPN account."""
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
    server = vpn_service.create_server(server_data)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create VPN account
    account_data = VPNAccountCreate(
        user_id=user.id,
        server_id=server.id,
        username="testvpn",
        password="testpass123",
        is_active=True,
        bandwidth_limit=1000,
        traffic_limit=10000
    )
    created_account = vpn_service.create_vpn_account(account_data)
    
    update_data = VPNAccountUpdate(
        is_active=False,
        bandwidth_limit=2000
    )
    updated_account = vpn_service.update_vpn_account(created_account.id, update_data)
    
    assert updated_account.is_active is False
    assert updated_account.bandwidth_limit == 2000
    assert updated_account.username == created_account.username
    assert updated_account.user_id == created_account.user_id 