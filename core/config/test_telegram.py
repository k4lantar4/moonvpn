import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tests.utils import create_test_user, create_test_telegram_user
from app.core.config import settings

client = TestClient(app)

@pytest.mark.asyncio
class TestTelegramEndpoints:
    async def test_webhook_update(self, db_session, test_user_data):
        """Test Telegram webhook update."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **test_user_data)
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Simulate Telegram update
        update_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": telegram_user.telegram_id,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "chat": {
                    "id": telegram_user.telegram_id,
                    "type": "private"
                },
                "date": 1234567890,
                "text": "/start"
            }
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/telegram/webhook",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    async def test_get_telegram_status(self, db_session, test_user_data):
        """Test getting Telegram connection status."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **test_user_data)
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get Telegram status
        response = client.get(
            f"{settings.API_V1_STR}/telegram/status",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        assert "username" in data
        assert "last_active" in data

    async def test_disconnect_telegram(self, db_session, test_user_data):
        """Test disconnecting Telegram account."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **test_user_data)
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Disconnect Telegram
        response = client.post(
            f"{settings.API_V1_STR}/telegram/disconnect",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Telegram account disconnected successfully"

    async def test_get_telegram_notifications(self, db_session, test_user_data):
        """Test getting Telegram notification settings."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **test_user_data)
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get notification settings
        response = client.get(
            f"{settings.API_V1_STR}/telegram/notifications",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "subscription_notifications" in data
        assert "payment_notifications" in data
        assert "system_notifications" in data

    async def test_update_telegram_notifications(self, db_session, test_user_data):
        """Test updating Telegram notification settings."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **test_user_data)
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Update notification settings
        notification_settings = {
            "subscription_notifications": True,
            "payment_notifications": False,
            "system_notifications": True
        }
        
        response = client.put(
            f"{settings.API_V1_STR}/telegram/notifications",
            headers={"Authorization": f"Bearer {access_token}"},
            json=notification_settings
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["subscription_notifications"] == notification_settings["subscription_notifications"]
        assert data["payment_notifications"] == notification_settings["payment_notifications"]
        assert data["system_notifications"] == notification_settings["system_notifications"]

    async def test_send_test_notification(self, db_session, test_user_data):
        """Test sending a test notification."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **test_user_data)
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Send test notification
        response = client.post(
            f"{settings.API_V1_STR}/telegram/test-notification",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Test notification sent successfully"

    async def test_get_telegram_commands(self, db_session, test_user_data):
        """Test getting available Telegram commands."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **test_user_data)
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get available commands
        response = client.get(
            f"{settings.API_V1_STR}/telegram/commands",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("command" in cmd for cmd in data)
        assert all("description" in cmd for cmd in data) 