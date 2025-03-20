"""
Unit tests for the subscription service.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Subscription, SubscriptionPlan
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import SubscriptionCreate, SubscriptionPlanCreate

pytestmark = pytest.mark.asyncio

class TestSubscriptionService:
    """Test cases for SubscriptionService."""

    async def test_create_subscription_plan(self, db_session: AsyncSession):
        """Test creating a new subscription plan."""
        # Arrange
        plan_data = SubscriptionPlanCreate(
            name="Premium",
            description="Premium VPN plan",
            price=9.99,
            duration_days=30,
            features=["Unlimited bandwidth", "All locations", "Priority support"],
            is_active=True
        )
        subscription_service = SubscriptionService(db_session)

        # Act
        plan = await subscription_service.create_plan(plan_data)

        # Assert
        assert plan.name == plan_data.name
        assert plan.description == plan_data.description
        assert plan.price == plan_data.price
        assert plan.duration_days == plan_data.duration_days
        assert plan.features == plan_data.features
        assert plan.is_active == plan_data.is_active

    async def test_create_subscription(self, db_session: AsyncSession, test_user, test_subscription_plan):
        """Test creating a new subscription."""
        # Arrange
        subscription_data = SubscriptionCreate(
            user_id=test_user.id,
            plan_id=test_subscription_plan.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            is_active=True
        )
        subscription_service = SubscriptionService(db_session)

        # Act
        subscription = await subscription_service.create_subscription(subscription_data)

        # Assert
        assert subscription.user_id == test_user.id
        assert subscription.plan_id == test_subscription_plan.id
        assert subscription.is_active == subscription_data.is_active
        assert subscription.start_date == subscription_data.start_date
        assert subscription.end_date == subscription_data.end_date

    async def test_get_subscription(self, db_session: AsyncSession, test_subscription):
        """Test retrieving a subscription."""
        # Arrange
        subscription_service = SubscriptionService(db_session)

        # Act
        subscription = await subscription_service.get_subscription(test_subscription.id)

        # Assert
        assert subscription is not None
        assert subscription.id == test_subscription.id
        assert subscription.user_id == test_subscription.user_id
        assert subscription.plan_id == test_subscription.plan_id

    async def test_get_user_subscriptions(self, db_session: AsyncSession, test_user, test_subscription):
        """Test retrieving all subscriptions for a user."""
        # Arrange
        subscription_service = SubscriptionService(db_session)

        # Act
        subscriptions = await subscription_service.get_user_subscriptions(test_user.id)

        # Assert
        assert len(subscriptions) > 0
        assert any(sub.id == test_subscription.id for sub in subscriptions)

    async def test_update_subscription_status(self, db_session: AsyncSession, test_subscription):
        """Test updating subscription status."""
        # Arrange
        subscription_service = SubscriptionService(db_session)

        # Act
        await subscription_service.update_subscription_status(test_subscription.id, False)

        # Assert
        updated_subscription = await subscription_service.get_subscription(test_subscription.id)
        assert updated_subscription.is_active is False

    async def test_delete_subscription(self, db_session: AsyncSession, test_subscription):
        """Test deleting a subscription."""
        # Arrange
        subscription_service = SubscriptionService(db_session)

        # Act
        await subscription_service.delete_subscription(test_subscription.id)

        # Assert
        deleted_subscription = await subscription_service.get_subscription(test_subscription.id)
        assert deleted_subscription is None

    async def test_get_active_plans(self, db_session: AsyncSession, test_subscription_plan):
        """Test retrieving active subscription plans."""
        # Arrange
        subscription_service = SubscriptionService(db_session)

        # Act
        plans = await subscription_service.get_active_plans()

        # Assert
        assert len(plans) > 0
        assert any(plan.id == test_subscription_plan.id for plan in plans)

    async def test_check_subscription_validity(self, db_session: AsyncSession, test_subscription):
        """Test checking subscription validity."""
        # Arrange
        subscription_service = SubscriptionService(db_session)

        # Act
        is_valid = await subscription_service.check_subscription_validity(test_subscription.id)

        # Assert
        assert is_valid is True

    async def test_renew_subscription(self, db_session: AsyncSession, test_subscription):
        """Test renewing a subscription."""
        # Arrange
        subscription_service = SubscriptionService(db_session)
        new_end_date = datetime.utcnow() + timedelta(days=30)

        # Act
        renewed_subscription = await subscription_service.renew_subscription(
            test_subscription.id,
            new_end_date
        )

        # Assert
        assert renewed_subscription.end_date == new_end_date
        assert renewed_subscription.is_active is True 