"""
Geometry and Layout Utilities
Helper functions for positioning, sizing, and grid operations
"""

from typing import Tuple, Optional
from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt


class GridUtils:
    """Utilities for grid-based layout operations"""

    @staticmethod
    def snap_to_grid(x: int, y: int, grid_size: int) -> Tuple[int, int]:
        """Snap coordinates to grid"""
        snapped_x = round(x / grid_size) * grid_size
        snapped_y = round(y / grid_size) * grid_size
        return snapped_x, snapped_y

    @staticmethod
    def snap_size_to_grid(width: int, height: int, grid_size: int) -> Tuple[int, int]:
        """Snap dimensions to grid"""
        snapped_width = max(grid_size, round(width / grid_size) * grid_size)
        snapped_height = max(grid_size, round(height / grid_size) * grid_size)
        return snapped_width, snapped_height


class BoundaryConstraints:
    """Utilities for constraining elements within boundaries"""

    @staticmethod
    def constrain_position(x: int, y: int, width: int, height: int,
                           canvas_width: int, canvas_height: int) -> Tuple[int, int]:
        """Constrain position to keep element within canvas bounds"""
        constrained_x = max(0, min(x, canvas_width - width))
        constrained_y = max(0, min(y, canvas_height - height))
        return constrained_x, constrained_y

    @staticmethod
    def constrain_size(width: int, height: int, x: int, y: int,
                       canvas_width: int, canvas_height: int,
                       min_width: int = 10, min_height: int = 10) -> Tuple[int, int]:
        """Constrain size to fit within canvas and meet minimum requirements"""
        max_width = canvas_width - x
        max_height = canvas_height - y

        constrained_width = max(min_width, min(width, max_width))
        constrained_height = max(min_height, min(height, max_height))

        return constrained_width, constrained_height


class ResizeHandles:
    """Utilities for resize handle detection and management"""

    HANDLE_SIZE = 8
    HANDLE_NAMES = [
        'top_left', 'top_right', 'bottom_left', 'bottom_right',
        'top', 'bottom', 'left', 'right'
    ]

    @staticmethod
    def get_handle_positions(x: int, y: int, width: int, height: int) -> dict:
        """Get positions of all resize handles"""
        handle_size = ResizeHandles.HANDLE_SIZE
        half_handle = handle_size // 2

        return {
            'top_left': (x - half_handle, y - half_handle),
            'top_right': (x + width - half_handle, y - half_handle),
            'bottom_left': (x - half_handle, y + height - half_handle),
            'bottom_right': (x + width - half_handle, y + height - half_handle),
            'top': (x + width // 2 - half_handle, y - half_handle),
            'bottom': (x + width // 2 - half_handle, y + height - half_handle),
            'left': (x - half_handle, y + height // 2 - half_handle),
            'right': (x + width - half_handle, y + height // 2 - half_handle)
        }

    @staticmethod
    def get_handle_at_position(pos_x: int, pos_y: int, field_x: int, field_y: int,
                               field_width: int, field_height: int) -> Optional[str]:
        """Determine which resize handle is at the given position"""
        handle_positions = ResizeHandles.get_handle_positions(
            field_x, field_y, field_width, field_height
        )
        handle_size = ResizeHandles.HANDLE_SIZE

        for handle_name, (hx, hy) in handle_positions.items():
            if (hx <= pos_x <= hx + handle_size and
                    hy <= pos_y <= hy + handle_size):
                return handle_name

        return None

    @staticmethod
    def get_cursor_for_handle(handle_name: str) -> Qt.CursorShape:
        """Get appropriate cursor for resize handle"""
        cursor_map = {
            'top_left': Qt.CursorShape.SizeFDiagCursor,
            'top_right': Qt.CursorShape.SizeBDiagCursor,
            'bottom_left': Qt.CursorShape.SizeBDiagCursor,
            'bottom_right': Qt.CursorShape.SizeFDiagCursor,
            'top': Qt.CursorShape.SizeVerCursor,
            'bottom': Qt.CursorShape.SizeVerCursor,
            'left': Qt.CursorShape.SizeHorCursor,
            'right': Qt.CursorShape.SizeHorCursor
        }
        return cursor_map.get(handle_name, Qt.CursorShape.ArrowCursor)


class ResizeCalculator:
    """Utilities for calculating new dimensions during resize operations"""

    @staticmethod
    def calculate_resize(start_x: int, start_y: int, start_width: int, start_height: int,
                         dx: int, dy: int, handle_name: str,
                         min_width: int = 20, min_height: int = 15) -> Tuple[int, int, int, int]:
        """
        Calculate new position and size during resize operation

        Returns: (new_x, new_y, new_width, new_height)
        """
        new_x, new_y = start_x, start_y
        new_width, new_height = start_width, start_height

        # Horizontal resize
        if 'left' in handle_name:
            new_x = start_x + dx
            new_width = start_width - dx
        elif 'right' in handle_name:
            new_width = start_width + dx

        # Vertical resize
        if 'top' in handle_name:
            new_y = start_y + dy
            new_height = start_height - dy
        elif 'bottom' in handle_name:
            new_height = start_height + dy

        # Apply minimum size constraints
        if new_width < min_width:
            if 'left' in handle_name:
                new_x = start_x + start_width - min_width
            new_width = min_width

        if new_height < min_height:
            if 'top' in handle_name:
                new_y = start_y + start_height - min_height
            new_height = min_height

        return new_x, new_y, new_width, new_height


class AlignmentUtils:
    """Utilities for field alignment operations"""

    @staticmethod
    def align_left(fields: list, reference_field) -> None:
        """Align fields to the left edge of reference field"""
        ref_x = reference_field.x
        for field in fields:
            if field != reference_field:
                field.x = ref_x

    @staticmethod
    def align_right(fields: list, reference_field) -> None:
        """Align fields to the right edge of reference field"""
        ref_right = reference_field.x + reference_field.width
        for field in fields:
            if field != reference_field:
                field.x = ref_right - field.width

    @staticmethod
    def align_top(fields: list, reference_field) -> None:
        """Align fields to the top edge of reference field"""
        ref_y = reference_field.y
        for field in fields:
            if field != reference_field:
                field.y = ref_y

    @staticmethod
    def align_bottom(fields: list, reference_field) -> None:
        """Align fields to the bottom edge of reference field"""
        ref_bottom = reference_field.y + reference_field.height
        for field in fields:
            if field != reference_field:
                field.y = ref_bottom - field.height

    @staticmethod
    def align_center_horizontal(fields: list, reference_field) -> None:
        """Align fields to horizontal center of reference field"""
        ref_center_x = reference_field.x + reference_field.width // 2
        for field in fields:
            if field != reference_field:
                field.x = ref_center_x - field.width // 2

    @staticmethod
    def align_center_vertical(fields: list, reference_field) -> None:
        """Align fields to vertical center of reference field"""
        ref_center_y = reference_field.y + reference_field.height // 2
        for field in fields:
            if field != reference_field:
                field.y = ref_center_y - field.height // 2


class DistributionUtils:
    """Utilities for distributing fields evenly"""

    @staticmethod
    def distribute_horizontal(fields: list, spacing: int = 10) -> None:
        """Distribute fields horizontally with equal spacing"""
        if len(fields) < 2:
            return

        # Sort fields by x position
        sorted_fields = sorted(fields, key=lambda f: f.x)

        # Calculate total width needed
        total_field_width = sum(field.width for field in sorted_fields)
        total_spacing = spacing * (len(sorted_fields) - 1)

        # Position fields
        current_x = sorted_fields[0].x
        for field in sorted_fields:
            field.x = current_x
            current_x += field.width + spacing

    @staticmethod
    def distribute_vertical(fields: list, spacing: int = 10) -> None:
        """Distribute fields vertically with equal spacing"""
        if len(fields) < 2:
            return

        # Sort fields by y position
        sorted_fields = sorted(fields, key=lambda f: f.y)

        # Position fields
        current_y = sorted_fields[0].y
        for field in sorted_fields:
            field.y = current_y
            current_y += field.height + spacing