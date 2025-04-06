import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add project root to sys.path to find models
# Assuming env.py is in migrations directory, one level down from root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

# Import Base from your models file
from api.models import Base

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata # Use the Base from your models

# other values from the config, defined by the needs of env.py,
# can be acquired:-
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use environment variables for connection URL (already configured in alembic.ini)
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    # --- Corrected way to get URL from environment for online mode ---
    from dotenv import load_dotenv
    load_dotenv() # Load .env file

    db_url = os.getenv('DATABASE_URL') # Try DATABASE_URL first
    if not db_url:
        # Construct from individual variables if DATABASE_URL is not set
        user = os.getenv('MYSQL_USER')
        password = os.getenv('MYSQL_PASSWORD')
        host = os.getenv('MYSQL_HOST')
        port = os.getenv('MYSQL_PORT')
        db_name = os.getenv('MYSQL_DATABASE')
        if not all([user, password, host, port, db_name]):
            raise ValueError("Database connection environment variables not set properly.")
        db_url = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db_name}"

    engine_config = config.get_section(config.config_ini_section, {})
    engine_config['sqlalchemy.url'] = db_url

    connectable = engine_from_config(
        engine_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # -------------------------------------------------------------------

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
