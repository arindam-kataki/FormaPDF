"""
Enhanced Single Control Resizing Implementation
Improvements to the existing resize functionality
"""

from typing import Optional, Tuple, Dict, List
from enum import Enum
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QCursor

from models.field_model import FormField, FieldManager
from utils.geometry_utils import (
    ResizeHandles, ResizeCalculator, BoundaryConstraints, GridUtils
)


class ResizeQuality(Enum):
    """Quality settings for resize operations"""
    FAST = "fast"  # Basic resizing, minimal calculations
    SMOOTH = "smooth"  # Smooth resizing with interpolation
    PRECISE = "precise"  # High precision with snap-to-grid


class EnhancedResizeHandler(QObject):
    """Enhanced resize handler with improved features"""

    # Signals
    resizeStarted = pyqtSignal(str)  # field_id
    resizeProgress = pyqtSignal(str, int, int, int, int)  # field_id, x, y, w, h
    resizeCompleted = pyqtSignal(str, int, int, int, int)  # field_id, x, y, w, h
    resizeCancelled = pyqtSignal(str)  # field_id

    def __init__(self, field_manager: FieldManager):
        super().__init__()
        self.field_manager = field_manager

        # Enhanced configuration
        self.resize_quality = ResizeQuality.SMOOTH
        self.preserve_aspect_ratio = False
        self.constrain_to_page = True
        self.show_resize_preview = True
        self.snap_threshold = 10  # pixels
        self.min_resize_delta = 3  # minimum movement before resize starts

        # Advanced constraints
        self.custom_min_sizes = {}  # field_id -> (width, height)
        self.custom_max_sizes = {}  # field_id -> (width, height)
        self.aspect_ratios = {}  # field_id -> ratio

        # Performance optimization
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._apply_pending_resize)
        self.pending_resize_data = None

        # State tracking
        self.active_resize = None
        self.resize_history = []  # For undo functionality

    def set_resize_quality(self, quality: ResizeQuality):
        """Set the quality/performance mode for resizing"""
        self.resize_quality = quality

    def set_field_constraints(self, field_id: str,
                              min_size: Optional[Tuple[int, int]] = None,
                              max_size: Optional[Tuple[int, int]] = None,
                              aspect_ratio: Optional[float] = None):
        """Set custom constraints for a specific field"""
        if min_size:
            self.custom_min_sizes[field_id] = min_size
        if max_size:
            self.custom_max_sizes[field_id] = max_size
        if aspect_ratio:
            self.aspect_ratios[field_id] = aspect_ratio

    def start_resize(self, field: FormField, handle: str, start_pos: QPoint) -> bool:
        """Start a resize operation with enhanced features"""
        if self.active_resize:
            return False

        # Store initial state for undo
        initial_state = {
            'field_id': field.id,
            'x': field.x,
            'y': field.y,
            'width': field.width,
            'height': field.height
        }
        self.resize_history.append(initial_state)

        self.active_resize = {
            'field': field,
            'handle': handle,
            'start_pos': start_pos,
            'start_field_pos': (field.x, field.y),
            'start_field_size': (field.width, field.height),
            'total_delta': (0, 0)
        }

        self.resizeStarted.emit(field.id)
        return True

    def update_resize(self, current_pos: QPoint, zoom_level: float = 1.0) -> bool:
        """Update resize operation with enhanced calculations"""
        if not self.active_resize:
            return False

        field = self.active_resize['field']
        handle = self.active_resize['handle']
        start_pos = self.active_resize['start_pos']
        start_field_pos = self.active_resize['start_field_pos']
        start_field_size = self.active_resize['start_field_size']

        # Calculate deltas with zoom consideration
        screen_dx = current_pos.x() - start_pos.x()
        screen_dy = current_pos.y() - start_pos.y()

        # Zoom-aware delta calculation
        dx = screen_dx / zoom_level
        dy = screen_dy / zoom_level

        # Check minimum movement threshold
        total_movement = abs(dx) + abs(dy)
        if total_movement < self.min_resize_delta:
            return True

        # Calculate new dimensions
        new_x, new_y, new_width, new_height = self._calculate_enhanced_resize(
            start_field_pos[0], start_field_pos[1],
            start_field_size[0], start_field_size[1],
            dx, dy, handle, field.id
        )

        # Apply quality-specific processing
        if self.resize_quality == ResizeQuality.SMOOTH:
            new_x, new_y, new_width, new_height = self._apply_smooth_resize(
                new_x, new_y, new_width, new_height
            )
        elif self.resize_quality == ResizeQuality.PRECISE:
            new_x, new_y, new_width, new_height = self._apply_precise_resize(
                new_x, new_y, new_width, new_height
            )

        # Update field with performance optimization
        if self.resize_quality == ResizeQuality.FAST:
            # Immediate update for fast mode
            self._apply_resize_to_field(field, new_x, new_y, new_width, new_height)
        else:
            # Debounced update for smooth/precise modes
            self.pending_resize_data = (field, new_x, new_y, new_width, new_height)
            self.resize_timer.start(16)  # ~60fps

        self.resizeProgress.emit(field.id, new_x, new_y, new_width, new_height)
        return True

    def _calculate_enhanced_resize(self, start_x: int, start_y: int,
                                   start_width: int, start_height: int,
                                   dx: int, dy: int, handle: str,
                                   field_id: str) -> Tuple[int, int, int, int]:
        """Enhanced resize calculation with custom constraints"""

        # Get custom constraints for this field
        min_w, min_h = self.custom_min_sizes.get(field_id, (20, 15))
        max_w, max_h = self.custom_max_sizes.get(field_id, (9999, 9999))
        aspect_ratio = self.aspect_ratios.get(field_id)

        # Basic resize calculation
        new_x, new_y, new_width, new_height = ResizeCalculator.calculate_resize(
            start_x, start_y, start_width, start_height,
            dx, dy, handle, min_w, min_h
        )

        # Apply aspect ratio constraint if enabled
        if self.preserve_aspect_ratio or aspect_ratio:
            ratio = aspect_ratio or (start_width / start_height)
            new_width, new_height = self._apply_aspect_ratio(
                new_width, new_height, ratio, handle
            )

        # Apply maximum size constraints
        new_width = min(new_width, max_w)
        new_height = min(new_height, max_h)

        # Recalculate position if size was constrained
        if 'left' in handle and new_width != start_width + dx:
            new_x = start_x + start_width - new_width
        if 'top' in handle and new_height != start_height + dy:
            new_y = start_y + start_height - new_height

        return new_x, new_y, new_width, new_height

    def _apply_aspect_ratio(self, width: int, height: int, ratio: float,
                            handle: str) -> Tuple[int, int]:
        """Apply aspect ratio constraints based on resize handle"""
        if 'left' in handle or 'right' in handle:
            # Width-driven resize
            height = int(width / ratio)
        elif 'top' in handle or 'bottom' in handle:
            # Height-driven resize
            width = int(height * ratio)
        else:
            # Corner resize - maintain ratio based on dominant change
            width_driven_height = int(width / ratio)
            height_driven_width = int(height * ratio)

            # Choose the option that requires less change
            if abs(height - width_driven_height) < abs(width - height_driven_width):
                height = width_driven_height
            else:
                width = height_driven_width

        return width, height

    def _apply_smooth_resize(self, x: int, y: int, width: int, height: int) -> Tuple[int, int, int, int]:
        """Apply smooth resize with interpolation"""
        # Smooth out small jittery movements
        if hasattr(self, '_last_resize_values'):
            last_x, last_y, last_w, last_h = self._last_resize_values

            # Apply simple smoothing
            smooth_factor = 0.7
            x = int(x * smooth_factor + last_x * (1 - smooth_factor))
            y = int(y * smooth_factor + last_y * (1 - smooth_factor))
            width = int(width * smooth_factor + last_w * (1 - smooth_factor))
            height = int(height * smooth_factor + last_h * (1 - smooth_factor))

        self._last_resize_values = (x, y, width, height)
        return x, y, width, height

    def _apply_precise_resize(self, x: int, y: int, width: int, height: int) -> Tuple[int, int, int, int]:
        """Apply precise resize with grid snapping"""
        # Always snap to grid in precise mode
        x, y = GridUtils.snap_to_grid(x, y, 5)  # Fine grid
        width, height = GridUtils.snap_size_to_grid(width, height, 5)
        return x, y, width, height

    def _apply_pending_resize(self):
        """Apply pending resize operation (called by timer)"""
        if self.pending_resize_data:
            field, x, y, width, height = self.pending_resize_data
            self._apply_resize_to_field(field, x, y, width, height)
            self.pending_resize_data = None

    def _apply_resize_to_field(self, field: FormField, x: int, y: int,
                               width: int, height: int):
        """Apply resize changes to the field"""
        field.x = x
        field.y = y
        field.resize_to(width, height)

    def finish_resize(self) -> bool:
        """Complete the resize operation"""
        if not self.active_resize:
            return False

        field = self.active_resize['field']
        self.resizeCompleted.emit(field.id, field.x, field.y, field.width, field.height)

        # Clear state
        self.active_resize = None
        if hasattr(self, '_last_resize_values'):
            delattr(self, '_last_resize_values')

        return True

    def cancel_resize(self) -> bool:
        """Cancel the current resize operation"""
        if not self.active_resize:
            return False

        field = self.active_resize['field']

        # Restore original state
        if self.resize_history:
            original_state = self.resize_history[-1]
            field.x = original_state['x']
            field.y = original_state['y']
            field.resize_to(original_state['width'], original_state['height'])

        self.resizeCancelled.emit(field.id)
        self.active_resize = None

        return True

    def undo_last_resize(self) -> bool:
        """Undo the last resize operation"""
        if not self.resize_history:
            return False

        last_state = self.resize_history.pop()
        field = self.field_manager.get_field_by_id(last_state['field_id'])

        if field:
            field.x = last_state['x']
            field.y = last_state['y']
            field.resize_to(last_state['width'], last_state['height'])
            return True

        return False

    def clear_resize_history(self):
        """Clear the resize history (call periodically to manage memory)"""
        # Keep only last 10 operations
        if len(self.resize_history) > 10:
            self.resize_history = self.resize_history[-10:]


# Integration example for main window
class ResizeIntegration:
    """Example of how to integrate enhanced resizing into the main application"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.enhanced_resize = EnhancedResizeHandler(main_window.field_manager)

        # Connect signals
        self.enhanced_resize.resizeStarted.connect(self.on_resize_started)
        self.enhanced_resize.resizeProgress.connect(self.on_resize_progress)
        self.enhanced_resize.resizeCompleted.connect(self.on_resize_completed)

        # Configure resize settings
        self.enhanced_resize.set_resize_quality(ResizeQuality.SMOOTH)
        self.enhanced_resize.preserve_aspect_ratio = False
        self.enhanced_resize.show_resize_preview = True

    def on_resize_started(self, field_id: str):
        """Handle resize start"""
        self.main_window.status_bar.showMessage(f"Resizing {field_id}...")

    def on_resize_progress(self, field_id: str, x: int, y: int, width: int, height: int):
        """Handle resize progress"""
        # Update properties panel in real-time
        if hasattr(self.main_window, 'properties_panel'):
            self.main_window.properties_panel.update_field_properties(
                field_id, x, y, width, height
            )

    def on_resize_completed(self, field_id: str, x: int, y: int, width: int, height: int):
        """Handle resize completion"""
        self.main_window.status_bar.showMessage(f"Resized {field_id}", 2000)

        # Mark document as modified
        if hasattr(self.main_window, 'document_modified'):
            self.main_window.document_modified = True