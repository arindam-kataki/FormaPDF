# a_migration_manager.py
"""
Migration Manager for PDF Research Platform
Provides a Python interface to Alembic migrations
Works with DatabaseConfig class methods
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations using Alembic
    Provides a clean Python interface for migration operations
    """

    def __init__(self, database_config=None, alembic_ini_path: str = "alembic.ini"):
        """
        Initialize Migration Manager

        Args:
            database_config: DatabaseConfig class (not instance) or None
            alembic_ini_path: Path to alembic.ini file
        """
        # Load environment variables if not already loaded
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except:
            pass

        self.database_config = database_config
        self.alembic_ini_path = alembic_ini_path

        # Get database URL from DatabaseConfig class methods
        if database_config and hasattr(database_config, 'get_database_url'):
            database_url = database_config.get_database_url()
        else:
            # Fallback to environment variables
            db_type = os.getenv('DB_TYPE', 'postgresql')
            if db_type == 'postgresql':
                db_host = os.getenv('DB_HOST', 'localhost')
                db_port = os.getenv('DB_PORT', '5432')
                db_name = os.getenv('DB_NAME', 'formapdf')
                db_user = os.getenv('DB_USER', 'postgres')
                db_password = os.getenv('DB_PASSWORD', '')
                database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            else:
                db_path = os.getenv('DB_PATH', 'data/formapdf.db')
                database_url = f"sqlite:///{db_path}"

        self.database_url = database_url

        # Create engine with appropriate settings
        if 'postgresql' in database_url:
            self.engine = create_engine(
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
            Path('data').mkdir(exist_ok=True)  # Ensure data directory exists
            self.engine = create_engine(
                database_url,
                poolclass=NullPool,
                connect_args={"check_same_thread": False}
            )

        # Set up Alembic config
        self.alembic_config = Config(alembic_ini_path)

        # Override database URL in Alembic config
        self.alembic_config.set_main_option("sqlalchemy.url", database_url)

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%%(message)s'  # Simple format to avoid the logging issue
        )

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

            # Replace the generated env.py with our custom one if it exists
            env_py_path = migrations_dir / "env.py"
            if env_py_path.exists() and Path("a_migrations_env.py").exists():
                logger.info("   Replacing env.py with custom configuration...")
                with open("a_migrations_env.py", "r") as f:
                    custom_env_content = f.read()

                with open(env_py_path, "w") as f:
                    f.write(custom_env_content)

                logger.info("✅ Replaced env.py with custom configuration")

            # Replace script.py.mako if we have a custom template
            script_template_path = migrations_dir / "script.py.mako"
            if script_template_path.exists() and Path("a_script.py.mako").exists():
                logger.info("   Replacing script.py.mako with custom template...")
                with open("a_script.py.mako", "r") as f:
                    custom_template = f.read()

                with open(script_template_path, "w") as f:
                    f.write(custom_template)

                logger.info("✅ Replaced script.py.mako with custom template")
            elif script_template_path.exists():
                # If no custom template, ensure the default has revision variables
                logger.info("   Updating default script.py.mako template...")
                template_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Apply database schema changes."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Revert database schema changes."""
    ${downgrades if downgrades else "pass"}
'''
                with open(script_template_path, "w") as f:
                    f.write(template_content)
                logger.info("✅ Updated script.py.mako template")

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

            # Ensure migrations are initialized
            if not Path("migrations").exists():
                logger.info("   Migrations not initialized, initializing now...")
                if not self.initialize_migrations():
                    return None

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
            traceback.print_exc()
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
            logger.error(f"   Error details: {str(e)}")
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
            'table_count': 0,
            'table_list': []
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
                status['table_list'] = sorted(tables)

                # Check if Alembic is initialized
                if 'alembic_version' in tables:
                    status['migrations_initialized'] = True
                    status['current_revision'] = self.get_current_revision()

                # Check for pending migrations if migrations exist
                if Path("migrations").exists() and status['migrations_initialized']:
                    script_dir = ScriptDirectory.from_config(self.alembic_config)
                    current_rev = status['current_revision']
                    head_rev = script_dir.get_current_head()

                    if current_rev != head_rev:
                        # Get pending migrations
                        for revision in script_dir.iterate_revisions(head_rev, current_rev):
                            if revision and revision.revision != current_rev:
                                status['pending_migrations'].append({
                                    'revision': revision.revision,
                                    'message': revision.doc
                                })

        except Exception as e:
            logger.error(f"❌ Error checking database status: {e}")
            status['error'] = str(e)

        return status

    def initialize_fresh_database(self) -> bool:
        """
        Initialize a fresh database with current schema
        This is useful for new installations
        """
        try:
            logger.info("🔄 Initializing fresh database...")

            # Ensure data directory exists for SQLite
            if 'sqlite' in self.database_url:
                Path('data').mkdir(exist_ok=True)

            # Create initial migration if migrations directory doesn't exist
            if not Path("migrations").exists():
                logger.info("   Creating migrations directory...")
                if not self.initialize_migrations():
                    return False

                # Create initial migration
                logger.info("   Creating initial migration...")
                initial_revision = self.create_migration("Initial migration", autogenerate=True)
                if not initial_revision:
                    return False

            # Apply all migrations
            logger.info("   Applying migrations...")
            if not self.apply_migrations():
                return False

            logger.info("✅ Fresh database initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize fresh database: {e}")
            return False

    def stamp_current(self, revision: str = "head") -> bool:
        """
        Stamp the database with a specific revision without running migrations
        Useful when tables already exist

        Args:
            revision: Revision to stamp (default: "head")

        Returns:
            True if successful
        """
        try:
            logger.info(f"🔄 Stamping database with revision: {revision}")
            command.stamp(self.alembic_config, revision)
            logger.info("✅ Database stamped successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to stamp database: {e}")
            return False

    def create_database_if_not_exists(self) -> bool:
        """
        Create PostgreSQL database if it doesn't exist

        Returns:
            True if database exists or was created
        """
        if 'sqlite' in self.database_url:
            # SQLite creates automatically
            Path('data').mkdir(exist_ok=True)
            return True

        if 'postgresql' not in self.database_url:
            return True

        try:
            # Parse connection details from URL
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)

            # Connect to PostgreSQL without database
            root_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"
            root_engine = create_engine(root_url, isolation_level='AUTOCOMMIT')

            with root_engine.connect() as conn:
                # Check if database exists
                from sqlalchemy import text
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": parsed.path[1:]}  # Remove leading /
                )

                if not result.fetchone():
                    # Create database
                    db_name = parsed.path[1:]
                    conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                    logger.info(f"✅ Created database: {db_name}")
                else:
                    logger.info(f"✅ Database already exists: {parsed.path[1:]}")

            root_engine.dispose()
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False


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
        print("⚠️ python-dotenv not installed - using system environment variables")
    except Exception as e:
        print(f"⚠️ Could not load .env file: {e}")

    if len(sys.argv) < 2:
        print("\n📚 Migration Manager for FormaPDF")
        print("=" * 50)
        print("Usage: python a_migration_manager.py <command> [args]")
        print("\nCommands:")
        print("  init                     - Initialize migrations")
        print("  create <message>         - Create new migration")
        print("  apply                    - Apply all pending migrations")
        print("  rollback <revision>      - Rollback to specific revision")
        print("  status                   - Show database status")
        print("  history                  - Show migration history")
        print("  fresh                    - Initialize fresh database")
        print("  stamp <revision>         - Stamp existing database with revision")
        print("  createdb                 - Create database if it doesn't exist")
        print("\nExamples:")
        print("  python a_migration_manager.py status")
        print("  python a_migration_manager.py create 'Add user table'")
        print("  python a_migration_manager.py apply")
        print("  python a_migration_manager.py stamp head  # Mark existing DB as current")
        return

    command_name = sys.argv[1]

    # Try to import DatabaseConfig, use it if available
    try:
        from a_database_config import DatabaseConfig
        manager = MigrationManager(DatabaseConfig, alembic_ini_path="alembic.ini")
        print(f"📍 Using database: {DatabaseConfig.get_database_url(include_password=False)}")
    except ImportError:
        # Fall back to environment variables
        manager = MigrationManager(alembic_ini_path="alembic.ini")
        db_type = os.getenv('DB_TYPE', 'postgresql')
        if db_type == 'postgresql':
            print(f"📍 Using PostgreSQL database from environment variables")
        else:
            print(f"📍 Using SQLite database from environment variables")

    # Execute commands
    if command_name == 'init':
        success = manager.initialize_migrations()
        if success:
            print("\n✨ Next step: Create your first migration with:")
            print("   python a_migration_manager.py create 'Initial schema'")
        sys.exit(0 if success else 1)

    elif command_name == 'create':
        if len(sys.argv) < 3:
            print("❌ Error: Please provide a migration message")
            print("   Example: python a_migration_manager.py create 'Add user table'")
            sys.exit(1)
        message = ' '.join(sys.argv[2:])
        revision = manager.create_migration(message)
        if revision:
            print(f"\n✨ Next step: Apply the migration with:")
            print(f"   python a_migration_manager.py apply")
        sys.exit(0 if revision else 1)

    elif command_name == 'apply':
        success = manager.apply_migrations()
        sys.exit(0 if success else 1)

    elif command_name == 'rollback':
        if len(sys.argv) < 3:
            print("❌ Error: Please provide target revision")
            print("   Example: python a_migration_manager.py rollback -1")
            sys.exit(1)
        target = sys.argv[2]
        success = manager.rollback_migration(target)
        sys.exit(0 if success else 1)

    elif command_name == 'status':
        status = manager.check_database_status()
        print("\n📊 Database Status")
        print("=" * 50)
        print(f"Database exists:       {'✅ Yes' if status['database_exists'] else '❌ No'}")
        print(f"Migrations initialized: {'✅ Yes' if status['migrations_initialized'] else '❌ No'}")
        print(f"Current revision:      {status['current_revision'] or 'None'}")
        print(f"Tables in database:    {status['table_count']}")

        if status['table_list']:
            print("\n📋 Existing tables:")
            for table in status['table_list']:
                print(f"   • {table}")

        if status['pending_migrations']:
            print(f"\n⚠️  Pending migrations ({len(status['pending_migrations'])}):")
            for migration in status['pending_migrations']:
                print(f"   • {migration['revision'][:8]}: {migration['message']}")
            print("\n💡 Run 'python a_migration_manager.py apply' to apply pending migrations")
        elif status['migrations_initialized']:
            print("\n✅ All migrations are up to date")

        if not status['migrations_initialized'] and status['tables_exist']:
            print("\n💡 Tables exist but migrations not initialized.")
            print("   If these are existing tables, run:")
            print("   python a_migration_manager.py stamp head")

    elif command_name == 'history':
        history = manager.get_migration_history()
        if history:
            print("\n📚 Migration History")
            print("=" * 50)
            for i, migration in enumerate(history):
                prefix = "→" if i == 0 else " "
                print(f"{prefix} {migration['revision'][:8]}: {migration['message']}")
        else:
            print("📭 No migrations found")
            print("💡 Create your first migration with:")
            print("   python a_migration_manager.py create 'Initial schema'")

    elif command_name == 'fresh':
        print("🚀 Setting up fresh database with migrations...")
        success = manager.initialize_fresh_database()
        if success:
            print("\n🎉 Fresh database initialized successfully!")
            print("   Your database is ready to use.")
        sys.exit(0 if success else 1)

    elif command_name == 'stamp':
        revision = sys.argv[2] if len(sys.argv) > 2 else 'head'
        success = manager.stamp_current(revision)
        if success:
            print(f"\n✅ Database stamped with revision: {revision}")
            print("   Alembic will now track future schema changes.")
        sys.exit(0 if success else 1)

    elif command_name == 'createdb':
        success = manager.create_database_if_not_exists()
        sys.exit(0 if success else 1)

    else:
        print(f"❌ Unknown command: {command_name}")
        print("   Run without arguments to see available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()