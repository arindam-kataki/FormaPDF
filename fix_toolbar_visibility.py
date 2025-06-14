#!/usr/bin/env python3
"""
Fix Toolbar Visibility in main_window.py
Ensures the toolbar is properly created and visible
"""

import os
from pathlib import Path


def fix_toolbar_visibility():
    """Fix toolbar creation and visibility in main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Fixing toolbar visibility in main_window.py...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if toolbar creation is being called in init_ui
        if 'self.create_toolbar()' in content:
            print("✅ Toolbar creation is already called in init_ui")

            # Check if the toolbar method actually creates visible toolbar
            if 'QToolBar()' not in content:
                print("❌ No QToolBar creation found - adding working toolbar")
                needs_toolbar_method = True
            else:
                print("✅ QToolBar creation found")
                needs_toolbar_method = False
        else:
            print("❌ Toolbar creation not called in init_ui - will fix")
            needs_toolbar_method = True

        # Add proper toolbar creation call to init_ui if missing
        if 'self.create_toolbar()' not in content:
            # Find init_ui method and add toolbar creation
            init_ui_pos = content.find('def init_ui(self):')
            if init_ui_pos != -1:
                # Find where to insert the toolbar creation call
                # Look for where other UI components are created
                splitter_pos = content.find('self.splitter.setSizes', init_ui_pos)
                if splitter_pos != -1:
                    # Find the end of that line
                    line_end = content.find('\n', splitter_pos)
                    if line_end != -1:
                        # Insert toolbar creation after splitter setup
                        insert_text = '\n\n        # Create UI components\n        self.create_toolbar()\n        self.create_status_bar()'
                        content = content[:line_end] + insert_text + content[line_end:]
                        print("✅ Added toolbar creation call to init_ui")

        # Create a working toolbar method if needed
        if needs_toolbar_method or 'QToolBar()' not in content:
            working_toolbar = '''
    def create_toolbar(self):
        """Create main toolbar with working navigation and zoom controls"""
        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # File operations
        open_action = QAction("📁 Open PDF", self)
        open_action.setToolTip("Open PDF file (Ctrl+O)")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save form data (Ctrl+S)")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_form_data)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Navigation controls
        prev_action = QAction("⬅️ Previous", self)
        prev_action.setToolTip("Previous page")
        prev_action.triggered.connect(self.previous_page)
        toolbar.addAction(prev_action)

        next_action = QAction("➡️ Next", self)
        next_action.setToolTip("Next page")  
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Zoom controls
        zoom_out_action = QAction("🔍- Zoom Out", self)
        zoom_out_action.setToolTip("Zoom out")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        zoom_in_action = QAction("🔍+ Zoom In", self)
        zoom_in_action.setToolTip("Zoom in")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        fit_width_action = QAction("📏 Fit Width", self)
        fit_width_action.setToolTip("Fit page to window width")
        fit_width_action.triggered.connect(self.fit_width)
        toolbar.addAction(fit_width_action)

        toolbar.addSeparator()

        # View controls
        self.grid_action = QAction("📐 Grid", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setToolTip("Toggle grid display")
        self.grid_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_action)

        toolbar.addSeparator()

        # Info
        info_action = QAction("ℹ️ Info", self)
        info_action.setToolTip("Show application information")
        info_action.triggered.connect(self.show_info)
        toolbar.addAction(info_action)

        # Make sure toolbar is visible
        toolbar.show()
        print("🔧 Toolbar created and should be visible")
'''

            # Find where to insert the toolbar method
            # Look for other method definitions
            method_insert_pos = content.find('    def create_status_bar(self):')
            if method_insert_pos == -1:
                method_insert_pos = content.find('    def setup_connections(self):')
            if method_insert_pos == -1:
                method_insert_pos = content.find('    @pyqtSlot()')
            if method_insert_pos == -1:
                # Insert before main function
                method_insert_pos = content.find('\ndef main():')

            if method_insert_pos != -1:
                # Remove any existing broken toolbar method first
                existing_toolbar_start = content.find('    def create_toolbar(self):')
                if existing_toolbar_start != -1:
                    # Find the end of the existing method
                    next_method = content.find('\n    def ', existing_toolbar_start + 1)
                    if next_method == -1:
                        next_method = content.find('\n\ndef ', existing_toolbar_start + 1)
                    if next_method == -1:
                        next_method = len(content)

                    # Remove the old method
                    content = content[:existing_toolbar_start] + content[next_method:]
                    print("✅ Removed old broken toolbar method")

                    # Recalculate insert position
                    method_insert_pos = content.find('    def create_status_bar(self):')
                    if method_insert_pos == -1:
                        method_insert_pos = content.find('    def setup_connections(self):')
                    if method_insert_pos == -1:
                        method_insert_pos = content.find('\ndef main():')

                # Insert the working toolbar method
                content = content[:method_insert_pos] + working_toolbar + '\n' + content[method_insert_pos:]
                print("✅ Added working toolbar method")

        # Also ensure status bar creation is called
        if 'self.create_status_bar()' not in content:
            # Add status bar creation call if missing
            toolbar_call_pos = content.find('self.create_toolbar()')
            if toolbar_call_pos != -1:
                line_end = content.find('\n', toolbar_call_pos)
                if line_end != -1:
                    content = content[:line_end] + '\n        self.create_status_bar()' + content[line_end:]
                    print("✅ Added status bar creation call")

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Successfully fixed toolbar visibility")
        return True

    except Exception as e:
        print(f"❌ Error fixing toolbar visibility: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_toolbar_setup():
    """Verify that toolbar setup is correct"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("🔍 Verifying toolbar setup...")

        checks = [
            ("Toolbar creation called in init_ui", "self.create_toolbar()" in content),
            ("Status bar creation called", "self.create_status_bar()" in content),
            ("QToolBar imported", "QToolBar" in content),
            ("QAction imported", "QAction" in content),
            ("Toolbar method exists", "def create_toolbar(self):" in content),
            ("Toolbar.show() called", "toolbar.show()" in content),
        ]

        all_good = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
            if not check_result:
                all_good = False

        if all_good:
            print("✅ All toolbar setup checks passed!")
        else:
            print("❌ Some toolbar setup issues found")

        return all_good

    except Exception as e:
        print(f"❌ Error verifying toolbar setup: {e}")
        return False


def add_missing_imports():
    """Add any missing imports needed for toolbar"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required imports
        required_imports = [
            "QToolBar",
            "QAction",
            "Qt"
        ]

        missing_imports = []
        for imp in required_imports:
            if imp not in content:
                missing_imports.append(imp)

        if missing_imports:
            print(f"🔧 Adding missing imports: {', '.join(missing_imports)}")

            # Find the PyQt6 imports section
            pyqt_import_pos = content.find('from PyQt6.QtWidgets import (')
            if pyqt_import_pos != -1:
                # Find the end of the import
                import_end = content.find(')', pyqt_import_pos)
                if import_end != -1:
                    # Get current imports
                    current_imports = content[pyqt_import_pos:import_end]

                    # Add missing imports
                    for imp in missing_imports:
                        if imp == "Qt":
                            # Qt comes from QtCore
                            if "from PyQt6.QtCore import" not in content:
                                qtcore_import = "\nfrom PyQt6.QtCore import Qt, pyqtSlot"
                                content = content[:import_end + 1] + qtcore_import + content[import_end + 1:]
                        else:
                            # Add to QtWidgets import
                            if imp not in current_imports:
                                # Add before the closing parenthesis
                                addition = f", {imp}"
                                content = content[:import_end] + addition + content[import_end:]

            # Write back
            with open(main_window_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print("✅ Added missing imports")
        else:
            print("✅ All required imports present")

        return True

    except Exception as e:
        print(f"❌ Error adding imports: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Fix Toolbar Visibility")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Add missing imports first
    if not add_missing_imports():
        print("❌ Failed to add missing imports")
        return 1

    # Fix toolbar visibility
    if not fix_toolbar_visibility():
        print("❌ Failed to fix toolbar visibility")
        return 1

    # Verify the setup
    if verify_toolbar_setup():
        print("\n🎉 Toolbar should now be visible!")
        print("\n🎯 Next steps:")
        print("1. Run: python launch.py")
        print("2. The toolbar should now be visible at the top")
        print("3. Test the navigation and zoom buttons")
        return 0
    else:
        print("\n⚠️ Some issues may remain. Check the verification output above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())