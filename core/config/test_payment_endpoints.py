"""Integration tests for payment API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.payment import PaymentCreate, SubscriptionCreate
from app.core.security import create_access_token

client = TestClient(app)

class TestPaymentEndpoints:
    """Test payment API endpoints."""
    
    def test_create_payment(self, db, authorized_client):
        """Test creating a new payment via API."""
        payment_data = {
            "user_id": 1,
            "amount": 10.00,
            "currency": "USD",
            "status": "pending",
            "payment_method": "stripe",
            "payment_id": "test_payment_id",
            "description": "Test payment"
        }
        
        response = authorized_client.post("/api/v1/payments/", json=payment_data)
        assert response.status_code == 201
        data = response.json()
        
        assert data["user_id"] == payment_data["user_id"]
        assert data["amount"] == payment_data["amount"]
        assert data["currency"] == payment_data["currency"]
        assert data["status"] == payment_data["status"]
        assert data["payment_method"] == payment_data["payment_method"]
        assert data["payment_id"] == payment_data["payment_id"]
        assert data["description"] == payment_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_payments(self, db, authorized_client):
        """Test getting list of payments via API."""
        # Create multiple payments
        payment_data1 = {
            "user_id": 1,
            "amount": 10.00,
            "currency": "USD",
            "status": "completed",
            "payment_method": "stripe",
            "payment_id": "test_payment_id_1",
            "description": "First test payment"
        }
        
        payment_data2 = {
            "user_id": 1,
            "amount": 20.00,
            "currency": "USD",
            "status": "pending",
            "payment_method": "stripe",
            "payment_id": "test_payment_id_2",
            "description": "Second test payment"
        }
        
        authorized_client.post("/api/v1/payments/", json=payment_data1)
        authorized_client.post("/api/v1/payments/", json=payment_data2)
        
        response = authorized_client.get("/api/v1/payments/")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        assert any(p["amount"] == 10.00 for p in data)
        assert any(p["amount"] == 20.00 for p in data)
    
    def test_get_payment(self, db, authorized_client):
        """Test getting a specific payment via API."""
        # Create a payment
        payment_data = {
            "user_id": 1,
            "amount": 10.00,
            "currency": "USD",
            "status": "pending",
            "payment_method": "stripe",
            "payment_id": "test_payment_id",
            "description": "Test payment"
        }
        
        response = authorized_client.post("/api/v1/payments/", json=payment_data)
        payment_id = response.json()["id"]
        
        response = authorized_client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == payment_data["user_id"]
        assert data["amount"] == payment_data["amount"]
        assert data["currency"] == payment_data["currency"]
        assert data["status"] == payment_data["status"]
        assert data["payment_method"] == payment_data["payment_method"]
        assert data["payment_id"] == payment_data["payment_id"]
        assert data["description"] == payment_data["description"]
        assert data["id"] == payment_id
    
    def test_update_payment(self, db, authorized_client):
        """Test updating a payment via API."""
        # Create a payment
        payment_data = {
            "user_id": 1,
            "amount": 10.00,
            "currency": "USD",
            "status": "pending",
            "payment_method": "stripe",
            "payment_id": "test_payment_id",
            "description": "Test payment"
        }
        
        response = authorized_client.post("/api/v1/payments/", json=payment_data)
        payment_id = response.json()["id"]
        
        # Update the payment
        update_data = {
            "status": "completed",
            "description": "Updated payment description"
        }
        
        response = authorized_client.put(f"/api/v1/payments/{payment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == update_data["status"]
        assert data["description"] == update_data["description"]
        assert data["amount"] == payment_data["amount"]  # Unchanged
        assert data["currency"] == payment_data["currency"]  # Unchanged
    
    def test_delete_payment(self, db, authorized_client):
        """Test deleting a payment via API."""
        # Create a payment
        payment_data = {
            "user_id": 1,
            "amount": 10.00,
            "currency": "USD",
            "status": "pending",
            "payment_method": "stripe",
            "payment_id": "test_payment_id",
            "description": "Test payment"
        }
        
        response = authorized_client.post("/api/v1/payments/", json=payment_data)
        payment_id = response.json()["id"]
        
        # Delete the payment
        response = authorized_client.delete(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 204
        
        # Verify payment is deleted
        response = authorized_client.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 404

class TestSubscriptionEndpoints:
    """Test subscription API endpoints."""
    
    def test_create_subscription(self, db, authorized_client):
        """Test creating a new subscription via API."""
        subscription_data = {
            "user_id": 1,
            "plan_id": 1,
            "status": "active",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "auto_renew": True,
            "payment_id": "test_payment_id"
        }
        
        response = authorized_client.post("/api/v1/subscriptions/", json=subscription_data)
        assert response.status_code == 201
        data = response.json()
        
        assert data["user_id"] == subscription_data["user_id"]
        assert data["plan_id"] == subscription_data["plan_id"]
        assert data["status"] == subscription_data["status"]
        assert data["start_date"] == subscription_data["start_date"]
        assert data["end_date"] == subscription_data["end_date"]
        assert data["auto_renew"] == subscription_data["auto_renew"]
        assert data["payment_id"] == subscription_data["payment_id"]
        assert "id" in data
    
    def test_get_subscriptions(self, db, authorized_client):
        """Test getting list of subscriptions via API."""
        # Create multiple subscriptions
        subscription_data1 = {
            "user_id": 1,
            "plan_id": 1,
            "status": "active",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "auto_renew": True,
            "payment_id": "test_payment_id_1"
        }
        
        subscription_data2 = {
            "user_id": 1,
            "plan_id": 2,
            "status": "cancelled",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "auto_renew": False,
            "payment_id": "test_payment_id_2"
        }
        
        authorized_client.post("/api/v1/subscriptions/", json=subscription_data1)
        authorized_client.post("/api/v1/subscriptions/", json=subscription_data2)
        
        response = authorized_client.get("/api/v1/subscriptions/")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 2
        assert any(s["plan_id"] == 1 for s in data)
        assert any(s["plan_id"] == 2 for s in data)
    
    def test_get_subscription(self, db, authorized_client):
        """Test getting a specific subscription via API."""
        # Create a subscription
        subscription_data = {
            "user_id": 1,
            "plan_id": 1,
            "status": "active",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "auto_renew": True,
            "payment_id": "test_payment_id"
        }
        
        response = authorized_client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = response.json()["id"]
        
        response = authorized_client.get(f"/api/v1/subscriptions/{subscription_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == subscription_data["user_id"]
        assert data["plan_id"] == subscription_data["plan_id"]
        assert data["status"] == subscription_data["status"]
        assert data["start_date"] == subscription_data["start_date"]
        assert data["end_date"] == subscription_data["end_date"]
        assert data["auto_renew"] == subscription_data["auto_renew"]
        assert data["payment_id"] == subscription_data["payment_id"]
        assert data["id"] == subscription_id
    
    def test_update_subscription(self, db, authorized_client):
        """Test updating a subscription via API."""
        # Create a subscription
        subscription_data = {
            "user_id": 1,
            "plan_id": 1,
            "status": "active",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "auto_renew": True,
            "payment_id": "test_payment_id"
        }
        
        response = authorized_client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = response.json()["id"]
        
        # Update the subscription
        update_data = {
            "status": "cancelled",
            "auto_renew": False
        }
        
        response = authorized_client.put(f"/api/v1/subscriptions/{subscription_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == update_data["status"]
        assert data["auto_renew"] == update_data["auto_renew"]
        assert data["plan_id"] == subscription_data["plan_id"]  # Unchanged
        assert data["start_date"] == subscription_data["start_date"]  # Unchanged
    
    def test_delete_subscription(self, db, authorized_client):
        """Test deleting a subscription via API."""
        # Create a subscription
        subscription_data = {
            "user_id": 1,
            "plan_id": 1,
            "status": "active",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "auto_renew": True,
            "payment_id": "test_payment_id"
        }
        
        response = authorized_client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = response.json()["id"]
        
        # Delete the subscription
        response = authorized_client.delete(f"/api/v1/subscriptions/{subscription_id}")
        assert response.status_code == 204
        
        # Verify subscription is deleted
        response = authorized_client.get(f"/api/v1/subscriptions/{subscription_id}")
        assert response.status_code == 404 