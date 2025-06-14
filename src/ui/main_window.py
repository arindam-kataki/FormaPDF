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

# Fix these imports to use absolute imports (remove leading dots)
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
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)

        # File operations
        open_action = QAction("📁", self)
        open_action.setText("Open")
        open_action.setToolTip("Open PDF file (Ctrl+O)")
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        save_action = QAction("💾", self)
        save_action.setText("Save")
        save_action.setToolTip("Save form data (Ctrl+S)")
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_form_data)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Navigation controls
        prev_action = QAction("⬅️", self)
        prev_action.setText("Previous")
        prev_action.setToolTip("Previous page")
        prev_action.triggered.connect(self.previous_page)
        toolbar.addAction(prev_action)

        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setMinimumWidth(80)
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar.addWidget(self.page_label)

        next_action = QAction("➡️", self)
        next_action.setText("Next")
        next_action.setToolTip("Next page")
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Zoom controls
        zoom_out_action = QAction("🔍-", self)
        zoom_out_action.setText("Zoom Out")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["25%", "50%", "75%", "100%", "125%", "150%", "200%", "300%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setMinimumWidth(80)
        self.zoom_combo.currentTextChanged.connect(self.zoom_changed)
        toolbar.addWidget(self.zoom_combo)

        zoom_in_action = QAction("🔍+", self)
        zoom_in_action.setText("Zoom In")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        toolbar.addSeparator()

        # View options
        self.grid_action = QAction("📐", self)
        self.grid_action.setText("Grid")
        self.grid_action.setToolTip("Toggle grid display")
        self.grid_action.setCheckable(True)
        self.grid_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_action)

        fit_width_action = QAction("↔️", self)
        fit_width_action.setText("Fit Width")
        fit_width_action.setToolTip("Fit page to window width")
        fit_width_action.triggered.connect(self.fit_width)
        toolbar.addAction(fit_width_action)

        toolbar.addSeparator()

        # Voice controls (placeholder for future implementation)
        self.voice_action = QAction("🎤", self)
        self.voice_action.setText("Voice")
        self.voice_action.setToolTip("Toggle voice recognition")
        self.voice_action.setCheckable(True)
        self.voice_action.triggered.connect(self.toggle_voice)
        toolbar.addAction(self.voice_action)

    def create_status_bar(self):
        """Create enhanced status bar with multiple information panels"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Field information
        self.field_info_label = QLabel("No field selected")
        status_bar.addWidget(self.field_info_label)

        # Current operation/cursor position
        self.operation_label = QLabel("Ready")
        status_bar.addPermanentWidget(self.operation_label)

        # Document information
        self.doc_info_label = QLabel("No document loaded")
        status_bar.addPermanentWidget(self.doc_info_label)

        # Helpful hints
        self.hints_label = QLabel("💡 Drag fields to move • Drag handles to resize • Arrow keys for precision")
        status_bar.addPermanentWidget(self.hints_label)

    def create_menu_bar(self):
        """Create comprehensive menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open PDF...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_form_action = QAction("&Save Form Data...", self)
        save_form_action.setShortcut(QKeySequence.StandardKey.Save)
        save_form_action.triggered.connect(self.save_form_data)
        file_menu.addAction(save_form_action)

        load_form_action = QAction("&Load Form Data...", self)
        load_form_action.triggered.connect(self.load_form_data)
        file_menu.addAction(load_form_action)

        file_menu.addSeparator()

        export_action = QAction("&Export PDF...", self)
        export_action.triggered.connect(self.export_pdf)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        duplicate_action = QAction("&Duplicate Field", self)
        duplicate_action.setShortcut(QKeySequence("Ctrl+D"))
        duplicate_action.triggered.connect(self.duplicate_field)
        edit_menu.addAction(duplicate_action)

        delete_action = QAction("&Delete Field", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_field)
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Select &All Fields", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self.select_all_fields)
        edit_menu.addAction(select_all_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        grid_action = QAction("Toggle &Grid", self)
        grid_action.setShortcut(QKeySequence("Ctrl+G"))
        grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(grid_action)

        view_menu.addSeparator()

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        fit_width_action = QAction("&Fit Width", self)
        fit_width_action.triggered.connect(self.fit_width)
        view_menu.addAction(fit_width_action)

        # Fields menu
        fields_menu = menubar.addMenu("&Fields")

        # Alignment submenu
        align_menu = fields_menu.addMenu("&Align")

        align_actions = [
            ("Align &Left", "left"),
            ("Align &Right", "right"),
            ("Align &Top", "top"),
            ("Align &Bottom", "bottom"),
            ("Align &Center Horizontal", "center_h"),
            ("Align &Center Vertical", "center_v")
        ]

        for action_text, alignment in align_actions:
            action = QAction(action_text, self)
            action.triggered.connect(lambda checked, a=alignment: self.align_fields(a))
            align_menu.addAction(action)

        # Distribution submenu
        distribute_menu = fields_menu.addMenu("&Distribute")

        dist_horizontal_action = QAction("Distribute &Horizontally", self)
        dist_horizontal_action.triggered.connect(lambda: self.distribute_fields("horizontal"))
        distribute_menu.addAction(dist_horizontal_action)

        dist_vertical_action = QAction("Distribute &Vertically", self)
        dist_vertical_action.triggered.connect(lambda: self.distribute_fields("vertical"))
        distribute_menu.addAction(dist_vertical_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def apply_styling(self):
        """Apply modern styling to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QToolBar {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                spacing: 3px;
                padding: 5px;
            }
            QToolBar QToolButton {
                padding: 5px;
                margin: 2px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #e9ecef;
            }
            QStatusBar {
                background-color: #ffffff;
                border-top: 1px solid #dee2e6;
            }
            QStatusBar QLabel {
                padding: 2px 8px;
            }
        """)

    def setup_connections(self):
        """Setup signal connections between components"""
        # Field palette connections
        self.field_palette.fieldRequested.connect(self.create_field_at_center)
        self.field_palette.duplicateRequested.connect(self.duplicate_field)
        self.field_palette.deleteRequested.connect(self.delete_field)
        self.field_palette.alignRequested.connect(self.align_fields)

        # PDF canvas connections
        self.pdf_canvas.fieldClicked.connect(self.on_field_clicked)
        self.pdf_canvas.fieldMoved.connect(self.on_field_moved)
        self.pdf_canvas.fieldResized.connect(self.on_field_resized)
        self.pdf_canvas.positionClicked.connect(self.on_position_clicked)
        self.pdf_canvas.selectionChanged.connect(self.on_selection_changed)

        # Properties panel connections
        self.properties_panel.propertyChanged.connect(self.on_property_changed)

    # File operations
    @pyqtSlot()
    def open_pdf(self):
        """Open PDF file dialog and load selected file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            if self.pdf_canvas.load_pdf(file_path):
                self.current_pdf_path = file_path
                self.update_document_info()
                self.statusBar().showMessage(f"Loaded: {Path(file_path).name}", 3000)
            else:
                QMessageBox.critical(self, "Error", "Failed to load PDF file")

    @pyqtSlot()
    def save_form_data(self):
        """Save form field data to JSON file"""
        if not self.pdf_canvas.get_fields_as_objects():
            QMessageBox.information(self, "No Data", "No form fields to save")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Form Data", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                form_data = {
                    'pdf_path': self.current_pdf_path,
                    'page': self.pdf_canvas.current_page,
                    'zoom': self.pdf_canvas.zoom_level,
                    'fields': self.pdf_canvas.form_fields
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(form_data, f, indent=2, ensure_ascii=False)

                self.statusBar().showMessage(f"Form data saved to {Path(file_path).name}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save form data:\n{e}")

    @pyqtSlot()
    def load_form_data(self):
        """Load form field data from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Form Data", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    form_data = json.load(f)

                # Load the PDF if specified and different from current
                pdf_path = form_data.get('pdf_path')
                if pdf_path and pdf_path != self.current_pdf_path:
                    if Path(pdf_path).exists():
                        self.pdf_canvas.load_pdf(pdf_path)
                        self.current_pdf_path = pdf_path

                # Set page and zoom
                if 'page' in form_data:
                    self.pdf_canvas.set_page(form_data['page'])
                if 'zoom' in form_data:
                    self.pdf_canvas.set_zoom(form_data['zoom'])
                    self.zoom_combo.setCurrentText(f"{int(form_data['zoom'] * 100)}%")

                # Load fields
                if 'fields' in form_data:
                    field_manager = self.pdf_canvas.get_field_manager()
                    field_manager.from_dict_list(form_data['fields'])
                    self.pdf_canvas.draw_overlay()

                self.update_document_info()
                self.statusBar().showMessage(f"Form data loaded from {Path(file_path).name}", 3000)

            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load form data:\n{e}")

    @pyqtSlot()
    def export_pdf(self):
        """Export PDF with embedded form fields (placeholder)"""
        QMessageBox.information(
            self, "Export PDF",
            "PDF export functionality will be implemented in a future version.\n"
            "Currently, you can save form data as JSON and reload it later."
        )

    # Navigation operations
    @pyqtSlot()
    def previous_page(self):
        """Navigate to previous page"""
        if self.pdf_canvas.current_page > 0:
            self.pdf_canvas.set_page(self.pdf_canvas.current_page - 1)
            self.update_document_info()

    @pyqtSlot()
    def next_page(self):
        """Navigate to next page"""
        if (self.pdf_canvas.pdf_document and
                self.pdf_canvas.current_page < self.pdf_canvas.pdf_document.page_count - 1):
            self.pdf_canvas.set_page(self.pdf_canvas.current_page + 1)
            self.update_document_info()

    # Zoom operations
    @pyqtSlot()
    def zoom_in(self):
        """Increase zoom level"""
        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = min(current_zoom * 1.25, 5.0)
        self.pdf_canvas.set_zoom(new_zoom)
        self.zoom_combo.setCurrentText(f"{int(new_zoom * 100)}%")

    @pyqtSlot()
    def zoom_out(self):
        """Decrease zoom level"""
        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = max(current_zoom / 1.25, 0.1)
        self.pdf_canvas.set_zoom(new_zoom)
        self.zoom_combo.setCurrentText(f"{int(new_zoom * 100)}%")

    @pyqtSlot(str)
    def zoom_changed(self, text: str):
        """Handle zoom combo box selection"""
        try:
            zoom_percent = int(text.replace('%', ''))
            zoom_level = zoom_percent / 100.0
            self.pdf_canvas.set_zoom(zoom_level)
        except ValueError:
            pass

    @pyqtSlot()
    def fit_width(self):
        """Fit PDF page to window width"""
        if self.pdf_canvas.page_pixmap:
            available_width = self.scroll_area.width() - 40  # Account for scrollbars and margins
            page_width = self.pdf_canvas.page_pixmap.width() / self.pdf_canvas.zoom_level
            new_zoom = available_width / page_width
            self.pdf_canvas.set_zoom(new_zoom)
            self.zoom_combo.setCurrentText(f"{int(new_zoom * 100)}%")

    # View operations
    @pyqtSlot()
    def toggle_grid(self):
        """Toggle grid display"""
        self.pdf_canvas.toggle_grid()
        self.grid_action.setChecked(self.pdf_canvas.show_grid)

    @pyqtSlot()
    def toggle_voice(self):
        """Toggle voice recognition (placeholder)"""
        if self.voice_action.isChecked():
            self.statusBar().showMessage("Voice recognition activated", 2000)
            # TODO: Implement voice recognition
        else:
            self.statusBar().showMessage("Voice recognition deactivated", 2000)

    # Field operations
    @pyqtSlot(str)
    def create_field_at_center(self, field_type: str):
        """Create a new field at the center of the visible area"""
        # Calculate center of visible area
        center_x = self.scroll_area.width() // 2
        center_y = self.scroll_area.height() // 2

        # Convert to canvas coordinates
        scroll_x = self.scroll_area.horizontalScrollBar().value()
        scroll_y = self.scroll_area.verticalScrollBar().value()

        canvas_x = center_x + scroll_x
        canvas_y = center_y + scroll_y

        # Create field
        field = self.pdf_canvas.add_field(field_type, canvas_x, canvas_y)
        self.statusBar().showMessage(f"Created {field_type} field: {field.name}", 2000)

    @pyqtSlot()
    def duplicate_field(self):
        """Duplicate the currently selected field"""
        new_field = self.pdf_canvas.duplicate_selected_field()
        if new_field:
            self.statusBar().showMessage(f"Duplicated field: {new_field.name}", 2000)
        else:
            self.statusBar().showMessage("No field selected to duplicate", 2000)

    @pyqtSlot()
    def delete_field(self):
        """Delete the currently selected field"""
        selected_field = self.pdf_canvas.selected_field
        if selected_field:
            field_name = selected_field.name
            if self.pdf_canvas.delete_selected_field():
                self.statusBar().showMessage(f"Deleted field: {field_name}", 2000)
        else:
            self.statusBar().showMessage("No field selected to delete", 2000)

    @pyqtSlot()
    def select_all_fields(self):
        """Select all fields (placeholder for multiple selection)"""
        self.statusBar().showMessage("Select all fields - Feature coming soon!", 2000)

    @pyqtSlot(str)
    def align_fields(self, alignment: str):
        """Align selected fields"""
        # Placeholder for alignment functionality
        self.statusBar().showMessage(f"Align {alignment} - Feature coming soon!", 2000)

    @pyqtSlot(str)
    def distribute_fields(self, direction: str):
        """Distribute fields evenly"""
        # Placeholder for distribution functionality
        self.statusBar().showMessage(f"Distribute {direction} - Feature coming soon!", 2000)

    # Event handlers for canvas signals
    @pyqtSlot(str)
    def on_field_clicked(self, field_id: str):
        """Handle field selection"""
        selected_field = self.pdf_canvas.selected_field
        if selected_field:
            self.properties_panel.show_field_properties(selected_field)
            self.field_info_label.setText(f"Selected: {selected_field.name} ({selected_field.type.value})")
            self.field_palette.set_field_selected(True)
            self.field_palette.highlight_field_type(selected_field.type.value)

    @pyqtSlot(str, int, int)
    def on_field_moved(self, field_id: str, x: int, y: int):
        """Handle field movement"""
        self.operation_label.setText(f"Moved to ({x}, {y})")
        # Update properties panel
        self.properties_panel.update_field_property(field_id, 'x', x)
        self.properties_panel.update_field_property(field_id, 'y', y)

    @pyqtSlot(str, int, int, int, int)
    def on_field_resized(self, field_id: str, x: int, y: int, width: int, height: int):
        """Handle field resize"""
        self.operation_label.setText(f"Resized to {width}×{height}")
        # Update properties panel
        self.properties_panel.update_field_property(field_id, 'x', x)
        self.properties_panel.update_field_property(field_id, 'y', y)
        self.properties_panel.update_field_property(field_id, 'width', width)
        self.properties_panel.update_field_property(field_id, 'height', height)

    @pyqtSlot(int, int)
    def on_position_clicked(self, x: int, y: int):
        """Handle position click (no field selected)"""
        self.operation_label.setText(f"Position: ({x}, {y})")
        self.field_info_label.setText("No field selected")

    @pyqtSlot(object)
    def on_selection_changed(self, field: Optional[FormField]):
        """Handle selection change"""
        if field:
            self.properties_panel.show_field_properties(field)
            self.field_palette.set_field_selected(True)
            self.field_palette.highlight_field_type(field.type.value)
        else:
            self.properties_panel.show_no_selection()
            self.field_palette.set_field_selected(False)
            self.field_palette.clear_highlights()

    @pyqtSlot(str, str, object)
    def on_property_changed(self, field_id: str, property_name: str, value):
        """Handle property changes from properties panel"""
        # Find and update the field
        field_manager = self.pdf_canvas.get_field_manager()
        field = field_manager.get_field_by_id(field_id)

        if field:
            if hasattr(field, property_name):
                setattr(field, property_name, value)
            else:
                field.properties[property_name] = value

            self.pdf_canvas.draw_overlay()

    def update_document_info(self):
        """Update document information in the UI"""
        if self.pdf_canvas.pdf_document:
            current = self.pdf_canvas.current_page + 1
            total = self.pdf_canvas.pdf_document.page_count
            self.page_label.setText(f"Page {current} of {total}")

            zoom_percent = int(self.pdf_canvas.zoom_level * 100)
            fields_count = len(self.pdf_canvas.get_fields_as_objects())

            self.doc_info_label.setText(f"Zoom: {zoom_percent}% | Fields: {fields_count}")
        else:
            self.page_label.setText("Page 1 of 1")
            self.doc_info_label.setText("No document loaded")

    # Help and information dialogs
    @pyqtSlot()
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table>
        <tr><td><b>Ctrl+O</b></td><td>Open PDF</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save form data</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Duplicate selected field</td></tr>
        <tr><td><b>Delete</b></td><td>Delete selected field</td></tr>
        <tr><td><b>Ctrl+G</b></td><td>Toggle grid</td></tr>
        <tr><td><b>Ctrl++</b></td><td>Zoom in</td></tr>
        <tr><td><b>Ctrl+-</b></td><td>Zoom out</td></tr>
        <tr><td><b>Arrow keys</b></td><td>Move selected field</td></tr>
        <tr><td><b>Shift+Arrow</b></td><td>Move selected field (large steps)</td></tr>
        </table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)

    @pyqtSlot()
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>PDF Voice Editor</h3>
        <p>Enhanced version with draggable form fields</p>
        <p>Version 1.1</p>
        <p>Features:</p>
        <ul>
        <li>Interactive PDF viewing</li>
        <li>Draggable and resizable form fields</li>
        <li>Multiple field types</li>
        <li>Grid snapping</li>
        <li>Keyboard shortcuts</li>
        <li>Form data export/import</li>
        <li>Live property editing</li>
        <li>Voice recognition (coming soon)</li>
        </ul>
        """
        QMessageBox.about(self, "About PDF Voice Editor", about_text)

    def closeEvent(self, event):
        """Handle application close event"""
        # Check if there are unsaved changes
        if self.pdf_canvas.get_fields_as_objects():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have form fields that may not be saved.\n"
                "Do you want to save before closing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_form_data()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("PDF Voice Editor - Enhanced")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("PDF Tools")

    # Set application icon
    app.setWindowIcon(create_app_icon(32))

    # Create and show main window
    window = PDFViewerMainWindow()
    window.show()

    # Add some sample fields for demonstration if no PDF is loaded
    if not window.current_pdf_path:
        canvas = window.pdf_canvas
        canvas.add_field('text', 150, 100)
        canvas.add_field('checkbox', 150, 150)
        canvas.add_field('dropdown', 150, 200)
        canvas.add_field('signature', 150, 250)
        window.update_document_info()

    print("🎉 Enhanced PDF Voice Editor started!")
    print("Features available:")
    print("  • Drag fields to move them around")
    print("  • Drag resize handles to change size")
    print("  • Use arrow keys for precise movement")
    print("  • Ctrl+D to duplicate selected field")
    print("  • Delete key to remove selected field")
    print("  • Grid snapping for alignment")
    print("  • Live property editing")
    print("  • Form data save/load")

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()