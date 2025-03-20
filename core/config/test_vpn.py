import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tests.utils import create_test_user, create_test_vpn_config
from app.core.config import settings

client = TestClient(app)

@pytest.mark.asyncio
class TestVPNEndpoints:
    async def test_get_vpn_config(self, db_session, test_user_data):
        """Test getting VPN configuration."""
        # Create test user and VPN config
        user = await create_test_user(db_session, **test_user_data)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get VPN config
        response = client.get(
            f"{settings.API_V1_STR}/vpn/config",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user.id
        assert data["is_active"] is True
        assert "config_data" in data

    async def test_get_vpn_config_unauthorized(self, db_session):
        """Test getting VPN config without authentication."""
        response = client.get(f"{settings.API_V1_STR}/vpn/config")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    async def test_update_vpn_config(self, db_session, test_user_data):
        """Test updating VPN configuration."""
        # Create test user and VPN config
        user = await create_test_user(db_session, **test_user_data)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Update VPN config
        new_config = {
            "server": "new.vpn.server",
            "port": 1195,
            "protocol": "udp"
        }
        
        response = client.put(
            f"{settings.API_V1_STR}/vpn/config",
            headers={"Authorization": f"Bearer {access_token}"},
            json=new_config
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["server"] == new_config["server"]
        assert data["port"] == new_config["port"]
        assert data["protocol"] == new_config["protocol"]

    async def test_deactivate_vpn_config(self, db_session, test_user_data):
        """Test deactivating VPN configuration."""
        # Create test user and VPN config
        user = await create_test_user(db_session, **test_user_data)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Deactivate VPN config
        response = client.post(
            f"{settings.API_V1_STR}/vpn/config/deactivate",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_get_subscription_status(self, db_session, test_user_data):
        """Test getting subscription status."""
        # Create test user and VPN config
        user = await create_test_user(db_session, **test_user_data)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get subscription status
        response = client.get(
            f"{settings.API_V1_STR}/vpn/subscription",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "expiry_date" in data
        assert "plan_type" in data

    async def test_extend_subscription(self, db_session, test_user_data):
        """Test extending subscription."""
        # Create test user and VPN config
        user = await create_test_user(db_session, **test_user_data)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Extend subscription
        response = client.post(
            f"{settings.API_V1_STR}/vpn/subscription/extend",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"months": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "expiry_date" in data
        assert "status" in data
        assert data["status"] == "active"

    async def test_get_usage_statistics(self, db_session, test_user_data):
        """Test getting usage statistics."""
        # Create test user and VPN config
        user = await create_test_user(db_session, **test_user_data)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get usage statistics
        response = client.get(
            f"{settings.API_V1_STR}/vpn/usage",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_usage" in data
        assert "monthly_usage" in data
        assert "bandwidth_used" in data

    async def test_get_server_status(self, db_session, test_user_data):
        """Test getting VPN server status."""
        # Create test user and VPN config
        user = await create_test_user(db_session, **test_user_data)
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get server status
        response = client.get(
            f"{settings.API_V1_STR}/vpn/server-status",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "load" in data
        assert "uptime" in data
        assert "connected_users" in data 