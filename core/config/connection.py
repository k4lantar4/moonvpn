"""
Database connection manager for PostgreSQL.
"""

import logging
from typing import Optional, Dict, List, Any, Generator
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import select
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from datetime import datetime
import psycopg2
import os
import json

from .config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database manager."""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.engine = None
            self.SessionLocal = None
            self.metadata = MetaData()
    
    def initialize(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800
    ) -> 'DatabaseManager':
        """Initialize database connection."""
        try:
            # Create connection URL
            self.connection_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            
            # Create engine with connection pooling
            self.engine = create_engine(
                self.connection_url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                echo=False  # Set to True for SQL query logging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            
            logger.info("Successfully connected to PostgreSQL database")
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            if self.engine:
                self.engine.dispose()
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
            logger.info("Closed database connection")
    
    def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def get_table_sizes(self) -> Dict[str, Dict[str, int]]:
        """Get size information for all tables."""
        query = """
        SELECT
            relname as table_name,
            pg_total_relation_size(relid) as total_size,
            pg_table_size(relid) as data_size,
            pg_indexes_size(relid) as index_size,
            pg_total_relation_size(relid) - pg_table_size(relid) as external_size
        FROM pg_catalog.pg_statio_user_tables
        ORDER BY pg_total_relation_size(relid) DESC;
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query))
                return {
                    row.table_name: {
                        'total_size': row.total_size,
                        'data_size': row.data_size,
                        'index_size': row.index_size,
                        'external_size': row.external_size
                    }
                    for row in result
                }
        except Exception as e:
            logger.error(f"Failed to get table sizes: {e}")
            raise
    
    def get_slow_queries(self, min_duration: float = 1.0) -> List[Dict]:
        """Get slow query information."""
        query = """
        SELECT
            query,
            calls,
            total_time,
            mean_time,
            rows
        FROM pg_stat_statements
        WHERE mean_time > :min_duration
        ORDER BY mean_time DESC
        LIMIT 100;
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query), {'min_duration': min_duration})
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            raise
    
    def vacuum_analyze(self, table_name: Optional[str] = None):
        """Run VACUUM ANALYZE on specified table or entire database."""
        try:
            # Need to run outside transaction block
            connection = self.engine.raw_connection()
            try:
                connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                cursor = connection.cursor()
                if table_name:
                    cursor.execute(f"VACUUM ANALYZE {table_name};")
                else:
                    cursor.execute("VACUUM ANALYZE;")
            finally:
                connection.close()
            logger.info(f"Successfully ran VACUUM ANALYZE on {table_name or 'all tables'}")
        except Exception as e:
            logger.error(f"Failed to run VACUUM ANALYZE: {e}")
            raise
    
    def create_backup(self, backup_dir: str) -> str:
        """Create database backup using pg_dump."""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")
            
            # Get connection info
            url = self.engine.url
            env = os.environ.copy()
            env['PGPASSWORD'] = url.password
            
            # Run pg_dump
            command = [
                'pg_dump',
                '-h', url.host,
                '-p', str(url.port or 5432),
                '-U', url.username,
                '-d', url.database,
                '-F', 'c',  # Custom format
                '-f', backup_file
            ]
            
            import subprocess
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Backup failed: {result.stderr}")
            
            logger.info(f"Successfully created backup at {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore database from backup using pg_restore."""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Get connection info
            url = self.engine.url
            env = os.environ.copy()
            env['PGPASSWORD'] = url.password
            
            # Run pg_restore
            command = [
                'pg_restore',
                '-h', url.host,
                '-p', str(url.port or 5432),
                '-U', url.username,
                '-d', url.database,
                '-c',  # Clean (drop) database objects before recreating
                '-F', 'c',  # Custom format
                backup_file
            ]
            
            import subprocess
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Restore failed: {result.stderr}")
            
            logger.info(f"Successfully restored from backup {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get detailed information about a specific table."""
        try:
            inspector = inspect(self.engine)
            
            return {
                'columns': inspector.get_columns(table_name),
                'indexes': inspector.get_indexes(table_name),
                'foreign_keys': inspector.get_foreign_keys(table_name),
                'primary_key': inspector.get_pk_constraint(table_name),
                'schema': inspector.get_schema_names()
            }
        except Exception as e:
            logger.error(f"Failed to get table info for {table_name}: {e}")
            raise
    
    def analyze_table_bloat(self) -> Dict[str, Dict]:
        """Analyze table and index bloat."""
        query = """
        WITH constants AS (
            SELECT current_setting('block_size')::numeric AS bs,
                   23 AS hdr,
                   4 AS ma
        ),
        bloat_info AS (
            SELECT
                schemaname, tablename, bs,
                reltuples::numeric as tups,
                relpages::numeric as pages,
                relam,
                (toast.relpages + toast.reltuples * 4)::numeric as toast_pages
            FROM pg_class c
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
                LEFT JOIN pg_am am ON am.oid = c.relam
                LEFT JOIN pg_class toast ON c.reltoastrelid = toast.oid
            WHERE relkind = 'r'
        )
        SELECT
            schemaname || '.' || tablename as full_table_name,
            pg_size_pretty(bs*(case when pages>0 then pages else 0 end)::bigint) as size,
            pg_size_pretty(bs*(case when pages-estimated_pages>0 then pages-estimated_pages else 0 end)::bigint) as bloat,
            case when pages>0 and pages-estimated_pages>0
                then round((100*(pages-estimated_pages)::numeric/pages)::numeric,2)
                else 0
            end as bloat_percentage
        FROM (
            SELECT bs, schemaname, tablename, pages,
                ceil((reltuples*6 + (hdr + ma - (case when hdr%ma=0 then ma else hdr%ma end)))::numeric / (bs-20::numeric)) + coalesce(toast_pages,0) as estimated_pages
            FROM constants, bloat_info
        ) bloat_ratios
        ORDER BY bloat_percentage DESC;
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query))
                return {
                    row.full_table_name: {
                        'size': row.size,
                        'bloat': row.bloat,
                        'bloat_percentage': row.bloat_percentage
                    }
                    for row in result
                }
        except Exception as e:
            logger.error(f"Failed to analyze table bloat: {e}")
            raise
    
    def get_active_connections(self) -> List[Dict]:
        """Get information about active database connections."""
        query = """
        SELECT 
            pid,
            usename,
            application_name,
            client_addr,
            backend_start,
            state,
            query
        FROM pg_stat_activity
        WHERE state != 'idle'
        AND pid != pg_backend_pid();
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query))
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Failed to get active connections: {e}")
            raise
    
    def kill_connection(self, pid: int) -> bool:
        """Kill a specific database connection."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT pg_terminate_backend(:pid)"), {'pid': pid})
                return True
        except Exception as e:
            logger.error(f"Failed to kill connection {pid}: {e}")
            return False

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
            return False 