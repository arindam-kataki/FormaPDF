"""
PDF Viewer - Complete GUI Application for PDF Voice Editor
Multi-panel interface with PDF display, field creation, and voice integration
Built with PyQt6 and PyMuPDF
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import json

import fitz  # PyMuPDF
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QScrollArea, QLabel, QToolBar, QStatusBar, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QListWidget, QTextEdit, QLineEdit,
    QCheckBox, QSlider, QFileDialog, QMessageBox, QFrame, QGridLayout,
    QTabWidget, QProgressBar
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QRect, QPoint, QSize, QPropertyAnimation,
    QEasingCurve, pyqtSlot
)
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QBrush, QColor, QFont, QAction, QIcon,
    QKeySequence, QPalette
)

from ui.field_palette import ScrollableFieldPalette


class PDFCanvas(QLabel):
    """Custom widget for displaying PDF pages with field overlay"""

    # Signals
    fieldClicked = pyqtSignal(str)  # field_id
    positionClicked = pyqtSignal(int, int)  # x, y coordinates

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("border: 1px solid #ccc; background-color: white;")

        # PDF document and page
        self.pdf_document = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.page_pixmap = None

        # Grid settings
        self.show_grid = False
        self.grid_size = 20

        # Field overlay
        self.form_fields = []
        self.selected_field = None

        # Mouse interaction
        self.setMouseTracking(True)
        self.mouse_pressed = False
        self.drag_start = None

        # Create default "no document" display
        self.show_no_document_message()

    def show_no_document_message(self):
        """Display message when no PDF is loaded"""
        self.setText("No PDF loaded\n\nClick 'Open PDF' or drag & drop a PDF file here")
        self.setStyleSheet("""
            border: 2px dashed #ccc; 
            background-color: #f9f9f9; 
            color: #666;
            font-size: 14px;
            padding: 20px;
        """)

    def load_pdf(self, pdf_path: str) -> bool:
        """Load PDF document"""
        try:
            self.pdf_document = fitz.open(pdf_path)
            self.current_page = 0
            self.zoom_level = 1.0
            self.form_fields = []
            self.selected_field = None

            self.render_page()
            self.setStyleSheet("border: 1px solid #ccc; background-color: white;")

            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load PDF: {e}")
            return False

    def render_page(self):
        """Render current PDF page to pixmap"""
        if not self.pdf_document or self.current_page >= self.pdf_document.page_count:
            return

        try:
            # Get page
            page = self.pdf_document[self.current_page]

            # Create transformation matrix for zoom
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)

            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")

            # Convert to QPixmap
            self.page_pixmap = QPixmap()
            self.page_pixmap.loadFromData(img_data)

            # Set the widget size to match the pixmap size
            pixmap_size = self.page_pixmap.size()
            self.resize(pixmap_size)  # This makes scroll bars appear!

            # Update the displayed pixmap
            self.setPixmap(self.page_pixmap)

            # Draw overlay (grid, fields, etc.)
            self.draw_overlay()

        except Exception as e:
            print(f"Error rendering page: {e}")

    def draw_overlay(self):
        """Draw grid and form fields overlay on PDF"""
        if not self.page_pixmap:
            return

        # Create a copy of the page pixmap to draw on
        overlay_pixmap = self.page_pixmap.copy()
        painter = QPainter(overlay_pixmap)

        # Draw grid if enabled
        if self.show_grid:
            self.draw_grid(painter)

        # Draw form fields
        self.draw_form_fields(painter)

        painter.end()

        # Update display
        self.setPixmap(overlay_pixmap)
        self.resize(overlay_pixmap.size())

    def draw_grid(self, painter: QPainter):
        """Draw grid overlay"""
        pen = QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        width = self.page_pixmap.width()
        height = self.page_pixmap.height()

        # Vertical lines
        for x in range(0, width, self.grid_size):
            painter.drawLine(x, 0, x, height)

        # Horizontal lines
        for y in range(0, height, self.grid_size):
            painter.drawLine(0, y, width, y)

    def draw_form_fields(self, painter: QPainter):
        """Draw form fields overlay"""
        for field in self.form_fields:
            self.draw_single_field(painter, field)

    def draw_single_field(self, painter: QPainter, field: Dict):
        """Draw a single form field"""
        x, y, w, h = field['x'], field['y'], field['width'], field['height']
        field_type = field['type']

        # Select colors based on selection state
        if field == self.selected_field:
            border_color = QColor(0, 120, 215)  # Blue selection
            bg_color = QColor(0, 120, 215, 30)  # Light blue background
            pen_width = 2
        else:
            border_color = QColor(100, 100, 100)  # Gray border
            bg_color = QColor(255, 255, 255, 150)  # Light background
            pen_width = 1

        # Draw field background
        painter.fillRect(x, y, w, h, bg_color)

        # Draw field border
        pen = QPen(border_color, pen_width)
        painter.setPen(pen)
        painter.drawRect(x, y, w, h)

        # Draw field type indicator
        self.draw_field_type_indicator(painter, field)

        # Draw field name
        if field.get('name'):
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(x + 2, y - 2, field['name'])

    def draw_field_type_indicator(self, painter: QPainter, field: Dict):
        """Draw indicator showing field type"""
        x, y, w, h = field['x'], field['y'], field['width'], field['height']
        field_type = field['type']

        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", min(h - 4, 12)))

        if field_type == 'text':
            painter.drawText(x + 5, y + h // 2 + 4, "abc")
        elif field_type == 'checkbox':
            # Draw checkbox
            checkbox_size = min(w - 4, h - 4, 16)
            checkbox_x = x + (w - checkbox_size) // 2
            checkbox_y = y + (h - checkbox_size) // 2
            painter.drawRect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)
            if field.get('checked', False):
                # Draw checkmark
                painter.drawLine(checkbox_x + 3, checkbox_y + checkbox_size // 2,
                                 checkbox_x + checkbox_size // 2, checkbox_y + checkbox_size - 3)
                painter.drawLine(checkbox_x + checkbox_size // 2, checkbox_y + checkbox_size - 3,
                                 checkbox_x + checkbox_size - 3, checkbox_y + 3)
        elif field_type == 'dropdown':
            painter.drawText(x + 5, y + h // 2 + 4, "▼")
        elif field_type == 'signature':
            painter.drawText(x + 5, y + h // 2 + 4, "✒️")

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed = True
            self.drag_start = event.position().toPoint()

            # Check if clicked on a field
            clicked_field = self.get_field_at_position(event.position().toPoint())

            if clicked_field:
                self.selected_field = clicked_field
                self.fieldClicked.emit(clicked_field['id'])
            else:
                self.selected_field = None
                # Emit position for new field creation
                self.positionClicked.emit(
                    int(event.position().x()),
                    int(event.position().y())
                )

            self.draw_overlay()

    def get_field_at_position(self, pos: QPoint) -> Optional[Dict]:
        """Get form field at given position"""
        for field in self.form_fields:
            if (field['x'] <= pos.x() <= field['x'] + field['width'] and
                    field['y'] <= pos.y() <= field['y'] + field['height']):
                return field
        return None

    def add_field(self, field_type: str, x: int, y: int, width: int = 100, height: int = 25):
        """Add a new form field"""
        field_id = f"{field_type}_{len(self.form_fields) + 1}"

        field = {
            'id': field_id,
            'type': field_type,
            'name': field_id,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'required': False,
            'value': '',
            'properties': {}
        }

        self.form_fields.append(field)
        self.selected_field = field
        self.draw_overlay()

        return field

    def delete_selected_field(self):
        """Delete currently selected field"""
        if self.selected_field and self.selected_field in self.form_fields:
            self.form_fields.remove(self.selected_field)
            self.selected_field = None
            self.draw_overlay()

    def set_zoom(self, zoom_level: float):
        """Set zoom level and re-render page"""
        self.zoom_level = zoom_level
        self.render_page()

    def set_page(self, page_number: int):
        """Set current page and re-render"""
        if self.pdf_document and 0 <= page_number < self.pdf_document.page_count:
            self.current_page = page_number
            self.form_fields = []  # Clear fields when changing pages
            self.selected_field = None
            self.render_page()

    def toggle_grid(self):
        """Toggle grid display"""
        self.show_grid = not self.show_grid
        self.draw_overlay()


class FieldPalette(QWidget):
    """Widget containing draggable field types"""

    fieldRequested = pyqtSignal(str)  # field_type

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Form Fields")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Field buttons
        field_types = [
            ("📝 Text Field", "text"),
            ("☑️ Checkbox", "checkbox"),
            ("🔘 Radio Button", "radio"),
            ("📋 Dropdown", "dropdown"),
            ("✏️ Signature", "signature"),
            ("📅 Date Field", "date"),
            ("🔘 Button", "button")
        ]

        for label, field_type in field_types:
            btn = QPushButton(label)
            btn.setMinimumHeight(35)
            btn.clicked.connect(lambda checked, ft=field_type: self.fieldRequested.emit(ft))
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)


class PropertiesPanel(QWidget):
    """Widget for editing field properties"""

    def __init__(self):
        super().__init__()
        self.current_field = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Properties")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Properties form
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout()
        self.properties_widget.setLayout(self.properties_layout)

        layout.addWidget(self.properties_widget)
        layout.addStretch()

        self.setLayout(layout)
        self.show_no_selection()

    def show_no_selection(self):
        """Show message when no field is selected"""
        self.clear_properties()

        label = QLabel("No field selected\n\nClick on a field to edit properties")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #666; font-style: italic;")
        self.properties_layout.addWidget(label)

    def clear_properties(self):
        """Clear all property widgets"""
        while self.properties_layout.count():
            child = self.properties_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_field_properties(self, field: Dict):
        """Show properties for selected field"""
        self.current_field = field
        self.clear_properties()

        # Field name
        name_label = QLabel("Field Name:")
        self.name_edit = QLineEdit(field.get('name', ''))
        self.properties_layout.addWidget(name_label)
        self.properties_layout.addWidget(self.name_edit)

        # Field type
        type_label = QLabel(f"Type: {field['type'].title()}")
        type_label.setStyleSheet("font-weight: bold;")
        self.properties_layout.addWidget(type_label)

        # Position and size
        pos_group = QGroupBox("Position & Size")
        pos_layout = QGridLayout()

        pos_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 2000)
        self.x_spin.setValue(field['x'])
        pos_layout.addWidget(self.x_spin, 0, 1)

        pos_layout.addWidget(QLabel("Y:"), 1, 0)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 2000)
        self.y_spin.setValue(field['y'])
        pos_layout.addWidget(self.y_spin, 1, 1)

        pos_layout.addWidget(QLabel("Width:"), 0, 2)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 500)
        self.width_spin.setValue(field['width'])
        pos_layout.addWidget(self.width_spin, 0, 3)

        pos_layout.addWidget(QLabel("Height:"), 1, 2)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 200)
        self.height_spin.setValue(field['height'])
        pos_layout.addWidget(self.height_spin, 1, 3)

        pos_group.setLayout(pos_layout)
        self.properties_layout.addWidget(pos_group)

        # Required checkbox
        self.required_check = QCheckBox("Required Field")
        self.required_check.setChecked(field.get('required', False))
        self.properties_layout.addWidget(self.required_check)

        # Field-specific properties
        if field['type'] == 'text':
            self.add_text_field_properties(field)
        elif field['type'] == 'checkbox':
            self.add_checkbox_properties(field)
        elif field['type'] == 'dropdown':
            self.add_dropdown_properties(field)

    def add_text_field_properties(self, field: Dict):
        """Add text field specific properties"""
        text_group = QGroupBox("Text Properties")
        text_layout = QVBoxLayout()

        # Default value
        text_layout.addWidget(QLabel("Default Value:"))
        self.default_value_edit = QLineEdit(field.get('value', ''))
        text_layout.addWidget(self.default_value_edit)

        # Multiline
        self.multiline_check = QCheckBox("Multiline")
        self.multiline_check.setChecked(field.get('multiline', False))
        text_layout.addWidget(self.multiline_check)

        text_group.setLayout(text_layout)
        self.properties_layout.addWidget(text_group)

    def add_checkbox_properties(self, field: Dict):
        """Add checkbox specific properties"""
        checkbox_group = QGroupBox("Checkbox Properties")
        checkbox_layout = QVBoxLayout()

        # Checked by default
        self.checked_check = QCheckBox("Checked by default")
        self.checked_check.setChecked(field.get('checked', False))
        checkbox_layout.addWidget(self.checked_check)

        checkbox_group.setLayout(checkbox_layout)
        self.properties_layout.addWidget(checkbox_group)

    def add_dropdown_properties(self, field: Dict):
        """Add dropdown specific properties"""
        dropdown_group = QGroupBox("Dropdown Properties")
        dropdown_layout = QVBoxLayout()

        dropdown_layout.addWidget(QLabel("Options (one per line):"))
        self.options_edit = QTextEdit()
        self.options_edit.setMaximumHeight(100)
        options = field.get('options', ['Option 1', 'Option 2', 'Option 3'])
        self.options_edit.setPlainText('\n'.join(options))
        dropdown_layout.addWidget(self.options_edit)

        dropdown_group.setLayout(dropdown_layout)
        self.properties_layout.addWidget(dropdown_group)


class VoiceStatusWidget(QWidget):
    """Widget showing voice recognition status"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        self.status_icon = QLabel("🎤")
        self.status_text = QLabel("Voice: Ready")
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setMaximumWidth(100)
        self.confidence_bar.setVisible(False)

        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_text)
        layout.addWidget(self.confidence_bar)
        layout.addStretch()

        self.setLayout(layout)

    def set_status(self, status: str, confidence: float = None):
        """Update voice status"""
        status_map = {
            'ready': ('🎤', 'Voice: Ready'),
            'listening': ('🎙️', 'Voice: Listening...'),
            'processing': ('🔄', 'Voice: Processing...'),
            'command': ('✅', 'Voice: Command received'),
            'error': ('❌', 'Voice: Error')
        }

        icon, text = status_map.get(status, ('🎤', f'Voice: {status}'))
        self.status_icon.setText(icon)
        self.status_text.setText(text)

        if confidence is not None:
            self.confidence_bar.setValue(int(confidence * 100))
            self.confidence_bar.setVisible(True)
        else:
            self.confidence_bar.setVisible(False)


class PDFViewerMainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.current_pdf_path = None
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        self.setWindowTitle("PDF Voice Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # Left panel (field palette + properties)
        left_panel = self.create_left_panel()
        self.splitter.addWidget(left_panel)

        # Center panel (PDF viewer)
        center_panel = self.create_center_panel()
        self.splitter.addWidget(center_panel)

        # Set splitter proportions
        self.splitter.setSizes([250, 950])

        # Create toolbar
        self.create_toolbar()

        # Create status bar
        self.create_status_bar()

        # Create menu bar
        self.create_menu_bar()

    def create_left_panel(self):
        """Create left panel with field palette and properties"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Field palette
        self.field_palette = ScrollableFieldPalette()
        left_layout.addWidget(self.field_palette)

        # Properties panel
        self.properties_panel = PropertiesPanel()
        left_layout.addWidget(self.properties_panel)

        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(300)
        left_widget.setMinimumWidth(200)

        return left_widget

    def create_center_panel(self):
        """Create center panel with PDF viewer"""
        # Scroll area for PDF canvas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # PDF canvas
        self.pdf_canvas = PDFCanvas()
        self.scroll_area.setWidget(self.pdf_canvas)

        return self.scroll_area

    def create_toolbar(self):
        """Create main toolbar"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # File operations
        open_action = QAction("📁 Open", self)
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        save_action = QAction("💾 Save", self)
        save_action.triggered.connect(self.save_pdf)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Navigation
        prev_action = QAction("⬅️", self)
        prev_action.triggered.connect(self.previous_page)
        toolbar.addAction(prev_action)

        self.page_label = QLabel("Page 1 of 1")
        toolbar.addWidget(self.page_label)

        next_action = QAction("➡️", self)
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Zoom controls
        zoom_out_action = QAction("🔍-", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["25%", "50%", "75%", "100%", "125%", "150%", "200%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self.zoom_changed)
        toolbar.addWidget(self.zoom_combo)

        zoom_in_action = QAction("🔍+", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        toolbar.addSeparator()

        # View options
        self.grid_action = QAction("📐 Grid", self)
        self.grid_action.setCheckable(True)
        self.grid_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_action)

        toolbar.addSeparator()

        # Voice controls
        self.voice_action = QAction("🎤 Voice", self)
        self.voice_action.setCheckable(True)
        self.voice_action.triggered.connect(self.toggle_voice)
        toolbar.addAction(self.voice_action)

    def create_status_bar(self):
        """Create status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Voice status widget
        self.voice_status = VoiceStatusWidget()
        status_bar.addWidget(self.voice_status)

        # Document info
        self.doc_info_label = QLabel("No document loaded")
        status_bar.addPermanentWidget(self.doc_info_label)

        # Position info
        self.position_label = QLabel("Position: (0, 0)")
        status_bar.addPermanentWidget(self.position_label)

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open PDF", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_pdf)
        file_menu.addAction(save_action)

        export_action = QAction("Export", self)
        export_action.triggered.connect(self.export_pdf)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(lambda: None)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(lambda: None)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        delete_action = QAction("Delete Field", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_selected_field)
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menubar.addMenu("View")

        grid_action = QAction("Toggle Grid", self)
        grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(grid_action)

        fit_width_action = QAction("Fit Width", self)
        fit_width_action.triggered.connect(self.fit_width)
        view_menu.addAction(fit_width_action)

        fit_page_action = QAction("Fit Page", self)
        fit_page_action.triggered.connect(self.fit_page)
        view_menu.addAction(fit_page_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        voice_settings_action = QAction("Voice Settings", self)
        voice_settings_action.triggered.connect(self.voice_settings)
        tools_menu.addAction(voice_settings_action)

        form_properties_action = QAction("Form Properties", self)
        form_properties_action.triggered.connect(self.form_properties)
        tools_menu.addAction(form_properties_action)

    def setup_connections(self):
        """Setup signal connections"""
        # Field palette connections
        self.field_palette.fieldRequested.connect(self.create_field_at_center)

        # PDF canvas connections
        self.pdf_canvas.fieldClicked.connect(self.on_field_clicked)
        self.pdf_canvas.positionClicked.connect(self.on_position_clicked)

    # Slot implementations
    def open_pdf(self):
        """Open PDF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )

        if file_path:
            if self.pdf_canvas.load_pdf(file_path):
                self.current_pdf_path = file_path
                self.update_document_info()
                self.statusBar().showMessage(f"Loaded: {Path(file_path).name}", 3000)

    def save_pdf(self):
        """Save PDF with form fields"""
        if not self.current_pdf_path:
            QMessageBox.warning(self, "Warning", "No PDF loaded to save")
            return

        # Implementation for saving PDF with fields
        self.statusBar().showMessage("PDF saved", 2000)

    def export_pdf(self):
        """Export PDF"""
        # Implementation for PDF export
        pass

    def previous_page(self):
        """Go to previous page"""
        if self.pdf_canvas.current_page > 0:
            self.pdf_canvas.set_page(self.pdf_canvas.current_page - 1)
            self.update_document_info()

    def next_page(self):
        """Go to next page"""
        if (self.pdf_canvas.pdf_document and
                self.pdf_canvas.current_page < self.pdf_canvas.pdf_document.page_count - 1):
            self.pdf_canvas.set_page(self.pdf_canvas.current_page + 1)
            self.update_document_info()

    def zoom_in(self):
        """Zoom in"""
        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = min(current_zoom * 1.25, 4.0)
        self.pdf_canvas.set_zoom(new_zoom)
        self.zoom_combo.setCurrentText(f"{int(new_zoom * 100)}%")

    def zoom_out(self):
        """Zoom out"""
        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = max(current_zoom / 1.25, 0.25)
        self.pdf_canvas.set_zoom(new_zoom)
        self.zoom_combo.setCurrentText(f"{int(new_zoom * 100)}%")

    def zoom_changed(self, text: str):
        """Handle zoom combo box change"""
        try:
            zoom_percent = int(text.replace('%', ''))
            zoom_level = zoom_percent / 100.0
            self.pdf_canvas.set_zoom(zoom_level)
        except ValueError:
            pass

    def toggle_grid(self):
        """Toggle grid display"""
        self.pdf_canvas.toggle_grid()
        self.grid_action.setChecked(self.pdf_canvas.show_grid)

    def toggle_voice(self):
        """Toggle voice recognition"""
        # Implementation for voice toggle
        if self.voice_action.isChecked():
            self.voice_status.set_status('listening')
        else:
            self.voice_status.set_status('ready')

    def fit_width(self):
        """Fit PDF to window width"""
        # Implementation for fit width
        pass

    def fit_page(self):
        """Fit PDF page to window"""
        # Implementation for fit page
        pass

    def voice_settings(self):
        """Open voice settings dialog"""
        QMessageBox.information(self, "Voice Settings", "Voice settings dialog would open here")

    def form_properties(self):
        """Open form properties dialog"""
        QMessageBox.information(self, "Form Properties", "Form properties dialog would open here")

    def delete_selected_field(self):
        """Delete currently selected field"""
        self.pdf_canvas.delete_selected_field()
        self.properties_panel.show_no_selection()

    def create_field_at_center(self, field_type: str):
        """Create field at center of visible area"""
        # Get center of scroll area
        center_x = self.scroll_area.width() // 2
        center_y = self.scroll_area.height() // 2

        # Create field
        field = self.pdf_canvas.add_field(field_type, center_x, center_y)
        self.properties_panel.show_field_properties(field)

    def on_field_clicked(self, field_id: str):
        """Handle field selection"""
        # Find field by ID
        selected_field = None
        for field in self.pdf_canvas.form_fields:
            if field['id'] == field_id:
                selected_field = field
                break

        if selected_field:
            self.properties_panel.show_field_properties(selected_field)

    def on_position_clicked(self, x: int, y: int):
        """Handle position click (for creating fields)"""
        self.position_label.setText(f"Position: ({x}, {y})")
        self.properties_panel.show_no_selection()

    def update_document_info(self):
        """Update document information in UI"""
        if self.pdf_canvas.pdf_document:
            current = self.pdf_canvas.current_page + 1
            total = self.pdf_canvas.pdf_document.page_count
            self.page_label.setText(f"Page {current} of {total}")

            zoom_percent = int(self.pdf_canvas.zoom_level * 100)
            fields_count = len(self.pdf_canvas.form_fields)

            self.doc_info_label.setText(
                f"Zoom: {zoom_percent}% | Fields: {fields_count}"
            )
        else:
            self.page_label.setText("Page 1 of 1")
            self.doc_info_label.setText("No document loaded")


def main():
    """Run the PDF viewer application"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("PDF Voice Editor")
    app.setApplicationVersion("1.0")

    # Create and show main window
    window = PDFViewerMainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()