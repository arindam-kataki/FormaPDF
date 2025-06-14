"""
Debug script to check project structure and identify missing files
"""

import os
from pathlib import Path


def check_project_structure():
    """Check what files actually exist in the project"""

    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    print("=" * 50)

    # Check main files
    main_files = ['main.py', 'run_app.py', 'requirements.txt']
    print("📁 Main files:")
    for file in main_files:
        exists = (current_dir / file).exists()
        print(f"  {'✅' if exists else '❌'} {file}")

    print()

    # Check src directory structure
    src_dir = current_dir / "src"
    print(f"📁 src directory ({src_dir}):")
    print(f"  {'✅' if src_dir.exists() else '❌'} src/ exists")

    if src_dir.exists():
        # Check subdirectories
        subdirs = ['ui', 'models', 'utils', 'core', 'training']
        for subdir in subdirs:
            subdir_path = src_dir / subdir
            exists = subdir_path.exists()
            print(f"  {'✅' if exists else '❌'} src/{subdir}/")

            if exists:
                # Check key files in each subdirectory
                files_to_check = {
                    'ui': ['__init__.py', 'main_window.py', 'pdf_canvas.py', 'field_palette.py', 'properties_panel.py'],
                    'models': ['__init__.py', 'field_model.py'],
                    'utils': ['__init__.py', 'geometry_utils.py', 'icon_utils.py'],
                    'core': ['__init__.py', 'voice_handler.py'],
                    'training': ['__init__.py', 'intent_classifier.py', 'training_data.py']
                }

                if subdir in files_to_check:
                    for file in files_to_check[subdir]:
                        file_path = subdir_path / file
                        exists = file_path.exists()
                        print(f"    {'✅' if exists else '❌'} {file}")

    print()

    # Check data directory
    data_dir = current_dir / "data"
    print(f"📁 data directory ({data_dir}):")
    print(f"  {'✅' if data_dir.exists() else '❌'} data/ exists")

    if data_dir.exists():
        subdirs = ['training', 'models']
        for subdir in subdirs:
            subdir_path = data_dir / subdir
            exists = subdir_path.exists()
            print(f"  {'✅' if exists else '❌'} data/{subdir}/")

    print()
    print("=" * 50)

    # Suggest fixes
    print("🔧 Suggested fixes:")

    if not src_dir.exists():
        print("1. Create src directory and move Python modules there")

    missing_files = []
    if src_dir.exists():
        critical_files = [
            'src/ui/main_window.py',
            'src/ui/pdf_canvas.py',
            'src/models/field_model.py',
            'src/utils/geometry_utils.py'
        ]

        for file_path in critical_files:
            if not (current_dir / file_path).exists():
                missing_files.append(file_path)

    if missing_files:
        print("2. Create missing critical files:")
        for file in missing_files:
            print(f"   - {file}")

    # Check Python path issues
    print("3. Import test:")
    import sys
    sys.path.insert(0, str(src_dir))

    try:
        import ui
        print("   ✅ Can import ui module")
    except ImportError as e:
        print(f"   ❌ Cannot import ui module: {e}")

    try:
        from ui import main_window
        print("   ✅ Can import main_window")
    except ImportError as e:
        print(f"   ❌ Cannot import main_window: {e}")


if __name__ == "__main__":
    check_project_structure()