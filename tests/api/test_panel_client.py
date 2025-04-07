"""
XuiPanelClient Tests

This module contains tests for the XuiPanelClient class.
"""

import pytest
import httpx
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from integrations.panels.client import XuiPanelClient


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client for testing."""
    mock_client = MagicMock()
    mock_client.post = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.put = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.close = AsyncMock()
    
    # Mock successful login response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_response.cookies = MagicMock()
    mock_response.cookies.jar = [MagicMock(name="session", value="test_session")]
    mock_client.post.return_value = mock_response
    
    return mock_client


@pytest.fixture
async def panel_client(mock_httpx_client):
    """Create a panel client for testing."""
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        client = XuiPanelClient(
            base_url="https://example.com:54321",
            username="admin",
            password="password",
            login_path="/login"
        )
        yield client
        await client.close()


@pytest.mark.asyncio
async def test_login_success(panel_client, mock_httpx_client):
    """Test successful login."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_response.cookies = MagicMock()
    mock_response.cookies.jar = [MagicMock(name="session", value="test_session")]
    
    mock_httpx_client.post.return_value = mock_response
    
    # Execute
    result = await panel_client.login()
    
    # Assert
    assert result is True
    mock_httpx_client.post.assert_called_once_with(
        "https://example.com:54321/login",
        json={"username": "admin", "password": "password"}
    )


@pytest.mark.asyncio
async def test_login_failure(panel_client, mock_httpx_client):
    """Test failed login."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": False}
    mock_response.cookies = MagicMock()
    mock_response.cookies.jar = []
    
    mock_httpx_client.post.return_value = mock_response
    
    # Execute
    result = await panel_client.login()
    
    # Assert
    assert result is False
    mock_httpx_client.post.assert_called_once_with(
        "https://example.com:54321/login",
        json={"username": "admin", "password": "password"}
    )


@pytest.mark.asyncio
async def test_get_inbounds_success(panel_client, mock_httpx_client):
    """Test getting inbounds successfully."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "obj": [
            {"id": 1, "remark": "Test Inbound"},
            {"id": 2, "remark": "Another Inbound"}
        ]
    }
    
    mock_httpx_client.get.return_value = mock_response
    
    # Execute
    success, inbounds = await panel_client.get_inbounds()
    
    # Assert
    assert success is True
    assert len(inbounds) == 2
    assert inbounds[0]["id"] == 1
    assert inbounds[1]["remark"] == "Another Inbound"
    
    mock_httpx_client.get.assert_called_once_with(
        "https://example.com:54321/panel/api/inbounds/list",
        headers={"Cookie": None},
        params=None
    )


@pytest.mark.asyncio
async def test_add_client_success(panel_client, mock_httpx_client):
    """Test adding a client successfully."""
    # Setup
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "obj": {
            "id": "test-uuid",
            "email": "test@example.com",
            "enable": True
        }
    }
    
    mock_httpx_client.post.return_value = mock_response
    
    client_config = {
        "email": "test@example.com",
        "inboundId": 1,
        "enable": True,
        "total_gb": 10
    }
    
    # Execute
    success, client = await panel_client.add_client(client_config)
    
    # Assert
    assert success is True
    assert client["id"] == "test-uuid"
    assert client["email"] == "test@example.com"
    

@pytest.mark.asyncio
async def test_request_error_handling(panel_client, mock_httpx_client):
    """Test error handling in _request method."""
    # Setup - simulate a connection error
    mock_httpx_client.get.side_effect = httpx.ConnectError("Connection refused")
    
    # Execute
    success, result = await panel_client._request("GET", "/panel/api/inbounds/list")
    
    # Assert
    assert success is False
    assert "error" in result
    assert "Connection refused" in result["error"]


@pytest.mark.asyncio
async def test_retry_on_auth_failure(panel_client, mock_httpx_client):
    """Test retry behavior on authentication failure."""
    # Setup - First request fails with 401, second succeeds
    failed_response = MagicMock()
    failed_response.status_code = 401
    
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {"success": True, "obj": {"data": "test"}}
    
    mock_httpx_client.get.side_effect = [failed_response, success_response]
    
    # Mock login to return True
    panel_client.login = AsyncMock(return_value=True)
    
    # Execute
    success, result = await panel_client._request("GET", "/panel/api/inbounds/list")
    
    # Assert
    assert panel_client.login.called
    assert success is True
    assert result == {"data": "test"} 