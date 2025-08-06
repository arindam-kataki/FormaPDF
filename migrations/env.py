# a_migrations_env.py
"""
Alembic Environment Configuration
This file should be placed in migrations/env.py
"""

from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add the project root to Python path so we can import our models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import your models here
from a_database_models import Base, DatabaseConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def get_database_url():
    """
    Get database URL from environment or config
    Priority:
    1. DATABASE_URL environment variable
    2. Individual environment variables (DB_TYPE, DB_HOST, etc.)
    3. Alembic config file
    """

    # Check for full DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url

    # Check for individual environment variables
    db_type = os.getenv('DB_TYPE', 'postgresql')

    if db_type == 'postgresql':
        db_config = DatabaseConfig(
            db_type='postgresql',
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'synaiptic'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        return db_config.get_database_url()

    elif db_type == 'sqlite':
        db_path = os.getenv('DB_PATH', 'data/synaiptic.db')
        db_config = DatabaseConfig(db_type='sqlite', path=db_path)
        return db_config.get_database_url()

    # Fallback to config file
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
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

    # Override the sqlalchemy.url in config with our dynamic URL
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Include object name in constraint names for better debugging
            render_as_batch=True,
            # Compare types to detect column type changes
            compare_type=True,
            # Compare server defaults
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()