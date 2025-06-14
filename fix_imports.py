"""
Script to fix relative imports in all Python files
This will convert relative imports (from ..module import) to absolute imports (from module import)
"""

import os
import re
from pathlib import Path


def fix_relative_imports(file_path):
    """Fix relative imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Pattern to match relative imports
        patterns_to_fix = [
            # from ..models.field_model import -> from models.field_model import
            (r'from \.\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*) import', r'from \1 import'),
            # from .field_model import -> from models.field_model import (need context)
            (r'from \.([a-zA-Z_][a-zA-Z0-9_]*) import', r'from \1 import'),
        ]

        for pattern, replacement in patterns_to_fix:
            content = re.sub(pattern, replacement, content)

        # Specific fixes based on directory structure
        # These are common relative import patterns we need to fix

        # Fix imports in ui/ directory
        if '/ui/' in str(file_path) or '\\ui\\' in str(file_path):
            content = content.replace('from ..models.', 'from models.')
            content = content.replace('from ..utils.', 'from utils.')
            content = content.replace('from ..core.', 'from core.')
            content = content.replace('from ..training.', 'from training.')
            content = content.replace('from .', 'from ui.')

        # Fix imports in models/ directory
        if '/models/' in str(file_path) or '\\models\\' in str(file_path):
            content = content.replace('from ..utils.', 'from utils.')
            content = content.replace('from ..core.', 'from core.')
            content = content.replace('from .', 'from models.')

        # Fix imports in utils/ directory
        if '/utils/' in str(file_path) or '\\utils\\' in str(file_path):
            content = content.replace('from ..models.', 'from models.')
            content = content.replace('from .', 'from utils.')

        # Fix imports in core/ directory
        if '/core/' in str(file_path) or '\\core\\' in str(file_path):
            content = content.replace('from ..models.', 'from models.')
            content = content.replace('from ..utils.', 'from utils.')
            content = content.replace('from ..training.', 'from training.')
            content = content.replace('from .', 'from core.')

        # Fix imports in training/ directory
        if '/training/' in str(file_path) or '\\training\\' in str(file_path):
            content = content.replace('from ..models.', 'from models.')
            content = content.replace('from ..utils.', 'from utils.')
            content = content.replace('from .', 'from training.')

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def fix_all_imports(src_dir):
    """Fix imports in all Python files"""
    src_path = Path(src_dir)

    if not src_path.exists():
        print(f"Source directory not found: {src_path}")
        return

    print(f"Fixing imports in: {src_path}")
    print("=" * 50)

    fixed_files = []

    # Find all Python files
    for py_file in src_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue  # Skip __init__.py files

        print(f"Checking: {py_file.relative_to(src_path)}")

        if fix_relative_imports(py_file):
            fixed_files.append(py_file)
            print(f"  ✅ Fixed imports")
        else:
            print(f"  ⏭️ No changes needed")

    print("=" * 50)
    print(f"Summary: Fixed {len(fixed_files)} files")

    if fixed_files:
        print("\nFixed files:")
        for file in fixed_files:
            print(f"  - {file.relative_to(src_path)}")


def create_proper_init_files(src_dir):
    """Create proper __init__.py files"""
    src_path = Path(src_dir)

    init_files = {
        src_path / "__init__.py": '"""PDF Voice Editor - Main package"""',
        src_path / "ui" / "__init__.py": '"""User Interface components"""',
        src_path / "models" / "__init__.py": '"""Data models and business logic"""',
        src_path / "utils" / "__init__.py": '"""Utility functions and helpers"""',
        src_path / "core" / "__init__.py": '"""Core application logic"""',
        src_path / "training" / "__init__.py": '"""Machine learning and training components"""',
    }

    print("\n📝 Creating/updating __init__.py files...")

    for init_path, content in init_files.items():
        try:
            init_path.parent.mkdir(parents=True, exist_ok=True)

            if not init_path.exists():
                init_path.write_text(content + "\n", encoding='utf-8')
                print(f"  ✅ Created: {init_path.relative_to(src_path)}")
            else:
                print(f"  ⏭️ Exists: {init_path.relative_to(src_path)}")

        except Exception as e:
            print(f"  ❌ Error creating {init_path}: {e}")


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Import Fixer")
    print("This will fix relative imports in your Python files")
    print("=" * 60)

    current_dir = Path.cwd()
    src_dir = current_dir / "src"

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        print("Make sure you're running this from the project root directory")
        return 1

    # Fix imports
    fix_all_imports(src_dir)

    # Create proper __init__.py files
    create_proper_init_files(src_dir)

    print("\n🎉 Import fixing complete!")
    print("\nNext steps:")
    print("1. Try running: python test_basic.py")
    print("2. Then try: python launch.py")
    print("3. Finally: python main.py")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())