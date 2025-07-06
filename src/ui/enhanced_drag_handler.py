"""
Enhanced Drag Handler
Manages drag and drop operations for form fields with improved functionality
"""

from typing import Optional, Tuple, List, Any
from enum import Enum
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import QCursor

# Import dependencies - these MUST work for enhanced drag handler to function
from models.field_model import FormField, FieldManager
from ui.drag_overlay import DragOverlay
from utils.geometry_utils import (
    ResizeHandles, ResizeCalculator, BoundaryConstraints, GridUtils
)
from ui.resize_visual_guide import ResizeVisualGuide

class DragMode(Enum):
    """Enumeration of drag operation modes"""
    NONE = "none"
    MOVE = "move"
    RESIZE = "resize"
    MULTI_SELECT = "multi_select"


class DragState:
    """Holds state information during drag operations"""

    def __init__(self):
        self.mode = DragMode.NONE
        self.start_pos: Optional[QPoint] = None
        self.current_pos: Optional[QPoint] = None
        self.start_field_pos: Optional[Tuple[int, int]] = None
        self.start_field_size: Optional[Tuple[int, int]] = None
        self.resize_handle: Optional[str] = None
        self.target_field: Optional[FormField] = None
        self.selected_fields: List[FormField] = []
        self.drag_threshold = 5  # Minimum pixels before starting drag
        self.is_dragging = False

        # Multi-selection drag data
        self.multi_drag_start_positions = {}  # field_id -> (x, y)

    def reset(self):
        """Reset drag state"""
        self.mode = DragMode.NONE
        self.start_pos = None
        self.current_pos = None
        self.start_field_pos = None
        self.start_field_size = None
        self.resize_handle = None
        self.target_field = None
        self.is_dragging = False
        self.multi_drag_start_positions.clear()

    def is_active(self) -> bool:
        """Check if drag operation is active"""
        return self.mode != DragMode.NONE and self.is_dragging

    def should_start_drag(self, current_pos: QPoint) -> bool:
        """Check if we should start dragging based on movement threshold"""
        if not self.start_pos:
            return False

        dx = abs(current_pos.x() - self.start_pos.x())
        dy = abs(current_pos.y() - self.start_pos.y())

        return (dx + dy) >= self.drag_threshold


class EnhancedDragHandler(QObject):
    """
    Enhanced drag handler that works with the transparent overlay
    """

    selectionChanged = pyqtSignal(list)  # When selection changes (which fields are selected)
    propertiesChanged = pyqtSignal(list)  # When field properties change (position, size, etc.)
    cursorChanged = pyqtSignal(Qt.CursorShape)

    # Signals for drag and resize operations
    fieldMoved = pyqtSignal(str, float, float)  # field_id, new_x, new_y
    fieldResized = pyqtSignal(str, float, float, float, float)  # field_id, x, y, width, height
    dragStarted = pyqtSignal(str, str)  # field_id, operation_type
    dragProgress = pyqtSignal(str, int, int, int, int)  # field_id, x, y, w, h
    dragCompleted = pyqtSignal(str)  # field_id

    def __init__(self, canvas, field_manager):
        super().__init__()  # This is the critical line that was missing!
        self.canvas = canvas
        self.field_manager = field_manager
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.zoom_level = 1.0

        self.resize_guide = None

        # Create drag overlay
        self.drag_overlay = DragOverlay(canvas)
        self.drag_overlay.hide()  # Initially hidden

        self.resize_mode = False
        self.resize_handle = None
        self.resize_start_pos = QPoint()
        self.resize_start_size = (0, 0)
        self.resize_field = None
        self.resize_start_field_pos = None  # 🔧 ADD THIS LINE

        self.grid_manager = None
        self.snap_enabled = False

    def set_zoom_level(self, zoom_level: float):
        """Update zoom level for drag calculations"""
        self.zoom_level = zoom_level

    def set_grid_manager(self, grid_manager):
        """Connect to grid manager for snap functionality"""
        self.grid_manager = grid_manager
        if grid_manager:
            # Connect to snap state changes
            grid_manager.snap_changed.connect(self.set_snap_enabled)
            self.snap_enabled = grid_manager.is_snap_enabled()
            print(f"🧲 Drag handler connected to grid manager, snap: {self.snap_enabled}")

    def set_snap_enabled(self, enabled: bool):
        """Enable/disable snap functionality"""
        if self.snap_enabled != enabled:
            self.snap_enabled = enabled
            print(f"🧲 Drag handler snap: {'enabled' if enabled else 'disabled'}")

    def _should_snap(self) -> bool:
        """Check if snap should be applied"""
        snap_enabled = self.snap_enabled
        has_grid_manager = self.grid_manager is not None
        grid_snap_enabled = self.grid_manager.is_snap_enabled() if self.grid_manager else False
        grid_visible = self.grid_manager.get_settings().visible if self.grid_manager else False

        result = (snap_enabled and has_grid_manager and grid_snap_enabled and grid_visible)

        # ⭐ ADD DEBUG OUTPUT ⭐
        print(f"🧲 _should_snap(): snap_enabled={snap_enabled}, "
              f"has_grid_manager={has_grid_manager}, "
              f"grid_snap_enabled={grid_snap_enabled}, "
              f"grid_visible={grid_visible}, "
              f"result={result}")

        return result

    def snap_point_to_grid(self, x: float, y: float, zoom_level: float = 1.0) -> tuple:
        """Snap a point to the nearest grid intersection"""
        if not self._should_snap():
            return (x, y)

        return self.grid_manager.snap_point_to_grid(x, y, zoom_level)

    def handle_mouse_press(self, pos: QPoint, modifiers: Qt.KeyboardModifier, page_num: int = None) -> Optional[Any]:
        """
        Handle mouse press - detect field clicks and prepare for dragging

        Returns:
            Field object if clicked, None otherwise
        """

        # ✅ DETERMINE WHICH PAGE TO SEARCH - USE PROVIDED PAGE_NUM FIRST
        if page_num is not None:
            # Use the page number passed from mousePressEvent (this is most accurate)
            search_page = page_num
            print(f"🔍 Using provided page number: {search_page}")
        else:
            # Fallback to canvas current page with update
            if hasattr(self.canvas, 'update_current_page_from_scroll'):
                self.canvas.update_current_page_from_scroll()

            search_page = getattr(self.canvas, 'current_page', 0)
            print(f"🔍 Using canvas current page: {search_page}")

        print(f"🔍 Enhanced drag handler: Looking for field at {pos} on page {search_page}")

        # ✅ SINGLE FIELD LOOKUP WITH CORRECT PAGE
        clicked_field = self.field_manager.get_field_at_position(
            pos.x(), pos.y(), search_page
        )

        if clicked_field:
            # NEW: Check for resize handles first (only for single field)
            if len(self.get_selected_fields()) == 1 and clicked_field == self.get_selected_fields()[0]:
                from utils.geometry_utils import ResizeHandles
                handle = ResizeHandles.get_handle_at_position(
                    pos.x(), pos.y(),
                    clicked_field.x, clicked_field.y,
                    clicked_field.width, clicked_field.height
                )

                if handle:
                    print(f"🔧 Resize handle detected: {handle}")
                    self.resize_mode = True
                    self.resize_handle = handle
                    self.resize_start_pos = pos
                    self.resize_start_size = (clicked_field.width, clicked_field.height)
                    self.resize_start_field_pos = (clicked_field.x, clicked_field.y)  # 🔧 ADD THIS LINE
                    self.resize_field = clicked_field

                    # NEW: Start visual guide
                    if not self.resize_guide:
                        #self.resize_guide = SimpleResizeGuide(self.canvas)
                        self.resize_guide = ResizeVisualGuide(self.canvas)
                    self.resize_guide.start_resize(clicked_field, handle, self.zoom_level)

                    self.dragStarted.emit(clicked_field.id, "resize")
                    return clicked_field

            # Handle multi-selection with Ctrl
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                # Multi-selection via field manager
                if hasattr(self, 'field_manager') and self.field_manager:
                    self.field_manager.select_field(clicked_field, multi_select=True)
                print(f"🎯 Multi-select: Ctrl+clicked {clicked_field.name}")

                # 🔧 EMIT SIGNAL RIGHT AFTER MULTI-SELECTION
                selected_fields = self.get_selected_fields()
                print(f"📡 Emitted selectionChanged: {len(selected_fields)} fields (multi-select)")
                self.selectionChanged.emit(selected_fields)
            else:
                # Single selection via field manager
                if hasattr(self, 'field_manager') and self.field_manager:
                    self.field_manager.select_field(clicked_field, multi_select=False)
                    # Add this debug:
                    current_selection = self.field_manager.get_selected_fields()
                    print(f"🔍 DEBUG: FieldManager now has {len(current_selection)} fields selected:")
                    for f in current_selection:
                        print(f"   - {f.id}")
                print(f"🎯 Single-select: Clicked {clicked_field.name}")
                # 🔧 EMIT SIGNAL RIGHT AFTER SINGLE-SELECTION
                selected_fields = self.get_selected_fields()
                print(f"📡 Emitted selectionChanged: {len(selected_fields)} fields (single-select)")
                self.selectionChanged.emit(selected_fields)

            # Prepare for potential drag
            self.drag_start_pos = pos
            if self._should_snap():
                zoom = getattr(self, 'zoom_level', 1.0)
                snapped_x, snapped_y = self.snap_point_to_grid(pos.x(), pos.y(), zoom)
                pos = QPoint(int(snapped_x), int(snapped_y))
                self.drag_start_pos = pos
                print(f"🧲 Snapped click position: ({snapped_x:.1f}, {snapped_y:.1f})")

            self.canvas.draw_overlay()
            print(f"🎯 Enhanced drag handler: {len(self.get_selected_fields())} fields selected")

        else:
            print(f"❌ No field found at {pos} on page {search_page}")
            # ✅ DEBUG: Show what fields exist on this page
            fields_on_page = [f for f in self.field_manager.fields if f.page_number == search_page]
            print(f"   Available fields on page {search_page}: {len(fields_on_page)}")
            for field in fields_on_page:
                print(f"   - {field.name} at ({field.x}, {field.y})")
            self.field_manager.clear_selection()
            self.selectionChanged.emit(self.get_selected_fields())
            self.canvas.draw_overlay()

        return clicked_field

    def handle_mouse_move(self, pos: QPoint) -> bool:
        """
        Handle mouse move - start/update dragging or resizing

        Returns:
            bool: True if currently dragging or resizing
        """
        # Handle resize mode
        if self.resize_mode and self.resize_field:
            self._handle_resize_move(pos)
            return True

        if not self.get_selected_fields():
            return False

        # Check if we should start dragging
        if not self.is_dragging:
            drag_distance = (pos - self.drag_start_pos).manhattanLength()
            if drag_distance > 1:  # Start drag after 5 pixel threshold
                self.start_drag()

        # Update drag if in progress
        if self.is_dragging:
            # Apply snap to drag position
            if self._should_snap():
                zoom = getattr(self, 'zoom_level', 1.0)
                # 🎯 FIX: Use grid_manager's snap method with distance threshold
                snapped_x, snapped_y = self.grid_manager.snap_point_to_grid(
                    pos.x(), pos.y(), zoom, max_snap_distance=25.0
                )
                pos = QPoint(int(snapped_x), int(snapped_y))

            self.drag_overlay.update_drag(pos)

        return self.is_dragging

    def working_handle_mouse_move(self, pos: QPoint) -> bool:
        """
        Handle mouse move - start/update dragging or resizing

        Returns:
            bool: True if currently dragging or resizing
        """
        # Handle resize mode
        if self.resize_mode and self.resize_field:
            self._handle_resize_move(pos)
            return True

        if not self.get_selected_fields():
            return False

        # Check if we should start dragging
        if not self.is_dragging:
            drag_distance = (pos - self.drag_start_pos).manhattanLength()
            if drag_distance > 5:  # Start drag after 5 pixel threshold
                self.start_drag()

        # Update drag if in progress
        if self.is_dragging:
            # Apply snap to drag position
            if self._should_snap():
                zoom = getattr(self, 'zoom_level', 1.0)
                snapped_x, snapped_y = self.snap_point_to_grid(pos.x(), pos.y(), zoom)
                pos = QPoint(int(snapped_x), int(snapped_y))

            self.drag_overlay.update_drag(pos)

        return self.is_dragging

    def _handle_resize_move(self, pos):
        """Handle mouse movement during resize operation"""
        if not self.resize_field or not self.resize_handle or not self.resize_start_field_pos:
            return

        field = self.resize_field

        # ✅ Use the ORIGINAL starting position, not current field position
        start_x, start_y = self.resize_start_field_pos
        start_width, start_height = self.resize_start_size

        # Calculate deltas from mouse movement
        dx = (pos.x() - self.resize_start_pos.x()) #/ self.zoom_level
        dy = (pos.y() - self.resize_start_pos.y()) #/ self.zoom_level

        # Calculate new dimensions using ORIGINAL starting values
        from utils.geometry_utils import ResizeCalculator
        new_x, new_y, new_width, new_height = ResizeCalculator.calculate_resize(
            start_x, start_y, start_width, start_height,
            dx, dy, self.resize_handle, 20, 15
        )

        # 🧲 ADD SNAP TO RESIZE INTEGRATION HERE 🧲
        # Apply snap to resize if enabled
        if self._should_snap():
            # Snap both position and size to grid
            spacing = self.grid_manager.settings.spacing if hasattr(self.grid_manager, 'settings') else 20
            zoom_level = getattr(self, 'zoom_level', 1.0)
            if self.grid_manager.settings.sync_with_zoom:
                effective_spacing = spacing * zoom_level
            else:
                effective_spacing = spacing

            # Snap position
            new_x, new_y = self.snap_point_to_grid(new_x, new_y, zoom_level)

            # Snap size to grid intervals
            #new_width = max(scaled_spacing, round(new_width / scaled_spacing) * scaled_spacing)
            #new_height = max(scaled_spacing, round(new_height / scaled_spacing) * scaled_spacing)

            #print(f"🧲 Snapped resize: ({new_x:.1f}, {new_y:.1f}) {new_width:.1f}x{new_height:.1f}")
        # 🧲 END SNAP INTEGRATION 🧲

        # Update field with new values
        field.x = new_x
        field.y = new_y
        field.resize_to(new_width, new_height)

        # ADD this line:
        self.dragProgress.emit(field.id, int(field.x), int(field.y), int(field.width), int(field.height))

        # Update visual guide
        if hasattr(self, 'resize_guide') and self.resize_guide:
            self.resize_guide.update_resize(field)

    def snap_multiple_fields(self, fields: list, offset_x: float, offset_y: float, zoom_level: float = 1.0):
        """Snap multiple selected fields maintaining their relative positions"""
        if not self._should_snap() or not fields:
            return

        # Find the primary field (first selected)
        primary_field = fields[0]

        # Calculate new position for primary field
        new_primary_x = primary_field.x + offset_x
        new_primary_y = primary_field.y + offset_y

        # Snap the primary field's new position
        snapped_x, snapped_y = self.snap_point_to_grid(new_primary_x, new_primary_y, zoom_level)

        # Calculate the actual offset after snapping
        actual_offset_x = snapped_x - primary_field.x
        actual_offset_y = snapped_y - primary_field.y

        # Apply the snapped offset to all fields
        for field in fields:
            field.x += actual_offset_x
            field.y += actual_offset_y

        print(f"🧲 Snapped {len(fields)} fields with offset ({actual_offset_x:.1f}, {actual_offset_y:.1f})")

    def start_drag(self):
        """Start drag operation using overlay"""
        if not self.get_selected_fields():
            return

        print(f"🚀 Starting drag operation with {len(self.get_selected_fields())} fields")

        self.is_dragging = True
        self.drag_overlay.start_drag(
            self.get_selected_fields(),
            self.drag_start_pos,
            self.zoom_level
        )

        # Emit drag started signal
        field_info = "multiple" if len(self.get_selected_fields()) > 1 else self.get_selected_fields()[0].id
        self.dragStarted.emit(field_info, "move")
        self.propertiesChanged.emit(self.get_selected_fields())

    def handle_mouse_release(self, pos: QPoint) -> bool:
        """
        Handle mouse release - end dragging/resizing and apply changes

        Returns:
            bool: True if drag or resize was ended
        """
        # Handle resize mode
        if self.resize_mode and self.resize_field:
            field = self.resize_field

            self.fieldResized.emit(field.id, field.x, field.y, field.width, field.height)
            self.dragCompleted.emit(field.id)
            # Emit property changed
            self.propertiesChanged.emit(self.get_selected_fields())

            # NEW: End visual guide
            if hasattr(self, 'resize_guide') and self.resize_guide:
                self.resize_guide.end_resize()

            # Reset resize mode
            self.resize_mode = False
            self.resize_handle = None
            self.resize_field = None
            self.resize_start_field_pos = None  # 🔧 ADD THIS LINE
            print("✅ Resize operation completed")
            return True

        if not self.is_dragging:
            return False

        # End drag operation
        was_dragging = self.drag_overlay.end_drag()

        if was_dragging:

            if self._should_snap():
                zoom = getattr(self, 'zoom_level', 1.0)
                snapped_x, snapped_y = self.snap_point_to_grid(pos.x(), pos.y(), zoom)
                pos = QPoint(int(snapped_x), int(snapped_y))
                print(f"🧲 Final snap position: ({snapped_x:.1f}, {snapped_y:.1f})")

            # Apply drag changes to actual fields
            self.apply_drag_changes(pos)

            for field in self.get_selected_fields():
                self.fieldMoved.emit(field.id, field.x, field.y)

            # Emit completion signal
            self.dragCompleted.emit("multiple" if len(self.get_selected_fields()) > 1 else self.get_selected_fields()[0].id)

            # Emit property changed
            self.propertiesChanged.emit(self.get_selected_fields())

            # ✅ CLEAR SELECTION AFTER DRAG ENDS
            print("🧹 Clearing selection after drag completion")
            field_count = len(self.get_selected_fields())
            if hasattr(self, 'field_manager') and self.field_manager:
                self.field_manager.clear_selection()

            # Also clear canvas selection handler
            if hasattr(self.canvas, 'selection_handler') and self.canvas.selection_handler:
                try:
                    self.canvas.selection_handler.clear_selection()
                    print("🧹 Cleared canvas selection handler")
                except Exception as e:
                    print(f"⚠️ Error clearing canvas selection: {e}")


        self.is_dragging = False
        return was_dragging

    def select_field(self, field):
        """Select a single field (delegates to field_manager)"""
        try:
            if hasattr(self, 'field_manager') and self.field_manager:
                self.field_manager.select_field(field, multi_select=False)
                print(f"✅ Selected field via field_manager: {field.id if field else 'None'}")
            else:
                print("⚠️ No field_manager available for selection")
        except Exception as e:
            print(f"⚠️ Error in select_field: {e}")

    def get_selected_field(self):
        """Get the first selected field (delegates to field_manager)"""
        try:
            if hasattr(self, 'field_manager') and self.field_manager:
                return self.field_manager.get_selected_field()
            return None
        except Exception as e:
            print(f"⚠️ Error getting selected field: {e}")
            return None

    def get_selected_fields(self):
        """Get all selected fields (delegates to field_manager)"""
        try:
            if hasattr(self, 'field_manager') and self.field_manager:
                return self.field_manager.get_selected_fields()
            return []
        except Exception as e:
            print(f"⚠️ Error getting selected fields: {e}")
            return []

    def copy_apply_drag_changes(self, final_pos: QPoint):
        """
        Apply drag offset to actual field positions with snap support
        FIXED: Single snap to prevent double-snapping issues
        """
        selected_fields = self.get_selected_fields()
        if not selected_fields:
            return

        print(f"🎯 Applying drag changes:")
        print(f"   Drag start pos: {self.drag_start_pos}")
        print(f"   Final pos: {final_pos}")
        print(f"   Zoom level: {self.zoom_level}")

        # Calculate screen offset first (no snapping yet)
        screen_offset = final_pos - self.drag_start_pos
        print(f"   Screen offset: {screen_offset}")

        # Convert to document offset (keeping zoom handling as current)
        doc_offset_x = screen_offset.x()  # / self.zoom_level
        doc_offset_y = screen_offset.y()  # / self.zoom_level
        print(f"   Document offset: ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

        # Apply document offset to each field with single snap
        for field in selected_fields:
            original_x = field.x
            original_y = field.y

            # Calculate new position before snapping
            target_x = original_x + doc_offset_x
            target_y = original_y + doc_offset_y

            # Apply snap ONCE to the final field position
            if self._should_snap():
                zoom = getattr(self, 'zoom_level', 1.0)
                snapped_x, snapped_y = self.snap_point_to_grid(target_x, target_y, zoom)

                # Calculate movement distances
                total_movement_x = snapped_x - original_x
                total_movement_y = snapped_y - original_y
                total_distance = (total_movement_x ** 2 + total_movement_y ** 2) ** 0.5

                # Calculate snap adjustment
                snap_adjustment_x = snapped_x - target_x
                snap_adjustment_y = snapped_y - target_y
                snap_adjustment_distance = (snap_adjustment_x ** 2 + snap_adjustment_y ** 2) ** 0.5

                print(f"🧲 FIELD '{field.id}' MOVEMENT SUMMARY:")
                print(f"   📍 Original position: ({original_x:.1f}, {original_y:.1f})")
                print(f"   📍 Target position:   ({target_x:.1f}, {target_y:.1f})")
                print(f"   📍 Snapped position:  ({snapped_x:.1f}, {snapped_y:.1f})")
                print(
                    f"   📏 Total movement:    ({total_movement_x:+.1f}, {total_movement_y:+.1f}) = {total_distance:.1f}px")
                print(
                    f"   🧲 Snap adjustment:   ({snap_adjustment_x:+.1f}, {snap_adjustment_y:+.1f}) = {snap_adjustment_distance:.1f}px")

                # Update field position to snapped location
                field.x = snapped_x
                field.y = snapped_y

            else:
                # No snapping - use target position directly
                total_movement_x = target_x - original_x
                total_movement_y = target_y - original_y
                total_distance = (total_movement_x ** 2 + total_movement_y ** 2) ** 0.5

                print(f"📍 FIELD '{field.id}' MOVEMENT (NO SNAP):")
                print(f"   📍 Original position: ({original_x:.1f}, {original_y:.1f})")
                print(f"   📍 Final position:    ({target_x:.1f}, {target_y:.1f})")
                print(
                    f"   📏 Total movement:    ({total_movement_x:+.1f}, {total_movement_y:+.1f}) = {total_distance:.1f}px")

                # Update field position to target location
                field.x = target_x
                field.y = target_y

            # Emit field moved signal
            self.fieldMoved.emit(field.id, field.x, field.y)

        print(f"✅ Updated {len(selected_fields)} field positions")

    def apply_1_drag_changes(self, final_pos: QPoint):
        """
        Apply drag offset to actual field positions with snap support
        FIXED: Prevent double-snapping by snapping only the offset, not individual fields
        """
        selected_fields = self.get_selected_fields()
        if not selected_fields:
            return

        print(f"🎯 Applying drag changes:")
        print(f"   Drag start pos: {self.drag_start_pos}")
        print(f"   Final pos: {final_pos}")
        print(f"   Zoom level: {self.zoom_level}")

        # ⭐ APPLY SNAP TO FINAL POSITION ONLY ONCE ⭐
        snapped_final_pos = final_pos
        if self._should_snap():
            zoom = getattr(self, 'zoom_level', 1.0)
            snapped_x, snapped_y = self.snap_point_to_grid(final_pos.x(), final_pos.y(), zoom)
            snapped_final_pos = QPoint(int(snapped_x), int(snapped_y))
            print(f"🧲 SNAP: Final pos {final_pos} → snapped to {snapped_final_pos}")

        # Calculate screen offset using snapped final position
        screen_offset = snapped_final_pos - self.drag_start_pos
        print(f"   Screen offset: {screen_offset}")

        # Convert to document offset (keeping zoom handling as-is)
        doc_offset_x = screen_offset.x()  # / self.zoom_level
        doc_offset_y = screen_offset.y()  # / self.zoom_level
        print(f"   Document offset: ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

        # Apply document offset to each field - NO ADDITIONAL SNAPPING
        for field in selected_fields:
            original_x = field.x
            original_y = field.y

            # Simple offset application - snapping already handled above
            new_x = original_x + doc_offset_x
            new_y = original_y + doc_offset_y

            print(f"🧲 FIELD '{field.id}' MOVEMENT SUMMARY:")
            print(f"   📍 Original position: ({original_x:.1f}, {original_y:.1f})")
            print(f"   📍 Target position:   ({new_x:.1f}, {new_y:.1f})")
            print(
                f"   📏 Total movement:    ({doc_offset_x:.1f}, {doc_offset_y:.1f}) = {(doc_offset_x ** 2 + doc_offset_y ** 2) ** 0.5:.1f}px")

            if self._should_snap():
                print(f"   🧲 Snap adjustment:   (+0.0, +0.0) = 0.0px")

            # Update field position
            field.x = new_x
            field.y = new_y

            # Emit field moved signal
            self.fieldMoved.emit(field.id, field.x, field.y)

        print(f"✅ Updated {len(selected_fields)} field positions")

    def apply_0_drag_changes(self, final_pos: QPoint):
        """
        Apply drag offset to actual field positions with snap support
        FIXED: Proper coordinate system handling to prevent oversized jumps
        """
        selected_fields = self.get_selected_fields()
        if not selected_fields:
            return

        print(f"🎯 Applying drag changes:")
        print(f"   Drag start pos: {self.drag_start_pos} (screen coordinates)")
        print(f"   Final pos: {final_pos} (screen coordinates)")
        print(f"   Zoom level: {self.zoom_level}")

        # 🎯 KEY FIX: Convert screen coordinates to document coordinates FIRST
        # Both drag_start_pos and final_pos are in screen coordinates
        # We need to work in document coordinate space for field positioning

        drag_start_doc_x = self.drag_start_pos.x() / self.zoom_level
        drag_start_doc_y = self.drag_start_pos.y() / self.zoom_level
        final_doc_x = final_pos.x() / self.zoom_level
        final_doc_y = final_pos.y() / self.zoom_level

        print(f"   Drag start (doc): ({drag_start_doc_x:.1f}, {drag_start_doc_y:.1f})")
        print(f"   Final pos (doc): ({final_doc_x:.1f}, {final_doc_y:.1f})")

        # ⭐ APPLY SNAP IN DOCUMENT COORDINATE SPACE ⭐
        snapped_final_doc_x = final_doc_x
        snapped_final_doc_y = final_doc_y

        if self._should_snap():
            # Important: Pass zoom_level=1.0 because we're already in document coordinates
            # The grid manager will handle zoom scaling internally based on sync_with_zoom setting
            snapped_final_doc_x, snapped_final_doc_y = self.grid_manager.snap_point_to_grid(
                final_doc_x, final_doc_y, zoom_level=1.0, max_snap_distance=25.0
            )
            print(
                f"🧲 SNAP (doc coords): ({final_doc_x:.1f}, {final_doc_y:.1f}) → ({snapped_final_doc_x:.1f}, {snapped_final_doc_y:.1f})")
        else:
            print(f"🧲 SNAP: Not applied - _should_snap() = {self._should_snap()}")

        # Calculate document offset
        doc_offset_x = snapped_final_doc_x - drag_start_doc_x
        doc_offset_y = snapped_final_doc_y - drag_start_doc_y
        print(f"   Document offset: ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

        # Apply document offset to each field (already in document coordinates)
        for field in selected_fields:
            original_x = field.x
            original_y = field.y
            new_x = original_x + doc_offset_x
            new_y = original_y + doc_offset_y

            # Calculate movement distances for logging
            total_movement_x = new_x - original_x
            total_movement_y = new_y - original_y
            total_distance = (total_movement_x ** 2 + total_movement_y ** 2) ** 0.5

            print(f"🧲 FIELD '{field.id}' MOVEMENT (CORRECTED):")
            print(f"   📍 Original position: ({original_x:.1f}, {original_y:.1f})")
            print(f"   📍 Final position:    ({new_x:.1f}, {new_y:.1f})")
            print(
                f"   📏 Total movement:    ({total_movement_x:+.1f}, {total_movement_y:+.1f}) = {total_distance:.1f}px")

            # Update field position
            field.x = new_x
            field.y = new_y

            # Emit field moved signal
            self.fieldMoved.emit(field.id, field.x, field.y)

        print(f"✅ Updated {len(selected_fields)} field positions")

    def apply_drag_changes(self, final_pos: QPoint):
        """
        Apply drag offset to actual field positions with snap support
        FIXED: Added snap to grid functionality, kept zoom handling as-is
        """
        selected_fields = self.get_selected_fields()
        if not selected_fields:
            return

        print(f"🎯 Applying drag changes:")
        print(f"   Drag start pos: {self.drag_start_pos}")
        print(f"   Final pos: {final_pos}")
        print(f"   Zoom level: {self.zoom_level}")

        # ⭐ APPLY SNAP TO FINAL POSITION FIRST ⭐
        snapped_final_pos = final_pos
        if self._should_snap():
            zoom = getattr(self, 'zoom_level', 1.0)
            snapped_x, snapped_y = self.snap_point_to_grid(final_pos.x(), final_pos.y(), zoom)
            snapped_final_pos = QPoint(int(snapped_x), int(snapped_y))
            print(f"🧲 SNAP: Final pos {final_pos} → snapped to {snapped_final_pos}")
        else:
            print(f"🧲 SNAP: Not applied - _should_snap() = {self._should_snap()}")

        # Calculate screen offset using snapped final position
        screen_offset = snapped_final_pos - self.drag_start_pos
        print(f"   Screen offset: {screen_offset}")

        # ⭐ KEEP ZOOM HANDLING AS-IS (commented out division) ⭐
        doc_offset_x = screen_offset.x()  # / self.zoom_level
        doc_offset_y = screen_offset.y()  # / self.zoom_level
        print(f"   Document offset: ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

        # Apply document offset to each field
        for field in selected_fields:
            original_x = field.x
            original_y = field.y

            # ⭐ ENHANCED SNAP LOGGING WITH MOVEMENT DETAILS ⭐
            if self._should_snap():
                # Calculate new position
                new_x = original_x + doc_offset_x
                new_y = original_y + doc_offset_y

                # Snap the final field position
                zoom = getattr(self, 'zoom_level', 1.0)

                # Add this BEFORE the snap calculation in your method:
                print(f"🔍 SNAP DEBUG FOR {field.id}:")
                print(f"   Original field position: ({original_x:.1f}, {original_y:.1f})")
                print(f"   Field size: {field.width}x{field.height}")
                print(f"   Current field bounds:")
                print(f"     Left: {original_x:.1f}, Right: {original_x + field.width:.1f}")
                print(f"     Top: {original_y:.1f}, Bottom: {original_y + field.height:.1f}")
                print(f"   Target position before snap: ({new_x:.1f}, {new_y:.1f})")
                print(f"   Target bounds before snap:")
                print(f"     Left: {new_x:.1f}, Right: {new_x + field.width:.1f}")
                print(f"     Top: {new_y:.1f}, Bottom: {new_y + field.height:.1f}")

                # Your existing snap call:
                snapped_new_x, snapped_new_y = self.snap_point_to_grid(new_x, new_y, zoom)

                # Add this AFTER the snap calculation:
                print(f"   Snapped position: ({snapped_new_x:.1f}, {snapped_new_y:.1f})")
                print(f"   Snapped bounds:")
                print(f"     Left: {snapped_new_x:.1f}, Right: {snapped_new_x + field.width:.1f}")
                print(f"     Top: {snapped_new_y:.1f}, Bottom: {snapped_new_y + field.height:.1f}")
                print(f"   Available grid lines:")
                print(f"     Vertical: {self.grid_manager.vertical_lines[:10]}")
                print(f"     Horizontal: {self.grid_manager.horizontal_lines[:10]}")

                # Calculate movement distances
                total_movement_x = snapped_new_x - original_x
                total_movement_y = snapped_new_y - original_y
                total_distance = (total_movement_x ** 2 + total_movement_y ** 2) ** 0.5

                # Calculate snap adjustment
                snap_adjustment_x = snapped_new_x - new_x
                snap_adjustment_y = snapped_new_y - new_y
                snap_adjustment_distance = (snap_adjustment_x ** 2 + snap_adjustment_y ** 2) ** 0.5

                print(f"🧲 FIELD '{field.id}' MOVEMENT SUMMARY:")
                print(f"   📍 Original position: ({original_x:.1f}, {original_y:.1f})")
                print(f"   📍 Target position:   ({new_x:.1f}, {new_y:.1f})")
                print(f"   📍 Snapped position:  ({snapped_new_x:.1f}, {snapped_new_y:.1f})")
                print(
                    f"   📏 Total movement:    ({total_movement_x:+.1f}, {total_movement_y:+.1f}) = {total_distance:.1f}px")
                print(
                    f"   🧲 Snap adjustment:   ({snap_adjustment_x:+.1f}, {snap_adjustment_y:+.1f}) = {snap_adjustment_distance:.1f}px")

                # Update field position
                field.x = snapped_new_x
                field.y = snapped_new_y

            else:
                # Normal positioning without snap
                new_x = original_x + doc_offset_x
                new_y = original_y + doc_offset_y

                # Calculate movement distances
                total_movement_x = new_x - original_x
                total_movement_y = new_y - original_y
                total_distance = (total_movement_x ** 2 + total_movement_y ** 2) ** 0.5

                print(f"📍 FIELD '{field.id}' MOVEMENT (NO SNAP):")
                print(f"   📍 Original position: ({original_x:.1f}, {original_y:.1f})")
                print(f"   📍 Final position:    ({new_x:.1f}, {new_y:.1f})")
                print(
                    f"   📏 Total movement:    ({total_movement_x:+.1f}, {total_movement_y:+.1f}) = {total_distance:.1f}px")

                # Update field position
                field.x = new_x
                field.y = new_y

            # Emit field moved signal
            self.fieldMoved.emit(field.id, field.x, field.y)
            print(f"✅ Emitted field moved signal")

        print(f"✅ Updated {len(selected_fields)} field positions")

    def working_1_apply_drag_changes(self, final_pos: QPoint):
        """
        Apply drag offset to actual field positions with snap support
        FIXED: Added snap to grid functionality, kept zoom handling as-is
        """
        selected_fields = self.get_selected_fields()
        if not selected_fields:
            return

        print(f"🎯 Applying drag changes:")
        print(f"   Drag start pos: {self.drag_start_pos}")
        print(f"   Final pos: {final_pos}")
        print(f"   Zoom level: {self.zoom_level}")

        # ⭐ APPLY SNAP TO FINAL POSITION FIRST ⭐
        snapped_final_pos = final_pos
        if self._should_snap():
            zoom = getattr(self, 'zoom_level', 1.0)
            snapped_x, snapped_y = self.snap_point_to_grid(final_pos.x(), final_pos.y(), zoom)
            snapped_final_pos = QPoint(int(snapped_x), int(snapped_y))
            print(f"🧲 SNAP: Final pos {final_pos} → snapped to {snapped_final_pos}")
        else:
            print(f"🧲 SNAP: Not applied - _should_snap() = {self._should_snap()}")

        # Calculate screen offset using snapped final position
        screen_offset = snapped_final_pos - self.drag_start_pos
        print(f"   Screen offset: {screen_offset}")

        # ⭐ KEEP ZOOM HANDLING AS-IS (commented out division) ⭐
        doc_offset_x = screen_offset.x()  # / self.zoom_level
        doc_offset_y = screen_offset.y()  # / self.zoom_level
        print(f"   Document offset: ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

        # Apply document offset to each field
        for field in selected_fields:
            original_x = field.x
            original_y = field.y

            # ⭐ APPLY SNAP AT FIELD LEVEL IF ENABLED ⭐
            if self._should_snap():
                # Calculate new position
                new_x = original_x + doc_offset_x
                new_y = original_y + doc_offset_y

                # Snap the final field position
                zoom = getattr(self, 'zoom_level', 1.0)
                new_x, new_y = self.snap_point_to_grid(new_x, new_y, zoom)
                print(f"🧲 Snapped field {field.id}: ({original_x:.1f}, {original_y:.1f}) → ({new_x:.1f}, {new_y:.1f})")
            else:
                # Normal positioning without snap
                new_x = original_x + doc_offset_x
                new_y = original_y + doc_offset_y
                print(f"   Field {field.id}: ({original_x:.1f}, {original_y:.1f}) → ({new_x:.1f}, {new_y:.1f})")

            # Update field position
            field.x = new_x
            field.y = new_y

            # Emit field moved signal
            self.fieldMoved.emit(field.id, field.x, field.y)

        print(f"✅ Updated {len(selected_fields)} field positions")

    def working_apply_drag_changes(self, final_pos: QPoint):
        """
        Apply drag offset to actual field positions
        FIXED: Properly convert screen offset to document offset
        """
        selected_fields = self.get_selected_fields()
        if not selected_fields:
            return

        print(f"🎯 Applying drag changes:")
        print(f"   Drag start pos: {self.drag_start_pos}")
        print(f"   Final pos: {final_pos}")
        print(f"   Zoom level: {self.zoom_level}")

        # FIXED: Calculate screen offset first
        screen_offset = final_pos - self.drag_start_pos
        print(f"   Screen offset: {screen_offset}")

        # FIXED: Convert screen offset to document offset
        doc_offset_x = screen_offset.x() #/ self.zoom_level
        doc_offset_y = screen_offset.y() #/ self.zoom_level
        print(f"   Document offset: ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

        # Apply document offset to each field
        for field in selected_fields:
            original_x = field.x
            original_y = field.y

            # FIXED: Apply document-space offset
            new_x = original_x + doc_offset_x
            new_y = original_y + doc_offset_y

            print(f"   Field {field.id}: ({original_x:.1f}, {original_y:.1f}) → ({new_x:.1f}, {new_y:.1f})")

            # Update field position
            field.x = new_x
            field.y = new_y

            # Emit field moved signal
            self.fieldMoved.emit(field.id, field.x, field.y)

        print(f"✅ Updated {len(selected_fields)} field positions")

    def deprecated_apply_drag_changes(self, final_pos: QPoint):
        """Apply drag offset to actual field positions"""
        selected_fields = self.get_selected_fields()  # ✅ FIXED
        if not selected_fields:
            return

        # Calculate final drag offset
        drag_offset = final_pos - self.drag_start_pos

        # Apply offset to each field
        for field in self.get_selected_fields():
            # Convert screen offset to document coordinates
            doc_offset_x = drag_offset.x() / self.zoom_level
            doc_offset_y = drag_offset.y() / self.zoom_level

            # Update field position
            field.x += doc_offset_x
            field.y += doc_offset_y

            print(f"✅ Moved field {field.name} by ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

    def clear_selection(self):
        """Clear selection via field manager"""
        print("🔄 EnhancedDragHandler: Clearing selection...")
        try:
            # Use field manager as primary source
            if hasattr(self, 'field_manager') and self.field_manager:
                self.field_manager.clear_selection()
                print("✅ Cleared via FieldManager")
            else:
                print("⚠️ No field manager available")

            # Cancel any ongoing drag operation
            if hasattr(self, 'is_dragging') and self.is_dragging:
                if hasattr(self, 'drag_overlay') and self.drag_overlay:
                    self.drag_overlay.cancel_drag()
                self.is_dragging = False
                print("✅ Cancelled drag operation")

        except Exception as e:
            print(f"❌ Error in EnhancedDragHandler.clear_selection: {e}")

# For backward compatibility, keep the original DragHandler available
class DragHandler(EnhancedDragHandler):
    """Backward compatible drag handler"""
    pass

# Keep existing WorkingSelectionHandler for compatibility
class WorkingSelectionHandler(QObject):
    """A completely working SelectionHandler class"""
    fieldSelected = pyqtSignal(object)  # Emits selected field or None
    def __init__(self, field_manager=None):
        super().__init__()
        self.field_manager = field_manager
        #self.selected_field = None
        print("✅ WorkingSelectionHandler initialized successfully")

    def select_field(self, field):
        """Select a field via field manager"""
        try:
            if hasattr(self, 'field_manager') and self.field_manager:
                self.field_manager.select_field(field, multi_select=False)
                print(f"✅ WorkingSelectionHandler: Selected via FieldManager: {field.id if field else 'None'}")
            else:
                print("⚠️ WorkingSelectionHandler: No FieldManager available")

            self._notify_callbacks(field)
        except Exception as e:
            print(f"❌ Error in WorkingSelectionHandler.select_field: {e}")

    def _notify_callbacks(self, field):
        """Notify callbacks of selection change - replaces signal emission"""
        # If there are any callback functions registered, call them
        if hasattr(self, 'callbacks'):
            for callback in getattr(self, 'callbacks', []):
                try:
                    callback(field)
                except Exception as e:
                    print(f"⚠️ Callback error: {e}")

        # For backward compatibility with existing code that expects signals
        # we can manually trigger any connected methods
        if hasattr(self, '_selection_callbacks'):
            for callback in self._selection_callbacks:
                try:
                    callback(field)
                except Exception as e:
                    print(f"⚠️ Selection callback error: {e}")

    def add_selection_callback(self, callback_func):
        """Add a callback function for selection changes"""
        if not hasattr(self, '_selection_callbacks'):
            self._selection_callbacks = []
        if callback_func not in self._selection_callbacks:
            self._selection_callbacks.append(callback_func)
            print(f"✅ Added selection callback")

    def clear_selection(self):
        """Clear selection via field manager"""
        print("🔄 WorkingSelectionHandler: Clearing selection...")
        try:
            if hasattr(self, 'field_manager') and self.field_manager:
                self.field_manager.clear_selection()
                print("✅ WorkingSelectionHandler: Cleared via FieldManager")
            else:
                print("⚠️ WorkingSelectionHandler: No FieldManager available")
        except Exception as e:
            print(f"❌ Error in WorkingSelectionHandler.clear_selection: {e}")

    def get_selected_field(self):
        """Get selected field via field manager"""
        try:
            if hasattr(self, 'field_manager') and self.field_manager:
                return self.field_manager.get_selected_field()
            else:
                return None
        except Exception as e:
            print(f"❌ Error getting selected field: {e}")
            return None

    @property
    def selectionChanged(self):
        """Fake signal for backward compatibility"""

        class FakeSignal:
            def emit(self, *args):
                print("🔄 Fake signal emit (safely ignored)")

            def connect(self, callback):
                print("🔄 Fake signal connect (safely ignored)")

        return FakeSignal()


# For backward compatibility, create an alias
SelectionHandler = WorkingSelectionHandler

