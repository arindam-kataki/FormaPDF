from typing import List, Tuple, Optional
from PyQt6.QtCore import QSizeF, QRectF, QPointF


class LayoutManager:
    """Manages page positioning and coordinate transformations with full implementation"""

    def __init__(self, document, zoom: float = 1.0, page_spacing: int = 10):
        self.document = document
        self.zoom = zoom
        self.page_spacing = page_spacing  # pixels between pages
        self.page_positions = []  # List of QRectF for each page in canvas coordinates
        self.total_width = 0
        self.total_height = 0
        self._calculate_layout()

    def _calculate_layout(self):
        """Calculate positions for all pages in canvas coordinates"""
        self.page_positions.clear()

        if not self.document or self.document.get_page_count() == 0:
            self.total_width = 0
            self.total_height = 0
            return

        current_y = 0
        max_width = 0

        # Vertical stacking layout
        for i in range(self.document.get_page_count()):
            page_size = self.document.get_page_size(i)

            # Convert from document points to canvas pixels
            canvas_width = page_size.width() * self.zoom
            canvas_height = page_size.height() * self.zoom

            # Center horizontally (assuming fixed canvas width or auto-centering)
            x = 0  # Will be adjusted by canvas for centering

            page_rect = QRectF(x, current_y, canvas_width, canvas_height)
            self.page_positions.append(page_rect)

            max_width = max(max_width, canvas_width)
            current_y += canvas_height + self.page_spacing

        # Calculate total canvas size
        self.total_width = max_width
        self.total_height = current_y - self.page_spacing if current_y > 0 else 0

    def set_zoom(self, zoom: float):
        """Update zoom level and recalculate layout"""
        if abs(self.zoom - zoom) > 0.01:  # Avoid unnecessary recalculation
            self.zoom = zoom
            self._calculate_layout()

    def get_zoom(self) -> float:
        """Get current zoom level"""
        return self.zoom

    def get_canvas_size(self) -> Tuple[int, int]:
        """Get total canvas size needed for all pages"""
        return int(self.total_width), int(self.total_height)

    def get_page_rect(self, page_index: int) -> Optional[QRectF]:
        """Get page rectangle in canvas coordinates"""
        if 0 <= page_index < len(self.page_positions):
            return self.page_positions[page_index]
        return None

    def get_page_count(self) -> int:
        """Get number of pages in layout"""
        return len(self.page_positions)

    def get_visible_pages(self, viewport_rect: QRectF) -> List[int]:
        """Get list of page indices visible in viewport"""
        visible_pages = []

        for i, page_rect in enumerate(self.page_positions):
            if viewport_rect.intersects(page_rect):
                visible_pages.append(i)

        return visible_pages

    def get_page_at_position(self, y_position: float) -> int:
        """Get page index at given Y position"""
        for i, page_rect in enumerate(self.page_positions):
            if page_rect.top() <= y_position <= page_rect.bottom():
                return i

        # If not within any page, return closest
        if y_position < 0:
            return 0
        elif y_position > self.total_height:
            return len(self.page_positions) - 1

        # Find closest page
        min_distance = float('inf')
        closest_page = 0
        for i, page_rect in enumerate(self.page_positions):
            distance = min(abs(y_position - page_rect.top()),
                           abs(y_position - page_rect.bottom()))
            if distance < min_distance:
                min_distance = distance
                closest_page = i

        return closest_page

    def get_page_at_canvas_position(self, x: float, y: float) -> Optional[int]:
        """Get page index at canvas position (x, y)"""
        for i, page_rect in enumerate(self.page_positions):
            if page_rect.contains(x, y):
                return i
        return None

    def document_to_canvas(self, page_index: int, doc_point: QPointF) -> QPointF:
        """Convert document coordinates to canvas coordinates"""
        page_rect = self.get_page_rect(page_index)
        if not page_rect:
            return QPointF(0, 0)

        # Scale document point by zoom and offset by page position
        canvas_x = doc_point.x() * self.zoom + page_rect.left()
        canvas_y = doc_point.y() * self.zoom + page_rect.top()

        return QPointF(canvas_x, canvas_y)

    def canvas_to_document(self, page_index: int, canvas_point: QPointF) -> QPointF:
        """Convert canvas coordinates to document coordinates"""
        page_rect = self.get_page_rect(page_index)
        if not page_rect:
            return QPointF(0, 0)

        # Remove page offset and scale down by zoom
        doc_x = (canvas_point.x() - page_rect.left()) / self.zoom
        doc_y = (canvas_point.y() - page_rect.top()) / self.zoom

        return QPointF(doc_x, doc_y)

    def get_page_y_position(self, page_index: int) -> float:
        """Get Y position where page starts in canvas coordinates"""
        page_rect = self.get_page_rect(page_index)
        return page_rect.top() if page_rect else 0.0

    def get_page_bounds_in_canvas(self, page_index: int) -> Optional[QRectF]:
        """Get page bounds in canvas coordinates"""
        return self.get_page_rect(page_index)

    def get_page_center(self, page_index: int) -> Optional[QPointF]:
        """Get center point of page in canvas coordinates"""
        page_rect = self.get_page_rect(page_index)
        if page_rect:
            return page_rect.center()
        return None

    def is_point_on_page(self, page_index: int, canvas_point: QPointF) -> bool:
        """Check if a canvas point is on a specific page"""
        page_rect = self.get_page_rect(page_index)
        if page_rect:
            return page_rect.contains(canvas_point)
        return False

    def get_layout_info(self) -> dict:
        """Get comprehensive layout information"""
        return {
            'page_count': len(self.page_positions),
            'total_width': self.total_width,
            'total_height': self.total_height,
            'zoom_level': self.zoom,
            'page_spacing': self.page_spacing,
            'layout_type': 'vertical_stack'
        }

    def set_page_spacing(self, spacing: int):
        """Set spacing between pages and recalculate layout"""
        if self.page_spacing != spacing:
            self.page_spacing = spacing
            self._calculate_layout()

    def get_page_spacing(self) -> int:
        """Get current page spacing"""
        return self.page_spacing

    def get_page_size_in_canvas(self, page_index: int) -> Optional[QSizeF]:
        """Get page size in canvas coordinates"""
        page_rect = self.get_page_rect(page_index)
        if page_rect:
            return page_rect.size()
        return None

    def get_page_size_in_document(self, page_index: int) -> Optional[QSizeF]:
        """Get page size in document coordinates (points)"""
        if self.document and 0 <= page_index < self.document.get_page_count():
            return self.document.get_page_size(page_index)
        return None