"""
Unit tests for the VPN service.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vpn import VPNServer, VPNAccount
from app.services.vpn_service import VPNService
from app.schemas.vpn import VPNServerCreate, VPNAccountCreate

pytestmark = pytest.mark.asyncio

class TestVPNService:
    """Test cases for VPNService."""

    async def test_create_vpn_server(self, db_session: AsyncSession):
        """Test creating a new VPN server."""
        # Arrange
        server_data = VPNServerCreate(
            host="test.vpn.example.com",
            port=443,
            protocol="tls",
            bandwidth_limit=1000,
            location="US",
            is_active=True
        )
        vpn_service = VPNService(db_session)

        # Act
        server = await vpn_service.create_server(server_data)

        # Assert
        assert server.host == server_data.host
        assert server.port == server_data.port
        assert server.protocol == server_data.protocol
        assert server.bandwidth_limit == server_data.bandwidth_limit
        assert server.location == server_data.location
        assert server.is_active == server_data.is_active

    async def test_create_vpn_account(self, db_session: AsyncSession, test_user, test_vpn_server):
        """Test creating a new VPN account."""
        # Arrange
        account_data = VPNAccountCreate(
            user_id=test_user.id,
            server_id=test_vpn_server.id,
            username="test_user",
            password="test_password123"
        )
        vpn_service = VPNService(db_session)

        # Act
        account = await vpn_service.create_account(account_data)

        # Assert
        assert account.user_id == test_user.id
        assert account.server_id == test_vpn_server.id
        assert account.username == account_data.username
        assert account.is_active is True

    async def test_get_vpn_account(self, db_session: AsyncSession, test_vpn_account):
        """Test retrieving a VPN account."""
        # Arrange
        vpn_service = VPNService(db_session)

        # Act
        account = await vpn_service.get_account(test_vpn_account.id)

        # Assert
        assert account is not None
        assert account.id == test_vpn_account.id
        assert account.user_id == test_vpn_account.user_id
        assert account.server_id == test_vpn_account.server_id

    async def test_get_user_vpn_accounts(self, db_session: AsyncSession, test_user, test_vpn_account):
        """Test retrieving all VPN accounts for a user."""
        # Arrange
        vpn_service = VPNService(db_session)

        # Act
        accounts = await vpn_service.get_user_accounts(test_user.id)

        # Assert
        assert len(accounts) > 0
        assert any(acc.id == test_vpn_account.id for acc in accounts)

    async def test_update_vpn_account_status(self, db_session: AsyncSession, test_vpn_account):
        """Test updating VPN account status."""
        # Arrange
        vpn_service = VPNService(db_session)

        # Act
        await vpn_service.update_account_status(test_vpn_account.id, False)

        # Assert
        updated_account = await vpn_service.get_account(test_vpn_account.id)
        assert updated_account.is_active is False

    async def test_delete_vpn_account(self, db_session: AsyncSession, test_vpn_account):
        """Test deleting a VPN account."""
        # Arrange
        vpn_service = VPNService(db_session)

        # Act
        await vpn_service.delete_account(test_vpn_account.id)

        # Assert
        deleted_account = await vpn_service.get_account(test_vpn_account.id)
        assert deleted_account is None

    async def test_get_active_servers(self, db_session: AsyncSession, test_vpn_server):
        """Test retrieving active VPN servers."""
        # Arrange
        vpn_service = VPNService(db_session)

        # Act
        servers = await vpn_service.get_active_servers()

        # Assert
        assert len(servers) > 0
        assert any(server.id == test_vpn_server.id for server in servers)

    async def test_update_server_status(self, db_session: AsyncSession, test_vpn_server):
        """Test updating VPN server status."""
        # Arrange
        vpn_service = VPNService(db_session)

        # Act
        await vpn_service.update_server_status(test_vpn_server.id, False)

        # Assert
        updated_server = await vpn_service.get_server(test_vpn_server.id)
        assert updated_server.is_active is False 