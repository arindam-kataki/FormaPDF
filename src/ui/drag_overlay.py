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

    def deprecated_calculate_zoom_aware_ghost_position(self, field, doc_offset_x, doc_offset_y, canvas):
        """Fallback method for zoom-aware ghost positioning"""
        field_page = getattr(field, 'page_number', 0)

        try:
            # Calculate new field position in document coordinates
            new_field_doc_x = field.x + doc_offset_x
            new_field_doc_y = field.y + doc_offset_y

            # Convert to screen coordinates manually
            ghost_screen_x = int(new_field_doc_x * self.zoom_level)
            ghost_screen_y = int(new_field_doc_y * self.zoom_level)

            # Add page offset for multi-page documents
            page_offset_y = self._get_page_offset_y(field_page, canvas)
            ghost_screen_y += page_offset_y

            # Account for scroll position
            if canvas and hasattr(canvas, 'horizontalScrollBar') and hasattr(canvas, 'verticalScrollBar'):
                scroll_x = canvas.horizontalScrollBar().value()
                scroll_y = canvas.verticalScrollBar().value()
                ghost_screen_x -= scroll_x
                ghost_screen_y -= scroll_y

            # Account for canvas margins
            canvas_margin_x = getattr(canvas, 'canvas_margin_x', 0)
            canvas_margin_y = getattr(canvas, 'canvas_margin_y', 0)
            ghost_screen_x += canvas_margin_x
            ghost_screen_y += canvas_margin_y

            ghost_pos = QPoint(ghost_screen_x, ghost_screen_y)
            self.ghost_positions[field.id] = ghost_pos

            print(
                f"   {field.name} (fallback): new_doc({new_field_doc_x:.1f}, {new_field_doc_y:.1f}) -> screen({ghost_screen_x}, {ghost_screen_y})")

        except Exception as e:
            print(f"❌ Error calculating zoom-aware ghost position for {field.name}: {e}")
            # Last resort: direct screen offset (will be wrong at zoom != 1.0)
            if hasattr(field, 'get_screen_rect'):
                field_rect = field.get_screen_rect(self.zoom_level)
                screen_cursor_offset = self.current_drag_pos - self.drag_start_pos
                ghost_pos = QPoint(
                    field_rect.x() + screen_cursor_offset.x(),
                    field_rect.y() + screen_cursor_offset.y()
                )
            else:
                ghost_pos = QPoint(
                    self.current_drag_pos.x() - 50,
                    self.current_drag_pos.y() - 15
                )
            self.ghost_positions[field.id] = ghost_pos

    """
    Multi-Page Drag Ghost Fix v2.1
    Author: Claude Assistant
    Date: 2025-06-20
    Purpose: Fix drag ghost visibility on non-first pages in multi-page PDF documents

    Changes in v2.1:
    - Fixed coordinate conversion for multi-page documents
    - Added zoom-aware ghost positioning
    - Enhanced debugging and validation
    - Improved fallback handling for page offset calculation
    - Added visual debug indicators (removable)
    """

    def deprecated_update_ghost_positions(self):
        """
        Calculate ghost positions with proper multi-page support
        Version: 2.1
        """
        if not self.is_dragging or not self.drag_fields:
            return

        print(f"🎯 [v2.1] Updating ghost positions for {len(self.drag_fields)} fields")

        # v2.1: Convert screen drag offset to document coordinates first
        screen_drag_offset = self.current_drag_pos - self.drag_start_pos
        doc_drag_offset_x = screen_drag_offset.x() / self.zoom_level
        doc_drag_offset_y = screen_drag_offset.y() / self.zoom_level

        print(f"   Screen drag offset: {screen_drag_offset}")
        print(f"   Document drag offset: ({doc_drag_offset_x:.1f}, {doc_drag_offset_y:.1f})")
        print(f"   Zoom level: {self.zoom_level:.2f}x")

        # Get canvas reference for coordinate conversion
        canvas = self.parent() if hasattr(self, 'parent') and self.parent() else None

        # Process each dragged field
        for field in self.drag_fields:
            page_number = getattr(field, 'page_number', 0)

            try:
                # v2.1: Calculate new field position in document coordinates
                new_field_doc_x = field.x + doc_drag_offset_x
                new_field_doc_y = field.y + doc_drag_offset_y

                print(f"   Field {field.name} on page {page_number}:")
                print(f"     Original doc: ({field.x}, {field.y})")
                print(f"     New doc: ({new_field_doc_x:.1f}, {new_field_doc_y:.1f})")

                # v2.1: Convert new document position to screen coordinates
                if canvas and hasattr(canvas, 'document_to_screen_coordinates'):
                    screen_coords = canvas.document_to_screen_coordinates(
                        page_number, new_field_doc_x, new_field_doc_y
                    )

                    if screen_coords:
                        ghost_screen_x, ghost_screen_y = screen_coords
                        ghost_pos = QPoint(int(ghost_screen_x), int(ghost_screen_y))
                        self.ghost_positions[field.id] = ghost_pos

                        print(f"     Ghost screen: ({ghost_screen_x}, {ghost_screen_y})")

                        # v2.1: Validate ghost position is within reasonable bounds
                        if self._validate_ghost_position(ghost_pos, canvas):
                            print(f"     ✅ Valid ghost position for {field.name}")
                        else:
                            print(f"     ⚠️ Ghost position may be off-screen for {field.name}")

                        continue
                    else:
                        print(f"     ❌ Canvas coordinate conversion failed")

                # v2.1: Enhanced fallback calculation with manual page offset
                print(f"     Using v2.1 fallback calculation...")
                self._calculate_multi_page_ghost_fallback(field, new_field_doc_x, new_field_doc_y, canvas)

            except Exception as e:
                print(f"❌ [v2.1] Error calculating ghost for {field.name}: {e}")
                # Emergency fallback - position near cursor
                self.ghost_positions[field.id] = QPoint(
                    self.current_drag_pos.x() - 50,
                    self.current_drag_pos.y() - 15
                )

    def _calculate_multi_page_ghost_fallback(self, field, new_doc_x, new_doc_y, canvas):
        """
        Fallback calculation for multi-page ghost positioning
        Version: 2.1 - Enhanced page offset handling
        """
        try:
            page_number = getattr(field, 'page_number', 0)

            # v2.1: Manual conversion from document to screen coordinates
            page_relative_x = new_doc_x * self.zoom_level
            page_relative_y = new_doc_y * self.zoom_level

            # v2.1: Get page top position from canvas
            page_top = 0
            if canvas and hasattr(canvas, 'page_positions') and canvas.page_positions:
                if page_number < len(canvas.page_positions):
                    page_top = canvas.page_positions[page_number]
                    print(f"     [v2.1] Page {page_number} top position: {page_top}")
                else:
                    print(f"     ⚠️ [v2.1] Page {page_number} not found in page_positions")
                    # v2.1: Calculate page offset manually if page_positions incomplete
                    page_top = self._estimate_page_top(page_number, canvas)

            # v2.1: Calculate final screen coordinates with proper margins
            ghost_screen_x = int(page_relative_x + 10)  # Add horizontal margin
            ghost_screen_y = int(page_relative_y + page_top)

            # v2.1: Account for scroll position
            if canvas and hasattr(canvas, 'parent') and hasattr(canvas.parent(), 'verticalScrollBar'):
                scroll_y = canvas.parent().verticalScrollBar().value()
                ghost_screen_y -= scroll_y
                print(f"     [v2.1] Adjusted for scroll: -{scroll_y}")

            # v2.1: Store calculated ghost position
            ghost_pos = QPoint(ghost_screen_x, ghost_screen_y)
            self.ghost_positions[field.id] = ghost_pos

            print(f"     [v2.1] Fallback ghost: ({ghost_screen_x}, {ghost_screen_y})")

        except Exception as e:
            print(f"❌ [v2.1] Fallback calculation failed: {e}")

    def _estimate_page_top(self, page_number, canvas):
        """
        Estimate page top position when page_positions is incomplete
        Version: 2.1
        """
        try:
            if page_number == 0:
                return 0

            # v2.1: Calculate based on page height and spacing
            if canvas and hasattr(canvas, 'pdf_document') and canvas.pdf_document:
                total_height = 0
                for i in range(page_number):
                    if i < canvas.pdf_document.page_count:
                        page = canvas.pdf_document[i]
                        page_height = page.rect.height * self.zoom_level
                        page_spacing = 20  # Default spacing between pages
                        total_height += page_height + page_spacing

                print(f"     [v2.1] Estimated page {page_number} top: {total_height}")
                return int(total_height)
        except Exception as e:
            print(f"⚠️ [v2.1] Page estimation failed: {e}")

        return 0

    def _validate_ghost_position(self, ghost_pos, canvas):
        """
        Validate that ghost position is within visible bounds
        Version: 2.1 - Enhanced validation logic
        """
        try:
            if not canvas:
                return True  # Can't validate without canvas

            # v2.1: Get canvas dimensions for validation
            canvas_width = canvas.width()
            canvas_height = canvas.height()

            # v2.1: Check if ghost is within reasonable bounds (allow off-screen tolerance)
            tolerance = 200  # Increased tolerance for better UX
            valid_x = -tolerance <= ghost_pos.x() <= canvas_width + tolerance
            valid_y = -tolerance <= ghost_pos.y() <= canvas_height + tolerance

            return valid_x and valid_y

        except Exception:
            return True  # Default to valid if validation fails

    def draw_drag_feedback(self, painter: QPainter):
        """
        Draw multi-page aware visual feedback for dragged fields
        Version: 2.1 - Enhanced visibility and debugging
        """
        if not self.is_dragging or not self.drag_fields:
            return

        print(f"🎨 [v2.1] Drawing ghosts for {len(self.drag_fields)} fields")

        # v2.1: Enhanced ghost styling for better visibility
        ghost_color = QColor(100, 150, 255, 140)  # Semi-transparent blue
        ghost_border = QColor(50, 100, 255, 255)  # Solid blue border

        # v2.1: Scale border thickness with zoom level
        border_thickness = max(1, int(2 * self.zoom_level))

        ghost_brush = QBrush(ghost_color)
        ghost_pen = QPen(ghost_border, border_thickness)
        painter.setBrush(ghost_brush)
        painter.setPen(ghost_pen)

        ghosts_drawn = 0

        # v2.1: Draw ghost for each dragged field
        for field in self.drag_fields:
            if field.id in self.ghost_positions:
                ghost_pos = self.ghost_positions[field.id]
                page_number = getattr(field, 'page_number', 0)

                print(f"   [v2.1] Drawing ghost for {field.name} (page {page_number}) at {ghost_pos}")

                # v2.1: Get field dimensions scaled by zoom
                field_width = int(getattr(field, 'width', 100) * self.zoom_level)
                field_height = int(getattr(field, 'height', 30) * self.zoom_level)

                # v2.1: Create ghost rectangle
                ghost_rect = QRect(ghost_pos.x(), ghost_pos.y(), field_width, field_height)

                # v2.1: DEBUG FEATURE - Draw page indicator for non-first pages (REMOVABLE)
                if page_number > 0:
                    # Draw small red page indicator for debugging
                    painter.setPen(QPen(QColor(255, 0, 0), 1))
                    painter.drawText(ghost_pos.x() - 20, ghost_pos.y() - 5, f"P{page_number}")
                    painter.setPen(ghost_pen)  # Restore ghost pen

                # v2.1: Draw the main ghost rectangle
                painter.drawRect(ghost_rect)

                # v2.1: Draw field label with proper scaling
                self._draw_multi_page_ghost_label(painter, field, ghost_rect)

                ghosts_drawn += 1
            else:
                page_number = getattr(field, 'page_number', 0)
                print(f"   ❌ [v2.1] No ghost position for {field.name} on page {page_number}")

        print(f"✅ [v2.1] Drew {ghosts_drawn}/{len(self.drag_fields)} multi-page ghosts")

        # v2.1: DEBUG FEATURE - Draw cursor indicator (REMOVABLE)
        self._draw_debug_cursor_indicator(painter)

    def _draw_multi_page_ghost_label(self, painter, field, rect):
        """
        Draw field label with zoom-aware scaling
        Version: 2.1
        """
        if not hasattr(field, 'name') or not field.name:
            return

        # v2.1: Scale font size with zoom level (capped for readability)
        base_font_size = 10
        scaled_font_size = max(7, int(base_font_size * min(self.zoom_level, 1.5)))
        font = QFont("Arial", scaled_font_size)

        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255, 230)))  # White text

        # v2.1: Calculate centered text position
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(field.name)

        text_x = rect.x() + (rect.width() - text_rect.width()) // 2
        text_y = rect.y() + (rect.height() + text_rect.height()) // 2

        painter.drawText(text_x, text_y, field.name)

    def _draw_debug_cursor_indicator(self, painter):
        """
        Draw cursor position indicator for debugging
        Version: 2.1 - DEBUG FEATURE (REMOVABLE)

        NOTE: Remove this method in production for cleaner visuals
        """
        if not self.is_dragging:
            return

        cursor_x = self.current_drag_pos.x()
        cursor_y = self.current_drag_pos.y()

        # v2.1: Draw red crosshair at cursor position
        painter.setPen(QPen(QColor(255, 100, 100, 180), 2))
        painter.drawLine(cursor_x - 10, cursor_y, cursor_x + 10, cursor_y)  # Horizontal
        painter.drawLine(cursor_x, cursor_y - 10, cursor_x, cursor_y + 10)  # Vertical

        # v2.1: Draw cursor coordinates text
        painter.setPen(QPen(QColor(255, 255, 255, 200)))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(cursor_x + 15, cursor_y - 5, f"({cursor_x}, {cursor_y})")

    def debug_multi_page_ghost_setup(self):
        """
        Debug multi-page ghost positioning setup
        Version: 2.1 - DEBUG METHOD (REMOVABLE)

        Call this method to troubleshoot ghost positioning issues
        """
        canvas = self.parent() if hasattr(self, 'parent') and self.parent() else None

        print("🐛 [v2.1] Multi-Page Ghost Debug Report:")
        print(f"   Version: 2.1")
        print(f"   Zoom level: {self.zoom_level:.2f}x")
        print(f"   Currently dragging: {self.is_dragging}")
        print(f"   Number of drag fields: {len(self.drag_fields) if self.drag_fields else 0}")
        print(f"   Ghost positions calculated: {len(self.ghost_positions)}")

        if canvas:
            print(f"   Canvas size: {canvas.width()}x{canvas.height()}")

            if hasattr(canvas, 'page_positions'):
                print(f"   Page positions available: {len(canvas.page_positions) if canvas.page_positions else 0}")
                if canvas.page_positions:
                    print(f"   Page positions: {canvas.page_positions[:5]}...")  # Show first 5
            else:
                print("   ⚠️ No page_positions attribute on canvas")

            if hasattr(canvas, 'document_to_screen_coordinates'):
                print("   ✅ Canvas has document_to_screen_coordinates method")
            else:
                print("   ❌ Canvas missing document_to_screen_coordinates method")

            if hasattr(canvas, 'pdf_document') and canvas.pdf_document:
                print(f"   PDF document: {canvas.pdf_document.page_count} pages")
            else:
                print("   ⚠️ No PDF document loaded")
        else:
            print("   ❌ No canvas parent found")

        if self.drag_fields:
            print("   Field Details:")
            for i, field in enumerate(self.drag_fields):
                page_num = getattr(field, 'page_number', 0)
                has_ghost = field.id in self.ghost_positions
                ghost_pos = self.ghost_positions.get(field.id, "None")
                print(f"     {i + 1}. {field.name}: page {page_num}, ghost: {ghost_pos}, valid: {has_ghost}")

    def start_drag(self, fields: List[Any], start_pos: QPoint, zoom_level: float = 1.0):
        """
        Start dragging operation with v2.1 enhancements
        Version: 2.1
        """
        print(f"🎯 [v2.1] Starting drag with {len(fields)} fields at {start_pos}")

        self.is_dragging = True
        self.drag_fields = fields.copy()
        self.drag_start_pos = start_pos
        self.current_drag_pos = start_pos
        self.zoom_level = zoom_level

        # v2.1: Clear any previous ghost positions
        self.ghost_positions.clear()

        # v2.1: Calculate initial ghost positions
        self.update_ghost_positions()

        # v2.1: Enable mouse events for the overlay during drag
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # v2.1: Make overlay visible and bring to front
        self.show()
        self.raise_()
        self.update()

        print(f"✅ [v2.1] Drag initialization complete: {len(self.ghost_positions)} ghosts positioned")

    """
    INSTALLATION INSTRUCTIONS for v2.1:

    1. Replace the following methods in your src/ui/drag_overlay.py file:
       - update_ghost_positions()
       - draw_drag_feedback()
       - start_drag()

    2. Add these new helper methods:
       - _calculate_multi_page_ghost_fallback()
       - _estimate_page_top()
       - _validate_ghost_position()
       - _draw_multi_page_ghost_label()

    3. OPTIONAL DEBUG FEATURES (remove in production):
       - _draw_debug_cursor_indicator()
       - debug_multi_page_ghost_setup()

    4. TEST with multi-page documents at various zoom levels

    5. To remove debug features in production:
       - Remove calls to _draw_debug_cursor_indicator() in draw_drag_feedback()
       - Remove page indicator drawing in draw_drag_feedback()
       - Remove debug_multi_page_ghost_setup() method

    EXPECTED RESULTS:
    - Drag ghosts visible on all pages
    - Proper zoom-aware positioning
    - Smooth cursor following
    - Red debug indicators show page numbers and cursor (removable)
    """

    # Enhanced drag handler methods with zoom awareness
    def set_zoom_level(self, zoom_level: float):
        """Update zoom level for accurate drag calculations"""
        self.zoom_level = zoom_level
        print(f"🔍 Drag handler zoom level updated to {zoom_level:.2f}x")

        # Update overlay zoom level
        if hasattr(self, 'drag_overlay') and self.drag_overlay:
            self.drag_overlay.zoom_level = zoom_level

    def start_drag(self, fields, start_pos, zoom_level=1.0):
        """Start dragging operation with zoom level"""
        print(f"🎯 Starting zoom-aware drag: {len(fields)} fields at {start_pos} (zoom: {zoom_level:.2f}x)")

        self.is_dragging = True
        self.drag_fields = fields.copy()
        self.drag_start_pos = start_pos
        self.current_drag_pos = start_pos
        self.zoom_level = zoom_level  # ✅ Store zoom level

        # Calculate initial ghost positions
        self.update_ghost_positions()

        # Enable mouse events and show overlay
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.show()
        self.raise_()
        self.update()

    def debug_zoom_calculations(self):
        """Debug helper to verify zoom calculations"""
        if not self.is_dragging:
            print("🐛 Not currently dragging")
            return

        screen_offset = self.current_drag_pos - self.drag_start_pos
        doc_offset_x = screen_offset.x() / self.zoom_level
        doc_offset_y = screen_offset.y() / self.zoom_level

        print(f"🐛 Zoom Debug (zoom: {self.zoom_level:.2f}x):")
        print(f"   Drag start: {self.drag_start_pos}")
        print(f"   Current cursor: {self.current_drag_pos}")
        print(f"   Screen offset: {screen_offset}")
        print(f"   Document offset: ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

        for field in self.drag_fields:
            if field.id in self.ghost_positions:
                ghost_pos = self.ghost_positions[field.id]
                print(
                    f"   {field.name}: original_doc({field.x}, {field.y}) -> ghost_screen({ghost_pos.x()}, {ghost_pos.y()})")

    def _is_ghost_position_valid(self, ghost_pos):
        """Validate that ghost position is within reasonable bounds"""
        return (-500 <= ghost_pos.x() <= 3000 and -500 <= ghost_pos.y() <= 3000)

    def _draw_cursor_indicator(self, painter):
        """Draw a small indicator at cursor position for debugging (optional)"""
        if not self.is_dragging:
            return

        # Draw small crosshair at cursor position
        cursor_x = self.current_drag_pos.x()
        cursor_y = self.current_drag_pos.y()

        painter.setPen(QPen(QColor(255, 0, 0, 150), 1))  # Red, semi-transparent
        painter.drawLine(cursor_x - 5, cursor_y, cursor_x + 5, cursor_y)  # Horizontal line
        painter.drawLine(cursor_x, cursor_y - 5, cursor_x, cursor_y + 5)  # Vertical line

    def deprecated_1_update_ghost_positions(self):
        """Calculate ghost positions for all dragged fields with proper page offset handling"""
        if not self.is_dragging or not self.drag_fields:
            return

        # Calculate drag offset
        drag_offset = self.current_drag_pos - self.drag_start_pos

        # Get canvas reference
        canvas = self.parent() if hasattr(self, 'parent') and self.parent() else None

        print(f"🎯 Updating ghost positions for {len(self.drag_fields)} fields with offset {drag_offset}")

        # Update ghost position for each field
        for field in self.drag_fields:
            field_page = getattr(field, 'page_number', 0)

            # Try to use canvas method for accurate screen coordinates
            if canvas and hasattr(canvas, 'document_to_screen_coordinates'):
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
                    print(f"✅ Ghost for {field.name} on page {field_page}: "
                          f"doc({field.x}, {field.y}) -> screen({field_screen_x}, {field_screen_y}) "
                          f"+ offset({drag_offset.x()}, {drag_offset.y()}) = ghost({ghost_pos.x()}, {ghost_pos.y()})")
                else:
                    print(f"⚠️ Canvas method failed for {field.name} on page {field_page}, using fallback")
                    self._calculate_fallback_ghost_position(field, drag_offset, canvas)
            else:
                print(f"⚠️ No canvas document_to_screen_coordinates method, using fallback for {field.name}")
                self._calculate_fallback_ghost_position(field, drag_offset, canvas)

    def _calculate_fallback_ghost_position(self, field, drag_offset, canvas):
        """Fallback method to calculate ghost position with proper page offset"""
        field_page = getattr(field, 'page_number', 0)

        # Calculate page offset
        page_offset_y = 0
        if canvas and hasattr(canvas, 'get_page_offset'):
            # Use canvas method if available
            page_offset_y = canvas.get_page_offset(field_page)
        elif canvas and hasattr(canvas, 'page_height') and hasattr(canvas, 'page_spacing'):
            # Calculate page offset manually
            page_height = getattr(canvas, 'page_height', 792)  # Default PDF page height
            page_spacing = getattr(canvas, 'page_spacing', 20)  # Space between pages
            page_offset_y = field_page * (page_height * self.zoom_level + page_spacing)

        # Get field dimensions and position
        if hasattr(field, 'get_screen_rect'):
            # Use field's method if available
            field_rect = field.get_screen_rect(self.zoom_level)
            base_x, base_y = field_rect.x(), field_rect.y()
        else:
            # Manual calculation with zoom and page offset
            base_x = int(field.x * self.zoom_level)
            base_y = int(field.y * self.zoom_level + page_offset_y)

            # Add canvas scroll offset if available
            if canvas and hasattr(canvas, 'horizontalScrollBar') and hasattr(canvas, 'verticalScrollBar'):
                scroll_x = canvas.horizontalScrollBar().value()
                scroll_y = canvas.verticalScrollBar().value()
                base_x -= scroll_x
                base_y -= scroll_y

        # Apply drag offset
        ghost_pos = QPoint(
            base_x + drag_offset.x(),
            base_y + drag_offset.y()
        )

        self.ghost_positions[field.id] = ghost_pos
        print(f"📍 Fallback ghost for {field.name} on page {field_page}: "
              f"base({base_x}, {base_y}) + offset({drag_offset.x()}, {drag_offset.y()}) "
              f"= ghost({ghost_pos.x()}, {ghost_pos.y()}) [page_offset_y: {page_offset_y}]")

    def get_page_offset_y(self, page_number, canvas):
        """Calculate the Y offset for a given page number"""
        if not canvas:
            return 0

        # Try different methods to get page offset
        methods_to_try = [
            ('get_page_offset', lambda: canvas.get_page_offset(page_number)),
            ('get_page_y_offset', lambda: canvas.get_page_y_offset(page_number)),
            ('calculate_page_offset', lambda: self._calculate_manual_page_offset(page_number, canvas))
        ]

        for method_name, method_func in methods_to_try:
            try:
                if hasattr(canvas, method_name.split('_')[0]) or method_name == 'calculate_page_offset':
                    offset = method_func()
                    if offset is not None:
                        print(f"✅ Using {method_name} for page {page_number} offset: {offset}")
                        return offset
            except Exception as e:
                print(f"⚠️ {method_name} failed: {e}")

        print(f"❌ Could not determine page offset for page {page_number}, using 0")
        return 0

    def _calculate_manual_page_offset(self, page_number, canvas):
        """Manually calculate page offset based on page dimensions"""
        try:
            # Get page dimensions from canvas or use defaults
            page_height = getattr(canvas, 'page_height', 792)  # Default PDF page height in points
            page_spacing = getattr(canvas, 'page_spacing', 20)  # Default spacing between pages

            # Convert to screen coordinates with zoom
            screen_page_height = page_height * self.zoom_level
            screen_page_spacing = page_spacing * self.zoom_level

            # Calculate total offset for this page
            offset = page_number * (screen_page_height + screen_page_spacing)

            print(f"📏 Manual page offset calculation: page {page_number} = "
                  f"{page_number} * ({screen_page_height} + {screen_page_spacing}) = {offset}")

            return offset
        except Exception as e:
            print(f"❌ Manual page offset calculation failed: {e}")
            return 0

    def paintEvent(self, event):
        """Paint drag ghosts and feedback with improved visibility"""
        if not self.is_dragging or not self.drag_fields:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        try:
            self.draw_drag_feedback(painter)
        except Exception as e:
            print(f"⚠️ Error painting drag overlay: {e}")
            import traceback
            traceback.print_exc()
        finally:
            painter.end()

    def draw_drag_feedback(self, painter):
        """Draw visual feedback for dragged fields with enhanced visibility"""
        # Enhanced ghost styling for better visibility
        ghost_color = QColor(100, 150, 255, 120)  # More opaque blue
        ghost_border = QColor(50, 100, 255, 255)  # Solid border

        ghost_brush = QBrush(ghost_color)
        ghost_pen = QPen(ghost_border, 3)  # Thicker border
        painter.setBrush(ghost_brush)
        painter.setPen(ghost_pen)

        ghosts_drawn = 0

        # Draw ghost for each dragged field
        for field in self.drag_fields:
            if field.id in self.ghost_positions:
                ghost_pos = self.ghost_positions[field.id]

                # Verify ghost position is within reasonable bounds
                if ghost_pos.x() < -1000 or ghost_pos.y() < -1000 or ghost_pos.x() > 5000 or ghost_pos.y() > 5000:
                    print(f"⚠️ Ghost position for {field.name} seems unreasonable: {ghost_pos}")
                    continue

                # Get field dimensions (scaled by zoom)
                field_width = int(getattr(field, 'width', 100) * self.zoom_level)
                field_height = int(getattr(field, 'height', 30) * self.zoom_level)

                # Draw ghost rectangle
                ghost_rect = QRect(ghost_pos.x(), ghost_pos.y(), field_width, field_height)
                painter.drawRect(ghost_rect)

                # Draw field label in ghost
                self.draw_ghost_label(painter, field, ghost_rect)

                ghosts_drawn += 1
                print(f"👻 Drew ghost for {field.name} at {ghost_pos} (page {getattr(field, 'page_number', '?')})")
            else:
                print(f"❌ No ghost position found for field {field.name} (id: {getattr(field, 'id', 'no-id')})")

        print(f"✅ Drew {ghosts_drawn}/{len(self.drag_fields)} ghosts")

        # Draw additional visual feedback
        self.draw_drag_guidelines(painter)

    def deprecated_1_update_ghost_positions(self):
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

    def update_ghost_positions(self):
        """Calculate ghost positions with proper zoom support"""
        if not self.is_dragging or not self.drag_fields:
            return

        print(f"🎯 Updating ghost positions for {len(self.drag_fields)} fields")

        # ✅ KEY FIX: Convert screen drag offset to document coordinates
        screen_drag_offset = self.current_drag_pos - self.drag_start_pos
        doc_drag_offset_x = screen_drag_offset.x() / self.zoom_level
        doc_drag_offset_y = screen_drag_offset.y() / self.zoom_level

        print(f"   Screen drag offset: {screen_drag_offset}")
        print(f"   Document drag offset: ({doc_drag_offset_x:.1f}, {doc_drag_offset_y:.1f})")
        print(f"   Zoom level: {self.zoom_level:.2f}x")

        # Get canvas reference for coordinate conversion
        canvas = self.parent() if hasattr(self, 'parent') and self.parent() else None

        # Process each dragged field
        for field in self.drag_fields:
            page_number = getattr(field, 'page_number', 0)

            try:
                # ✅ Calculate new field position in document coordinates
                new_field_doc_x = field.x + doc_drag_offset_x
                new_field_doc_y = field.y + doc_drag_offset_y

                # Try to use canvas method for accurate screen coordinates
                if canvas and hasattr(canvas, 'document_to_screen_coordinates'):
                    screen_coords = canvas.document_to_screen_coordinates(
                        page_number, new_field_doc_x, new_field_doc_y
                    )

                    if screen_coords:
                        ghost_pos = QPoint(int(screen_coords[0]), int(screen_coords[1]))
                        self.ghost_positions[field.id] = ghost_pos
                        print(f"   {field.name}: using canvas conversion -> {ghost_pos}")
                        continue

                # ✅ Fallback: Manual zoom-aware calculation
                self._calculate_zoom_aware_ghost_position(field, doc_drag_offset_x, doc_drag_offset_y, canvas)

            except Exception as e:
                print(f"❌ Error updating ghost for {field.name}: {e}")
                # Last resort fallback
                ghost_pos = QPoint(
                    self.current_drag_pos.x() - 50,
                    self.current_drag_pos.y() - 15
                )
                self.ghost_positions[field.id] = ghost_pos

    # new
    def _calculate_zoom_aware_ghost_position(self, field, doc_offset_x, doc_offset_y, canvas):
        """Fallback method for zoom-aware ghost positioning"""
        field_page = getattr(field, 'page_number', 0)

        try:
            # Calculate new field position in document coordinates
            new_field_doc_x = field.x + doc_offset_x
            new_field_doc_y = field.y + doc_offset_y

            # ✅ Convert to screen coordinates manually with zoom
            ghost_screen_x = int(new_field_doc_x * self.zoom_level)
            ghost_screen_y = int(new_field_doc_y * self.zoom_level)

            # Add page offset for multi-page documents
            if canvas and hasattr(canvas, 'get_page_offset'):
                try:
                    page_offset_y = canvas.get_page_offset(field_page)
                    ghost_screen_y += page_offset_y
                except:
                    pass

            # Account for scroll position
            if canvas and hasattr(canvas, 'horizontalScrollBar') and hasattr(canvas, 'verticalScrollBar'):
                scroll_x = canvas.horizontalScrollBar().value()
                scroll_y = canvas.verticalScrollBar().value()
                ghost_screen_x -= scroll_x
                ghost_screen_y -= scroll_y

            # Account for canvas margins
            if canvas:
                canvas_margin_x = getattr(canvas, 'canvas_margin_x', 0)
                canvas_margin_y = getattr(canvas, 'canvas_margin_y', 0)
                ghost_screen_x += canvas_margin_x
                ghost_screen_y += canvas_margin_y

            ghost_pos = QPoint(ghost_screen_x, ghost_screen_y)
            self.ghost_positions[field.id] = ghost_pos

            print(
                f"   {field.name} (zoom-aware): doc({new_field_doc_x:.1f}, {new_field_doc_y:.1f}) -> screen({ghost_screen_x}, {ghost_screen_y})")

        except Exception as e:
            print(f"❌ Error calculating zoom-aware ghost position for {field.name}: {e}")

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