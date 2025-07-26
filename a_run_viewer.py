#!/usr/bin/env python3
"""
PDF Viewer Application Launcher (for a_prefixed files)
Run this script to start the PDF viewer application
"""

import sys
import os

# Add the src/ui directory to Python path for direct imports
project_root = os.path.dirname(os.path.abspath(__file__))
src_ui_path = os.path.join(project_root, 'src', 'ui')
if src_ui_path not in sys.path:
    sys.path.insert(0, src_ui_path)

# Now we can import the a_prefixed files directly
try:
    from PyQt6.QtWidgets import QApplication

    # Import your main window (adjust import based on actual file structure)
    # If main window is in src/ui/main_window.py:
    sys.path.insert(0, os.path.join(project_root, 'src'))
    from ui.a_main_window import PDFMainWindow


    # OR if you have a_main_window.py, uncomment this instead:
    # from a_main_window import PDFMainWindow

    def main():
        """Main entry point for the PDF viewer application"""
        print("Starting PDF Viewer...")

        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("PDF Viewer")
        app.setApplicationVersion("1.0")

        # Create and show main window
        window = PDFMainWindow()
        window.show()

        print("PDF Viewer started successfully!")
        print("Use File -> Open PDF to load a document")

        # Start the event loop
        return app.exec()

except ImportError as e:
    print(f"Error importing modules: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure PyQt6 is installed: pip install PyQt6")
    print("2. Make sure PyMuPDF is installed: pip install PyMuPDF")
    print("3. Check that your main window file exists")
    print(f"4. Current working directory: {os.getcwd()}")
    print(f"5. Project root: {project_root}")
    sys.exit(1)

if __name__ == '__main__':
    sys.exit(main())