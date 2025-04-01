import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.deps import get_db, get_current_active_user, get_current_active_superuser
from app.models.user import User
from app.models.role import Role
from app.models.subscription import Subscription
from app.services.subscription_service import SubscriptionService, SubscriptionNotFoundError, SubscriptionException

# Test data
def create_test_user(role_name="user"):
    role = Role(id=1, name=role_name)
    user = User(
        id=1,
        email="test@example.com", 
        first_name="Test",
        last_name="User",
        hashed_password="hashed_password",
        is_active=True,
        is_verified=True,
        role=role
    )
    return user

def create_test_admin():
    return create_test_user(role_name="admin")

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
        end_date=now + timedelta(days=30),
        notes="Initial notes"
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

# Mock dependencies
def override_get_db():
    return MagicMock()

def override_get_current_active_user():
    return create_test_user()

def override_get_current_active_superuser():
    return create_test_admin()

# Apply mocks
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user
app.dependency_overrides[get_current_active_superuser] = override_get_current_active_superuser

# Create test client
client = TestClient(app)

class TestSubscriptionApi:
    """Tests for the subscription API endpoints."""
    
    @patch.object(SubscriptionService, "get_user_subscriptions")
    def test_get_subscriptions(self, mock_get_user_subscriptions):
        """Test GET /api/v1/subscriptions/"""
        # Setup mock
        mock_subscriptions = [create_test_subscription(), create_frozen_subscription()]
        mock_get_user_subscriptions.return_value = mock_subscriptions
        
        # Make request
        response = client.get("/api/v1/subscriptions/")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["id"] == 2
        
        # Verify service was called
        mock_get_user_subscriptions.assert_called_once()
    
    @patch.object(SubscriptionService, "get_subscription")
    def test_get_subscription(self, mock_get_subscription):
        """Test GET /api/v1/subscriptions/{subscription_id}"""
        # Setup mock for existing subscription
        mock_subscription = create_test_subscription()
        mock_get_subscription.return_value = mock_subscription
        
        # Make request
        response = client.get("/api/v1/subscriptions/1")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["user_id"] == 1
        assert data["plan_id"] == 1
        assert data["status"] == "active"
        assert data["is_frozen"] == False
        
        # Verify service was called with correct args
        mock_get_subscription.assert_called_once_with(MagicMock(), 1)
        
        # Test subscription not found
        mock_get_subscription.side_effect = SubscriptionNotFoundError("Not found")
        
        # Make request
        response = client.get("/api/v1/subscriptions/999")
        
        # Check response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch.object(SubscriptionService, "create_subscription")
    def test_create_subscription(self, mock_create_subscription):
        """Test POST /api/v1/subscriptions/"""
        # Setup mock
        mock_subscription = create_test_subscription()
        mock_create_subscription.return_value = mock_subscription
        
        # Prepare request data
        subscription_data = {
            "user_id": 1,
            "plan_id": 1,
            "auto_renew": False
        }
        
        # Make request
        response = client.post("/api/v1/subscriptions/", json=subscription_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["user_id"] == 1
        assert data["plan_id"] == 1
        
        # Verify service was called with correct args
        mock_create_subscription.assert_called_once()
        
        # Test error case
        mock_create_subscription.side_effect = SubscriptionException("Invalid data")
        
        # Make request
        response = client.post("/api/v1/subscriptions/", json=subscription_data)
        
        # Check response
        assert response.status_code == 400
        assert "invalid data" in response.json()["detail"].lower()
    
    @patch.object(SubscriptionService, "freeze_subscription")
    @patch.object(SubscriptionService, "get_subscription")
    def test_freeze_subscription(self, mock_get_subscription, mock_freeze_subscription):
        """Test POST /api/v1/subscriptions/{subscription_id}/freeze"""
        # Setup mocks
        mock_subscription = create_test_subscription()
        mock_get_subscription.return_value = mock_subscription
        mock_freeze_subscription.return_value = create_frozen_subscription()
        
        # Prepare request data
        freeze_data = {
            "freeze_reason": "Going on vacation",
            "freeze_end_date": (datetime.utcnow() + timedelta(days=14)).isoformat()
        }
        
        # Make request
        response = client.post("/api/v1/subscriptions/1/freeze", json=freeze_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["is_frozen"] == True
        assert data["freeze_reason"] == "User requested"  # From the mock data
        
        # Verify service was called with correct args
        mock_get_subscription.assert_called_once_with(MagicMock(), 1)
        mock_freeze_subscription.assert_called_once()
        
        # Test subscription not found
        mock_get_subscription.side_effect = SubscriptionNotFoundError("Not found")
        
        # Make request
        response = client.post("/api/v1/subscriptions/999/freeze", json=freeze_data)
        
        # Check response
        assert response.status_code == 404
    
    @patch.object(SubscriptionService, "unfreeze_subscription")
    @patch.object(SubscriptionService, "get_subscription")
    def test_unfreeze_subscription(self, mock_get_subscription, mock_unfreeze_subscription):
        """Test POST /api/v1/subscriptions/{subscription_id}/unfreeze"""
        # Setup mocks
        mock_subscription = create_frozen_subscription()
        mock_get_subscription.return_value = mock_subscription
        mock_unfreeze_subscription.return_value = create_test_subscription()
        
        # Prepare request data (empty but required by FastAPI)
        unfreeze_data = {}
        
        # Make request
        response = client.post("/api/v1/subscriptions/2/unfreeze", json=unfreeze_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["is_frozen"] == False
        
        # Verify service was called with correct args
        mock_get_subscription.assert_called_once_with(MagicMock(), 2)
        mock_unfreeze_subscription.assert_called_once()
        
        # Test error case
        mock_get_subscription.side_effect = None
        mock_unfreeze_subscription.side_effect = SubscriptionException("Cannot unfreeze")
        
        # Make request
        response = client.post("/api/v1/subscriptions/2/unfreeze", json=unfreeze_data)
        
        # Check response
        assert response.status_code == 400
        assert "cannot unfreeze" in response.json()["detail"].lower()
    
    @patch.object(SubscriptionService, "add_note")
    @patch.object(SubscriptionService, "get_subscription")
    def test_add_note(self, mock_get_subscription, mock_add_note):
        """Test POST /api/v1/subscriptions/{subscription_id}/notes"""
        # Setup mocks
        mock_subscription = create_test_subscription()
        mock_get_subscription.return_value = mock_subscription
        
        # Updated subscription with new note
        updated_subscription = create_test_subscription()
        updated_subscription.notes = "Initial notes\nAdded a new note"
        mock_add_note.return_value = updated_subscription
        
        # Prepare request data
        note_data = {
            "note": "Added a new note"
        }
        
        # Make request
        response = client.post("/api/v1/subscriptions/1/notes", json=note_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "Added a new note" in data["notes"]
        
        # Verify service was called with correct args
        mock_get_subscription.assert_called_once_with(MagicMock(), 1)
        mock_add_note.assert_called_once_with(MagicMock(), 1, "Added a new note")
    
    @patch.object(SubscriptionService, "toggle_auto_renew")
    @patch.object(SubscriptionService, "get_subscription")
    def test_toggle_auto_renew(self, mock_get_subscription, mock_toggle_auto_renew):
        """Test POST /api/v1/subscriptions/{subscription_id}/auto-renew"""
        # Setup mocks
        mock_subscription = create_test_subscription()
        mock_get_subscription.return_value = mock_subscription
        
        # Updated subscription with auto-renew enabled
        updated_subscription = create_test_subscription()
        updated_subscription.auto_renew = True
        updated_subscription.auto_renew_payment_method = "credit_card"
        mock_toggle_auto_renew.return_value = updated_subscription
        
        # Prepare request data
        auto_renew_data = {
            "enabled": True,
            "payment_method": "credit_card"
        }
        
        # Make request
        response = client.post("/api/v1/subscriptions/1/auto-renew", json=auto_renew_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["auto_renew"] == True
        assert data["auto_renew_payment_method"] == "credit_card"
        
        # Verify service was called with correct args
        mock_get_subscription.assert_called_once_with(MagicMock(), 1)
        mock_toggle_auto_renew.assert_called_once_with(
            MagicMock(), 1, True, "credit_card"
        ) 