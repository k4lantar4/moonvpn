"""
CLI script for database management operations.
"""

import asyncio
import click
import logging
from pathlib import Path
from core.database.connection import DatabaseManager
from core.database.migrations import DatabaseMigrator

logger = logging.getLogger(__name__)

@click.group()
def db():
    """Database management commands."""
    pass

@db.command()
@click.option('--force', is_flag=True, help='Force initialization even if schema exists')
def init(force):
    """Initialize the database schema."""
    async def _init():
        db_manager = DatabaseManager()
        migrator = DatabaseMigrator(db_manager)
        
        if force or not await migrator.check_schema():
            success = await migrator.init_db()
            if success:
                click.echo("Database schema initialized successfully")
            else:
                click.echo("Failed to initialize database schema", err=True)
        else:
            click.echo("Database schema already exists")
    
    asyncio.run(_init())

@db.command()
def drop():
    """Drop all tables in the database."""
    async def _drop():
        db_manager = DatabaseManager()
        migrator = DatabaseMigrator(db_manager)
        
        if click.confirm('Are you sure you want to drop all tables?'):
            success = await migrator.drop_db()
            if success:
                click.echo("Database schema dropped successfully")
            else:
                click.echo("Failed to drop database schema", err=True)
    
    asyncio.run(_drop())

@db.command()
def check():
    """Check if the database schema is up to date."""
    async def _check():
        db_manager = DatabaseManager()
        migrator = DatabaseMigrator(db_manager)
        
        success = await migrator.check_schema()
        if success:
            click.echo("Database schema is up to date")
        else:
            click.echo("Database schema needs to be initialized", err=True)
    
    asyncio.run(_check())

@db.command()
@click.argument('backup_file', type=click.Path())
def backup(backup_file):
    """Backup the current database schema."""
    async def _backup():
        db_manager = DatabaseManager()
        migrator = DatabaseMigrator(db_manager)
        
        success = await migrator.backup_schema(backup_file)
        if success:
            click.echo(f"Database schema backed up to {backup_file}")
        else:
            click.echo("Failed to backup database schema", err=True)
    
    asyncio.run(_backup())

@db.command()
@click.argument('backup_file', type=click.Path(exists=True))
def restore(backup_file):
    """Restore the database schema from a backup file."""
    async def _restore():
        db_manager = DatabaseManager()
        migrator = DatabaseMigrator(db_manager)
        
        if click.confirm('Are you sure you want to restore the database schema?'):
            success = await migrator.restore_schema(backup_file)
            if success:
                click.echo(f"Database schema restored from {backup_file}")
            else:
                click.echo("Failed to restore database schema", err=True)
    
    asyncio.run(_restore())

@db.command()
def status():
    """Show database connection status."""
    async def _status():
        db_manager = DatabaseManager()
        try:
            is_connected = await db_manager.check_connection()
            if is_connected:
                click.echo("Database connection is active")
            else:
                click.echo("Database connection failed", err=True)
        except Exception as e:
            click.echo(f"Error checking database connection: {e}", err=True)
    
    asyncio.run(_status())

if __name__ == '__main__':
    db() 