# a_migration_manager.py
"""
Migration Manager for PDF Research Platform
Provides a Python interface to Alembic migrations
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, NullPool
from a_database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations using Alembic
    Provides a clean Python interface for migration operations
    """

    def __init__(self, database_config: DatabaseConfig, alembic_ini_path: str = "alembic.ini"):
        # Load environment variables if not already loaded
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except:
            pass

        self.database_config = database_config
        self.alembic_ini_path = alembic_ini_path
        self.engine = self.create_database_engine(database_config)

        # Set up Alembic config
        self.alembic_config = Config(alembic_ini_path)

        # Override database URL in Alembic config
        database_url = database_config.get_database_url()
        self.alembic_config.set_main_option("sqlalchemy.url", database_url)

        # Set up logging
        logging.basicConfig(level=logging.INFO)

    def initialize_migrations(self) -> bool:
        """
        Initialize Alembic for the project
        Creates the migrations directory and initial setup
        """
        try:
            # Check if migrations directory already exists
            migrations_dir = Path("migrations")
            if migrations_dir.exists():
                logger.info("✅ Migrations directory already exists")
                return True

            logger.info("🔄 Initializing Alembic migrations...")

            # Initialize Alembic
            command.init(self.alembic_config, "migrations")

            # Replace the generated env.py with our custom one
            env_py_path = migrations_dir / "env.py"
            if env_py_path.exists():
                # Read our custom env.py content
                with open("a_migrations_env.py", "r") as f:
                    custom_env_content = f.read()

                # Write to the migrations directory
                with open(env_py_path, "w") as f:
                    f.write(custom_env_content)

                logger.info("✅ Replaced env.py with custom configuration")

            # Replace script.py.mako if we have a custom template
            script_template_path = migrations_dir / "script.py.mako"
            if script_template_path.exists() and Path("a_script.py.mako").exists():
                with open("a_script.py.mako", "r") as f:
                    custom_template = f.read()

                with open(script_template_path, "w") as f:
                    f.write(custom_template)

                logger.info("✅ Replaced script.py.mako with custom template")

            logger.info("✅ Alembic initialization complete")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize migrations: {e}")
            return False

    def create_migration(self, message: str, autogenerate: bool = True) -> Optional[str]:
        """
        Create a new migration

        Args:
            message: Description of the migration
            autogenerate: Whether to auto-generate migration from model changes

        Returns:
            Migration revision ID if successful, None otherwise
        """
        try:
            logger.info(f"🔄 Creating migration: {message}")

            if autogenerate:
                # Create migration with autogenerate
                command.revision(
                    self.alembic_config,
                    message=message,
                    autogenerate=True
                )
            else:
                # Create empty migration
                command.revision(
                    self.alembic_config,
                    message=message
                )

            # Get the latest revision ID
            script_dir = ScriptDirectory.from_config(self.alembic_config)
            latest_revision = script_dir.get_current_head()

            logger.info(f"✅ Created migration: {latest_revision}")
            return latest_revision

        except Exception as e:
            logger.error(f"❌ Failed to create migration: {e}")
            return None

    def apply_migrations(self, target_revision: str = "head") -> bool:
        """
        Apply migrations to the database

        Args:
            target_revision: Target revision to upgrade to ('head' for latest)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🔄 Applying migrations to: {target_revision}")

            command.upgrade(self.alembic_config, target_revision)

            logger.info("✅ Migrations applied successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to apply migrations: {e}")
            return False

    def rollback_migration(self, target_revision: str) -> bool:
        """
        Rollback to a specific migration

        Args:
            target_revision: Target revision to downgrade to

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🔄 Rolling back to: {target_revision}")

            command.downgrade(self.alembic_config, target_revision)

            logger.info("✅ Rollback completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to rollback migration: {e}")
            return False

    def get_current_revision(self) -> Optional[str]:
        """
        Get the current database revision

        Returns:
            Current revision ID or None if not set
        """
        try:
            with self.engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                return current_rev
        except Exception as e:
            logger.error(f"❌ Failed to get current revision: {e}")
            return None

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """
        Get the migration history

        Returns:
            List of migration information
        """
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_config)
            migrations = []

            for revision in script_dir.walk_revisions():
                migrations.append({
                    'revision': revision.revision,
                    'down_revision': revision.down_revision,
                    'branch_labels': revision.branch_labels,
                    'message': revision.doc,
                    'create_date': getattr(revision, 'create_date', None)
                })

            return migrations

        except Exception as e:
            logger.error(f"❌ Failed to get migration history: {e}")
            return []

    def check_database_status(self) -> Dict[str, Any]:
        """
        Check the current status of the database and migrations

        Returns:
            Dictionary with database status information
        """
        status = {
            'database_exists': False,
            'migrations_initialized': False,
            'current_revision': None,
            'pending_migrations': [],
            'tables_exist': False,
            'table_count': 0
        }

        try:
            # Check if database is accessible
            with self.engine.connect() as connection:
                status['database_exists'] = True

                # Check if tables exist
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                status['tables_exist'] = len(tables) > 0
                status['table_count'] = len(tables)

                # Check if Alembic is initialized
                if 'alembic_version' in tables:
                    status['migrations_initialized'] = True
                    status['current_revision'] = self.get_current_revision()

                # Check for pending migrations
                if status['migrations_initialized']:
                    script_dir = ScriptDirectory.from_config(self.alembic_config)
                    current_rev = status['current_revision']
                    head_rev = script_dir.get_current_head()

                    if current_rev != head_rev:
                        # Get pending migrations
                        for revision in script_dir.iterate_revisions(head_rev, current_rev):
                            if revision.revision != current_rev:
                                status['pending_migrations'].append({
                                    'revision': revision.revision,
                                    'message': revision.doc
                                })

        except Exception as e:
            logger.error(f"❌ Error checking database status: {e}")

        return status

    def initialize_fresh_database(self) -> bool:
        """
        Initialize a fresh database with current schema
        This is useful for new installations
        """
        try:
            logger.info("🔄 Initializing fresh database...")

            # Create initial migration if migrations directory doesn't exist
            if not Path("migrations").exists():
                if not self.initialize_migrations():
                    return False

                # Create initial migration
                initial_revision = self.create_migration("Initial migration", autogenerate=True)
                if not initial_revision:
                    return False

            # Apply all migrations
            if not self.apply_migrations():
                return False

            logger.info("✅ Fresh database initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize fresh database: {e}")
            return False

    def migrate_from_sqlite_to_postgresql(self, postgresql_config: DatabaseConfig) -> bool:
        """
        Migrate data from SQLite to PostgreSQL
        This is a helper method for scaling up
        """
        try:
            logger.info("🔄 Starting SQLite to PostgreSQL migration...")

            # This would involve:
            # 1. Export data from SQLite
            # 2. Create PostgreSQL database with same schema
            # 3. Import data to PostgreSQL
            # 4. Update application configuration

            # For now, this is a placeholder for future implementation
            logger.warning("⚠️ SQLite to PostgreSQL migration not yet implemented")
            logger.info("Manual steps required:")
            logger.info("1. Create PostgreSQL database")
            logger.info("2. Update DATABASE_URL environment variable")
            logger.info("3. Run: python -m a_migration_manager apply_migrations")

            return False

        except Exception as e:
            logger.error(f"❌ Failed to migrate to PostgreSQL: {e}")
            return False

    def create_database_engine(self):
        """
        Create a database engine from configuration

        Args:
            self: DatabaseConfig instance or class

        Returns:
            SQLAlchemy engine
        """
        # Get URL from config
        if hasattr(self, 'get_database_url'):
            database_url = self.get_database_url()
        else:
            # Assume it's a URL string
            database_url = str(self)

        # Create engine with appropriate settings
        if 'postgresql' in database_url:
            return create_engine(
                database_url,
                poolclass=NullPool,
                pool_pre_ping=True,
                connect_args={
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=30000"
                }
            )
        else:
            # SQLite
            return create_engine(
                database_url,
                poolclass=NullPool,
                connect_args={"check_same_thread": False}
            )


def main():
    """
    Command-line interface for migration management
    Usage: python a_migration_manager.py <command> [args]
    """

    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env")
    except ImportError:
        print("⚠️ python-dotenv not installed - install with: pip install python-dotenv")
    except Exception as e:
        print(f"⚠️ Could not load .env file: {e}")

    if len(sys.argv) < 2:
        print("Usage: python a_migration_manager.py <command> [args]")
        print("Commands:")
        print("  init                     - Initialize migrations")
        print("  create <message>         - Create new migration")
        print("  apply                    - Apply all pending migrations")
        print("  rollback <revision>      - Rollback to specific revision")
        print("  status                   - Show database status")
        print("  history                  - Show migration history")
        print("  fresh                    - Initialize fresh database")
        return

    command_name = sys.argv[1]

    # Create database config from environment
    db_type = os.getenv('DB_TYPE', 'postgresql')

    if db_type == 'postgresql':
        config = DatabaseConfig(
            db_type='postgresql',
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'synaiptic'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
    else:
        config = DatabaseConfig(
            db_type='sqlite',
            path=os.getenv('DB_PATH', 'data/synaiptic.db')
        )

    manager = MigrationManager(config)

    if command_name == 'init':
        success = manager.initialize_migrations()
        sys.exit(0 if success else 1)

    elif command_name == 'create':
        if len(sys.argv) < 3:
            print("Error: Please provide a migration message")
            sys.exit(1)
        message = ' '.join(sys.argv[2:])
        revision = manager.create_migration(message)
        sys.exit(0 if revision else 1)

    elif command_name == 'apply':
        success = manager.apply_migrations()
        sys.exit(0 if success else 1)

    elif command_name == 'rollback':
        if len(sys.argv) < 3:
            print("Error: Please provide target revision")
            sys.exit(1)
        target = sys.argv[2]
        success = manager.rollback_migration(target)
        sys.exit(0 if success else 1)

    elif command_name == 'status':
        status = manager.check_database_status()
        print("\n📊 Database Status:")
        print(f"Database exists: {'✅' if status['database_exists'] else '❌'}")
        print(f"Migrations initialized: {'✅' if status['migrations_initialized'] else '❌'}")
        print(f"Current revision: {status['current_revision'] or 'None'}")
        print(f"Tables exist: {'✅' if status['tables_exist'] else '❌'} ({status['table_count']} tables)")

        if status['pending_migrations']:
            print(f"\n⚠️ Pending migrations ({len(status['pending_migrations'])}):")
            for migration in status['pending_migrations']:
                print(f"  - {migration['revision']}: {migration['message']}")
        else:
            print("\n✅ No pending migrations")

    elif command_name == 'history':
        history = manager.get_migration_history()
        if history:
            print("\n📚 Migration History:")
            for migration in history:
                print(f"  {migration['revision']}: {migration['message']}")
        else:
            print("No migrations found")

    elif command_name == 'fresh':
        success = manager.initialize_fresh_database()
        sys.exit(0 if success else 1)

    else:
        print(f"Unknown command: {command_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()