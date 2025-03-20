"""
Test cases for resource optimization API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from core.main import app
from core.schemas.resource_optimization import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationStatusResponse,
    OptimizationHistoryResponse,
    ResourceMetricsResponse,
    OptimizationSummaryResponse
)

client = TestClient(app)

@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return {
        "id": "test_user_id",
        "username": "test_user",
        "email": "test@example.com",
        "is_active": True,
        "is_superuser": False
    }

@pytest.fixture
def mock_optimization_service():
    """Create a mock optimization service."""
    with patch("core.api.v1.resource_optimization.ResourceOptimizationService") as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service

def test_start_optimization_success(mock_user, mock_optimization_service):
    """Test successful optimization start."""
    # Arrange
    request_data = {
        "resource_type": "cpu",
        "target_usage": 80.0,
        "max_iterations": 3,
        "interval": 1.0,
        "threshold": 0.1,
        "parameters": {}
    }
    mock_optimization_service.start_optimization.return_value = "test_optimization_id"

    # Act
    response = client.post(
        "/api/v1/optimization/start",
        json=request_data,
        headers={"Authorization": f"Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "optimization_id" in response.json()["data"]
    mock_optimization_service.start_optimization.assert_called_once()

def test_start_optimization_failure(mock_user, mock_optimization_service):
    """Test failed optimization start."""
    # Arrange
    request_data = {
        "resource_type": "cpu",
        "target_usage": 80.0
    }
    mock_optimization_service.start_optimization.side_effect = Exception("Test error")

    # Act
    response = client.post(
        "/api/v1/optimization/start",
        json=request_data,
        headers={"Authorization": f"Bearer test_token"}
    )

    # Assert
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]

def test_stop_optimization_success(mock_user, mock_optimization_service):
    """Test successful optimization stop."""
    # Arrange
    mock_optimization_service.stop_optimization.return_value = None

    # Act
    response = client.post(
        "/api/v1/optimization/stop",
        headers={"Authorization": f"Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_optimization_service.stop_optimization.assert_called_once()

def test_get_optimization_status_success(mock_user, mock_optimization_service):
    """Test successful status retrieval."""
    # Arrange
    mock_status = {
        "is_active": True,
        "resource_type": "cpu",
        "last_optimized": datetime.now().isoformat(),
        "current_metrics": {"cpu_percent": 75.0},
        "optimization_history": []
    }
    mock_optimization_service.get_status.return_value = mock_status

    # Act
    response = client.get(
        "/api/v1/optimization/status",
        headers={"Authorization": f"Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["is_active"] is True
    mock_optimization_service.get_status.assert_called_once()

def test_get_optimization_history_success(mock_user, mock_optimization_service):
    """Test successful history retrieval."""
    # Arrange
    mock_history = {
        "total_optimizations": 5,
        "successful_optimizations": 4,
        "failed_optimizations": 1,
        "history": []
    }
    mock_optimization_service.get_history.return_value = mock_history

    # Act
    response = client.get(
        "/api/v1/optimization/history",
        headers={"Authorization": f"Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["total_optimizations"] == 5
    mock_optimization_service.get_history.assert_called_once()

def test_get_resource_metrics_success(mock_user, mock_optimization_service):
    """Test successful metrics retrieval."""
    # Arrange
    mock_metrics = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "cpu_percent": 75.0,
            "memory_percent": 60.0
        },
        "optimization_status": {"is_active": True}
    }
    mock_optimization_service.get_metrics.return_value = mock_metrics

    # Act
    response = client.get(
        "/api/v1/optimization/metrics",
        headers={"Authorization": f"Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert "cpu_percent" in response.json()["metrics"]
    mock_optimization_service.get_metrics.assert_called_once()

def test_get_optimization_summary_success(mock_user, mock_optimization_service):
    """Test successful summary retrieval."""
    # Arrange
    mock_summary = {
        "total_optimizations": 10,
        "successful_optimizations": 8,
        "failed_optimizations": 2,
        "average_improvement": 15.5,
        "best_optimization": {"improvement": 25.0},
        "worst_optimization": {"improvement": 5.0},
        "resource_types": {"cpu": 5, "memory": 5}
    }
    mock_optimization_service.get_summary.return_value = mock_summary

    # Act
    response = client.get(
        "/api/v1/optimization/summary",
        headers={"Authorization": f"Bearer test_token"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["total_optimizations"] == 10
    mock_optimization_service.get_summary.assert_called_once() 