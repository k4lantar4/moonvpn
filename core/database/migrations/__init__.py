"""Database migration manager."""
from typing import Optional
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine

class MigrationManager:
    """Manages database migrations using Alembic."""
    
    def __init__(self, engine: AsyncEngine, alembic_cfg: Config):
        """Initialize the migration manager.
        
        Args:
            engine: The SQLAlchemy async engine
            alembic_cfg: The Alembic configuration
        """
        self.engine = engine
        self.alembic_cfg = alembic_cfg
    
    async def create_migration(self, message: str) -> None:
        """Create a new migration.
        
        Args:
            message: The migration message
        """
        command.revision(self.alembic_cfg, message=message, autogenerate=True)
    
    async def upgrade(self, revision: Optional[str] = None) -> None:
        """Upgrade the database to a specific revision.
        
        Args:
            revision: The revision to upgrade to. If None, upgrade to latest.
        """
        if revision:
            command.upgrade(self.alembic_cfg, revision)
        else:
            command.upgrade(self.alembic_cfg, "head")
    
    async def downgrade(self, revision: Optional[str] = None) -> None:
        """Downgrade the database to a specific revision.
        
        Args:
            revision: The revision to downgrade to. If None, downgrade one step.
        """
        if revision:
            command.downgrade(self.alembic_cfg, revision)
        else:
            command.downgrade(self.alembic_cfg, "-1")
    
    async def current_revision(self) -> str:
        """Get the current database revision.
        
        Returns:
            The current revision identifier
        """
        return command.current(self.alembic_cfg)
    
    async def history(self) -> list:
        """Get the migration history.
        
        Returns:
            List of migration revisions
        """
        return command.history(self.alembic_cfg)

