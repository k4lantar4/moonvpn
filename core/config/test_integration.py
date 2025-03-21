import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tests.utils import (
    create_test_user,
    create_test_vpn_config,
    create_test_subscription,
    create_test_payment,
    create_test_telegram_user,
    get_test_user_data
)
from app.core.config import settings

client = TestClient(app)

@pytest.mark.asyncio
class TestIntegration:
    async def test_user_registration_flow(self, db_session):
        """Test the complete user registration flow."""
        # Create test user
        user_data = get_test_user_data()
        user = await create_test_user(db_session, **user_data)
        
        # Create VPN config
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Create subscription
        subscription = await create_test_subscription(db_session, user.id)
        
        # Create payment
        payment = await create_test_payment(
            db_session,
            user.id,
            amount=29.99,
            status="completed"
        )
        
        # Create Telegram user
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Verify all components are properly linked
        assert vpn_config.user_id == user.id
        assert subscription.user_id == user.id
        assert payment.user_id == user.id
        assert telegram_user.user_id == user.id
        
        # Verify user can access all components
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Test VPN config access
        vpn_response = client.get(
            f"{settings.API_V1_STR}/vpn/config",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert vpn_response.status_code == 200
        
        # Test subscription access
        subscription_response = client.get(
            f"{settings.API_V1_STR}/vpn/subscription",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert subscription_response.status_code == 200
        
        # Test payment history access
        payment_response = client.get(
            f"{settings.API_V1_STR}/payments/history",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert payment_response.status_code == 200
        
        # Test Telegram status access
        telegram_response = client.get(
            f"{settings.API_V1_STR}/telegram/status",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert telegram_response.status_code == 200

    async def test_payment_subscription_flow(self, db_session):
        """Test the payment and subscription flow."""
        # Create test user
        user = await create_test_user(db_session, **get_test_user_data())
        
        # Create payment
        payment = await create_test_payment(
            db_session,
            user.id,
            amount=29.99,
            status="pending"
        )
        
        # Simulate payment completion
        payment.status = "completed"
        await db_session.commit()
        
        # Create subscription
        subscription = await create_test_subscription(
            db_session,
            user.id,
            plan_type="premium",
            duration_days=30
        )
        
        # Verify subscription is active
        assert subscription.is_active is True
        assert subscription.plan_type == "premium"
        
        # Test subscription access
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        subscription_response = client.get(
            f"{settings.API_V1_STR}/vpn/subscription",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert subscription_response.status_code == 200
        data = subscription_response.json()
        assert data["status"] == "active"
        assert data["plan_type"] == "premium"

    async def test_telegram_notification_flow(self, db_session):
        """Test the Telegram notification flow."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **get_test_user_data())
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Create VPN config
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Create subscription
        subscription = await create_test_subscription(db_session, user.id)
        
        # Test Telegram notification settings
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Update notification settings
        notification_settings = {
            "subscription_notifications": True,
            "payment_notifications": True,
            "system_notifications": True
        }
        
        update_response = client.put(
            f"{settings.API_V1_STR}/telegram/notifications",
            headers={"Authorization": f"Bearer {access_token}"},
            json=notification_settings
        )
        
        assert update_response.status_code == 200
        
        # Test sending notification
        notification_response = client.post(
            f"{settings.API_V1_STR}/telegram/test-notification",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert notification_response.status_code == 200
        assert notification_response.json()["status"] == "success"

    async def test_vpn_usage_tracking(self, db_session):
        """Test VPN usage tracking integration."""
        # Create test user and VPN config
        user = await create_test_user(db_session, **get_test_user_data())
        vpn_config = await create_test_vpn_config(db_session, user.id)
        
        # Create subscription
        subscription = await create_test_subscription(db_session, user.id)
        
        # Test VPN usage tracking
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get usage statistics
        usage_response = client.get(
            f"{settings.API_V1_STR}/vpn/usage",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert usage_response.status_code == 200
        data = usage_response.json()
        assert "total_usage" in data
        assert "monthly_usage" in data
        assert "bandwidth_used" in data
        
        # Test server status
        status_response = client.get(
            f"{settings.API_V1_STR}/vpn/server-status",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert "load" in status_data
        assert "uptime" in status_data
        assert "connected_users" in status_data 