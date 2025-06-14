"""
PDF Canvas Widget - Updated for New Field Model
Main widget for displaying PDF pages with interactive form fields
"""

from typing import Optional
import fitz  # PyMuPDF
from PyQt6.QtWidgets import QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QCursor  # QCursor IS needed here

from models.field_model import FormField, FieldManager
from ui.field_renderer import FieldRenderer
from ui.drag_handler import DragHandler, SelectionHandler


class PDFCanvas(QLabel):
    """
    PDF Canvas widget with draggable form fields
    Combines PDF rendering with interactive field management
    """

    # Signals
    fieldClicked = pyqtSignal(str)  # field_id
    fieldMoved = pyqtSignal(str, int, int)  # field_id, new_x, new_y
    fieldResized = pyqtSignal(str, int, int, int, int)  # field_id, x, y, width, height
    positionClicked = pyqtSignal(int, int)  # x, y coordinates
    selectionChanged = pyqtSignal(object)  # FormField or None

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("border: 1px solid #ccc; background-color: white;")

        # PDF document and page management
        self.pdf_document = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.page_pixmap = None

        # Field management
        self.field_manager = FieldManager()
        self.field_renderer = FieldRenderer()

        # Drag and selection handling
        self.drag_handler = DragHandler(self.field_manager)
        self.selection_handler = SelectionHandler(self.field_manager)

        # Grid settings
        self.show_grid = False
        self.grid_size = 20

        # Mouse tracking for hover effects
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard events

        # Connect internal signals
        self._setup_signal_connections()

        # Show initial message
        self.show_no_document_message()

    def _setup_signal_connections(self):
        """Setup internal signal connections"""
        # Connect drag handler signals
        self.drag_handler.fieldMoved.connect(self.fieldMoved)
        self.drag_handler.fieldResized.connect(self.fieldResized)

        # THIS is where QCursor is needed - converting CursorShape enum to QCursor object
        self.drag_handler.cursorChanged.connect(
            lambda cursor_shape: self.setCursor(QCursor(cursor_shape))
        )

        # Connect selection handler signals
        self.selection_handler.selectionChanged.connect(self.selectionChanged)
        self.selection_handler.selectionChanged.connect(self._on_selection_changed)

    def show_no_document_message(self):
        """Display message when no PDF is loaded"""
        self.setText(
            "No PDF loaded\n\n"
            "Click 'Open PDF' or drag & drop a PDF file here\n\n"
            "💡 Tips:\n"
            "• Drag fields to move them\n"
            "• Drag handles to resize them\n"
            "• Use arrow keys for precise movement"
        )
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

            # Clear existing fields
            self.field_manager.clear_all()
            self.selection_handler.clear_selection()

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
            # Get page and render to pixmap
            page = self.pdf_document[self.current_page]
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")

            # Convert to QPixmap
            self.page_pixmap = QPixmap()
            self.page_pixmap.loadFromData(img_data)

            # Update drag handler with canvas size
            self.drag_handler.set_canvas_size(
                self.page_pixmap.width(),
                self.page_pixmap.height()
            )

            # Draw overlay with fields
            self.draw_overlay()

        except Exception as e:
            print(f"Error rendering page: {e}")

    def draw_overlay(self):
        """Draw grid and form fields overlay on PDF"""
        if not self.page_pixmap:
            return

        # Create overlay on copy of page pixmap
        overlay_pixmap = self.page_pixmap.copy()
        painter = QPainter(overlay_pixmap)

        # Draw grid if enabled
        if self.show_grid:
            self.field_renderer.render_grid(
                painter,
                self.page_pixmap.width(),
                self.page_pixmap.height(),
                self.grid_size
            )

        # Draw form fields
        self.field_renderer.render_fields(
            painter,
            self.field_manager.fields,
            self.selection_handler.get_selected_field()
        )

        painter.end()

        # Update display
        self.setPixmap(overlay_pixmap)
        self.resize(overlay_pixmap.size())

    def add_field(self, field_type: str, x: int, y: int) -> FormField:
        """Add a new form field"""
        field = self.field_manager.add_field(field_type, x, y)
        self.selection_handler.select_field(field)
        self.draw_overlay()
        return field

    def delete_selected_field(self) -> bool:
        """Delete currently selected field"""
        success = self.selection_handler.delete_selected_field()
        if success:
            self.draw_overlay()
        return success

    def duplicate_selected_field(self) -> Optional[FormField]:
        """Duplicate the currently selected field"""
        new_field = self.selection_handler.duplicate_selected_field()
        if new_field:
            self.draw_overlay()
        return new_field

    def set_zoom(self, zoom_level: float):
        """Set zoom level and re-render page"""
        self.zoom_level = zoom_level
        self.render_page()

    def set_page(self, page_number: int):
        """Set current page and re-render"""
        if self.pdf_document and 0 <= page_number < self.pdf_document.page_count:
            self.current_page = page_number
            self.field_manager.clear_all()
            self.selection_handler.clear_selection()
            self.render_page()

    def toggle_grid(self):
        """Toggle grid display"""
        self.show_grid = not self.show_grid
        self.drag_handler.set_grid_settings(self.grid_size, self.show_grid)
        self.draw_overlay()

    def set_grid_size(self, size: int):
        """Set grid size"""
        self.grid_size = size
        self.drag_handler.set_grid_settings(self.grid_size, self.show_grid)
        if self.show_grid:
            self.draw_overlay()

    # Mouse event handlers
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()  # Enable keyboard events

            pos = event.position().toPoint()
            selected_field = self.drag_handler.handle_mouse_press(
                pos, self.selection_handler.get_selected_field()
            )

            if selected_field:
                self.selection_handler.select_field(selected_field)
                self.fieldClicked.emit(selected_field.id)
            else:
                self.selection_handler.clear_selection()
                self.positionClicked.emit(pos.x(), pos.y())

            self.draw_overlay()

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        pos = event.position().toPoint()
        is_dragging = self.drag_handler.handle_mouse_move(pos)

        if is_dragging:
            self.draw_overlay()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            was_dragging = self.drag_handler.handle_mouse_release(pos)

            if was_dragging:
                self.draw_overlay()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for field manipulation"""
        selected_field = self.selection_handler.get_selected_field()
        if not selected_field:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()

        # Arrow keys for movement
        if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            step = 10 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1

            dx, dy = 0, 0
            if key == Qt.Key.Key_Up:
                dy = -step
            elif key == Qt.Key.Key_Down:
                dy = step
            elif key == Qt.Key.Key_Left:
                dx = -step
            elif key == Qt.Key.Key_Right:
                dx = step

            self.drag_handler.handle_keyboard_move(selected_field, dx, dy)
            self.draw_overlay()
            return

        # Delete key
        if key == Qt.Key.Key_Delete:
            self.delete_selected_field()
            return

        # Ctrl+D for duplicate
        if (key == Qt.Key.Key_D and
            modifiers & Qt.KeyboardModifier.ControlModifier):
            self.duplicate_selected_field()
            return

        super().keyPressEvent(event)

    def _on_selection_changed(self, field: Optional[FormField]):
        """Handle selection changes"""
        self.draw_overlay()

    # Public interface for external access
    @property
    def selected_field(self) -> Optional[FormField]:
        """Get currently selected field"""
        return self.selection_handler.get_selected_field()

    @property
    def form_fields(self) -> list:
        """Get all form fields as dictionaries (for backward compatibility)"""
        return [field.to_dict() for field in self.field_manager.fields]

    def get_field_manager(self) -> FieldManager:
        """Get the field manager instance"""
        return self.field_manager

    def get_fields_as_objects(self) -> list:
        """Get all fields as FormField objects"""
        return self.field_manager.fields.copy()


    """
    Safe enhancement to PDF Canvas - adds navigation and zoom without breaking existing functionality
    Add these methods to your existing PDFCanvas class in src/ui/pdf_canvas.py
    """


    # Add these methods to your existing PDFCanvas class after the existing methods

    def get_page_count(self) -> int:
        """Get total number of pages in the document"""
        if self.pdf_document:
            return self.pdf_document.page_count
        return 0


    def get_current_page_number(self) -> int:
        """Get current page number (1-based)"""
        return self.current_page + 1 if self.pdf_document else 0


    def can_go_previous(self) -> bool:
        """Check if can navigate to previous page"""
        return self.pdf_document and self.current_page > 0


    def can_go_next(self) -> bool:
        """Check if can navigate to next page"""
        return (self.pdf_document and
                self.current_page < self.pdf_document.page_count - 1)


    def go_to_page(self, page_number: int) -> bool:
        """Navigate to specific page (1-based numbering)"""
        if not self.pdf_document:
            return False

        # Convert to 0-based indexing
        page_index = page_number - 1

        if 0 <= page_index < self.pdf_document.page_count:
            self.set_page(page_index)
            return True
        return False


    def zoom_to_level(self, zoom_percent: int) -> bool:
        """Set zoom to specific percentage (e.g., 100 for 100%)"""
        if zoom_percent < 10 or zoom_percent > 500:
            return False

        zoom_level = zoom_percent / 100.0
        self.set_zoom(zoom_level)
        return True


    def zoom_in_step(self, step: float = 1.25) -> float:
        """Zoom in by a step factor, returns new zoom level"""
        new_zoom = min(self.zoom_level * step, 5.0)
        self.set_zoom(new_zoom)
        return new_zoom


    def zoom_out_step(self, step: float = 1.25) -> float:
        """Zoom out by a step factor, returns new zoom level"""
        new_zoom = max(self.zoom_level / step, 0.1)
        self.set_zoom(new_zoom)
        return new_zoom


    def get_zoom_percent(self) -> int:
        """Get current zoom as percentage"""
        return int(self.zoom_level * 100)


    def fit_to_width(self, available_width: int) -> float:
        """Fit page to available width, returns new zoom level"""
        if not self.page_pixmap:
            return self.zoom_level

        # Calculate zoom needed to fit width
        page_width = self.page_pixmap.width() / self.zoom_level
        new_zoom = (available_width - 40) / page_width  # 40px margin
        new_zoom = max(0.1, min(new_zoom, 5.0))  # Clamp to reasonable range

        self.set_zoom(new_zoom)
        return new_zoom


    def get_document_info(self) -> dict:
        """Get document information"""
        if not self.pdf_document:
            return {
                'page_count': 0,
                'current_page': 0,
                'zoom_percent': 100,
                'field_count': 0,
                'has_document': False
            }

        return {
            'page_count': self.pdf_document.page_count,
            'current_page': self.current_page + 1,
            'zoom_percent': self.get_zoom_percent(),
            'field_count': len(self.field_manager.fields),
            'has_document': True
        }