import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.order import Order
from app.models.transaction import Transaction
from app.models.vpn_config import VPNConfig
from app.models.server import Server
from app.services.database import DatabaseService

@pytest.fixture
def db_service():
    """Create a database service instance."""
    return DatabaseService()

@pytest.fixture
def test_data(db):
    """Create test data for database optimization tests."""
    # Create test users
    users = []
    for i in range(100):
        user = User(
            telegram_id=100000000 + i,
            username=f"testuser{i}",
            email=f"test{i}@example.com",
            phone_number=f"9891234567{i:03d}",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        users.append(user)
    
    # Create test orders
    orders = []
    for user in users:
        for j in range(5):
            order = Order(
                user_id=user.id,
                amount=100 * (j + 1),
                currency="USD",
                status="completed",
                payment_method="wallet"
            )
            db.add(order)
            orders.append(order)
    
    # Create test transactions
    transactions = []
    for order in orders:
        transaction = Transaction(
            order_id=order.id,
            amount=order.amount,
            currency=order.currency,
            status="completed",
            payment_method=order.payment_method
        )
        db.add(transaction)
        transactions.append(transaction)
    
    # Create test VPN configs
    vpn_configs = []
    for user in users:
        config = VPNConfig(
            user_id=user.id,
            client_cert="test_cert",
            client_key="test_key",
            server_id=1
        )
        db.add(config)
        vpn_configs.append(config)
    
    # Create test servers
    servers = []
    for i in range(10):
        server = Server(
            name=f"Test Server {i}",
            host=f"test{i}.example.com",
            port=1194 + i,
            protocol="udp",
            country="US",
            is_active=True,
            load=0.5
        )
        db.add(server)
        servers.append(server)
    
    db.commit()
    return {
        "users": users,
        "orders": orders,
        "transactions": transactions,
        "vpn_configs": vpn_configs,
        "servers": servers
    }

@pytest.mark.asyncio
async def test_index_optimization(db_service, test_data):
    """Test database index optimization."""
    # Test query performance with and without indexes
    with SessionLocal() as session:
        # Query without index
        start_time = time.time()
        result = session.query(User).filter(User.is_active == True).all()
        time_without_index = time.time() - start_time
        
        # Create index
        await db_service.create_index("users", "is_active")
        
        # Query with index
        start_time = time.time()
        result = session.query(User).filter(User.is_active == True).all()
        time_with_index = time.time() - start_time
        
        assert time_with_index < time_without_index

@pytest.mark.asyncio
async def test_query_optimization(db_service, test_data):
    """Test query optimization."""
    with SessionLocal() as session:
        # Test optimized join query
        start_time = time.time()
        result = session.query(
            User.username,
            Order.amount,
            Transaction.status
        ).join(
            Order, User.id == Order.user_id
        ).join(
            Transaction, Order.id == Transaction.order_id
        ).filter(
            User.is_active == True
        ).all()
        time_with_optimization = time.time() - start_time
        
        # Test unoptimized query
        start_time = time.time()
        result = session.query(User).all()
        for user in result:
            orders = session.query(Order).filter(Order.user_id == user.id).all()
            for order in orders:
                transactions = session.query(Transaction).filter(
                    Transaction.order_id == order.id
                ).all()
        time_without_optimization = time.time() - start_time
        
        assert time_with_optimization < time_without_optimization

@pytest.mark.asyncio
async def test_connection_pooling(db_service, test_data):
    """Test database connection pooling."""
    # Test connection pool size
    pool_size = engine.pool.size()
    assert pool_size > 0
    
    # Test connection reuse
    connections = []
    for _ in range(10):
        with SessionLocal() as session:
            connections.append(session)
    
    # Verify connections are reused
    assert len(set(id(conn) for conn in connections)) < 10

@pytest.mark.asyncio
async def test_query_caching(db_service, test_data):
    """Test query result caching."""
    with SessionLocal() as session:
        # First query
        start_time = time.time()
        result1 = session.query(User).filter(User.is_active == True).all()
        time_first_query = time.time() - start_time
        
        # Second query (should be cached)
        start_time = time.time()
        result2 = session.query(User).filter(User.is_active == True).all()
        time_second_query = time.time() - start_time
        
        assert time_second_query < time_first_query

@pytest.mark.asyncio
async def test_batch_operations(db_service, test_data):
    """Test batch database operations."""
    # Test batch insert
    start_time = time.time()
    new_users = []
    for i in range(100):
        user = User(
            telegram_id=200000000 + i,
            username=f"batchuser{i}",
            email=f"batch{i}@example.com",
            phone_number=f"9891234568{i:03d}",
            is_active=True,
            is_verified=True
        )
        new_users.append(user)
    
    with SessionLocal() as session:
        session.bulk_save_objects(new_users)
        session.commit()
    time_batch_insert = time.time() - start_time
    
    # Test individual inserts
    start_time = time.time()
    with SessionLocal() as session:
        for user in new_users:
            session.add(user)
            session.commit()
    time_individual_insert = time.time() - start_time
    
    assert time_batch_insert < time_individual_insert

@pytest.mark.asyncio
async def test_database_maintenance(db_service, test_data):
    """Test database maintenance operations."""
    # Test vacuum operation
    await db_service.vacuum_database()
    
    # Test analyze operation
    await db_service.analyze_database()
    
    # Test reindex operation
    await db_service.reindex_database()
    
    # Verify maintenance operations completed successfully
    with SessionLocal() as session:
        result = session.execute(text("SELECT * FROM pg_stat_user_tables"))
        assert result is not None

@pytest.mark.asyncio
async def test_error_handling(db_service, test_data):
    """Test database error handling."""
    # Test connection error
    with patch("app.core.database.SessionLocal") as mock_session:
        mock_session.side_effect = Exception("Connection failed")
        with pytest.raises(Exception) as exc_info:
            with SessionLocal() as session:
                session.query(User).all()
        assert "Connection failed" in str(exc_info.value)
    
    # Test query timeout
    with patch("app.core.database.SessionLocal") as mock_session:
        mock_session.side_effect = Exception("Query timeout")
        with pytest.raises(Exception) as exc_info:
            with SessionLocal() as session:
                session.query(User).all()
        assert "Query timeout" in str(exc_info.value)

@pytest.mark.asyncio
async def test_database_monitoring(db_service, test_data):
    """Test database monitoring."""
    # Test query performance monitoring
    metrics = await db_service.get_query_metrics()
    assert "slow_queries" in metrics
    assert "query_count" in metrics
    assert "average_query_time" in metrics
    
    # Test connection pool monitoring
    pool_metrics = await db_service.get_pool_metrics()
    assert "pool_size" in pool_metrics
    assert "checkedin" in pool_metrics
    assert "checkedout" in pool_metrics
    assert "overflow" in pool_metrics 