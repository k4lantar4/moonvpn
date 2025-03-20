"""
API endpoint tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.vpn import VPNServer, VPNAccount
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.payment import Payment, PaymentTransaction
from app.models.telegram import TelegramUser, TelegramChat

client = TestClient(app)

class TestUserEndpoints:
    """Test cases for user endpoints."""

    def test_register_user(self, test_user_data):
        """Test user registration endpoint."""
        response = client.post("/api/v1/users/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["phone"] == test_user_data["phone"]
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "created_at" in data

    def test_login_user(self, test_user_data):
        """Test user login endpoint."""
        # First register the user
        client.post("/api/v1/users/register", json=test_user_data)
        
        # Then try to login
        login_data = {
            "phone": test_user_data["phone"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/users/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_get_user_profile(self, test_user_token):
        """Test getting user profile endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/users/profile", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "phone" in data
        assert "email" in data

    def test_update_user_profile(self, test_user_token):
        """Test updating user profile endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
        response = client.put("/api/v1/users/profile", headers=headers, json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]

class TestVPNAndpoints:
    """Test cases for VPN endpoints."""

    def test_get_vpn_servers(self, test_user_token):
        """Test getting VPN servers endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/vpn/servers", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_vpn_accounts(self, test_user_token):
        """Test getting user's VPN accounts endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/vpn/accounts", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_vpn_account(self, test_user_token, test_vpn_server):
        """Test creating VPN account endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        account_data = {
            "server_id": test_vpn_server.id,
            "username": "test_vpn_user",
            "password": "test_vpn_pass"
        }
        response = client.post("/api/v1/vpn/accounts", headers=headers, json=account_data)
        assert response.status_code == 201
        data = response.json()
        assert data["server_id"] == account_data["server_id"]
        assert data["username"] == account_data["username"]

class TestSubscriptionEndpoints:
    """Test cases for subscription endpoints."""

    def test_get_subscription_plans(self, test_user_token):
        """Test getting subscription plans endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/subscriptions/plans", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_user_subscriptions(self, test_user_token):
        """Test getting user's subscriptions endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/subscriptions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_subscription(self, test_user_token, test_subscription_plan):
        """Test creating subscription endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        subscription_data = {
            "plan_id": test_subscription_plan.id,
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-02-01T00:00:00Z"
        }
        response = client.post("/api/v1/subscriptions", headers=headers, json=subscription_data)
        assert response.status_code == 201
        data = response.json()
        assert data["plan_id"] == subscription_data["plan_id"]

class TestPaymentEndpoints:
    """Test cases for payment endpoints."""

    def test_create_payment(self, test_user_token, test_subscription_plan):
        """Test creating payment endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        payment_data = {
            "plan_id": test_subscription_plan.id,
            "amount": test_subscription_plan.price,
            "currency": "USD",
            "payment_method": "credit_card"
        }
        response = client.post("/api/v1/payments", headers=headers, json=payment_data)
        assert response.status_code == 201
        data = response.json()
        assert data["plan_id"] == payment_data["plan_id"]
        assert data["amount"] == payment_data["amount"]

    def test_get_user_payments(self, test_user_token):
        """Test getting user's payments endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/payments", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_payment_status(self, test_user_token, test_payment):
        """Test getting payment status endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get(f"/api/v1/payments/{test_payment.id}/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

class TestTelegramEndpoints:
    """Test cases for Telegram endpoints."""

    def test_connect_telegram(self, test_user_token):
        """Test connecting Telegram account endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        telegram_data = {
            "telegram_id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User"
        }
        response = client.post("/api/v1/telegram/connect", headers=headers, json=telegram_data)
        assert response.status_code == 201
        data = response.json()
        assert data["telegram_id"] == telegram_data["telegram_id"]

    def test_get_telegram_status(self, test_user_token):
        """Test getting Telegram connection status endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/v1/telegram/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "is_connected" in data

    def test_disconnect_telegram(self, test_user_token):
        """Test disconnecting Telegram account endpoint."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.delete("/api/v1/telegram/disconnect", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Telegram account disconnected successfully" 