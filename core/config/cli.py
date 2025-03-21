"""
Command-line interface for database management.
"""

import os
import click
import logging
from typing import Optional
from core.database.connection import DatabaseManager
from core.database.migrations import MigrationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), 'database', 'migrations')

def get_db_manager() -> DatabaseManager:
    """Get database manager instance."""
    db = DatabaseManager()
    db.initialize(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'moonvpn'),
        username=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    return db

def get_migration_manager(db: DatabaseManager) -> MigrationManager:
    """Get migration manager instance."""
    return MigrationManager(db, DEFAULT_MIGRATIONS_DIR)

@click.group()
def cli():
    """MoonVPN database management CLI."""
    pass

@cli.group()
def db():
    """Database operations."""
    pass

@db.command()
@click.option('--name', prompt='Migration name', help='Name of the migration')
def create_migration(name: str):
    """Create a new migration file."""
    try:
        db_manager = get_db_manager()
        migration_manager = get_migration_manager(db_manager)
        
        filepath = migration_manager.create_migration(name)
        click.echo(f"Created migration file: {filepath}")
        
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise click.ClickException(str(e))
    finally:
        db_manager.close()

@db.command()
@click.option('--target', help='Target version to migrate to')
def migrate(target: Optional[str]):
    """Apply pending migrations."""
    try:
        db_manager = get_db_manager()
        migration_manager = get_migration_manager(db_manager)
        
        applied = migration_manager.apply_migrations(target)
        if applied:
            click.echo(f"Applied migrations: {', '.join(applied)}")
        else:
            click.echo("No migrations to apply")
            
    except Exception as e:
        logger.error(f"Failed to apply migrations: {e}")
        raise click.ClickException(str(e))
    finally:
        db_manager.close()

@db.command()
@click.option('--target', help='Target version to rollback to')
def rollback(target: Optional[str]):
    """Rollback migrations."""
    try:
        db_manager = get_db_manager()
        migration_manager = get_migration_manager(db_manager)
        
        rolled_back = migration_manager.rollback_migrations(target)
        if rolled_back:
            click.echo(f"Rolled back migrations: {', '.join(rolled_back)}")
        else:
            click.echo("No migrations to roll back")
            
    except Exception as e:
        logger.error(f"Failed to rollback migrations: {e}")
        raise click.ClickException(str(e))
    finally:
        db_manager.close()

@db.command()
def status():
    """Show migration status."""
    try:
        db_manager = get_db_manager()
        migration_manager = get_migration_manager(db_manager)
        
        migrations = migration_manager.get_migrations()
        
        if not migrations:
            click.echo("No migrations found")
            return
        
        click.echo("\nMigration Status:")
        click.echo("-" * 80)
        click.echo(f"{'Version':<20} {'Name':<30} {'Status':<10} {'Applied At'}")
        click.echo("-" * 80)
        
        for migration in migrations:
            status = '✓' if migration['status'] == 'applied' else ' '
            modified = '*' if migration['is_modified'] else ' '
            applied_at = migration['applied_at'].strftime('%Y-%m-%d %H:%M:%S') if migration['applied_at'] else ''
            
            click.echo(
                f"{migration['version']:<20} "
                f"{migration['name']:<30} "
                f"[{status}]{modified:<8} "
                f"{applied_at}"
            )
            
        click.echo("-" * 80)
        click.echo("Legend: [✓] Applied  [ ] Pending  [*] Modified\n")
            
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        raise click.ClickException(str(e))
    finally:
        db_manager.close()

@db.command()
def repair():
    """Repair modified migrations."""
    try:
        db_manager = get_db_manager()
        migration_manager = get_migration_manager(db_manager)
        
        repaired = migration_manager.repair_migrations()
        if repaired:
            click.echo(f"Repaired migrations: {', '.join(repaired)}")
        else:
            click.echo("No migrations to repair")
            
    except Exception as e:
        logger.error(f"Failed to repair migrations: {e}")
        raise click.ClickException(str(e))
    finally:
        db_manager.close()

@db.command()
@click.option('--table', help='Table to analyze')
def vacuum(table: Optional[str]):
    """Run VACUUM ANALYZE on database."""
    try:
        db_manager = get_db_manager()
        db_manager.vacuum_analyze(table)
        click.echo(f"Successfully ran VACUUM ANALYZE on {table or 'all tables'}")
            
    except Exception as e:
        logger.error(f"Failed to run VACUUM ANALYZE: {e}")
        raise click.ClickException(str(e))
    finally:
        db_manager.close()

@db.command()
def info():
    """Show database information."""
    try:
        db_manager = get_db_manager()
        
        # Get table sizes
        sizes = db_manager.get_table_sizes()
        
        click.echo("\nDatabase Tables:")
        click.echo("-" * 80)
        click.echo(f"{'Table':<30} {'Total Size':<15} {'Data Size':<15} {'Index Size':<15}")
        click.echo("-" * 80)
        
        for table, info in sizes.items():
            total = f"{info['total_size'] / 1024 / 1024:.2f} MB"
            data = f"{info['data_size'] / 1024 / 1024:.2f} MB"
            index = f"{info['index_size'] / 1024 / 1024:.2f} MB"
            
            click.echo(
                f"{table:<30} "
                f"{total:<15} "
                f"{data:<15} "
                f"{index:<15}"
            )
            
        click.echo("-" * 80)
        
        # Get active connections
        connections = db_manager.get_active_connections()
        
        if connections:
            click.echo("\nActive Connections:")
            click.echo("-" * 80)
            for conn in connections:
                click.echo(
                    f"PID: {conn['pid']}, "
                    f"User: {conn['usename']}, "
                    f"State: {conn['state']}, "
                    f"Query: {conn['query'][:50]}..."
                )
            click.echo("-" * 80)
            
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        raise click.ClickException(str(e))
    finally:
        db_manager.close()

if __name__ == '__main__':
    cli() 