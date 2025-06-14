#!/usr/bin/env python3
"""
Make Main Window Fully Resizable
Ensures the main window can be resized properly with good size policies
"""

import os
import re
from pathlib import Path


def make_main_window_resizable():
    """Make the main window fully resizable with proper size policies"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Making main window fully resizable...")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the init_ui method
        init_ui_start = content.find('def init_ui(self):')
        if init_ui_start == -1:
            print("❌ init_ui method not found")
            return False

        # Look for existing window setup
        window_setup_start = content.find('self.setWindowTitle', init_ui_start)
        if window_setup_start == -1:
            print("❌ Window setup not found")
            return False

        # Find the end of the current window setup
        setup_end = content.find('\n\n        # Create central widget', window_setup_start)
        if setup_end == -1:
            setup_end = content.find('\n        # Create central widget', window_setup_start)
        if setup_end == -1:
            setup_end = content.find('\n        central_widget = QWidget()', window_setup_start)

        if setup_end == -1:
            print("❌ Could not find end of window setup")
            return False

        # Create enhanced window setup
        enhanced_setup = '''        # Window setup - Enhanced for resizability
        self.setWindowTitle("PDF Voice Editor - Enhanced with Draggable Fields")

        # Set initial size and make fully resizable
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(800, 600)  # Minimum usable size

        # Remove any size constraints that might prevent resizing
        self.setMaximumSize(16777215, 16777215)  # Qt's maximum size

        # Set size policy to allow growing and shrinking
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Enable window resizing (this should be default, but make it explicit)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)

        # Show the window initially in a normal state (not maximized/minimized)
        self.setWindowState(Qt.WindowState.WindowNoState)'''

        # Replace the old setup
        old_setup = content[window_setup_start:setup_end]
        content = content.replace(old_setup, enhanced_setup)

        print("✅ Enhanced window setup for resizability")

        # Ensure panels have proper size policies
        if not enhance_panel_size_policies(content):
            print("⚠️ Could not enhance panel size policies")
        else:
            # Re-read content after panel enhancement
            with open(main_window_path, 'r', encoding='utf-8') as f:
                content = f.read()

        # Write the updated content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Made main window fully resizable")
        return True

    except Exception as e:
        print(f"❌ Error making main window resizable: {e}")
        import traceback
        traceback.print_exc()
        return False


def enhance_panel_size_policies(content):
    """Enhance size policies for panels to support resizing"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        # Look for left panel creation
        if 'def create_left_panel(self):' in content:
            left_panel_start = content.find('def create_left_panel(self):')
            left_panel_end = content.find('\n    def ', left_panel_start + 1)
            if left_panel_end == -1:
                left_panel_end = content.find('\n\n    def ', left_panel_start + 1)

            if left_panel_end != -1:
                left_panel_method = content[left_panel_start:left_panel_end]

                # Add size policy if not present
                if 'setSizePolicy' not in left_panel_method:
                    # Find where to add size policy (before return statement)
                    return_pos = left_panel_method.rfind('return left_widget')
                    if return_pos != -1:
                        size_policy_code = '''
        # Set size policy for resizable left panel
        from PyQt6.QtWidgets import QSizePolicy
        left_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        left_widget.setMinimumWidth(250)
        left_widget.setMaximumWidth(500)

        '''

                        updated_method = (left_panel_method[:return_pos] +
                                          size_policy_code +
                                          left_panel_method[return_pos:])

                        content = content.replace(left_panel_method, updated_method)
                        print("✅ Enhanced left panel size policy")

        # Look for center panel creation
        if 'def create_center_panel(self):' in content:
            center_panel_start = content.find('def create_center_panel(self):')
            center_panel_end = content.find('\n    def ', center_panel_start + 1)
            if center_panel_end == -1:
                center_panel_end = content.find('\n\n    def ', center_panel_start + 1)

            if center_panel_end != -1:
                center_panel_method = content[center_panel_start:center_panel_end]

                # Add size policy for scroll area if not present
                if 'scroll_area.*setSizePolicy' not in center_panel_method:
                    # Find where scroll area is created
                    scroll_area_pos = center_panel_method.find('self.scroll_area = QScrollArea()')
                    if scroll_area_pos != -1:
                        # Find end of line
                        line_end = center_panel_method.find('\n', scroll_area_pos) + 1

                        size_policy_code = '''        
        # Set size policy for resizable center panel
        from PyQt6.QtWidgets import QSizePolicy
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
'''

                        updated_method = (center_panel_method[:line_end] +
                                          size_policy_code +
                                          center_panel_method[line_end:])

                        content = content.replace(center_panel_method, updated_method)
                        print("✅ Enhanced center panel size policy")

        # Write the updated content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error enhancing panel size policies: {e}")
        return False


def add_resize_event_handler():
    """Add resize event handler to the main window"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if resize event handler already exists
        if 'def resizeEvent(self, event):' in content:
            print("✅ Resize event handler already exists")
            return True

        # Add resize event handler
        resize_handler = '''
    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)

        # Update scroll area when window is resized
        if hasattr(self, 'scroll_area') and self.scroll_area:
            # Force scroll area to update its viewport
            self.scroll_area.updateGeometry()

        # Update status bar with window size (optional)
        if hasattr(self, 'statusBar'):
            size = event.size()
            # Uncomment the next line if you want to see window size in status bar
            # self.statusBar().showMessage(f"Window size: {size.width()}x{size.height()}", 2000)

        # Ensure splitter proportions are maintained
        if hasattr(self, 'splitter') and self.splitter:
            # Maintain proportional sizing
            total_width = self.width()
            left_width = max(250, min(400, total_width * 0.25))  # 25% but between 250-400px
            center_width = total_width - left_width - 20  # 20px for splitter handle
            self.splitter.setSizes([int(left_width), int(center_width)])

'''

        # Find where to insert the method (before the main function or at end of class)
        insert_pos = content.find('\ndef main():')
        if insert_pos == -1:
            insert_pos = content.find('if __name__ == "__main__":')
        if insert_pos == -1:
            insert_pos = len(content)

        # Insert the resize handler
        content = content[:insert_pos] + resize_handler + '\n' + content[insert_pos:]

        # Write the updated content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Added resize event handler")
        return True

    except Exception as e:
        print(f"❌ Error adding resize event handler: {e}")
        return False


def add_window_state_restoration():
    """Add window state saving and restoration"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add import for QSettings if not present
        if 'QSettings' not in content:
            # Find PyQt6 imports
            qt_import_pos = content.find('from PyQt6.QtWidgets import')
            if qt_import_pos != -1:
                line_end = content.find('\n', qt_import_pos)
                # Add QSettings import after QtWidgets
                content = (content[:line_end] +
                           '\nfrom PyQt6.QtCore import QSettings' +
                           content[line_end:])
                print("✅ Added QSettings import")

        # Add window state methods if they don't exist
        if 'def save_window_state(self):' not in content:
            window_state_methods = '''
    def save_window_state(self):
        """Save window state and geometry"""
        try:
            settings = QSettings('PDFVoiceEditor', 'MainWindow')
            settings.setValue('geometry', self.saveGeometry())
            settings.setValue('windowState', self.saveState())
            if hasattr(self, 'splitter'):
                settings.setValue('splitterSizes', self.splitter.saveState())
        except Exception as e:
            print(f"Could not save window state: {e}")

    def restore_window_state(self):
        """Restore window state and geometry"""
        try:
            settings = QSettings('PDFVoiceEditor', 'MainWindow')
            geometry = settings.value('geometry')
            if geometry:
                self.restoreGeometry(geometry)
            window_state = settings.value('windowState')
            if window_state:
                self.restoreState(window_state)
            if hasattr(self, 'splitter'):
                splitter_state = settings.value('splitterSizes')
                if splitter_state:
                    self.splitter.restoreState(splitter_state)
        except Exception as e:
            print(f"Could not restore window state: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        self.save_window_state()
        super().closeEvent(event)

'''

            # Find where to insert the methods
            insert_pos = content.find('\ndef main():')
            if insert_pos == -1:
                insert_pos = content.find('if __name__ == "__main__":')
            if insert_pos == -1:
                insert_pos = len(content)

            # Insert the methods
            content = content[:insert_pos] + window_state_methods + '\n' + content[insert_pos:]

            print("✅ Added window state save/restore methods")

        # Add call to restore_window_state in init_ui if not present
        if 'self.restore_window_state()' not in content:
            init_ui_end = content.find('self.setup_connections()', content.find('def init_ui(self):'))
            if init_ui_end == -1:
                init_ui_end = content.find('def setup_connections(self):', content.find('def init_ui(self):'))

            if init_ui_end != -1:
                line_end = content.find('\n', init_ui_end)
                content = (content[:line_end] +
                           '\n        \n        # Restore window state from previous session\n        self.restore_window_state()' +
                           content[line_end:])
                print("✅ Added window state restoration call")

        # Write the updated content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error adding window state restoration: {e}")
        return False


def validate_resizable_setup():
    """Validate that the window is properly set up for resizing"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ('setMinimumSize', 'Minimum size set'),
            ('setMaximumSize', 'Maximum size set (unlimited)'),
            ('setSizePolicy', 'Size policy configured'),
            ('def resizeEvent', 'Resize event handler'),
            ('save_window_state', 'Window state saving'),
        ]

        all_good = True
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"⚠️ {description} - missing")
                all_good = False

        # Try to compile
        try:
            compile(content, str(main_window_path), 'exec')
            print("✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"❌ Syntax error: Line {e.lineno}: {e.msg}")
            all_good = False

        return all_good

    except Exception as e:
        print(f"❌ Error validating setup: {e}")
        return False


def main():
    """Main execution function"""
    print("🔧 PDF Voice Editor - Make Main Window Resizable")
    print("=" * 55)

    success = True

    # Step 1: Make window resizable
    if not make_main_window_resizable():
        success = False

    # Step 2: Add resize event handler
    if not add_resize_event_handler():
        success = False

    # Step 3: Add window state restoration
    if not add_window_state_restoration():
        success = False

    # Step 4: Validate setup
    if success and validate_resizable_setup():
        print("\n🎉 Success! Main window is now fully resizable.")
        print("\n🎯 Features added:")
        print("   • Window can be resized with mouse")
        print("   • Minimum size: 800x600")
        print("   • Maximum size: unlimited")
        print("   • Panels resize proportionally")
        print("   • Window state is saved/restored")
        print("   • Splitter maintains proportions")
        print("\n🎯 Try the application:")
        print("   python launch.py")
        print("\n📝 You should be able to:")
        print("   • Drag window edges to resize")
        print("   • Drag splitter to adjust panel sizes")
        print("   • Window remembers size between sessions")
        return 0
    else:
        print("\n⚠️ Some issues may remain. Check the messages above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())