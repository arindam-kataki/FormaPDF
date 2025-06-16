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
                     selected_field: Optional[FormField] = None, current_page: int = 0):
        """Render all form fields"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Filter fields for current page
        page_fields = [field for field in fields if getattr(field, 'page_number', 0) == current_page]

        for field in page_fields:
            is_selected = field == selected_field
            self.render_single_field(painter, field, is_selected)

    def render_single_field(self, painter: QPainter, field: FormField, is_selected: bool = False):
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

    def render_field_content(self, painter: QPainter, field: FormField):
        """Render field type-specific content"""
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", min(field.height - 4, 12)))

        if field.type == FieldType.TEXT:
            self._render_text_field(painter, field)
        elif field.type == FieldType.CHECKBOX:
            self._render_checkbox_field(painter, field)
        elif field.type == FieldType.DROPDOWN:
            self._render_dropdown_field(painter, field)
        elif field.type == FieldType.SIGNATURE:
            self._render_signature_field(painter, field)
        elif field.type == FieldType.DATE:
            self._render_date_field(painter, field)
        elif field.type == FieldType.BUTTON:
            self._render_button_field(painter, field)
        elif field.type == FieldType.RADIO:
            self._render_radio_field(painter, field)

    def _render_text_field(self, painter: QPainter, field: FormField):
        """Render text field content"""
        value = field.value if field.value else "Text Field"
        painter.drawText(int(field.x + 5), int(field.y + field.height // 2 + 4), str(value))

    def _render_checkbox_field(self, painter: QPainter, field: FormField):
        """Render checkbox field content"""
        checkbox_size = min(field.width - 4, field.height - 4, 16)
        checkbox_x = field.x + (field.width - checkbox_size) // 2
        checkbox_y = field.y + (field.height - checkbox_size) // 2

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

    def _render_dropdown_field(self, painter: QPainter, field: FormField):
        """Render dropdown field content"""
        text = field.value if field.value else "Select Option"
        painter.drawText(int(field.x + 5), int(field.y + field.height // 2 + 4), f"{text} ▼")

    def _render_signature_field(self, painter: QPainter, field: FormField):
        """Render signature field content"""
        painter.drawText(int(field.x + 5), int(field.y + field.height // 2 + 4), "Signature Area")

        # Draw signature line
        line_y = field.y + field.height - 10
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawLine(int(field.x + 10), line_y, int(field.x + field.width - 10), line_y)

    def _render_date_field(self, painter: QPainter, field: FormField):
        """Render date field content"""
        value = field.value if field.value else "DD/MM/YYYY"
        painter.drawText(int(field.x + 5), int(field.y + field.height // 2 + 4), str(value))

    def _render_button_field(self, painter: QPainter, field: FormField):
        """Render button field content"""
        # Draw button-like appearance
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawRect(int(field.x + 1), int(field.y + 1), int(field.width - 2), int(field.height - 2))

        # Draw button text
        painter.setPen(QPen(QColor(0, 0, 0)))
        text = field.value if field.value else "Button"
        painter.drawText(int(field.x + 5), int(field.y + field.height // 2 + 4), str(text))

    def _render_radio_field(self, painter: QPainter, field: FormField):
        """Render radio button field content"""
        radio_size = min(field.width - 4, field.height - 4, 16)
        radio_x = int(field.x + (field.width - radio_size) // 2)
        radio_y = int(field.y + (field.height - radio_size) // 2)

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

    def render_field_name(self, painter: QPainter, field: FormField):
        """Render field name above the field"""
        if not field.name:
            return

        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 8))

        # Position text above the field if there's space, otherwise inside
        text_rect = painter.fontMetrics().boundingRect(field.name)
        text_y = field.y - 2 if field.y > text_rect.height() else field.y + 12
        painter.drawText(int(field.x + 2), int(text_y), field.name)

    def render_resize_handles(self, painter: QPainter, field: FormField):
        """Render resize handles around selected field"""
        handle_positions = ResizeHandles.get_handle_positions(
            field.x, field.y, field.width, field.height
        )
        handle_size = ResizeHandles.HANDLE_SIZE

        painter.setPen(QPen(self.handle_color, 1))
        painter.setBrush(QBrush(self.handle_bg_color))

        for handle_name, (hx, hy) in handle_positions.items():
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


class FieldPreviewRenderer:
    """Renders field previews for drag operations"""

    @staticmethod
    def render_drag_preview(painter: QPainter, field: FormField, opacity: float = 0.7):
        """Render semi-transparent preview during drag"""
        preview_color = QColor(0, 120, 215, int(255 * opacity))
        painter.fillRect(field.x, field.y, field.width, field.height, preview_color)

        painter.setPen(QPen(QColor(0, 120, 215), 2, Qt.PenStyle.DashLine))
        painter.drawRect(field.x, field.y, field.width, field.height)

    @staticmethod
    def render_snap_guides(painter: QPainter, snap_lines: List[tuple]):
        """Render snap-to-grid or alignment guides"""
        guide_color = QColor(255, 165, 0)  # Orange
        painter.setPen(QPen(guide_color, 1, Qt.PenStyle.DotLine))

        for x1, y1, x2, y2 in snap_lines:
            painter.drawLine(x1, y1, x2, y2)