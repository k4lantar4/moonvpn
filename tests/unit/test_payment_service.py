"""Unit tests for payment service."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from core.services.payment import PaymentService
from core.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    SubscriptionCreate,
    SubscriptionUpdate,
    PlanCreate,
    PlanUpdate
)
from core.database.models import Payment, Subscription, Plan, User

def test_create_payment(db: Session, test_user_data):
    """Test creating a new payment."""
    payment_service = PaymentService(db)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create payment
    payment_data = PaymentCreate(
        user_id=user.id,
        amount=100.00,
        currency="USD",
        status="pending",
        payment_method="credit_card",
        description="Test payment"
    )
    
    payment = payment_service.create_payment(payment_data)
    
    assert payment.user_id == user.id
    assert payment.amount == payment_data.amount
    assert payment.currency == payment_data.currency
    assert payment.status == payment_data.status
    assert payment.payment_method == payment_data.payment_method
    assert payment.description == payment_data.description
    assert payment.id is not None

def test_get_payment(db: Session, test_user_data):
    """Test getting a payment by ID."""
    payment_service = PaymentService(db)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create payment
    payment_data = PaymentCreate(
        user_id=user.id,
        amount=100.00,
        currency="USD",
        status="pending",
        payment_method="credit_card",
        description="Test payment"
    )
    created_payment = payment_service.create_payment(payment_data)
    
    retrieved_payment = payment_service.get_payment(created_payment.id)
    
    assert retrieved_payment is not None
    assert retrieved_payment.id == created_payment.id
    assert retrieved_payment.user_id == created_payment.user_id
    assert retrieved_payment.amount == created_payment.amount

def test_get_user_payments(db: Session, test_user_data):
    """Test getting payments for a user."""
    payment_service = PaymentService(db)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create multiple payments
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
    
    payments = payment_service.get_user_payments(user.id)
    assert len(payments) == 2
    assert any(p.amount == 100.00 for p in payments)
    assert any(p.amount == 200.00 for p in payments)

def test_update_payment(db: Session, test_user_data):
    """Test updating a payment."""
    payment_service = PaymentService(db)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create payment
    payment_data = PaymentCreate(
        user_id=user.id,
        amount=100.00,
        currency="USD",
        status="pending",
        payment_method="credit_card",
        description="Test payment"
    )
    created_payment = payment_service.create_payment(payment_data)
    
    update_data = PaymentUpdate(
        status="completed",
        description="Updated payment"
    )
    updated_payment = payment_service.update_payment(created_payment.id, update_data)
    
    assert updated_payment.status == "completed"
    assert updated_payment.description == "Updated payment"
    assert updated_payment.amount == created_payment.amount
    assert updated_payment.user_id == created_payment.user_id

def test_create_subscription(db: Session, test_user_data):
    """Test creating a new subscription."""
    payment_service = PaymentService(db)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a plan
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    # Create subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status="active",
        auto_renew=True
    )
    
    subscription = payment_service.create_subscription(subscription_data)
    
    assert subscription.user_id == user.id
    assert subscription.plan_id == plan.id
    assert subscription.status == subscription_data.status
    assert subscription.auto_renew == subscription_data.auto_renew
    assert subscription.id is not None

def test_get_subscription(db: Session, test_user_data):
    """Test getting a subscription by ID."""
    payment_service = PaymentService(db)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a plan
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    # Create subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status="active",
        auto_renew=True
    )
    created_subscription = payment_service.create_subscription(subscription_data)
    
    retrieved_subscription = payment_service.get_subscription(created_subscription.id)
    
    assert retrieved_subscription is not None
    assert retrieved_subscription.id == created_subscription.id
    assert retrieved_subscription.user_id == created_subscription.user_id
    assert retrieved_subscription.plan_id == created_subscription.plan_id

def test_get_user_subscriptions(db: Session, test_user_data):
    """Test getting subscriptions for a user."""
    payment_service = PaymentService(db)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a plan
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
    
    subscriptions = payment_service.get_user_subscriptions(user.id)
    assert len(subscriptions) == 2
    assert any(s.status == "active" for s in subscriptions)
    assert any(s.status == "expired" for s in subscriptions)

def test_update_subscription(db: Session, test_user_data):
    """Test updating a subscription."""
    payment_service = PaymentService(db)
    
    # Create a user
    user_service = UserService(db)
    user = user_service.create_user(UserCreate(**test_user_data))
    
    # Create a plan
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    plan = payment_service.create_plan(plan_data)
    
    # Create subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        status="active",
        auto_renew=True
    )
    created_subscription = payment_service.create_subscription(subscription_data)
    
    update_data = SubscriptionUpdate(
        status="cancelled",
        auto_renew=False
    )
    updated_subscription = payment_service.update_subscription(created_subscription.id, update_data)
    
    assert updated_subscription.status == "cancelled"
    assert updated_subscription.auto_renew is False
    assert updated_subscription.user_id == created_subscription.user_id
    assert updated_subscription.plan_id == created_subscription.plan_id

def test_create_plan(db: Session):
    """Test creating a new plan."""
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
    
    assert plan.name == plan_data.name
    assert plan.description == plan_data.description
    assert plan.price == plan_data.price
    assert plan.duration_days == plan_data.duration_days
    assert plan.features == plan_data.features
    assert plan.is_active == plan_data.is_active
    assert plan.id is not None

def test_get_plan(db: Session):
    """Test getting a plan by ID."""
    payment_service = PaymentService(db)
    
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    created_plan = payment_service.create_plan(plan_data)
    
    retrieved_plan = payment_service.get_plan(created_plan.id)
    
    assert retrieved_plan is not None
    assert retrieved_plan.id == created_plan.id
    assert retrieved_plan.name == created_plan.name
    assert retrieved_plan.price == created_plan.price

def test_get_plans(db: Session):
    """Test getting list of plans."""
    payment_service = PaymentService(db)
    
    # Create multiple plans
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
    
    plans = payment_service.get_plans()
    assert len(plans) == 2
    assert any(p.name == "Basic" for p in plans)
    assert any(p.name == "Premium" for p in plans)

def test_update_plan(db: Session):
    """Test updating a plan."""
    payment_service = PaymentService(db)
    
    plan_data = PlanCreate(
        name="Premium",
        description="Premium VPN plan",
        price=9.99,
        duration_days=30,
        features=["feature1", "feature2"],
        is_active=True
    )
    created_plan = payment_service.create_plan(plan_data)
    
    update_data = PlanUpdate(
        name="Premium Plus",
        price=14.99,
        features=["feature1", "feature2", "feature3"]
    )
    updated_plan = payment_service.update_plan(created_plan.id, update_data)
    
    assert updated_plan.name == "Premium Plus"
    assert updated_plan.price == 14.99
    assert updated_plan.features == ["feature1", "feature2", "feature3"]
    assert updated_plan.duration_days == created_plan.duration_days
    assert updated_plan.is_active == created_plan.is_active 