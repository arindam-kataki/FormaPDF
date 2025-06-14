"""
Alternative entry point for the PDF Voice Editor
Provides more detailed error handling and setup
"""

import sys
import os
from pathlib import Path


def check_dependencies():
    """Check if all required dependencies are available"""
    required_packages = {
        'PyQt6': 'PyQt6',
        'fitz': 'PyMuPDF',
    }

    missing_packages = []

    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True


def setup_environment():
    """Setup the application environment"""
    # Add src to Python path
    current_dir = Path(__file__).parent
    src_path = current_dir / "src"

    if src_path.exists():
        sys.path.insert(0, str(src_path))
        return True
    else:
        print(f"Error: src directory not found at {src_path}")
        return False


def main():
    """Main application entry point with error handling"""
    print("🚀 Starting PDF Voice Editor...")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup environment
    if not setup_environment():
        sys.exit(1)

    try:
        # Import and run the application
        from ui.main_window import main as app_main

        print("✅ All dependencies found")
        print("🎨 Initializing user interface...")

        app_main()

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please check that all source files are present")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()