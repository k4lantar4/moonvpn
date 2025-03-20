import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.monitoring import MonitoringService
from app.models.monitoring import MonitoringMetric, Alert, SystemStatus
from app.core.config import settings

@pytest.fixture
def monitoring_service():
    """Create a monitoring service instance."""
    return MonitoringService()

@pytest.fixture
def test_metric(db):
    """Create a test monitoring metric."""
    metric = MonitoringMetric(
        name="test_metric",
        value=100,
        unit="count",
        timestamp=time.time(),
        tags={"service": "test"}
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric

@pytest.fixture
def test_alert(db):
    """Create a test alert."""
    alert = Alert(
        name="test_alert",
        description="Test alert description",
        severity="high",
        status="active",
        created_at=time.time(),
        resolved_at=None
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

@pytest.mark.asyncio
async def test_metric_collection(monitoring_service):
    """Test metric collection."""
    # Test system metrics collection
    metrics = await monitoring_service.collect_system_metrics()
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    assert "disk_usage" in metrics
    
    # Test application metrics collection
    app_metrics = await monitoring_service.collect_application_metrics()
    assert "request_count" in app_metrics
    assert "response_time" in app_metrics
    assert "error_rate" in app_metrics
    
    # Test custom metric collection
    custom_metric = await monitoring_service.collect_custom_metric(
        name="test_metric",
        value=100,
        tags={"service": "test"}
    )
    assert custom_metric is not None
    assert custom_metric.name == "test_metric"
    assert custom_metric.value == 100

@pytest.mark.asyncio
async def test_metric_storage(monitoring_service, test_metric):
    """Test metric storage."""
    # Test metric storage
    stored_metric = await monitoring_service.store_metric(test_metric)
    assert stored_metric is not None
    assert stored_metric.id is not None
    
    # Test metric retrieval
    retrieved_metric = await monitoring_service.get_metric(stored_metric.id)
    assert retrieved_metric is not None
    assert retrieved_metric.name == test_metric.name
    assert retrieved_metric.value == test_metric.value
    
    # Test metric aggregation
    aggregated_metrics = await monitoring_service.aggregate_metrics(
        name="test_metric",
        interval="1h"
    )
    assert isinstance(aggregated_metrics, list)
    assert len(aggregated_metrics) > 0

@pytest.mark.asyncio
async def test_alert_management(monitoring_service, test_alert):
    """Test alert management."""
    # Test alert creation
    alert = await monitoring_service.create_alert(
        name="test_alert",
        description="Test alert description",
        severity="high"
    )
    assert alert is not None
    assert alert.name == "test_alert"
    assert alert.severity == "high"
    
    # Test alert status update
    updated_alert = await monitoring_service.update_alert_status(
        alert.id,
        "resolved"
    )
    assert updated_alert.status == "resolved"
    assert updated_alert.resolved_at is not None
    
    # Test alert retrieval
    alerts = await monitoring_service.get_active_alerts()
    assert isinstance(alerts, list)
    assert len(alerts) > 0

@pytest.mark.asyncio
async def test_system_status(monitoring_service):
    """Test system status monitoring."""
    # Test status check
    status = await monitoring_service.check_system_status()
    assert status is not None
    assert "health" in status
    assert "components" in status
    assert "last_check" in status
    
    # Test component status
    components = await monitoring_service.get_component_status()
    assert isinstance(components, list)
    for component in components:
        assert "name" in component
        assert "status" in component
        assert "last_check" in component
    
    # Test status history
    history = await monitoring_service.get_status_history()
    assert isinstance(history, list)
    assert len(history) > 0

@pytest.mark.asyncio
async def test_performance_monitoring(monitoring_service):
    """Test performance monitoring."""
    # Test response time monitoring
    response_time = await monitoring_service.monitor_response_time()
    assert response_time is not None
    assert "average" in response_time
    assert "p95" in response_time
    assert "p99" in response_time
    
    # Test throughput monitoring
    throughput = await monitoring_service.monitor_throughput()
    assert throughput is not None
    assert "requests_per_second" in throughput
    assert "bytes_per_second" in throughput
    
    # Test resource usage monitoring
    resources = await monitoring_service.monitor_resources()
    assert "cpu" in resources
    assert "memory" in resources
    assert "disk" in resources

@pytest.mark.asyncio
async def test_log_monitoring(monitoring_service):
    """Test log monitoring."""
    # Test log collection
    logs = await monitoring_service.collect_logs()
    assert isinstance(logs, list)
    assert len(logs) > 0
    
    # Test log analysis
    analysis = await monitoring_service.analyze_logs()
    assert "error_count" in analysis
    assert "warning_count" in analysis
    assert "info_count" in analysis
    
    # Test log search
    search_results = await monitoring_service.search_logs(
        query="error",
        level="ERROR"
    )
    assert isinstance(search_results, list)
    assert len(search_results) > 0

@pytest.mark.asyncio
async def test_dashboard_metrics(monitoring_service):
    """Test dashboard metrics."""
    # Test metric aggregation
    dashboard_metrics = await monitoring_service.get_dashboard_metrics()
    assert "system_health" in dashboard_metrics
    assert "performance" in dashboard_metrics
    assert "alerts" in dashboard_metrics
    
    # Test metric visualization
    visualization = await monitoring_service.generate_visualization(
        metric_name="test_metric",
        time_range="1h"
    )
    assert "data" in visualization
    assert "chart_type" in visualization
    
    # Test metric comparison
    comparison = await monitoring_service.compare_metrics(
        metric_name="test_metric",
        time_ranges=["1h", "24h"]
    )
    assert isinstance(comparison, list)
    assert len(comparison) == 2

@pytest.mark.asyncio
async def test_notification_system(monitoring_service):
    """Test notification system."""
    # Test alert notification
    notification = await monitoring_service.send_alert_notification(
        alert_id=1,
        channel="email"
    )
    assert notification is not None
    assert "status" in notification
    assert "sent_at" in notification
    
    # Test status notification
    status_notification = await monitoring_service.send_status_notification(
        status="critical",
        channel="slack"
    )
    assert status_notification is not None
    assert status_notification["status"] == "sent"
    
    # Test notification history
    history = await monitoring_service.get_notification_history()
    assert isinstance(history, list)
    assert len(history) > 0

@pytest.mark.asyncio
async def test_reporting(monitoring_service):
    """Test monitoring reporting."""
    # Test report generation
    report = await monitoring_service.generate_report()
    assert report is not None
    assert "summary" in report
    assert "metrics" in report
    assert "alerts" in report
    
    # Test report scheduling
    schedule = await monitoring_service.schedule_report(
        report_type="daily",
        recipients=["test@example.com"]
    )
    assert schedule is not None
    assert "schedule_id" in schedule
    assert "next_run" in schedule
    
    # Test report history
    history = await monitoring_service.get_report_history()
    assert isinstance(history, list)
    assert len(history) > 0

@pytest.mark.asyncio
async def test_error_handling(monitoring_service):
    """Test monitoring error handling."""
    # Test metric collection failure
    with patch("app.services.monitoring.MonitoringService.collect_system_metrics") as mock_collect:
        mock_collect.side_effect = Exception("Collection failed")
        with pytest.raises(Exception) as exc_info:
            await monitoring_service.collect_system_metrics()
        assert "Collection failed" in str(exc_info.value)
    
    # Test alert creation failure
    with patch("app.services.monitoring.MonitoringService.create_alert") as mock_create:
        mock_create.side_effect = Exception("Alert creation failed")
        with pytest.raises(Exception) as exc_info:
            await monitoring_service.create_alert("test", "test")
        assert "Alert creation failed" in str(exc_info.value)
    
    # Test recovery from monitoring failure
    with patch("app.services.monitoring.MonitoringService.recover_from_failure") as mock_recover:
        mock_recover.return_value = True
        result = await monitoring_service.handle_monitoring_failure()
        assert result["status"] == "success"
        assert "recovery_time" in result
        mock_recover.assert_called_once() 