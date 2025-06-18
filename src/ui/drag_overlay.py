"""
Transparent Drag Overlay Implementation for PDF Canvas
Provides smooth dragging without repainting the underlying PDF canvas
"""

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from typing import List, Optional, Dict, Tuple, Any


class DragOverlay(QWidget):
    """
    Transparent overlay widget for handling drag operations without repainting the main canvas
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_overlay_properties()
        self.reset_drag_state()

    def setup_overlay_properties(self):
        """Configure the overlay to be transparent and handle events properly"""
        # Make overlay transparent to mouse events when not dragging
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Ensure overlay covers entire parent area
        if self.parent():
            self.resize(self.parent().size())

    def reset_drag_state(self):
        """Reset all drag-related state"""
        self.is_dragging = False
        self.drag_fields = []  # List of fields being dragged
        self.drag_start_pos = QPoint()
        self.current_drag_pos = QPoint()
        self.drag_offset = QPoint()
        self.ghost_positions = {}  # field_id -> QPoint for ghost positions
        self.zoom_level = 1.0

    def start_drag(self, fields: List[Any], start_pos: QPoint, zoom_level: float = 1.0):
        """
        Start dragging operation

        Args:
            fields: List of field objects being dragged
            start_pos: Starting position in canvas coordinates
            zoom_level: Current zoom level for proper scaling
        """
        print(f"🎯 DragOverlay: Starting drag with {len(fields)} fields at {start_pos}")

        self.is_dragging = True
        self.drag_fields = fields.copy()
        self.drag_start_pos = start_pos
        self.current_drag_pos = start_pos
        self.zoom_level = zoom_level

        # Calculate initial ghost positions
        self.update_ghost_positions()

        # Enable mouse events for the overlay during drag
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # Make overlay visible
        self.show()
        self.raise_()
        self.update()

    def update_drag(self, current_pos: QPoint):
        """
        Update drag position and redraw ghosts

        Args:
            current_pos: Current mouse position in canvas coordinates
        """
        if not self.is_dragging:
            return

        self.current_drag_pos = current_pos
        self.update_ghost_positions()

        # Only update the overlay, not the entire canvas
        self.update()

    def update_ghost_positions(self):
        """Calculate ghost positions for all dragged fields with proper page offset"""
        if not self.is_dragging or not self.drag_fields:
            return

        # Calculate drag offset
        drag_offset = self.current_drag_pos - self.drag_start_pos

        # Get canvas reference
        canvas = self.parent() if hasattr(self, 'parent') and self.parent() else None

        # Update ghost position for each field
        for field in self.drag_fields:
            if canvas and hasattr(canvas, 'document_to_screen_coordinates'):
                # ✅ USE CANVAS METHOD FOR ACCURATE SCREEN COORDINATES
                screen_coords = canvas.document_to_screen_coordinates(
                    field.page_number, field.x, field.y
                )

                if screen_coords:
                    field_screen_x, field_screen_y = screen_coords

                    # Apply drag offset to screen coordinates
                    ghost_pos = QPoint(
                        int(field_screen_x + drag_offset.x()),
                        int(field_screen_y + drag_offset.y())
                    )

                    self.ghost_positions[field.id] = ghost_pos
                    print(
                        f"🎯 Ghost for {field.name} on page {field.page_number}: screen({field_screen_x}, {field_screen_y}) + offset({drag_offset.x()}, {drag_offset.y()}) = ghost({ghost_pos.x()}, {ghost_pos.y()})")
                else:
                    print(f"⚠️ Could not get screen coordinates for {field.name} on page {field.page_number}")
            else:
                # Fallback to simple calculation
                field_rect = field.get_screen_rect(self.zoom_level) if hasattr(field, 'get_screen_rect') else QRect(0,
                                                                                                                    0,
                                                                                                                    100,
                                                                                                                    30)
                ghost_pos = QPoint(
                    field_rect.x() + drag_offset.x(),
                    field_rect.y() + drag_offset.y()
                )
                self.ghost_positions[field.id] = ghost_pos

    def deprecated_update_ghost_positions(self):
        """Calculate ghost positions for all dragged fields"""
        if not self.is_dragging or not self.drag_fields:
            return

        # Calculate drag offset
        drag_offset = self.current_drag_pos - self.drag_start_pos

        # Update ghost position for each field
        for field in self.drag_fields:
            if hasattr(field, 'get_screen_rect'):
                # Get field's current screen position
                field_rect = field.get_screen_rect(self.zoom_level)

                # Apply drag offset
                ghost_pos = QPoint(
                    field_rect.x() + drag_offset.x(),
                    field_rect.y() + drag_offset.y()
                )

                self.ghost_positions[field.id] = ghost_pos

    def end_drag(self) -> bool:
        """
        End dragging operation

        Returns:
            bool: True if drag was active and ended, False otherwise
        """
        if not self.is_dragging:
            return False

        print("✅ DragOverlay: Ending drag operation")

        was_dragging = self.is_dragging
        self.reset_drag_state()

        # Make overlay transparent to mouse events again
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Clear the overlay
        self.update()

        return was_dragging

    def cancel_drag(self):
        """Cancel current drag operation without applying changes"""
        print("❌ DragOverlay: Canceling drag operation")
        self.end_drag()

    def paintEvent(self, event):
        """Paint drag ghosts and feedback"""
        if not self.is_dragging or not self.drag_fields:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        try:
            self.draw_drag_feedback(painter)
        except Exception as e:
            print(f"⚠️ Error painting drag overlay: {e}")
        finally:
            painter.end()

    def draw_drag_feedback(self, painter: QPainter):
        """Draw visual feedback for dragged fields"""
        # Set up ghost styling
        ghost_color = QColor(100, 150, 255, 100)  # Semi-transparent blue
        ghost_border = QColor(100, 150, 255, 200)  # More opaque border

        ghost_brush = QBrush(ghost_color)
        ghost_pen = QPen(ghost_border, 2)
        painter.setBrush(ghost_brush)
        painter.setPen(ghost_pen)

        # Draw ghost for each dragged field
        for field in self.drag_fields:
            if field.id in self.ghost_positions:
                ghost_pos = self.ghost_positions[field.id]

                # Get field dimensions (scaled by zoom)
                field_width = int(field.width * self.zoom_level)
                field_height = int(field.height * self.zoom_level)

                # Draw ghost rectangle
                ghost_rect = QRect(ghost_pos.x(), ghost_pos.y(), field_width, field_height)
                painter.drawRect(ghost_rect)

                # Draw field label in ghost
                self.draw_ghost_label(painter, field, ghost_rect)

        # Draw drag guidelines/snapping hints if needed
        self.draw_drag_guidelines(painter)

    def draw_ghost_label(self, painter: QPainter, field: Any, rect: QRect):
        """Draw field label in ghost"""
        if not hasattr(field, 'name') or not field.name:
            return

        # Set up text styling
        font = QFont("Arial", max(8, int(10 * self.zoom_level)))
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255, 200)))  # Semi-transparent white

        # Calculate text position
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(field.name)

        # Center text in ghost rectangle
        text_x = rect.x() + (rect.width() - text_rect.width()) // 2
        text_y = rect.y() + (rect.height() + text_rect.height()) // 2

        painter.drawText(text_x, text_y, field.name)

    def draw_drag_guidelines(self, painter: QPainter):
        """Draw snapping guidelines or grid alignment hints"""
        # This can be extended to show:
        # - Grid snapping lines
        # - Alignment guides with other fields
        # - Drop zones
        pass

    def resizeEvent(self, event):
        """Handle parent resize to maintain overlay coverage"""
        super().resizeEvent(event)
        if self.parent():
            self.resize(self.parent().size())