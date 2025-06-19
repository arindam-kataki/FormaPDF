"""
Visual Resize Guides Implementation
Add visual feedback during resize operations
"""

from typing import Optional, Tuple
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics

class ResizeVisualGuide(QWidget):
    """Overlay widget that shows visual feedback during resize operations"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_overlay()
        self.reset_state()

    def setup_overlay(self):
        """Configure the overlay widget"""
        # Make overlay transparent to mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Cover entire parent
        if self.parent():
            self.resize(self.parent().size())

        # Start hidden
        self.hide()

    def reset_state(self):
        """Reset resize state"""
        self.is_resizing = False
        self.resize_field = None
        self.original_rect = None
        self.current_rect = None
        self.resize_handle = None
        self.zoom_level = 1.0
        self.show_dimensions = True
        self.show_guidelines = True

    def start_resize(self, field, handle: str, zoom_level: float = 1.0):
        """Start showing resize guides"""
        self.is_resizing = True
        self.resize_field = field
        self.resize_handle = handle
        self.zoom_level = zoom_level

        # 🔧 FIX: Use canvas coordinate conversion if available
        if hasattr(self.parent(), 'document_to_screen_coordinates'):
            screen_coords = self.parent().document_to_screen_coordinates(
                field.page_number, field.x, field.y
            )
            if screen_coords:
                screen_x, screen_y = screen_coords
                self.original_rect = QRect(
                    int(screen_x), int(screen_y),
                    int(field.width * zoom_level), int(field.height * zoom_level)
                )
            else:
                # Fallback to simple multiplication
                self.original_rect = QRect(
                    int(field.x * zoom_level), int(field.y * zoom_level),
                    int(field.width * zoom_level), int(field.height * zoom_level)
                )
        else:
            # Fallback for cases where parent doesn't have conversion method
            self.original_rect = QRect(
                int(field.x * zoom_level), int(field.y * zoom_level),
                int(field.width * zoom_level), int(field.height * zoom_level)
            )

        self.current_rect = QRect(self.original_rect)

        # Show overlay
        self.show()
        self.raise_()
        self.update()

    def update_resize(self, field):
        """Update resize preview"""
        if not self.is_resizing or not field:
            return

        # 🔧 FIX: Use canvas coordinate conversion if available
        if hasattr(self.parent(), 'document_to_screen_coordinates'):
            screen_coords = self.parent().document_to_screen_coordinates(
                field.page_number, field.x, field.y
            )
            if screen_coords:
                screen_x, screen_y = screen_coords
                self.current_rect = QRect(
                    int(screen_x), int(screen_y),
                    int(field.width * self.zoom_level), int(field.height * self.zoom_level)
                )
            else:
                # Fallback to simple multiplication
                self.current_rect = QRect(
                    int(field.x * self.zoom_level), int(field.y * self.zoom_level),
                    int(field.width * self.zoom_level), int(field.height * self.zoom_level)
                )
        else:
            # Fallback for cases where parent doesn't have conversion method
            self.current_rect = QRect(
                int(field.x * self.zoom_level), int(field.y * self.zoom_level),
                int(field.width * self.zoom_level), int(field.height * self.zoom_level)
            )

        self.update()

    def end_resize(self):
        """End resize and hide guides"""
        self.is_resizing = False
        self.hide()
        self.reset_state()

    def paintEvent(self, event):
        """Paint resize guides"""
        if not self.is_resizing:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        try:
            self.draw_resize_guides(painter)
        except Exception as e:
            print(f"⚠️ Error painting resize guides: {e}")
        finally:
            painter.end()

    def draw_resize_guides(self, painter: QPainter):
        """Draw all resize visual elements"""
        if not self.current_rect:
            return

        # Draw resize preview
        self.draw_resize_preview(painter)

        # Draw dimension labels
        if self.show_dimensions:
            self.draw_dimension_labels(painter)

        # Draw resize handles
        self.draw_resize_handles(painter)

        # Draw guidelines
        if self.show_guidelines:
            self.draw_resize_guidelines(painter)

    def draw_resize_preview(self, painter: QPainter):
        """Draw the resize preview rectangle"""
        # Semi-transparent fill
        preview_color = QColor(0, 120, 255, 80)  # Blue with transparency
        painter.fillRect(self.current_rect, preview_color)

        # Border
        border_pen = QPen(QColor(0, 120, 255), 2, Qt.PenStyle.SolidLine)
        painter.setPen(border_pen)
        painter.setBrush(QBrush())
        painter.drawRect(self.current_rect)

        # Show original size as comparison
        if self.original_rect != self.current_rect:
            original_pen = QPen(QColor(128, 128, 128), 1, Qt.PenStyle.DashLine)
            painter.setPen(original_pen)
            painter.drawRect(self.original_rect)

    def draw_dimension_labels(self, painter: QPainter):
        """Draw dimension labels showing width and height"""
        if not self.resize_field:
            return

        # Set up text styling
        font = QFont("Arial", 10)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # Background for text
        text_bg = QColor(0, 0, 0, 180)
        text_color = QColor(255, 255, 255)

        # Get actual field dimensions (not screen dimensions)
        actual_width = self.resize_field.width
        actual_height = self.resize_field.height

        # Width label (bottom center)
        width_text = f"{actual_width}px"
        width_rect = fm.boundingRect(width_text)
        width_x = self.current_rect.center().x() - width_rect.width() // 2
        width_y = self.current_rect.bottom() + 20

        width_bg_rect = QRect(width_x - 4, width_y - width_rect.height() - 2,
                              width_rect.width() + 8, width_rect.height() + 4)
        painter.fillRect(width_bg_rect, text_bg)
        painter.setPen(text_color)
        painter.drawText(width_x, width_y - 2, width_text)

        # Height label (right center)
        height_text = f"{actual_height}px"
        height_rect = fm.boundingRect(height_text)
        height_x = self.current_rect.right() + 8
        height_y = self.current_rect.center().y() + height_rect.height() // 2

        height_bg_rect = QRect(height_x - 4, height_y - height_rect.height() - 2,
                               height_rect.width() + 8, height_rect.height() + 4)
        painter.fillRect(height_bg_rect, text_bg)
        painter.drawText(height_x, height_y - 2, height_text)

        # Position label (top left)
        pos_text = f"({self.resize_field.x}, {self.resize_field.y})"
        pos_rect = fm.boundingRect(pos_text)
        pos_x = self.current_rect.left()
        pos_y = self.current_rect.top() - 8

        pos_bg_rect = QRect(pos_x - 4, pos_y - pos_rect.height() - 2,
                            pos_rect.width() + 8, pos_rect.height() + 4)
        painter.fillRect(pos_bg_rect, text_bg)
        painter.drawText(pos_x, pos_y - 2, pos_text)

    def draw_resize_handles(self, painter: QPainter):
        """Draw resize handles on the preview"""
        handle_size = 8
        handle_color = QColor(0, 120, 255)
        active_handle_color = QColor(255, 165, 0)  # Orange for active handle

        painter.setBrush(QBrush(handle_color))
        painter.setPen(QPen(QColor(255, 255, 255), 2))

        # Handle positions
        rect = self.current_rect
        handles = {
            'top_left': (rect.left() - handle_size // 2, rect.top() - handle_size // 2),
            'top_right': (rect.right() - handle_size // 2, rect.top() - handle_size // 2),
            'bottom_left': (rect.left() - handle_size // 2, rect.bottom() - handle_size // 2),
            'bottom_right': (rect.right() - handle_size // 2, rect.bottom() - handle_size // 2),
            'top': (rect.center().x() - handle_size // 2, rect.top() - handle_size // 2),
            'bottom': (rect.center().x() - handle_size // 2, rect.bottom() - handle_size // 2),
            'left': (rect.left() - handle_size // 2, rect.center().y() - handle_size // 2),
            'right': (rect.right() - handle_size // 2, rect.center().y() - handle_size // 2)
        }

        # Draw all handles
        for handle_name, (x, y) in handles.items():
            # Highlight active handle
            if handle_name == self.resize_handle:
                painter.setBrush(QBrush(active_handle_color))
            else:
                painter.setBrush(QBrush(handle_color))

            painter.drawRect(x, y, handle_size, handle_size)

    def draw_resize_guidelines(self, painter: QPainter):
        """Draw helpful guidelines during resize"""
        if not self.current_rect:
            return

        # Grid alignment guides
        guide_color = QColor(255, 165, 0, 120)  # Semi-transparent orange
        painter.setPen(QPen(guide_color, 1, Qt.PenStyle.DotLine))

        # Draw center cross
        center = self.current_rect.center()
        painter.drawLine(center.x(), 0, center.x(), self.height())
        painter.drawLine(0, center.y(), self.width(), center.y())

        # Draw edge guides
        rect = self.current_rect
        # Vertical guides at left and right edges
        painter.drawLine(rect.left(), 0, rect.left(), self.height())
        painter.drawLine(rect.right(), 0, rect.right(), self.height())

        # Horizontal guides at top and bottom edges
        painter.drawLine(0, rect.top(), self.width(), rect.top())
        painter.drawLine(0, rect.bottom(), self.width(), rect.bottom())

