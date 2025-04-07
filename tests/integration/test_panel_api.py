"""
Panel API Integration Tests

This module contains integration tests for the panel API endpoints.
"""

import pytest
import uuid
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
import json

from api.main import app
from api.routes.panels import router as panel_router
from core.database import Base, engine, get_db
from api.models import Panel, PanelHealthCheck
from api.services.panel_service import PanelService
from core.config import get_settings


@pytest.fixture
async def test_db():
    """Create test database for integration tests."""
    # Create tables in test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield

    # Drop tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Get database session for tests."""
    async for session in get_db():
        yield session


@pytest.fixture
async def client():
    """Get test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def panel_service(db_session):
    """Get panel service for tests."""
    return PanelService(db=db_session)


@pytest.fixture
async def test_panel(db_session):
    """Create a test panel for integration tests."""
    panel = Panel(
        name=f"Test Panel {uuid.uuid4()}",
        url="https://example.com:54321",
        username="admin",
        password="password",  # will be automatically encrypted
        login_path="/login",
        notes="Integration test panel",
        is_active=True
    )
    
    db_session.add(panel)
    await db_session.commit()
    await db_session.refresh(panel)
    
    # Add a health check
    health_check = PanelHealthCheck(
        panel_id=panel.id,
        status="healthy",
        response_time_ms=100,
        details='{"success": true}',
        checked_at=None  # will use default
    )
    
    db_session.add(health_check)
    await db_session.commit()
    
    return panel


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_panels(client, test_panel):
    """Test listing panels."""
    response = await client.get("/api/v1/panels/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check if our test panel is in the list
    panel_ids = [panel["id"] for panel in data]
    assert test_panel.id in panel_ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_panel(client, test_panel):
    """Test getting a panel by ID."""
    response = await client.get(f"/api/v1/panels/{test_panel.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_panel.id
    assert data["name"] == test_panel.name
    assert "password" not in data  # Password should be excluded
    assert "health_checks" in data
    assert len(data["health_checks"]) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_and_delete_panel(client):
    """Test creating and deleting a panel."""
    # Mock the test_panel_connection function
    with patch("api.services.panel_service.test_panel_connection", 
               new=AsyncMock(return_value={"success": True, "status": "healthy", "response_time_ms": 100})):
        
        # Create a panel
        panel_data = {
            "name": f"New Test Panel {uuid.uuid4()}",
            "url": "https://example.com:54321",
            "username": "admin",
            "password": "password",
            "login_path": "/login",
            "notes": "Test panel for API test",
            "is_active": True
        }
        
        response = await client.post("/api/v1/panels/", json=panel_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == panel_data["name"]
        assert "password" not in data  # Password should be excluded
        
        # Delete the panel
        panel_id = data["id"]
        response = await client.delete(f"/api/v1/panels/{panel_id}")
        
        assert response.status_code == 204


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_panel(client, test_panel):
    """Test updating a panel."""
    # Mock the test_panel_connection function
    with patch("api.services.panel_service.test_panel_connection", 
               new=AsyncMock(return_value={"success": True, "status": "healthy", "response_time_ms": 100})):
        
        # Update the panel
        update_data = {
            "name": f"Updated Test Panel {uuid.uuid4()}",
            "notes": "Updated test panel notes"
        }
        
        response = await client.put(f"/api/v1/panels/{test_panel.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["notes"] == update_data["notes"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_check_panel_health(client, test_panel):
    """Test checking panel health."""
    # Mock the check_panel_health method in PanelService
    with patch("api.services.panel_service.PanelService.check_panel_health", 
               new=AsyncMock(return_value={"status": "healthy", "inbounds_count": 2, "version": "1.0.0"})):
        
        # Request health check
        response = await client.post("/api/v1/panels/health-check", json={"panel_id": test_panel.id})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["panel_id"] == test_panel.id
        assert data[0]["health_check"]["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_panel_stats(client, test_panel):
    """Test getting panel statistics."""
    response = await client.get("/api/v1/panels/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_panels" in data
    assert "active_panels" in data
    assert "healthy_panels" in data
    assert data["total_panels"] >= 1
    assert data["active_panels"] >= 1 