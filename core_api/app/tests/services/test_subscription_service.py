import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.user import User
from app.models.plan import Plan
from app.models.client import Client
from app.services.subscription_service import (
    SubscriptionService,
    SubscriptionNotFoundError,
    SubscriptionException
)

# Test data
def create_test_user():
    return User(
        id=1,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True
    )

def create_test_plan():
    return Plan(
        id=1,
        name="Basic Plan",
        description="Basic VPN plan",
        price=9.99,
        duration_days=30,
        traffic_limit_gb=100,
        is_active=True
    )

def create_test_subscription():
    now = datetime.utcnow()
    return Subscription(
        id=1,
        user_id=1,
        plan_id=1,
        status="active",
        is_frozen=False,
        auto_renew=False,
        start_date=now,
        end_date=now + timedelta(days=30)
    )

def create_frozen_subscription():
    now = datetime.utcnow()
    return Subscription(
        id=2,
        user_id=1,
        plan_id=1,
        status="active",
        is_frozen=True,
        freeze_start_date=now,
        freeze_end_date=now + timedelta(days=7),
        freeze_reason="User requested",
        auto_renew=False,
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=20)
    )

def create_test_client():
    return Client(
        id=1,
        email="test@example.com",
        subscription_id=1
    )

class TestSubscriptionService:
    """Tests for the SubscriptionService class."""
    
    def test_get_subscription(self, mocker):
        """Test getting a subscription by ID."""
        # Mock DB session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        
        # Case 1: Subscription exists
        test_subscription = create_test_subscription()
        mock_filter.first.return_value = test_subscription
        
        result = SubscriptionService.get_subscription(mock_db, 1)
        
        mock_db.query.assert_called_once_with(Subscription)
        mock_query.filter.assert_called_once()
        assert result == test_subscription
        
        # Reset mocks
        mock_db.reset_mock()
        mock_query.reset_mock()
        mock_filter.reset_mock()
        
        # Case 2: Subscription doesn't exist
        mock_filter.first.return_value = None
        
        with pytest.raises(SubscriptionNotFoundError):
            SubscriptionService.get_subscription(mock_db, 999)
    
    def test_get_user_subscriptions(self, mocker):
        """Test getting all subscriptions for a user."""
        # Mock DB session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        
        # Set up test data
        test_subscriptions = [create_test_subscription(), create_frozen_subscription()]
        mock_filter.all.return_value = test_subscriptions
        
        # Call the method
        result = SubscriptionService.get_user_subscriptions(mock_db, 1)
        
        # Verify the method was called with the correct arguments
        mock_db.query.assert_called_once_with(Subscription)
        mock_query.filter.assert_called_once()
        assert result == test_subscriptions
    
    def test_create_subscription(self, mocker):
        """Test creating a new subscription."""
        # Mock DB session
        mock_db = MagicMock()
        mock_user_query = MagicMock()
        mock_plan_query = MagicMock()
        
        # Mock query results for User and Plan
        mock_db.query.side_effect = lambda model: mock_user_query if model == User else mock_plan_query
        
        mock_user_filter = MagicMock()
        mock_user_query.filter.return_value = mock_user_filter
        mock_user_filter.first.return_value = create_test_user()
        
        mock_plan_filter = MagicMock()
        mock_plan_query.filter.return_value = mock_plan_filter
        mock_plan_filter.first.return_value = create_test_plan()
        
        # Call the method
        subscription = SubscriptionService.create_subscription(
            db=mock_db,
            user_id=1,
            plan_id=1
        )
        
        # Verify method was called with correct args and subscription was created
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
        assert subscription.user_id == 1
        assert subscription.plan_id == 1
        assert subscription.status == "active"
        assert subscription.is_frozen == False
        assert subscription.auto_renew == False
        
        # Test user not found
        mock_user_filter.first.return_value = None
        
        with pytest.raises(SubscriptionException):
            SubscriptionService.create_subscription(
                db=mock_db,
                user_id=999,
                plan_id=1
            )
        
        # Test plan not found
        mock_user_filter.first.return_value = create_test_user()
        mock_plan_filter.first.return_value = None
        
        with pytest.raises(SubscriptionException):
            SubscriptionService.create_subscription(
                db=mock_db,
                user_id=1,
                plan_id=999
            )
    
    @patch('app.services.subscription_service.PanelService')
    def test_freeze_subscription(self, mock_panel_service, mocker):
        """Test freezing a subscription."""
        # Mock DB session and get_subscription method
        mock_db = MagicMock()
        mock_subscription = create_test_subscription()
        
        mocker.patch.object(
            SubscriptionService, 
            'get_subscription',
            return_value=mock_subscription
        )
        
        # Mock the freeze method on the subscription object
        mock_subscription.freeze = MagicMock()
        
        # Mock Client query
        mock_client_query = MagicMock()
        mock_db.query.return_value = mock_client_query
        mock_client_filter = MagicMock()
        mock_client_query.filter.return_value = mock_client_filter
        mock_client_filter.first.return_value = create_test_client()
        
        # Mock PanelService context manager
        mock_panel_service_instance = MagicMock()
        mock_panel_service.return_value.__enter__.return_value = mock_panel_service_instance
        
        # Call the method
        freeze_end_date = datetime.utcnow() + timedelta(days=7)
        result = SubscriptionService.freeze_subscription(
            db=mock_db,
            subscription_id=1,
            freeze_end_date=freeze_end_date,
            freeze_reason="Test reason"
        )
        
        # Verify method was called with correct args
        SubscriptionService.get_subscription.assert_called_once_with(mock_db, 1)
        mock_subscription.freeze.assert_called_once_with(end_date=freeze_end_date, reason="Test reason")
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_subscription)
        mock_panel_service_instance.disable_client.assert_called_once_with(email="test@example.com")
        
        # Test subscription already frozen
        mocker.patch.object(
            SubscriptionService, 
            'get_subscription',
            return_value=create_frozen_subscription()
        )
        
        with pytest.raises(SubscriptionException):
            SubscriptionService.freeze_subscription(
                db=mock_db,
                subscription_id=2
            )
    
    @patch('app.services.subscription_service.PanelService')
    def test_unfreeze_subscription(self, mock_panel_service, mocker):
        """Test unfreezing a subscription."""
        # Mock DB session and get_subscription method
        mock_db = MagicMock()
        mock_subscription = create_frozen_subscription()
        
        mocker.patch.object(
            SubscriptionService, 
            'get_subscription',
            return_value=mock_subscription
        )
        
        # Mock the unfreeze method on the subscription object
        mock_subscription.unfreeze = MagicMock()
        
        # Mock Client query
        mock_client_query = MagicMock()
        mock_db.query.return_value = mock_client_query
        mock_client_filter = MagicMock()
        mock_client_query.filter.return_value = mock_client_filter
        mock_client_filter.first.return_value = create_test_client()
        
        # Mock PanelService context manager
        mock_panel_service_instance = MagicMock()
        mock_panel_service.return_value.__enter__.return_value = mock_panel_service_instance
        
        # Call the method
        result = SubscriptionService.unfreeze_subscription(
            db=mock_db,
            subscription_id=2
        )
        
        # Verify method was called with correct args
        SubscriptionService.get_subscription.assert_called_once_with(mock_db, 2)
        mock_subscription.unfreeze.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_subscription)
        mock_panel_service_instance.enable_client.assert_called_once_with(email="test@example.com")
        
        # Test subscription not frozen
        mocker.patch.object(
            SubscriptionService, 
            'get_subscription',
            return_value=create_test_subscription()
        )
        
        with pytest.raises(SubscriptionException):
            SubscriptionService.unfreeze_subscription(
                db=mock_db,
                subscription_id=1
            )
    
    def test_add_note(self, mocker):
        """Test adding a note to a subscription."""
        # Mock DB session and get_subscription method
        mock_db = MagicMock()
        mock_subscription = create_test_subscription()
        
        mocker.patch.object(
            SubscriptionService, 
            'get_subscription',
            return_value=mock_subscription
        )
        
        # Mock the add_note method on the subscription object
        mock_subscription.add_note = MagicMock()
        
        # Call the method
        result = SubscriptionService.add_note(
            db=mock_db,
            subscription_id=1,
            note="Test note"
        )
        
        # Verify method was called with correct args
        SubscriptionService.get_subscription.assert_called_once_with(mock_db, 1)
        mock_subscription.add_note.assert_called_once_with("Test note")
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_subscription)
    
    def test_toggle_auto_renew(self, mocker):
        """Test toggling auto-renew for a subscription."""
        # Mock DB session and get_subscription method
        mock_db = MagicMock()
        mock_subscription = create_test_subscription()
        
        mocker.patch.object(
            SubscriptionService, 
            'get_subscription',
            return_value=mock_subscription
        )
        
        # Mock the toggle_auto_renew method on the subscription object
        mock_subscription.toggle_auto_renew = MagicMock()
        
        # Call the method
        result = SubscriptionService.toggle_auto_renew(
            db=mock_db,
            subscription_id=1,
            enabled=True,
            payment_method="credit_card"
        )
        
        # Verify method was called with correct args
        SubscriptionService.get_subscription.assert_called_once_with(mock_db, 1)
        mock_subscription.toggle_auto_renew.assert_called_once_with(True, "credit_card")
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_subscription)
    
    @patch('app.services.subscription_service.PanelService')
    def test_check_expired_subscriptions(self, mock_panel_service, mocker):
        """Test checking for expired subscriptions."""
        # Mock DB session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        
        # Set up test data - one with auto-renew True, one with False
        sub1 = create_test_subscription()
        sub1.auto_renew = True
        
        sub2 = create_test_subscription()
        sub2.auto_renew = False
        sub2.id = 2
        
        mock_filter.all.return_value = [sub1, sub2]
        
        # Mock Client query
        mock_client_query = MagicMock()
        mock_db.query.side_effect = lambda model: mock_client_query if model == Client else mock_query
        mock_client_filter = MagicMock()
        mock_client_query.filter.return_value = mock_client_filter
        mock_client_filter.first.return_value = create_test_client()
        
        # Mock PanelService context manager
        mock_panel_service_instance = MagicMock()
        mock_panel_service.return_value.__enter__.return_value = mock_panel_service_instance
        
        # Call the method
        result = SubscriptionService.check_expired_subscriptions(mock_db)
        
        # Verify correct queries were made
        mock_query.filter.assert_called_once()
        assert result == [sub1, sub2]
        
        # Only sub2 should be marked as expired and have client disabled
        assert sub2.status == "expired"
        mock_panel_service_instance.disable_client.assert_called_once_with(email="test@example.com")
        
        # sub1 should still be active (auto-renew enabled, would trigger renewal)
        assert sub1.status == "active" 