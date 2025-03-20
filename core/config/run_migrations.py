#!/usr/bin/env python3
"""
Script to run database migrations.

This script handles:
1. Running SQL migrations in order
2. Running Python migrations
3. Handling errors and rollbacks
4. Logging migration status
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'moonvpn'),
    'user': os.getenv('DB_USER', 'moonvpn'),
    'password': os.getenv('DB_PASSWORD', 'moonvpn')
}

@contextmanager
def get_db_connection():
    """Get a database connection with proper error handling."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def check_database_exists() -> bool:
    """Check if the database exists."""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['database'],))
            exists = cur.fetchone() is not None
        
        conn.close()
        return exists
    except psycopg2.Error as e:
        logger.error(f"Error checking database existence: {e}")
        raise

def create_database() -> None:
    """Create the database if it doesn't exist."""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            logger.info(f"Created database: {DB_CONFIG['database']}")
        
        conn.close()
    except psycopg2.Error as e:
        logger.error(f"Error creating database: {e}")
        raise

def get_migration_files() -> List[Path]:
    """Get list of migration files in order."""
    migrations_dir = Path(__file__).parent.parent.parent.parent / 'core' / 'database' / 'migrations'
    sql_files = sorted(migrations_dir.glob('V*.sql'))
    py_files = sorted(migrations_dir.glob('v*.py'))
    return sql_files + py_files

def run_sql_migration(cur, migration_file: Path) -> None:
    """Run a SQL migration file."""
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
        cur.execute(sql)
        logger.info(f"Applied SQL migration: {migration_file.name}")
    except Exception as e:
        logger.error(f"Error running SQL migration {migration_file.name}: {e}")
        raise

def run_python_migration(migration_file: Path) -> None:
    """Run a Python migration file."""
    try:
        # Add migrations directory to Python path
        migrations_dir = migration_file.parent
        if str(migrations_dir) not in sys.path:
            sys.path.insert(0, str(migrations_dir))
        
        # Import and run migration
        module_name = migration_file.stem
        module = __import__(module_name)
        if hasattr(module, 'run_migration'):
            module.run_migration()
            logger.info(f"Applied Python migration: {migration_file.name}")
        else:
            logger.warning(f"No run_migration function found in {migration_file.name}")
    except Exception as e:
        logger.error(f"Error running Python migration {migration_file.name}: {e}")
        raise

def main() -> None:
    """Main function to run migrations."""
    try:
        # Check if database exists
        if not check_database_exists():
            logger.info(f"Database {DB_CONFIG['database']} does not exist. Creating...")
            create_database()
        
        # Get migration files
        migration_files = get_migration_files()
        if not migration_files:
            logger.warning("No migration files found")
            return
        
        # Run migrations
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for migration_file in migration_files:
                    try:
                        if migration_file.suffix == '.sql':
                            run_sql_migration(cur, migration_file)
                        elif migration_file.suffix == '.py':
                            run_python_migration(migration_file)
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        logger.error(f"Migration failed: {e}")
                        raise
        
        logger.info("All migrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 