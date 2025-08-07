#!/usr/bin/env python3
"""
Enable verbose SQLAlchemy logging to see why ROLLBACK happens
"""

import sys
import logging
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "ui"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "models"))

# Enable MAXIMUM verbosity for SQLAlchemy
logging.basicConfig(level=logging.DEBUG)

# Set up detailed logging for all SQLAlchemy components
loggers = [
    'sqlalchemy.engine',
    'sqlalchemy.orm',
    'sqlalchemy.pool',
    'sqlalchemy.dialects',
    'sqlalchemy.orm.mapper',
    'sqlalchemy.orm.relationships',
    'sqlalchemy.orm.strategies',
    'sqlalchemy.orm.query',
    'sqlalchemy.orm.unitofwork',
]

for logger_name in loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

print("=" * 80)
print("TESTING ASSEMBLY QUERY WITH MAXIMUM VERBOSITY")
print("=" * 80)

try:
    from ui.a_assembly_manager import AssemblyManager

    print("\nCreating AssemblyManager...")
    manager = AssemblyManager()

    print("\nCalling get_recent_assemblies...")
    result = manager.get_recent_assemblies(10)

    print(f"\n✅ Success! Got {len(result)} assemblies")

except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
print("CHECKING FOR IMPLICIT ROLLBACKS")
print("=" * 80)