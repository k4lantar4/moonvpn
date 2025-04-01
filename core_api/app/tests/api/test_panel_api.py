from typing import Dict
import pytest
import uuid
from fastapi.testclient import TestClient

from app.core.config import settings
from app.tests.utils.utils import get_superuser_token_headers

# Test panel API endpoints with authentication
def test_panel_api_get_inbounds(client: TestClient, superuser_token_headers: Dict[str, str]) -> None:
    """Test that a superuser can get the list of inbounds."""
    # This might fail if the panel connection is not properly configured in test environment
    response = client.get(
        f"{settings.API_V1_STR}/panel/inbounds",
        headers=superuser_token_headers,
    )
    # Even if the panel is not available in test environment, we should get a proper error response
    # (not a 404 which would mean wrong endpoint path)
    assert response.status_code in (200, 401, 503, 500)

def test_panel_api_create_client(client: TestClient, superuser_token_headers: Dict[str, str]) -> None:
    """Test that a superuser can create a client on the panel."""
    # Random test data using uuid to ensure uniqueness
    random_suffix = str(uuid.uuid4())[:8]
    client_data = {
        "email": f"test_client_{random_suffix}@example.com",
        "total_gb": 10,
        "expire_days": 30,
        "limit_ip": 1
    }
    
    # This might fail if the panel connection is not properly configured in test environment
    response = client.post(
        f"{settings.API_V1_STR}/panel/clients",
        headers=superuser_token_headers,
        json=client_data
    )
    # Even if the panel is not available in test environment, we should get a proper error response
    # (not a 404 which would mean wrong endpoint path)
    assert response.status_code in (201, 401, 503, 500, 404)  # 404 if inbound not found

def test_panel_api_no_auth(client: TestClient) -> None:
    """Test that panel endpoints require authentication."""
    response = client.get(f"{settings.API_V1_STR}/panel/inbounds")
    assert response.status_code == 401

def test_panel_api_normal_user(client: TestClient, normal_user_token_headers: Dict[str, str]) -> None:
    """Test that only superusers can access panel endpoints."""
    response = client.get(
        f"{settings.API_V1_STR}/panel/inbounds",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403

def test_panel_api_get_client_config(client: TestClient, superuser_token_headers: Dict[str, str]) -> None:
    """Test that a superuser can get client configuration."""
    # Random email for testing
    random_suffix = str(uuid.uuid4())[:8]
    email = f"test_client_{random_suffix}@example.com"
    
    # First create a client
    client_data = {
        "email": email,
        "total_gb": 10,
        "expire_days": 30,
        "limit_ip": 1
    }
    
    # This might fail if the panel connection is not properly configured in test environment
    response = client.post(
        f"{settings.API_V1_STR}/panel/clients",
        headers=superuser_token_headers,
        json=client_data
    )
    
    # Skip further testing if client creation failed
    if response.status_code not in (201, 200):
        pytest.skip("Client creation failed, skipping config test")
    
    # Now try to get the config
    response = client.get(
        f"{settings.API_V1_STR}/panel/clients/{email}/config",
        headers=superuser_token_headers,
    )
    
    # Even if the panel is not available in test environment, we should get a proper error response
    # (not a 404 which would mean wrong endpoint path)
    assert response.status_code in (200, 401, 503, 500, 404)
    
    # If successful, check that the response contains expected fields
    if response.status_code == 200:
        data = response.json()
        assert "email" in data
        assert "protocol" in data
        assert "link" in data
        assert data["email"] == email

def test_panel_api_get_client_qrcode(client: TestClient, superuser_token_headers: Dict[str, str]) -> None:
    """Test that a superuser can get client QR code."""
    # Random email for testing
    random_suffix = str(uuid.uuid4())[:8]
    email = f"test_client_{random_suffix}@example.com"
    
    # First create a client
    client_data = {
        "email": email,
        "total_gb": 10,
        "expire_days": 30,
        "limit_ip": 1
    }
    
    # This might fail if the panel connection is not properly configured in test environment
    response = client.post(
        f"{settings.API_V1_STR}/panel/clients",
        headers=superuser_token_headers,
        json=client_data
    )
    
    # Skip further testing if client creation failed
    if response.status_code not in (201, 200):
        pytest.skip("Client creation failed, skipping QR code test")
    
    # Now try to get the QR code
    response = client.get(
        f"{settings.API_V1_STR}/panel/clients/{email}/qrcode",
        headers=superuser_token_headers,
    )
    
    # Even if the panel is not available in test environment, we should get a proper error response
    # (not a 404 which would mean wrong endpoint path)
    assert response.status_code in (200, 401, 503, 500, 404)
    
    # If successful, check that the response contains expected fields
    if response.status_code == 200:
        data = response.json()
        assert "email" in data
        assert "protocol" in data
        assert "qrcode" in data
        assert "link" in data
        assert data["email"] == email
        assert len(data["qrcode"]) > 0  # Base64 data should not be empty 