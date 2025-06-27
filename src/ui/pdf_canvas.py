"""
PDF Canvas Widget
Complete working version for displaying PDFs with scrolling and field support
"""

from typing import List

from PyQt6.QtCore import QPoint
from PyQt6.QtCore import pyqtSignal, Qt, QRect
from PyQt6.QtGui import QPixmap, QPainter, QPen, QCursor, QPalette, QColor, QBrush
from PyQt6.QtWidgets import QLabel

from .enhanced_drag_handler import EnhancedDragHandler

# Try to import PyMuPDF
try:
    import fitz
    FITZ_AVAILABLE = True
except ImportError:
    print("⚠️ PyMuPDF (fitz) not available - PDF functionality limited")
    FITZ_AVAILABLE = False
    fitz = None

# Try to import field management components
try:
    from models.field_model import FormField, FieldType, FieldManager
    from ui.field_renderer import FieldRenderer
    from ui.enhanced_drag_handler import EnhancedDragHandler as DragHandler, WorkingSelectionHandler, SelectionHandler
    FIELD_COMPONENTS_AVAILABLE = True
    print("✅ Enhanced field components loaded successfully")
except ImportError as e:
    print(f"⚠️ Enhanced field management components not available: {e}")
    print("   Falling back to minimal versions...")
    FIELD_COMPONENTS_AVAILABLE = False


class MinimalFieldManager:
    """Minimal field manager for when full version isn't available"""
    def __init__(self):
        self.fields = []

    def add_field(self, field):
        self.fields.append(field)

    def remove_field(self, field_id):
        self.fields = [f for f in self.fields if f.id != field_id]

    def clear_all(self):
        self.fields = []


class MinimalSelectionHandler:
    """Minimal selection handler"""
    def __init__(self):
        self.selected_field = None
        self.selectionChanged = pyqtSignal(object)

    def select_field(self, field):
        self.selected_field = field
        self.selectionChanged.emit(field)

    def clear_selection(self):
        self.selected_field = None
        try:
            self.selectionChanged.emit(None)
        except AttributeError as e:
            print(f"⚠️ Selection handler issue: {e}")
            # Continue without clearing selection

    def get_selected_field(self):
        return self.selected_field


class MinimalDragHandler:
    """Minimal drag handler"""
    def __init__(self):
        self.cursorChanged = pyqtSignal(Qt.CursorShape)

    def handle_mouse_press(self, pos, selected_field):
        return None

    def handle_mouse_move(self, pos):
        return False

    def handle_mouse_release(self, pos):
        return False

    def set_canvas_size(self, width, height):
        pass

    def set_grid_settings(self, size, show):
        pass


class PDFCanvas(QLabel):
    """PDF Canvas widget for displaying and interacting with PDF documents"""

    # Signals
    fieldMoved = pyqtSignal(str, int, int)  # field_id, x, y
    fieldResized = pyqtSignal(str, int, int, int, int)  # field_id, x, y, width, height
    fieldClicked = pyqtSignal(str)  # field_id
    positionClicked = pyqtSignal(int, int)  # x, y
    selectionChanged = pyqtSignal(object)  # field or None

    def __init__(self):
        super().__init__()

        # Basic properties
        self.pdf_document = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.page_pixmap = None

        # Grid properties
        self.show_grid = False
        self.grid_size = 20

        # Initialize handlers
        self._init_handlers()

        # Initialize UI
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        self.setMinimumSize(400, 300)

        self.setStyleSheet("border:none;")  # Remove border

        # Show initial message
        self.show_no_document_message()

        # Setup signal connections
        self._setup_signal_connections()

        if hasattr(self, 'enhanced_drag_handler'):
            self.enhanced_drag_handler.pdf_canvas_ref = self

        self._rendering_in_progress = False

    def _init_handlers(self):
        """Initialize field and interaction handlers"""
        if FIELD_COMPONENTS_AVAILABLE:
            try:
                self.field_manager = FieldManager()
                self.selection_handler = WorkingSelectionHandler(self.field_manager)
                self.enhanced_drag_handler = EnhancedDragHandler(self, self.field_manager)
                self.field_renderer = FieldRenderer()
            except Exception as e:
                print(f"⚠️ Error initializing full handlers: {e}")
                self._init_minimal_handlers()
        else:
            self._init_minimal_handlers()

    def _init_minimal_handlers(self):
        """Initialize minimal handlers as fallback"""
        self.field_manager = MinimalFieldManager()
        self.selection_handler = MinimalSelectionHandler()
        self.enhanced_drag_handler = EnhancedDragHandler(self, self.field_manager)
        self.field_renderer = None

    def _setup_signal_connections(self):
        """Setup internal signal connections"""
        try:
            # Connect drag handler signals to PDF canvas signals
            if hasattr(self.enhanced_drag_handler, 'fieldMoved'):
                self.enhanced_drag_handler.fieldMoved.connect(self.fieldMoved)
            if hasattr(self.enhanced_drag_handler, 'fieldResized'):
                self.enhanced_drag_handler.fieldResized.connect(self.fieldResized)

            # Connect cursor changes (if enhanced handler supports it)
            if hasattr(self.enhanced_drag_handler, 'cursorChanged'):
                self.enhanced_drag_handler.cursorChanged.connect(
                    lambda cursor_shape: self.setCursor(QCursor(cursor_shape))
                )

            # Connect selection handler signals - ONLY if they exist and are real signals
            if hasattr(self.selection_handler, 'selectionChanged'):
                selection_signal = self.selection_handler.selectionChanged
                # Check if it's a real PyQt signal (not our fake one)
                if hasattr(selection_signal, 'connect') and callable(selection_signal.connect):
                    try:
                        selection_signal.connect(self.selectionChanged)
                        selection_signal.connect(self._on_selection_changed)
                    except Exception as e:
                        print(f"⚠️ Could not connect selection signals: {e}")
                else:
                    print("ℹ️ Using fake selection signals (callback-based)")

            print("✅ Signal connections established")

        except Exception as e:
            print(f"⚠️ Error in signal connections: {e}")


    def _on_selection_changed(self, field):
        """Handle selection changes from selection handler"""
        try:
            # Update display when selection changes
            if hasattr(self, 'draw_overlay'):
                self.draw_overlay()

            # Emit field clicked signal if field is selected
            if field and hasattr(self, 'fieldClicked'):
                self.fieldClicked.emit(field.id)
        except Exception as e:
            print(f"⚠️ Error in _on_selection_changed: {e}")



    def _on_selection_changed(self, field):
        """Handle selection changes from selection handler"""
        try:
            # Update display when selection changes
            if hasattr(self, 'draw_overlay'):
                self.draw_overlay()

            # Emit field clicked signal if field is selected
            if field and hasattr(self, 'fieldClicked'):
                self.fieldClicked.emit(field.id)
        except Exception as e:
            print(f"Error in _on_selection_changed: {e}")

    def show_no_document_message(self):
        """Display message when no PDF is loaded"""
        self.setText(
            "No PDF loaded\n\n"
            "Click 'Open PDF' to load a document\n\n"
            "💡 Tips:\n"
            "• Use Ctrl+Mouse Wheel to zoom\n"
            "• Use Mouse Wheel to scroll"
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
        print(f"🔧 Loading PDF: {pdf_path}")

        if not FITZ_AVAILABLE:
            print("❌ PyMuPDF not available")
            self.setText("PyMuPDF not available\nCannot load PDF files")
            return False

        try:
            print("✅ fitz imported successfully")

            # Open the PDF
            self.pdf_document = fitz.open(pdf_path)
            print(f"✅ PDF opened: {self.pdf_document.page_count} pages")

            # Reset to first page
            self.current_page = 0
            self.zoom_level = 1.0

            # Clear existing fields
            self.field_manager.clear_all_fields()

            # Clear selection safely
            try:
                self.selection_handler.clear_selection()
            except Exception as e:
                print(f"⚠️ Selection handler issue: {e}")
                # Continue without clearing selection

            # Render the first page
            self.render_page()
            print("✅ First page rendered")

            # Update styling
            self.setStyleSheet("border: none; background-color: transparent;")

            self.debug_widget_setup()
            #self.update_drag_handler_for_document()

            return True

        except Exception as e:
            print(f"❌ Error loading PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Enhanced render_page method with page moats
    def render_page(self):
        """Render all PDF pages as continuous vertical view with simple spacing and borders"""
        if not self.pdf_document:
            return
        # Import PyQt6 classes locally to avoid import issues
        from PyQt6.QtGui import QColor, QPainter, QPen
        from PyQt6.QtCore import QRect

        self.setStyleSheet("border:solid 1px red;");

        try:
            print(f"🎨 Rendering all {self.pdf_document.page_count} pages with simple moats")

            # Simple spacing settings
            top_margin = 15  # Gap from top
            bottom_margin = 15 # Gap from bottom
            vertical_spacing = 15  # Gap between pages
            horizontal_margin = 15  # Left/right gaps when fit-to-width

            # Calculate page dimensions
            page_heights = []
            max_width = 0

            # First pass: get dimensions of all pages
            for page_num in range(self.pdf_document.page_count):
                page = self.pdf_document[page_num]
                mat = fitz.Matrix(self.zoom_level, self.zoom_level)

                rect = page.rect
                page_width = int(rect.width * self.zoom_level)
                page_height = int(rect.height * self.zoom_level)

                page_heights.append(page_height)
                max_width = max(max_width, page_width)

            # Calculate total canvas dimensions
            canvas_width = max_width + (2 * horizontal_margin)
            total_height = top_margin + sum(page_heights) + (len(page_heights) - 1) * vertical_spacing + top_margin + bottom_margin

            # Create canvas with white background (no overall boundary)
            self.page_pixmap = QPixmap(canvas_width, total_height)
            #self.page_pixmap.fill(QColor(255, 255, 255))

            scroll_area = self.parent()
            if scroll_area and hasattr(scroll_area, 'viewport'):
                bg_color = scroll_area.viewport().palette().color(QPalette.ColorRole.Base)
            else:
                bg_color = QColor(240, 240, 240)  # Light gray fallback

            self.page_pixmap.fill(bg_color)

            painter = QPainter(self.page_pixmap)
            # painter.setPen(QPen(QColor(255, 255, 255), 1))  # Light silver border
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Render all pages
            current_y = top_margin
            self.page_positions = []

            for page_num in range(self.pdf_document.page_count):
                page = self.pdf_document[page_num]
                mat = fitz.Matrix(self.zoom_level, self.zoom_level)

                # Render page to pixmap
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")

                page_pixmap = QPixmap()
                page_pixmap.loadFromData(img_data)

                # Calculate page position (centered horizontally with margins)
                page_x = horizontal_margin
                page_y = current_y

                # Draw light silver border around page
                border_rect = QRect(page_x - 1, page_y - 1,
                                    page_pixmap.width() + 2, page_pixmap.height() + 2)
                painter.setPen(QPen(QColor(200, 200, 200), 1))  # Light silver border
                painter.drawRect(border_rect)

                # Draw the page content
                painter.drawPixmap(page_x, page_y, page_pixmap)

                # Store page position for navigation
                self.page_positions.append(page_y)

                # Move to next page position
                current_y += page_pixmap.height() + vertical_spacing

                print(f"  ✅ Rendered page {page_num + 1} at y={page_y}")

            painter.end()

            # Set widget size to match the full document
            self.setMinimumSize(self.page_pixmap.size())
            self.resize(self.page_pixmap.size())

            # Update the displayed pixmap
            self.setPixmap(self.page_pixmap)

            # Draw overlay (grid, fields, etc.)
            self.draw_overlay()

            print(f"✅ Simple continuous view rendered: {canvas_width}x{total_height} pixels")

            # ADD THESE LINES:
            # Setup scroll tracking after successful rendering
            #self.setup_scroll_tracking()

            # Initialize current_page and visible pages tracking
            if not hasattr(self, 'current_page'):
                self.current_page = 0
            if not hasattr(self, '_last_visible_pages'):
                self._last_visible_pages = [0]

            print("✅ PDF rendering complete with scroll tracking")

        except Exception as e:
            print(f"❌ Error rendering simple continuous view: {e}")
            import traceback
            traceback.print_exc()

    def draw_page_number(self, painter, page_num, moat_x, moat_y, moat_w, moat_h):
        """Draw page number indicator in the moat area"""
        from PyQt6.QtGui import QColor, QPen, QFont

        # Page number in top-right corner of moat
        painter.setPen(QPen(QColor(120, 120, 120)))
        painter.setFont(QFont("Arial", 10))

        text = f"Page {page_num}"
        text_rect = painter.fontMetrics().boundingRect(text)

        # Position in top-right corner with some padding
        text_x = moat_x + moat_w - text_rect.width() - 10
        text_y = moat_y + text_rect.height() + 5

        painter.drawText(text_x, text_y, text)

    # Configuration method to customize moat appearance
    def set_moat_settings(self, padding=20, border_width=2, spacing=40,
                          background_color=None,
                          page_color=None,
                          border_color=None,
                          show_shadow=True, show_page_numbers=True):
        """Configure the appearance of page moats"""
        from PyQt6.QtGui import QColor

        self.moat_padding = padding
        self.moat_border_width = border_width
        self.moat_spacing = spacing
        self.moat_background_color = background_color or QColor(240, 240, 240)
        self.moat_page_color = page_color or QColor(255, 255, 255)
        self.moat_border_color = border_color or QColor(180, 180, 180)
        self.moat_show_shadow = show_shadow
        self.moat_show_page_numbers = show_page_numbers

        # Re-render with new settings
        if self.pdf_document:
            self.render_page()


    def render_page_cards(self):
        """Render pages as Material Design-style cards"""
        if not self.pdf_document:
            return

        try:
            # Card settings
            card_margin = 30  # Space around each card
            card_padding = 15  # Space inside each card
            card_radius = 8  # Rounded corners
            shadow_blur = 10  # Shadow blur radius

            # Calculate dimensions
            page_heights = []
            max_width = 0

            for page_num in range(self.pdf_document.page_count):
                page = self.pdf_document[page_num]
                mat = fitz.Matrix(self.zoom_level, self.zoom_level)
                rect = page.rect

                page_width = int(rect.width * self.zoom_level)
                page_height = int(rect.height * self.zoom_level)

                page_heights.append(page_height)
                max_width = max(max_width, page_width)

            # Total canvas dimensions
            canvas_width = max_width + (2 * (card_margin + card_padding))
            total_height = sum(h + 2 * (card_margin + card_padding) for h in page_heights)

            # Create canvas
            self.page_pixmap = QPixmap(canvas_width, total_height)
            self.page_pixmap.fill(QColor(250, 250, 250))  # Very light background

            painter = QPainter(self.page_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            current_y = 0
            self.page_positions = []

            for page_num in range(self.pdf_document.page_count):
                # Render page content
                page = self.pdf_document[page_num]
                mat = fitz.Matrix(self.zoom_level, self.zoom_level)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")

                page_pixmap = QPixmap()
                page_pixmap.loadFromData(img_data)

                # Card dimensions
                card_x = card_margin
                card_y = current_y + card_margin
                card_w = page_pixmap.width() + (2 * card_padding)
                card_h = page_pixmap.height() + (2 * card_padding)

                # Draw card shadow
                shadow_rect = QRect(card_x + 3, card_y + 3, card_w, card_h)
                painter.fillRect(shadow_rect, QColor(0, 0, 0, 30))

                # Draw card background
                card_rect = QRect(card_x, card_y, card_w, card_h)
                painter.fillRect(card_rect, QColor(255, 255, 255))

                # Draw card border
                painter.setPen(QPen(QColor(220, 220, 220), 1))
                painter.drawRect(card_rect)

                # Draw page content
                content_x = card_x + card_padding
                content_y = card_y + card_padding
                painter.drawPixmap(content_x, content_y, page_pixmap)

                # Store position
                self.page_positions.append(content_y)

                # Move to next card
                current_y += card_h + card_margin

            painter.end()

            # Update display
            self.setMinimumSize(self.page_pixmap.size())
            self.resize(self.page_pixmap.size())
            self.setPixmap(self.page_pixmap)
            self.draw_overlay()

        except Exception as e:
            print(f"❌ Error rendering card-style pages: {e}")

    # Method to toggle between rendering styles
    def set_page_style(self, style="moat"):
        """Set the page rendering style

        Args:
            style: "continuous", "moat", or "cards"
        """
        self.page_style = style

        if style == "continuous":
            self.render_page_original()  # Your existing method
        elif style == "moat":
            self.render_page()  # Enhanced method with moats
        elif style == "cards":
            self.render_page_cards()  # Card-style rendering

    def render_page_original(self):
        """Render all PDF pages as continuous vertical view"""
        if not self.pdf_document:
            return

        try:
            print(f"🎨 Rendering all {self.pdf_document.page_count} pages for continuous view")

            # Calculate total height needed for all pages
            page_heights = []
            max_width = 0

            # First pass: get dimensions of all pages
            for page_num in range(self.pdf_document.page_count):
                page = self.pdf_document[page_num]
                mat = fitz.Matrix(self.zoom_level, self.zoom_level)

                # Get page dimensions
                rect = page.rect
                page_width = int(rect.width * self.zoom_level)
                page_height = int(rect.height * self.zoom_level)

                page_heights.append(page_height)
                max_width = max(max_width, page_width)

            # Calculate total height with spacing between pages
            page_spacing = 10  # pixels between pages
            total_height = sum(page_heights) + (len(page_heights) - 1) * page_spacing

            # Create one large pixmap to hold all pages
            self.page_pixmap = QPixmap(max_width, total_height)
            self.page_pixmap.fill(Qt.GlobalColor.white)

            painter = QPainter(self.page_pixmap)

            # Second pass: render all pages onto the large pixmap
            current_y = 0
            self.page_positions = []  # Store where each page starts

            for page_num in range(self.pdf_document.page_count):
                page = self.pdf_document[page_num]
                mat = fitz.Matrix(self.zoom_level, self.zoom_level)

                # Render page to pixmap
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")

                # Convert to QPixmap
                page_pixmap = QPixmap()
                page_pixmap.loadFromData(img_data)

                # Center the page horizontally if it's narrower than max_width
                x_offset = (max_width - page_pixmap.width()) // 2

                # Draw this page onto the large pixmap
                painter.drawPixmap(x_offset, current_y, page_pixmap)

                # Store page position for navigation
                self.page_positions.append(current_y)

                # Move to next page position
                current_y += page_pixmap.height() + page_spacing

                print(f"  ✅ Rendered page {page_num + 1}")

            painter.end()

            # Set widget size to match the full document
            self.setMinimumSize(self.page_pixmap.size())
            self.resize(self.page_pixmap.size())

            # Update the displayed pixmap
            self.setPixmap(self.page_pixmap)

            # Draw overlay (grid, fields, etc.)
            self.draw_overlay()

            print(f"✅ Continuous view rendered: {max_width}x{total_height} pixels")

        except Exception as e:
            print(f"❌ Error rendering continuous view: {e}")
            import traceback
            traceback.print_exc()

    def set_page(self, page_number: int):
        """Set current page and render it"""
        if not self.pdf_document:
            return

        if 0 <= page_number < self.pdf_document.page_count:
            self.current_page = page_number
            self.render_page()

    def set_zoom(self, zoom_level: float):
        """Set zoom level and re-render"""
        if zoom_level < 0.1 or zoom_level > 5.0:
            return

        self.zoom_level = zoom_level

        # ✅ ADD THIS LINE - Update enhanced drag handler zoom level
        if hasattr(self, 'enhanced_drag_handler'):
            self.enhanced_drag_handler.set_zoom_level(zoom_level)

        # Re-render with new zoom level
        self.render_page()
        # self.update_drag_handler_for_document()

    def _filter_fields_in_zoomed_viewport(self, fields: List[FormField], viewport_rect: QRect,
                                          page_num: int, zoom_level: float) -> List[FormField]:
        """Filter fields considering zoom level and viewport"""
        visible_fields = []

        for field in fields:
            # Convert field document coordinates to zoomed screen coordinates
            screen_coords = self.document_to_screen_coordinates(page_num, field.x, field.y)

            if screen_coords:
                screen_x, screen_y = screen_coords

                # Calculate field dimensions at current zoom
                field_width = int(field.width * zoom_level)
                field_height = int(field.height * zoom_level)

                # Create field rectangle in screen coordinates
                field_rect = QRect(screen_x, screen_y, field_width, field_height)

                # Add tolerance for fields partially visible
                tolerance = max(5, int(10 * zoom_level))  # Scale tolerance with zoom
                expanded_viewport = viewport_rect.adjusted(-tolerance, -tolerance, tolerance, tolerance)

                # Check intersection with expanded viewport
                if expanded_viewport.intersects(field_rect):
                    visible_fields.append(field)
                    print(f"     Field {field.id}: visible at zoom {zoom_level:.1f}x")

        return visible_fields

    def _draw_grid_in_viewport_zoomed(self, painter: QPainter, viewport_rect: QRect, zoom_level: float):
        """Draw grid scaled appropriately for zoom level"""
        if not self.show_grid:
            return

        # Scale grid size with zoom level
        scaled_grid_size = int(self.grid_size * zoom_level)

        # At very high zoom, might want larger grid spacing
        if zoom_level > 3.0:
            scaled_grid_size = int(scaled_grid_size * 2)  # Double spacing at high zoom

        # At very low zoom, might want to skip grid entirely
        if zoom_level < 0.3:
            return  # Grid would be too dense to be useful

        pen = QPen(Qt.GlobalColor.lightGray, 1)
        painter.setPen(pen)

        # Draw vertical lines with zoom-scaled spacing
        start_x = (viewport_rect.left() // scaled_grid_size) * scaled_grid_size
        for x in range(start_x, viewport_rect.right() + scaled_grid_size, scaled_grid_size):
            if viewport_rect.left() <= x <= viewport_rect.right():
                painter.drawLine(x, viewport_rect.top(), x, viewport_rect.bottom())

        # Draw horizontal lines with zoom-scaled spacing
        start_y = (viewport_rect.top() // scaled_grid_size) * scaled_grid_size
        for y in range(start_y, viewport_rect.bottom() + scaled_grid_size, scaled_grid_size):
            if viewport_rect.top() <= y <= viewport_rect.bottom():
                painter.drawLine(viewport_rect.left(), y, viewport_rect.right(), y)

    def _render_field_at_zoom(self, painter: QPainter, field: FormField,
                              selected_field: FormField, zoom_level: float):
        """Render field with zoom-appropriate detail level"""

        # Get screen coordinates
        page_num = getattr(field, 'page_number', 0)
        screen_coords = self.document_to_screen_coordinates(page_num, field.x, field.y)

        if not screen_coords:
            return

        screen_x, screen_y = screen_coords
        field_width = int(field.width * zoom_level)
        field_height = int(field.height * zoom_level)

        # Adjust rendering detail based on zoom level
        if zoom_level < 0.5:
            # Low zoom: simple rectangles only
            self._render_field_simple(painter, screen_x, screen_y, field_width, field_height, field)
        elif zoom_level < 2.0:
            # Medium zoom: normal detail
            self._render_field_normal(painter, screen_x, screen_y, field_width, field_height, field)
        else:
            # High zoom: full detail including borders, text, etc.
            self._render_field_detailed(painter, screen_x, screen_y, field_width, field_height, field)

        # Draw selection handles if selected (scale with zoom)
        if field == selected_field:
            self._draw_selection_handles_zoomed(painter, screen_x, screen_y,
                                                field_width, field_height, zoom_level)

    def _draw_selection_handles_zoomed(self, painter: QPainter, x: int, y: int,
                                       width: int, height: int, zoom_level: float):
        """Draw selection handles scaled appropriately for zoom"""

        # Scale handle size with zoom, but keep readable
        base_handle_size = 8
        handle_size = max(6, min(16, int(base_handle_size * zoom_level)))

        # Draw selection rectangle
        painter.setPen(QPen(QColor(255, 0, 0), max(1, int(2 * zoom_level))))
        painter.setBrush(QBrush())
        painter.drawRect(x - 2, y - 2, width + 4, height + 4)

        # Draw corner handles
        painter.setBrush(QBrush(QColor(255, 0, 0)))

        positions = [
            (x - handle_size // 2, y - handle_size // 2),  # Top-left
            (x + width - handle_size // 2, y - handle_size // 2),  # Top-right
            (x - handle_size // 2, y + height - handle_size // 2),  # Bottom-left
            (x + width - handle_size // 2, y + height - handle_size // 2)  # Bottom-right
        ]

        for pos_x, pos_y in positions:
            painter.drawRect(pos_x, pos_y, handle_size, handle_size)

    def update_current_page_from_scroll(self):
        """Update current page and render controls with zoom awareness"""
        try:
            v_scrollbar = self.scroll_area.verticalScrollBar()
            h_scrollbar = self.scroll_area.horizontalScrollBar()

            scroll_x = h_scrollbar.value()
            scroll_y = v_scrollbar.value()
            viewport_width = self.scroll_area.viewport().width()
            viewport_height = self.scroll_area.viewport().height()

            # Get current zoom level
            zoom_level = getattr(self.pdf_canvas, 'zoom_level', 1.0)

            # Calculate viewport rectangle in canvas coordinates (already zoom-scaled)
            viewport_rect = QRect(scroll_x, scroll_y, viewport_width, viewport_height)

            # Determine visible page range (zoom affects page positions)
            start_page = self.pdf_canvas.get_page_at_y_position(scroll_y)
            end_page = self.pdf_canvas.get_page_at_y_position(scroll_y + viewport_height)

            # Update current page
            current_page = self.pdf_canvas.get_current_page_from_scroll(scroll_y)
            self.pdf_canvas.current_page = current_page

            print(f"📜 Scroll update: zoom={zoom_level:.1f}x, pages={start_page}-{end_page}")

            # Render controls for visible area with zoom consideration
            self.pdf_canvas.draw_controls_and_overlay(start_page, end_page, viewport_rect)

            # Update UI
            self.update_document_info()

        except Exception as e:
            print(f"⚠️ Error in scroll update: {e}")

    def on_zoom_changed(self, new_zoom_level: float):
        """Handle zoom level changes"""
        old_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)

        print(f"🔍 Zoom changed: {old_zoom:.1f}x → {new_zoom_level:.1f}x")

        # Update canvas zoom
        self.pdf_canvas.set_zoom(new_zoom_level)

        # Force full re-render at new zoom (don't use viewport method here)
        self.pdf_canvas.draw_overlay()  # Full redraw needed when zoom changes

        # Update scroll position to maintain focus point
        self._maintain_zoom_focus_point(old_zoom, new_zoom_level)

    def get_rendering_strategy_for_zoom(self, zoom_level: float) -> str:
        """Determine rendering strategy based on zoom level"""
        if zoom_level < 0.3:
            return "ultra_low_detail"  # Just colored rectangles
        elif zoom_level < 0.7:
            return "low_detail"  # Simple borders, no text
        elif zoom_level < 1.5:
            return "normal_detail"  # Standard rendering
        elif zoom_level < 3.0:
            return "high_detail"  # Enhanced borders, full text
        else:
            return "ultra_high_detail"  # All decorations, crisp text

    def draw_controls_and_overlay(self, start_page: int, end_page: int, viewport_rect: QRect):
        """
        Draw controls with zoom-aware viewport handling

        Args:
            start_page: First visible page (0-based)
            end_page: Last visible page (0-based, inclusive)
            viewport_rect: Bounding rectangle in canvas coordinates (already zoom-scaled)
        """
        if not self.page_pixmap:
            return

        try:
            zoom_level = getattr(self, 'zoom_level', 1.0)
            print(f"🎨 Drawing controls for pages {start_page}-{end_page} at zoom {zoom_level:.1f}x")
            print(f"   Viewport: {viewport_rect} (canvas coords)")

            # Create overlay copy
            overlay_pixmap = self.page_pixmap.copy()
            painter = QPainter(overlay_pixmap)

            # Scale grid size with zoom
            if self.show_grid:
                self._draw_grid_in_viewport_zoomed(painter, viewport_rect, zoom_level)

            # Draw fields with zoom-aware filtering
            if self.field_renderer and hasattr(self, 'field_manager'):
                selected_field = self.selection_handler.get_selected_field() if hasattr(self,
                                                                                        'selection_handler') else None

                total_fields_rendered = 0
                for page_num in range(start_page, end_page + 1):
                    # Get fields on this page
                    page_fields = [f for f in self.field_manager.fields
                                   if getattr(f, 'page_number', 0) == page_num]

                    # Filter fields visible in zoomed viewport
                    visible_fields = self._filter_fields_in_zoomed_viewport(
                        page_fields, viewport_rect, page_num, zoom_level
                    )

                    print(f"   Page {page_num}: {len(visible_fields)}/{len(page_fields)} fields in zoomed viewport")

                    # Render visible fields at current zoom
                    for field in visible_fields:
                        self._render_field_at_zoom(painter, field, selected_field, zoom_level)
                        total_fields_rendered += 1

                print(f"✅ Rendered {total_fields_rendered} fields at {zoom_level:.1f}x zoom")

            painter.end()
            self.setPixmap(overlay_pixmap)

        except Exception as e:
            print(f"❌ Error in draw_controls_and_overlay: {e}")

    def draw_overlay(self):

        """Draw overlay with fields and grid for all visible pages"""
        if hasattr(self, 'enhanced_drag_handler') and self.enhanced_drag_handler.is_dragging:
            return  # Skip expensive redraw during drag - overlay handles it!

        if not self.page_pixmap:
            return

        # Prevent concurrent rendering conflicts
        if getattr(self, '_rendering_in_progress', False):
            return

        try:
            self._rendering_in_progress = True

            # Create a copy of the pixmap to draw on
            overlay_pixmap = self.page_pixmap.copy()
            painter = QPainter(overlay_pixmap)

            # Draw grid if enabled
            if self.show_grid:
                self._draw_grid(painter)

            # Draw fields if available - HANDLE MULTIPLE VISIBLE PAGES
            if self.field_renderer and hasattr(self.field_renderer, 'render_fields'):
                # Get primary selected field
                primary_selected_field = self.selection_handler.get_selected_field() if hasattr(self,
                                                                                                'selection_handler') else None

                # Get ALL selected fields from drag handler for counting
                multi_selected_fields = []
                if hasattr(self, 'enhanced_drag_handler') and hasattr(self.enhanced_drag_handler, 'get_selected_fields'):
                    multi_selected_fields = self.enhanced_drag_handler.get_selected_fields()

                # Get ALL visible pages
                visible_pages = self.get_visible_page_numbers()
                print(f"🎨 Drawing fields for visible pages: {visible_pages}")

                # DEBUG: Check what fields exist per page
                total_fields = len(self.field_manager.fields) if self.field_manager else 0
                print(f"🎨 Total fields in manager: {total_fields}")
                print(f"🎨 Multi-selected fields: {len(multi_selected_fields)}")

                # Render fields for each visible page (WITHOUT multi_selected_fields parameter)
                for page_num in visible_pages:
                    self.field_renderer.render_fields(
                        painter,
                        self.field_manager.fields,
                        primary_selected_field,
                        page_num,
                        zoom_level=self.zoom_level,
                        coord_transform_func=self.document_to_screen_coordinates
                    )

            # ✅ Draw selection handles for all selected fields AFTER field rendering
            self._draw_selection_handles(painter)

            painter.end()

            # Update the displayed pixmap
            self.setPixmap(overlay_pixmap)

        except Exception as e:
            print(f"Error drawing overlay: {e}")
        finally:
            # CRITICAL: Always reset the flag
            self._rendering_in_progress = False

    def _draw_selection_handles(self, painter):
        """Draw selection handles for all selected fields with detailed logging"""

        # Check what handlers think is selected when drawing starts
        if hasattr(self, 'selection_handler'):
            current = getattr(self.selection_handler, 'selected_field', None)
            current_id = getattr(current, 'id', 'None') if current else 'None'
            print(f"   Selection handler at draw time: {current_id}")

        if hasattr(self, 'enhanced_drag_handler'):
            if hasattr(self.enhanced_drag_handler, 'selected_fields'):
                current_list = self.enhanced_drag_handler.selected_fields
                current_ids = [getattr(f, 'id', 'unknown') for f in current_list]
                print(f"   Enhanced drag handler at draw time: {current_ids}")

        try:
            # Get all selected fields from drag handler
            selected_fields = []
            if hasattr(self, 'enhanced_drag_handler') and hasattr(self.enhanced_drag_handler, 'get_selected_fields'):
                selected_fields = self.enhanced_drag_handler.get_selected_fields()

            # Also include the primary selected field from selection handler
            if hasattr(self, 'selection_handler'):
                primary_field = self.selection_handler.get_selected_field()
                if primary_field and primary_field not in selected_fields:
                    selected_fields.append(primary_field)

            # Enhanced logging with field details
            print(f"🎨 Drawing selection handles for {len(selected_fields)} fields:")

            if not selected_fields:
                print("   📭 No fields selected")
                return

            # Log each selected field with details
            for i, field in enumerate(selected_fields):
                field_id = getattr(field, 'id', getattr(field, 'name', f'field_{i}'))
                field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))

                # Handle field_type that might be an enum
                if hasattr(field_type, 'value'):
                    field_type = field_type.value
                elif hasattr(field_type, 'name'):
                    field_type = field_type.name

                page_num = getattr(field, 'page_number', 0)
                x = getattr(field, 'x', 0)
                y = getattr(field, 'y', 0)
                width = getattr(field, 'width', 0)
                height = getattr(field, 'height', 0)

                print(
                    f"   🎯 Field {i + 1}: {field_type.upper()} '{field_id}' on page {page_num} at ({x}, {y}) size {width}x{height}")

                # Use different colors for multi-selection
                if len(selected_fields) > 1:
                    # Multi-selection: use blue for all, but different shades
                    colors = [
                        QColor(0, 120, 255),  # Blue
                        QColor(255, 120, 0),  # Orange
                        QColor(120, 255, 0),  # Green
                        QColor(255, 0, 120),  # Magenta
                        QColor(0, 255, 120),  # Cyan
                    ]
                    color = colors[i % len(colors)]
                    print(f"      🎨 Using multi-selection color: {color.name()}")
                    self._draw_field_selection_handles(painter, field, color, i)
                else:
                    # Single selection: use red
                    color = QColor(255, 0, 0)
                    print(f"      🎨 Using single-selection color: {color.name()}")
                    self._draw_field_selection_handles(painter, field, color, 0)

            print(f"   ✅ Selection handles drawn for all {len(selected_fields)} field(s)")

        except Exception as e:
            print(f"⚠️ Error drawing selection handles: {e}")
            import traceback
            traceback.print_exc()

    def _draw_field_selection_handles(self, painter, field, color, index=0):
        """Draw selection handles for a single field with enhanced debugging"""
        try:
            field_id = getattr(field, 'id', getattr(field, 'name', f'field_{index}'))
            print(f"      🖌️ Drawing handles for {field_id}...")

            # Get field position and size
            page_num = getattr(field, 'page_number', 0)

            # Convert field coordinates to screen coordinates
            screen_coords = self.document_to_screen_coordinates(page_num, field.x, field.y)
            if not screen_coords:
                print(f"      ⚠️ Field {field_id} not visible (page {page_num} not rendered)")
                return

            screen_x, screen_y = screen_coords
            screen_width = field.width * self.zoom_level
            screen_height = field.height * self.zoom_level

            print(
                f"      📍 {field_id}: doc({field.x}, {field.y}) -> screen({int(screen_x)}, {int(screen_y)}) size({int(screen_width)}x{int(screen_height)})")

            # Draw selection rectangle with specified color
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(QBrush())

            selection_rect = QRect(
                int(screen_x - 2),
                int(screen_y - 2),
                int(screen_width + 4),
                int(screen_height + 4)
            )
            painter.drawRect(selection_rect)

            # Draw corner handles
            handle_size = 8
            painter.setBrush(QBrush(color))

            # Calculate handle positions
            handles = [
                (screen_x - handle_size // 2, screen_y - handle_size // 2),  # Top-left
                (screen_x + screen_width - handle_size // 2, screen_y - handle_size // 2),  # Top-right
                (screen_x - handle_size // 2, screen_y + screen_height - handle_size // 2),  # Bottom-left
                (screen_x + screen_width - handle_size // 2, screen_y + screen_height - handle_size // 2)
                # Bottom-right
            ]

            handle_count = 0
            for handle_x, handle_y in handles:
                handle_rect = QRect(int(handle_x), int(handle_y), handle_size, handle_size)
                painter.drawRect(handle_rect)
                handle_count += 1

            print(f"      ✅ Drew selection rectangle and {handle_count} handles for {field_id}")

        except Exception as e:
            print(f"      ❌ Error drawing handles for field: {e}")
            import traceback
            traceback.print_exc()

    def debug_selection_state(self):
        """Debug method to show current selection state"""
        print("\n🔍 SELECTION STATE DEBUG:")

        # Check selection handler
        if hasattr(self, 'selection_handler'):
            primary = self.selection_handler.get_selected_field()
            if primary:
                print(
                    f"   Selection Handler: {getattr(primary, 'field_type', 'unknown')} '{getattr(primary, 'id', 'unknown')}'")
            else:
                print(f"   Selection Handler: None")
        else:
            print(f"   Selection Handler: Not available")

        # Check enhanced drag handler
        if hasattr(self, 'enhanced_drag_handler'):
            if hasattr(self.enhanced_drag_handler, 'get_selected_fields'):
                selected = self.enhanced_drag_handler.get_selected_fields()
                if selected:
                    print(f"   Enhanced Drag Handler: {len(selected)} field(s)")
                    for i, field in enumerate(selected):
                        field_type = getattr(field, 'field_type', 'unknown')
                        field_id = getattr(field, 'id', f'field_{i}')
                        print(f"     {i + 1}. {field_type} '{field_id}'")
                else:
                    print(f"   Enhanced Drag Handler: No fields selected")
            else:
                print(f"   Enhanced Drag Handler: No get_selected_fields method")
        else:
            print(f"   Enhanced Drag Handler: Not available")

        print("🔍 END SELECTION DEBUG\n")

    def cleanup_scroll_tracking(self):
        """Clean up scroll tracking timer"""
        if hasattr(self, 'scroll_timer'):
            self.scroll_timer.stop()
            print("✅ Scroll tracking timer stopped")

    def _draw_grid(self, painter):
        """Draw grid overlay"""
        if not self.page_pixmap:
            return

        pen = QPen(Qt.GlobalColor.lightGray, 1)
        painter.setPen(pen)

        width = self.page_pixmap.width()
        height = self.page_pixmap.height()

        # Draw vertical lines
        for x in range(0, width, self.grid_size):
            painter.drawLine(x, 0, x, height)

        # Draw horizontal lines
        for y in range(0, height, self.grid_size):
            painter.drawLine(0, y, width, y)

    def toggle_grid(self):
        """Toggle grid display"""
        self.show_grid = not self.show_grid
        if hasattr(self.enhanced_drag_handler, 'set_grid_settings'):
            self.enhanced_drag_handler.set_grid_settings(self.grid_size, self.show_grid)
        self.draw_overlay()

    def get_fields_as_objects(self):
        """Get all fields as objects"""
        return self.field_manager.fields

    # Enhanced Navigation and Information Methods
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

    def fit_to_window(self, available_width: int, available_height: int) -> float:
        """Fit page to window size, returns new zoom level"""
        if not self.page_pixmap:
            return self.zoom_level

        # Calculate zoom needed for both width and height
        page_width = self.page_pixmap.width() / self.zoom_level
        page_height = self.page_pixmap.height() / self.zoom_level

        zoom_for_width = (available_width - 40) / page_width
        zoom_for_height = (available_height - 40) / page_height

        # Use smaller zoom to ensure page fits completely
        new_zoom = min(zoom_for_width, zoom_for_height)
        new_zoom = max(0.1, min(new_zoom, 5.0))

        self.set_zoom(new_zoom)
        return new_zoom

    def get_document_info(self) -> dict:
        """Get comprehensive document information"""
        if not self.pdf_document:
            return {
                'page_count': 0,
                'current_page': 0,
                'zoom_percent': 100,
                'field_count': 0,
                'has_document': False,
                'can_go_previous': False,
                'can_go_next': False
            }

        return {
            'page_count': self.pdf_document.page_count,
            'current_page': self.current_page + 1,
            'zoom_percent': self.get_zoom_percent(),
            'field_count': len(self.field_manager.fields),
            'has_document': True,
            'can_go_previous': self.can_go_previous(),
            'can_go_next': self.can_go_next()
        }

    def get_page_info_text(self) -> str:
        """Get formatted page information text"""
        if not self.pdf_document:
            return "No document loaded"

        current = self.current_page + 1
        total = self.pdf_document.page_count
        zoom = self.get_zoom_percent()
        fields = len(self.field_manager.fields)

        return f"Page {current} of {total} | Zoom: {zoom}% | Fields: {fields}"


    def reset_view(self):
        """Reset zoom and position to defaults"""
        self.zoom_level = 1.0
        if self.pdf_document:
            self.render_page()

    # Scrolling Event Handlers
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming and scrolling"""
        modifiers = event.modifiers()

        # Ctrl + Wheel = Zoom
        if (modifiers & Qt.KeyboardModifier.ControlModifier) or (modifiers & Qt.KeyboardModifier.MetaModifier):
            # Get the angle delta (positive = zoom in, negative = zoom out)
            delta = event.angleDelta().y()

            if delta > 0:
                # Zoom in
                new_zoom = min(self.zoom_level * 1.15, 5.0)
            else:
                # Zoom out
                new_zoom = max(self.zoom_level / 1.15, 0.1)

            if new_zoom != self.zoom_level:
                # Store the mouse position relative to the widget
                mouse_pos = event.position().toPoint()

                # Set new zoom
                self.set_zoom(new_zoom)

                # Emit signal to notify main window of zoom change
                if hasattr(self, 'zoomChanged'):
                    self.zoomChanged.emit(new_zoom)

            # Accept the event to prevent default scrolling
            event.accept()

        # Shift + Wheel = Horizontal scroll
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Let the parent scroll area handle horizontal scrolling
            super().wheelEvent(event)

        # Regular wheel = Vertical scroll
        else:
            # Let the parent scroll area handle vertical scrolling
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Enhanced key press event with field manipulation shortcuts"""
        key = event.key()
        modifiers = event.modifiers()

        # Get selected fields from drag handler
        selected_fields = self.enhanced_drag_handler.get_selected_fields()

        if not selected_fields:
            super().keyPressEvent(event)
            return

        # Movement shortcuts
        move_distance = 10 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1

        if key == Qt.Key.Key_Left:
            self.enhanced_drag_handler.handle_keyboard_move(-move_distance, 0)
            self.draw_overlay()
            event.accept()
        elif key == Qt.Key.Key_Right:
            self.enhanced_drag_handler.handle_keyboard_move(move_distance, 0)
            self.draw_overlay()
            event.accept()
        elif key == Qt.Key.Key_Up:
            self.enhanced_drag_handler.handle_keyboard_move(0, -move_distance)
            self.draw_overlay()
            event.accept()
        elif key == Qt.Key.Key_Down:
            self.enhanced_drag_handler.handle_keyboard_move(0, move_distance)
            self.draw_overlay()
            event.accept()

        # Delete selected fields
        elif key == Qt.Key.Key_Delete or key == Qt.Key.Key_Backspace:
            for field in selected_fields:
                try:
                    self.field_manager.remove_field(field)
                except Exception as e:
                    print(f"⚠️ Error deleting field: {e}")

            self.enhanced_drag_handler.clear_selection()
            self.selection_handler.clear_selection()
            self.draw_overlay()
            event.accept()

        # Copy/Paste shortcuts
        elif key == Qt.Key.Key_C and modifiers & Qt.KeyboardModifier.ControlModifier:
            # TODO: Implement copy functionality
            print("📋 Copy functionality (to be implemented)")
            event.accept()

        elif key == Qt.Key.Key_V and modifiers & Qt.KeyboardModifier.ControlModifier:
            # TODO: Implement paste functionality
            print("📋 Paste functionality (to be implemented)")
            event.accept()

        # Select all
        elif key == Qt.Key.Key_A and modifiers & Qt.KeyboardModifier.ControlModifier:
            for field in self.field_manager.fields:
                self.enhanced_drag_handler.select_field(field, add_to_selection=True)
            self.draw_overlay()
            event.accept()

        # Escape to clear selection
        elif key == Qt.Key.Key_Escape:
            self.enhanced_drag_handler.clear_selection()
            self.selection_handler.clear_selection()
            self.draw_overlay()
            event.accept()

        else:
            super().keyPressEvent(event)


    def scroll_page(self, direction: int):
        """Scroll by one page height"""
        if hasattr(self.parent(), 'verticalScrollBar'):
            scroll_bar = self.parent().verticalScrollBar()
            page_step = scroll_bar.pageStep()
            current_value = scroll_bar.value()
            new_value = current_value + (page_step * direction)
            scroll_bar.setValue(new_value)

    def scroll_vertical(self, delta: int):
        """Scroll vertically by delta pixels"""
        if hasattr(self.parent(), 'verticalScrollBar'):
            scroll_bar = self.parent().verticalScrollBar()
            current_value = scroll_bar.value()
            scroll_bar.setValue(current_value + delta)

    def scroll_horizontal(self, delta: int):
        """Scroll horizontally by delta pixels"""
        if hasattr(self.parent(), 'horizontalScrollBar'):
            scroll_bar = self.parent().horizontalScrollBar()
            current_value = scroll_bar.value()
            scroll_bar.setValue(current_value + delta)

    def scroll_to_top(self):
        """Scroll to top of document"""
        if hasattr(self.parent(), 'verticalScrollBar'):
            self.parent().verticalScrollBar().setValue(0)

    def scroll_to_bottom(self):
        """Scroll to bottom of document"""
        if hasattr(self.parent(), 'verticalScrollBar'):
            scroll_bar = self.parent().verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())

    def scroll_to_left(self):
        """Scroll to left edge of document"""
        if hasattr(self.parent(), 'horizontalScrollBar'):
            self.parent().horizontalScrollBar().setValue(0)

    def scroll_to_right(self):
        """Scroll to right edge of document"""
        if hasattr(self.parent(), 'horizontalScrollBar'):
            scroll_bar = self.parent().horizontalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())

    def center_on_point(self, x: int, y: int):
        """Center the view on a specific point"""
        if hasattr(self.parent(), 'ensureVisible'):
            # QScrollArea method to ensure a point is visible
            margin = 50  # Margin around the point
            self.parent().ensureVisible(x, y, margin, margin)

    # Mouse event handlers

    def paintEvent(self, event):
        """Paint event to render PDF and fields"""
        super().paintEvent(event)

        try:
            # Get a painter for this widget
            from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
            painter = QPainter(self)

            # Draw all fields
            #if hasattr(self, 'field_manager') and self.field_manager:
            #    for field in self.field_manager.fields:
            #        self._draw_field(painter, field)

            # Draw selection handles for selected field
            #if (hasattr(self, 'selection_handler') and
            #    self.selection_handler and
            #    hasattr(self.selection_handler, 'selected_field') and
            #    self.selection_handler.selected_field):

            #    self._draw_selection_handles(painter, self.selection_handler.selected_field)

        except Exception as e:
            print(f"⚠️ Error in paintEvent: {e}")

    def _draw_field(self, painter, field):
        """Draw a single field"""
        try:
            from PyQt6.QtGui import QPen, QBrush, QColor
            from PyQt6.QtCore import Qt

            # Convert document coordinates to screen coordinates
            page_num = getattr(field, 'page_number', 0)
            screen_coords = self.document_to_screen_coordinates(page_num, field.x, field.y)

            if not screen_coords:
                return  # Field is on a page that's not currently rendered

            screen_x, screen_y = screen_coords
            screen_width = field.width * self.zoom_level
            screen_height = field.height * self.zoom_level

            # CRITICAL: Convert ALL coordinates to integers
            screen_x = int(screen_x)
            screen_y = int(screen_y)
            screen_width = int(screen_width)
            screen_height = int(screen_height)

            print(
                f"   Drawing field page {page_num} doc({field.x}, {field.y}) -> screen({screen_x}, {screen_y}) zoom={self.zoom_level}")

            # Set up pen and brush
            painter.setPen(QPen(QColor(0, 0, 255), 2))
            painter.setBrush(QBrush(QColor(255, 255, 255, 100)))

            # Draw field rectangle using integer coordinates
            painter.drawRect(screen_x, screen_y, screen_width, screen_height)

            # Draw field type text using integer coordinates
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(screen_x + 5, screen_y + 15, f"{field.type.value}")

        except Exception as e:
            print(f"⚠️ Error drawing field: {e}")

    def debug_multi_selection(self):
        """Debug method to show multi-selection state"""
        print("\n🔍 MULTI-SELECTION DEBUG:")

        # Enhanced drag handler state
        if hasattr(self, 'enhanced_drag_handler'):
            selected_fields = self.enhanced_drag_handler.get_selected_fields()
            print(f"   Enhanced Drag Handler: {len(selected_fields)} fields")
            for i, field in enumerate(selected_fields):
                print(f"     {i + 1}. {field.name} ({field.field_type})")

        # Selection handler state
        if hasattr(self, 'selection_handler'):
            primary = self.selection_handler.get_selected_field()
            print(f"   Selection Handler Primary: {primary.name if primary else 'None'}")

        print()

    def mousePressEvent(self, event):
        """Simplified mouse press - let enhanced_drag_handler do the work"""
        print("🖱️ Enhanced mouse press event started")

        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            screen_pos = event.position().toPoint()
            modifiers = event.modifiers()

            # Convert coordinates
            doc_coords = self.screen_to_document_coordinates(screen_pos.x(), screen_pos.y())

            if not doc_coords:
                print("   Click was in margin/gap area - clearing selection")
                self._handle_outside_click()
                return

            page_num, doc_x, doc_y = doc_coords
            self.current_page = page_num
            doc_pos = QPoint(int(doc_x), int(doc_y))

            # Let enhanced_drag_handler handle EVERYTHING else
            clicked_field = self.enhanced_drag_handler.handle_mouse_press(doc_pos, modifiers, page_num)

            # If no field was clicked and we have a selected field type, create new field
            if not clicked_field:
                field_type = self._get_selected_field_type()
                if field_type:
                    self.create_field_at_position(doc_x, doc_y, page_num, field_type)

    def deprecated_mousePressEvent(self, event):
        """Enhanced mouse press event with proper outside-click handling"""
        print("🖱️ Enhanced mouse press event started")
        print(f"   Button: {event.button()}")
        print(f"   Position: {event.position().toPoint()}")
        print(f"   Modifiers: {event.modifiers()}")
        print(f"   Current page: {self.current_page}")

        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()  # Enable keyboard events
            screen_pos = event.position().toPoint()
            modifiers = event.modifiers()

            # Convert screen coordinates to document coordinates
            doc_coords = self.screen_to_document_coordinates(screen_pos.x(), screen_pos.y())

            if not doc_coords:
                print("   Click was in margin/gap area - clearing selection")
                self._handle_outside_click()
                return

            page_num, doc_x, doc_y = doc_coords
            print(f"   Screen pos: ({screen_pos.x()}, {screen_pos.y()})")
            print(f"   Page {page_num} doc pos: ({doc_x}, {doc_y}) at zoom {self.zoom_level}")

            self.current_page = page_num  # Update canvas current page to match click location
            print(f"✅ Updated canvas current_page to: {self.current_page}")

            doc_pos = QPoint(int(doc_x), int(doc_y))

            # Check if we clicked on an existing field
            clicked_field = None
            try:
                clicked_field = self.enhanced_drag_handler.handle_mouse_press(doc_pos, modifiers, page_num)
                print(f"   Enhanced drag handler result: {clicked_field.name if clicked_field else 'None'}")
            except Exception as e:
                print(f"⚠️ Error in enhanced drag handler: {e}")

            # If we clicked on a field, handle field selection
            if clicked_field:
                try:
                    if modifiers & Qt.KeyboardModifier.ControlModifier:
                        # 🔧 FIXED: Use field ID for comparison instead of object identity
                        clicked_field_id = getattr(clicked_field, 'id', None)

                        # Debug current selection
                        current_ids = [getattr(f, 'id', 'no_id') for f in self.field_manager.get_selected_fields()]
                        print(f"   🔍 Current selection: {current_ids}")
                        print(f"   🔍 Clicked field: {clicked_field_id}")

                        # Check if field is already selected by ID
                        already_selected = False
                        field_to_remove = None

                        for existing_field in self.field_manager.get_selected_fields():
                            if getattr(existing_field, 'id', None) == clicked_field_id:
                                already_selected = True
                                field_to_remove = existing_field
                                break

                        if already_selected:
                            # Remove the field
                            self.field_manager.get_selected_fields().remove(field_to_remove)
                            print(f"   ➖ Removed {clicked_field_id} from selection")
                        else:
                            # Add the field
                            self.field_manager.get_selected_fields().append(clicked_field)
                            print(f"   ➕ Added {clicked_field_id} to selection")

                    else:
                        # Single selection
                        self.field_manager.select_field(clicked_field, multi_select=False)
                        print(f"   🎯 Single selection: {getattr(clicked_field, 'id', 'no_id')}")

                    print(f"✅ Field interaction: {clicked_field.id}")
                    self._handle_field_clicked(clicked_field.id)

                    # Force redraw to show selection
                    self.draw_overlay()
                    return

                except Exception as e:
                    print(f"⚠️ Error in field selection: {e}")

            # Handle field creation for empty areas (if field type is selected)
            if not (modifiers & Qt.KeyboardModifier.ControlModifier):
                selected_field_type = self.get_selected_field_type()
                if selected_field_type and selected_field_type != 'select':
                    try:
                        self.create_field_at_position(doc_x, doc_y, page_num, selected_field_type)
                        return
                    except Exception as e:
                        print(f"⚠️ Error creating field: {e}")

            # Handle empty space click (clear selection if not holding Ctrl)
            if not (modifiers & Qt.KeyboardModifier.ControlModifier):
                print("   Clicked on empty space - clearing all selections")
                self._handle_outside_click()

    def _handle_outside_click(self):
        """Handle clicking outside any control - clear all selections and reset UI"""
        print("🧹 Handling outside click - clearing all selections")

        try:
            # Clear canvas selections
            if hasattr(self, 'selection_handler') and self.selection_handler:
                self.selection_handler.clear_selection()
                print("   ✅ Cleared selection handler")

            if hasattr(self, 'enhanced_drag_handler') and self.enhanced_drag_handler:
                self.enhanced_drag_handler.clear_selection()
                print("   ✅ Cleared enhanced drag handler")

            # Clear properties panel and dropdown
            self._clear_properties_panel()

            # Redraw to remove any visual selection indicators
            self.draw_overlay()

            print("✅ Outside click handling completed")

        except Exception as e:
            print(f"⚠️ Error in outside click handling: {e}")

    def _clear_properties_panel(self):
        """Clear the properties panel and reset dropdown to 'No controls selected'"""
        try:
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'field_palette'):
                properties_tab = main_window.field_palette.properties_tab

                # Just call the simple method we already have
                properties_tab.select_no_control()

        except Exception as e:
            print(f"   ⚠️ Error clearing properties panel: {e}")

    def _get_main_window(self):
        """Helper method to find the main window"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'field_palette'):
                return parent
            parent = parent.parent()
        return None

    def screen_to_document_coordinates(self, screen_x, screen_y):
        """Convert screen coordinates to (page_num, doc_x, doc_y)"""
        if not hasattr(self, 'page_positions') or not self.page_positions:
            return None

        # Find which page was clicked
        for page_num, page_top in enumerate(self.page_positions):
            # Get page height (accounting for zoom)
            page = self.pdf_document[page_num]
            page_height = int(page.rect.height * self.zoom_level)
            page_bottom = page_top + page_height

            if page_top <= screen_y <= page_bottom:
                # Click is within this page
                # Convert to page-relative coordinates
                page_relative_x = screen_x - 10  # Remove horizontal margin
                page_relative_y = screen_y - page_top

                # Convert to document coordinates (remove zoom)
                doc_x = page_relative_x / self.zoom_level
                doc_y = page_relative_y / self.zoom_level

                return (page_num, doc_x, doc_y)

        return None  # Click was in gap/margin area

    def document_to_screen_coordinates(self, page_num, doc_x, doc_y):
        """Convert document coordinates back to screen coordinates"""
        if not hasattr(self, 'page_positions') or page_num >= len(self.page_positions):
            return None

        # Get page top position
        page_top = self.page_positions[page_num]

        # Convert document to page-relative screen coordinates
        page_relative_x = doc_x * self.zoom_level
        page_relative_y = doc_y * self.zoom_level

        # Add page layout offsets
        screen_x = page_relative_x + 10  # Add horizontal margin
        screen_y = page_relative_y + page_top

        return (int(screen_x), int(screen_y))

    def _try_create_field_at_position(self, x, y, page_num):
        """Try to create a field at the specified position using the selected control type"""
        try:
            # Get the selected field type from the main window's field palette
            field_type = self._get_selected_field_type()

            if field_type:
                # Create the field WITH page number
                new_field = self._create_field_at_position(x, y, field_type, page_num)
                if new_field:
                    print(f"✅ Created {field_type} field at ({x}, {y}) on page {page_num}")
                    self._reset_field_type_selection()

                    # Select the new field
                    try:
                        self.selection_handler.select_field(new_field)
                        self._handle_field_clicked(new_field.id)
                    except Exception as e:
                        print(f"⚠️ Error selecting new field: {e}")

                    return True
            else:
                print("ℹ️ No field type selected in palette")

        except Exception as e:
            print(f"⚠️ Error creating field: {e}")

        return False

    def _reset_field_type_selection(self):
        """Reset field type selection in both canvas and palette"""
        print("🔄 Starting field type selection reset...")

        # Clear canvas selection
        self.selected_field_type = None
        print("✅ Cleared canvas selected_field_type")

        # Find and reset field palette
        try:
            main_window = self._get_main_window()
            if main_window:
                print(f"✅ Found main window: {type(main_window).__name__}")

                # Try multiple possible paths to field palette
                field_palette = None

                # Path 1: Direct field_palette attribute (most likely)
                if hasattr(main_window, 'field_palette'):
                    field_palette = main_window.field_palette
                    print("✅ Found field_palette via main_window.field_palette")

                # Path 2: Via sidebar (backup)
                elif hasattr(main_window, 'sidebar') and hasattr(main_window.sidebar, 'field_palette'):
                    field_palette = main_window.sidebar.field_palette
                    print("✅ Found field_palette via main_window.sidebar.field_palette")

                # Try to reset the field palette
                if field_palette:
                    # Check if it's an EnhancedFieldPalette with nested field_palette
                    if hasattr(field_palette, 'field_palette') and hasattr(field_palette.field_palette,
                                                                           'reset_selection'):
                        field_palette.field_palette.reset_selection()
                        print("✅ Called nested field_palette.reset_selection()")

                    # Direct reset_selection method
                    elif hasattr(field_palette, 'reset_selection'):
                        field_palette.reset_selection()
                        print("✅ Called field_palette.reset_selection()")

                    # Manual reset as fallback
                    else:
                        if hasattr(field_palette, 'clear_highlights'):
                            field_palette.clear_highlights()
                        if hasattr(field_palette, 'selected_field_type'):
                            field_palette.selected_field_type = None
                        print("✅ Manually cleared field_palette highlights and selection")
                else:
                    print("⚠️ Could not find field palette to reset")

        except Exception as e:
            print(f"⚠️ Error resetting field palette: {e}")

        print("✅ Field type selection reset complete")

    def create_field_at_position(self, x: float, y: float, page_number: int, field_type: str):
        """Create a new field at the specified position"""
        try:
            print(f"🎯 Creating {field_type} field at ({x}, {y}) on page {page_number}")

            # Use the field manager to create the field (note: correct parameters)
            field = self.field_manager.create_field(
                field_type,
                int(x),
                int(y),
                page_number
                # Note: width and height are NOT parameters - they're set by default in FormField.create()
            )

            if field:
                print(f"✅ Created field: {field.id}")


                #self._add_field_to_dropdown(field)
                self._reset_field_type_selection()

                # Optionally resize the field after creation if needed
                # field.resize_to(100, 30)  # Set custom size if desired

                # Select the newly created field
                try:
                    self.selection_handler.select_field(field)
                    self.enhanced_drag_handler.select_field(field)
                except Exception as e:
                    print(f"⚠️ Error selecting new field: {e}")

                # Redraw to show the new field
                self.draw_overlay()

                # Emit signal to notify other components
                if hasattr(self, 'fieldClicked'):
                    self.fieldClicked.emit(field.id)

                return field
            else:
                print(f"⚠️ Failed to create field via field manager")
                return None

        except Exception as e:
            print(f"⚠️ Error creating field: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _add_field_to_dropdown(self, field):
        """Add field to dropdown and ensure field manager is set"""
        try:
            # Find properties tab
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'field_palette'):
                    main_window = parent
                    break
                parent = parent.parent()

            if main_window and hasattr(main_window, 'field_palette'):
                properties_tab = main_window.field_palette.properties_tab

                # CRITICAL FIX: Ensure properties tab has field manager
                if not properties_tab.field_manager and hasattr(self, 'field_manager'):
                    properties_tab.field_manager = self.field_manager
                    print(f"  🔗 Set field manager in properties tab")

                # Remove placeholder if needed
                if (properties_tab.control_dropdown.count() == 1 and
                        properties_tab.control_dropdown.itemText(0) == "No controls available"):
                    properties_tab.control_dropdown.clear()

                # Fix field type detection
                field_type = getattr(field, 'field_type', 'unknown')
                if hasattr(field_type, 'value'):
                    field_type = field_type.value
                elif hasattr(field_type, 'name'):
                    field_type = field_type.name
                else:
                    field_type = str(field_type).lower()

                field_id = getattr(field, 'id', 'unknown')

                # Create display text with proper field type
                display_text = f"{str(field_type).title()} - {field_id}"
                properties_tab.control_dropdown.addItem(display_text, field_id)
                print(f"  ➕ Added to dropdown: {display_text}")

                # Update selection and properties
                last_index = properties_tab.control_dropdown.count() - 1
                properties_tab.control_dropdown.blockSignals(True)
                properties_tab.control_dropdown.setCurrentIndex(last_index)
                properties_tab.control_dropdown.blockSignals(False)

                # Update properties panel
                properties_tab.current_field = field
                properties_tab._update_properties_display(field)
                print(f"  ✅ Updated dropdown selection and properties")

        except Exception as e:
            print(f"  ⚠️ Error adding field to dropdown: {e}")

    def _remove_field_from_dropdown(self, field_id):
        """Remove single field from dropdown"""
        try:
            # Find the main window and properties tab
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'field_palette'):
                    main_window = parent
                    break
                parent = parent.parent()

            if main_window and hasattr(main_window, 'field_palette'):
                properties_tab = main_window.field_palette.properties_tab

                # Find and remove the item
                for i in range(properties_tab.control_dropdown.count()):
                    if properties_tab.control_dropdown.itemData(i) == field_id:
                        item_text = properties_tab.control_dropdown.itemText(i)
                        properties_tab.control_dropdown.removeItem(i)
                        print(f"  ➖ Removed from dropdown: {item_text}")
                        break

                # If no items left, add placeholder
                if properties_tab.control_dropdown.count() == 0:
                    properties_tab.control_dropdown.addItem("No controls available", None)
                    print(f"  ➕ Added 'No controls available' placeholder")

        except Exception as e:
            print(f"  ⚠️ Error removing field from dropdown: {e}")

    def delete_field(self, field_id):
        """Delete field and update dropdown"""
        try:
            # Delete from field manager
            success = self.field_manager.remove_field(field_id)

            if success:
                # Remove from dropdown
                self._remove_field_from_dropdown(field_id)
                print(f"🗑️ Deleted field: {field_id}")

                # Clear selection if deleted field was selected
                self.selection_handler.clear_selection()
                self.enhanced_drag_handler.clear_selection()
                self.draw_overlay()

        except Exception as e:
            print(f"❌ Error deleting field: {e}")

    def _get_selected_field_type(self):
        """Get the currently selected field type from the field palette"""
        try:

            if hasattr(self, 'selected_field_type') and self.selected_field_type:
                print(f"✅ Using stored field type: {self.selected_field_type}")
                return self.selected_field_type

            # Get the main window
            main_window = self._get_main_window()
            if not main_window:
                print("⚠️ Main window not found")
                return None

            # Check if field palette has a selected field type
            if hasattr(main_window, 'field_palette'):
                field_palette = main_window.field_palette

                # Look for a selected field type property
                if hasattr(field_palette, 'selected_field_type'):
                    return field_palette.selected_field_type

                # Look for highlighted button
                if hasattr(field_palette, 'field_buttons'):
                    for field_type, button in field_palette.field_buttons.items():
                        if button.isChecked() or 'border-color: #0078d4' in button.styleSheet():
                            return field_type

                # Default to text field if nothing specific is selected
                print("ℹ️ No specific field type selected, defaulting to TEXT")
                return None

        except Exception as e:
            print(f"⚠️ Error getting selected field type: {e}")

        return None

    def _create_field_at_position(self, x, y, field_type, page_num):
        """Create a new field at the specified position"""
        try:
            # Import field model components
            from models.field_model import FormField, FieldType

            # Map string field types to enum values
            field_type_map = {
                "text": FieldType.TEXT,
                "signature": FieldType.SIGNATURE,
                "checkbox": FieldType.CHECKBOX,
                "radio": FieldType.RADIO,
                "dropdown": FieldType.DROPDOWN,
                "date": FieldType.DATE,
                "number": FieldType.NUMBER,
                "button": FieldType.BUTTON
            }

            # Get the enum value
            field_enum = field_type_map.get(field_type.lower(), FieldType.TEXT)

            # Calculate field dimensions based on type
            width, height = self._get_field_dimensions(field_enum)

            # Center the field on the click position
            field_x = x - width // 2
            field_y = y - height // 2

            # Create unique field name
            field_count = len(self.field_manager.fields) + 1
            field_name = f"{field_type.lower()}_{field_count}"

            # Create the field using field manager (which now accepts page_number)
            new_field = self.field_manager.create_field(field_type, field_x, field_y, page_num)

            # Add to field manager
            # self.field_manager.fields.append(new_field)

            print(f"✅ Created field: {new_field.name} ({field_enum.value}) at ({field_x}, {field_y})")
            return new_field

        except Exception as e:
            print(f"⚠️ Error creating field: {e}")
            return None

    def _get_field_dimensions(self, field_type):
        """Get default dimensions for different field types"""
        try:
            from models.field_model import FieldType

            # Default dimensions based on field type
            dimensions = {
                FieldType.TEXT: (120, 25),
                FieldType.SIGNATURE: (150, 40),
                FieldType.CHECKBOX: (20, 20),
                FieldType.RADIO: (20, 20),
                FieldType.DROPDOWN: (120, 25),
                FieldType.DATE: (100, 25),
                FieldType.NUMBER: (80, 25),
                FieldType.BUTTON: (80, 30)
            }

            return dimensions.get(field_type, (100, 25))  # Default fallback

        except Exception as e:
            print(f"⚠️ Error getting field dimensions: {e}")
            return (100, 25)

    def _get_main_window(self):
        """Get the main window safely"""
        try:
            widget = self
            while widget.parent():
                widget = widget.parent()
                # Look for main window characteristics
                if (hasattr(widget, 'field_palette') and
                        hasattr(widget, 'pdf_canvas') and
                        hasattr(widget, 'on_field_clicked')):
                    return widget
            return None
        except Exception as e:
            print(f"⚠️ Error finding main window: {e}")
            return None

    def _handle_field_clicked(self, field_id):
        """Handle field click without using signals"""
        print(f"🎯 Field clicked: {field_id}")

        # Update main window directly
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'on_field_clicked'):
            try:
                main_window.on_field_clicked(field_id)
            except Exception as e:
                print(f"⚠️ Error calling main window field clicked handler: {e}")

    # Alternative: Enhanced version that tracks selected field type
    def set_selected_field_type(self, field_type):
        """Set the currently selected field type for placement"""
        self.selected_field_type = field_type
        print(f"🎯 Selected field type for placement: {field_type}")

    def get_selected_field_type(self):
        """Get the currently selected field type"""
        return getattr(self, 'selected_field_type', 'text')

    # Method to add to your field palette to track selection
    def on_field_button_clicked(self, field_type):
        """Handle field button click in palette (add this to FieldPalette)"""
        # Clear previous highlights
        self.clear_highlights()

        # Highlight selected button
        self.highlight_field_type(field_type, True)

        # Store selection
        self.selected_field_type = field_type

        # Notify canvas about selection
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'pdf_canvas'):
            main_window.pdf_canvas.set_selected_field_type(field_type)

        print(f"🎯 Field type selected: {field_type}")

        # Emit signal for other connections
        self.fieldRequested.emit(field_type)

    def mouseMoveEvent(self, event):
        """Enhanced mouse move event with improved drag handling"""
        pos = event.position().toPoint()

        # Convert to document coordinates for drag handler
        doc_coords = self.screen_to_document_coordinates(pos.x(), pos.y())
        if doc_coords:
            page_num, doc_x, doc_y = doc_coords
            doc_pos = QPoint(int(doc_x), int(doc_y))

            # Update drag handler zoom level
            self.enhanced_drag_handler.set_zoom_level(self.zoom_level)
            is_dragging = self.enhanced_drag_handler.handle_mouse_move(doc_pos)

            #if is_dragging:
            #    self.draw_overlay()
        else:
            # Still update cursor for areas outside document
            if hasattr(self, 'enhanced_drag_handler'):
                self.enhanced_drag_handler.handle_mouse_move(pos)

    def mouseReleaseEvent(self, event):
        """Enhanced mouse release event"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()

            # Convert to document coordinates
            doc_coords = self.screen_to_document_coordinates(pos.x(), pos.y())
            if doc_coords:
                page_num, doc_x, doc_y = doc_coords
                doc_pos = QPoint(int(doc_x), int(doc_y))

                was_dragging = self.enhanced_drag_handler.handle_mouse_release(doc_pos)

                if was_dragging:
                    print("✅ Drag operation completed")
                    self.draw_overlay()

                    # Notify main window of changes
                    main_window = self._get_main_window()
                    if main_window and hasattr(main_window, 'on_field_moved'):
                        try:
                            selected_fields = self.enhanced_drag_handler.get_selected_fields()
                            for field in selected_fields:
                                main_window.on_field_moved(field.id, field.x, field.y)
                        except Exception as e:
                            print(f"⚠️ Error notifying main window: {e}")


    def scroll_to_page(self, page_number):
        """Scroll to show a specific page"""
        if (not hasattr(self, 'page_positions') or
                not self.page_positions or
                page_number >= len(self.page_positions)):
            return

        # Get the Y position of the requested page
        target_y = self.page_positions[page_number]

        # Get the scroll area (parent)
        if hasattr(self.parent(), 'verticalScrollBar'):
            scroll_bar = self.parent().verticalScrollBar()
            scroll_bar.setValue(target_y)

    def debug_widget_setup(self):
        """Debug how the PDF canvas is connected to scroll area"""
        print("🔍 Widget hierarchy:")
        widget = self
        level = 0

        while widget and level < 5:  # Prevent infinite loop
            print(f"   Level {level}: {type(widget).__name__}")
            if hasattr(widget, 'verticalScrollBar'):
                print(f"     - Has verticalScrollBar: {widget.verticalScrollBar()}")
            if hasattr(widget, 'viewport'):
                print(f"     - Has viewport: {widget.viewport()}")
            if hasattr(widget, 'height'):
                print(f"     - Height: {widget.height()}")

            widget = widget.parent()
            level += 1

    def get_visible_page_numbers(self):
        """Get visible pages - direct access method"""
        if not hasattr(self, 'page_positions') or not self.page_positions:
            return [0]

        # Direct access: self -> QWidget -> QScrollArea
        try:
            scroll_area = self.parent().parent()  # Level 2 from your hierarchy

            if not hasattr(scroll_area, 'viewport') or not hasattr(scroll_area, 'verticalScrollBar'):
                print(f"⚠️ Direct access failed, not a QScrollArea")
                return [0]

            viewport = scroll_area.viewport()
            scroll_bar = scroll_area.verticalScrollBar()

            viewport_top = scroll_bar.value()
            viewport_bottom = viewport_top + viewport.height()

            print(f"🔍 Viewport: top={viewport_top}, bottom={viewport_bottom}")

            visible_pages = []
            for i, page_y in enumerate(self.page_positions):
                if i < len(self.page_positions) - 1:
                    page_bottom = self.page_positions[i + 1] - 15
                else:
                    page_bottom = page_y + 800  # Estimate

                if page_y <= viewport_bottom and page_bottom >= viewport_top:
                    visible_pages.append(i)

            result = visible_pages if visible_pages else [0]
            print(f"🎨 Visible pages: {result}")
            return result

        except Exception as e:
            print(f"⚠️ Error getting visible pages: {e}")
            return [0]

    def get_page_at_y_position(self, y_position):
        """Get page number at given Y position"""
        if not self.pdf_document or not hasattr(self, 'page_positions'):
            return 0

        try:
            for page_num, page_top in enumerate(self.page_positions):
                # Get page height (accounting for zoom)
                page = self.pdf_document[page_num]
                page_height = int(page.rect.height * self.zoom_level)
                page_bottom = page_top + page_height

                if page_top <= y_position <= page_bottom:
                    return page_num

            # If not found, return last page
            return len(self.page_positions) - 1 if self.page_positions else 0
        except:
            return 0

    def get_current_page_from_scroll(self, scroll_y):
        """Get current page based on scroll position"""
        if not self.pdf_document:
            return 0

        # Simple approach: find the page that occupies most of the viewport
        return self.get_page_at_y_position(scroll_y + 100)  # Add offset for better detection

    def _render_field_normal(self, painter, field, zoom_level, page_offset_y=0, field_rect=None, *args):
        """Render field at normal zoom level"""
        try:
            # Use provided field_rect if available, otherwise calculate it
            if field_rect is not None:
                x, y, width, height = field_rect.x(), field_rect.y(), field_rect.width(), field_rect.height()
            else:
                # Calculate field position and size
                x = field.rect.x0 * zoom_level
                y = (field.rect.y0 * zoom_level) + page_offset_y
                width = (field.rect.x1 - field.rect.x0) * zoom_level
                height = (field.rect.y1 - field.rect.y0) * zoom_level

            # Draw field border
            from PyQt6.QtCore import Qt, QRect
            from PyQt6.QtGui import QPen, QBrush, QColor

            field_rect = QRect(int(x), int(y), int(width), int(height))

            # Set field appearance based on type
            if hasattr(field, 'field_type'):
                if field.field_type == 'text':
                    painter.setPen(QPen(QColor(0, 0, 255), 1))  # Blue border
                    painter.setBrush(QBrush(QColor(255, 255, 255, 50)))  # Semi-transparent white
                elif field.field_type == 'checkbox':
                    painter.setPen(QPen(QColor(0, 128, 0), 1))  # Green border
                    painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
                else:
                    painter.setPen(QPen(QColor(128, 128, 128), 1))  # Gray border
                    painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
            else:
                painter.setPen(QPen(QColor(128, 128, 128), 1))
                painter.setBrush(QBrush(QColor(255, 255, 255, 50)))

            # Draw the field rectangle
            painter.drawRect(field_rect)

            # Draw field value if it has one
            if hasattr(field, 'value') and field.value:
                painter.setPen(QPen(QColor(0, 0, 0)))  # Black text
                painter.drawText(field_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                 str(field.value))

        except Exception as e:
            print(f"❌ Error rendering field: {e}")

    def _render_field_zoomed(self, painter, field, zoom_level, page_offset_y=0, field_rect=None, *args):
        """Render field at zoomed level"""
        self._render_field_normal(painter, field, zoom_level, page_offset_y, field_rect, *args)

    def _render_field_selected(self, painter, field, zoom_level, page_offset_y=0, field_rect=None, *args):
        """Render selected field with highlight"""
        try:
            # First render normal field
            self._render_field_normal(painter, field, zoom_level, page_offset_y, field_rect, *args)

            # Add selection highlight
            from PyQt6.QtCore import Qt, QRect
            from PyQt6.QtGui import QPen, QBrush, QColor

            # Use provided field_rect if available, otherwise calculate it
            if field_rect is not None:
                selection_rect = field_rect
            else:
                x = field.rect.x0 * zoom_level
                y = (field.rect.y0 * zoom_level) + page_offset_y
                width = (field.rect.x1 - field.rect.x0) * zoom_level
                height = (field.rect.y1 - field.rect.y0) * zoom_level
                selection_rect = QRect(int(x), int(y), int(width), int(height))

            # Draw selection highlight
            painter.setPen(QPen(QColor(255, 0, 0), 2))  # Red border for selection
            painter.setBrush(QBrush(QColor(255, 0, 0, 30)))  # Semi-transparent red
            painter.drawRect(selection_rect)

        except Exception as e:
            print(f"❌ Error rendering selected field: {e}")

    def _render_field_detailed(self, painter, field, zoom_level, page_offset_y=0, field_rect=None, *args, **kwargs):
        """Render field with detailed view (high zoom level)"""
        try:
            # Use provided field_rect if available, otherwise calculate it
            if field_rect is not None:
                x, y, width, height = field_rect.x(), field_rect.y(), field_rect.width(), field_rect.height()
            else:
                # Calculate field position and size
                x = field.rect.x0 * zoom_level
                y = (field.rect.y0 * zoom_level) + page_offset_y
                width = (field.rect.x1 - field.rect.x0) * zoom_level
                height = (field.rect.y1 - field.rect.y0) * zoom_level

            # Draw field border
            from PyQt6.QtCore import Qt, QRect
            from PyQt6.QtGui import QPen, QBrush, QColor, QFont

            field_rect = QRect(int(x), int(y), int(width), int(height))

            # More detailed rendering for high zoom
            if hasattr(field, 'field_type'):
                if field.field_type == 'text':
                    # Text field - blue border, white background
                    painter.setPen(QPen(QColor(0, 0, 255), 2))  # Thicker border for detail
                    painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
                elif field.field_type == 'checkbox':
                    # Checkbox - green border
                    painter.setPen(QPen(QColor(0, 128, 0), 2))
                    painter.setBrush(QBrush(QColor(240, 255, 240, 80)))
                elif field.field_type == 'signature':
                    # Signature field - purple border
                    painter.setPen(QPen(QColor(128, 0, 128), 2))
                    painter.setBrush(QBrush(QColor(255, 240, 255, 80)))
                else:
                    # Default field
                    painter.setPen(QPen(QColor(128, 128, 128), 2))
                    painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
            else:
                painter.setPen(QPen(QColor(128, 128, 128), 2))
                painter.setBrush(QBrush(QColor(255, 255, 255, 80)))

            # Draw the field rectangle
            painter.drawRect(field_rect)

            # Draw field label/name at high zoom
            if hasattr(field, 'name') and field.name and zoom_level > 1.5:
                painter.setPen(QPen(QColor(100, 100, 100)))
                font = QFont()
                font.setPointSize(max(8, int(10 * zoom_level)))
                painter.setFont(font)

                # Draw field name above the field
                label_rect = QRect(int(x), int(y - 20 * zoom_level), int(width), int(15 * zoom_level))
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft, field.name)

            # Draw field value if it has one
            if hasattr(field, 'value') and field.value:
                painter.setPen(QPen(QColor(0, 0, 0)))
                font = QFont()
                font.setPointSize(max(8, int(12 * zoom_level)))
                painter.setFont(font)
                painter.drawText(field_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                 str(field.value))

            # Draw field border highlight for better visibility at high zoom
            if zoom_level > 2.0:
                painter.setPen(QPen(QColor(255, 255, 0, 100), 1))  # Yellow highlight
                painter.setBrush(QBrush())  # No fill
                painter.drawRect(field_rect.adjusted(-2, -2, 2, 2))

        except Exception as e:
            print(f"❌ Error rendering detailed field: {e}")

    def draw_selected_fields(self, painter):
        """Draw selection handles for all selected fields"""
        try:
            # Get all selected fields from drag handler
            selected_fields = []
            if hasattr(self, 'enhanced_drag_handler') and hasattr(self.enhanced_drag_handler, 'get_selected_fields'):
                selected_fields = self.enhanced_drag_handler.get_selected_fields()

            # Also include the primary selected field from selection handler
            if hasattr(self, 'selection_handler'):
                primary_field = self.selection_handler.get_selected_field()
                if primary_field and primary_field not in selected_fields:
                    selected_fields.append(primary_field)

            # Draw selection for each selected field
            for field in selected_fields:
                self._draw_field_selection(painter, field)

        except Exception as e:
            print(f"⚠️ Error drawing selected fields: {e}")

    def _draw_field_selection(self, painter, field):
        """Draw selection handles for a single field"""
        try:
            # Convert field coordinates to screen coordinates
            screen_coords = self.document_to_screen_coordinates(field.page_number, field.x, field.y)
            if not screen_coords:
                return

            screen_x, screen_y = screen_coords
            screen_width = field.width * self.zoom_level
            screen_height = field.height * self.zoom_level

            # Draw selection rectangle
            painter.setPen(QPen(QColor(0, 120, 255), 2))  # Blue selection
            painter.setBrush(QBrush())
            painter.drawRect(int(screen_x - 2), int(screen_y - 2),
                             int(screen_width + 4), int(screen_height + 4))

            # Draw corner handles
            handle_size = 8
            painter.setBrush(QBrush(QColor(0, 120, 255)))

            # Corner positions
            corners = [
                (screen_x - handle_size // 2, screen_y - handle_size // 2),  # Top-left
                (screen_x + screen_width - handle_size // 2, screen_y - handle_size // 2),  # Top-right
                (screen_x - handle_size // 2, screen_y + screen_height - handle_size // 2),  # Bottom-left
                (screen_x + screen_width - handle_size // 2, screen_y + screen_height - handle_size // 2)
                # Bottom-right
            ]

            for corner_x, corner_y in corners:
                painter.drawRect(int(corner_x), int(corner_y), handle_size, handle_size)

        except Exception as e:
            print(f"⚠️ Error drawing field selection: {e}")

class SafeSelectionHandler:
    """Emergency fallback SelectionHandler that never crashes"""

    def __init__(self, field_manager=None):
        self.field_manager = field_manager
        self.selected_field = None
        print("🛡️ SafeSelectionHandler initialized (emergency fallback)")

    def select_field(self, field):
        """Safe select field"""
        self.selected_field = field
        print(f"🛡️ Safe selection: {field.name if field else 'None'}")

    def clear_selection(self):
        """Safe clear selection"""
        print("🛡️ Safe clear selection")
        self.selected_field = None

    def get_selected_field(self):
        """Safe get selected field"""
        return self.selected_field

    def select_field_at_position(self, x, y):
        """Safe select at position"""
        if self.field_manager and hasattr(self.field_manager, 'get_field_at_position'):
            field = self.field_manager.get_field_at_position(x, y)
            self.select_field(field)
            return field
        return None
