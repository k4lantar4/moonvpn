import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tests.utils import create_test_user, get_test_user_data

client = TestClient(app)

@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_register(self, db_session):
        """Test user registration endpoint."""
        user_data = get_test_user_data()
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data

    async def test_login(self, db_session):
        """Test user login endpoint."""
        # Create a test user first
        user_data = get_test_user_data()
        await create_test_user(db_session, **user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_get_current_user(self, db_session):
        """Test getting current user endpoint."""
        # Create and login a test user
        user_data = get_test_user_data()
        test_user = await create_test_user(db_session, **user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == user_data["email"]

@pytest.mark.asyncio
class TestVPNEndpoints:
    async def test_create_vpn_config(self, db_session):
        """Test VPN configuration creation endpoint."""
        # Create and login a test user
        user_data = get_test_user_data()
        test_user = await create_test_user(db_session, **user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        vpn_data = {
            "server_location": "US",
            "protocol": "wireguard",
            "port": 51820
        }
        
        response = client.post(
            "/api/v1/vpn/config",
            headers={"Authorization": f"Bearer {token}"},
            json=vpn_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["server_location"] == vpn_data["server_location"]
        assert data["protocol"] == vpn_data["protocol"]
        assert data["port"] == vpn_data["port"]
        assert data["user_id"] == test_user.id

    async def test_get_vpn_status(self, db_session):
        """Test getting VPN status endpoint."""
        # Create and login a test user
        user_data = get_test_user_data()
        test_user = await create_test_user(db_session, **user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/v1/vpn/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "last_connected" in data
        assert "bytes_sent" in data
        assert "bytes_received" in data

@pytest.mark.asyncio
class TestSubscriptionEndpoints:
    async def test_create_subscription(self, db_session):
        """Test subscription creation endpoint."""
        # Create and login a test user
        user_data = get_test_user_data()
        test_user = await create_test_user(db_session, **user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        subscription_data = {
            "plan_type": "premium",
            "duration_days": 30
        }
        
        response = client.post(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {token}"},
            json=subscription_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["plan_type"] == subscription_data["plan_type"]
        assert data["duration_days"] == subscription_data["duration_days"]
        assert data["user_id"] == test_user.id
        assert data["is_active"] is True

    async def test_get_subscription_info(self, db_session):
        """Test getting subscription information endpoint."""
        # Create and login a test user
        user_data = get_test_user_data()
        test_user = await create_test_user(db_session, **user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/v1/subscriptions/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "plan_type" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "is_active" in data

@pytest.mark.asyncio
class TestPaymentEndpoints:
    async def test_create_payment(self, db_session):
        """Test payment creation endpoint."""
        # Create and login a test user
        user_data = get_test_user_data()
        test_user = await create_test_user(db_session, **user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        payment_data = {
            "amount": 29.99,
            "currency": "USD",
            "payment_method": "crypto",
            "description": "Premium VPN Subscription"
        }
        
        response = client.post(
            "/api/v1/payments",
            headers={"Authorization": f"Bearer {token}"},
            json=payment_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == payment_data["amount"]
        assert data["currency"] == payment_data["currency"]
        assert data["payment_method"] == payment_data["payment_method"]
        assert data["user_id"] == test_user.id
        assert data["status"] == "pending"

    async def test_get_payment_history(self, db_session):
        """Test getting payment history endpoint."""
        # Create and login a test user
        user_data = get_test_user_data()
        test_user = await create_test_user(db_session, **user_data)
        
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/v1/payments/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for payment in data:
            assert "id" in payment
            assert "amount" in payment
            assert "status" in payment
            assert "created_at" in payment 