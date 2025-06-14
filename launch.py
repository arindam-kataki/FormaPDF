#!/usr/bin/env python3
"""
Simple launcher for PDF Voice Editor
This script handles path setup and launches the application
"""

import sys
import os
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are available"""
    required = ['PyQt6', 'fitz']  # fitz is PyMuPDF
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            if pkg == 'fitz':
                print(f"   - PyMuPDF (install with: pip install PyMuPDF)")
            else:
                print(f"   - {pkg} (install with: pip install {pkg})")
        print("\nInstall missing packages and try again.")
        return False

    return True


def setup_paths():
    """Setup Python paths for the application"""
    current_dir = Path(__file__).parent
    src_dir = current_dir / "src"

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return False

    # Add src to Python path
    sys.path.insert(0, str(src_dir))
    print(f"✅ Added {src_dir} to Python path")

    return True


def create_minimal_ui():
    """Create a minimal UI if full application fails"""
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
    from PyQt6.QtCore import Qt

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("PDF Voice Editor - Minimal Mode")
    window.setGeometry(100, 100, 800, 600)

    central_widget = QWidget()
    layout = QVBoxLayout()

    label = QLabel("""
    📄 PDF Voice Editor

    Minimal mode - some features may not be available.

    This means some modules couldn't be loaded.
    Check the console for error details.

    To fix this:
    1. Ensure all Python files are in the correct directories
    2. Check that all imports are working
    3. Install missing dependencies
    """)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("font-size: 14px; padding: 20px;")

    layout.addWidget(label)

    close_btn = QPushButton("Close")
    close_btn.clicked.connect(window.close)
    layout.addWidget(close_btn)

    central_widget.setLayout(layout)
    window.setCentralWidget(central_widget)

    window.show()
    return app.exec()


def main():
    """Main launcher function"""
    print("🚀 PDF Voice Editor Launcher")
    print("=" * 40)

    # Check dependencies
    if not check_dependencies():
        return 1

    # Setup paths
    if not setup_paths():
        return 1

    try:
        # Try to import and run the main application
        print("📦 Loading application modules...")
        from ui.main_window import main as app_main

        print("✅ All modules loaded successfully!")
        print("🎉 Starting PDF Voice Editor...")

        app_main()
        return 0

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Trying minimal mode...")

        try:
            return create_minimal_ui()
        except Exception as e2:
            print(f"❌ Even minimal mode failed: {e2}")
            return 1

    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())