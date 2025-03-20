"""API tests for payment endpoints."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from core.database.models import User
from core.schemas.user import UserCreate
from core.services.user import UserService
from core.services.payment import PaymentService
from core.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    SubscriptionCreate,
    SubscriptionUpdate,
    PlanCreate,
    PlanUpdate
)

def test_create_payment(client: TestClient, db: Session, test_user_data):
    """Test creating a payment through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create payment data
    payment_data = {
        "user_id": user.id,
        "amount": 100.00,
        "currency": "USD",
        "status": "pending",
        "payment_method": "credit_card",
        "description": "Test payment"
    }
    
    response = client.post("/api/v1/payments/", json=payment_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_id"] == user.id
    assert data["amount"] == payment_data["amount"]
    assert data["currency"] == payment_data["currency"]
    assert data["status"] == payment_data["status"]
    assert data["payment_method"] == payment_data["payment_method"]
    assert data["description"] == payment_data["description"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_get_payment(client: TestClient, db: Session, test_user_data):
    """Test getting a payment through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a payment
    payment_service = PaymentService(db)
    payment_data = PaymentCreate(
        user_id=user.id,
        amount=100.00,
        currency="USD",
        status="pending",
        payment_method="credit_card",
        description="Test payment"
    )
    payment = payment_service.create_payment(payment_data)
    
    response = client.get(f"/api/v1/payments/{payment.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == payment.id
    assert data["user_id"] == payment.user_id
    assert data["amount"] == payment.amount
    assert data["currency"] == payment.currency
    assert data["status"] == payment.status

def test_get_user_payments(client: TestClient, db: Session, test_user_data):
    """Test getting user payments through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create multiple payments
    payment_service = PaymentService(db)
    payment_data1 = PaymentCreate(
        user_id=user.id,
        amount=100.00,
        currency="USD",
        status="completed",
        payment_method="credit_card",
        description="First test payment"
    )
    
    payment_data2 = PaymentCreate(
        user_id=user.id,
        amount=200.00,
        currency="USD",
        status="pending",
        payment_method="credit_card",
        description="Second test payment"
    )
    
    payment_service.create_payment(payment_data1)
    payment_service.create_payment(payment_data2)
    
    response = client.get(f"/api/v1/payments/user/{user.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert any(p["amount"] == 100.00 for p in data)
    assert any(p["amount"] == 200.00 for p in data)

def test_update_payment(client: TestClient, db: Session, test_user_data):
    """Test updating a payment through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a payment
    payment_service = PaymentService(db)
    payment_data = PaymentCreate(
        user_id=user.id,
        amount=100.00,
        currency="USD",
        status="pending",
        payment_method="credit_card",
        description="Test payment"
    )
    payment = payment_service.create_payment(payment_data)
    
    update_data = {
        "status": "completed",
        "description": "Updated payment"
    }
    
    response = client.put(f"/api/v1/payments/{payment.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == update_data["status"]
    assert data["description"] == update_data["description"]
    assert data["amount"] == payment.amount
    assert data["user_id"] == payment.user_id

def test_create_subscription(client: TestClient, db: Session, test_user_data):
    """Test creating a subscription through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a plan
    payment_service = PaymentService(db)
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    # Create subscription data
    subscription_data = {
        "user_id": user.id,
        "plan_id": plan.id,
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "status": "active",
        "auto_renew": True
    }
    
    response = client.post("/api/v1/payments/subscriptions/", json=subscription_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_id"] == user.id
    assert data["plan_id"] == plan.id
    assert data["status"] == subscription_data["status"]
    assert data["auto_renew"] == subscription_data["auto_renew"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_get_subscription(client: TestClient, db: Session, test_user_data):
    """Test getting a subscription through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a plan
    payment_service = PaymentService(db)
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    # Create a subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status="active",
        auto_renew=True
    )
    subscription = payment_service.create_subscription(subscription_data)
    
    response = client.get(f"/api/v1/payments/subscriptions/{subscription.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == subscription.id
    assert data["user_id"] == subscription.user_id
    assert data["plan_id"] == subscription.plan_id
    assert data["status"] == subscription.status
    assert data["auto_renew"] == subscription.auto_renew

def test_get_user_subscriptions(client: TestClient, db: Session, test_user_data):
    """Test getting user subscriptions through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a plan
    payment_service = PaymentService(db)
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    # Create multiple subscriptions
    subscription_data1 = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status="active",
        auto_renew=True
    )
    
    subscription_data2 = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status="expired",
        auto_renew=False
    )
    
    payment_service.create_subscription(subscription_data1)
    payment_service.create_subscription(subscription_data2)
    
    response = client.get(f"/api/v1/payments/subscriptions/user/{user.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert any(s["status"] == "active" for s in data)
    assert any(s["status"] == "expired" for s in data)

def test_update_subscription(client: TestClient, db: Session, test_user_data):
    """Test updating a subscription through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a plan
    payment_service = PaymentService(db)
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    # Create a subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status="active",
        auto_renew=True
    )
    subscription = payment_service.create_subscription(subscription_data)
    
    update_data = {
        "status": "cancelled",
        "auto_renew": False
    }
    
    response = client.put(f"/api/v1/payments/subscriptions/{subscription.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == update_data["status"]
    assert data["auto_renew"] == update_data["auto_renew"]
    assert data["user_id"] == subscription.user_id
    assert data["plan_id"] == subscription.plan_id

def test_create_plan(client: TestClient, db: Session):
    """Test creating a plan through the API."""
    plan_data = {
        "name": "Premium",
        "description": "Premium VPN plan",
        "price": 9.99,
        "duration_days": 30,
        "features": ["feature1", "feature2"],
        "is_active": True
    }
    
    response = client.post("/api/v1/payments/plans/", json=plan_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == plan_data["name"]
    assert data["description"] == plan_data["description"]
    assert data["price"] == plan_data["price"]
    assert data["duration_days"] == plan_data["duration_days"]
    assert data["features"] == plan_data["features"]
    assert data["is_active"] == plan_data["is_active"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_get_plan(client: TestClient, db: Session):
    """Test getting a plan through the API."""
    # Create a plan
    payment_service = PaymentService(db)
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    response = client.get(f"/api/v1/payments/plans/{plan.id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == plan.id
    assert data["name"] == plan.name
    assert data["price"] == plan.price
    assert data["features"] == plan.features

def test_get_plans(client: TestClient, db: Session):
    """Test getting list of plans through the API."""
    # Create multiple plans
    payment_service = PaymentService(db)
    plan_data1 = PlanCreate(
        name="Basic",
        description="Basic VPN plan",
        price=4.99,
        duration_days=30,
        features=["feature1"],
        is_active=True
    )
    
    plan_data2 = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    
    payment_service.create_plan(plan_data1)
    payment_service.create_plan(plan_data2)
    
    response = client.get("/api/v1/payments/plans/")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    assert any(p["name"] == "Basic" for p in data)
    assert any(p["name"] == "Premium" for p in data)

def test_update_plan(client: TestClient, db: Session):
    """Test updating a plan through the API."""
    # Create a plan
    payment_service = PaymentService(db)
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    update_data = {
        "name": "Premium Plus",
        "price": 14.99,
        "features": ["feature1", "feature2", "feature3"]
    }
    
    response = client.put(f"/api/v1/payments/plans/{plan.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == update_data["name"]
    assert data["price"] == update_data["price"]
    assert data["features"] == update_data["features"]
    assert data["duration_days"] == plan.duration_days
    assert data["is_active"] == plan.is_active

def test_get_payment_stats(client: TestClient, db: Session, test_user_data):
    """Test getting payment statistics through the API."""
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create multiple payments
    payment_service = PaymentService(db)
    payment_data1 = PaymentCreate(
        user_id=user.id,
        amount=100.00,
        currency="USD",
        status="completed",
        payment_method="credit_card",
        description="First test payment"
    )
    
    payment_data2 = PaymentCreate(
        user_id=user.id,
        amount=200.00,
        currency="USD",
        status="completed",
        payment_method="credit_card",
        description="Second test payment"
    )
    
    payment_service.create_payment(payment_data1)
    payment_service.create_payment(payment_data2)
    
    response = client.get("/api/v1/payments/stats/")
    assert response.status_code == 200
    data = response.json()
    
    assert "total_amount" in data
    assert "total_transactions" in data
    assert "last_24h" in data
    assert "last_7d" in data
    assert "last_30d" in data
    assert data["total_transactions"] >= 2
    assert data["total_amount"] >= 300.00 