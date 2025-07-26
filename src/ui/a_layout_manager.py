from typing import List, Tuple, Optional
from PyQt6.QtCore import QSizeF, QRectF, QPointF


class LayoutManager:
    """Manages page positioning and coordinate transformations with configurable spacing"""

    # Layout constants - easily configurable
    PAGE_SPACING_VERTICAL = 15  # Pixels between pages vertically
    PAGE_SPACING_HORIZONTAL = 15  # Pixels on left and right of pages
    PAGE_MARGIN_TOP = 15  # Pixels above first page
    PAGE_MARGIN_BOTTOM = 15  # Pixels below last page

    def __init__(self, document, zoom: float = 1.0):
        self.document = document
        self.zoom = zoom
        self.page_positions = []  # List of QRectF for each page in canvas coordinates
        self.total_width = 0
        self.total_height = 0
        self._calculate_layout()

    def _calculate_layout(self):
        """Calculate positions for all pages with proper spacing and different page sizes"""
        self.page_positions.clear()

        if not self.document or self.document.get_page_count() == 0:
            self.total_width = 0
            self.total_height = 0
            return

        current_y = self.PAGE_MARGIN_TOP  # Start with top margin
        max_page_width = 0

        # First pass: find the maximum page width to center all pages
        for i in range(self.document.get_page_count()):
            page_size = self.document.get_page_size(i)
            canvas_width = page_size.width() * self.zoom
            max_page_width = max(max_page_width, canvas_width)

        # Second pass: position pages with centering
        for i in range(self.document.get_page_count()):
            page_size = self.document.get_page_size(i)

            # Convert from document points to canvas pixels
            canvas_width = page_size.width() * self.zoom
            canvas_height = page_size.height() * self.zoom

            # Center this page horizontally within the maximum page width
            x_offset = (max_page_width - canvas_width) / 2
            x = self.PAGE_SPACING_HORIZONTAL + x_offset

            # Create page rectangle
            page_rect = QRectF(x, current_y, canvas_width, canvas_height)
            self.page_positions.append(page_rect)

            # Move to next page position
            current_y += canvas_height + self.PAGE_SPACING_VERTICAL

        # Calculate total canvas size
        # Width: max page width + horizontal margins on both sides
        self.total_width = max_page_width + (2 * self.PAGE_SPACING_HORIZONTAL)

        # Height: last page bottom + bottom margin
        if self.page_positions:
            last_page_bottom = self.page_positions[-1].bottom()
            self.total_height = last_page_bottom + self.PAGE_MARGIN_BOTTOM
        else:
            self.total_height = self.PAGE_MARGIN_TOP + self.PAGE_MARGIN_BOTTOM

    def set_zoom(self, zoom: float):
        """Update zoom level and recalculate layout"""
        if abs(self.zoom - zoom) > 0.01:  # Avoid unnecessary recalculation
            self.zoom = zoom
            self._calculate_layout()

    def get_zoom(self) -> float:
        """Get current zoom level"""
        return self.zoom

    def get_canvas_size(self) -> Tuple[int, int]:
        """Get total canvas size needed for all pages including margins"""
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
        # Handle positions before first page
        if y_position < self.PAGE_MARGIN_TOP:
            return 0

        # Handle positions after last page
        if y_position > self.total_height - self.PAGE_MARGIN_BOTTOM:
            return max(0, len(self.page_positions) - 1)

        # Find page that contains this Y position
        for i, page_rect in enumerate(self.page_positions):
            if page_rect.top() <= y_position <= page_rect.bottom():
                return i

        # If between pages, find the closest page
        min_distance = float('inf')
        closest_page = 0

        for i, page_rect in enumerate(self.page_positions):
            # Distance to top edge
            dist_to_top = abs(y_position - page_rect.top())
            # Distance to bottom edge
            dist_to_bottom = abs(y_position - page_rect.bottom())
            distance = min(dist_to_top, dist_to_bottom)

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
        return page_rect.top() if page_rect else self.PAGE_MARGIN_TOP

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
            'vertical_spacing': self.PAGE_SPACING_VERTICAL,
            'horizontal_spacing': self.PAGE_SPACING_HORIZONTAL,
            'top_margin': self.PAGE_MARGIN_TOP,
            'bottom_margin': self.PAGE_MARGIN_BOTTOM,
            'layout_type': 'vertical_stack_centered'
        }

    def get_page_spacing_vertical(self) -> int:
        """Get current vertical page spacing"""
        return self.PAGE_SPACING_VERTICAL

    def get_page_spacing_horizontal(self) -> int:
        """Get current horizontal page spacing"""
        return self.PAGE_SPACING_HORIZONTAL

    def get_page_margins(self) -> dict:
        """Get page margins"""
        return {
            'top': self.PAGE_MARGIN_TOP,
            'bottom': self.PAGE_MARGIN_BOTTOM,
            'left': self.PAGE_SPACING_HORIZONTAL,
            'right': self.PAGE_SPACING_HORIZONTAL
        }

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

    @classmethod
    def set_layout_constants(cls, vertical_spacing: int = None, horizontal_spacing: int = None,
                             top_margin: int = None, bottom_margin: int = None):
        """Update layout constants globally"""
        if vertical_spacing is not None:
            cls.PAGE_SPACING_VERTICAL = vertical_spacing
        if horizontal_spacing is not None:
            cls.PAGE_SPACING_HORIZONTAL = horizontal_spacing
        if top_margin is not None:
            cls.PAGE_MARGIN_TOP = top_margin
        if bottom_margin is not None:
            cls.PAGE_MARGIN_BOTTOM = bottom_margin