# a_setup_migrations.py
"""
Setup script for initializing migrations in your PDF Research Platform
Run this once to set up the migration system
"""

import os
import sys
from pathlib import Path
import shutil

from a_database_models import DatabaseConfig, init_database
from a_migration_manager import MigrationManager


def setup_migration_environment():
    """
    Set up the complete migration environment for SYNAIPTIC
    """
    print("🚀 Setting up migration environment for SYNAIPTIC AI Research Platform...")

    # 1. Create necessary directories
    directories = [
        "data",
        "migrations",
        "migrations/versions"
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

    # 2. Copy configuration files to appropriate locations
    config_files = {
        "a_alembic.ini": "alembic.ini",
        "a_migrations_env.py": "migrations/env.py",
        "a_script.py.mako": "migrations/script.py.mako"
    }

    for source, destination in config_files.items():
        if Path(source).exists():
            shutil.copy2(source, destination)
            print(f"✅ Copied {source} → {destination}")
        else:
            print(f"⚠️ Source file not found: {source}")

    # 3. Set up environment variables template
    create_env_template()

    # 4. Initialize database configuration
    setup_database_config()

    print("\n✅ Migration environment setup complete!")
    print("\nNext steps:")
    print("1. Configure your database connection (see .env.template)")
    print("2. Run: python a_migration_manager.py init")
    print("3. Run: python a_migration_manager.py create 'Initial migration'")
    print("4. Run: python a_migration_manager.py apply")


def create_env_template():
    """Create environment variables template"""
    env_template = """# Environment Variables for SYNAIPTIC AI Research Platform
# Copy this file to .env and configure your database settings

# Database Configuration
# PostgreSQL is recommended for production use

# === PostgreSQL Configuration (Recommended) ===
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=synaiptic
DB_USER=synaiptic_user
DB_PASSWORD=your_secure_password

# === SQLite Configuration (Development Only) ===
# DB_TYPE=sqlite
# DB_PATH=data/synaiptic.db

# === Alternative: Full Database URL ===
# DATABASE_URL=postgresql://synaiptic_user:password@localhost:5432/synaiptic
# DATABASE_URL=sqlite:///data/synaiptic.db

# Application Settings
DEBUG=true
LOG_LEVEL=INFO

# AI Configuration (Optional)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
"""

    with open(".env.template", "w") as f:
        f.write(env_template)

    print("✅ Created .env.template")

    # Create a basic .env file if it doesn't exist
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write("# Environment Variables for SYNAIPTIC\n")
            f.write("DB_TYPE=postgresql\n")
            f.write("DB_HOST=localhost\n")
            f.write("DB_PORT=5432\n")
            f.write("DB_NAME=synaiptic\n")
            f.write("DB_USER=synaiptic_user\n")
            f.write("DB_PASSWORD=change_this_password\n")
        print("✅ Created default .env file with PostgreSQL configuration")


def setup_database_config():
    """Set up initial database configuration"""
    try:
        # Try to read from environment or use defaults
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

            print("🔄 Testing PostgreSQL connection...")
            if not config.config.get('username') or not config.config.get('password'):
                print("⚠️ PostgreSQL username/password not configured")
                print("Please set DB_USER and DB_PASSWORD in your .env file")
                return

        elif db_type == 'sqlite':
            config = DatabaseConfig(
                db_type='sqlite',
                path=os.getenv('DB_PATH', 'data/synaiptic.db')
            )
            print("🔄 Testing SQLite connection...")
        else:
            print(f"❌ Unknown database type: {db_type}")
            return

        # Test database connection
        print("🔄 Testing database connection...")
        engine = init_database(config)

        print("✅ Database connection successful")

        # Initialize migration manager
        manager = MigrationManager(config)

        # Check if we should initialize migrations
        if not Path("migrations").exists() or not any(Path("migrations").iterdir()):
            print("🔄 Initializing migration system...")
            if manager.initialize_migrations():
                print("✅ Migration system initialized")
            else:
                print("❌ Failed to initialize migration system")

    except Exception as e:
        print(f"❌ Database setup error: {e}")
        if db_type == 'postgresql':
            print("\n💡 PostgreSQL Setup Help:")
            print("1. Install PostgreSQL: https://www.postgresql.org/download/")
            print("2. Create database: createdb synaiptic")
            print("3. Create user: createuser -P synaiptic_user")
            print("4. Grant permissions: GRANT ALL PRIVILEGES ON DATABASE synaiptic TO synaiptic_user;")
            print("5. Update .env file with correct credentials")
        print("Please check your database configuration in .env file")


def create_requirements_additions():
    """Create additional requirements for migrations"""
    migration_requirements = """
# Additional requirements for database migrations
alembic>=1.12.0
psycopg2-binary>=2.9.7  # PostgreSQL adapter
python-dotenv>=1.0.0    # Environment variable loading
"""

    # Append to existing requirements.txt or create new one
    with open("requirements_migrations.txt", "w") as f:
        f.write(migration_requirements.strip())

    print("✅ Created requirements_migrations.txt")
    print("   Run: pip install -r requirements_migrations.txt")


def verify_setup():
    """Verify that the migration setup is working"""
    print("\n🔍 Verifying migration setup...")

    required_files = [
        "alembic.ini",
        "migrations/env.py",
        ".env"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    # Try to create a migration manager
    try:
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
            config = DatabaseConfig(db_type='sqlite', path=os.getenv('DB_PATH', 'data/synaiptic.db'))

        manager = MigrationManager(config)
        status = manager.check_database_status()

        print("✅ Migration system verification successful")
        print(f"   Database exists: {status['database_exists']}")
        print(f"   Migrations initialized: {status['migrations_initialized']}")

        return True

    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        if db_type == 'postgresql':
            print("💡 This is normal if PostgreSQL isn't set up yet")
        return False


def main():
    """Main setup function"""
    print("=" * 60)
    print("SYNAIPTIC - AI Research Platform Migration Setup")
    print("=" * 60)

    # Load environment variables from .env if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env")
    except ImportError:
        print("⚠️ python-dotenv not installed - using system environment variables")
    except Exception:
        pass

    # Set up migration environment
    setup_migration_environment()

    # Create additional requirements
    create_requirements_additions()

    # Verify setup
    if verify_setup():
        print("\n🎉 SYNAIPTIC migration setup completed successfully!")

        print("\n📋 Quick Start Commands:")
        print("   python a_migration_manager.py status    # Check current status")
        print("   python a_migration_manager.py fresh     # Set up fresh database")
        print("   python a_migration_manager.py create 'Add neural features'  # Create migration")
        print("   python a_migration_manager.py apply     # Apply migrations")

    else:
        print("\n❌ Setup completed with errors. Please check the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()