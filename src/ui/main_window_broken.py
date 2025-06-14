"""
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
from PyQt6.QtGui import QAction, QKeySequence, QFont, QIcon, QPixmap, QColor, QCursor
from PyQt6.QtCore import Qt, pyqtSlot


from ui.pdf_canvas import PDFCanvas
from ui.field_palette import EnhancedFieldPalette
from ui.properties_panel import PropertiesPanel
from models.field_model import FormField
from utils.icon_utils import create_app_icon, create_toolbar_icons

# Optional imports - only import if available
try:
    from core.voice_handler import VoiceHandler, VoiceState
    from training.intent_classifier import IntentClassifier
    VOICE_AVAILABLE = True
except ImportError:
    print("⚠️ Voice recognition not available - continuing without voice features")
    VOICE_AVAILABLE = False

from PyQt6.QtWidgets import QApplication

class PDFViewerMainWindow(QMainWindow):
    """Main application window with enhanced draggable functionality"""

    def _safe_call_field_palette(self, method_name: str, *args, **kwargs):
        """Safely call a method on field_palette if it exists"""
        if hasattr(self.field_palette, method_name):
            method = getattr(self.field_palette, method_name)
            return method(*args, **kwargs)
        return None

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
        self.create_menu_bar()

        # Apply application styling
        self.apply_styling()

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
        """Create main toolbar with file and field operations"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Open action
        open_action = QAction("📁 Open", self)
        open_action.setToolTip("Open PDF file")
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        # Save action
        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save form data")
        save_action.triggered.connect(self.save_form_data)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Navigation
        prev_action = QAction("⬅️ Previous", self)
        prev_action.triggered.connect(self.previous_page)
        toolbar.addAction(prev_action)

        next_action = QAction("➡️ Next", self)
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Zoom
        zoom_out_action = QAction("🔍- Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        zoom_in_action = QAction("🔍+ Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        toolbar.addSeparator()

        # Grid toggle
        self.grid_action = QAction("📐 Grid", self)
        self.grid_action.setCheckable(True)
        self.grid_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_action)

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("PDF Voice Editor - Enhanced")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("PDF Tools")

    # Set application icon if available
    try:
        app.setWindowIcon(create_app_icon(32))
    except:
        pass  # Icon creation might fail, continue without it

    # Create and show main window
    window = PDFViewerMainWindow()
    window.show()

    # Add some sample fields for demonstration if no PDF is loaded
    try:
        if not window.current_pdf_path:
            canvas = window.pdf_canvas
            if hasattr(canvas, 'add_field'):
                canvas.add_field('text', 150, 100)
                canvas.add_field('checkbox', 150, 150)
                canvas.add_field('dropdown', 150, 200)
                canvas.add_field('signature', 150, 250)
            window.update_document_info()
    except:
        pass  # Sample fields creation might fail, continue without them

    print("🎉 Enhanced PDF Voice Editor started!")
    print("Features available:")
    print("  • Drag fields to move them around")
    print("  • Drag resize handles to change size")
    print("  • Use arrow keys for precise movement")
    print("  • Ctrl+D to duplicate selected field")
    print("  • Delete key to remove selected field")
    print("  • Grid snapping for alignment")
    print("  • Form data save/load")

    # Run the application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

