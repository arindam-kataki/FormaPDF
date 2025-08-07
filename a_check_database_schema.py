#!/usr/bin/env python3
"""
Check the actual database schema to see what's really in PostgreSQL
This will help us understand what migration is needed
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, text

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "ui"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "models"))


def check_database_schema():
    """Check the actual database schema"""

    try:
        from a_database_config import DatabaseConfig

        # Get database URL
        db_url = DatabaseConfig.get_database_url()
        print(f"Connecting to: {DatabaseConfig.get_database_url(include_password=False)}")

        # Create engine
        engine = create_engine(db_url)

        # Create inspector
        inspector = inspect(engine)

        # Check if user_toc table exists
        tables = inspector.get_table_names()
        print(f"\n📊 Tables in database: {tables}")

        if 'user_toc' in tables:
            print("\n✅ user_toc table exists")

            # Get columns
            columns = inspector.get_columns('user_toc')
            print("\n📋 Columns in user_toc table:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  - {col['name']}: {col['type']} {nullable}")

            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys('user_toc')
            print("\n🔗 Foreign keys in user_toc:")
            for fk in foreign_keys:
                print(
                    f"  - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

            # Get indexes
            indexes = inspector.get_indexes('user_toc')
            print("\n📍 Indexes on user_toc:")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")

            # Check for parent_id column specifically
            has_parent_id = any(col['name'] == 'parent_id' for col in columns)
            if has_parent_id:
                print("\n✅ parent_id column exists")
            else:
                print("\n❌ parent_id column is MISSING - this needs to be added!")

        else:
            print("\n❌ user_toc table does NOT exist")

        # Also check assemblies table
        if 'assemblies' in tables:
            print("\n✅ assemblies table exists")
            assembly_cols = inspector.get_columns('assemblies')
            print(f"  - Has {len(assembly_cols)} columns")

        # Try a test query
        print("\n🔍 Testing Assembly query...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as count FROM assemblies 
                WHERE is_active = true AND is_archived = false
            """))
            count = result.scalar()
            print(f"  - Found {count} active assemblies")

        return True

    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🔍 Database Schema Checker")
    print("=" * 60)

    if check_database_schema():
        print("\n✅ Database check complete")
        print("\nNext steps based on findings above:")
        print("1. If parent_id is missing, we need to add it")
        print("2. If table doesn't exist, we need to create it")
        print("3. If there are constraint issues, we need to fix them")
    else:
        print("\n❌ Database check failed")

    return 0


if __name__ == "__main__":
    sys.exit(main())