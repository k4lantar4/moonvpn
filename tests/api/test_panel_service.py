"""
PanelService Tests

This module contains tests for the PanelService class.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.services.panel_service import PanelService
from api.models import Panel, PanelHealthCheck
from core.security import encrypt_text, decrypt_text
from integrations.panels.client import XuiPanelClient


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_panel():
    """Create a mock Panel object for testing."""
    panel = MagicMock(spec=Panel)
    panel.id = 1
    panel.name = "Test Panel"
    panel.url = "https://example.com:54321"
    panel.username = "admin"
    panel.password = encrypt_text("password")  # Encrypted password
    panel.login_path = "/login"
    panel.notes = "Test panel notes"
    panel.is_active = True
    panel.timeout = 10.0
    panel.max_retries = 3
    panel.retry_delay = 1.0
    panel.created_at = datetime.utcnow()
    panel.updated_at = datetime.utcnow()
    panel.last_connected_at = None
    panel.health_checks = []
    
    # Add decrypted_password property
    panel.decrypted_password = "password"
    
    return panel


@pytest.fixture
def mock_panel_client():
    """Create a mock XuiPanelClient for testing."""
    client = MagicMock(spec=XuiPanelClient)
    client.login = AsyncMock(return_value=True)
    client.get_inbounds = AsyncMock(return_value=(True, [{"id": 1, "remark": "Test Inbound"}]))
    client.get_status = AsyncMock(return_value=(True, {"version": "1.0.0"}))
    client.get_online_clients = AsyncMock(return_value=(True, ["client1", "client2"]))
    client.close = AsyncMock()
    return client


@pytest.fixture
def panel_service(mock_db_session):
    """Create a PanelService instance for testing."""
    service = PanelService(db=mock_db_session)
    return service


@pytest.mark.asyncio
async def test_list_panels(panel_service, mock_db_session, mock_panel):
    """Test listing panels."""
    # Setup - mock database response
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_panel]
    mock_db_session.execute.return_value = mock_result
    
    # Execute
    panels = await panel_service.list_panels()
    
    # Assert
    assert len(panels) == 1
    assert panels[0].id == 1
    assert panels[0].name == "Test Panel"
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_panel(panel_service, mock_db_session, mock_panel):
    """Test getting a panel by ID."""
    # Setup - mock database response
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_panel
    mock_db_session.execute.return_value = mock_result
    
    # Execute
    panel = await panel_service.get_panel(1)
    
    # Assert
    assert panel.id == 1
    assert panel.name == "Test Panel"
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_panel(panel_service, mock_db_session, mock_panel):
    """Test creating a panel."""
    # Setup - mock test_panel_connection
    with patch("api.services.panel_service.test_panel_connection", 
               new=AsyncMock(return_value={"success": True, "status": "healthy", "response_time_ms": 100})):
        
        # Mock database behavior
        mock_db_session.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", 1))
        
        # Execute
        panel_data = {
            "name": "Test Panel",
            "url": "https://example.com:54321",
            "username": "admin",
            "password": "password",
            "login_path": "/login",
            "notes": "Test panel notes",
            "is_active": True
        }
        result = await panel_service.create_panel(panel_data)
        
        # Assert
        assert result.name == "Test Panel"
        assert result.url == "https://example.com:54321"
        mock_db_session.add.assert_called()
        assert mock_db_session.commit.call_count == 2  # Once for panel, once for health check


@pytest.mark.asyncio
async def test_update_panel(panel_service, mock_db_session, mock_panel):
    """Test updating a panel."""
    # Setup - mock get_panel
    panel_service.get_panel = AsyncMock(return_value=mock_panel)
    
    # Mock test_panel_connection
    with patch("api.services.panel_service.test_panel_connection", 
               new=AsyncMock(return_value={"success": True, "status": "healthy", "response_time_ms": 100})):
        
        # Execute
        panel_data = {"name": "Updated Panel", "notes": "Updated notes"}
        result = await panel_service.update_panel(1, panel_data)
        
        # Assert
        assert result.name == "Updated Panel"
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_panel(panel_service, mock_db_session, mock_panel):
    """Test deleting a panel."""
    # Setup - mock get_panel
    panel_service.get_panel = AsyncMock(return_value=mock_panel)
    
    # Execute
    result = await panel_service.delete_panel(1)
    
    # Assert
    assert result is True
    mock_db_session.delete.assert_called_once_with(mock_panel)
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_panel_health(panel_service, mock_db_session, mock_panel, mock_panel_client):
    """Test checking panel health."""
    # Setup - mock get_panel and client
    panel_service.get_panel = AsyncMock(return_value=mock_panel)
    panel_service.get_client = AsyncMock(return_value=(mock_panel_client, mock_panel))
    
    # Execute
    result = await panel_service.check_panel_health(1)
    
    # Assert
    assert result["status"] == "healthy"
    assert "inbounds_count" in result
    assert "version" in result
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_client(panel_service, mock_db_session, mock_panel, mock_panel_client):
    """Test getting a panel client."""
    # Setup - mock database and XuiPanelClient
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_panel
    mock_db_session.execute.return_value = mock_result
    
    with patch("api.services.panel_service.XuiPanelClient", return_value=mock_panel_client):
        # Execute
        client, panel = await panel_service.get_client(1)
        
        # Assert
        assert panel.id == 1
        assert panel.name == "Test Panel"
        assert client.login.called
        mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_panel_inbounds(panel_service, mock_panel, mock_panel_client):
    """Test getting panel inbounds."""
    # Setup - mock get_client
    panel_service.get_client = AsyncMock(return_value=(mock_panel_client, mock_panel))
    
    # Execute
    inbounds = await panel_service.get_panel_inbounds(1)
    
    # Assert
    assert len(inbounds) == 1
    assert inbounds[0]["id"] == 1
    assert inbounds[0]["remark"] == "Test Inbound"
    assert mock_panel_client.get_inbounds.called 