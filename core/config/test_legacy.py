"""
Tests for legacy code management service.
"""

import pytest
from datetime import datetime
from pathlib import Path
import shutil

from core.services.legacy import LegacyCodeService
from core.database.models.legacy import LegacyCode, LegacyMigration

@pytest.fixture
def legacy_service(db_session):
    """Create a legacy code service instance."""
    return LegacyCodeService(db_session)

@pytest.fixture
def test_code_dir(tmp_path):
    """Create a test directory with some code files."""
    code_dir = tmp_path / "test_code"
    code_dir.mkdir()
    
    # Create some test files
    (code_dir / "test.py").write_text("print('Hello, World!')")
    (code_dir / "config.json").write_text('{"key": "value"}')
    
    return code_dir

@pytest.fixture
def sample_legacy_code(db_session):
    """Create a sample legacy code record."""
    legacy_code = LegacyCode(
        original_path="/path/to/legacy",
        archive_path="/path/to/archive",
        description="Test legacy code",
        archived_at=datetime.utcnow()
    )
    db_session.add(legacy_code)
    db_session.commit()
    return legacy_code

@pytest.fixture
def sample_migration(db_session, sample_legacy_code):
    """Create a sample migration record."""
    migration = LegacyMigration(
        legacy_code_id=sample_legacy_code.id,
        new_implementation="/path/to/new",
        steps=[
            {"type": "move", "source": "old.py", "target": "new.py"},
            {"type": "update", "file": "new.py", "changes": []}
        ],
        status="planned",
        created_at=datetime.utcnow()
    )
    db_session.add(migration)
    db_session.commit()
    return migration

@pytest.mark.asyncio
async def test_archive_legacy_code(legacy_service, test_code_dir, db_session):
    """Test archiving legacy code."""
    result = await legacy_service.archive_legacy_code(
        str(test_code_dir),
        "Test legacy code archive"
    )
    
    assert isinstance(result, LegacyCode)
    assert result.original_path == str(test_code_dir)
    assert result.description == "Test legacy code archive"
    assert Path(result.archive_path).exists()
    
    # Check that files were copied
    assert (Path(result.archive_path) / "test.py").exists()
    assert (Path(result.archive_path) / "config.json").exists()

@pytest.mark.asyncio
async def test_create_migration_plan(legacy_service, sample_legacy_code, db_session):
    """Test creating a migration plan."""
    steps = [
        {"type": "move", "source": "old.py", "target": "new.py"},
        {"type": "update", "file": "new.py", "changes": []}
    ]
    
    result = await legacy_service.create_migration_plan(
        sample_legacy_code.id,
        "/path/to/new",
        steps
    )
    
    assert isinstance(result, LegacyMigration)
    assert result.legacy_code_id == sample_legacy_code.id
    assert result.new_implementation == "/path/to/new"
    assert result.steps == steps
    assert result.status == "planned"

@pytest.mark.asyncio
async def test_execute_migration(legacy_service, sample_migration, db_session):
    """Test executing a migration plan."""
    result = await legacy_service.execute_migration(sample_migration.id)
    
    assert result["status"] == "completed"
    assert len(result["results"]) == len(sample_migration.steps)
    
    # Check database record
    migration = db_session.query(LegacyMigration).get(sample_migration.id)
    assert migration.status == "completed"
    assert migration.completed_at is not None
    assert migration.results is not None

@pytest.mark.asyncio
async def test_rollback_migration(legacy_service, sample_migration, db_session):
    """Test rolling back a migration."""
    # First execute the migration
    await legacy_service.execute_migration(sample_migration.id)
    
    # Then roll it back
    result = await legacy_service.rollback_migration(sample_migration.id)
    
    assert result["status"] == "rolled_back"
    assert len(result["results"]) == len(sample_migration.steps)
    
    # Check database record
    migration = db_session.query(LegacyMigration).get(sample_migration.id)
    assert migration.status == "rolled_back"
    assert migration.rollback_at is not None
    assert migration.rollback_results is not None

@pytest.mark.asyncio
async def test_get_legacy_code_status(
    legacy_service,
    sample_legacy_code,
    sample_migration,
    db_session
):
    """Test getting legacy code status."""
    result = await legacy_service.get_legacy_code_status()
    
    assert result["total_legacy_codes"] == 1
    assert result["total_migrations"] == 1
    assert result["migrations_by_status"]["planned"] == 1
    assert len(result["latest_activities"]) == 1
    assert result["latest_activities"][0]["id"] == sample_migration.id

@pytest.mark.asyncio
async def test_error_handling(legacy_service):
    """Test error handling in legacy code operations."""
    with pytest.raises(ValueError):
        await legacy_service.create_migration_plan(999, "/path/to/new", [])
    
    with pytest.raises(ValueError):
        await legacy_service.execute_migration(999)
    
    with pytest.raises(ValueError):
        await legacy_service.rollback_migration(999) 