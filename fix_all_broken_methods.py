#!/usr/bin/env python3
"""
Fix All Broken Methods in main_window.py
Comprehensive fix for all duplicated and incomplete if statements
"""

import os
from pathlib import Path
import re


def fix_all_broken_methods():
    """Fix all broken methods with duplicated if statements"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Fixing all broken methods in main_window.py...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Define the correct implementations for all broken methods
        method_fixes = {
            'on_field_clicked': '''    @pyqtSlot(str)
    def on_field_clicked(self, field_id: str):
        """Handle field selection"""
        selected_field = self.pdf_canvas.selected_field
        if selected_field:
            self.properties_panel.show_field_properties(selected_field)
            self.field_info_label.setText(f"Selected: {selected_field.name} ({selected_field.type.value})")

            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(True)
            if hasattr(self.field_palette, "highlight_field_type"):
                self.field_palette.highlight_field_type(selected_field.type.value)
''',

            'on_selection_changed': '''    @pyqtSlot(object)
    def on_selection_changed(self, field):
        """Handle selection change"""
        if field:
            self.properties_panel.show_field_properties(field)
            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(True)
            if hasattr(self.field_palette, "highlight_field_type"):
                self.field_palette.highlight_field_type(field.type.value)
        else:
            self.properties_panel.show_no_selection()
            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(False)
            if hasattr(self.field_palette, "clear_highlights"):
                self.field_palette.clear_highlights()
''',

            'on_field_moved': '''    @pyqtSlot(str, int, int)
    def on_field_moved(self, field_id: str, x: int, y: int):
        """Handle field movement"""
        self.operation_label.setText(f"Moved to ({x}, {y})")
        # Update properties panel
        self.properties_panel.update_field_property(field_id, 'x', x)
        self.properties_panel.update_field_property(field_id, 'y', y)
''',

            'on_field_resized': '''    @pyqtSlot(str, int, int, int, int)
    def on_field_resized(self, field_id: str, x: int, y: int, width: int, height: int):
        """Handle field resize"""
        self.operation_label.setText(f"Resized to {width}×{height}")
        # Update properties panel
        self.properties_panel.update_field_property(field_id, 'x', x)
        self.properties_panel.update_field_property(field_id, 'y', y)
        self.properties_panel.update_field_property(field_id, 'width', width)
        self.properties_panel.update_field_property(field_id, 'height', height)
''',

            'on_position_clicked': '''    @pyqtSlot(int, int)
    def on_position_clicked(self, x: int, y: int):
        """Handle position click (no field selected)"""
        self.operation_label.setText(f"Position: ({x}, {y})")
        self.field_info_label.setText("No field selected")
''',
        }

        # Replace each broken method
        for method_name, fixed_code in method_fixes.items():
            # Find the method using a flexible pattern
            pattern = rf'(\s*)@pyqtSlot.*?\s*def {method_name}\(.*?\):.*?(?=\n\s*@|\n\s*def |\nclass |\Z)'

            match = re.search(pattern, content, re.DOTALL)
            if match:
                old_method = match.group(0)
                content = content.replace(old_method, fixed_code)
                print(f"  ✅ Fixed {method_name} method")
            else:
                print(f"  ⚠️ Could not find {method_name} method to fix")

        # Remove any remaining duplicate lines throughout the file
        print("\n🧹 Cleaning up duplicate lines...")

        lines = content.split('\n')
        cleaned_lines = []
        prev_line = ""

        for line in lines:
            # Skip duplicate if hasattr lines
            if (line.strip().startswith('if hasattr(self.field_palette,') and
                    line.strip() == prev_line.strip() and
                    prev_line.strip().startswith('if hasattr(self.field_palette,')):
                print(f"  ✅ Removed duplicate: {line.strip()}")
                continue

            cleaned_lines.append(line)
            prev_line = line

        content = '\n'.join(cleaned_lines)

        # Write the fixed content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("\n✅ Fixed all broken methods in main_window.py")
        return True

    except Exception as e:
        print(f"❌ Error fixing methods: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_syntax():
    """Validate that the file has correct Python syntax"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔍 Validating Python syntax...")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to compile the code to check for syntax errors
        compile(content, main_window_path, 'exec')
        print("✅ Python syntax is valid")
        return True

    except SyntaxError as e:
        print(f"❌ Syntax error found:")
        print(f"   Line {e.lineno}: {e.text}")
        print(f"   Error: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error validating syntax: {e}")
        return False


def create_clean_main_window():
    """Create a completely clean version of main_window.py if all else fails"""

    main_window_path = Path("src/ui/main_window.py")
    backup_path = Path("src/ui/main_window_backup.py")

    print("🆘 Creating clean version of main_window.py...")

    try:
        # Backup the current file
        if main_window_path.exists():
            with open(main_window_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            print(f"  ✅ Backed up current file to {backup_path}")

        # Create a minimal working version
        clean_content = '''"""
Main Application Window
Main window for the PDF Voice Editor with enhanced draggable functionality
"""

import sys
import json
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QLabel, QToolBar, QStatusBar, QPushButton,
    QComboBox, QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtGui import QAction, QKeySequence, QFont
from PyQt6.QtCore import Qt, pyqtSlot

from ui.pdf_canvas import PDFCanvas
from ui.field_palette import EnhancedFieldPalette
from ui.properties_panel import PropertiesPanel
from models.field_model import FormField
from utils.icon_utils import create_app_icon


class PDFViewerMainWindow(QMainWindow):
    """Main application window with enhanced draggable functionality"""

    def __init__(self):
        super().__init__()
        self.current_pdf_path = None
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PDF Voice Editor - Enhanced with Draggable Fields")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # Create panels
        left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()

        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(center_panel)

        # Set splitter proportions (left panel smaller)
        self.splitter.setSizes([300, 1100])

        # Create UI components
        self.create_toolbar()
        self.create_status_bar()

    def create_left_panel(self) -> QWidget:
        """Create left panel with field palette and properties"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Enhanced field palette with preview and quick actions
        self.field_palette = EnhancedFieldPalette()
        left_layout.addWidget(self.field_palette)

        # Properties panel
        self.properties_panel = PropertiesPanel()
        left_layout.addWidget(self.properties_panel)

        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(350)
        left_widget.setMinimumWidth(250)

        return left_widget

    def create_center_panel(self) -> QWidget:
        """Create center panel with PDF viewer"""
        # Scroll area for PDF canvas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Enhanced PDF canvas with drag support
        self.pdf_canvas = PDFCanvas()
        self.scroll_area.setWidget(self.pdf_canvas)

        return self.scroll_area

    def create_toolbar(self):
        """Create main toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Open action
        open_action = QAction("📁 Open", self)
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

    def create_status_bar(self):
        """Create status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Field information
        self.field_info_label = QLabel("No field selected")
        status_bar.addWidget(self.field_info_label)

        # Operation label
        self.operation_label = QLabel("Ready")
        status_bar.addPermanentWidget(self.operation_label)

    def setup_connections(self):
        """Setup signal connections between components"""
        # Field palette connections - safe calls
        if hasattr(self.field_palette, 'fieldRequested'):
            self.field_palette.fieldRequested.connect(self.create_field_at_center)

        # PDF canvas connections - safe calls
        if hasattr(self.pdf_canvas, 'fieldClicked'):
            self.pdf_canvas.fieldClicked.connect(self.on_field_clicked)
        if hasattr(self.pdf_canvas, 'selectionChanged'):
            self.pdf_canvas.selectionChanged.connect(self.on_selection_changed)

    @pyqtSlot()
    def open_pdf(self):
        """Open PDF file dialog and load selected file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            if self.pdf_canvas.load_pdf(file_path):
                self.current_pdf_path = file_path
                self.statusBar().showMessage(f"Loaded: {Path(file_path).name}", 3000)

    @pyqtSlot(str)
    def create_field_at_center(self, field_type: str):
        """Create a new field at the center of the visible area"""
        center_x = self.scroll_area.width() // 2
        center_y = self.scroll_area.height() // 2

        field = self.pdf_canvas.add_field(field_type, center_x, center_y)
        self.statusBar().showMessage(f"Created {field_type} field", 2000)

    @pyqtSlot(str)
    def on_field_clicked(self, field_id: str):
        """Handle field selection"""
        selected_field = self.pdf_canvas.selected_field
        if selected_field:
            self.properties_panel.show_field_properties(selected_field)
            self.field_info_label.setText(f"Selected: {selected_field.name}")

            # Safe method calls
            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(True)
            if hasattr(self.field_palette, "highlight_field_type"):
                self.field_palette.highlight_field_type(selected_field.type.value)

    @pyqtSlot(object)
    def on_selection_changed(self, field):
        """Handle selection change"""
        if field:
            self.properties_panel.show_field_properties(field)
            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(True)
            if hasattr(self.field_palette, "highlight_field_type"):
                self.field_palette.highlight_field_type(field.type.value)
        else:
            self.properties_panel.show_no_selection()
            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(False)
            if hasattr(self.field_palette, "clear_highlights"):
                self.field_palette.clear_highlights()


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Voice Editor - Enhanced")
    app.setWindowIcon(create_app_icon(32))

    window = PDFViewerMainWindow()
    window.show()

    print("🎉 PDF Voice Editor started!")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
'''

        # Write the clean version
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(clean_content)

        print("✅ Created clean main_window.py")
        print("  📄 Original backed up as main_window_backup.py")
        return True

    except Exception as e:
        print(f"❌ Error creating clean version: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Complete Method Fixer")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    print("Choose fix approach:")
    print("1. Try to fix existing methods")
    print("2. Create clean main_window.py (recommended if many errors)")

    choice = input("Enter choice (1 or 2, default 1): ").strip()

    if choice == "2":
        success = create_clean_main_window()
    else:
        success = fix_all_broken_methods()

    if success:
        # Validate syntax
        if validate_syntax():
            print("\n🎉 All fixes applied successfully!")
            print("\n🎯 Next steps:")
            print("1. Try running: python launch.py")
            print("2. If missing methods errors: python fix_field_palette_missing_methods.py")
        else:
            print("\n⚠️ Syntax errors remain. Consider using option 2 (clean version).")
    else:
        print("\n❌ Fix failed. Consider using option 2 to create a clean version.")

    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())