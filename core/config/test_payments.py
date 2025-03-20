import pytest
from fastapi import status
from app.models.payment import Payment
from .base import TestBase
from .helpers import create_test_user, create_test_payment

class TestPayments(TestBase):
    """Test payment endpoints."""

    @pytest.mark.asyncio
    async def test_create_payment(self, client, db_session):
        """Test create payment."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Create payment request
        payment_data = {
            "amount": 20.0,
            "currency": "USD",
            "status": "pending"
        }
        response = client.post(
            "/api/v1/payments/",
            json=payment_data,
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_201_CREATED)
        data = response.json()
        assert data["amount"] == payment_data["amount"]
        assert data["currency"] == payment_data["currency"]
        assert data["status"] == payment_data["status"]
        assert data["user_id"] == user.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_payments(self, client, db_session):
        """Test get payments list."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Create test payments
        await create_test_payment(db_session, user.id)
        await create_test_payment(
            db_session,
            user.id,
            amount=30.0,
            currency="EUR",
            status="completed"
        )
        
        # Get payments request
        response = client.get(
            "/api/v1/payments/",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert all(isinstance(payment, dict) for payment in data)
        assert all("id" in payment for payment in data)
        assert all("amount" in payment for payment in data)
        assert all("currency" in payment for payment in data)
        assert all("status" in payment for payment in data)

    @pytest.mark.asyncio
    async def test_get_payment(self, client, db_session):
        """Test get payment by ID."""
        # Create test user and payment
        user = await create_test_user(db_session)
        payment = await create_test_payment(db_session, user.id)
        
        # Get payment request
        response = client.get(
            f"/api/v1/payments/{payment.id}",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert data["id"] == payment.id
        assert data["amount"] == payment.amount
        assert data["currency"] == payment.currency
        assert data["status"] == payment.status
        assert data["user_id"] == user.id

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self, client):
        """Test get non-existent payment."""
        # Get payment request with non-existent ID
        response = client.get(
            "/api/v1/payments/999",
            headers=self.get_auth_headers(self.test_user_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "Payment not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_update_payment_status(self, client, db_session):
        """Test update payment status."""
        # Create test user and payment
        user = await create_test_user(db_session)
        payment = await create_test_payment(db_session, user.id)
        
        # Update payment status request
        update_data = {
            "status": "completed"
        }
        response = client.put(
            f"/api/v1/payments/{payment.id}/status",
            json=update_data,
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert data["id"] == payment.id
        assert data["status"] == update_data["status"]
        assert data["amount"] == payment.amount
        assert data["currency"] == payment.currency
        assert data["user_id"] == user.id

    @pytest.mark.asyncio
    async def test_update_payment_status_not_found(self, client):
        """Test update status of non-existent payment."""
        # Update payment status request with non-existent ID
        update_data = {
            "status": "completed"
        }
        response = client.put(
            "/api/v1/payments/999/status",
            json=update_data,
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "Payment not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_user_payments(self, client, db_session):
        """Test get user's payments."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Create test payments for user
        await create_test_payment(db_session, user.id)
        await create_test_payment(
            db_session,
            user.id,
            amount=30.0,
            currency="EUR",
            status="completed"
        )
        
        # Get user payments request
        response = client.get(
            f"/api/v1/users/{user.id}/payments",
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert all(isinstance(payment, dict) for payment in data)
        assert all(payment["user_id"] == user.id for payment in data)
        assert all("id" in payment for payment in data)
        assert all("amount" in payment for payment in data)
        assert all("currency" in payment for payment in data)
        assert all("status" in payment for payment in data)

    @pytest.mark.asyncio
    async def test_get_user_payments_not_found(self, client):
        """Test get payments of non-existent user."""
        # Get user payments request with non-existent ID
        response = client.get(
            "/api/v1/users/999/payments",
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_404_NOT_FOUND)
        data = response.json()
        assert "detail" in data
        assert "User not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_payment_statistics(self, client, db_session):
        """Test get payment statistics."""
        # Create test user
        user = await create_test_user(db_session)
        
        # Create test payments with different statuses
        await create_test_payment(db_session, user.id, status="completed")
        await create_test_payment(
            db_session,
            user.id,
            amount=30.0,
            status="pending"
        )
        await create_test_payment(
            db_session,
            user.id,
            amount=40.0,
            status="failed"
        )
        
        # Get payment statistics request
        response = client.get(
            "/api/v1/payments/statistics",
            headers=self.get_auth_headers(self.test_superuser_token)
        )
        
        # Assert response
        self.assert_response(response, status.HTTP_200_OK)
        data = response.json()
        assert "total_amount" in data
        assert "total_count" in data
        assert "completed_count" in data
        assert "pending_count" in data
        assert "failed_count" in data
        assert data["total_count"] >= 3
        assert data["completed_count"] >= 1
        assert data["pending_count"] >= 1
        assert data["failed_count"] >= 1 