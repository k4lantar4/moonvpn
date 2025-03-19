"""
Database migration manager for PostgreSQL.
"""

import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import text
from .connection import DatabaseManager

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db_manager: DatabaseManager, migrations_dir: str):
        """Initialize migration manager."""
        self.db = db_manager
        self.migrations_dir = migrations_dir
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Ensure migrations table exists."""
        query = """
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            checksum VARCHAR(64) NOT NULL
        );
        """
        try:
            with self.db.get_session() as session:
                session.execute(text(query))
                session.commit()
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
    
    def create_migration(self, name: str) -> str:
        """Create a new migration file."""
        try:
            # Create migrations directory if it doesn't exist
            os.makedirs(self.migrations_dir, exist_ok=True)
            
            # Generate version and filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            version = f"V{timestamp}"
            filename = f"{version}__{name.replace(' ', '_').lower()}.sql"
            filepath = os.path.join(self.migrations_dir, filename)
            
            # Create migration file template
            template = f"""-- Migration: {name}
-- Version: {version}
-- Created: {datetime.now().isoformat()}

-- Write your migration SQL here
-- Use -- @up and -- @down to separate upgrade and downgrade scripts

-- @up
-- Add upgrade SQL here


-- @down
-- Add downgrade SQL here

"""
            
            # Write template to file
            with open(filepath, 'w') as f:
                f.write(template)
            
            logger.info(f"Created migration file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise
    
    def get_migrations(self) -> List[Dict]:
        """Get list of all migrations and their status."""
        try:
            # Get applied migrations from database
            with self.db.get_session() as session:
                result = session.execute(text(
                    "SELECT version, name, applied_at, checksum FROM migrations ORDER BY version"
                ))
                applied = {row.version: row for row in result}
            
            # Get all migration files
            migrations = []
            for filename in sorted(os.listdir(self.migrations_dir)):
                if not filename.endswith('.sql'):
                    continue
                
                version = filename.split('__')[0]
                name = filename.split('__')[1].replace('.sql', '').replace('_', ' ')
                filepath = os.path.join(self.migrations_dir, filename)
                checksum = self._calculate_checksum(filepath)
                
                migration = {
                    'version': version,
                    'name': name,
                    'filename': filename,
                    'status': 'pending',
                    'applied_at': None,
                    'checksum': checksum,
                    'is_modified': False
                }
                
                # Check if migration was applied
                if version in applied:
                    migration['status'] = 'applied'
                    migration['applied_at'] = applied[version].applied_at
                    migration['is_modified'] = checksum != applied[version].checksum
                
                migrations.append(migration)
            
            return migrations
            
        except Exception as e:
            logger.error(f"Failed to get migrations: {e}")
            raise
    
    def apply_migrations(self, target_version: Optional[str] = None) -> List[str]:
        """Apply pending migrations up to target version."""
        try:
            applied = []
            migrations = self.get_migrations()
            
            # Filter migrations to apply
            to_apply = [
                m for m in migrations
                if m['status'] == 'pending' and
                (not target_version or m['version'] <= target_version)
            ]
            
            # Apply each migration in a transaction
            for migration in to_apply:
                try:
                    filepath = os.path.join(self.migrations_dir, migration['filename'])
                    sql = self._get_migration_sql(filepath, 'up')
                    
                    with self.db.get_session() as session:
                        # Apply migration
                        session.execute(text(sql))
                        
                        # Record migration
                        session.execute(
                            text("""
                            INSERT INTO migrations (version, name, checksum)
                            VALUES (:version, :name, :checksum)
                            """),
                            {
                                'version': migration['version'],
                                'name': migration['name'],
                                'checksum': migration['checksum']
                            }
                        )
                        
                        session.commit()
                        
                    applied.append(migration['version'])
                    logger.info(f"Applied migration {migration['version']}: {migration['name']}")
                    
                except Exception as e:
                    logger.error(f"Failed to apply migration {migration['version']}: {e}")
                    raise
            
            return applied
            
        except Exception as e:
            logger.error(f"Failed to apply migrations: {e}")
            raise
    
    def rollback_migrations(self, target_version: Optional[str] = None) -> List[str]:
        """Rollback migrations down to target version."""
        try:
            rolled_back = []
            migrations = self.get_migrations()
            
            # Filter migrations to rollback
            to_rollback = [
                m for m in reversed(migrations)
                if m['status'] == 'applied' and
                (not target_version or m['version'] > target_version)
            ]
            
            # Rollback each migration in a transaction
            for migration in to_rollback:
                try:
                    filepath = os.path.join(self.migrations_dir, migration['filename'])
                    sql = self._get_migration_sql(filepath, 'down')
                    
                    with self.db.get_session() as session:
                        # Apply rollback
                        session.execute(text(sql))
                        
                        # Remove migration record
                        session.execute(
                            text("DELETE FROM migrations WHERE version = :version"),
                            {'version': migration['version']}
                        )
                        
                        session.commit()
                        
                    rolled_back.append(migration['version'])
                    logger.info(f"Rolled back migration {migration['version']}: {migration['name']}")
                    
                except Exception as e:
                    logger.error(f"Failed to rollback migration {migration['version']}: {e}")
                    raise
            
            return rolled_back
            
        except Exception as e:
            logger.error(f"Failed to rollback migrations: {e}")
            raise
    
    def repair_migrations(self) -> List[str]:
        """Repair migration checksums for modified files."""
        try:
            repaired = []
            migrations = self.get_migrations()
            
            # Filter modified migrations
            modified = [m for m in migrations if m['is_modified']]
            
            # Update checksums
            for migration in modified:
                try:
                    with self.db.get_session() as session:
                        session.execute(
                            text("""
                            UPDATE migrations
                            SET checksum = :checksum
                            WHERE version = :version
                            """),
                            {
                                'version': migration['version'],
                                'checksum': migration['checksum']
                            }
                        )
                        session.commit()
                        
                    repaired.append(migration['version'])
                    logger.info(f"Repaired migration {migration['version']}: {migration['name']}")
                    
                except Exception as e:
                    logger.error(f"Failed to repair migration {migration['version']}: {e}")
                    raise
            
            return repaired
            
        except Exception as e:
            logger.error(f"Failed to repair migrations: {e}")
            raise
    
    def _get_migration_sql(self, filepath: str, direction: str) -> str:
        """Extract upgrade or downgrade SQL from migration file."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Split content by markers
            parts = content.split(f"-- @{direction}")
            if len(parts) < 2:
                raise ValueError(f"Missing -- @{direction} marker in {filepath}")
            
            # Get SQL between markers or until end of file
            sql = parts[1]
            next_marker = f"-- @{'down' if direction == 'up' else 'up'}"
            if next_marker in sql:
                sql = sql.split(next_marker)[0]
            
            return sql.strip()
            
        except Exception as e:
            logger.error(f"Failed to get migration SQL from {filepath}: {e}")
            raise
    
    def _calculate_checksum(self, filepath: str) -> str:
        """Calculate checksum of migration file."""
        import hashlib
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {filepath}: {e}")
            raise 