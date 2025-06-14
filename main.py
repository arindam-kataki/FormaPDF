"""
PDF Voice Editor - Main Entry Point
Run this file to start the application
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
else:
    print(f"Error: src directory not found at {src_path}")
    sys.exit(1)

try:
    # Import using absolute path after adding src to sys.path
    from ui.main_window import main

    if __name__ == "__main__":
        print("🚀 Starting PDF Voice Editor...")
        main()

except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install PyQt6 PyMuPDF scikit-learn pandas numpy joblib")

    # Show more detailed error information
    import traceback
    print("\nDetailed error:")
    traceback.print_exc()

    # Check if src directory and files exist
    print(f"\nDebugging info:")
    print(f"Current directory: {Path.cwd()}")
    print(f"src path: {src_path}")
    print(f"src exists: {src_path.exists()}")

    if src_path.exists():
        ui_path = src_path / "ui"
        main_window_path = ui_path / "main_window.py"
        print(f"ui directory exists: {ui_path.exists()}")
        print(f"main_window.py exists: {main_window_path.exists()}")

    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)