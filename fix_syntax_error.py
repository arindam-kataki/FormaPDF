#!/usr/bin/env python3
"""
Fix Encoding and Syntax Issues in main_window.py
Handles encoding problems and creates a clean working version
"""

import os
import sys
from pathlib import Path


def read_file_safely(filepath):
    """Read a file with multiple encoding attempts"""
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']

    for encoding in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"  ✅ Successfully read file with {encoding} encoding")
            return content, encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  ⚠️ Error with {encoding}: {e}")
            continue

    print("  ❌ Could not read file with any encoding")
    return None, None


def create_clean_main_window():
    """Create a completely clean main_window.py file"""

    main_window_path = Path("src/ui/main_window.py")
    backup_path = Path("src/ui/main_window_broken.py")

    print("🔧 Creating clean main_window.py...")

    try:
        # Backup the problematic file if it exists
        if main_window_path.exists():
            # Try to read and backup the current file
            content, encoding = read_file_safely(main_window_path)
            if content:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Backed up current file to {backup_path}")
            else:
                # If we can't read it, just rename it
                import shutil
                shutil.move(str(main_window_path), str(backup_path))
                print(f"  ✅ Moved problematic file to {backup_path}")

        # Create a clean, working main_window.py
        clean_content = '''"""
Main Application Window
Clean working version of the PDF Voice Editor main window
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

# Safe imports with fallbacks
try:
    from ui.pdf_canvas import PDFCanvas
    PDF_CANVAS_AVAILABLE = True
except ImportError:
    print("Warning: PDFCanvas not available")
    PDFCanvas = None
    PDF_CANVAS_AVAILABLE = False

try:
    from ui.field_palette import EnhancedFieldPalette
    FIELD_PALETTE_AVAILABLE = True
except ImportError:
    print("Warning: FieldPalette not available")
    EnhancedFieldPalette = None
    FIELD_PALETTE_AVAILABLE = False

try:
    from ui.properties_panel import PropertiesPanel
    PROPERTIES_PANEL_AVAILABLE = True
except ImportError:
    print("Warning: PropertiesPanel not available")
    PropertiesPanel = None
    PROPERTIES_PANEL_AVAILABLE = False

try:
    from models.field_model import FormField
    FIELD_MODEL_AVAILABLE = True
except ImportError:
    print("Warning: FormField model not available")
    FormField = None
    FIELD_MODEL_AVAILABLE = False

try:
    from utils.icon_utils import create_app_icon
    ICON_UTILS_AVAILABLE = True
except ImportError:
    print("Warning: Icon utils not available")
    create_app_icon = None
    ICON_UTILS_AVAILABLE = False


class PDFViewerMainWindow(QMainWindow):
    """Main application window with safe fallbacks"""

    def __init__(self):
        super().__init__()
        self.current_pdf_path = None
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PDF Voice Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
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
        self.splitter.setSizes([300, 900])

        # Create UI components
        self.create_toolbar()
        self.create_status_bar()

    def create_left_panel(self) -> QWidget:
        """Create left panel with field palette and properties"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Field palette (with fallback)
        if FIELD_PALETTE_AVAILABLE and EnhancedFieldPalette:
            self.field_palette = EnhancedFieldPalette()
            left_layout.addWidget(self.field_palette)
        else:
            # Fallback widget
            self.field_palette = QLabel("Field Palette\\n(Not Available)")
            self.field_palette.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.field_palette.setStyleSheet("border: 1px solid #ccc; padding: 20px;")
            left_layout.addWidget(self.field_palette)

        # Properties panel (with fallback)
        if PROPERTIES_PANEL_AVAILABLE and PropertiesPanel:
            self.properties_panel = PropertiesPanel()
            left_layout.addWidget(self.properties_panel)
        else:
            # Fallback widget
            self.properties_panel = QLabel("Properties Panel\\n(Not Available)")
            self.properties_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.properties_panel.setStyleSheet("border: 1px solid #ccc; padding: 20px;")
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

        # PDF canvas (with fallback)
        if PDF_CANVAS_AVAILABLE and PDFCanvas:
            self.pdf_canvas = PDFCanvas()
        else:
            # Fallback widget
            self.pdf_canvas = QLabel(
                "PDF Canvas Not Available\\n\\n"
                "Some modules are missing.\\n"
                "The application is running in limited mode.\\n\\n"
                "To fix this:\\n"
                "1. Ensure all Python files are present\\n"
                "2. Run the fix scripts\\n"
                "3. Check imports"
            )
            self.pdf_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pdf_canvas.setStyleSheet("""
                border: 2px dashed #ccc; 
                background-color: #f9f9f9; 
                color: #666;
                font-size: 14px;
                padding: 40px;
            """)

        self.scroll_area.setWidget(self.pdf_canvas)
        return self.scroll_area

    def create_toolbar(self):
        """Create main toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Open PDF action
        open_action = QAction("📁 Open PDF", self)
        open_action.setToolTip("Open PDF file")
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        # Save action
        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save form data")
        save_action.triggered.connect(self.save_form_data)
        toolbar.addAction(save_action)

        # Separator
        toolbar.addSeparator()

        # Info action
        info_action = QAction("ℹ️ Info", self)
        info_action.setToolTip("Show application info")
        info_action.triggered.connect(self.show_info)
        toolbar.addAction(info_action)

    def create_status_bar(self):
        """Create status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Status label
        self.field_info_label = QLabel("Ready")
        status_bar.addWidget(self.field_info_label)

        # Module status
        missing_modules = []
        if not PDF_CANVAS_AVAILABLE:
            missing_modules.append("PDFCanvas")
        if not FIELD_PALETTE_AVAILABLE:
            missing_modules.append("FieldPalette")
        if not PROPERTIES_PANEL_AVAILABLE:
            missing_modules.append("PropertiesPanel")

        if missing_modules:
            module_status = QLabel(f"Missing: {', '.join(missing_modules)}")
            module_status.setStyleSheet("color: orange;")
            status_bar.addPermanentWidget(module_status)
        else:
            status_bar.addPermanentWidget(QLabel("All modules loaded"))

    def setup_connections(self):
        """Setup signal connections safely"""
        try:
            # Only connect signals if the objects have the required methods
            if hasattr(self.field_palette, 'fieldRequested'):
                self.field_palette.fieldRequested.connect(self.create_field_at_center)

            if hasattr(self.pdf_canvas, 'fieldClicked'):
                self.pdf_canvas.fieldClicked.connect(self.on_field_clicked)

            if hasattr(self.pdf_canvas, 'selectionChanged'):
                self.pdf_canvas.selectionChanged.connect(self.on_selection_changed)

            if hasattr(self.properties_panel, 'propertyChanged'):
                self.properties_panel.propertyChanged.connect(self.on_property_changed)

        except Exception as e:
            print(f"Warning: Some signal connections failed: {e}")

    @pyqtSlot()
    def open_pdf(self):
        """Open PDF file dialog and load selected file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            try:
                if hasattr(self.pdf_canvas, 'load_pdf'):
                    if self.pdf_canvas.load_pdf(file_path):
                        self.current_pdf_path = file_path
                        self.statusBar().showMessage(f"Loaded: {Path(file_path).name}", 3000)
                        self.field_info_label.setText(f"Loaded: {Path(file_path).name}")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to load PDF file")
                else:
                    # Fallback - just show the selected file
                    self.current_pdf_path = file_path
                    self.field_info_label.setText(f"Selected: {Path(file_path).name}")
                    QMessageBox.information(
                        self, "Info", 
                        f"PDF selected: {Path(file_path).name}\\n\\n"
                        "PDF viewing not fully available in current mode.\\n"
                        "Fix missing modules to enable full functionality."
                    )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error opening PDF: {e}")

    @pyqtSlot()
    def save_form_data(self):
        """Save form field data"""
        if not self.current_pdf_path:
            QMessageBox.information(self, "No PDF", "Please open a PDF file first")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Form Data", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                # Create basic form data
                form_data = {
                    'pdf_path': self.current_pdf_path,
                    'timestamp': str(Path().resolve()),
                    'status': 'saved_in_limited_mode'
                }

                # Add field data if available
                if hasattr(self.pdf_canvas, 'get_fields_as_objects'):
                    try:
                        fields = self.pdf_canvas.get_fields_as_objects()
                        form_data['fields'] = [field.to_dict() for field in fields]
                        form_data['field_count'] = len(fields)
                    except:
                        form_data['fields'] = []
                        form_data['field_count'] = 0
                else:
                    form_data['fields'] = []
                    form_data['field_count'] = 0

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(form_data, f, indent=2, ensure_ascii=False)

                self.statusBar().showMessage(f"Saved to {Path(file_path).name}", 3000)

            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save: {e}")

    @pyqtSlot()
    def show_info(self):
        """Show application information"""
        info_text = f"""
        <h3>PDF Voice Editor</h3>
        <p><b>Status:</b> Running</p>

        <p><b>Module Status:</b></p>
        <ul>
        <li>PDF Canvas: {'✅' if PDF_CANVAS_AVAILABLE else '❌'}</li>
        <li>Field Palette: {'✅' if FIELD_PALETTE_AVAILABLE else '❌'}</li>
        <li>Properties Panel: {'✅' if PROPERTIES_PANEL_AVAILABLE else '❌'}</li>
        <li>Field Model: {'✅' if FIELD_MODEL_AVAILABLE else '❌'}</li>
        <li>Icon Utils: {'✅' if ICON_UTILS_AVAILABLE else '❌'}</li>
        </ul>

        <p><b>Current PDF:</b> {self.current_pdf_path or 'None'}</p>

        {'<p><b>Note:</b> Some modules are missing. Run fix scripts to enable full functionality.</p>' if not all([PDF_CANVAS_AVAILABLE, FIELD_PALETTE_AVAILABLE, PROPERTIES_PANEL_AVAILABLE]) else ''}
        """

        QMessageBox.information(self, "Application Info", info_text)

    # Placeholder methods for signal connections
    @pyqtSlot(str)
    def create_field_at_center(self, field_type: str):
        """Create field at center (placeholder)"""
        self.statusBar().showMessage(f"Field creation requested: {field_type}", 2000)

    @pyqtSlot(str)
    def on_field_clicked(self, field_id: str):
        """Handle field click (placeholder)"""
        self.statusBar().showMessage(f"Field clicked: {field_id}", 2000)

    @pyqtSlot(object)
    def on_selection_changed(self, field):
        """Handle selection change (placeholder)"""
        self.statusBar().showMessage("Selection changed", 2000)

    @pyqtSlot(str, str, object)
    def on_property_changed(self, field_id: str, property_name: str, value):
        """Handle property change (placeholder)"""
        self.statusBar().showMessage(f"Property changed: {property_name}", 2000)


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("PDF Voice Editor")
    app.setApplicationVersion("1.1")

    # Set application icon if available
    if ICON_UTILS_AVAILABLE and create_app_icon:
        try:
            app.setWindowIcon(create_app_icon(32))
        except Exception:
            pass  # Continue without icon if it fails

    # Create and show main window
    window = PDFViewerMainWindow()
    window.show()

    print("🎉 PDF Voice Editor started!")
    if not all([PDF_CANVAS_AVAILABLE, FIELD_PALETTE_AVAILABLE, PROPERTIES_PANEL_AVAILABLE]):
        print("⚠️  Running in limited mode - some modules are missing")
        print("   Run fix scripts to enable full functionality")
    else:
        print("✅ All modules loaded successfully")

    # Run the application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
'''

        # Write the clean version with explicit UTF-8 encoding
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(clean_content)

        print("✅ Created clean main_window.py with UTF-8 encoding")

        # Validate the new file
        try:
            with open(main_window_path, 'r', encoding='utf-8') as f:
                test_content = f.read()
            compile(test_content, main_window_path, 'exec')
            print("✅ New file has valid Python syntax")
            return True
        except Exception as e:
            print(f"❌ Error validating new file: {e}")
            return False

    except Exception as e:
        print(f"❌ Error creating clean file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Encoding & Syntax Fixer")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    main_window_path = Path("src/ui/main_window.py")

    if main_window_path.exists():
        print("📄 Checking current main_window.py...")
        content, encoding = read_file_safely(main_window_path)

        if content is None:
            print("❌ Cannot read current file due to encoding issues")
            print("🔧 Will create a clean version instead")
        else:
            print(f"📄 Current file read successfully with {encoding} encoding")
            print(f"📊 File size: {len(content)} characters")

    # Create clean version
    if create_clean_main_window():
        print("\\n🎉 Successfully created clean main_window.py!")
        print("\\n🎯 Next steps:")
        print("1. Try running: python launch.py")
        print("2. The application should now start")
        print("3. If modules are missing, run the appropriate fix scripts")
        return 0
    else:
        print("\\n❌ Failed to create clean version")
        return 1


if __name__ == "__main__":
    sys.exit(main())