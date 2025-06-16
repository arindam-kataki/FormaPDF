"""
Field Renderer
Handles drawing and visual representation of form fields
"""

from typing import List, Optional
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt

from models.field_model import FormField, FieldType
from utils.geometry_utils import ResizeHandles


class FieldRenderer:
    """Handles rendering of form fields on the canvas"""

    def __init__(self):
        self.selection_color = QColor(0, 120, 215)
        self.selection_bg_color = QColor(0, 120, 215, 30)
        self.normal_color = QColor(100, 100, 100)
        self.normal_bg_color = QColor(255, 255, 255, 150)
        self.handle_color = QColor(0, 120, 215)
        self.handle_bg_color = QColor(255, 255, 255)

    def render_fields(self, painter: QPainter, fields: List[FormField],
                      selected_field: Optional[FormField] = None, current_page: int = 0,
                      zoom_level: float = 1.0, coord_transform_func=None):
        """Render all form fields with zoom and coordinate transformation for multi-page support"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Filter fields for current page
        page_fields = [field for field in fields if getattr(field, 'page_number', 0) == current_page]

        print(f"🎨 Rendering {len(page_fields)} fields on page {current_page} (zoom: {zoom_level})")

        for field in page_fields:
            is_selected = field == selected_field
            self.render_single_field(painter, field, is_selected, zoom_level, coord_transform_func)

    def render_single_field(self, painter: QPainter, field: FormField, is_selected: bool = False,
                            zoom_level: float = 1.0, coord_transform_func=None):
        """Render a single form field with coordinate transformation for multi-page support"""

        # Apply coordinate transformation if available (for multi-page support)
        if coord_transform_func:
            page_num = getattr(field, 'page_number', 0)
            screen_coords = coord_transform_func(page_num, field.x, field.y)

            if not screen_coords:
                # Field is on a page that's not currently visible
                return

            screen_x, screen_y = screen_coords
            screen_width = field.width * zoom_level
            screen_height = field.height * zoom_level

            # Use screen coordinates
            x = int(screen_x)
            y = int(screen_y)
            width = int(screen_width)
            height = int(screen_height)

            print(
                f"   Field {field.name}: page {page_num} doc({field.x}, {field.y}) -> screen({x}, {y}) size({width}x{height})")
        else:
            # Fallback to direct coordinates (single page mode)
            x = int(field.x * zoom_level)
            y = int(field.y * zoom_level)
            width = int(field.width * zoom_level)
            height = int(field.height * zoom_level)

            print(f"   Field {field.name}: direct coordinates ({x}, {y}) size({width}x{height})")

        # Select colors based on selection state
        if is_selected:
            border_color = self.selection_color
            bg_color = self.selection_bg_color
            pen_width = 2
        else:
            border_color = self.normal_color
            bg_color = self.normal_bg_color
            pen_width = 1

        # Draw field background with transformed coordinates
        painter.fillRect(x, y, width, height, bg_color)

        # Draw field border with transformed coordinates
        painter.setPen(QPen(border_color, pen_width))
        painter.drawRect(x, y, width, height)

        # Draw field content with transformed coordinates
        self.render_field_content(painter, field, x, y, width, height, zoom_level)

        # Draw field name
        self.render_field_name(painter, field, x, y)

        # Draw resize handles for selected field
        if is_selected:
            self.render_resize_handles(painter, field, x, y, width, height)

    def deprecated_1_render_fields(self, painter: QPainter, fields: List[FormField],
                     selected_field: Optional[FormField] = None, current_page: int = 0):
        """Render all form fields"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Filter fields for current page
        page_fields = [field for field in fields if getattr(field, 'page_number', 0) == current_page]

        for field in page_fields:
            is_selected = field == selected_field
            self.render_single_field(painter, field, is_selected)

    def deprecated_1_render_single_field(self, painter: QPainter, field: FormField, is_selected: bool = False):
        """Render a single form field"""
        # Select colors based on selection state
        if is_selected:
            border_color = self.selection_color
            bg_color = self.selection_bg_color
            pen_width = 2
        else:
            border_color = self.normal_color
            bg_color = self.normal_bg_color
            pen_width = 1

        # CRITICAL: Convert all coordinates to integers
        x = int(field.x)
        y = int(field.y)
        width = int(field.width)
        height = int(field.height)

        # Draw field background with integer coordinates
        painter.fillRect(x, y, width, height, bg_color)

        # Draw field border with integer coordinates
        painter.setPen(QPen(border_color, pen_width))
        painter.drawRect(x, y, width, height)

        # Draw field content
        self.render_field_content(painter, field)

        # Draw field name
        self.render_field_name(painter, field)

        # Draw resize handles for selected field
        if is_selected:
            self.render_resize_handles(painter, field)

    def render_field_content(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int,
                             zoom_level: float = 1.0):
        """Render field type-specific content with transformed coordinates"""
        painter.setPen(QPen(QColor(0, 0, 0)))

        # Scale font size with zoom
        base_font_size = min(height - 4, 12)
        font_size = max(8, int(base_font_size))
        painter.setFont(QFont("Arial", font_size))

        if field.type == FieldType.TEXT:
            self._render_text_field(painter, field, x, y, width, height)
        elif field.type == FieldType.CHECKBOX:
            self._render_checkbox_field(painter, field, x, y, width, height)
        elif field.type == FieldType.DROPDOWN:
            self._render_dropdown_field(painter, field, x, y, width, height)
        elif field.type == FieldType.SIGNATURE:
            self._render_signature_field(painter, field, x, y, width, height)
        elif field.type == FieldType.DATE:
            self._render_date_field(painter, field, x, y, width, height)
        elif field.type == FieldType.BUTTON:
            self._render_button_field(painter, field, x, y, width, height)
        elif field.type == FieldType.RADIO:
            self._render_radio_field(painter, field, x, y, width, height)

    # Update all the individual field rendering methods to use transformed coordinates:

    def _render_text_field(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render text field content with transformed coordinates"""
        value = field.value if field.value else "Text Field"
        painter.drawText(x + 5, y + height // 2 + 4, str(value))

    def _render_date_field(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render date field content with transformed coordinates"""
        value = field.value if field.value else "DD/MM/YYYY"
        painter.drawText(x + 5, y + height // 2 + 4, str(value))

    def _render_checkbox_field(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render checkbox field content with transformed coordinates"""
        checkbox_size = min(width - 4, height - 4, 16)
        checkbox_x = x + (width - checkbox_size) // 2
        checkbox_y = y + (height - checkbox_size) // 2

        painter.drawRect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)

        # Draw checkmark if checked
        if field.properties.get('checked', False) or field.value:
            painter.drawLine(
                checkbox_x + 3, checkbox_y + checkbox_size // 2,
                checkbox_x + checkbox_size // 2, checkbox_y + checkbox_size - 3
            )
            painter.drawLine(
                checkbox_x + checkbox_size // 2, checkbox_y + checkbox_size - 3,
                checkbox_x + checkbox_size - 3, checkbox_y + 3
            )

    def _render_dropdown_field(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render dropdown field content with transformed coordinates"""
        text = field.value if field.value else "Select Option"
        painter.drawText(x + 5, y + height // 2 + 4, f"{text} ▼")

    def _render_signature_field(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render signature field content with transformed coordinates"""
        painter.drawText(x + 5, y + height // 2 + 4, "Signature Area")

        # Draw signature line
        line_y = y + height - 10
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawLine(x + 10, line_y, x + width - 10, line_y)

    def _render_button_field(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render button field content with transformed coordinates"""
        # Draw button-like appearance
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawRect(x + 1, y + 1, width - 2, height - 2)

        # Draw button text
        painter.setPen(QPen(QColor(0, 0, 0)))
        text = field.value if field.value else "Button"
        painter.drawText(x + 5, y + height // 2 + 4, str(text))

    def _render_radio_field(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render radio button field content with transformed coordinates"""
        radio_size = min(width - 4, height - 4, 16)
        radio_x = x + (width - radio_size) // 2
        radio_y = y + (height - radio_size) // 2

        # Draw radio button circle
        painter.drawEllipse(radio_x, radio_y, radio_size, radio_size)

        # Draw filled circle if selected
        if field.properties.get('selected', False) or field.value:
            inner_size = radio_size - 6
            inner_x = radio_x + 3
            inner_y = radio_y + 3
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.drawEllipse(inner_x, inner_y, inner_size, inner_size)
            painter.setBrush(QBrush())  # Reset brush

    def render_field_name(self, painter: QPainter, field: FormField, x: int, y: int):
        """Render field name above the field with transformed coordinates"""
        if not field.name:
            return

        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 8))

        # Position text above the field if there's space, otherwise inside
        text_rect = painter.fontMetrics().boundingRect(field.name)
        text_y = y - 2 if y > text_rect.height() else y + 12
        painter.drawText(x + 2, text_y, field.name)

    def render_resize_handles(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render resize handles around selected field with transformed coordinates"""
        handle_size = 6

        painter.setPen(QPen(self.handle_color, 1))
        painter.setBrush(QBrush(self.handle_bg_color))

        # Calculate handle positions using transformed coordinates
        positions = [
            (x - handle_size // 2, y - handle_size // 2),  # Top-left
            (x + width - handle_size // 2, y - handle_size // 2),  # Top-right
            (x - handle_size // 2, y + height - handle_size // 2),  # Bottom-left
            (x + width - handle_size // 2, y + height - handle_size // 2)  # Bottom-right
        ]

        for hx, hy in positions:
            painter.drawRect(hx, hy, handle_size, handle_size)

    def render_grid(self, painter: QPainter, width: int, height: int, grid_size: int):
        """Render grid overlay"""
        pen = QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        # Vertical lines
        for x in range(0, width, grid_size):
            painter.drawLine(x, 0, x, height)

        # Horizontal lines
        for y in range(0, height, grid_size):
            painter.drawLine(0, y, width, y)


class FieldHighlighter:
    """Handles special highlighting effects for fields"""

    @staticmethod
    def highlight_field_hover(painter: QPainter, field: FormField):
        """Add hover effect to field"""
        hover_color = QColor(0, 120, 215, 50)
        painter.fillRect(int(field.x), int(field.y), int(field.width), int(field.height), hover_color)

    @staticmethod
    def highlight_field_error(painter: QPainter, field: FormField):
        """Add error highlighting to field"""
        error_color = QColor(255, 0, 0)
        painter.setPen(QPen(error_color, 2, Qt.PenStyle.DashLine))
        painter.drawRect(int(field.x), int(field.y), int(field.width), int(field.height))

class FieldPreviewRenderer:
    """Renders field previews for drag operations"""

    @staticmethod
    def render_drag_preview(painter: QPainter, field: FormField, opacity: float = 0.7):
        """Render semi-transparent preview during drag"""
        preview_color = QColor(0, 120, 215, int(255 * opacity))
        painter.fillRect(int(field.x), int(field.y), int(field.width), int(field.height), preview_color)

        painter.setPen(QPen(QColor(0, 120, 215), 2, Qt.PenStyle.DashLine))
        painter.drawRect(int(field.x), int(field.y), int(field.width), int(field.height))

    @staticmethod
    def render_snap_guides(painter: QPainter, snap_lines: List[tuple]):
        """Render snap-to-grid or alignment guides"""
        guide_color = QColor(255, 165, 0)  # Orange
        painter.setPen(QPen(guide_color, 1, Qt.PenStyle.DotLine))

        for x1, y1, x2, y2 in snap_lines:
            painter.drawLine(x1, y1, x2, y2)