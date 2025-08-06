#!/usr/bin/env python3
"""
Launch Script for SYNAIPTIC PDF Research Platform
Run this from the project root to start the application
"""

import sys
import os
from pathlib import Path


def setup_environment():
    """Setup Python path and environment for the application"""

    # Get the root directory (where this script is located)
    root_dir = Path(__file__).parent.absolute()

    # Add src directory to Python path
    src_dir = root_dir / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))

    # Add src/ui directory to Python path
    ui_dir = src_dir / "ui"
    if ui_dir.exists():
        sys.path.insert(0, str(ui_dir))

    # Add src/models directory to Python path
    models_dir = src_dir / "models"
    if models_dir.exists():
        sys.path.insert(0, str(models_dir))

    # Add src/core directory to Python path
    core_dir = src_dir / "core"
    if core_dir.exists():
        sys.path.insert(0, str(core_dir))

    # Set environment variables if needed
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'  # For high DPI displays

    # Print startup information
    print("=" * 60)
    print("SYNAIPTIC PDF Research Platform")
    print("=" * 60)
    print(f"Root directory: {root_dir}")
    print(f"Python path includes: {src_dir}")
    print("-" * 60)


def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []

    # Check PyQt6
    try:
        from PyQt6 import QtCore
        print("✓ PyQt6 found")
    except ImportError:
        missing_deps.append("PyQt6")
        print("✗ PyQt6 not found")

    # Check SQLAlchemy
    try:
        import sqlalchemy
        print("✓ SQLAlchemy found")
    except ImportError:
        missing_deps.append("sqlalchemy")
        print("✗ SQLAlchemy not found")

    # Check PyMuPDF (for PDF handling)
    try:
        import fitz
        print("✓ PyMuPDF found")
    except ImportError:
        print("⚠ PyMuPDF not found (optional, but needed for PDF viewing)")

    print("-" * 60)

    if missing_deps:
        print("\n⚠️  Missing required dependencies!")
        print("Please install them using:")
        print(f"  pip install {' '.join(missing_deps)}")
        print("\nOr install all dependencies:")
        print("  pip install -r requirements.txt")
        response = input("\nDo you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    return len(missing_deps) == 0


def create_required_directories():
    """Create required directories if they don't exist"""
    root_dir = Path(__file__).parent.absolute()

    # List of required directories
    required_dirs = [
        root_dir / "data",
        root_dir / "data" / "assemblies",
        root_dir / "data" / "vector_db",
        root_dir / "logs",
        root_dir / "exports",
        root_dir / "temp"
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")


def main():
    """Main entry point"""
    try:
        # Setup environment
        setup_environment()

        # Check dependencies
        deps_ok = check_dependencies()

        # Create required directories
        create_required_directories()

        # Now import and run the main application
        print("\nLaunching application...")
        print("=" * 60)

        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt

        # Import the main window
        from ui.a_assembly_main_window import AssemblyMainWindow

        # Create application
        app = QApplication(sys.argv)

        # Set application properties
        app.setApplicationName("SYNAIPTIC")
        app.setOrganizationName("SYNAIPTIC")
        app.setApplicationDisplayName("PDF Research Platform")

        # Set application style
        app.setStyle("Fusion")

        # Enable high DPI scaling
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        # Create and show main window
        window = AssemblyMainWindow()

        # Center window on screen
        screen = app.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - window.width()) // 2
            y = (screen_geometry.height() - window.height()) // 2
            window.move(x, y)

        window.show()

        # Run application
        sys.exit(app.exec())

    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nMake sure all required files are in the correct location:")
        print("  src/ui/a_assembly_main_window.py")
        print("  src/ui/a_document_list_widget.py")
        print("  src/ui/a_assembly_manager.py")
        print("  src/ui/a_assembly_dialog.py")
        print("  src/models/a_database_models.py")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error launching application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()