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
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming and scrolling"""
        modifiers = event.modifiers()

        # Ctrl + Wheel = Zoom
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()

            if delta > 0:
                new_zoom = min(self.zoom_level * 1.15, 5.0)
            else:
                new_zoom = max(self.zoom_level / 1.15, 0.1)

            if new_zoom != self.zoom_level:
                self.set_zoom(new_zoom)

            event.accept()
        else:
            # Regular wheel = Pass to parent for scrolling
            super().wheelEvent(event)


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

            # *** KEY FIX: Set widget size to match pixmap ***
            pixmap_size = self.page_pixmap.size()

            # Set both minimum and actual size
            self.setMinimumSize(pixmap_size)
            self.resize(pixmap_size)

            # Update the displayed pixmap
            self.setPixmap(self.page_pixmap)
        # *** CRITICAL FIX: Set widget size to match PDF content ***
        if self.page_pixmap:
            pixmap_size = self.page_pixmap.size()

            # Set both minimum size and actual size
            self.setMinimumSize(pixmap_size)
            self.resize(pixmap_size)

            # Force parent to recognize size change
            if self.parent():
                self.parent().updateGeometry()

            print(f"📏 PDF Canvas sized to: {pixmap_size.width()}x{pixmap_size.height()}")

            # Debug: Print size information
            print(f"📏 PDF Canvas sizing:")
            print(f"  Pixmap size: {pixmap_size.width()}x{pixmap_size.height()}")
            print(f"  Widget size after resize: {self.size().width()}x{self.size().height()}")
            print(f"  Widget minimum size: {self.minimumSize().width()}x{self.minimumSize().height()}")

            # Force parent to update
            if self.parent():
                self.parent().updateGeometry()
                print(f"  Parent widget updated")

            # Update drag handler with canvas size
            if hasattr(self, 'drag_handler'):
                self.drag_handler.set_canvas_size(
                    self.page_pixmap.width(),
                    self.page_pixmap.height()
                )

            # Draw overlay (grid, fields, etc.)
            if hasattr(self, 'draw_overlay'):
                self.draw_overlay()

        except Exception as e:
            print(f"Error rendering page: {e}")