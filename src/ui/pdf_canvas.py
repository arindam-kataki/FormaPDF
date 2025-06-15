"""
PDF Canvas Widget
Complete working version for displaying PDFs with scrolling and field support
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QLabel, QApplication
from PyQt6.QtGui import QPixmap, QPainter, QPen, QCursor
from PyQt6.QtCore import QObject, pyqtSignal, Qt

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
    from models.field_model import FormField, FieldType
    from ui.field_renderer import FieldRenderer
    from ui.drag_handler import DragHandler, SelectionHandler
    from ui.selection_handler import SelectionHandler
    from managers.field_manager import FieldManager
    FIELD_COMPONENTS_AVAILABLE = True
except ImportError:
    print("⚠️ Field management components not available - using minimal versions")
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
    fieldClicked = pyqtSignal(str)
    positionClicked = pyqtSignal(int, int)
    selectionChanged = pyqtSignal(object)

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
        self.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        self.setMinimumSize(400, 300)

        # Show initial message
        self.show_no_document_message()

        # Setup signal connections
        self._setup_signal_connections()

    def _init_handlers(self):
        """Initialize field and interaction handlers"""
        if FIELD_COMPONENTS_AVAILABLE:
            try:
                self.field_manager = FieldManager()
                self.selection_handler = SelectionHandler()
                self.drag_handler = DragHandler()
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
        self.drag_handler = MinimalDragHandler()
        self.field_renderer = None

    def _setup_signal_connections(self):
        """Setup signal connections with error handling"""
        try:
            # Connect drag handler signals
            if hasattr(self.drag_handler, 'cursorChanged'):
                self.drag_handler.cursorChanged.connect(
                    lambda cursor_shape: self.setCursor(QCursor(cursor_shape))
                )

            # Connect selection handler signals
            if hasattr(self.selection_handler, 'selectionChanged'):
                self.selection_handler.selectionChanged.connect(self.selectionChanged)
                # Safe connection to _on_selection_changed
                self.selection_handler.selectionChanged.connect(self._on_selection_changed)
        except Exception as e:
            print(f"Warning: Error setting up signal connections: {e}")

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
            self.field_manager.clear_all()

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
            self.setStyleSheet("border: 1px solid #ccc; background-color: white;")

            return True

        except Exception as e:
            print(f"❌ Error loading PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

    def render_page(self):
        """Render current PDF page to pixmap"""
        print(f"🎨 Rendering page {self.current_page + 1}")

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

                # Debug: Check if scrolling should be enabled
                if self.parent() and hasattr(self.parent(), 'viewport'):
                    viewport_size = self.parent().viewport().size()
                    widget_size = self.size()
                    print(f"📏 Viewport: {viewport_size.width()}x{viewport_size.height()}")
                    print(f"📏 Widget: {widget_size.width()}x{widget_size.height()}")
                    print(f"📏 Scrolling needed: H={widget_size.width() > viewport_size.width()}, V={widget_size.height() > viewport_size.height()}")

            # Update the displayed pixmap
            self.setPixmap(self.page_pixmap)

            # Update drag handler with canvas size
            if hasattr(self.drag_handler, 'set_canvas_size'):
                self.drag_handler.set_canvas_size(
                    self.page_pixmap.width(),
                    self.page_pixmap.height()
                )

            # Draw overlay (grid, fields, etc.)
            self.draw_overlay()

        except Exception as e:
            print(f"❌ Error rendering page: {e}")
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
        # Re-render with new zoom level
        self.render_page()

    def draw_overlay(self):
        """Draw overlay with fields and grid"""
        if not self.page_pixmap:
            return

        try:
            # Create a copy of the pixmap to draw on
            overlay_pixmap = self.page_pixmap.copy()
            painter = QPainter(overlay_pixmap)

            # Draw grid if enabled
            if self.show_grid:
                self._draw_grid(painter)

            # Draw fields if available
            if self.field_renderer and hasattr(self.field_renderer, 'render_fields'):
                self.field_renderer.render_fields(painter, self.field_manager.fields)

            painter.end()

            # Update the displayed pixmap
            self.setPixmap(overlay_pixmap)

        except Exception as e:
            print(f"Error drawing overlay: {e}")

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
        if hasattr(self.drag_handler, 'set_grid_settings'):
            self.drag_handler.set_grid_settings(self.grid_size, self.show_grid)
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
        if modifiers & Qt.KeyboardModifier.ControlModifier:
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
        """Enhanced keyboard event handling for fields, scrolling, and zoom"""
        key = event.key()
        modifiers = event.modifiers()

        # Get selected field state once
        selected_field = self.selection_handler.get_selected_field()

        # Priority 1: Field manipulation (arrow keys only, when field selected)
        if selected_field and key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
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

            # Move the field within bounds
            new_x = selected_field.x + dx
            new_y = selected_field.y + dy
            selected_field.x = max(0, min(new_x, self.width() - selected_field.width))
            selected_field.y = max(0, min(new_y, self.height() - selected_field.height))

            self.draw_overlay()
            event.accept()
            return  # Exit early - don't process other shortcuts

        # Priority 2: Zoom shortcuts (work regardless of field selection)
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            zoom_handled = False

            if key in [Qt.Key.Key_Plus, Qt.Key.Key_Equal]:
                if hasattr(self, 'zoom_in_step'):
                    self.zoom_in_step()
                    zoom_handled = True
            elif key == Qt.Key.Key_Minus:
                if hasattr(self, 'zoom_out_step'):
                    self.zoom_out_step()
                    zoom_handled = True
            elif key == Qt.Key.Key_0:
                if hasattr(self, 'set_zoom'):
                    self.set_zoom(1.0)  # Reset to 100%
                    zoom_handled = True

            if zoom_handled:
                event.accept()
                return  # Exit early

        # Priority 3: Navigation shortcuts (Page Up/Down, Home/End)
        # These work regardless of field selection
        navigation_handled = False

        if key == Qt.Key.Key_PageUp:
            if hasattr(self, 'scroll_page'):
                self.scroll_page(-1)
                navigation_handled = True
        elif key == Qt.Key.Key_PageDown:
            if hasattr(self, 'scroll_page'):
                self.scroll_page(1)
                navigation_handled = True
        elif key == Qt.Key.Key_Home:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if hasattr(self, 'scroll_to_top'):
                    self.scroll_to_top()
                    navigation_handled = True
            else:
                if hasattr(self, 'scroll_to_left'):
                    self.scroll_to_left()
                    navigation_handled = True
        elif key == Qt.Key.Key_End:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if hasattr(self, 'scroll_to_bottom'):
                    self.scroll_to_bottom()
                    navigation_handled = True
            else:
                if hasattr(self, 'scroll_to_right'):
                    self.scroll_to_right()
                    navigation_handled = True

        if navigation_handled:
            event.accept()
            return  # Exit early

        # Priority 4: Arrow key scrolling (ONLY when no field is selected)
        # If field is selected, arrow keys were already handled above
        if not selected_field and key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            scroll_handled = False

            if key == Qt.Key.Key_Up:
                if hasattr(self, 'scroll_vertical'):
                    self.scroll_vertical(-50)
                    scroll_handled = True
            elif key == Qt.Key.Key_Down:
                if hasattr(self, 'scroll_vertical'):
                    self.scroll_vertical(50)
                    scroll_handled = True
            elif key == Qt.Key.Key_Left:
                if hasattr(self, 'scroll_horizontal'):
                    self.scroll_horizontal(-50)
                    scroll_handled = True
            elif key == Qt.Key.Key_Right:
                if hasattr(self, 'scroll_horizontal'):
                    self.scroll_horizontal(50)
                    scroll_handled = True

            if scroll_handled:
                event.accept()
                return  # Exit early

        # Fallback: Pass unhandled events to parent
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
            if hasattr(self, 'field_manager') and self.field_manager:
                for field in self.field_manager.fields:
                    self._draw_field(painter, field)

            # Draw selection handles for selected field
            if (hasattr(self, 'selection_handler') and 
                self.selection_handler and 
                hasattr(self.selection_handler, 'selected_field') and
                self.selection_handler.selected_field):

                self._draw_selection_handles(painter, self.selection_handler.selected_field)

        except Exception as e:
            print(f"⚠️ Error in paintEvent: {e}")

    def _draw_field(self, painter, field):
        """Draw a single field"""
        try:
            from PyQt6.QtGui import QPen, QBrush, QColor
            from PyQt6.QtCore import Qt

            # Set up pen and brush
            painter.setPen(QPen(QColor(0, 0, 255), 2))
            painter.setBrush(QBrush(QColor(255, 255, 255, 100)))

            # Draw field rectangle
            painter.drawRect(field.x, field.y, field.width, field.height)

            # Draw field type text
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(field.x + 5, field.y + 15, f"{field.type.value}")

        except Exception as e:
            print(f"⚠️ Error drawing field: {e}")

    def _draw_selection_handles(self, painter, field):
        """Draw selection handles around a field"""
        try:
            from PyQt6.QtGui import QPen, QBrush, QColor

            # Draw selection rectangle
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.setBrush(QBrush())
            painter.drawRect(field.x - 2, field.y - 2, field.width + 4, field.height + 4)

            # Draw corner handles
            handle_size = 6
            painter.setBrush(QBrush(QColor(255, 0, 0)))

            positions = [
                (field.x - handle_size//2, field.y - handle_size//2),
                (field.x + field.width - handle_size//2, field.y - handle_size//2),
                (field.x - handle_size//2, field.y + field.height - handle_size//2),
                (field.x + field.width - handle_size//2, field.y + field.height - handle_size//2)
            ]

            for pos_x, pos_y in positions:
                painter.drawRect(pos_x, pos_y, handle_size, handle_size)

        except Exception as e:
            print(f"⚠️ Error drawing selection handles: {e}")

    def mousePressEvent(self, event):
        """Handle mouse press events - place selected control or select existing field"""
        print("🖱️ Mouse press event started")
        print(f"   Button: {event.button()}")
        print(f"   Position: {event.position().toPoint()}")

        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()  # Enable keyboard events
            pos = event.position().toPoint()

            # First, check if we clicked on an existing field
            selected_field = None
            try:
                selected_field = self.drag_handler.handle_mouse_press(
                    pos, self.selection_handler.get_selected_field()
                )
            except Exception as e:
                print(f"⚠️ Error in drag handler: {e}")

            if selected_field:
                # Clicked on an existing field - select it
                try:
                    self.selection_handler.select_field(selected_field)
                    print(f"✅ Selected existing field: {selected_field.id}")
                    self._handle_field_clicked(selected_field.id)
                except Exception as e:
                    print(f"⚠️ Error selecting field: {e}")
            else:
                # Clicked on empty area - try to create a new field
                new_field_created = self._try_create_field_at_position(pos.x(), pos.y())

                if not new_field_created:
                    # No field was created, just clear selection
                    try:
                        self.selection_handler.clear_selection()
                        print("✅ Cleared selection")
                    except Exception as e:
                        print(f"⚠️ Error clearing selection: {e}")

            # Update display
            try:
                self.draw_overlay()
            except Exception as e:
                print(f"⚠️ Error drawing overlay: {e}")

    def _try_create_field_at_position(self, x, y):
        """Try to create a field at the specified position using the selected control type"""
        try:
            # Get the selected field type from the main window's field palette
            field_type = self._get_selected_field_type()

            if field_type:
                # Create the field
                new_field = self._create_field_at_position(x, y, field_type)
                if new_field:
                    print(f"✅ Created {field_type} field at ({x}, {y})")

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

    def _get_selected_field_type(self):
        """Get the currently selected field type from the field palette"""
        try:
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
                return "text"

        except Exception as e:
            print(f"⚠️ Error getting selected field type: {e}")

        return None

    def _create_field_at_position(self, x, y, field_type):
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
                "number": FieldType.NUMBER
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

            # Create the field
            new_field = FormField(
                name=field_name,
                field_type=field_enum,
                x=field_x,
                y=field_y,
                width=width,
                height=height
            )

            # Add to field manager
            self.field_manager.add_field(new_field)

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
                FieldType.NUMBER: (80, 25)
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
