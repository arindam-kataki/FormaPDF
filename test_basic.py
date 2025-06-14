"""
Minimal test to check if PyQt6 and basic setup works
"""

import sys
from pathlib import Path


def test_basic_imports():
    """Test if we can import basic requirements"""
    print("🧪 Testing basic imports...")

    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
        from PyQt6.QtCore import Qt
        print("✅ PyQt6 imports work")
    except ImportError as e:
        print(f"❌ PyQt6 import failed: {e}")
        return False

    try:
        import fitz  # PyMuPDF
        print("✅ PyMuPDF (fitz) import works")
    except ImportError as e:
        print(f"❌ PyMuPDF import failed: {e}")
        print("Install with: pip install PyMuPDF")
        return False

    return True


def test_minimal_app():
    """Create minimal PyQt6 app to test if GUI works"""
    print("🖥️ Testing minimal GUI...")

    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
        from PyQt6.QtCore import Qt

        app = QApplication(sys.argv)

        window = QMainWindow()
        window.setWindowTitle("PDF Voice Editor - Test")
        window.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel("🎉 Basic setup works!\n\nIf you can see this window,\nPyQt6 is working correctly.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 14px; padding: 20px;")

        layout.addWidget(label)
        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)

        window.show()
        print("✅ Minimal GUI created successfully")
        print("Close the window to continue...")

        return app.exec()

    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False


def main():
    print("🔧 PDF Voice Editor - Basic Setup Test")
    print("=" * 40)

    # Test imports first
    if not test_basic_imports():
        print("\n❌ Basic imports failed. Please install dependencies:")
        print("pip install PyQt6 PyMuPDF")
        return 1

    # Test minimal GUI
    print("\n🖥️ Testing GUI (a window should appear)...")
    result = test_minimal_app()

    if result == 0:
        print("\n✅ Basic setup test passed!")
        print("You can now try running the full application.")
    else:
        print("\n❌ GUI test failed.")

    return result


if __name__ == "__main__":
    sys.exit(main())