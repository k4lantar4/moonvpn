"""
This module configures Alembic environment for database migrations.
"""

import os
import sys
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine # Import async engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# Commented out as alembic.ini might not have logging configured
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# Add project root to sys.path to find models
# Assuming env.py is in migrations directory, one level down from root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# --- Import settings and Base ---
# try:
#     from core.config import settings # Import your project settings
#     from core.database.models import Base # Import your Base model
#     # Import all models to ensure they are registered with Base.metadata
#     import core.database.models # noqa
#     from core.exceptions import ConfigurationError # Import ConfigurationError
# except ImportError as e:
#     sys.stderr.write(f"Error importing core modules: {e}\n")
#     sys.exit(1)

# --- Simpler Import for Models ---
try:
    # Assume models are accessible via Base.metadata after importing Base
    from core.database.models import Base # Import your Base model
    # Ensure models are registered (important for autogenerate if used later)
    import core.database.models # noqa 
except ImportError as e:
    sys.stderr.write(f"Error importing Base model: {e}\n")
    sys.exit(1)

# The target metadata for 'autogenerate' support
target_metadata = Base.metadata

# --- Database URL Configuration ---
# Get DATABASE_URL directly from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # raise ConfigurationError("DATABASE_URL not found in environment variables.")
    # Use simple ValueError if ConfigurationError isn't available
    raise ValueError("DATABASE_URL not found in environment variables.")

# Set the sqlalchemy.url in the Alembic config (used by offline mode and engine creation)
config.set_main_option('sqlalchemy.url', DATABASE_URL)


# --- Migration Functions ---

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    Generates SQL scripts without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Helper function to run migrations within a context."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"), # Use the URL from config
        poolclass=pool.NullPool, # Use NullPool for migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations) # Run sync function in async context

    await connectable.dispose() # Dispose the engine


# --- Main Execution Logic ---

if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run the async online migration function
    asyncio.run(run_migrations_online())
