"""
Test cases for integration API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from ....core.api.v1.endpoints.integration import router
from ....core.main import app
from ....models.user import User

client = TestClient(app)

@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="test_user",
        email="test@example.com",
        is_active=True,
        is_superuser=False
    )

@pytest.fixture
def mock_integration_manager():
    with patch("core.api.v1.endpoints.integration.IntegrationManager") as mock:
        manager = AsyncMock()
        mock.return_value = manager
        yield manager

def test_get_system_status(mock_user, mock_integration_manager):
    """Test getting system status."""
    mock_status = {
        "timestamp": "2024-01-01T00:00:00",
        "components": {"status": "healthy"},
        "services": {"status": "healthy"},
        "apis": {"status": "healthy"},
        "databases": {"status": "healthy"},
        "security": {"status": "healthy"}
    }
    mock_integration_manager.get_system_status.return_value = mock_status
    
    response = client.get("/api/v1/integration/status")
    assert response.status_code == 200
    assert response.json() == mock_status

def test_check_system_health(mock_user, mock_integration_manager):
    """Test checking system health."""
    mock_integration_manager.check_system_health.return_value = True
    
    response = client.get("/api/v1/integration/health")
    assert response.status_code == 200
    assert response.json() is True

def test_restart_component(mock_user, mock_integration_manager):
    """Test restarting a component."""
    mock_integration_manager.restart_component.return_value = True
    
    response = client.post("/api/v1/integration/components/vpn/restart")
    assert response.status_code == 200
    assert response.json() is True

def test_restart_component_failure(mock_user, mock_integration_manager):
    """Test restarting a component failure."""
    mock_integration_manager.restart_component.return_value = False
    
    response = client.post("/api/v1/integration/components/vpn/restart")
    assert response.status_code == 500
    assert "Failed to restart component" in response.json()["detail"]

def test_backup_database(mock_user, mock_integration_manager):
    """Test backing up a database."""
    mock_integration_manager.backup_database.return_value = True
    
    response = client.post("/api/v1/integration/databases/backup?source_db=main&target_db=backup")
    assert response.status_code == 200
    assert response.json() is True

def test_backup_database_failure(mock_user, mock_integration_manager):
    """Test backing up a database failure."""
    mock_integration_manager.backup_database.return_value = False
    
    response = client.post("/api/v1/integration/databases/backup?source_db=main&target_db=backup")
    assert response.status_code == 500
    assert "Failed to backup database" in response.json()["detail"]

def test_sync_databases(mock_user, mock_integration_manager):
    """Test synchronizing databases."""
    mock_integration_manager.sync_databases.return_value = True
    
    response = client.post("/api/v1/integration/databases/sync?source_db=main&target_db=backup")
    assert response.status_code == 200
    assert response.json() is True

def test_sync_databases_failure(mock_user, mock_integration_manager):
    """Test synchronizing databases failure."""
    mock_integration_manager.sync_databases.return_value = False
    
    response = client.post("/api/v1/integration/databases/sync?source_db=main&target_db=backup")
    assert response.status_code == 500
    assert "Failed to sync databases" in response.json()["detail"]

def test_authenticate_user(mock_user, mock_integration_manager):
    """Test user authentication."""
    mock_result = {"token": "test_token", "user_id": 1}
    mock_integration_manager.authenticate_user.return_value = mock_result
    
    response = client.post("/api/v1/integration/security/authenticate", json={"username": "test", "password": "test"})
    assert response.status_code == 200
    assert response.json() == mock_result

def test_authenticate_user_failure(mock_user, mock_integration_manager):
    """Test user authentication failure."""
    mock_integration_manager.authenticate_user.return_value = None
    
    response = client.post("/api/v1/integration/security/authenticate", json={"username": "test", "password": "test"})
    assert response.status_code == 401
    assert "Authentication failed" in response.json()["detail"]

def test_authorize_access(mock_user, mock_integration_manager):
    """Test authorizing access."""
    mock_integration_manager.authorize_access.return_value = True
    
    response = client.post("/api/v1/integration/security/authorize?user_id=1&resource=admin")
    assert response.status_code == 200
    assert response.json() is True

def test_encrypt_data(mock_user, mock_integration_manager):
    """Test data encryption."""
    mock_integration_manager.encrypt_data.return_value = "encrypted_data"
    
    response = client.post("/api/v1/integration/security/encrypt", json="test_data")
    assert response.status_code == 200
    assert response.json() == "encrypted_data"

def test_encrypt_data_failure(mock_user, mock_integration_manager):
    """Test data encryption failure."""
    mock_integration_manager.encrypt_data.return_value = None
    
    response = client.post("/api/v1/integration/security/encrypt", json="test_data")
    assert response.status_code == 500
    assert "Failed to encrypt data" in response.json()["detail"]

def test_decrypt_data(mock_user, mock_integration_manager):
    """Test data decryption."""
    mock_integration_manager.decrypt_data.return_value = "decrypted_data"
    
    response = client.post("/api/v1/integration/security/decrypt", json="encrypted_data")
    assert response.status_code == 200
    assert response.json() == "decrypted_data"

def test_decrypt_data_failure(mock_user, mock_integration_manager):
    """Test data decryption failure."""
    mock_integration_manager.decrypt_data.return_value = None
    
    response = client.post("/api/v1/integration/security/decrypt", json="encrypted_data")
    assert response.status_code == 500
    assert "Failed to decrypt data" in response.json()["detail"]

def test_log_security_event(mock_user, mock_integration_manager):
    """Test logging security event."""
    mock_integration_manager.log_security_event.return_value = True
    
    response = client.post("/api/v1/integration/security/events", json={"event": "test_event"})
    assert response.status_code == 200
    assert response.json() is True

def test_log_security_event_failure(mock_user, mock_integration_manager):
    """Test logging security event failure."""
    mock_integration_manager.log_security_event.return_value = False
    
    response = client.post("/api/v1/integration/security/events", json={"event": "test_event"})
    assert response.status_code == 500
    assert "Failed to log security event" in response.json()["detail"] 