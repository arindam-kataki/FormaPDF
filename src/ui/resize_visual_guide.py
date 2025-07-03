# Fix for resize_visual_guide.py
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QPen, QBrush, QPainter, QColor, QFont, QFontMetrics
from PyQt6.QtWidgets import QWidget


class ResizeVisualGuide(QWidget):
    """Overlay widget that shows visual feedback during resize operations"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize all attributes FIRST before calling any methods
        self.is_resizing = False
        self.resize_field = None
        self.original_rect = None
        self.current_rect = None
        self.resize_handle = None
        self.zoom_level = 1.0
        self.show_dimensions = True
        self.show_guidelines = True

        # Add anchor tracking attributes
        self.resize_anchor_point = None
        self.original_field_pos = None
        self.original_field_size = None

        # NOW it's safe to call setup methods
        try:
            self.setup_overlay()
        except Exception as e:
            print(f"⚠️ Error in setup_overlay: {e}")
            # Fallback setup
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setStyleSheet("background: transparent;")
            self.hide()

    def setup_overlay(self):
        """Configure the overlay widget"""
        # Make overlay transparent to mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Cover entire parent
        if self.parent():
            try:
                self.resize(self.parent().size())
            except Exception as e:
                print(f"⚠️ Error resizing overlay: {e}")
                # Use a default size if parent size fails
                self.resize(800, 600)

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

        # Reset anchor tracking
        self.resize_anchor_point = None
        self.original_field_pos = None
        self.original_field_size = None

    def set_zoom_level(self, zoom_level: float):
        """Update zoom level for visual guide"""
        self.zoom_level = zoom_level
        if self.is_resizing and self.resize_field:
            self.update_resize(self.resize_field)

    def start_resize(self, field, handle: str, zoom_level: float = 1.0):
        """Start showing resize guides with proper anchor tracking"""
        print(f"🔧 ResizeVisualGuide: Starting resize {handle} with zoom {zoom_level:.2f}x")

        try:
            self.is_resizing = True
            self.resize_field = field
            self.resize_handle = handle
            self.zoom_level = zoom_level

            # Store original field state for anchor calculation
            self.original_field_pos = (field.x, field.y)
            self.original_field_size = (field.width, field.height)

            # Calculate anchor point based on resize handle
            self.resize_anchor_point = self._calculate_anchor_point(field, handle)

            print(f"🔧 Original field: pos({field.x}, {field.y}) size({field.width}x{field.height})")
            print(f"🔧 Anchor point: {self.resize_anchor_point}")

            # Calculate initial screen rectangle
            self._calculate_initial_screen_rect(field, zoom_level)

            # Show overlay
            self.show()
            self.raise_()
            self.update()

        except Exception as e:
            print(f"❌ Error in start_resize: {e}")
            import traceback
            traceback.print_exc()

    def _calculate_anchor_point(self, field, handle):
        """Calculate the anchor point that should remain fixed during resize"""
        # The anchor is the opposite corner/edge from the resize handle
        anchor_map = {
            'bottom_right': (field.x, field.y),  # Top-left stays fixed
            'bottom_left': (field.x + field.width, field.y),  # Top-right stays fixed
            'top_right': (field.x, field.y + field.height),  # Bottom-left stays fixed
            'top_left': (field.x + field.width, field.y + field.height),  # Bottom-right stays fixed
            'right': (field.x, field.y),  # Left edge stays fixed
            'left': (field.x + field.width, field.y),  # Right edge stays fixed
            'bottom': (field.x, field.y),  # Top edge stays fixed
            'top': (field.x, field.y + field.height),  # Bottom edge stays fixed
        }
        return anchor_map.get(handle, (field.x, field.y))

    def _calculate_initial_screen_rect(self, field, zoom_level):
        """Calculate initial screen rectangle for the field"""
        try:
            if hasattr(self.parent(), 'document_to_screen_coordinates'):
                screen_coords = self.parent().document_to_screen_coordinates(
                    getattr(field, 'page_number', 0), field.x, field.y
                )
                if screen_coords:
                    screen_x, screen_y = screen_coords

                    # Calculate dimensions using coordinate conversion
                    bottom_right_coords = self.parent().document_to_screen_coordinates(
                        getattr(field, 'page_number', 0),
                        field.x + field.width,
                        field.y + field.height
                    )

                    if bottom_right_coords:
                        screen_width = int(bottom_right_coords[0] - screen_x)
                        screen_height = int(bottom_right_coords[1] - screen_y)
                    else:
                        screen_width = int(field.width * zoom_level)
                        screen_height = int(field.height * zoom_level)

                    self.original_rect = QRect(int(screen_x), int(screen_y), screen_width, screen_height)
                else:
                    # Fallback
                    self.original_rect = QRect(
                        int(field.x * zoom_level), int(field.y * zoom_level),
                        int(field.width * zoom_level), int(field.height * zoom_level)
                    )
            else:
                # Simple fallback
                self.original_rect = QRect(
                    int(field.x * zoom_level), int(field.y * zoom_level),
                    int(field.width * zoom_level), int(field.height * zoom_level)
                )

            self.current_rect = QRect(self.original_rect)

        except Exception as e:
            print(f"❌ Error calculating initial screen rect: {e}")
            # Emergency fallback
            self.original_rect = QRect(0, 0, 100, 30)
            self.current_rect = QRect(self.original_rect)

    def update_resize(self, field):
        """Update resize preview using anchor-based positioning"""
        if not self.is_resizing or not field:
            return

        try:
            print(f"🔧 Updating resize ghost: field now at ({field.x}, {field.y}) size({field.width}x{field.height})")

            # For now, use simple approach until anchor logic is fully tested
            if hasattr(self.parent(), 'document_to_screen_coordinates'):
                screen_coords = self.parent().document_to_screen_coordinates(
                    getattr(field, 'page_number', 0), field.x, field.y
                )

                if screen_coords:
                    screen_x, screen_y = screen_coords

                    # Calculate dimensions using coordinate conversion
                    bottom_right_coords = self.parent().document_to_screen_coordinates(
                        getattr(field, 'page_number', 0),
                        field.x + field.width,
                        field.y + field.height
                    )

                    if bottom_right_coords:
                        screen_width = int(bottom_right_coords[0] - screen_x)
                        screen_height = int(bottom_right_coords[1] - screen_y)
                    else:
                        screen_width = int(field.width * self.zoom_level)
                        screen_height = int(field.height * self.zoom_level)

                    self.current_rect = QRect(int(screen_x), int(screen_y), screen_width, screen_height)
                else:
                    # Fallback
                    self.current_rect = QRect(
                        int(field.x * self.zoom_level), int(field.y * self.zoom_level),
                        int(field.width * self.zoom_level), int(field.height * self.zoom_level)
                    )
            else:
                # Simple fallback
                self.current_rect = QRect(
                    int(field.x * self.zoom_level), int(field.y * self.zoom_level),
                    int(field.width * self.zoom_level), int(field.height * self.zoom_level)
                )

            self.update()

        except Exception as e:
            print(f"❌ Error in update_resize: {e}")
            import traceback
            traceback.print_exc()

    def end_resize(self):
        """End resize and hide guides"""
        try:
            self.is_resizing = False
            self.hide()
            self.reset_state()
        except Exception as e:
            print(f"❌ Error in end_resize: {e}")

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

        try:
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

        except Exception as e:
            print(f"❌ Error in draw_resize_guides: {e}")

    def draw_resize_preview(self, painter: QPainter):
        """Draw the resize preview rectangle"""
        try:
            # Semi-transparent fill
            preview_color = QColor(0, 120, 255, 80)  # Blue with transparency
            painter.fillRect(self.current_rect, preview_color)

            # Border
            border_pen = QPen(QColor(0, 120, 255), 2, Qt.PenStyle.SolidLine)
            painter.setPen(border_pen)
            painter.setBrush(QBrush())
            painter.drawRect(self.current_rect)

            # Show original size as comparison
            if self.original_rect and self.original_rect != self.current_rect:
                original_pen = QPen(QColor(128, 128, 128), 1, Qt.PenStyle.DashLine)
                painter.setPen(original_pen)
                painter.drawRect(self.original_rect)

        except Exception as e:
            print(f"❌ Error in draw_resize_preview: {e}")

    def draw_dimension_labels(self, painter: QPainter):
        """Draw dimension labels showing width and height"""
        if not self.resize_field:
            return

        try:
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

        except Exception as e:
            print(f"❌ Error in draw_dimension_labels: {e}")

    def draw_resize_handles(self, painter: QPainter):
        """Draw resize handles on the preview"""
        try:
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

        except Exception as e:
            print(f"❌ Error in draw_resize_handles: {e}")

    def draw_resize_guidelines(self, painter: QPainter):
        """Draw helpful guidelines during resize"""
        # Skip guidelines for now to avoid any additional errors
        pass