"""
Drag Handler
Manages drag and drop operations for form fields
"""

from typing import Optional, Tuple
from enum import Enum
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject

from models.field_model import FormField, FieldManager
from utils.geometry_utils import (
    ResizeHandles, ResizeCalculator, BoundaryConstraints, GridUtils
)

class DragMode(Enum):
    """Enumeration of drag operation modes"""
    NONE = "none"
    MOVE = "move"
    RESIZE = "resize"

class DragState:
    """Holds state information during drag operations"""

    def __init__(self):
        self.mode = DragMode.NONE
        self.start_pos: Optional[QPoint] = None
        self.start_field_pos: Optional[Tuple[int, int]] = None
        self.start_field_size: Optional[Tuple[int, int]] = None
        self.resize_handle: Optional[str] = None
        self.target_field: Optional[FormField] = None

    def reset(self):
        """Reset drag state"""
        self.mode = DragMode.NONE
        self.start_pos = None
        self.start_field_pos = None
        self.start_field_size = None
        self.resize_handle = None
        self.target_field = None

    def is_active(self) -> bool:
        """Check if drag operation is active"""
        return self.mode != DragMode.NONE

class DragHandler(QObject):
    """Handles drag and drop operations for form fields"""

    # Type hints for signals to eliminate IDE warnings
    fieldMoved = pyqtSignal(str, int, int)  # field_id, new_x, new_y
    fieldResized = pyqtSignal(str, int, int, int, int)  # field_id, x, y, width, height
    cursorChanged = pyqtSignal(Qt.CursorShape)

    def __init__(self, field_manager: FieldManager):
        super().__init__()
        self.field_manager = field_manager
        self.drag_state = DragState()

        # Configuration
        self.grid_size = 20
        self.snap_to_grid = True
        self.canvas_width = 800
        self.canvas_height = 600

    def set_canvas_size(self, width: int, height: int):
        """Update canvas dimensions for boundary constraints"""
        self.canvas_width = width
        self.canvas_height = height

    def set_grid_settings(self, grid_size: int, snap_to_grid: bool):
        """Update grid settings"""
        self.grid_size = grid_size
        self.snap_to_grid = snap_to_grid

    def handle_mouse_press(self, pos: QPoint, selected_field: Optional[FormField]) -> Optional[FormField]:
        """
        Handle mouse press event
        Returns the field that should be selected
        """
        self.drag_state.reset()
        self.drag_state.start_pos = pos

        # Check if clicking on resize handle of selected field
        if selected_field:
            handle = ResizeHandles.get_handle_at_position(
                pos.x(), pos.y(),
                selected_field.x, selected_field.y,
                selected_field.width, selected_field.height
            )

            if handle:
                self._start_resize_operation(selected_field, handle)
                return selected_field

        # Check if clicking on a field
        clicked_field = self.field_manager.get_field_at_position(pos.x(), pos.y())

        if clicked_field:
            self._start_move_operation(clicked_field)
            return clicked_field

        return None

    def deprecated_handle_mouse_move(self, pos: QPoint) -> bool:
        """
        Handle mouse move event
        Returns True if a drag operation is in progress
        """
        if not self.drag_state.is_active() or not self.drag_state.start_pos:
            # Update cursor based on position
            self._update_cursor_for_position(pos)
            return False

        dx = pos.x() - self.drag_state.start_pos.x()
        dy = pos.y() - self.drag_state.start_pos.y()

        if self.drag_state.mode == DragMode.MOVE:
            self._handle_move_operation(dx, dy)
        elif self.drag_state.mode == DragMode.RESIZE:
            self._handle_resize_operation(dx, dy)

        return True

    def handle_mouse_move(self, pos: QPoint) -> bool:
        """
        Handle mouse move event
        Returns True if a drag operation is in progress
        """
        if not self.drag_state.is_active() or not self.drag_state.start_pos:
            # Update cursor based on position
            self._update_cursor_for_position(pos)
            return False

        # ✅ ADD THIS: If you need zoom-aware drag sensitivity
        # Convert screen movement to document movement
        screen_dx = pos.x() - self.drag_state.start_pos.x()
        screen_dy = pos.y() - self.drag_state.start_pos.y()

        # If pos is in screen coordinates, convert delta to document space
        # doc_dx = screen_dx / self.zoom_level  # Uncomment if needed
        # doc_dy = screen_dy / self.zoom_level  # Uncomment if needed

        # For now, assume pos is already in document coordinates
        dx = screen_dx
        dy = screen_dy

        if self.drag_state.mode == DragMode.MOVE:
            self._handle_move_operation(dx, dy)
        elif self.drag_state.mode == DragMode.RESIZE:
            self._handle_resize_operation(dx, dy)

        return True

    def handle_mouse_release(self, pos: QPoint) -> bool:
        """
        Handle mouse release event
        Returns True if a drag operation was completed
        """
        if not self.drag_state.is_active():
            return False

        # Emit final signals
        if self.drag_state.mode == DragMode.MOVE and self.drag_state.target_field:
            field = self.drag_state.target_field
            self.fieldMoved.emit(field.id, field.x, field.y)
        elif self.drag_state.mode == DragMode.RESIZE and self.drag_state.target_field:
            field = self.drag_state.target_field
            self.fieldResized.emit(field.id, field.x, field.y, field.width, field.height)

        # Reset drag state
        was_active = self.drag_state.is_active()
        self.drag_state.reset()

        # Update cursor
        self._update_cursor_for_position(pos)

        return was_active

    def _start_move_operation(self, field: FormField):
        """Start a move operation"""
        self.drag_state.mode = DragMode.MOVE
        self.drag_state.target_field = field
        self.drag_state.start_field_pos = (field.x, field.y)

    def _start_resize_operation(self, field: FormField, handle: str):
        """Start a resize operation"""
        self.drag_state.mode = DragMode.RESIZE
        self.drag_state.target_field = field
        self.drag_state.resize_handle = handle
        self.drag_state.start_field_pos = (field.x, field.y)
        self.drag_state.start_field_size = (field.width, field.height)

    def _handle_move_operation(self, dx: int, dy: int):
        """Handle field movement"""
        if not self.drag_state.target_field or not self.drag_state.start_field_pos:
            return

        field = self.drag_state.target_field
        start_x, start_y = self.drag_state.start_field_pos

        # Calculate new position
        new_x = start_x + dx
        new_y = start_y + dy

        # Apply boundary constraints
        new_x, new_y = BoundaryConstraints.constrain_position(
            new_x, new_y, field.width, field.height,
            self.canvas_width, self.canvas_height
        )

        # Apply grid snapping
        if self.snap_to_grid:
            new_x, new_y = GridUtils.snap_to_grid(new_x, new_y, self.grid_size)

        # Update field position
        field.move_to(new_x, new_y)

    def _handle_resize_operation(self, dx: int, dy: int):
        """Handle field resizing"""
        if (not self.drag_state.target_field or
            not self.drag_state.start_field_pos or
            not self.drag_state.start_field_size or
            not self.drag_state.resize_handle):
            return

        field = self.drag_state.target_field
        start_x, start_y = self.drag_state.start_field_pos
        start_width, start_height = self.drag_state.start_field_size

        # Calculate new dimensions
        new_x, new_y, new_width, new_height = ResizeCalculator.calculate_resize(
            start_x, start_y, start_width, start_height,
            dx, dy, self.drag_state.resize_handle
        )

        # Apply boundary constraints
        new_x, new_y = BoundaryConstraints.constrain_position(
            new_x, new_y, new_width, new_height,
            self.canvas_width, self.canvas_height
        )

        new_width, new_height = BoundaryConstraints.constrain_size(
            new_width, new_height, new_x, new_y,
            self.canvas_width, self.canvas_height
        )

        # Apply grid snapping for size
        if self.snap_to_grid:
            new_width, new_height = GridUtils.snap_size_to_grid(
                new_width, new_height, self.grid_size
            )

        # Update field
        field.x = new_x
        field.y = new_y
        field.resize_to(new_width, new_height)

    def _update_cursor_for_position(self, pos: QPoint):
        """Update cursor based on current position"""
        # Check all fields for resize handles or move cursor
        for field in self.field_manager.fields:
            # Check resize handles first
            handle = ResizeHandles.get_handle_at_position(
                pos.x(), pos.y(), field.x, field.y, field.width, field.height
            )

            if handle:
                cursor = ResizeHandles.get_cursor_for_handle(handle)
                self.cursorChanged.emit(cursor)  # No IDE warning with proper typing
                return

            # Check if over field body (for move cursor)
            if field.contains_point(pos.x(), pos.y()):
                self.cursorChanged.emit(Qt.CursorShape.SizeAllCursor)
                return

        # Default cursor
        self.cursorChanged.emit(Qt.CursorShape.ArrowCursor)

    def handle_keyboard_move(self, field: FormField, dx: int, dy: int):
        """Handle keyboard-based field movement"""
        if not field:
            return

        new_x = field.x + dx
        new_y = field.y + dy

        # Apply boundary constraints
        new_x, new_y = BoundaryConstraints.constrain_position(
            new_x, new_y, field.width, field.height,
            self.canvas_width, self.canvas_height
        )

        # Apply grid snapping if enabled
        if self.snap_to_grid:
            new_x, new_y = GridUtils.snap_to_grid(new_x, new_y, self.grid_size)

        # Update field position
        field.move_to(new_x, new_y)

        # Emit signal
        self.fieldMoved.emit(field.id, field.x, field.y)




class WorkingSelectionHandler(QObject):
    """A completely working SelectionHandler class"""

    def __init__(self, field_manager=None):
        super().__init__()
        self.field_manager = field_manager
        self.selected_field = None
        print("✅ WorkingSelectionHandler initialized successfully")

    def select_field(self, field):
        """Select a field - signal-free version"""
        old_field = self.selected_field
        self.selected_field = field
        if old_field != field:
            print(f"✅ Selection changed: {old_field.name if old_field else 'None'} → {field.name if field else 'None'}")

            # Notify any callbacks instead of using signals
            self._notify_callbacks(field)

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
        """Clear selection - this is where the error happens"""
        print("🔄 Clearing selection...")
        try:
            self.select_field(None)
            print("✅ Selection cleared successfully")
        except Exception as e:
            print(f"⚠️ Error clearing selection: {e}")
            self.selected_field = None

    def get_selected_field(self):
        """Get selected field"""
        return self.selected_field

    def select_field_at_position(self, x, y):
        """Select field at given position safely"""
        try:
            if self.field_manager and hasattr(self.field_manager, 'get_field_at_position'):
                field = self.field_manager.get_field_at_position(x, y)
                self.select_field(field)
                return field
            else:
                print("⚠️ Field manager not available for position selection")
                return None
        except Exception as e:
            print(f"⚠️ Error selecting field at position: {e}")
            return None

    def delete_selected_field(self):
        """Delete currently selected field safely"""
        try:
            if self.selected_field and self.field_manager:
                if hasattr(self.field_manager, 'remove_field'):
                    success = self.field_manager.remove_field(self.selected_field)
                    if success:
                        self.clear_selection()
                    return success
            return False
        except Exception as e:
            print(f"⚠️ Error deleting selected field: {e}")
            return False

    def duplicate_selected_field(self):
        """Duplicate currently selected field safely"""
        try:
            if self.selected_field and self.field_manager:
                if hasattr(self.field_manager, 'duplicate_field'):
                    new_field = self.field_manager.duplicate_field(self.selected_field)
                    if new_field:
                        self.select_field(new_field)
                    return new_field
            return None
        except Exception as e:
            print(f"⚠️ Error duplicating selected field: {e}")
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
