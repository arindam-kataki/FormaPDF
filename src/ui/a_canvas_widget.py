from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPainter, QPixmap, QPen, QBrush
from typing import Optional, List


class CanvasWidget(QWidget):
    """Canvas widget for rendering PDF pages - listens to document signals"""

    # Signals
    pageChanged = pyqtSignal(int)  # Emitted when current page changes
    zoomChanged = pyqtSignal(float)  # Emitted when zoom level changes
    mousePositionChanged = pyqtSignal(int, float, float)  # page, doc_x, doc_y

    def __init__(self, parent=None):
        super().__init__(parent)

        # Core components
        self.document = None
        self.layout_manager = None
        self.zoom_level = 1.0
        self.current_page = 0

        # Rendering state
        self.rendered_pages = {}  # Cache for rendered page pixmaps
        self.visible_pages = []  # Currently visible page indices
        self.viewport_rect = QRectF()

        # Performance optimization
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._perform_render)
        self.render_timer.setSingleShot(True)
        self.needs_render = False

        # UI settings
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

        # Background
        self.setStyleSheet("background-color: #2b2b2b;")

    @pyqtSlot(object)
    def on_document_loaded(self, document):
        """Handle document loaded signal from main window"""
        print(f"Canvas: Document loaded with {document.get_page_count()} pages")
        self._load_document(document)

    @pyqtSlot()
    def on_document_closed(self):
        """Handle document closed signal from main window"""
        print("Canvas: Document closed")
        self._clear_document()

    def _load_document(self, document):
        """Internal method to load document into canvas"""
        self.document = document

        if document:
            from a_layout_manager import LayoutManager
            self.layout_manager = LayoutManager(document, self.zoom_level)
            self._update_canvas_size()
            self.current_page = 0
            self.pageChanged.emit(0)
            self.schedule_render()
        else:
            self._clear_document()

    def _clear_document(self):
        """Internal method to clear document from canvas"""
        self.document = None
        self.layout_manager = None
        self.rendered_pages.clear()
        self.visible_pages.clear()
        self.current_page = 0
        self.update()

    def load_document(self, document):
        """DEPRECATED: Use signals instead. Load a PDF document for display"""
        print("Warning: load_document() is deprecated. Use document signals instead.")
        self._load_document(document)

    def set_zoom(self, zoom_level: float):
        """Set zoom level and update layout"""
        zoom_level = max(0.1, min(5.0, zoom_level))  # Clamp zoom range

        if abs(self.zoom_level - zoom_level) > 0.01:  # Avoid unnecessary updates
            self.zoom_level = zoom_level

            if self.layout_manager:
                self.layout_manager.set_zoom(zoom_level)
                self._update_canvas_size()
                self.rendered_pages.clear()  # Clear cache for new zoom
                self.schedule_render()

            self.zoomChanged.emit(zoom_level)

    def get_zoom(self) -> float:
        """Get current zoom level"""
        return self.zoom_level

    def get_zoom_percent(self) -> int:
        """Get zoom as percentage"""
        return int(self.zoom_level * 100)

    def zoom_in(self, factor: float = 1.25):
        """Zoom in by factor"""
        self.set_zoom(self.zoom_level * factor)

    def zoom_out(self, factor: float = 1.25):
        """Zoom out by factor"""
        self.set_zoom(self.zoom_level / factor)

    def fit_to_width(self, available_width: int):
        """Fit page to available width"""
        if not self.document:
            return

        page_size = self.document.get_page_size(0)
        zoom = (available_width - 40) / page_size.width()  # 40px margin
        self.set_zoom(zoom)

    def fit_to_page(self, available_width: int, available_height: int):
        """Fit entire page to window"""
        if not self.document:
            return

        page_size = self.document.get_page_size(0)
        zoom_w = (available_width - 40) / page_size.width()
        zoom_h = (available_height - 40) / page_size.height()
        zoom = min(zoom_w, zoom_h)
        self.set_zoom(zoom)

    def set_visible_pages(self, page_indices: List[int], viewport_rect: QRectF):
        """Set which pages are currently visible"""
        self.visible_pages = page_indices
        self.viewport_rect = viewport_rect
        self.schedule_render()

        # Update current page if needed
        if page_indices and self.current_page not in page_indices:
            new_page = page_indices[0]  # Use first visible page
            if new_page != self.current_page:
                self.current_page = new_page
                self.pageChanged.emit(new_page)

    def get_page_at_position(self, y_position: float) -> int:
        """Get page index at Y position"""
        if self.layout_manager:
            return self.layout_manager.get_page_at_position(y_position)
        return 0

    def get_page_y_position(self, page_index: int) -> float:
        """Get Y position of page start"""
        if self.layout_manager:
            return self.layout_manager.get_page_y_position(page_index)
        return 0.0

    def get_current_page_from_scroll(self, scroll_y: float) -> int:
        """Get current page based on scroll position"""
        return self.get_page_at_position(scroll_y + 100)  # Add offset for better detection

    def get_visible_pages_in_viewport(self, viewport_rect: QRectF) -> List[int]:
        """Get list of page indices visible in viewport"""
        if self.layout_manager:
            return self.layout_manager.get_visible_pages(viewport_rect)
        return []

    def get_canvas_size(self) -> tuple:
        """Get total canvas size needed"""
        if self.layout_manager:
            return self.layout_manager.get_canvas_size()
        return (400, 300)

    def document_to_canvas_coordinates(self, page_index: int, doc_x: float, doc_y: float) -> tuple:
        """Convert document coordinates to canvas coordinates"""
        if self.layout_manager:
            from PyQt6.QtCore import QPointF
            doc_point = QPointF(doc_x, doc_y)
            canvas_point = self.layout_manager.document_to_canvas(page_index, doc_point)
            return (canvas_point.x(), canvas_point.y())
        return (0, 0)

    def canvas_to_document_coordinates(self, page_index: int, canvas_x: float, canvas_y: float) -> tuple:
        """Convert canvas coordinates to document coordinates"""
        if self.layout_manager:
            from PyQt6.QtCore import QPointF
            canvas_point = QPointF(canvas_x, canvas_y)
            doc_point = self.layout_manager.canvas_to_document(page_index, canvas_point)
            return (doc_point.x(), doc_point.y())
        return (0, 0)

    def get_page_at_canvas_position(self, canvas_x: float, canvas_y: float) -> Optional[int]:
        """Get page index at canvas position"""
        if not self.layout_manager:
            return None

        for i in range(self.document.get_page_count() if self.document else 0):
            page_rect = self.layout_manager.get_page_rect(i)
            if page_rect and page_rect.contains(canvas_x, canvas_y):
                return i
        return None

    def schedule_render(self):
        """Schedule a render update (with debouncing)"""
        self.needs_render = True
        self.render_timer.stop()
        self.render_timer.start(50)  # 50ms delay for debouncing

    def _perform_render(self):
        """Perform the actual rendering"""
        if not self.needs_render or not self.document or not self.layout_manager:
            return

        self.needs_render = False

        # Render visible pages that aren't cached
        for page_index in self.visible_pages:
            if page_index not in self.rendered_pages:
                self._render_page(page_index)

        # Clean up cache - keep only visible pages + 2 adjacent
        pages_to_keep = set(self.visible_pages)
        for page_idx in self.visible_pages:
            pages_to_keep.add(max(0, page_idx - 1))
            pages_to_keep.add(min(self.document.get_page_count() - 1, page_idx + 1))

        # Remove pages not in keep list
        pages_to_remove = [p for p in self.rendered_pages.keys() if p not in pages_to_keep]
        for page_idx in pages_to_remove:
            del self.rendered_pages[page_idx]

        self.update()  # Trigger paint event

    def _render_page(self, page_index: int):
        """Render a single page"""
        try:
            pixmap = self.document.render_page(page_index, self.zoom_level)
            self.rendered_pages[page_index] = pixmap
        except Exception as e:
            print(f"Error rendering page {page_index}: {e}")

    def _update_canvas_size(self):
        """Update canvas size based on layout"""
        if self.layout_manager:
            width, height = self.layout_manager.get_canvas_size()
            self.resize(max(width, 400), max(height, 300))

    def paintEvent(self, event):
        """Paint the visible pages"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Paint background
        painter.fillRect(self.rect(), QBrush(Qt.GlobalColor.darkGray))

        if not self.document or not self.layout_manager:
            self._paint_no_document(painter)
            return

        # Paint visible pages
        for page_index in self.visible_pages:
            self._paint_page(painter, page_index)

    def _paint_no_document(self, painter):
        """Paint message when no document is loaded"""
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No document loaded")

    def _paint_page(self, painter, page_index: int):
        """Paint a single page"""
        page_rect = self.layout_manager.get_page_rect(page_index)
        if not page_rect:
            return

        # Draw page background
        painter.fillRect(page_rect, QBrush(Qt.GlobalColor.white))

        # Draw page border
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawRect(page_rect)

        # Draw rendered content if available
        if page_index in self.rendered_pages:
            pixmap = self.rendered_pages[page_index]

            # Center the pixmap in the page rect
            x_offset = (page_rect.width() - pixmap.width()) / 2
            y_offset = (page_rect.height() - pixmap.height()) / 2

            draw_rect = QRectF(
                page_rect.left() + x_offset,
                page_rect.top() + y_offset,
                pixmap.width(),
                pixmap.height()
            )

            painter.drawPixmap(draw_rect.toRect(), pixmap)
        else:
            # Draw loading indicator
            painter.setPen(QPen(Qt.GlobalColor.gray))
            painter.drawText(page_rect, Qt.AlignmentFlag.AlignCenter, f"Loading page {page_index + 1}...")

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton and self.layout_manager:
            # Determine which page was clicked and document coordinates
            page_index = self.get_page_at_canvas_position(event.position().x(), event.position().y())

            if page_index is not None:
                doc_x, doc_y = self.canvas_to_document_coordinates(
                    page_index, event.position().x(), event.position().y()
                )

                # Emit signal with page and document coordinates
                self.mousePositionChanged.emit(page_index, doc_x, doc_y)
                print(f"Clicked on page {page_index + 1} at document coords ({doc_x:.1f}, {doc_y:.1f})")

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.layout_manager:
            page_index = self.get_page_at_canvas_position(event.position().x(), event.position().y())
            if page_index is not None:
                doc_x, doc_y = self.canvas_to_document_coordinates(
                    page_index, event.position().x(), event.position().y()
                )
                # Could emit mouse move signal here if needed

        super().mouseMoveEvent(event)