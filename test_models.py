#!/usr/bin/env python3
"""
Test if UserTOC model is properly configured
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "ui"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "models"))


def test_models():
    try:
        print("Testing model imports...")

        # Import models
        from a_database_models import Base, Assembly, UserTOC, Document
        print("✅ Models imported successfully")

        # Check UserTOC relationships
        print("\nChecking UserTOC relationships:")

        # Check if children relationship exists
        if hasattr(UserTOC, 'children'):
            print("✅ UserTOC.children relationship exists")

        # Check if parent relationship exists (should be created by backref)
        if hasattr(UserTOC, 'parent'):
            print("✅ UserTOC.parent relationship exists (via backref)")

        # Try to access relationship properties
        try:
            rel = UserTOC.children.property
            print(f"✅ Children relationship configured: {rel}")
        except Exception as e:
            print(f"❌ Error with children relationship: {e}")

        # Test creating a query
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from a_database_config import DatabaseConfig

        print("\nTesting database query...")
        engine = create_engine(DatabaseConfig.get_database_url())
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # This should work without errors
            query = session.query(Assembly).filter_by(
                is_active=True,
                is_archived=False
            ).limit(1)

            # Execute the query
            result = query.first()
            print(f"✅ Query executed successfully. Result: {result}")

        finally:
            session.close()

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if test_models():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed")