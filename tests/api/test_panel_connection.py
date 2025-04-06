"""
Tests for panel connection functionality.

This module tests the 3x-ui panel connection client and API routes.
"""

import pytest
import httpx
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from api.main import app
from integrations.panels.client import XuiPanelClient, test_panel_connection

# Create test client
client = TestClient(app)


# --- Unit Tests for XuiPanelClient ---

@pytest.mark.asyncio
async def test_panel_client_login_success():
    """Test successful login to panel."""
    # Mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_response.cookies = MagicMock()
    mock_response.cookies.jar = [MagicMock(name="session", value="testvalue")]
    
    # Mock httpx client
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    
    # Create client and patch its http client
    xui_client = XuiPanelClient("http://test.com", "user", "pass")
    xui_client.client = mock_client
    
    # Test login
    result = await xui_client.login()
    
    # Assertions
    assert result is True
    mock_client.post.assert_called_once()
    assert xui_client.session_cookie is not None
    assert xui_client.last_login is not None


@pytest.mark.asyncio
async def test_panel_client_login_failure():
    """Test failed login to panel."""
    # Mock response
    mock_response = AsyncMock()
    mock_response.status_code = 401
    
    # Mock httpx client
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    
    # Create client and patch its http client
    xui_client = XuiPanelClient("http://test.com", "user", "wrong_pass")
    xui_client.client = mock_client
    
    # Test login
    result = await xui_client.login()
    
    # Assertions
    assert result is False
    mock_client.post.assert_called_once()
    assert xui_client.session_cookie is None


@pytest.mark.asyncio
async def test_panel_client_get_status_success():
    """Test successful status retrieval."""
    # Mock status response
    mock_status_response = AsyncMock()
    mock_status_response.status_code = 200
    mock_status_response.json.return_value = {
        "success": True,
        "obj": {
            "cpu": 5.2,
            "mem": {
                "total": 8192,
                "used": 3000
            },
            "disk": {
                "total": 50,
                "used": 20
            },
            "xray": "running",
            "uptime": "10:20:30"
        }
    }
    
    # Mock httpx client
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_status_response
    
    # Create client with mocked session
    xui_client = XuiPanelClient("http://test.com", "user", "pass")
    xui_client.client = mock_client
    xui_client.session_cookie = "test_session=value"
    
    # Test get_status
    success, data = await xui_client.get_status()
    
    # Assertions
    assert success is True
    assert "cpu" in data
    assert "mem" in data
    assert "xray" in data
    mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_panel_client_get_status_failure():
    """Test failed status retrieval."""
    # Mock status response
    mock_status_response = AsyncMock()
    mock_status_response.status_code = 500
    
    # Mock httpx client
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_status_response
    
    # Create client with mocked session
    xui_client = XuiPanelClient("http://test.com", "user", "pass")
    xui_client.client = mock_client
    xui_client.session_cookie = "test_session=value"
    
    # Test get_status
    success, data = await xui_client.get_status()
    
    # Assertions
    assert success is False
    assert "error" in data
    mock_client.get.assert_called_once()


# --- Integration Tests for test_panel_connection function ---

@pytest.mark.asyncio
async def test_panel_connection_success():
    """Test successful panel connection test."""
    # Setup mock for XuiPanelClient
    with patch('integrations.panels.client.XuiPanelClient') as MockClient:
        # Mock login and get_status
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.login.return_value = True
        mock_instance.get_status.return_value = (True, {"cpu": 5, "mem": {"total": 8192, "used": 3000}})
        MockClient.return_value = mock_instance
        
        # Test connection
        result = await test_panel_connection("http://test.com", "user", "pass")
        
        # Assertions
        assert result["success"] is True
        assert result["status"] == "healthy"
        assert "panel_info" in result
        assert result["response_time_ms"] is not None
        assert result["url"] == "http://test.com"


@pytest.mark.asyncio
async def test_panel_connection_auth_failure():
    """Test panel connection test with authentication failure."""
    # Setup mock for XuiPanelClient
    with patch('integrations.panels.client.XuiPanelClient') as MockClient:
        # Mock login and get_status
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.login.return_value = False  # Login fails
        MockClient.return_value = mock_instance
        
        # Test connection
        result = await test_panel_connection("http://test.com", "user", "wrong_pass")
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "auth_failed"
        assert "error" in result
        assert result["response_time_ms"] is not None


@pytest.mark.asyncio
async def test_panel_connection_api_error():
    """Test panel connection test with API error."""
    # Setup mock for XuiPanelClient
    with patch('integrations.panels.client.XuiPanelClient') as MockClient:
        # Mock login and get_status
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.login.return_value = True  # Login succeeds
        mock_instance.get_status.return_value = (False, {"error": "API error"})  # Status fails
        MockClient.return_value = mock_instance
        
        # Test connection
        result = await test_panel_connection("http://test.com", "user", "pass")
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "api_error"
        assert result["error"] == "API error"
        assert result["response_time_ms"] is not None


@pytest.mark.asyncio
async def test_panel_connection_connect_error():
    """Test panel connection test with connection error."""
    # Setup mock for XuiPanelClient that raises ConnectError
    with patch('integrations.panels.client.XuiPanelClient') as MockClient:
        # Mock instance that raises error
        mock_instance = AsyncMock()
        mock_instance.__aenter__.side_effect = httpx.ConnectError("Failed to connect")
        MockClient.return_value = mock_instance
        
        # Test connection
        result = await test_panel_connection("http://nonexistent.com", "user", "pass")
        
        # Assertions
        assert result["success"] is False
        assert result["status"] == "connect_error"
        assert "error" in result
        assert result["response_time_ms"] is not None


# --- API Endpoint Tests ---

def test_api_test_panel_endpoint():
    """Test the API endpoint for testing panel connection."""
    # Mock the test_panel_connection function
    with patch('api.routes.panels.test_panel_connection') as mock_test:
        # Setup mock return value
        mock_test.return_value = {
            "success": True,
            "url": "http://test.com",
            "response_time_ms": 250,
            "status": "healthy",
            "error": None,
            "panel_info": {"cpu": 5},
            "timestamp": datetime.now().isoformat()
        }
        
        # Make request to API
        response = client.post(
            "/api/v1/panels/test",
            json={
                "url": "http://test.com",
                "username": "admin",
                "password": "pass123"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["status"] == "healthy"
        assert "panel_info" in result


def test_api_test_default_panel_endpoint():
    """Test the API endpoint for testing the default panel connection."""
    # Mock the test_default_panel_connection function
    with patch('api.routes.panels.test_default_panel_connection') as mock_test:
        # Setup mock return value
        mock_test.return_value = {
            "success": True,
            "url": "http://default-panel.com",
            "response_time_ms": 250,
            "status": "healthy",
            "error": None,
            "panel_info": {"cpu": 5},
            "timestamp": datetime.now().isoformat()
        }
        
        # Make request to API
        response = client.get("/api/v1/panels/test/default")
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["status"] == "healthy"
        assert "panel_info" in result


def test_api_test_default_panel_config_error():
    """Test the API endpoint when default panel config is missing."""
    # Mock the test_default_panel_connection function
    with patch('api.routes.panels.test_default_panel_connection') as mock_test:
        # Setup mock return value for config error
        mock_test.return_value = {
            "success": False,
            "status": "config_error",
            "error": "Panel configuration is incomplete",
            "timestamp": datetime.now().isoformat()
        }
        
        # Make request to API
        response = client.get("/api/v1/panels/test/default")
        
        # Assertions
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "configuration" in result["detail"].lower() 