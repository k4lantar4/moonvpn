"""Performance tests for payment system."""
import pytest
import time
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

def test_payment_creation_performance(db: Session, test_user_data):
    """Test performance of creating multiple payments."""
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
    
    # Test creating 100 payments
    start_time = time.time()
    for i in range(100):
        payment_data = PaymentCreate(
            user_id=user.id,
            amount=plan.price,
            currency="USD",
            status="pending",
            payment_method="credit_card",
            description=f"Test payment {i}"
        )
        payment_service.create_payment(payment_data)
    end_time = time.time()
    
    # Calculate performance metrics
    total_time = end_time - start_time
    avg_time_per_payment = total_time / 100
    
    # Assert performance requirements
    assert total_time < 5.0  # Total time should be less than 5 seconds
    assert avg_time_per_payment < 0.05  # Each payment should take less than 50ms

def test_subscription_creation_performance(db: Session, test_user_data):
    """Test performance of creating multiple subscriptions."""
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
    
    # Test creating 100 subscriptions
    start_time = time.time()
    for i in range(100):
        subscription_data = SubscriptionCreate(
            user_id=user.id,
            plan_id=plan.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
            status="active",
            auto_renew=True
        )
        payment_service.create_subscription(subscription_data)
    end_time = time.time()
    
    # Calculate performance metrics
    total_time = end_time - start_time
    avg_time_per_subscription = total_time / 100
    
    # Assert performance requirements
    assert total_time < 5.0  # Total time should be less than 5 seconds
    assert avg_time_per_subscription < 0.05  # Each subscription should take less than 50ms

def test_payment_query_performance(db: Session, test_user_data):
    """Test performance of querying payments."""
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
    
    # Create 1000 payments
    for i in range(1000):
        payment_data = PaymentCreate(
            user_id=user.id,
            amount=plan.price,
            currency="USD",
            status="completed",
            payment_method="credit_card",
            description=f"Test payment {i}"
        )
        payment_service.create_payment(payment_data)
    
    # Test querying payments
    start_time = time.time()
    payments = payment_service.get_user_payments(user.id)
    end_time = time.time()
    
    # Calculate performance metrics
    query_time = end_time - start_time
    
    # Assert performance requirements
    assert query_time < 1.0  # Query should take less than 1 second
    assert len(payments) == 1000  # Should return all payments

def test_subscription_query_performance(db: Session, test_user_data):
    """Test performance of querying subscriptions."""
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
    
    # Create 1000 subscriptions
    for i in range(1000):
        subscription_data = SubscriptionCreate(
            user_id=user.id,
            plan_id=plan.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
            status="active",
            auto_renew=True
        )
        payment_service.create_subscription(subscription_data)
    
    # Test querying subscriptions
    start_time = time.time()
    subscriptions = payment_service.get_user_subscriptions(user.id)
    end_time = time.time()
    
    # Calculate performance metrics
    query_time = end_time - start_time
    
    # Assert performance requirements
    assert query_time < 1.0  # Query should take less than 1 second
    assert len(subscriptions) == 1000  # Should return all subscriptions

def test_payment_stats_performance(db: Session, test_user_data):
    """Test performance of calculating payment statistics."""
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
    
    # Create 1000 payments with different dates
    for i in range(1000):
        payment_data = PaymentCreate(
            user_id=user.id,
            amount=plan.price,
            currency="USD",
            status="completed",
            payment_method="credit_card",
            description=f"Test payment {i}",
            created_at=datetime.utcnow() - timedelta(days=i % 30)  # Spread across last 30 days
        )
        payment_service.create_payment(payment_data)
    
    # Test calculating statistics
    start_time = time.time()
    stats = payment_service.get_payment_stats()
    end_time = time.time()
    
    # Calculate performance metrics
    calculation_time = end_time - start_time
    
    # Assert performance requirements
    assert calculation_time < 2.0  # Calculation should take less than 2 seconds
    assert stats.total_transactions == 1000
    assert stats.total_amount == 1000 * plan.price

def test_concurrent_payment_creation(db: Session, test_user_data):
    """Test performance of concurrent payment creation."""
    import concurrent.futures
    
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
    
    def create_payment(i):
        payment_data = PaymentCreate(
            user_id=user.id,
            amount=plan.price,
            currency="USD",
            status="pending",
            payment_method="credit_card",
            description=f"Test payment {i}"
        )
        return payment_service.create_payment(payment_data)
    
    # Test creating 100 payments concurrently
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_payment, i) for i in range(100)]
        concurrent.futures.wait(futures)
    end_time = time.time()
    
    # Calculate performance metrics
    total_time = end_time - start_time
    avg_time_per_payment = total_time / 100
    
    # Assert performance requirements
    assert total_time < 10.0  # Total time should be less than 10 seconds
    assert avg_time_per_payment < 0.1  # Each payment should take less than 100ms

def test_concurrent_subscription_creation(db: Session, test_user_data):
    """Test performance of concurrent subscription creation."""
    import concurrent.futures
    
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
    
    def create_subscription(i):
        subscription_data = SubscriptionCreate(
            user_id=user.id,
            plan_id=plan.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=plan.duration_days),
            status="active",
            auto_renew=True
        )
        return payment_service.create_subscription(subscription_data)
    
    # Test creating 100 subscriptions concurrently
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_subscription, i) for i in range(100)]
        concurrent.futures.wait(futures)
    end_time = time.time()
    
    # Calculate performance metrics
    total_time = end_time - start_time
    avg_time_per_subscription = total_time / 100
    
    # Assert performance requirements
    assert total_time < 10.0  # Total time should be less than 10 seconds
    assert avg_time_per_subscription < 0.1  # Each subscription should take less than 100ms 