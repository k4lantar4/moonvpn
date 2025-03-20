"""Integration tests for payment system."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from core.database.models import User, Payment, Subscription, Plan
from core.schemas.user import UserCreate
from core.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    SubscriptionCreate,
    SubscriptionUpdate,
    PlanCreate,
    PlanUpdate
)
from core.services.user import UserService
from core.services.payment import PaymentService

def test_payment_workflow(db: Session, test_user_data):
    """Test complete payment workflow."""
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
    
    # Create a payment
    payment_data = PaymentCreate(
        user_id=user.id,
        amount=plan.price,
        currency="USD",
        status="pending",
        payment_method="credit_card",
        description="Premium plan payment"
    )
    payment = payment_service.create_payment(payment_data)
    
    # Update payment status to completed
    payment_update = PaymentUpdate(status="completed")
    payment_service.update_payment(payment.id, payment_update)
    
    # Create a subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
        status="active",
        auto_renew=True
    )
    subscription = payment_service.create_subscription(subscription_data)
    
    # Verify all components are properly linked
    assert payment.user_id == user.id
    assert payment.amount == plan.price
    assert payment.status == "completed"
    
    assert subscription.user_id == user.id
    assert subscription.plan_id == plan.id
    assert subscription.status == "active"
    assert subscription.auto_renew is True

def test_subscription_renewal(db: Session, test_user_data):
    """Test subscription renewal process."""
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
    
    # Create initial subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
        status="active",
        auto_renew=True
    )
    subscription = payment_service.create_subscription(subscription_data)
    
    # Create renewal payment
    payment_data = PaymentCreate(
        user_id=user.id,
        amount=plan.price,
        currency="USD",
        status="pending",
        payment_method="credit_card",
        description="Subscription renewal payment"
    )
    payment = payment_service.create_payment(payment_data)
    
    # Update payment status to completed
    payment_update = PaymentUpdate(status="completed")
    payment_service.update_payment(payment.id, payment_update)
    
    # Update subscription with new dates
    subscription_update = SubscriptionUpdate(
        start_date=subscription.end_date,
        end_date=subscription.end_date + timedelta(days=plan.duration_days)
    )
    updated_subscription = payment_service.update_subscription(subscription.id, subscription_update)
    
    # Verify renewal
    assert payment.status == "completed"
    assert updated_subscription.status == "active"
    assert updated_subscription.auto_renew is True
    assert updated_subscription.start_date == subscription.end_date
    assert updated_subscription.end_date > subscription.end_date

def test_subscription_cancellation(db: Session, test_user_data):
    """Test subscription cancellation process."""
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
    
    # Create subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
        status="active",
        auto_renew=True
    )
    subscription = payment_service.create_subscription(subscription_data)
    
    # Cancel subscription
    subscription_update = SubscriptionUpdate(
        status="cancelled",
        auto_renew=False
    )
    updated_subscription = payment_service.update_subscription(subscription.id, subscription_update)
    
    # Verify cancellation
    assert updated_subscription.status == "cancelled"
    assert updated_subscription.auto_renew is False
    assert updated_subscription.end_date == subscription.end_date

def test_plan_deactivation(db: Session, test_user_data):
    """Test plan deactivation and its effect on subscriptions."""
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
    
    # Create subscription
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
        status="active",
        auto_renew=True
    )
    subscription = payment_service.create_subscription(subscription_data)
    
    # Deactivate plan
    plan_update = PlanUpdate(is_active=False)
    updated_plan = payment_service.update_plan(plan.id, plan_update)
    
    # Verify plan deactivation
    assert updated_plan.is_active is False
    
    # Verify existing subscription is not affected
    assert subscription.status == "active"
    assert subscription.auto_renew is True

def test_payment_statistics(db: Session, test_user_data):
    """Test payment statistics calculation."""
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
        status="completed",
        payment_method="credit_card",
        description="Second test payment"
    )
    
    payment_service.create_payment(payment_data1)
    payment_service.create_payment(payment_data2)
    
    # Get statistics
    stats = payment_service.get_payment_stats()
    
    # Verify statistics
    assert stats.total_transactions >= 2
    assert stats.total_amount >= 300.00
    assert "last_24h" in stats
    assert "last_7d" in stats
    assert "last_30d" in stats

def test_subscription_expiration(db: Session, test_user_data):
    """Test subscription expiration handling."""
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
    
    # Create subscription with past end date
    subscription_data = SubscriptionCreate(
        user_id=user.id,
        plan_id=plan.id,
        start_date=datetime.utcnow() - timedelta(days=60),
        end_date=datetime.utcnow() - timedelta(days=30),
        status="active",
        auto_renew=True
    )
    subscription = payment_service.create_subscription(subscription_data)
    
    # Update subscription status to expired
    subscription_update = SubscriptionUpdate(status="expired")
    updated_subscription = payment_service.update_subscription(subscription.id, subscription_update)
    
    # Verify expiration
    assert updated_subscription.status == "expired"
    assert updated_subscription.end_date < datetime.utcnow()
    
    # Verify user's subscriptions
    user_subscriptions = payment_service.get_user_subscriptions(user.id)
    assert any(s.status == "expired" for s in user_subscriptions) 