import pytest
from fastapi import status
from app.models.vpn_config import VPNConfig
from .base import TestBase
from .helpers import create_test_user, create_test_vpn_config

class TestVPNConfigs(TestBase):
    """Test VPN configuration endpoints."""

    @pytest.mark.asyncio
    async def test_create_vpn_config(self, client, db_session):
        """Test create VPN configuration."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Create VPN config request
        vpn_data = {
            "name": "New VPN Config",
            "server": "new.vpn.server",
            "port": 1195,
            "protocol": "udp",
            "is_active": True
        }
        response = client.post(
            "/api/v1/vpn-configs/",
            json=vpn_data,
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_201_CREATED)
        data = response.json()
        assert data["name"] == vpn_data["name"]
        assert data["server"] == vpn_data["server"]
        assert data["port"] == vpn_data["port"]
        assert data["protocol"] == vpn_data["protocol"]
        assert data["is_active"] == vpn_data["is_active"]
        assert data["user_id"] == user.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_vpn_config_duplicate_name(self, client, db_session):
        """Test create VPN config with duplicate name."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Create existing VPN config
        await create_test_vpn_config(db_session, user.id)
        
        # Create VPN config request with duplicate name
        vpn_data = {
            "name": "test_vpn_config",
            "server": "new.vpn.server",
            "port": 1195,
            "protocol": "udp",
            "is_active": True
        }
        response = client.post(
            "/api/v1/vpn-configs/",
            json=vpn_data,
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        assert "detail" in data
        assert "VPN configuration name already exists" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_vpn_configs(self, client, db_session):
        """Test get VPN configurations list."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Create test VPN configs
        await create_test_vpn_config(db_session, user.id)
        await create_test_vpn_config(
            db_session,
            user.id,
            name="vpn_config_2",
            server="vpn2.server"
        )
        
        # Get VPN configs request
        response = client.get(
            "/api/v1/vpn-configs/",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert all(isinstance(config, dict) for config in data)
        assert all("id" in config for config in data)
        assert all("name" in config for config in data)
        assert all("server" in config for config in data)

    @pytest.mark.asyncio
    async def test_get_vpn_config(self, client, db_session):
        """Test get VPN configuration by ID."""
        # Create test user and VPN config
        user = await create_test_user(db_session)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Get VPN config request
        response = client.get(
            f"/api/v1/vpn-configs/{vpn_config.id}",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert data["id"] == vpn_config.id
        assert data["name"] == vpn_config.name
        assert data["server"] == vpn_config.server
        assert data["port"] == vpn_config.port
        assert data["protocol"] == vpn_config.protocol
        assert data["is_active"] == vpn_config.is_active
        assert data["user_id"] == user.id

    @pytest.mark.asyncio
    async def test_get_vpn_config_not_found(self, client):
        """Test get non-existent VPN configuration."""
        # Get VPN config request with non-existent ID
        response = client.get(
            "/api/v1/vpn-configs/999",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "VPN configuration not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_update_vpn_config(self, client, db_session):
        """Test update VPN configuration."""
        # Create test user and VPN config
        user = await create_test_user(db_session)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Update VPN config request
        update_data = {
            "name": "Updated VPN Config",
            "server": "updated.vpn.server",
            "port": 1196,
            "protocol": "tcp",
            "is_active": False
        }
        response = client.put(
            f"/api/v1/vpn-configs/{vpn_config.id}",
            json=update_data,
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert data["id"] == vpn_config.id
        assert data["name"] == update_data["name"]
        assert data["server"] == update_data["server"]
        assert data["port"] == update_data["port"]
        assert data["protocol"] == update_data["protocol"]
        assert data["is_active"] == update_data["is_active"]
        assert data["user_id"] == user.id

    @pytest.mark.asyncio
    async def test_update_vpn_config_not_found(self, client):
        """Test update non-existent VPN configuration."""
        # Update VPN config request with non-existent ID
        update_data = {
            "name": "Updated VPN Config",
            "server": "updated.vpn.server",
            "port": 1196,
            "protocol": "tcp",
            "is_active": False
        }
        response = client.put(
            "/api/v1/vpn-configs/999",
            json=update_data,
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "VPN configuration not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_delete_vpn_config(self, client, db_session):
        """Test delete VPN configuration."""
        # Create test user and VPN config
        user = await create_test_user(db_session)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Delete VPN config request
        response = client.delete(
            f"/api/v1/vpn-configs/{vpn_config.id}",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_204_NO_CONTENT)
        
        # Verify VPN config is deleted
        response = client.get(
            f"/api/v1/vpn-configs/{vpn_config.id}",
            headers=self.get_auth_headers(self.test_user_token)
        )
        self.assert_response(response, status.HTTP_404_NOT_FOUND)

    @pytest.mark.asyncio
    async def test_delete_vpn_config_not_found(self, client):
        """Test delete non-existent VPN configuration."""
        # Delete VPN config request with non-existent ID
        response = client.delete(
            "/api/v1/vpn-configs/999",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "VPN configuration not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_vpn_config_file(self, client, db_session):
        """Test get VPN configuration file."""
        # Create test user and VPN config
        user = await create_test_user(db_session)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Get VPN config file request
        response = client.get(
            f"/api/v1/vpn-configs/{vpn_config.id}/file",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        assert response.headers["content-type"] == "application/octet-stream"
        assert response.headers["content-disposition"] == f'attachment; filename="{vpn_config.name}.ovpn"' 