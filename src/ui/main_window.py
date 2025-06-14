"""
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
        self.setup_scroll_shortcuts()
        self.enable_smooth_scrolling()

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
            self.field_palette = QLabel("Field Palette\n(Not Available)")
            self.field_palette.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.field_palette.setStyleSheet("border: 1px solid #ccc; padding: 20px;")
            left_layout.addWidget(self.field_palette)

        # Properties panel (with fallback)
        if PROPERTIES_PANEL_AVAILABLE and PropertiesPanel:
            self.properties_panel = PropertiesPanel()
            left_layout.addWidget(self.properties_panel)
        else:
            # Fallback widget
            self.properties_panel = QLabel("Properties Panel\n(Not Available)")
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
                # Enhanced scroll area configuration
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Configure scroll bars
        from PyQt6.QtCore import Qt
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Configure smooth scrolling via scroll bar settings
        v_scrollbar = self.scroll_area.verticalScrollBar()
        h_scrollbar = self.scroll_area.horizontalScrollBar()

        if v_scrollbar:
            v_scrollbar.setSingleStep(10)
            v_scrollbar.setPageStep(100)
        if h_scrollbar:
            h_scrollbar.setSingleStep(10)
            h_scrollbar.setPageStep(100)

self.scroll_area.setWidget(self.pdf_canvas)
        return self.scroll_area

    def create_toolbar(self):
        """Create complete toolbar with page jump and zoom controls"""
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

        # Navigation controls with page input
        prev_action = QAction("⬅️", self)
        prev_action.setToolTip("Previous page")
        prev_action.triggered.connect(self.previous_page)
        toolbar.addAction(prev_action)

        # Page input control
        from PyQt6.QtWidgets import QSpinBox, QLabel
        page_label = QLabel("Page:")
        toolbar.addWidget(page_label)

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)  # Will be updated when PDF loads
        self.page_spinbox.setValue(1)
        self.page_spinbox.setToolTip("Jump to page number")
        self.page_spinbox.valueChanged.connect(self.jump_to_page)
        self.page_spinbox.setMinimumWidth(60)
        toolbar.addWidget(self.page_spinbox)

        # Page count label
        self.page_count_label = QLabel("of 1")
        self.page_count_label.setStyleSheet("color: #666; margin-right: 8px;")
        toolbar.addWidget(self.page_count_label)

        next_action = QAction("➡️", self)
        next_action.setToolTip("Next page")
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Zoom controls with percentage selector
        zoom_out_action = QAction("🔍-", self)
        zoom_out_action.setToolTip("Zoom out")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        # Zoom percentage dropdown
        from PyQt6.QtWidgets import QComboBox
        zoom_label = QLabel("Zoom:")
        toolbar.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.setEditable(True)
        zoom_levels = ["25%", "50%", "75%", "100%", "125%", "150%", "200%", "300%", "400%", "Fit Width", "Fit Page"]
        self.zoom_combo.addItems(zoom_levels)
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setToolTip("Set zoom level")
        self.zoom_combo.currentTextChanged.connect(self.set_zoom_level)
        self.zoom_combo.setMinimumWidth(100)
        toolbar.addWidget(self.zoom_combo)

        zoom_in_action = QAction("🔍+", self)
        zoom_in_action.setToolTip("Zoom in")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        toolbar.addSeparator()

        # Quick fit actions
        fit_width_action = QAction("📏 Fit Width", self)
        fit_width_action.setToolTip("Fit page to window width")
        fit_width_action.triggered.connect(self.fit_width)
        toolbar.addAction(fit_width_action)

        fit_page_action = QAction("📄 Fit Page", self)
        fit_page_action.setToolTip("Fit entire page in window")
        fit_page_action.triggered.connect(self.fit_page)
        toolbar.addAction(fit_page_action)

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
        print("🔧 Enhanced toolbar created with page jump and zoom controls")

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
                        f"PDF selected: {Path(file_path).name}\n\n"
                        "PDF viewing not fully available in current mode.\n"
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


    # Navigation and Zoom Methods
    @pyqtSlot()
    def previous_page(self):
        """Navigate to previous page"""
        if not hasattr(self.pdf_canvas, 'current_page'):
            self.statusBar().showMessage("No PDF loaded", 1000)
            return

        if hasattr(self.pdf_canvas, 'current_page') and self.pdf_canvas.current_page > 0:
            if hasattr(self.pdf_canvas, 'set_page'):
                new_page = self.pdf_canvas.current_page - 1
                self.pdf_canvas.set_page(new_page)
                self.statusBar().showMessage(f"Page {new_page + 1}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Navigation not available", 1000)
        else:
            self.statusBar().showMessage("Already at first page", 1000)

    @pyqtSlot()
    def next_page(self):
        """Navigate to next page"""
        if not hasattr(self.pdf_canvas, 'current_page') or not hasattr(self.pdf_canvas, 'pdf_document'):
            self.statusBar().showMessage("No PDF loaded", 1000)
            return

        if (self.pdf_canvas.pdf_document and 
            self.pdf_canvas.current_page < self.pdf_canvas.pdf_document.page_count - 1):
            if hasattr(self.pdf_canvas, 'set_page'):
                new_page = self.pdf_canvas.current_page + 1
                self.pdf_canvas.set_page(new_page)
                self.statusBar().showMessage(f"Page {new_page + 1}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Navigation not available", 1000)
        else:
            self.statusBar().showMessage("Already at last page", 1000)

    @pyqtSlot()
    def zoom_in(self):
        """Increase zoom level"""
        if not hasattr(self.pdf_canvas, 'zoom_level') or not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = min(current_zoom * 1.25, 5.0)
        self.pdf_canvas.set_zoom(new_zoom)
        zoom_percent = int(new_zoom * 100)
        self.statusBar().showMessage(f"Zoom: {zoom_percent}%", 1000)
        self.update_document_info()

    @pyqtSlot()
    def zoom_out(self):
        """Decrease zoom level"""
        if not hasattr(self.pdf_canvas, 'zoom_level') or not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = max(current_zoom / 1.25, 0.1)
        self.pdf_canvas.set_zoom(new_zoom)
        zoom_percent = int(new_zoom * 100)
        self.statusBar().showMessage(f"Zoom: {zoom_percent}%", 1000)
        self.update_document_info()

    @pyqtSlot()
    def fit_width(self):
        """Fit PDF page to window width"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Fit width not available", 1000)
            return

        try:
            # Calculate zoom needed to fit width
            available_width = self.scroll_area.width() - 40  # Account for margins
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)
            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            new_zoom = available_width / page_width
            new_zoom = max(0.1, min(new_zoom, 5.0))  # Clamp to reasonable range

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)
            self.statusBar().showMessage(f"Fit width: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Fit width failed", 1000)

    @pyqtSlot()
    def toggle_grid(self):
        """Toggle grid display"""
        if hasattr(self.pdf_canvas, 'toggle_grid'):
            self.pdf_canvas.toggle_grid()

            # Update grid action state if it exists
            if hasattr(self, 'grid_action') and hasattr(self.pdf_canvas, 'show_grid'):
                self.grid_action.setChecked(self.pdf_canvas.show_grid)

            grid_status = "on" if getattr(self.pdf_canvas, 'show_grid', False) else "off"
            self.statusBar().showMessage(f"Grid {grid_status}", 1000)
        else:
            self.statusBar().showMessage("Grid toggle not available", 1000)

    @pyqtSlot()
    def zoom_to_fit(self):
        """Zoom to fit entire page in window"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Zoom to fit not available", 1000)
            return

        try:
            # Calculate zoom to fit both width and height
            available_width = self.scroll_area.width() - 40
            available_height = self.scroll_area.height() - 40
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)

            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            page_height = self.pdf_canvas.page_pixmap.height() / current_zoom

            zoom_for_width = available_width / page_width
            zoom_for_height = available_height / page_height

            # Use the smaller zoom to ensure page fits completely
            new_zoom = min(zoom_for_width, zoom_for_height)
            new_zoom = max(0.1, min(new_zoom, 5.0))

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)
            self.statusBar().showMessage(f"Zoom to fit: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Zoom to fit failed", 1000)


    # Page and Zoom Control Methods
    @pyqtSlot(int)
    def jump_to_page(self, page_number: int):
        """Jump to specific page number"""
        if hasattr(self.pdf_canvas, 'go_to_page'):
            if self.pdf_canvas.go_to_page(page_number):
                self.statusBar().showMessage(f"Jumped to page {page_number}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Invalid page number", 1000)
        else:
            self.statusBar().showMessage("Page navigation not available", 1000)

    @pyqtSlot(str)
    def set_zoom_level(self, zoom_text: str):
        """Set zoom level from dropdown selection"""
        if not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        try:
            if zoom_text == "Fit Width":
                self.fit_width()
            elif zoom_text == "Fit Page":
                self.fit_page()
            elif zoom_text.endswith('%'):
                # Extract percentage value
                percent_str = zoom_text.replace('%', '').strip()
                percent = int(percent_str)
                zoom_level = percent / 100.0
                zoom_level = max(0.1, min(zoom_level, 5.0))  # Clamp to reasonable range

                self.pdf_canvas.set_zoom(zoom_level)
                self.statusBar().showMessage(f"Zoom set to {percent}%", 1000)
                self.update_document_info()
            else:
                # Try to parse as number
                percent = float(zoom_text)
                zoom_level = percent / 100.0
                zoom_level = max(0.1, min(zoom_level, 5.0))

                self.pdf_canvas.set_zoom(zoom_level)
                self.statusBar().showMessage(f"Zoom set to {int(percent)}%", 1000)
                self.update_document_info()

        except ValueError:
            self.statusBar().showMessage("Invalid zoom value", 1000)

    @pyqtSlot()
    def fit_page(self):
        """Fit entire page in window"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Fit page not available", 1000)
            return

        try:
            # Calculate zoom to fit both width and height
            available_width = self.scroll_area.width() - 40
            available_height = self.scroll_area.height() - 40
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)

            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            page_height = self.pdf_canvas.page_pixmap.height() / current_zoom

            zoom_for_width = available_width / page_width
            zoom_for_height = available_height / page_height

            # Use smaller zoom to ensure page fits completely
            new_zoom = min(zoom_for_width, zoom_for_height)
            new_zoom = max(0.1, min(new_zoom, 5.0))

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)

            # Update zoom combo
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText(f"{zoom_percent}%")

            self.statusBar().showMessage(f"Fit page: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Fit page failed", 1000)

    def update_page_controls(self):
        """Update page number controls based on current document"""
        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                current_page = getattr(self.pdf_canvas, 'current_page', 0) + 1
                total_pages = self.pdf_canvas.pdf_document.page_count

                # Update page spinbox
                if hasattr(self, 'page_spinbox'):
                    self.page_spinbox.setMaximum(total_pages)
                    self.page_spinbox.setValue(current_page)

                # Update page count label
                if hasattr(self, 'page_count_label'):
                    self.page_count_label.setText(f"of {total_pages}")

            else:
                # No document loaded
                if hasattr(self, 'page_spinbox'):
                    self.page_spinbox.setMaximum(1)
                    self.page_spinbox.setValue(1)

                if hasattr(self, 'page_count_label'):
                    self.page_count_label.setText("of 1")

        except Exception as e:
            pass  # Fail silently

    def update_zoom_controls(self):
        """Update zoom controls based on current zoom level"""
        try:
            if hasattr(self.pdf_canvas, 'zoom_level'):
                current_zoom = self.pdf_canvas.zoom_level
                zoom_percent = int(current_zoom * 100)

                # Update zoom combo
                if hasattr(self, 'zoom_combo'):
                    self.zoom_combo.setCurrentText(f"{zoom_percent}%")

        except Exception as e:
            pass  # Fail silently


    def setup_scroll_shortcuts(self):
        """Setup keyboard shortcuts for scrolling"""
        from PyQt6.QtGui import QShortcut

        # Zoom shortcuts
        zoom_in_shortcut = QShortcut("Ctrl++", self)
        zoom_in_shortcut.activated.connect(self.zoom_in)

        zoom_out_shortcut = QShortcut("Ctrl+-", self)
        zoom_out_shortcut.activated.connect(self.zoom_out)

        zoom_reset_shortcut = QShortcut("Ctrl+0", self)
        zoom_reset_shortcut.activated.connect(self.reset_zoom)

        # Fit shortcuts
        fit_width_shortcut = QShortcut("Ctrl+1", self)
        fit_width_shortcut.activated.connect(self.fit_width)

        fit_page_shortcut = QShortcut("Ctrl+2", self)
        fit_page_shortcut.activated.connect(self.fit_page)

        # Page navigation shortcuts
        next_page_shortcut = QShortcut("Ctrl+Right", self)
        next_page_shortcut.activated.connect(self.next_page)

        prev_page_shortcut = QShortcut("Ctrl+Left", self)
        prev_page_shortcut.activated.connect(self.previous_page)

        # Alternative page navigation
        page_down_shortcut = QShortcut("Page_Down", self)
        page_down_shortcut.activated.connect(self.next_page)

        page_up_shortcut = QShortcut("Page_Up", self)
        page_up_shortcut.activated.connect(self.previous_page)

    @pyqtSlot()
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if hasattr(self.pdf_canvas, 'set_zoom'):
            self.pdf_canvas.set_zoom(1.0)
            self.statusBar().showMessage("Zoom reset to 100%", 1000)
            self.update_document_info()

            # Update zoom combo if it exists
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText("100%")
        else:
            self.statusBar().showMessage("Zoom not available", 1000)

        def enable_smooth_scrolling(self):
        """Enable smooth scrolling for the scroll area"""
        if hasattr(self, 'scroll_area'):
            # Configure scroll bar step sizes for smoother scrolling
            v_scrollbar = self.scroll_area.verticalScrollBar()
            h_scrollbar = self.scroll_area.horizontalScrollBar()

            if v_scrollbar:
                v_scrollbar.setSingleStep(10)
                v_scrollbar.setPageStep(100)
            if h_scrollbar:
                h_scrollbar.setSingleStep(10)
                h_scrollbar.setPageStep(100)
    def update_document_info(self):
        """Update document information display - enhanced version"""
        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                # Get current page info
                current_page = getattr(self.pdf_canvas, 'current_page', 0) + 1
                total_pages = self.pdf_canvas.pdf_document.page_count

                # Get zoom info
                zoom_level = getattr(self.pdf_canvas, 'zoom_level', 1.0)
                zoom_percent = int(zoom_level * 100)

                # Get field count
                field_count = 0
                if hasattr(self.pdf_canvas, 'get_fields_as_objects'):
                    try:
                        fields = self.pdf_canvas.get_fields_as_objects()
                        field_count = len(fields)
                    except:
                        pass

                # Update display
                info_text = f"Page {current_page} of {total_pages} | Zoom: {zoom_percent}% | Fields: {field_count}"
                self.field_info_label.setText(info_text)

            else:
                self.field_info_label.setText("No document loaded")

        except Exception as e:
            # Fallback to basic info
            self.field_info_label.setText("Document info unavailable")

        # Update page and zoom controls
        self.update_page_controls()
        self.update_zoom_controls()

    def get_navigation_state(self) -> dict:
        """Get current navigation state for UI updates"""
        state = {
            'has_document': False,
            'can_go_previous': False,
            'can_go_next': False,
            'current_page': 0,
            'total_pages': 0,
            'zoom_percent': 100
        }

        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                state['has_document'] = True
                state['current_page'] = getattr(self.pdf_canvas, 'current_page', 0) + 1
                state['total_pages'] = self.pdf_canvas.pdf_document.page_count
                state['can_go_previous'] = getattr(self.pdf_canvas, 'current_page', 0) > 0
                state['can_go_next'] = getattr(self.pdf_canvas, 'current_page', 0) < state['total_pages'] - 1
                state['zoom_percent'] = int(getattr(self.pdf_canvas, 'zoom_level', 1.0) * 100)

        except Exception:
            pass

        return state


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
