"""
Tests for the DatabaseManager class.
"""

import pytest
import os
from datetime import datetime
from core.database.connection import DatabaseManager
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

# Test configuration
TEST_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'test_db',
    'username': 'test_user',
    'password': 'test_password'
}

@pytest.fixture
def db_manager():
    """Create a DatabaseManager instance for testing."""
    manager = DatabaseManager()
    with patch('bot.database.connection.create_engine') as mock_create_engine:
        # Mock engine and session
        mock_engine = MagicMock()
        mock_session = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value.execute.return_value = True
        
        # Initialize manager with test config
        manager.initialize(**TEST_DB_CONFIG)
        yield manager
        
        # Cleanup
        manager.close()

def test_singleton_pattern():
    """Test that DatabaseManager follows singleton pattern."""
    manager1 = DatabaseManager()
    manager2 = DatabaseManager()
    assert manager1 is manager2

def test_initialization(db_manager):
    """Test database initialization."""
    assert db_manager.engine is not None
    assert db_manager.SessionLocal is not None
    assert db_manager.connection_url == f"postgresql://{TEST_DB_CONFIG['username']}:{TEST_DB_CONFIG['password']}@{TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['database']}"

def test_get_session(db_manager):
    """Test session management."""
    with patch('bot.database.connection.sessionmaker') as mock_sessionmaker:
        mock_session = MagicMock()
        mock_sessionmaker.return_value = lambda: mock_session
        
        with db_manager.get_session() as session:
            assert session is mock_session
        
        # Verify session operations
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

def test_get_session_with_error(db_manager):
    """Test session management with error."""
    with patch('bot.database.connection.sessionmaker') as mock_sessionmaker:
        mock_session = MagicMock()
        mock_sessionmaker.return_value = lambda: mock_session
        mock_session.commit.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            with db_manager.get_session() as session:
                pass
        
        # Verify session operations
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

def test_check_connection(db_manager):
    """Test database connection check."""
    with patch.object(db_manager, 'get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        assert db_manager.check_connection() is True
        mock_session.execute.assert_called_once_with(text("SELECT 1"))

def test_get_table_sizes(db_manager):
    """Test getting table sizes."""
    mock_result = [
        MagicMock(
            table_name='test_table',
            total_size=1000,
            data_size=800,
            index_size=200,
            external_size=0
        )
    ]
    
    with patch.object(db_manager, 'get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = db_manager.get_table_sizes()
        
        assert 'test_table' in result
        assert result['test_table']['total_size'] == 1000
        assert result['test_table']['data_size'] == 800
        assert result['test_table']['index_size'] == 200

def test_vacuum_analyze(db_manager):
    """Test VACUUM ANALYZE operation."""
    with patch.object(db_manager.engine, 'raw_connection') as mock_raw_connection:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_raw_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # Test vacuum analyze on specific table
        db_manager.vacuum_analyze('test_table')
        mock_cursor.execute.assert_called_with("VACUUM ANALYZE test_table;")
        
        # Test vacuum analyze on entire database
        db_manager.vacuum_analyze()
        mock_cursor.execute.assert_called_with("VACUUM ANALYZE;")

@patch('subprocess.run')
def test_create_backup(mock_run, db_manager):
    """Test database backup creation."""
    mock_run.return_value = MagicMock(returncode=0)
    
    backup_dir = '/tmp/backups'
    result = db_manager.create_backup(backup_dir)
    
    assert result.startswith('/tmp/backups/backup_')
    assert result.endswith('.sql')
    mock_run.assert_called_once()

@patch('subprocess.run')
def test_restore_backup(mock_run, db_manager):
    """Test database backup restoration."""
    mock_run.return_value = MagicMock(returncode=0)
    
    backup_file = '/tmp/backups/backup_test.sql'
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        result = db_manager.restore_backup(backup_file)
        
        assert result is True
        mock_run.assert_called_once()

def test_get_table_info(db_manager):
    """Test getting table information."""
    mock_inspector = MagicMock()
    mock_inspector.get_columns.return_value = [{'name': 'id', 'type': 'INTEGER'}]
    mock_inspector.get_indexes.return_value = [{'name': 'idx_id', 'column_names': ['id']}]
    mock_inspector.get_foreign_keys.return_value = []
    mock_inspector.get_pk_constraint.return_value = {'name': 'pk_id', 'constrained_columns': ['id']}
    mock_inspector.get_schema_names.return_value = ['public']
    
    with patch('sqlalchemy.inspect') as mock_inspect:
        mock_inspect.return_value = mock_inspector
        
        result = db_manager.get_table_info('test_table')
        
        assert 'columns' in result
        assert 'indexes' in result
        assert 'foreign_keys' in result
        assert 'primary_key' in result
        assert 'schema' in result
        assert result['columns'][0]['name'] == 'id'

def test_analyze_table_bloat(db_manager):
    """Test table bloat analysis."""
    mock_result = [
        MagicMock(
            full_table_name='public.test_table',
            size='1 MB',
            bloat='100 KB',
            bloat_percentage=10.5
        )
    ]
    
    with patch.object(db_manager, 'get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = db_manager.analyze_table_bloat()
        
        assert 'public.test_table' in result
        assert result['public.test_table']['size'] == '1 MB'
        assert result['public.test_table']['bloat'] == '100 KB'
        assert result['public.test_table']['bloat_percentage'] == 10.5

def test_get_active_connections(db_manager):
    """Test getting active connections."""
    mock_result = [
        MagicMock(
            pid=1234,
            usename='test_user',
            application_name='test_app',
            client_addr='127.0.0.1',
            backend_start=datetime.now(),
            state='active',
            query='SELECT 1'
        )
    ]
    
    with patch.object(db_manager, 'get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = db_manager.get_active_connections()
        
        assert len(result) == 1
        assert result[0]['pid'] == 1234
        assert result[0]['usename'] == 'test_user'
        assert result[0]['state'] == 'active'

def test_kill_connection(db_manager):
    """Test killing a database connection."""
    with patch.object(db_manager, 'get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        result = db_manager.kill_connection(1234)
        
        assert result is True
        mock_session.execute.assert_called_once()

def test_close(db_manager):
    """Test database connection closure."""
    db_manager.close()
    assert db_manager.engine is None
    assert db_manager.SessionLocal is None 