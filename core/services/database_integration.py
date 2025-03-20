"""
Database Integration Service for managing database-to-database communication.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

from ..database.models.enhancements.health import SystemHealth, HealthStatus
from ..core.config import settings

logger = logging.getLogger(__name__)

class DatabaseIntegrationService:
    """Service for managing database-to-database integrations."""

    def __init__(self, db: Session):
        self.db = db
        self.databases: Dict[str, Any] = {}
        self.db_status: Dict[str, bool] = {}
        self.connection_pools: Dict[str, QueuePool] = {}
        self.retry_config = {
            "max_retries": 3,
            "retry_delay": 1,
            "max_delay": 10
        }

    async def initialize(self):
        """Initialize all database integrations."""
        try:
            # Initialize core databases
            await self._initialize_main_database()
            await self._initialize_backup_database()
            await self._initialize_analytics_database()
            await self._initialize_logging_database()
            
            logger.info("All database integrations initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database integrations: {str(e)}")
            raise

    async def _initialize_main_database(self):
        """Initialize main database integration."""
        try:
            engine = create_engine(
                settings.MAIN_DATABASE_URL,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
            self.connection_pools['main'] = engine
            self.db_status['main'] = True
            logger.info("Main database integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize main database: {str(e)}")
            self.db_status['main'] = False
            raise

    async def _initialize_backup_database(self):
        """Initialize backup database integration."""
        try:
            engine = create_engine(
                settings.BACKUP_DATABASE_URL,
                poolclass=QueuePool,
                pool_size=3,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800
            )
            self.connection_pools['backup'] = engine
            self.db_status['backup'] = True
            logger.info("Backup database integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize backup database: {str(e)}")
            self.db_status['backup'] = False
            raise

    async def _initialize_analytics_database(self):
        """Initialize analytics database integration."""
        try:
            engine = create_engine(
                settings.ANALYTICS_DATABASE_URL,
                poolclass=QueuePool,
                pool_size=3,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800
            )
            self.connection_pools['analytics'] = engine
            self.db_status['analytics'] = True
            logger.info("Analytics database integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {str(e)}")
            self.db_status['analytics'] = False
            raise

    async def _initialize_logging_database(self):
        """Initialize logging database integration."""
        try:
            engine = create_engine(
                settings.LOGGING_DATABASE_URL,
                poolclass=QueuePool,
                pool_size=3,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800
            )
            self.connection_pools['logging'] = engine
            self.db_status['logging'] = True
            logger.info("Logging database integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize logging database: {str(e)}")
            self.db_status['logging'] = False
            raise

    async def execute_query(self, database: str, query: str, 
                          params: Optional[Dict[str, Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """Execute a query on a specific database."""
        if database not in self.connection_pools:
            logger.error(f"Database {database} not found")
            return None
            
        try:
            retry_count = 0
            while retry_count < self.retry_config["max_retries"]:
                try:
                    with self.connection_pools[database].connect() as connection:
                        result = connection.execute(text(query), params or {})
                        return [dict(row) for row in result]
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.retry_config["max_retries"]:
                        raise
                    delay = min(self.retry_config["retry_delay"] * (2 ** retry_count), 
                              self.retry_config["max_delay"])
                    await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Failed to execute query on database {database}: {str(e)}")
            return None

    async def backup_database(self, source_db: str, target_db: str) -> bool:
        """Backup data from one database to another."""
        if source_db not in self.connection_pools or target_db not in self.connection_pools:
            logger.error(f"Source or target database not found")
            return False
            
        try:
            # Get list of tables from source database
            tables = await self.execute_query(source_db, "SELECT table_name FROM information_schema.tables")
            if not tables:
                return False
                
            # Backup each table
            for table in tables:
                table_name = table['table_name']
                # Get data from source
                data = await self.execute_query(source_db, f"SELECT * FROM {table_name}")
                if data:
                    # Insert into target
                    for row in data:
                        columns = ', '.join(row.keys())
                        values = ', '.join([f":{k}" for k in row.keys()])
                        query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
                        await self.execute_query(target_db, query, row)
                        
            return True
        except Exception as e:
            logger.error(f"Failed to backup database from {source_db} to {target_db}: {str(e)}")
            return False

    async def sync_databases(self, source_db: str, target_db: str) -> bool:
        """Synchronize data between two databases."""
        if source_db not in self.connection_pools or target_db not in self.connection_pools:
            logger.error(f"Source or target database not found")
            return False
            
        try:
            # Get list of tables from source database
            tables = await self.execute_query(source_db, "SELECT table_name FROM information_schema.tables")
            if not tables:
                return False
                
            # Sync each table
            for table in tables:
                table_name = table['table_name']
                # Get last sync timestamp
                last_sync = await self.execute_query(target_db, 
                    f"SELECT MAX(updated_at) as last_sync FROM {table_name}")
                last_sync_time = last_sync[0]['last_sync'] if last_sync else None
                
                # Get updated records from source
                if last_sync_time:
                    query = f"SELECT * FROM {table_name} WHERE updated_at > :last_sync"
                else:
                    query = f"SELECT * FROM {table_name}"
                    
                data = await self.execute_query(source_db, query, 
                    {"last_sync": last_sync_time} if last_sync_time else {})
                
                # Update target database
                if data:
                    for row in data:
                        columns = ', '.join([f"{k} = :{k}" for k in row.keys() if k != 'id'])
                        query = f"UPDATE {table_name} SET {columns} WHERE id = :id"
                        await self.execute_query(target_db, query, row)
                        
            return True
        except Exception as e:
            logger.error(f"Failed to sync databases {source_db} and {target_db}: {str(e)}")
            return False

    async def get_database_status(self, database: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific database."""
        if database not in self.connection_pools:
            return None
            
        try:
            # Check connection
            with self.connection_pools[database].connect() as connection:
                connection.execute(text("SELECT 1"))
                
            return {
                "database": database,
                "status": "healthy",
                "is_active": self.db_status.get(database, False),
                "last_check": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get status for database {database}: {str(e)}")
            return None

    async def get_all_database_status(self) -> List[Dict[str, Any]]:
        """Get the status of all databases."""
        status_list = []
        for database in self.connection_pools:
            status = await self.get_database_status(database)
            if status:
                status_list.append(status)
        return status_list

    async def shutdown(self):
        """Shutdown all database integrations."""
        for database in self.connection_pools:
            try:
                self.connection_pools[database].dispose()
            except Exception as e:
                logger.error(f"Failed to shutdown database {database}: {str(e)}")
        self.db_status.clear() 