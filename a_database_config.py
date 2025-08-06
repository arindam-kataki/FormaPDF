# a_database_config.py
"""
Database configuration for PostgreSQL
Handles connection settings and database initialization
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """PostgreSQL configuration and connection management"""

    # Database type (postgresql or sqlite for development)
    DB_TYPE = os.getenv('DB_TYPE', 'postgresql')

    # PostgreSQL connection settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'synaiplic_research')
    DB_USER = os.getenv('DB_USER', 'synaiplic')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Connection pool settings
    POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
    MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))

    # Application settings
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def get_database_url(cls, include_password: bool = True) -> str:
        """
        Build database URL

        Args:
            include_password: Whether to include password in URL (False for logging)

        Returns:
            Database connection string
        """
        # Check for override URL first
        override_url = os.getenv('DATABASE_URL')
        if override_url:
            if not include_password and 'postgresql://' in override_url:
                # Mask password for logging
                parts = override_url.split('@')
                if len(parts) > 1:
                    user_pass = parts[0].split('://')[-1]
                    user = user_pass.split(':')[0] if ':' in user_pass else user_pass
                    return f"postgresql://{user}:***@{parts[1]}"
            return override_url

        # Build URL from components
        if cls.DB_TYPE == 'postgresql':
            password = cls.DB_PASSWORD if include_password else '***'
            return f"postgresql://{cls.DB_USER}:{password}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        elif cls.DB_TYPE == 'sqlite':
            # SQLite fallback for development
            db_path = Path.home() / '.synaiplic' / 'research.db'
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{db_path}"
        else:
            raise ValueError(f"Unsupported database type: {cls.DB_TYPE}")

    @classmethod
    def get_engine_config(cls) -> Dict[str, Any]:
        """
        Get SQLAlchemy engine configuration

        Returns:
            Dictionary of engine configuration options
        """
        config = {
            'echo': cls.DEBUG,  # Log SQL statements if in debug mode
            'pool_pre_ping': True,  # Verify connections before using
            'pool_recycle': 3600,  # Recycle connections after 1 hour
        }

        if cls.DB_TYPE == 'postgresql':
            config.update({
                'pool_size': cls.POOL_SIZE,
                'max_overflow': cls.MAX_OVERFLOW,
                'pool_timeout': cls.POOL_TIMEOUT,
                'connect_args': {
                    'connect_timeout': 10,
                    'application_name': 'SYNAIPLIC_Research_Platform'
                }
            })

        return config

    @classmethod
    def get_alembic_config(cls) -> Dict[str, Any]:
        """
        Get Alembic migration configuration

        Returns:
            Dictionary of Alembic configuration options
        """
        return {
            'script_location': 'migrations',
            'file_template': '%%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s',
            'timezone': 'UTC',
            'compare_type': True,
            'compare_server_default': True,
            'sqlalchemy.url': cls.get_database_url()
        }

    @classmethod
    def test_connection(cls) -> tuple[bool, str]:
        """
        Test database connection

        Returns:
            Tuple of (success, message)
        """
        from sqlalchemy import create_engine, text

        try:
            engine = create_engine(
                cls.get_database_url(),
                connect_args={'connect_timeout': 5} if cls.DB_TYPE == 'postgresql' else {}
            )

            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            engine.dispose()
            return True, f"Successfully connected to {cls.DB_TYPE} database"

        except Exception as e:
            return False, f"Failed to connect to database: {str(e)}"

    @classmethod
    def init_database(cls) -> bool:
        """
        Initialize database with tables

        Returns:
            True if successful
        """
        from sqlalchemy import create_engine
        from a_database_models import Base

        try:
            engine = create_engine(cls.get_database_url(), **cls.get_engine_config())

            # Create all tables
            Base.metadata.create_all(engine)

            logger.info(f"Database initialized successfully at {cls.get_database_url(include_password=False)}")
            engine.dispose()
            return True

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False

    @classmethod
    def create_database_if_not_exists(cls) -> bool:
        """
        Create PostgreSQL database if it doesn't exist

        Returns:
            True if database exists or was created
        """
        if cls.DB_TYPE != 'postgresql':
            return True  # SQLite creates automatically

        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import ProgrammingError

        try:
            # Connect to PostgreSQL without specifying database
            root_url = f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/postgres"
            engine = create_engine(root_url, isolation_level='AUTOCOMMIT')

            with engine.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": cls.DB_NAME}
                )

                if not result.fetchone():
                    # Create database
                    conn.execute(text(f'CREATE DATABASE "{cls.DB_NAME}"'))
                    logger.info(f"Created database: {cls.DB_NAME}")
                else:
                    logger.info(f"Database already exists: {cls.DB_NAME}")

            engine.dispose()
            return True

        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False

    @classmethod
    def get_storage_path(cls) -> Path:
        """
        Get path for file storage

        Returns:
            Path object for storage directory
        """
        if os.name == 'nt':  # Windows
            storage_path = Path.home() / "Documents" / "SYNAIPLIC Research"
        else:  # macOS/Linux
            storage_path = Path.home() / "Documents" / "SYNAIPLIC Research"

        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    @classmethod
    def validate_config(cls) -> tuple[bool, list[str]]:
        """
        Validate database configuration

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if cls.DB_TYPE == 'postgresql':
            if not cls.DB_USER:
                errors.append("Database user (DB_USER) is not set")
            if not cls.DB_NAME:
                errors.append("Database name (DB_NAME) is not set")
            if not cls.DB_HOST:
                errors.append("Database host (DB_HOST) is not set")

            # Test connection if config seems valid
            if not errors:
                success, message = cls.test_connection()
                if not success:
                    errors.append(message)

        return len(errors) == 0, errors

    @classmethod
    def setup_logging(cls):
        """Setup logging configuration"""
        log_level = getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO)

        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'synaiplic.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Set SQLAlchemy logging
        if cls.DEBUG:
            logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        else:
            logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def init_database():
    """Initialize database - convenience function"""
    DatabaseConfig.setup_logging()

    # Create database if needed
    if DatabaseConfig.DB_TYPE == 'postgresql':
        if not DatabaseConfig.create_database_if_not_exists():
            logger.error("Failed to create database")
            return False

    # Initialize tables
    return DatabaseConfig.init_database()


if __name__ == "__main__":
    # Test configuration when run directly
    print("SYNAIPLIC Database Configuration")
    print("=" * 50)

    # Validate configuration
    valid, errors = DatabaseConfig.validate_config()

    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  ❌ {error}")
    else:
        print("✅ Configuration is valid")

        # Test connection
        success, message = DatabaseConfig.test_connection()
        print(f"{'✅' if success else '❌'} {message}")

        if success:
            print(f"Database URL: {DatabaseConfig.get_database_url(include_password=False)}")
            print(f"Storage Path: {DatabaseConfig.get_storage_path()}")