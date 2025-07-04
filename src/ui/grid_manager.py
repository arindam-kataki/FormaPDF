#!/usr/bin/env python3
"""
Enhanced Grid Manager - Complete grid functionality with show/hide and color selection
Integrates with existing GridControlPopup and PDF Canvas architecture
"""

from PyQt6.QtWidgets import QColorDialog
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import json


@dataclass
class GridSettings:
    """Data class for grid configuration"""
    visible: bool = False
    spacing: int = 20
    offset_x: int = 0
    offset_y: int = 0
    color: QColor = None
    opacity: float = 0.7
    snap_enabled: bool = False
    sync_with_zoom: bool = False

    def __post_init__(self):
        if self.color is None:
            self.color = QColor(128, 128, 128, 180)  # Default gray with transparency

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'visible': self.visible,
            'spacing': self.spacing,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'color': self.color.getRgb(),
            'opacity': self.opacity,
            'snap_enabled': self.snap_enabled,
            'sync_with_zoom': self.sync_with_zoom
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GridSettings':
        """Create from dictionary"""
        settings = cls()
        settings.visible = data.get('visible', False)
        settings.spacing = data.get('spacing', 20)
        settings.offset_x = data.get('offset_x', 0)
        settings.offset_y = data.get('offset_y', 0)
        settings.opacity = data.get('opacity', 0.7)
        settings.snap_enabled = data.get('snap_enabled', False),
        settings.sync_with_zoom=data.get('sync_with_zoom', False)

        # Handle color
        color_rgba = data.get('color', (128, 128, 128, 180))
        if isinstance(color_rgba, (list, tuple)) and len(color_rgba) >= 3:
            settings.color = QColor(*color_rgba[:4])
        else:
            settings.color = QColor(128, 128, 128, 180)

        return settings


class GridManager(QObject):
    """
    Enhanced Grid Manager - Centralized grid functionality

    Features:
    - Show/Hide grid with visual feedback
    - Customizable grid color with alpha channel
    - Grid spacing and offset controls
    - Snap-to-grid functionality
    - Settings persistence
    - Integration with existing popup and canvas
    """

    # Signals
    grid_changed = pyqtSignal(GridSettings)  # Emitted when any grid setting changes
    grid_visibility_changed = pyqtSignal(bool)
    grid_color_changed = pyqtSignal(QColor)
    grid_spacing_changed = pyqtSignal(int)
    grid_offset_changed = pyqtSignal(int, int)
    snap_changed = pyqtSignal(bool)
    sync_with_zoom_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Grid settings
        self.settings = GridSettings()

        # Color presets for quick selection
        self.color_presets = [
            QColor(128, 128, 128, 180),  # Default gray
            QColor(200, 200, 200, 150),  # Light gray
            QColor(100, 100, 100, 200),  # Dark gray
            QColor(0, 100, 200, 160),  # Blue
            QColor(200, 100, 0, 160),  # Orange
            QColor(100, 200, 0, 160),  # Green
            QColor(200, 0, 100, 160),  # Pink
            QColor(150, 0, 150, 160),  # Purple
        ]

        # Update timer for performance
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._emit_grid_changed)

    # =========================
    # CORE GRID FUNCTIONALITY
    # =========================

    def show_grid(self) -> None:
        """Show the grid"""
        if not self.settings.visible:
            self.settings.visible = True
            self.grid_visibility_changed.emit(True)
            self._schedule_update()
            print("📐 Grid shown")

    def hide_grid(self) -> None:
        """Hide the grid"""
        if self.settings.visible:
            self.settings.visible = False
            self.grid_visibility_changed.emit(False)
            self._schedule_update()
            print("📐 Grid hidden")

    def toggle_grid(self) -> bool:
        """Toggle grid visibility and return new state"""
        if self.settings.visible:
            self.hide_grid()
        else:
            self.show_grid()
        return self.settings.visible

    def is_grid_visible(self) -> bool:
        """Check if grid is currently visible"""
        return self.settings.visible

    # =========================
    # COLOR MANAGEMENT
    # =========================

    def set_grid_color(self, color: QColor) -> None:
        """Set grid color with validation"""
        if color.isValid() and color != self.settings.color:
            self.settings.color = color
            self.grid_color_changed.emit(color)
            self._schedule_update()
            print(f"📐 Grid color changed to: {color.name()} (alpha: {color.alpha()})")

    def get_grid_color(self) -> QColor:
        """Get current grid color"""
        return self.settings.color

    def show_color_picker(self, parent=None) -> bool:
        """Show color picker dialog and update grid color"""
        color = QColorDialog.getColor(
            self.settings.color,
            parent,
            "Select Grid Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )

        if color.isValid():
            self.set_grid_color(color)
            return True
        return False

    def set_color_from_preset(self, preset_index: int) -> None:
        """Set color from preset list"""
        if 0 <= preset_index < len(self.color_presets):
            self.set_grid_color(self.color_presets[preset_index])

    def get_color_presets(self) -> list[QColor]:
        """Get list of color presets"""
        return self.color_presets.copy()

    # =========================
    # GRID PROPERTIES
    # =========================

    def set_spacing(self, spacing: int) -> None:
        """Set grid spacing (5-100 pixels)"""
        spacing = max(5, min(spacing, 100))
        if spacing != self.settings.spacing:
            self.settings.spacing = spacing
            self.grid_spacing_changed.emit(spacing)
            self._schedule_update()
            print(f"📐 Grid spacing: {spacing}px")

    def get_spacing(self) -> int:
        """Get current grid spacing"""
        return self.settings.spacing

    def set_offset(self, x: int, y: int) -> None:
        """Set grid offset"""
        x = max(-50, min(x, 50))
        y = max(-50, min(y, 50))

        if x != self.settings.offset_x or y != self.settings.offset_y:
            self.settings.offset_x = x
            self.settings.offset_y = y
            self.grid_offset_changed.emit(x, y)
            self._schedule_update()
            print(f"📐 Grid offset: ({x}, {y})")

    def get_offset(self) -> Tuple[int, int]:
        """Get current grid offset"""
        return (self.settings.offset_x, self.settings.offset_y)

    def set_opacity(self, opacity: float) -> None:
        """Set grid opacity (0.0 - 1.0)"""
        opacity = max(0.0, min(opacity, 1.0))
        if abs(opacity - self.settings.opacity) > 0.01:
            self.settings.opacity = opacity
            # Update color alpha based on opacity
            color = self.settings.color
            color.setAlphaF(opacity)
            self.set_grid_color(color)

    def get_opacity(self) -> float:
        """Get current grid opacity"""
        return self.settings.opacity

    # =========================
    # SNAP TO GRID
    # =========================

    def enable_snap(self) -> None:
        """Enable snap to grid"""
        if not self.settings.snap_enabled:
            self.settings.snap_enabled = True
            self.snap_changed.emit(True)
            print("🧲 Snap to grid enabled")

    def disable_snap(self) -> None:
        """Disable snap to grid"""
        if self.settings.snap_enabled:
            self.settings.snap_enabled = False
            self.snap_changed.emit(False)
            print("🧲 Snap to grid disabled")

    def toggle_snap(self) -> bool:
        """Toggle snap to grid and return new state"""
        if self.settings.snap_enabled:
            self.disable_snap()
        else:
            self.enable_snap()
        return self.settings.snap_enabled

    def is_snap_enabled(self) -> bool:
        """Check if snap to grid is enabled"""
        return self.settings.snap_enabled

    def snap_point_to_grid(self, x: float, y: float, zoom_level: float = 1.0, max_snap_distance: float = 25.0) -> Tuple[
        float, float]:
        """
        Snap a point to the nearest grid intersection with proper zoom handling

        Args:
            x, y: Point coordinates to snap (in screen/canvas coordinates)
            zoom_level: Current zoom level
            max_snap_distance: Maximum distance to snap (in pixels)

        Returns:
            Snapped coordinates or original if too far
        """
        if not self.settings.snap_enabled or not self.settings.visible:
            return (x, y)

        # 🎯 KEY FIX: Only scale with zoom if sync_with_zoom is enabled
        if self.settings.sync_with_zoom:
            # Grid scales with zoom - use scaled values
            effective_spacing = self.settings.spacing * zoom_level
            effective_offset_x = self.settings.offset_x * zoom_level
            effective_offset_y = self.settings.offset_y * zoom_level
            snap_mode = "ZOOM-SCALED"
        else:
            # Grid is fixed pixel size - ignore zoom level
            effective_spacing = self.settings.spacing
            effective_offset_x = self.settings.offset_x
            effective_offset_y = self.settings.offset_y
            snap_mode = "FIXED-PIXEL"

        # Calculate potential snapped coordinates
        snapped_x = round((x - effective_offset_x) / effective_spacing) * effective_spacing + effective_offset_x
        snapped_y = round((y - effective_offset_y) / effective_spacing) * effective_spacing + effective_offset_y

        # Calculate snap distances
        distance_x = abs(snapped_x - x)
        distance_y = abs(snapped_y - y)
        total_distance = (distance_x ** 2 + distance_y ** 2) ** 0.5

        # Only snap if within threshold
        if total_distance <= max_snap_distance:
            print(
                f"🧲 {snap_mode} SNAP: ({x:.1f}, {y:.1f}) → ({snapped_x:.1f}, {snapped_y:.1f}) [distance: {total_distance:.1f}px, spacing: {effective_spacing:.1f}px]")
            return (snapped_x, snapped_y)
        else:
            print(f"🚫 NO SNAP: Distance {total_distance:.1f}px exceeds threshold {max_snap_distance}px")
            return (x, y)

    # =========================
    # ZOOM
    # =========================

    def set_sync_with_zoom(self, sync_enabled: bool) -> None:
        """Set whether grid should sync with zoom level"""
        if self.settings.sync_with_zoom != sync_enabled:
            self.settings.sync_with_zoom = sync_enabled
            self.sync_with_zoom_changed.emit(sync_enabled)
            self.grid_changed.emit(self.settings)
            print(f"📐 Grid zoom sync: {'enabled' if sync_enabled else 'disabled'}")

    # =========================
    # DRAWING
    # =========================

    def draw_grid(self, painter: QPainter, width: int, height: int, zoom_level: float = 1.0) -> None:
        """Draw grid on the given painter"""
        if not self.settings.visible:
            return

        # Create pen with current color and opacity
        pen = QPen(self.settings.color)
        pen.setWidth(1)
        painter.setPen(pen)

        # Apply zoom scaling only if sync_with_zoom is enabled
        if self.settings.sync_with_zoom:
            scaled_spacing = int(self.settings.spacing * zoom_level)
            scaled_offset_x = int(self.settings.offset_x * zoom_level)
            scaled_offset_y = int(self.settings.offset_y * zoom_level)
        else:
            # Use original values for fixed pixel grid
            scaled_spacing = self.settings.spacing
            scaled_offset_x = self.settings.offset_x
            scaled_offset_y = self.settings.offset_y

        # Skip if grid would be too dense
        if scaled_spacing < 2:
            return

        # Draw vertical lines
        start_x = scaled_offset_x % scaled_spacing
        for x in range(start_x, width, scaled_spacing):
            painter.drawLine(x, 0, x, height)

        # Draw horizontal lines
        start_y = scaled_offset_y % scaled_spacing
        for y in range(start_y, height, scaled_spacing):
            painter.drawLine(0, y, width, y)

    # =========================
    # PRESET MANAGEMENT
    # =========================

    def reset_to_defaults(self) -> None:
        """Reset all grid settings to defaults"""
        self.settings = GridSettings()
        self._emit_all_signals()
        print("📐 Grid settings reset to defaults")

    def apply_quick_preset(self, preset_name: str) -> None:
        """Apply a quick preset configuration"""
        presets = {
            'fine': GridSettings(visible=True, spacing=10, color=QColor(150, 150, 150, 120)),
            'normal': GridSettings(visible=True, spacing=20, color=QColor(128, 128, 128, 180)),
            'coarse': GridSettings(visible=True, spacing=40, color=QColor(100, 100, 100, 200)),
            'blueprint': GridSettings(visible=True, spacing=25, color=QColor(0, 100, 200, 150)),
            'design': GridSettings(visible=True, spacing=15, color=QColor(200, 100, 0, 140)),
        }

        if preset_name in presets:
            self.settings = presets[preset_name]
            self._emit_all_signals()
            print(f"📐 Applied '{preset_name}' preset")

    # =========================
    # SETTINGS PERSISTENCE
    # =========================

    def save_settings(self, filepath: str) -> bool:
        """Save grid settings to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            print(f"💾 Grid settings saved to {filepath}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to save grid settings: {e}")
            return False

    def load_settings(self, filepath: str) -> bool:
        """Load grid settings from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.settings = GridSettings.from_dict(data)
            self._emit_all_signals()
            print(f"📂 Grid settings loaded from {filepath}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to load grid settings: {e}")
            return False

    def get_settings(self) -> GridSettings:
        """Get current grid settings (copy)"""
        return GridSettings(
            visible=self.settings.visible,
            spacing=self.settings.spacing,
            offset_x=self.settings.offset_x,
            offset_y=self.settings.offset_y,
            color=QColor(self.settings.color),
            opacity=self.settings.opacity,
            snap_enabled=self.settings.snap_enabled
        )

    def set_settings(self, settings: GridSettings) -> None:
        """Set grid settings from GridSettings object"""
        self.settings = GridSettings(
            visible=settings.visible,
            spacing=settings.spacing,
            offset_x=settings.offset_x,
            offset_y=settings.offset_y,
            color=QColor(settings.color),
            opacity=settings.opacity,
            snap_enabled=settings.snap_enabled
        )
        self._emit_all_signals()

    # =========================
    # INTEGRATION METHODS
    # =========================

    def connect_to_popup(self, popup) -> None:
        """Connect to existing GridControlPopup"""
        if hasattr(popup, 'grid_visibility_changed'):
            popup.grid_visibility_changed.connect(lambda visible: setattr(self.settings, 'visible', visible))
        if hasattr(popup, 'grid_color_changed'):
            popup.grid_color_changed.connect(self.set_grid_color)
        if hasattr(popup, 'grid_spacing_changed'):
            popup.grid_spacing_changed.connect(self.set_spacing)
        if hasattr(popup, 'grid_offset_changed'):
            popup.grid_offset_changed.connect(self.set_offset)
        if hasattr(popup, 'snap_to_grid_changed'):
            # ✅ CORRECT: Use the proper enable/disable methods that emit signals
            popup.snap_to_grid_changed.connect(self._on_popup_snap_changed)

        print("🔗 Connected to GridControlPopup")

    def _on_popup_snap_changed(self, enabled: bool):
        """Handle snap change from popup - use proper methods that emit signals"""
        if enabled:
            self.enable_snap()  # This emits snap_changed signal
        else:
            self.disable_snap()  # This emits snap_changed signal

    def connect_to_canvas(self, canvas) -> None:
        """Connect to PDF canvas for drawing"""
        # Connect our signals to canvas methods
        self.grid_changed.connect(lambda settings: self._update_canvas(canvas, settings))
        print("🔗 Connected to PDF Canvas")

    def _update_canvas(self, canvas, settings: GridSettings) -> None:
        """Update canvas with new grid settings"""
        if hasattr(canvas, 'set_grid_visible'):
            canvas.set_grid_visible(settings.visible)
        elif hasattr(canvas, 'show_grid'):
            canvas.show_grid = settings.visible

        if hasattr(canvas, 'set_grid_color'):
            canvas.set_grid_color(settings.color)
        elif hasattr(canvas, 'grid_color'):
            canvas.grid_color = settings.color

        if hasattr(canvas, 'set_grid_spacing'):
            canvas.set_grid_spacing(settings.spacing)
        elif hasattr(canvas, 'grid_size'):
            canvas.grid_size = settings.spacing

        if hasattr(canvas, 'set_grid_offset'):
            canvas.set_grid_offset(settings.offset_x, settings.offset_y)
        else:
            if hasattr(canvas, 'grid_offset_x'):
                canvas.grid_offset_x = settings.offset_x
            if hasattr(canvas, 'grid_offset_y'):
                canvas.grid_offset_y = settings.offset_y

        # Force canvas to redraw
        if hasattr(canvas, 'draw_overlay'):
            canvas.draw_overlay()
        elif hasattr(canvas, 'update'):
            canvas.update()

        print(f"📐 Canvas updated: visible={settings.visible}, spacing={settings.spacing}")

    # =========================
    # PRIVATE METHODS
    # =========================

    def _schedule_update(self) -> None:
        """Schedule a delayed update to avoid too many signals"""
        self.update_timer.start(50)  # 50ms delay

    def _emit_grid_changed(self) -> None:
        """Emit the main grid changed signal"""
        self.grid_changed.emit(self.settings)

    def _emit_all_signals(self) -> None:
        """Emit all individual signals (used when loading settings)"""
        self.grid_visibility_changed.emit(self.settings.visible)
        self.grid_color_changed.emit(self.settings.color)
        self.grid_spacing_changed.emit(self.settings.spacing)
        self.grid_offset_changed.emit(self.settings.offset_x, self.settings.offset_y)
        self.snap_changed.emit(self.settings.snap_enabled)
        self.sync_with_zoom_changed.emit(self.settings.sync_with_zoom)  # ADD THIS LINE
        self._emit_grid_changed()


# =======================================
# ADVANCED USAGE
# =======================================

    def draw_grid(self, painter: QPainter, width: int, height: int, zoom_level: float = 1.0,
                  canvas=None, viewport_rect=None) -> None:
        """
        Draw grid with optional page boundary and viewport support

        Args:
            painter: QPainter object for drawing
            width: Canvas width (fallback if no page boundaries)
            height: Canvas height (fallback if no page boundaries)
            zoom_level: Current zoom level
            canvas: Optional canvas object with page information
            viewport_rect: Optional viewport rectangle for optimization
        """
        if not self.settings.visible:
            return

        # Create pen with current color and opacity
        pen = QPen(self.settings.color)
        pen.setWidth(1)
        painter.setPen(pen)

        # Calculate effective spacing and offsets based on zoom settings
        if self.settings.sync_with_zoom:
            effective_spacing = int(self.settings.spacing * zoom_level)
            effective_offset_x = int(self.settings.offset_x * zoom_level)
            effective_offset_y = int(self.settings.offset_y * zoom_level)
            snap_mode = "ZOOM-SCALED"
        else:
            effective_spacing = self.settings.spacing
            effective_offset_x = self.settings.offset_x
            effective_offset_y = self.settings.offset_y
            snap_mode = "FIXED-PIXEL"

        # Skip if grid would be too dense
        if effective_spacing < 2:
            return

        # Choose drawing method based on available information
        if canvas and hasattr(canvas, 'page_positions') and canvas.page_positions:
            # Enhanced page-bounded drawing
            self._draw_page_bounded_grid(painter, canvas, zoom_level, effective_spacing,
                                         effective_offset_x, effective_offset_y, viewport_rect)
        else:
            # Fallback to full canvas drawing
            self._draw_full_canvas_grid(painter, width, height, effective_spacing,
                                        effective_offset_x, effective_offset_y)

    def _draw_page_bounded_grid(self, painter: QPainter, canvas, zoom_level: float,
                                effective_spacing: int, effective_offset_x: int, effective_offset_y: int,
                                viewport_rect=None):
        """Draw grid limited to page boundaries with optional viewport optimization"""

        if not hasattr(canvas, 'pdf_document') or not canvas.pdf_document:
            print("🚫 No PDF document available for page-bounded grid")
            return

        pages_drawn = 0
        total_lines = 0

        # Determine drawing bounds (viewport or full canvas)
        if viewport_rect:
            draw_left = viewport_rect.left()
            draw_right = viewport_rect.right()
            draw_top = viewport_rect.top()
            draw_bottom = viewport_rect.bottom()
            print(f"🎯 Drawing grid in viewport: {viewport_rect}")
        else:
            draw_left = 0
            draw_right = getattr(canvas, 'width', lambda: 2000)()
            draw_top = 0
            draw_bottom = getattr(canvas, 'height', lambda: 2000)()
            print(f"🎯 Drawing grid for full canvas: {draw_right}x{draw_bottom}")

        # Process each page
        for page_num, page_top in enumerate(canvas.page_positions):
            if page_num >= len(canvas.pdf_document):
                continue

            # Quick viewport culling
            if viewport_rect and page_top > draw_bottom:
                break  # All subsequent pages are below viewport

            # Get page dimensions
            page = canvas.pdf_document[page_num]
            page_width = int(page.rect.width * zoom_level)
            page_height = int(page.rect.height * zoom_level)

            # Page boundaries in screen coordinates
            page_left = getattr(canvas, 'page_margin_left', 10)  # Standard margin
            page_right = page_left + page_width
            page_bottom = page_top + page_height

            # Skip if page doesn't intersect with drawing bounds
            if (page_bottom < draw_top or page_top > draw_bottom or
                    page_right < draw_left or page_left > draw_right):
                continue

            pages_drawn += 1

            # Calculate intersection of page and drawing bounds
            clip_left = max(page_left, draw_left)
            clip_right = min(page_right, draw_right)
            clip_top = max(page_top, draw_top)
            clip_bottom = min(page_bottom, draw_bottom)

            # Calculate grid start positions for this page
            # Grid starts from page top-left corner, then apply offset
            grid_origin_x = page_left + (effective_offset_x % effective_spacing)
            grid_origin_y = page_top + (effective_offset_y % effective_spacing)

            # Draw vertical lines for this page
            first_x = grid_origin_x
            if clip_left > grid_origin_x:
                # Optimize: jump to first visible line
                lines_to_skip = (clip_left - grid_origin_x) // effective_spacing
                first_x = grid_origin_x + (lines_to_skip * effective_spacing)

            x = first_x
            while x <= clip_right:
                if x >= clip_left:
                    painter.drawLine(x, clip_top, x, clip_bottom)
                    total_lines += 1
                x += effective_spacing

            # Draw horizontal lines for this page
            first_y = grid_origin_y
            if clip_top > grid_origin_y:
                # Optimize: jump to first visible line
                lines_to_skip = (clip_top - grid_origin_y) // effective_spacing
                first_y = grid_origin_y + (lines_to_skip * effective_spacing)

            y = first_y
            while y <= clip_bottom:
                if y >= clip_top:
                    painter.drawLine(clip_left, y, clip_right, y)
                    total_lines += 1
                y += effective_spacing

        print(f"🎯 Drew {total_lines} grid lines across {pages_drawn} pages at {zoom_level:.1f}x zoom")

    def _draw_full_canvas_grid(self, painter: QPainter, width: int, height: int,
                               effective_spacing: int, effective_offset_x: int, effective_offset_y: int):
        """Fallback method: draw grid across entire canvas"""

        total_lines = 0

        # Draw vertical lines
        start_x = effective_offset_x % effective_spacing
        for x in range(start_x, width, effective_spacing):
            painter.drawLine(x, 0, x, height)
            total_lines += 1

        # Draw horizontal lines
        start_y = effective_offset_y % effective_spacing
        for y in range(start_y, height, effective_spacing):
            painter.drawLine(0, y, width, y)
            total_lines += 1

        print(f"🎯 Drew {total_lines} grid lines (full canvas fallback)")

    # Additional helper method for zoom-aware density control
    def _should_draw_grid_at_zoom(self, zoom_level: float) -> bool:
        """Determine if grid should be drawn at current zoom level"""
        if zoom_level < 0.2:
            return False  # Too zoomed out, grid would be too dense
        elif zoom_level > 5.0:
            return True  # Very zoomed in, always show grid
        else:
            # Scale grid density based on zoom
            min_spacing = 3  # Minimum 3 pixels between lines
            effective_spacing = self.settings.spacing * zoom_level if self.settings.sync_with_zoom else self.settings.spacing
            return effective_spacing >= min_spacing

    # Enhanced method with zoom density control
    def draw_grid_with_density_control(self, painter: QPainter, width: int, height: int,
                                       zoom_level: float = 1.0, canvas=None, viewport_rect=None) -> None:
        """Enhanced draw_grid with automatic density control"""

        if not self.settings.visible or not self._should_draw_grid_at_zoom(zoom_level):
            return

        # Apply zoom-based spacing adjustments
        adjusted_spacing = self.settings.spacing
        adjusted_offset_x = self.settings.offset_x
        adjusted_offset_y = self.settings.offset_y

        if zoom_level > 3.0:
            # At high zoom, double the spacing to avoid visual clutter
            adjusted_spacing *= 2
            adjusted_offset_x *= 2
            adjusted_offset_y *= 2
            print(f"🎯 High zoom detected ({zoom_level:.1f}x), doubled grid spacing to {adjusted_spacing}px")

        # Temporarily modify settings for this draw call
        original_spacing = self.settings.spacing
        original_offset_x = self.settings.offset_x
        original_offset_y = self.settings.offset_y

        self.settings.spacing = adjusted_spacing
        self.settings.offset_x = adjusted_offset_x
        self.settings.offset_y = adjusted_offset_y

        try:
            # Call the main draw method
            self.draw_grid(painter, width, height, zoom_level, canvas, viewport_rect)
        finally:
            # Restore original settings
            self.settings.spacing = original_spacing
            self.settings.offset_x = original_offset_x
            self.settings.offset_y = original_offset_y

# =========================
# USAGE EXAMPLE
# =========================

def example_usage():
    """Example of how to use the GridManager"""
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Create grid manager
    grid_manager = GridManager()

    # Connect signals for demo
    grid_manager.grid_visibility_changed.connect(
        lambda visible: print(f"Grid visibility: {visible}")
    )
    grid_manager.grid_color_changed.connect(
        lambda color: print(f"Grid color: {color.name()}")
    )
    grid_manager.grid_spacing_changed.connect(
        lambda spacing: print(f"Grid spacing: {spacing}px")
    )

    # Demo operations
    print("=== Grid Manager Demo ===")

    # Show grid
    grid_manager.show_grid()

    # Change color
    grid_manager.set_grid_color(QColor(0, 100, 200, 150))

    # Change spacing
    grid_manager.set_spacing(30)

    # Set offset
    grid_manager.set_offset(5, -3)

    # Enable snap
    grid_manager.enable_snap()

    # Test snap functionality
    snapped = grid_manager.snap_point_to_grid(47.3, 83.7)
    print(f"Point (47.3, 83.7) snapped to {snapped}")

    # Apply preset
    grid_manager.apply_quick_preset('blueprint')

    # Save settings
    grid_manager.save_settings('grid_settings.json')

    print("Demo completed!")


if __name__ == "__main__":
    example_usage()