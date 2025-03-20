import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tests.utils import create_test_user, create_test_payment
from app.core.config import settings

client = TestClient(app)

@pytest.mark.asyncio
class TestPaymentEndpoints:
    async def test_create_payment(self, db_session, test_user_data):
        """Test creating a new payment."""
        # Create test user
        user = await create_test_user(db_session, **test_user_data)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Create payment
        payment_data = {
            "amount": 29.99,
            "currency": "USD",
            "plan_type": "premium",
            "duration_months": 3
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/payments/create",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payment_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user.id
        assert data["amount"] == payment_data["amount"]
        assert data["currency"] == payment_data["currency"]
        assert data["status"] == "pending"

    async def test_get_payment_status(self, db_session, test_user_data):
        """Test getting payment status."""
        # Create test user and payment
        user = await create_test_user(db_session, **test_user_data)
        payment = await create_test_payment(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get payment status
        response = client.get(
            f"{settings.API_V1_STR}/payments/{payment.id}/status",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == payment.id
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_payment_history(self, db_session, test_user_data):
        """Test getting payment history."""
        # Create test user and multiple payments
        user = await create_test_user(db_session, **test_user_data)
        payment1 = await create_test_payment(db_session, user.id)
        payment2 = await create_test_payment(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get payment history
        response = client.get(
            f"{settings.API_V1_STR}/payments/history",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert any(p["id"] == payment1.id for p in data)
        assert any(p["id"] == payment2.id for p in data)

    async def test_cancel_payment(self, db_session, test_user_data):
        """Test canceling a payment."""
        # Create test user and payment
        user = await create_test_user(db_session, **test_user_data)
        payment = await create_test_payment(db_session, user.id)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Cancel payment
        response = client.post(
            f"{settings.API_V1_STR}/payments/{payment.id}/cancel",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["id"] == payment.id

    async def test_get_payment_methods(self, db_session, test_user_data):
        """Test getting available payment methods."""
        # Create test user
        await create_test_user(db_session, **test_user_data)
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get payment methods
        response = client.get(
            f"{settings.API_V1_STR}/payments/methods",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("id" in method for method in data)
        assert all("name" in method for method in data)
        assert all("enabled" in method for method in data)

    async def test_get_payment_statistics(self, db_session, test_user_data):
        """Test getting payment statistics."""
        # Create test user and multiple payments
        user = await create_test_user(db_session, **test_user_data)
        await create_test_payment(db_session, user.id, amount=29.99, status="completed")
        await create_test_payment(db_session, user.id, amount=49.99, status="completed")
        
        # Login to get access token
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get payment statistics
        response = client.get(
            f"{settings.API_V1_STR}/payments/statistics",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_amount" in data
        assert "total_transactions" in data
        assert "successful_transactions" in data
        assert "failed_transactions" in data
        assert "average_amount" in data

    async def test_webhook_payment_update(self, db_session, test_user_data):
        """Test payment webhook update."""
        # Create test user and payment
        user = await create_test_user(db_session, **test_user_data)
        payment = await create_test_payment(db_session, user.id)
        
        # Simulate webhook update
        webhook_data = {
            "payment_id": payment.id,
            "status": "completed",
            "transaction_id": "test_transaction_123",
            "amount": payment.amount,
            "currency": payment.currency
        }
        
        response = client.post(
            f"{settings.API_V1_STR}/payments/webhook",
            json=webhook_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Payment status updated successfully" 