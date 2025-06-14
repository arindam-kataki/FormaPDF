#!/usr/bin/env python3
"""
Complete Toolbar Fix
Replace the minimal toolbar with a full-featured one and ensure it's called
"""

import os
from pathlib import Path
import re


def fix_complete_toolbar():
    """Replace the existing minimal toolbar with a complete one"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Replacing minimal toolbar with complete navigation toolbar...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # The current toolbar method only has Open, Save, Info
        # Let's replace it completely with a full-featured toolbar
        complete_toolbar = '''    def create_toolbar(self):
        """Create complete toolbar with all navigation and zoom controls"""
        # Create main toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # File operations
        open_action = QAction("📁 Open", self)
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
        zoom_out_action = QAction("🔍-", self)
        zoom_out_action.setToolTip("Zoom out")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        zoom_in_action = QAction("🔍+", self)
        zoom_in_action.setToolTip("Zoom in")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        fit_width_action = QAction("📏", self)
        fit_width_action.setToolTip("Fit page to window width")
        fit_width_action.triggered.connect(self.fit_width)
        toolbar.addAction(fit_width_action)

        toolbar.addSeparator()

        # View controls
        self.grid_action = QAction("📐", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setToolTip("Toggle grid display")
        self.grid_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_action)

        toolbar.addSeparator()

        # Info
        info_action = QAction("ℹ️", self)
        info_action.setToolTip("Show application information")
        info_action.triggered.connect(self.show_info)
        toolbar.addAction(info_action)

        # Ensure toolbar is visible
        toolbar.show()
        print("🔧 Complete toolbar created with navigation and zoom controls")'''

        # Find and replace the existing create_toolbar method
        toolbar_start = content.find('    def create_toolbar(self):')
        if toolbar_start == -1:
            print("❌ create_toolbar method not found")
            return False

        # Find the end of the current create_toolbar method
        next_method = content.find('\n    def ', toolbar_start + 1)
        if next_method == -1:
            # Look for other possible endings
            next_method = content.find('\n\n    def ', toolbar_start + 1)
        if next_method == -1:
            next_method = content.find('\ndef ', toolbar_start + 1)
        if next_method == -1:
            next_method = len(content)

        # Replace the existing method
        content = content[:toolbar_start] + complete_toolbar + '\n' + content[next_method:]
        print("✅ Replaced minimal toolbar with complete toolbar")

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error replacing toolbar: {e}")
        import traceback
        traceback.print_exc()
        return False


def ensure_toolbar_called_in_init_ui():
    """Ensure create_toolbar is called in init_ui method"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if create_toolbar is called in init_ui
        if 'self.create_toolbar()' in content:
            print("✅ create_toolbar() is already called")
            return True

        print("🔧 Adding create_toolbar() call to init_ui...")

        # Find the init_ui method
        init_ui_start = content.find('def init_ui(self):')
        if init_ui_start == -1:
            print("❌ init_ui method not found")
            return False

        # Find the end of init_ui method
        next_method = content.find('\n    def ', init_ui_start + 1)
        if next_method == -1:
            next_method = content.find('\ndef ', init_ui_start + 1)
        if next_method == -1:
            next_method = len(content)

        init_ui_content = content[init_ui_start:next_method]

        # Look for a good place to insert the toolbar call
        # Try to find after window setup but before final operations
        insert_positions = [
            'self.setCentralWidget(self.central_widget)',
            'self.setWindowTitle(',
            'self.resize(',
            'self.show()'
        ]

        insert_pos = None
        for position in insert_positions:
            pos = init_ui_content.find(position)
            if pos != -1:
                # Find the end of that line
                line_end = init_ui_content.find('\n', pos)
                if line_end != -1:
                    insert_pos = init_ui_start + line_end
                    break

        if insert_pos is None:
            # Insert at the end of the method
            insert_pos = next_method - 1

        # Insert the toolbar and status bar creation
        toolbar_call = '\n\n        # Create toolbar and status bar\n        self.create_toolbar()\n        self.create_status_bar()'
        content = content[:insert_pos] + toolbar_call + content[insert_pos:]

        # Write back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Added create_toolbar() call to init_ui")
        return True

    except Exception as e:
        print(f"❌ Error ensuring toolbar call: {e}")
        return False


def verify_complete_setup():
    """Verify that the complete toolbar setup is working"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("🔍 Verifying complete toolbar setup...")

        checks = [
            ("Toolbar creation called in init_ui", "self.create_toolbar()" in content),
            ("Status bar creation called", "self.create_status_bar()" in content),
            ("Previous page action exists", "⬅️ Previous" in content),
            ("Next page action exists", "➡️ Next" in content),
            ("Zoom out action exists", "🔍-" in content),
            ("Zoom in action exists", "🔍+" in content),
            ("Fit width action exists", "📏" in content),
            ("Grid toggle action exists", "📐" in content),
            ("Toolbar show called", "toolbar.show()" in content),
        ]

        all_good = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
            if not check_result:
                all_good = False

        if all_good:
            print("✅ Complete toolbar setup verified!")
        else:
            print("❌ Some toolbar setup issues found")

        return all_good

    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Complete Toolbar Fix")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Replace the minimal toolbar with complete one
    if not fix_complete_toolbar():
        print("❌ Failed to replace toolbar")
        return 1

    # Ensure toolbar is called in init_ui
    if not ensure_toolbar_called_in_init_ui():
        print("❌ Failed to ensure toolbar call")
        return 1

    # Verify everything is set up correctly
    if verify_complete_setup():
        print("\n🎉 Complete toolbar setup successful!")
        print("\n🎯 Now when you run the app, you should see:")
        print("  📁 Open | 💾 Save | ⬅️ Previous | ➡️ Next | 🔍- | 🔍+ | 📏 | 📐 | ℹ️")
        print("\n🚀 Test it now:")
        print("  python launch.py")
        return 0
    else:
        print("\n⚠️ Setup completed but verification found some issues")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())