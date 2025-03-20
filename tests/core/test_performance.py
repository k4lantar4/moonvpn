import pytest
import asyncio
from unittest.mock import Mock, patch
from app.core.cache import cache
from app.core.db.optimizer import QueryOptimizer
from app.core.api.optimizer import APIOptimizer
from app.core.monitoring.performance import PerformanceMonitor
from app.core.resource_optimizer import ResourceOptimizer
from app.core.load_balancer import LoadBalancer

@pytest.fixture
async def query_optimizer():
    """Create query optimizer fixture."""
    session = Mock()
    optimizer = QueryOptimizer(session)
    yield optimizer
    await optimizer.clear_stats()

@pytest.fixture
def api_optimizer():
    """Create API optimizer fixture."""
    optimizer = APIOptimizer()
    yield optimizer
    optimizer.clear_request_stats()

@pytest.fixture
def performance_monitor():
    """Create performance monitor fixture."""
    monitor = PerformanceMonitor()
    yield monitor
    asyncio.create_task(monitor.clear_alerts())

@pytest.fixture
async def resource_optimizer():
    """Create resource optimizer fixture."""
    optimizer = ResourceOptimizer()
    yield optimizer
    await optimizer.stop_cleanup()

@pytest.fixture
def load_balancer():
    """Create load balancer fixture."""
    balancer = LoadBalancer()
    yield balancer
    asyncio.create_task(balancer.stop_health_check())

@pytest.mark.asyncio
async def test_query_optimization(query_optimizer):
    """Test query optimization."""
    # Test cache hit
    model = Mock()
    model.__dict__ = {"id": 1, "name": "test"}
    
    with patch.object(cache, "get", return_value=model.__dict__):
        result = await query_optimizer.get_or_create(
            model=Mock,
            cache_key="test:1",
            query=Mock(),
            create_func=Mock()
        )
        assert result.id == 1
        assert result.name == "test"
        
    # Test cache miss
    with patch.object(cache, "get", return_value=None):
        with patch.object(cache, "set", return_value=True):
            result = await query_optimizer.get_or_create(
                model=Mock,
                cache_key="test:2",
                query=Mock(),
                create_func=lambda: model
            )
            assert result.id == 1
            assert result.name == "test"
            
    # Test bulk operations
    items = [{"id": i, "name": f"test{i}"} for i in range(3)]
    with patch.object(cache, "set", return_value=True):
        results = await query_optimizer.bulk_create(
            model=Mock,
            items=items,
            cache_key_prefix="test"
        )
        assert len(results) == 3
        
    # Test query analysis
    with patch.object(query_optimizer.session, "execute") as mock_execute:
        mock_execute.return_value.fetchall.return_value = [
            ("Seq Scan", "1000", "1000", "0.00")
        ]
        analysis = await query_optimizer.analyze_query(Mock())
        assert "plan" in analysis
        assert "stats" in analysis

@pytest.mark.asyncio
async def test_api_optimization(api_optimizer):
    """Test API optimization."""
    # Test response caching
    request = Mock()
    request.method = "GET"
    request.url.path = "/test"
    request.query_params = {}
    
    with patch.object(cache, "get", return_value={"data": "test"}):
        response = await api_optimizer.get_cached_response(
            request=request,
            cache_key="test"
        )
        assert response.body == b'{"data":"test"}'
        
    # Test response compression
    response = Mock()
    response.body = b"test" * 1000
    compressed = api_optimizer.compress_response(response)
    assert compressed.headers["Content-Encoding"] == "gzip"
    
    # Test pagination
    items = [f"item{i}" for i in range(10)]
    paginated = api_optimizer.paginate_response(items, page=1, size=5)
    assert len(paginated["data"]) == 5
    assert paginated["pagination"]["total"] == 10
    assert paginated["pagination"]["total_pages"] == 2
    
    # Test rate limiting
    with patch.object(cache, "get", return_value=100):
        response = api_optimizer.rate_limit_response(request)
        assert response.status_code == 429

@pytest.mark.asyncio
async def test_performance_monitoring(performance_monitor):
    """Test performance monitoring."""
    # Test request metrics
    await performance_monitor.record_request(
        method="GET",
        endpoint="/test",
        status=200,
        duration=0.1
    )
    metrics = await performance_monitor.get_metrics()
    assert metrics["requests"]["total"] > 0
    
    # Test cache metrics
    await performance_monitor.record_cache_metrics(hits=10, misses=5)
    metrics = await performance_monitor.get_metrics()
    assert metrics["cache"]["hits"] == 10
    assert metrics["cache"]["misses"] == 5
    
    # Test database metrics
    await performance_monitor.record_db_metrics(
        operation="select",
        duration=0.1
    )
    metrics = await performance_monitor.get_metrics()
    assert metrics["database"]["queries"] > 0
    
    # Test system metrics
    await performance_monitor.record_system_metrics()
    metrics = await performance_monitor.get_metrics()
    assert "cpu" in metrics["system"]
    assert "memory" in metrics["system"]
    assert "disk" in metrics["system"]
    
    # Test error metrics
    await performance_monitor.record_error("test_error")
    metrics = await performance_monitor.get_metrics()
    assert metrics["errors"]["test_error"] > 0

@pytest.mark.asyncio
async def test_resource_optimization(resource_optimizer):
    """Test resource optimization."""
    # Test cleanup task
    await resource_optimizer.start_cleanup()
    assert resource_optimizer._cleanup_task is not None
    assert not resource_optimizer._cleanup_task.done()
    
    # Test connection management
    connection = Mock()
    await resource_optimizer.register_connection("test_pool", connection)
    assert len(resource_optimizer._active_connections["test_pool"]) == 1
    
    await resource_optimizer.unregister_connection("test_pool", connection)
    assert len(resource_optimizer._active_connections["test_pool"]) == 0
    
    # Test connection pool management
    pool = Mock()
    pool.close = Mock()
    resource_optimizer._connection_pools["test_pool"] = pool
    
    await resource_optimizer.close_connection_pool("test_pool")
    assert "test_pool" not in resource_optimizer._connection_pools
    pool.close.assert_called_once()
    
    # Test resource stats
    stats = await resource_optimizer.get_resource_stats()
    assert "memory" in stats
    assert "disk" in stats
    assert "connections" in stats
    assert "pools" in stats
    
    # Test cleanup stats
    stats = await resource_optimizer.get_cleanup_stats()
    assert "last_cleanup" in stats
    assert "active_connections" in stats
    assert "connection_pools" in stats
    assert "memory_usage" in stats

@pytest.mark.asyncio
async def test_load_balancing(load_balancer):
    """Test load balancing."""
    # Test server management
    server_id = "test_server"
    server_url = "http://test:8000"
    
    await load_balancer.add_server(
        server_id=server_id,
        url=server_url,
        weight=1
    )
    assert server_id in load_balancer._servers
    
    # Test server selection
    server = await load_balancer.get_server()
    assert server["id"] == server_id
    assert server["url"] == server_url
    
    # Test health check
    await load_balancer.start_health_check()
    assert load_balancer._health_check_task is not None
    assert not load_balancer._health_check_task.done()
    
    # Test server status
    status = await load_balancer.get_server_status(server_id)
    assert status["id"] == server_id
    assert "health" in status
    assert "last_check" in status
    
    # Test failover
    with patch.object(load_balancer, "_check_server") as mock_check:
        mock_check.return_value = False
        await load_balancer._handle_failover(server_id)
        status = await load_balancer.get_server_status(server_id)
        assert status["health"] == "unhealthy" 