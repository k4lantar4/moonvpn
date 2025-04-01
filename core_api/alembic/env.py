import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the 'app' directory to the Python path to find modules
# Assuming env.py is in alembic/, and the app is in ../app
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_dir)

# Import your Base and all models needed for autogenerate
from app.db.base_class import Base # Import the actual Base class
# Import all your models here so Base knows about them
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.plan import Plan
from app.models.panel import Panel
from app.models.location import Location
from app.models.server import Server
from app.models.plan_category import PlanCategory
# Import association tables if they are defined separately
from app.models.associations import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Construct Database URI from individual environment variables
def get_db_uri():
    db_user = os.getenv("DB_USER", "moonvpn_user")
    db_password = os.getenv("DB_PASSWORD", "your_strong_password")
    db_host = os.getenv("DB_HOST", "db") # Default to service name 'db'
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "moonvpn_db")
    # Ensure port is valid
    try:
        int(db_port)
    except ValueError:
        raise ValueError(f"Invalid DB_PORT: {db_port}. Must be an integer.")
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

db_uri = get_db_uri()

# Set the sqlalchemy.url in the config object programmatically
config.set_main_option('sqlalchemy.url', db_uri)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=db_uri, # Use the obtained db_uri
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True # Added for better type comparison
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Use engine_from_config with the updated config
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Ensure the URL is explicitly passed if needed, though set_main_option should handle it
        # url=db_uri
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Add compare_type=True for better type comparison
            compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
