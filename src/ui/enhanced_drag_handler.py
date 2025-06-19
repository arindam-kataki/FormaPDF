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

    # Signals for drag and resize operations
    fieldMoved = pyqtSignal(str, int, int)  # field_id, new_x, new_y
    fieldResized = pyqtSignal(str, int, int, int, int)  # field_id, x, y, width, height
    cursorChanged = pyqtSignal(Qt.CursorShape)
    dragStarted = pyqtSignal(str, str)  # field_id, operation_type
    dragProgress = pyqtSignal(str, int, int, int, int)  # field_id, x, y, w, h
    dragCompleted = pyqtSignal(str)  # field_id

    def __init__(self, canvas, field_manager):
        self.canvas = canvas
        self.field_manager = field_manager
        self.selected_fields = []
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.zoom_level = 1.0

        # Create drag overlay
        self.drag_overlay = DragOverlay(canvas)
        self.drag_overlay.hide()  # Initially hidden

        self.resize_mode = False
        self.resize_handle = None
        self.resize_start_pos = QPoint()
        self.resize_start_size = (0, 0)
        self.resize_field = None

    def set_zoom_level(self, zoom_level: float):
        """Update zoom level for drag calculations"""
        self.zoom_level = zoom_level

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
            if len(self.selected_fields) == 1 and clicked_field == self.selected_fields[0]:
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
                    self.resize_field = clicked_field
                    self.dragStarted.emit(clicked_field.id, "resize")
                    return clicked_field

            # Handle multi-selection with Ctrl
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if clicked_field in self.selected_fields:
                    self.selected_fields.remove(clicked_field)
                else:
                    self.selected_fields.append(clicked_field)
            else:
                # Single selection
                self.selected_fields = [clicked_field]

            # Prepare for potential drag
            self.drag_start_pos = pos

            print(f"🎯 Enhanced drag handler: {len(self.selected_fields)} fields selected")
        else:
            print(f"❌ No field found at {pos} on page {search_page}")
            # ✅ DEBUG: Show what fields exist on this page
            fields_on_page = [f for f in self.field_manager.fields if f.page_number == search_page]
            print(f"   Available fields on page {search_page}: {len(fields_on_page)}")
            for field in fields_on_page:
                print(f"   - {field.name} at ({field.x}, {field.y})")

        return clicked_field

    def deprecated_2_handle_mouse_press(self, pos: QPoint, modifiers: Qt.KeyboardModifier, page_num: int = None) -> Optional[Any]:
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

            print(f"✅ Found field {clicked_field.name} on page {clicked_field.page_number}")

            # ✅ ADDITIONAL SAFETY CHECK: Ensure field is on current page
            if clicked_field.page_number != search_page:
                print(
                    f"⚠️ Field {clicked_field.name} is on page {clicked_field.page_number}, but current page is {search_page}. Ignoring click.")
                return None

            # ✅ WHEN MULTI-SELECTING, PREVENT CROSS-PAGE SELECTION
            if self.selected_fields and modifiers & Qt.KeyboardModifier.ControlModifier:
                # Check if we're trying to multi-select across pages
                first_selected_page = self.selected_fields[0].page_number if self.selected_fields else search_page
                if first_selected_page != search_page:
                    print(
                        f"🔄 Switching from page {first_selected_page} to page {search_page}, clearing previous selection")
                    self.selected_fields.clear()

            # Handle multi-selection with Ctrl
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if clicked_field in self.selected_fields:
                    self.selected_fields.remove(clicked_field)
                else:
                    self.selected_fields.append(clicked_field)
            else:
                # Single selection
                self.selected_fields = [clicked_field]

            # Prepare for potential drag
            self.drag_start_pos = pos

            print(f"🎯 Enhanced drag handler: {len(self.selected_fields)} fields selected")
        else:
            print(f"❌ No field found at {pos} on page {search_page}")
            # ✅ DEBUG: Show what fields exist on this page
            fields_on_page = [f for f in self.field_manager.fields if f.page_number == search_page]
            print(f"   Available fields on page {search_page}: {len(fields_on_page)}")
            for field in fields_on_page:
                print(f"   - {field.name} at ({field.x}, {field.y})")

        return clicked_field

    def deprecated_2_handle_mouse_press(self, pos: QPoint, modifiers: Qt.KeyboardModifier) -> Optional[Any]:
        """
        Handle mouse press - detect field clicks and prepare for dragging

        Returns:
            Field object if clicked, None otherwise
        """

        if hasattr(self.canvas, 'update_current_page_from_scroll'):
            self.canvas.update_current_page_from_scroll()

        current_page = getattr(self.canvas, 'current_page', 0)
        print(f"🔍 Enhanced drag handler: Looking for field at {pos} on page {current_page}")

        # ✅ FORCE UPDATE CURRENT PAGE BEFORE FIELD LOOKUP:
        if hasattr(self.canvas, 'update_current_page_from_scroll'):
            self.canvas.update_current_page_from_scroll()
            updated_page = getattr(self.canvas, 'current_page', 0)
            print(f"📄 Updated current page to: {updated_page}")
            current_page = updated_page

        clicked_field = self.field_manager.get_field_at_position(
            pos.x(), pos.y(), current_page
        )

        clicked_field = self.field_manager.get_field_at_position(
            pos.x(), pos.y(), self.canvas.current_page
        )

        if clicked_field:
            # Handle multi-selection with Ctrl
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if clicked_field in self.selected_fields:
                    self.selected_fields.remove(clicked_field)
                else:
                    self.selected_fields.append(clicked_field)
            else:
                # Single selection
                self.selected_fields = [clicked_field]

            # Prepare for potential drag
            self.drag_start_pos = pos

            print(f"🎯 Enhanced drag handler: {len(self.selected_fields)} fields selected")

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

        if not self.selected_fields:
            return False

        # Check if we should start dragging
        if not self.is_dragging:
            drag_distance = (pos - self.drag_start_pos).manhattanLength()
            if drag_distance > 5:  # Start drag after 5 pixel threshold
                self.start_drag()

        # Update drag if in progress
        if self.is_dragging:
            self.drag_overlay.update_drag(pos)

        return self.is_dragging

    def _handle_resize_move(self, pos: QPoint):
        """Handle mouse movement during resize operation"""
        if not self.resize_field or not self.resize_handle:
            return

        field = self.resize_field
        start_x, start_y = field.x, field.y
        start_width, start_height = self.resize_start_size

        # Calculate deltas
        dx = (pos.x() - self.resize_start_pos.x()) / self.zoom_level
        dy = (pos.y() - self.resize_start_pos.y()) / self.zoom_level

        # Import resize calculator
        from utils.geometry_utils import ResizeCalculator, BoundaryConstraints, GridUtils

        # Calculate new dimensions
        new_x, new_y, new_width, new_height = ResizeCalculator.calculate_resize(
            start_x, start_y, start_width, start_height,
            dx, dy, self.resize_handle, 20, 15  # min_width, min_height
        )

        # Apply constraints (optional - you can add canvas bounds later)
        # new_x, new_y = BoundaryConstraints.constrain_position(...)

        # Apply grid snapping (optional)
        # if snap_to_grid:
        #     new_x, new_y = GridUtils.snap_to_grid(new_x, new_y, grid_size)

        # Update field
        field.x = new_x
        field.y = new_y
        field.resize_to(new_width, new_height)

        # Emit progress signal
        self.dragProgress.emit(field.id, new_x, new_y, new_width, new_height)

    def deprecated_1_handle_mouse_move(self, pos: QPoint) -> bool:
        """
        Handle mouse move - start/update dragging

        Returns:
            bool: True if currently dragging
        """
        if not self.selected_fields:
            return False

        # Check if we should start dragging
        if not self.is_dragging:
            drag_distance = (pos - self.drag_start_pos).manhattanLength()
            if drag_distance > 5:  # Start drag after 5 pixel threshold
                self.start_drag()

        # Update drag if in progress
        if self.is_dragging:
            self.drag_overlay.update_drag(pos)

        return self.is_dragging

    def start_drag(self):
        """Start drag operation using overlay"""
        if not self.selected_fields:
            return

        print(f"🚀 Starting drag operation with {len(self.selected_fields)} fields")

        self.is_dragging = True
        self.drag_overlay.start_drag(
            self.selected_fields,
            self.drag_start_pos,
            self.zoom_level
        )

        # Emit drag started signal
        field_info = "multiple" if len(self.selected_fields) > 1 else self.selected_fields[0].id
        self.dragStarted.emit(field_info, "move")

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

            # Reset resize mode
            self.resize_mode = False
            self.resize_handle = None
            self.resize_field = None
            print("✅ Resize operation completed")
            return True

        if not self.is_dragging:
            return False

        # End drag operation
        was_dragging = self.drag_overlay.end_drag()

        if was_dragging:
            # Apply drag changes to actual fields
            self.apply_drag_changes(pos)

            # Emit completion signal
            self.dragCompleted.emit("multiple" if len(self.selected_fields) > 1 else self.selected_fields[0].id)

            # ✅ CLEAR SELECTION AFTER DRAG ENDS
            print("🧹 Clearing selection after drag completion")
            field_count = len(self.selected_fields)
            self.selected_fields.clear()

            # Also clear canvas selection handler
            if hasattr(self.canvas, 'selection_handler') and self.canvas.selection_handler:
                try:
                    self.canvas.selection_handler.clear_selection()
                    print("🧹 Cleared canvas selection handler")
                except Exception as e:
                    print(f"⚠️ Error clearing canvas selection: {e}")

        self.is_dragging = False
        return was_dragging

    def deprecated_1_handle_mouse_release(self, pos: QPoint) -> bool:
        """
        Handle mouse release - end dragging and apply changes

        Returns:
            bool: True if drag was ended
        """
        if not self.is_dragging:
            return False

        # End drag operation
        was_dragging = self.drag_overlay.end_drag()

        if was_dragging:
            # Apply drag changes to actual fields
            self.apply_drag_changes(pos)

            # ✅ CLEAR SELECTION AFTER DRAG ENDS
            print("🧹 Clearing selection after drag completion")
            field_count = len(self.selected_fields)
            self.selected_fields.clear()

            # Also clear canvas selection handler
            if hasattr(self.canvas, 'selection_handler') and self.canvas.selection_handler:
                try:
                    self.canvas.selection_handler.clear_selection()
                    print("🧹 Cleared canvas selection handler")
                except Exception as e:
                    print(f"⚠️ Error clearing canvas selection: {e}")

        self.is_dragging = False
        return was_dragging

    def apply_drag_changes(self, final_pos: QPoint):
        """Apply drag offset to actual field positions"""
        if not self.selected_fields:
            return

        # Calculate final drag offset
        drag_offset = final_pos - self.drag_start_pos

        # Apply offset to each field
        for field in self.selected_fields:
            # Convert screen offset to document coordinates
            doc_offset_x = drag_offset.x() / self.zoom_level
            doc_offset_y = drag_offset.y() / self.zoom_level

            # Update field position
            field.x += doc_offset_x
            field.y += doc_offset_y

            print(f"✅ Moved field {field.name} by ({doc_offset_x:.1f}, {doc_offset_y:.1f})")

    def clear_selection(self):
        """Clear field selection"""
        self.selected_fields.clear()
        if self.is_dragging:
            self.drag_overlay.cancel_drag()
            self.is_dragging = False

    def get_selected_fields(self) -> List[Any]:
        """Get currently selected fields"""
        return self.selected_fields.copy()


class Deprecated_EnhancedDragHandler(QObject):
    """Enhanced drag handler with multi-selection and improved functionality"""

    # Signals for drag operations
    fieldMoved = pyqtSignal(str, int, int)  # field_id, new_x, new_y
    fieldResized = pyqtSignal(str, int, int, int, int)  # field_id, x, y, width, height
    multipleFieldsMoved = pyqtSignal(list)  # list of (field_id, x, y) tuples
    cursorChanged = pyqtSignal(Qt.CursorShape)
    dragStarted = pyqtSignal(str)  # field_id or "multiple"
    dragCompleted = pyqtSignal(str)  # field_id or "multiple"

    def __init__(self, field_manager: FieldManager, selection_handler=None):
        super().__init__()
        self.field_manager = field_manager
        self.selection_handler = selection_handler
        self.drag_state = DragState()

        # Configuration
        self.grid_size = 20
        self.snap_to_grid = True
        self.canvas_width = 800
        self.canvas_height = 600
        self.zoom_level = 1.0

        # Multi-selection support
        self.multi_selection_enabled = True
        self.selected_fields = set()

    def set_canvas_size(self, width: int, height: int):
        """Update canvas dimensions for boundary constraints"""
        self.canvas_width = width
        self.canvas_height = height

    def set_zoom_level(self, zoom: float):
        """Update zoom level for coordinate transformations"""
        self.zoom_level = zoom

    def set_grid_settings(self, grid_size: int, snap_to_grid: bool):
        """Update grid settings"""
        self.grid_size = grid_size
        self.snap_to_grid = snap_to_grid

    def handle_mouse_press(self, pos: QPoint, modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier, page_num: int = None) -> Optional[FormField]:
        """
        Enhanced mouse press handler with multi-selection support
        Returns the field that should be selected
        """
        self.drag_state.reset()
        self.drag_state.start_pos = pos
        self.drag_state.current_pos = pos

        if page_num is not None:
            search_page = page_num
            print(f"🔍 Using provided page number: {search_page}")
        else:
            search_page = getattr(self.canvas, 'current_page', 0)
            print(f"🔍 Using canvas current page: {search_page}")

        print(f"🔍 Enhanced drag handler: Looking for field at {pos} on page {search_page}")

        # Get currently selected field(s)
        selected_field = self.selection_handler.get_selected_field() if self.selection_handler else None

        # Check if clicking on resize handle of selected field
        if selected_field and not (modifiers & Qt.KeyboardModifier.ControlModifier):
            handle = ResizeHandles.get_handle_at_position(
                pos.x(), pos.y(),
                selected_field.x, selected_field.y,
                selected_field.width, selected_field.height
            )

            if handle:
                self._prepare_resize_operation(selected_field, handle)
                return selected_field

        # Check if clicking on a field
        clicked_field = self.field_manager.get_field_at_position(pos.x(), pos.y(), search_page)

        if clicked_field:
            print(f"✅ Found field {clicked_field.name} on page {clicked_field.page_number}")
            if modifiers & Qt.KeyboardModifier.ControlModifier and self.multi_selection_enabled:
                # Multi-select mode: toggle the clicked field
                self._handle_multi_selection(clicked_field)
                self._prepare_multi_move_operation()
            else:
                # Single select mode: clear others and select this one
                self.selected_fields.clear()
                self.selected_fields.add(clicked_field)
                self._prepare_move_operation(clicked_field)

            return clicked_field

        else:
            print(f"❌ No field found at {pos} on page {search_page}")

            # Clicked empty space
        if not (modifiers & Qt.KeyboardModifier.ControlModifier):
            self.selected_fields.clear()

        return None

    def handle_mouse_move(self, pos: QPoint) -> bool:
        """
        Enhanced mouse move handler with smooth dragging
        Returns True if a drag operation is in progress
        """
        if not self.drag_state.start_pos:
            self._update_cursor_for_position(pos)
            return False

        self.drag_state.current_pos = pos

        # Check if we should start dragging
        if not self.drag_state.is_dragging and self.drag_state.should_start_drag(pos):
            self.drag_state.is_dragging = True
            self._emit_drag_started()

        if not self.drag_state.is_active():
            self._update_cursor_for_position(pos)
            return False

        # Calculate movement deltas
        dx = pos.x() - self.drag_state.start_pos.x()
        dy = pos.y() - self.drag_state.start_pos.y()

        # Handle different drag modes
        if self.drag_state.mode == DragMode.MOVE:
            self._handle_move_operation(dx, dy)
        elif self.drag_state.mode == DragMode.RESIZE:
            self._handle_resize_operation(dx, dy)
        elif self.drag_state.mode == DragMode.MULTI_SELECT:
            self._handle_multi_move_operation(dx, dy)

        return True

    def handle_mouse_release(self, pos: QPoint) -> bool:
        """
        Enhanced mouse release handler
        Returns True if a drag operation was completed
        """
        was_dragging = self.drag_state.is_active()

        if was_dragging:
            self._emit_drag_completed()

            # Emit final position signals
            if self.drag_state.mode == DragMode.MOVE and self.drag_state.target_field:
                field = self.drag_state.target_field
                # ✅ UPDATE PAGE NUMBER based on final Y position
                self._update_field_page_number(field, field.x, field.y)  # Pass x, y
                self.fieldMoved.emit(field.id, field.x, field.y)
            elif self.drag_state.mode == DragMode.RESIZE and self.drag_state.target_field:
                field = self.drag_state.target_field
                self.fieldResized.emit(field.id, field.x, field.y, field.width, field.height)
            elif self.drag_state.mode == DragMode.MULTI_SELECT:
                # ✅ ADD: Update page numbers for all moved fields
                for field in self.selected_fields:
                    self._update_field_page_number(field, field.x, field.y)  # Pass x, y

                moved_fields = [(f.id, f.x, f.y) for f in self.selected_fields]
                self.multipleFieldsMoved.emit(moved_fields)

        # Reset drag state
        self.drag_state.reset()

        # Update cursor
        self._update_cursor_for_position(pos)

        return was_dragging

    def _update_field_page_number(self, field):
        """Update field's page number based on Y position"""
        try:
            # Simple logic: assume each page is ~800 pixels high at 1x zoom
            page_height = 800 * self.zoom_level
            page_gap = 20  # Gap between pages

            # Calculate which page based on Y position
            total_page_height = page_height + page_gap
            new_page = max(0, int(field.y / total_page_height))

            if new_page != field.page_number:
                print(f"🔄 Field {field.id}: page {field.page_number} → page {new_page} (y={field.y})")
                field.page_number = new_page

        except Exception as e:
            print(f"⚠️ Error updating page number for {field.id}: {e}")

    def _handle_multi_selection(self, clicked_field: FormField):
        """Handle Ctrl+Click multi-selection with toggle support"""

        # Check if we're starting selection on a different page
        if self.selected_fields:
            first_selected_page = list(self.selected_fields)[0].page_number
            if clicked_field.page_number != first_selected_page:
                # Clear selection and start fresh on new page
                print(f"🔄 Switching from page {first_selected_page} to page {clicked_field.page_number}")
                self.selected_fields.clear()
                self.selected_fields.add(clicked_field)
                return

        # Toggle behavior: if already selected, remove it; if not selected, add it
        if clicked_field in self.selected_fields:
            self.selected_fields.remove(clicked_field)
            print(f"➖ Removed {clicked_field.id} from selection ({len(self.selected_fields)} remaining)")
        else:
            self.selected_fields.add(clicked_field)
            print(f"➕ Added {clicked_field.id} to selection ({len(self.selected_fields)} total)")

    def _prepare_move_operation(self, field: FormField):
        """Prepare for moving a single field"""
        self.drag_state.mode = DragMode.MOVE
        self.drag_state.target_field = field
        self.drag_state.start_field_pos = (field.x, field.y)

    def _prepare_multi_move_operation(self):
        """Prepare for moving multiple fields"""
        if len(self.selected_fields) > 1:
            self.drag_state.mode = DragMode.MULTI_SELECT
            # Store start positions for all selected fields
            for field in self.selected_fields:
                self.drag_state.multi_drag_start_positions[field.id] = (field.x, field.y)

    def _prepare_resize_operation(self, field: FormField, handle: str):
        """Prepare for resizing a field"""
        self.drag_state.mode = DragMode.RESIZE
        self.drag_state.target_field = field
        self.drag_state.resize_handle = handle
        self.drag_state.start_field_pos = (field.x, field.y)
        self.drag_state.start_field_size = (field.width, field.height)

    def _handle_move_operation(self, dx: int, dy: int):
        """Handle single field movement with WORKING page constraints"""
        if not self.drag_state.target_field or not self.drag_state.start_field_pos:
            return

        field = self.drag_state.target_field
        start_x, start_y = self.drag_state.start_field_pos

        # Calculate proposed new position
        adjusted_dx = dx / self.zoom_level if self.zoom_level != 1.0 else dx
        adjusted_dy = dy / self.zoom_level if self.zoom_level != 1.0 else dy

        proposed_x = start_x + adjusted_dx
        proposed_y = start_y + adjusted_dy

        # ✅ APPLY CONSTRAINTS BEFORE UPDATING
        page_bounds = self._get_page_bounds(field.page_number)

        # Constrain to page boundaries
        final_x = max(0, min(proposed_x, page_bounds['width'] - field.width))
        final_y = max(0, min(proposed_y, page_bounds['height'] - field.height))

        # Apply grid snapping to final constrained position
        if self.snap_to_grid:
            final_x, final_y = GridUtils.snap_to_grid(final_x, final_y, self.grid_size)

        # Update field position with constrained coordinates
        field.move_to(int(final_x), int(final_y))

    def _deprecated_handle_move_operation(self, dx: int, dy: int):
        """Handle single field movement with cross-page support"""
        if not self.drag_state.target_field or not self.drag_state.start_field_pos:
            return

        field = self.drag_state.target_field
        start_x, start_y = self.drag_state.start_field_pos

        # Calculate new position with zoom consideration
        adjusted_dx = dx / self.zoom_level if self.zoom_level != 1.0 else dx
        adjusted_dy = dy / self.zoom_level if self.zoom_level != 1.0 else dy

        new_x = start_x + adjusted_dx
        new_y = start_y + adjusted_dy



        # ENABLE CROSS-PAGE DRAGGING: Only apply minimal constraints
        # Allow movement across the entire document area
        new_x = max(-50, new_x)  # Small left margin
        new_y = max(-50, new_y)  # Small top margin
        # No right/bottom limits - allow dragging to any page

        # Apply grid snapping
        #if self.snap_to_grid:
        #    new_x, new_y = GridUtils.snap_to_grid(new_x, new_y, self.grid_size)

        # Update field position
        field.move_to(int(new_x), int(new_y))

        # IMPORTANT: Update the field's page number based on new position
        self._update_field_page_number(field, new_x, new_y)

    def _deprecated__handle_move_operation(self, dx: int, dy: int):
        """Handle single field movement with improved constraints"""
        if not self.drag_state.target_field or not self.drag_state.start_field_pos:
            return

        field = self.drag_state.target_field
        start_x, start_y = self.drag_state.start_field_pos

        # Calculate new position with zoom consideration
        adjusted_dx = dx / self.zoom_level if self.zoom_level != 1.0 else dx
        adjusted_dy = dy / self.zoom_level if self.zoom_level != 1.0 else dy

        new_x = start_x + adjusted_dx
        new_y = start_y + adjusted_dy

        # Apply boundary constraints
        new_x, new_y = BoundaryConstraints.constrain_position(
            new_x, new_y, field.width, field.height,
            self.canvas_width, self.canvas_height
        )

        # Apply grid snapping
        if self.snap_to_grid:
            new_x, new_y = GridUtils.snap_to_grid(new_x, new_y, self.grid_size)

        # Update field position
        field.move_to(int(new_x), int(new_y))

    def _update_field_page_number(self, field: FormField, x: float, y: float):
        """Update field's page number based on its Y position"""
        try:
            # Get PDF canvas to determine which page the field is on
            if hasattr(self, 'pdf_canvas_ref'):
                canvas = self.pdf_canvas_ref
            else:
                # Try to find PDF canvas through field manager or selection handler
                canvas = self._find_pdf_canvas()

            if canvas and hasattr(canvas, 'get_page_at_position'):
                page_num = canvas.get_page_at_position(y)
                if page_num is not None and page_num != field.page_number:
                    print(f"🎯 Moving field {field.id} from page {field.page_number} to page {page_num}")
                    field.page_number = page_num

        except Exception as e:
            print(f"⚠️ Error updating field page number: {e}")

    def _find_pdf_canvas(self):
        """Try to find the PDF canvas reference"""
        # This is a helper method to find the canvas when we need it
        if self.selection_handler and hasattr(self.selection_handler, 'field_manager'):
            # Try to get canvas through various paths
            pass
        return None

    def _handle_multi_move_operation(self, dx: int, dy: int):
        """Handle multiple field movement"""
        if not self.drag_state.multi_drag_start_positions:
            return

        # Calculate adjusted deltas for zoom
        adjusted_dx = dx / self.zoom_level if self.zoom_level != 1.0 else dx
        adjusted_dy = dy / self.zoom_level if self.zoom_level != 1.0 else dy

        # Move all selected fields
        for field in self.selected_fields:
            if field.id in self.drag_state.multi_drag_start_positions:
                start_x, start_y = self.drag_state.multi_drag_start_positions[field.id]

                new_x = start_x + adjusted_dx
                new_y = start_y + adjusted_dy

                # Apply boundary constraints
                #new_x, new_y = BoundaryConstraints.constrain_position(
                #    new_x, new_y, field.width, field.height,
                #    self.canvas_width, self.canvas_height
                #)

                # Apply grid snapping
                if self.snap_to_grid:
                    new_x, new_y = GridUtils.snap_to_grid(new_x, new_y, self.grid_size)

                # Update field position
                field.move_to(int(new_x), int(new_y))

    def _handle_resize_operation(self, dx: int, dy: int):
        """Handle field resizing with improved calculations"""
        if (not self.drag_state.target_field or
                not self.drag_state.start_field_pos or
                not self.drag_state.start_field_size or
                not self.drag_state.resize_handle):
            return

        field = self.drag_state.target_field
        start_x, start_y = self.drag_state.start_field_pos
        start_width, start_height = self.drag_state.start_field_size

        # Calculate new dimensions with zoom consideration
        adjusted_dx = dx / self.zoom_level if self.zoom_level != 1.0 else dx
        adjusted_dy = dy / self.zoom_level if self.zoom_level != 1.0 else dy

        new_x, new_y, new_width, new_height = ResizeCalculator.calculate_resize(
            start_x, start_y, start_width, start_height,
            adjusted_dx, adjusted_dy, self.drag_state.resize_handle
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
        field.x = int(new_x)
        field.y = int(new_y)
        field.resize_to(int(new_width), int(new_height))

    def _update_cursor_for_position(self, pos: QPoint):
        """Update cursor based on current position"""
        # Check selected field for resize handles first
        if self.selection_handler:
            selected_field = self.selection_handler.get_selected_field()
            if selected_field:
                handle = ResizeHandles.get_handle_at_position(
                    pos.x(), pos.y(),
                    selected_field.x, selected_field.y,
                    selected_field.width, selected_field.height
                )

                if handle:
                    cursor = ResizeHandles.get_cursor_for_handle(handle)
                    self.cursorChanged.emit(cursor)
                    return

        # Check all fields for move cursor
        for field in self.field_manager.fields:
            if field.contains_point(pos.x(), pos.y()):
                if field in self.selected_fields:
                    self.cursorChanged.emit(Qt.CursorShape.SizeAllCursor)
                else:
                    self.cursorChanged.emit(Qt.CursorShape.PointingHandCursor)
                return

        # Default cursor
        self.cursorChanged.emit(Qt.CursorShape.ArrowCursor)

    def _emit_drag_started(self):
        """Emit drag started signal"""
        if self.drag_state.mode == DragMode.MULTI_SELECT:
            self.dragStarted.emit("multiple")
        elif self.drag_state.target_field:
            self.dragStarted.emit(self.drag_state.target_field.id)

    def _emit_drag_completed(self):
        """Emit drag completed signal"""
        if self.drag_state.mode == DragMode.MULTI_SELECT:
            self.dragCompleted.emit("multiple")
        elif self.drag_state.target_field:
            self.dragCompleted.emit(self.drag_state.target_field.id)

    def handle_keyboard_move(self, dx: int, dy: int):
        """Handle keyboard-based field movement for selected fields"""
        if not self.selected_fields:
            return

        for field in self.selected_fields:
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

    def get_selected_fields(self) -> List[FormField]:
        """Get list of currently selected fields"""
        return list(self.selected_fields)

    def clear_selection(self):
        """Clear all field selections"""
        self.selected_fields.clear()

    def select_field(self, field: FormField, add_to_selection: bool = False):
        """Select a field, optionally adding to existing selection"""
        if not add_to_selection:
            self.selected_fields.clear()

        if field:
            self.selected_fields.add(field)

    def is_field_selected(self, field: FormField) -> bool:
        """Check if a field is currently selected"""
        return field in self.selected_fields

    def _get_page_bounds(self, page_number: int):
        """Get the boundaries for a specific page"""
        try:
            # Simple approach: assume standard page size
            # A4 dimensions in points (72 points per inch)
            page_width = 595  # A4 width in points (8.27 inches * 72)
            page_height = 842  # A4 height in points (11.69 inches * 72)

            # Apply zoom to get actual pixel dimensions
            page_width = int(page_width * self.zoom_level)
            page_height = int(page_height * self.zoom_level)

            return {
                'x': 0,
                'y': 0,
                'width': page_width,
                'height': page_height
            }
        except Exception as e:
            print(f"⚠️ Error getting page bounds: {e}")
            # Fallback dimensions
            return {
                'x': 0,
                'y': 0,
                'width': int(595 * self.zoom_level),
                'height': int(842 * self.zoom_level)
            }

# For backward compatibility, keep the original DragHandler available
class DragHandler(EnhancedDragHandler):
    """Backward compatible drag handler"""
    pass


# Keep existing WorkingSelectionHandler for compatibility
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