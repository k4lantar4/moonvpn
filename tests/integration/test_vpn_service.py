import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.vpn import VPNService
from app.models.user import User
from app.models.vpn_config import VPNConfig
from app.models.server import Server
from app.core.config import settings

@pytest.fixture
def vpn_service():
    """Create a VPN service instance."""
    return VPNService()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        email="test@example.com",
        phone_number="989123456789",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_server(db):
    """Create a test VPN server."""
    server = Server(
        name="Test Server",
        host="test.example.com",
        port=1194,
        protocol="udp",
        country="US",
        is_active=True,
        load=0.5
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return server

@pytest.mark.asyncio
async def test_create_vpn_config(vpn_service, test_user, test_server):
    """Test creating a VPN configuration."""
    with patch("app.services.vpn.VPNService._generate_certificates") as mock_generate_certs:
        mock_generate_certs.return_value = ("client_cert", "client_key")
        config = await vpn_service.create_vpn_config(test_user, test_server)
        assert config is not None
        assert config.user_id == test_user.id
        assert config.server_id == test_server.id
        assert config.client_cert == "client_cert"
        assert config.client_key == "client_key"

@pytest.mark.asyncio
async def test_get_vpn_status(vpn_service, test_user):
    """Test getting VPN status."""
    with patch("app.services.vpn.VPNService._check_connection") as mock_check:
        mock_check.return_value = True
        status = await vpn_service.get_vpn_status(test_user)
        assert status["is_connected"] is True
        assert "uptime" in status
        assert "bytes_sent" in status
        assert "bytes_received" in status

@pytest.mark.asyncio
async def test_connect_vpn(vpn_service, test_user, test_server):
    """Test connecting to VPN."""
    with patch("app.services.vpn.VPNService._start_vpn_connection") as mock_start:
        mock_start.return_value = True
        result = await vpn_service.connect_vpn(test_user, test_server)
        assert result is True
        mock_start.assert_called_once()

@pytest.mark.asyncio
async def test_disconnect_vpn(vpn_service, test_user):
    """Test disconnecting from VPN."""
    with patch("app.services.vpn.VPNService._stop_vpn_connection") as mock_stop:
        mock_stop.return_value = True
        result = await vpn_service.disconnect_vpn(test_user)
        assert result is True
        mock_stop.assert_called_once()

@pytest.mark.asyncio
async def test_get_available_servers(vpn_service):
    """Test getting available VPN servers."""
    servers = await vpn_service.get_available_servers()
    assert isinstance(servers, list)
    for server in servers:
        assert server.is_active is True
        assert server.load < 1.0

@pytest.mark.asyncio
async def test_get_server_status(vpn_service, test_server):
    """Test getting server status."""
    with patch("app.services.vpn.VPNService._check_server_health") as mock_check:
        mock_check.return_value = {
            "status": "healthy",
            "load": 0.5,
            "uptime": 3600,
            "connected_clients": 10
        }
        status = await vpn_service.get_server_status(test_server)
        assert status["status"] == "healthy"
        assert status["load"] == 0.5
        assert status["uptime"] == 3600
        assert status["connected_clients"] == 10

@pytest.mark.asyncio
async def test_renew_vpn_config(vpn_service, test_user, test_server):
    """Test renewing VPN configuration."""
    with patch("app.services.vpn.VPNService._generate_certificates") as mock_generate_certs:
        mock_generate_certs.return_value = ("new_client_cert", "new_client_key")
        config = await vpn_service.renew_vpn_config(test_user, test_server)
        assert config is not None
        assert config.client_cert == "new_client_cert"
        assert config.client_key == "new_client_key"

@pytest.mark.asyncio
async def test_get_usage_stats(vpn_service, test_user):
    """Test getting VPN usage statistics."""
    with patch("app.services.vpn.VPNService._get_connection_stats") as mock_stats:
        mock_stats.return_value = {
            "total_connections": 100,
            "total_duration": 3600,
            "total_data": 1024 * 1024 * 100  # 100 MB
        }
        stats = await vpn_service.get_usage_stats(test_user)
        assert stats["total_connections"] == 100
        assert stats["total_duration"] == 3600
        assert stats["total_data"] == 1024 * 1024 * 100

@pytest.mark.asyncio
async def test_error_handling(vpn_service, test_user, test_server):
    """Test error handling in VPN service."""
    # Test connection error
    with patch("app.services.vpn.VPNService._start_vpn_connection") as mock_start:
        mock_start.side_effect = Exception("Connection failed")
        with pytest.raises(Exception) as exc_info:
            await vpn_service.connect_vpn(test_user, test_server)
        assert str(exc_info.value) == "Connection failed"

    # Test certificate generation error
    with patch("app.services.vpn.VPNService._generate_certificates") as mock_generate_certs:
        mock_generate_certs.side_effect = Exception("Certificate generation failed")
        with pytest.raises(Exception) as exc_info:
            await vpn_service.create_vpn_config(test_user, test_server)
        assert str(exc_info.value) == "Certificate generation failed"

@pytest.mark.asyncio
async def test_server_selection(vpn_service):
    """Test VPN server selection logic."""
    with patch("app.services.vpn.VPNService.get_available_servers") as mock_get_servers:
        mock_get_servers.return_value = [
            Server(name="Server 1", load=0.8),
            Server(name="Server 2", load=0.3),
            Server(name="Server 3", load=0.6)
        ]
        server = await vpn_service.select_best_server()
        assert server.name == "Server 2"  # Should select server with lowest load
        assert server.load == 0.3 