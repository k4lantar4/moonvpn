"""
Test cases for performance testing API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from ....core.api.v1.endpoints.performance import router
from ....core.main import app
from ....models.user import User
from ....schemas.performance import TestConfig, TestResult, PerformanceTest, TestStatus, TestSummary

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
def mock_performance_service():
    with patch("core.api.v1.endpoints.performance.PerformanceTestingService") as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service

@pytest.fixture
def test_config():
    return TestConfig(
        concurrent_users=10,
        actions_per_user=5,
        action_delay=0.1,
        api_latency=0.05,
        error_rate=0.1,
        max_instances=3
    )

def test_start_load_test(mock_user, mock_performance_service, test_config):
    """Test starting a load test."""
    mock_performance_service.start_load_test.return_value = "test_id_1"
    
    response = client.post("/api/v1/performance/load", json=test_config.dict())
    assert response.status_code == 200
    assert response.json() == "test_id_1"

def test_start_stress_test(mock_user, mock_performance_service, test_config):
    """Test starting a stress test."""
    mock_performance_service.start_stress_test.return_value = "test_id_2"
    
    response = client.post("/api/v1/performance/stress", json=test_config.dict())
    assert response.status_code == 200
    assert response.json() == "test_id_2"

def test_start_scalability_test(mock_user, mock_performance_service, test_config):
    """Test starting a scalability test."""
    mock_performance_service.start_scalability_test.return_value = "test_id_3"
    
    response = client.post("/api/v1/performance/scalability", json=test_config.dict())
    assert response.status_code == 200
    assert response.json() == "test_id_3"

def test_stop_test(mock_user, mock_performance_service):
    """Test stopping a test."""
    mock_performance_service.stop_test.return_value = True
    
    response = client.post("/api/v1/performance/test_id/stop")
    assert response.status_code == 200
    assert response.json() is True

def test_stop_test_not_found(mock_user, mock_performance_service):
    """Test stopping a non-existent test."""
    mock_performance_service.stop_test.return_value = False
    
    response = client.post("/api/v1/performance/test_id/stop")
    assert response.status_code == 404
    assert "Test test_id not found" in response.json()["detail"]

def test_get_test_status(mock_user, mock_performance_service):
    """Test getting test status."""
    mock_status = TestStatus(
        test_id="test_id",
        status="running",
        results=[]
    )
    mock_performance_service.get_test_status.return_value = mock_status
    
    response = client.get("/api/v1/performance/test_id/status")
    assert response.status_code == 200
    assert response.json() == mock_status.dict()

def test_get_test_status_not_found(mock_user, mock_performance_service):
    """Test getting status of non-existent test."""
    mock_performance_service.get_test_status.return_value = None
    
    response = client.get("/api/v1/performance/test_id/status")
    assert response.status_code == 404
    assert "Test test_id not found" in response.json()["detail"]

def test_get_test_summary(mock_user, mock_performance_service):
    """Test getting test summary."""
    mock_status = {
        "test_id": "test_id",
        "type": "load",
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow(),
        "duration": 60.0,
        "status": "completed",
        "results": [
            TestResult(
                id=1,
                test_id="test_id",
                user_id=1,
                duration=1.0,
                cpu_usage=50.0,
                memory_usage=60.0,
                disk_usage=40.0,
                success=True,
                timestamp=datetime.utcnow()
            )
        ]
    }
    mock_performance_service.get_test_status.return_value = mock_status
    
    response = client.get("/api/v1/performance/test_id/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["test_id"] == "test_id"
    assert data["type"] == "load"
    assert data["status"] == "completed"
    assert data["total_users"] == 1
    assert data["total_actions"] == 1
    assert data["success_rate"] == 1.0
    assert data["avg_cpu_usage"] == 50.0
    assert data["avg_memory_usage"] == 60.0
    assert data["avg_disk_usage"] == 40.0
    assert data["avg_duration"] == 1.0

def test_get_test_summary_not_found(mock_user, mock_performance_service):
    """Test getting summary of non-existent test."""
    mock_performance_service.get_test_status.return_value = None
    
    response = client.get("/api/v1/performance/test_id/summary")
    assert response.status_code == 404
    assert "Test test_id not found" in response.json()["detail"]

def test_get_test_summary_no_results(mock_user, mock_performance_service):
    """Test getting summary of test with no results."""
    mock_status = {
        "test_id": "test_id",
        "type": "load",
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow(),
        "duration": 60.0,
        "status": "completed",
        "results": []
    }
    mock_performance_service.get_test_status.return_value = mock_status
    
    response = client.get("/api/v1/performance/test_id/summary")
    assert response.status_code == 400
    assert "No results available" in response.json()["detail"]

def test_list_tests(mock_user, mock_performance_service):
    """Test listing all tests."""
    mock_tests = [
        PerformanceTest(
            id="test_id_1",
            type="load",
            config={},
            start_time=datetime.utcnow(),
            status="completed"
        ),
        PerformanceTest(
            id="test_id_2",
            type="stress",
            config={},
            start_time=datetime.utcnow(),
            status="running"
        )
    ]
    mock_performance_service.db.query.return_value.all.return_value = mock_tests
    
    response = client.get("/api/v1/performance/")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == "test_id_1"
    assert response.json()[1]["id"] == "test_id_2"

def test_get_test_results(mock_user, mock_performance_service):
    """Test getting test results."""
    mock_results = [
        TestResult(
            id=1,
            test_id="test_id",
            user_id=1,
            duration=1.0,
            cpu_usage=50.0,
            memory_usage=60.0,
            disk_usage=40.0,
            success=True,
            timestamp=datetime.utcnow()
        )
    ]
    mock_status = {
        "test_id": "test_id",
        "type": "load",
        "start_time": datetime.utcnow(),
        "end_time": datetime.utcnow(),
        "duration": 60.0,
        "status": "completed",
        "results": mock_results
    }
    mock_performance_service.get_test_status.return_value = mock_status
    
    response = client.get("/api/v1/performance/test_id/results")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1
    assert response.json()[0]["user_id"] == 1
    assert response.json()[0]["success"] is True

def test_get_test_results_not_found(mock_user, mock_performance_service):
    """Test getting results of non-existent test."""
    mock_performance_service.get_test_status.return_value = None
    
    response = client.get("/api/v1/performance/test_id/results")
    assert response.status_code == 404
    assert "Test test_id not found" in response.json()["detail"]

"""
Tests for performance tuning API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from ....core.api.v1.performance import router
from ....core.models.performance import TuningType, TuningPhase
from ....core.schemas.performance import TuningConfig, TuningRead, TuningStatus

client = TestClient(router)

@pytest.fixture
def mock_tuning_service():
    """Mock the performance tuning service."""
    with patch("core.api.v1.performance.PerformanceTuningService") as mock:
        service = mock.return_value
        service.start_database_tuning = AsyncMock()
        service.start_cache_tuning = AsyncMock()
        service.start_network_tuning = AsyncMock()
        service.start_application_tuning = AsyncMock()
        service.stop_tuning = AsyncMock()
        service.get_tuning_status = AsyncMock()
        service.get_tuning = AsyncMock()
        service.list_tunings = AsyncMock()
        yield service

@pytest.fixture
def test_config():
    """Create a test tuning configuration."""
    return TuningConfig(
        max_connections=100,
        buffer_pool_size=1024,
        query_cache_size=512,
        cache_size=2048,
        eviction_policy="lru",
        ttl=3600,
        tcp_keepalive=True,
        connection_timeout=30,
        max_retries=3,
        thread_pool_size=10,
        memory_limit=4096,
        gc_interval=300
    )

@pytest.mark.asyncio
async def test_start_database_tuning(mock_tuning_service, test_config):
    """Test starting database performance tuning."""
    mock_tuning_service.start_database_tuning.return_value = "test_tuning_1"
    
    response = client.post("/database", json=test_config.dict())
    
    assert response.status_code == 200
    assert response.json() == "test_tuning_1"
    mock_tuning_service.start_database_tuning.assert_called_once_with(test_config)

@pytest.mark.asyncio
async def test_start_cache_tuning(mock_tuning_service, test_config):
    """Test starting cache performance tuning."""
    mock_tuning_service.start_cache_tuning.return_value = "test_tuning_2"
    
    response = client.post("/cache", json=test_config.dict())
    
    assert response.status_code == 200
    assert response.json() == "test_tuning_2"
    mock_tuning_service.start_cache_tuning.assert_called_once_with(test_config)

@pytest.mark.asyncio
async def test_start_network_tuning(mock_tuning_service, test_config):
    """Test starting network performance tuning."""
    mock_tuning_service.start_network_tuning.return_value = "test_tuning_3"
    
    response = client.post("/network", json=test_config.dict())
    
    assert response.status_code == 200
    assert response.json() == "test_tuning_3"
    mock_tuning_service.start_network_tuning.assert_called_once_with(test_config)

@pytest.mark.asyncio
async def test_start_application_tuning(mock_tuning_service, test_config):
    """Test starting application performance tuning."""
    mock_tuning_service.start_application_tuning.return_value = "test_tuning_4"
    
    response = client.post("/application", json=test_config.dict())
    
    assert response.status_code == 200
    assert response.json() == "test_tuning_4"
    mock_tuning_service.start_application_tuning.assert_called_once_with(test_config)

@pytest.mark.asyncio
async def test_stop_tuning_success(mock_tuning_service):
    """Test stopping a tuning process successfully."""
    mock_tuning_service.stop_tuning.return_value = True
    
    response = client.post("/test_tuning_1/stop")
    
    assert response.status_code == 200
    assert response.json() is True
    mock_tuning_service.stop_tuning.assert_called_once_with("test_tuning_1")

@pytest.mark.asyncio
async def test_stop_tuning_not_found(mock_tuning_service):
    """Test stopping a non-existent tuning process."""
    mock_tuning_service.stop_tuning.return_value = False
    
    response = client.post("/test_tuning_999/stop")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Tuning process not found"
    mock_tuning_service.stop_tuning.assert_called_once_with("test_tuning_999")

@pytest.mark.asyncio
async def test_get_tuning_status_success(mock_tuning_service):
    """Test getting tuning status successfully."""
    mock_status = TuningStatus(
        tuning_id="test_tuning_1",
        status="running",
        results=[]
    )
    mock_tuning_service.get_tuning_status.return_value = mock_status
    
    response = client.get("/test_tuning_1/status")
    
    assert response.status_code == 200
    assert response.json() == {
        "tuning_id": "test_tuning_1",
        "status": "running",
        "results": []
    }
    mock_tuning_service.get_tuning_status.assert_called_once_with("test_tuning_1")

@pytest.mark.asyncio
async def test_get_tuning_status_not_found(mock_tuning_service):
    """Test getting status of a non-existent tuning process."""
    mock_tuning_service.get_tuning_status.return_value = None
    
    response = client.get("/test_tuning_999/status")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Tuning process not found"
    mock_tuning_service.get_tuning_status.assert_called_once_with("test_tuning_999")

@pytest.mark.asyncio
async def test_get_tuning_success(mock_tuning_service):
    """Test getting tuning details successfully."""
    mock_tuning = TuningRead(
        id="test_tuning_1",
        type=TuningType.DATABASE,
        config=TuningConfig(),
        start_time=datetime.utcnow(),
        status="running",
        results=[]
    )
    mock_tuning_service.get_tuning.return_value = mock_tuning
    
    response = client.get("/test_tuning_1")
    
    assert response.status_code == 200
    assert response.json()["id"] == "test_tuning_1"
    assert response.json()["type"] == TuningType.DATABASE
    mock_tuning_service.get_tuning.assert_called_once_with("test_tuning_1")

@pytest.mark.asyncio
async def test_get_tuning_not_found(mock_tuning_service):
    """Test getting details of a non-existent tuning process."""
    mock_tuning_service.get_tuning.return_value = None
    
    response = client.get("/test_tuning_999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Tuning process not found"
    mock_tuning_service.get_tuning.assert_called_once_with("test_tuning_999")

@pytest.mark.asyncio
async def test_list_tunings(mock_tuning_service):
    """Test listing all tuning processes."""
    mock_tunings = [
        TuningRead(
            id="test_tuning_1",
            type=TuningType.DATABASE,
            config=TuningConfig(),
            start_time=datetime.utcnow(),
            status="running",
            results=[]
        ),
        TuningRead(
            id="test_tuning_2",
            type=TuningType.CACHE,
            config=TuningConfig(),
            start_time=datetime.utcnow(),
            status="completed",
            results=[]
        )
    ]
    mock_tuning_service.list_tunings.return_value = mock_tunings
    
    response = client.get("/")
    
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == "test_tuning_1"
    assert response.json()[1]["id"] == "test_tuning_2"
    mock_tuning_service.list_tunings.assert_called_once_with(None)

@pytest.mark.asyncio
async def test_list_tunings_by_type(mock_tuning_service):
    """Test listing tuning processes by type."""
    mock_tunings = [
        TuningRead(
            id="test_tuning_1",
            type=TuningType.DATABASE,
            config=TuningConfig(),
            start_time=datetime.utcnow(),
            status="running",
            results=[]
        )
    ]
    mock_tuning_service.list_tunings.return_value = mock_tunings
    
    response = client.get("/?type=database")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == "test_tuning_1"
    assert response.json()[0]["type"] == TuningType.DATABASE
    mock_tuning_service.list_tunings.assert_called_once_with(TuningType.DATABASE) 