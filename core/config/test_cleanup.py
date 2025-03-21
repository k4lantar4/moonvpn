"""
Tests for the cleanup service.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import os
import shutil

from core.services.cleanup import CleanupService
from core.database.models import SystemBackup, SystemMetrics, SystemLogs

@pytest.fixture
def cleanup_service(db_session):
    """Create a cleanup service instance."""
    return CleanupService(db_session)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory."""
    temp = tmp_path / "temp"
    temp.mkdir()
    return temp

@pytest.fixture
def sample_backup(db_session):
    """Create a sample backup record."""
    backup = SystemBackup(
        storage_path="/tmp/test_backup.tar.gz",
        created_at=datetime.utcnow() - timedelta(days=40)
    )
    db_session.add(backup)
    db_session.commit()
    return backup

@pytest.fixture
def sample_metrics(db_session):
    """Create sample metrics records."""
    metrics = []
    for i in range(10):
        metric = SystemMetrics(
            timestamp=datetime.utcnow() - timedelta(days=i),
            cpu_usage=50.0,
            memory_usage=60.0,
            disk_usage=70.0
        )
        metrics.append(metric)
    
    db_session.add_all(metrics)
    db_session.commit()
    return metrics

@pytest.fixture
def sample_logs(db_session):
    """Create sample log records."""
    logs = []
    for i in range(10):
        log = SystemLogs(
            timestamp=datetime.utcnow() - timedelta(days=i),
            level="INFO",
            message=f"Test log {i}"
        )
        logs.append(log)
    
    db_session.add_all(logs)
    db_session.commit()
    return logs

@pytest.mark.asyncio
async def test_cleanup_old_backups(cleanup_service, sample_backup, db_session):
    """Test cleaning up old backups."""
    # Create test backup file
    backup_path = Path(sample_backup.storage_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text("test backup content")
    
    result = await cleanup_service.cleanup_old_backups(retention_days=30)
    
    assert result["removed_count"] == 1
    assert result["freed_space_bytes"] > 0
    assert not db_session.query(SystemBackup).filter_by(id=sample_backup.id).first()
    assert not backup_path.exists()

@pytest.mark.asyncio
async def test_cleanup_old_metrics(cleanup_service, sample_metrics, db_session):
    """Test cleaning up old metrics."""
    result = await cleanup_service.cleanup_old_metrics(retention_days=5)
    
    remaining = db_session.query(SystemMetrics).count()
    assert result["removed_count"] == 5  # Should remove metrics older than 5 days
    assert remaining == 5  # Should keep metrics newer than 5 days

@pytest.mark.asyncio
async def test_cleanup_old_logs(cleanup_service, sample_logs, db_session):
    """Test cleaning up old logs."""
    result = await cleanup_service.cleanup_old_logs(retention_days=5)
    
    remaining = db_session.query(SystemLogs).count()
    assert result["removed_count"] == 5  # Should remove logs older than 5 days
    assert remaining == 5  # Should keep logs newer than 5 days

@pytest.mark.asyncio
async def test_cleanup_temp_files(cleanup_service, temp_dir, monkeypatch):
    """Test cleaning up temporary files."""
    # Create some temporary files and directories
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    
    test_dir = temp_dir / "test_dir"
    test_dir.mkdir()
    (test_dir / "test.txt").write_text("test content")
    
    # Mock settings.TEMP_DIR
    monkeypatch.setattr("core.config.settings.TEMP_DIR", str(temp_dir))
    
    result = await cleanup_service.cleanup_temp_files()
    
    assert result["removed_count"] == 2  # Should remove both file and directory
    assert result["freed_space_bytes"] > 0
    assert not test_file.exists()
    assert not test_dir.exists()

@pytest.mark.asyncio
async def test_cleanup_all(
    cleanup_service,
    sample_backup,
    sample_metrics,
    sample_logs,
    temp_dir,
    monkeypatch,
    db_session
):
    """Test running all cleanup operations."""
    # Create test backup file
    backup_path = Path(sample_backup.storage_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text("test backup content")
    
    # Create temp files
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    
    # Mock settings.TEMP_DIR
    monkeypatch.setattr("core.config.settings.TEMP_DIR", str(temp_dir))
    
    result = await cleanup_service.cleanup_all()
    
    assert "backups" in result
    assert "metrics" in result
    assert "logs" in result
    assert "temp_files" in result
    assert "timestamp" in result
    
    # Verify backups were cleaned
    assert not db_session.query(SystemBackup).filter_by(id=sample_backup.id).first()
    assert not backup_path.exists()
    
    # Verify metrics were cleaned
    metrics_count = db_session.query(SystemMetrics).count()
    assert metrics_count < 10
    
    # Verify logs were cleaned
    logs_count = db_session.query(SystemLogs).count()
    assert logs_count < 10
    
    # Verify temp files were cleaned
    assert not test_file.exists()

@pytest.mark.asyncio
async def test_cleanup_error_handling(cleanup_service, db_session, monkeypatch):
    """Test error handling in cleanup operations."""
    def mock_error(*args, **kwargs):
        raise Exception("Test error")
    
    # Mock database query to raise an error
    monkeypatch.setattr("sqlalchemy.orm.Session.query", mock_error)
    
    with pytest.raises(Exception) as exc:
        await cleanup_service.cleanup_old_backups()
    assert str(exc.value) == "Test error" 