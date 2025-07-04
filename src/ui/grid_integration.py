#!/usr/bin/env python3
"""
Grid Integration Module - Connects GridManager with existing GridControlPopup and PDF Canvas
Provides seamless integration without breaking existing functionality
"""

from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtGui import QColor
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grid_manager import GridManager
    from src.ui.grid_control_popup import GridControlPopup
    from src.ui.pdf_canvas import PDFCanvas
    from src.ui.toolbar_manager import ToolbarManager


class GridIntegrator(QObject):
    """
    Integration layer between GridManager and existing components

    This class acts as a bridge to connect the new GridManager with:
    - GridControlPopup (UI controls)
    - PDFCanvas (drawing/rendering)
    - ToolbarManager (toolbar actions)

    It ensures bidirectional communication while maintaining existing functionality.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Component references
        self.grid_manager: Optional['GridManager'] = None
        self.grid_popup: Optional['GridControlPopup'] = None
        self.pdf_canvas: Optional['PDFCanvas'] = None
        self.toolbar_manager: Optional['ToolbarManager'] = None

        # Integration state
        self.connections_established = False
        self.sync_in_progress = False

    # =========================
    # COMPONENT REGISTRATION
    # =========================

    def set_grid_manager(self, grid_manager: 'GridManager') -> None:
        """Register the GridManager"""
        self.grid_manager = grid_manager
        self._connect_grid_manager()
        print("🔗 GridManager registered with integrator")

    def set_grid_popup(self, grid_popup: 'GridControlPopup') -> None:
        """Register the GridControlPopup"""
        self.grid_popup = grid_popup
        self._connect_grid_popup()
        print("🔗 GridControlPopup registered with integrator")

    def set_pdf_canvas(self, pdf_canvas: 'PDFCanvas') -> None:
        """Register the PDFCanvas"""
        self.pdf_canvas = pdf_canvas
        self._connect_pdf_canvas()
        print("🔗 PDFCanvas registered with integrator")

    def set_toolbar_manager(self, toolbar_manager: 'ToolbarManager') -> None:
        """Register the ToolbarManager"""
        self.toolbar_manager = toolbar_manager
        self._connect_toolbar_manager()
        print("🔗 ToolbarManager registered with integrator")

    # =========================
    # CONNECTION SETUP
    # =========================

    def _connect_grid_manager(self) -> None:
        """Connect GridManager signals"""
        if not self.grid_manager:
            return

        # Connect GridManager signals to update other components
        self.grid_manager.grid_visibility_changed.connect(self._on_manager_visibility_changed)
        self.grid_manager.grid_color_changed.connect(self._on_manager_color_changed)
        self.grid_manager.grid_spacing_changed.connect(self._on_manager_spacing_changed)
        self.grid_manager.grid_offset_changed.connect(self._on_manager_offset_changed)
        self.grid_manager.snap_changed.connect(self._on_manager_snap_changed)
        self.grid_manager.grid_changed.connect(self._on_manager_grid_changed)
        self.grid_manager.sync_with_zoom_changed.connect(self._on_manager_sync_zoom_changed)

    def _connect_grid_popup(self) -> None:
        """Connect GridControlPopup signals"""
        if not self.grid_popup:
            return

        # Connect popup signals to GridManager
        if hasattr(self.grid_popup, 'grid_visibility_changed'):
            self.grid_popup.grid_visibility_changed.connect(self._on_popup_visibility_changed)

        if hasattr(self.grid_popup, 'grid_color_changed'):
            self.grid_popup.grid_color_changed.connect(self._on_popup_color_changed)

        if hasattr(self.grid_popup, 'grid_spacing_changed'):
            self.grid_popup.grid_spacing_changed.connect(self._on_popup_spacing_changed)

        if hasattr(self.grid_popup, 'grid_offset_changed'):
            self.grid_popup.grid_offset_changed.connect(self._on_popup_offset_changed)

        if hasattr(self.grid_popup, 'snap_to_grid_changed'):
            self.grid_popup.snap_to_grid_changed.connect(self._on_popup_snap_changed)

        if hasattr(self.grid_popup, 'grid_reset_requested'):
            self.grid_popup.grid_reset_requested.connect(self._on_popup_reset_requested)

        if hasattr(self.grid_popup, 'sync_with_zoom_changed'):
            self.grid_popup.sync_with_zoom_changed.connect(self._on_popup_sync_zoom_changed)

    def _connect_pdf_canvas(self) -> None:
        """Connect PDFCanvas integration"""
        if not self.pdf_canvas:
            return

        # Override or enhance existing grid drawing methods
        self._enhance_canvas_grid_methods()

    def _connect_toolbar_manager(self) -> None:
        """Connect ToolbarManager integration"""
        if not self.toolbar_manager:
            return

        # Connect toolbar grid actions to GridManager
        if hasattr(self.toolbar_manager, 'toggle_grid_action'):
            # Connect toolbar toggle to our grid manager
            pass  # Will be implemented based on specific toolbar structure

    # =========================
    # GRIDMANAGER EVENT HANDLERS
    # =========================

    @pyqtSlot(bool)
    def _on_manager_visibility_changed(self, visible: bool) -> None:
        """Handle visibility change from GridManager"""
        if self.sync_in_progress:
            return

        self.sync_in_progress = True
        try:
            # Update popup UI
            if self.grid_popup and hasattr(self.grid_popup, 'grid_checkbox'):
                self.grid_popup.grid_checkbox.setChecked(visible)

            # Update canvas
            if self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'set_grid_visible'):
                    self.pdf_canvas.set_grid_visible(visible)
                elif hasattr(self.pdf_canvas, 'show_grid'):
                    self.pdf_canvas.show_grid = visible
                    if hasattr(self.pdf_canvas, 'update'):
                        self.pdf_canvas.update()

            # Update toolbar
            if self.toolbar_manager:
                if hasattr(self.toolbar_manager, 'grid_visible'):
                    self.toolbar_manager.grid_visible = visible
                if hasattr(self.toolbar_manager, 'grid_action'):
                    self.toolbar_manager.grid_action.setChecked(visible)

            print(f"📐 Synced visibility to components: {visible}")

        finally:
            self.sync_in_progress = False

    @pyqtSlot(QColor)
    def _on_manager_color_changed(self, color: QColor) -> None:
        """Handle color change from GridManager"""
        if self.sync_in_progress:
            return

        self.sync_in_progress = True
        try:
            # Update popup UI
            if self.grid_popup and hasattr(self.grid_popup, 'grid_color'):
                self.grid_popup.grid_color = color
                if hasattr(self.grid_popup, 'update_color_button'):
                    self.grid_popup.update_color_button()

            # Update canvas
            if self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'set_grid_color'):
                    self.pdf_canvas.set_grid_color(color)
                elif hasattr(self.pdf_canvas, 'grid_color'):
                    self.pdf_canvas.grid_color = color
                    if hasattr(self.pdf_canvas, 'update'):
                        self.pdf_canvas.update()

            print(f"📐 Synced color to components: {color.name()}")

        finally:
            self.sync_in_progress = False

    @pyqtSlot(bool)
    def _on_manager_sync_zoom_changed(self, sync_enabled: bool) -> None:
        """Handle sync with zoom change from GridManager"""
        if self.sync_in_progress:
            return

        self.sync_in_progress = True

        # Update popup
        if self.grid_popup and hasattr(self.grid_popup, 'update_sync_with_zoom'):
            self.grid_popup.update_sync_with_zoom(sync_enabled)

        # Update toolbar if it has sync controls
        if self.toolbar_manager and hasattr(self.toolbar_manager, 'update_sync_with_zoom'):
            self.toolbar_manager.update_sync_with_zoom(sync_enabled)

        self.sync_in_progress = False

    @pyqtSlot(bool)
    def _on_popup_sync_zoom_changed(self, sync_enabled: bool) -> None:
        """Handle sync with zoom change from popup"""
        if self.sync_in_progress or not self.grid_manager:
            return

        self.grid_manager.set_sync_with_zoom(sync_enabled)

    @pyqtSlot(int)
    def _on_manager_spacing_changed(self, spacing: int) -> None:
        """Handle spacing change from GridManager"""
        if self.sync_in_progress:
            return

        self.sync_in_progress = True
        try:
            # Update popup UI
            if self.grid_popup and hasattr(self.grid_popup, 'spacing_spinbox'):
                self.grid_popup.spacing_spinbox.setValue(spacing)

            # Update canvas
            if self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'set_grid_spacing'):
                    self.pdf_canvas.set_grid_spacing(spacing)
                elif hasattr(self.pdf_canvas, 'grid_spacing'):
                    self.pdf_canvas.grid_spacing = spacing
                elif hasattr(self.pdf_canvas, 'grid_size'):
                    self.pdf_canvas.grid_size = spacing

                if hasattr(self.pdf_canvas, 'update'):
                    self.pdf_canvas.update()

            # Update toolbar
            if self.toolbar_manager and hasattr(self.toolbar_manager, 'grid_spacing'):
                self.toolbar_manager.grid_spacing = spacing

            print(f"📐 Synced spacing to components: {spacing}px")

        finally:
            self.sync_in_progress = False

    @pyqtSlot(int, int)
    def _on_manager_offset_changed(self, offset_x: int, offset_y: int) -> None:
        """Handle offset change from GridManager"""
        if self.sync_in_progress:
            return

        self.sync_in_progress = True
        try:
            # Update popup UI
            if self.grid_popup:
                if hasattr(self.grid_popup, 'offset_x_spinbox'):
                    self.grid_popup.offset_x_spinbox.setValue(offset_x)
                if hasattr(self.grid_popup, 'offset_y_spinbox'):
                    self.grid_popup.offset_y_spinbox.setValue(offset_y)

            # Update canvas
            if self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'set_grid_offset'):
                    self.pdf_canvas.set_grid_offset(offset_x, offset_y)
                else:
                    if hasattr(self.pdf_canvas, 'grid_offset_x'):
                        self.pdf_canvas.grid_offset_x = offset_x
                    if hasattr(self.pdf_canvas, 'grid_offset_y'):
                        self.pdf_canvas.grid_offset_y = offset_y

                if hasattr(self.pdf_canvas, 'update'):
                    self.pdf_canvas.update()

            # Update toolbar
            if self.toolbar_manager:
                if hasattr(self.toolbar_manager, 'grid_offset_x'):
                    self.toolbar_manager.grid_offset_x = offset_x
                if hasattr(self.toolbar_manager, 'grid_offset_y'):
                    self.toolbar_manager.grid_offset_y = offset_y

            print(f"📐 Synced offset to components: ({offset_x}, {offset_y})")

        finally:
            self.sync_in_progress = False

    @pyqtSlot(bool)
    def _on_manager_snap_changed(self, snap_enabled: bool) -> None:
        """Handle snap change from GridManager"""
        if self.sync_in_progress:
            return

        self.sync_in_progress = True
        try:
            # Update popup UI
            if self.grid_popup and hasattr(self.grid_popup, 'snap_checkbox'):
                self.grid_popup.snap_checkbox.setChecked(snap_enabled)

            # Update canvas snap functionality
            if self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'set_snap_enabled'):
                    self.pdf_canvas.set_snap_enabled(snap_enabled)
                elif hasattr(self.pdf_canvas, 'snap_enabled'):
                    self.pdf_canvas.snap_enabled = snap_enabled

            print(f"📐 Synced snap to components: {snap_enabled}")

        finally:
            self.sync_in_progress = False

    @pyqtSlot(object)
    def _on_manager_grid_changed(self, settings) -> None:
        """Handle complete grid settings change from GridManager"""
        if self.sync_in_progress:
            return

        print("📐 Complete grid settings updated across all components")

    # =========================
    # POPUP EVENT HANDLERS
    # =========================

    @pyqtSlot(bool)
    def _on_popup_visibility_changed(self, visible: bool) -> None:
        """Handle visibility change from popup"""
        if self.sync_in_progress or not self.grid_manager:
            return

        if visible:
            self.grid_manager.show_grid()
        else:
            self.grid_manager.hide_grid()

    @pyqtSlot(QColor)
    def _on_popup_color_changed(self, color: QColor) -> None:
        """Handle color change from popup"""
        if self.sync_in_progress or not self.grid_manager:
            return

        self.grid_manager.set_grid_color(color)

    @pyqtSlot(int)
    def _on_popup_spacing_changed(self, spacing: int) -> None:
        """Handle spacing change from popup"""
        if self.sync_in_progress or not self.grid_manager:
            return

        self.grid_manager.set_spacing(spacing)

    @pyqtSlot(int, int)
    def _on_popup_offset_changed(self, offset_x: int, offset_y: int) -> None:
        """Handle offset change from popup"""
        if self.sync_in_progress or not self.grid_manager:
            return

        self.grid_manager.set_offset(offset_x, offset_y)

    @pyqtSlot(bool)
    def _on_popup_snap_changed(self, snap_enabled: bool) -> None:
        """Handle snap change from popup"""
        if self.sync_in_progress or not self.grid_manager:
            return

        if snap_enabled:
            self.grid_manager.enable_snap()
        else:
            self.grid_manager.disable_snap()

    @pyqtSlot()
    def _on_popup_reset_requested(self) -> None:
        """Handle reset request from popup"""
        if self.sync_in_progress or not self.grid_manager:
            return

        self.grid_manager.reset_to_defaults()

    # =========================
    # CANVAS ENHANCEMENT
    # =========================

    def _enhance_canvas_grid_methods(self) -> None:
        """Enhance existing canvas grid methods"""
        if not self.pdf_canvas or not self.grid_manager:
            return

        # Store original methods if they exist
        original_draw_grid = getattr(self.pdf_canvas, '_draw_grid', None)
        original_toggle_grid = getattr(self.pdf_canvas, 'toggle_grid', None)

    # Enhanced grid drawing method
    def enhanced_draw_grid(painter):
        """Enhanced grid drawing using GridManager with page boundaries"""
        if hasattr(self.pdf_canvas, 'page_pixmap') and self.pdf_canvas.page_pixmap:
            width = self.pdf_canvas.page_pixmap.width()
            height = self.pdf_canvas.page_pixmap.height()
            zoom_level = getattr(self.pdf_canvas, 'zoom_level', 1.0)

            # NEW: Pass canvas for page boundary support
            self.grid_manager.draw_grid(painter, width, height, zoom_level,
                                        canvas=self.pdf_canvas)

    # =========================
    # PUBLIC API
    # =========================

    def sync_all_components(self) -> None:
        """Synchronize all components with GridManager state"""
        if not self.grid_manager:
            return

        settings = self.grid_manager.get_settings()

        self._on_manager_visibility_changed(settings.visible)
        self._on_manager_color_changed(settings.color)
        self._on_manager_spacing_changed(settings.spacing)
        self._on_manager_offset_changed(settings.offset_x, settings.offset_y)
        self._on_manager_snap_changed(settings.snap_enabled)
        self._on_manager_sync_zoom_changed(settings.sync_with_zoom)

        print("📐 All components synchronized with GridManager")

    def is_ready(self) -> bool:
        """Check if all required components are registered"""
        return (self.grid_manager is not None and
                self.grid_popup is not None and
                self.pdf_canvas is not None)

    def get_status(self) -> dict:
        """Get integration status"""
        return {
            'grid_manager': self.grid_manager is not None,
            'grid_popup': self.grid_popup is not None,
            'pdf_canvas': self.pdf_canvas is not None,
            'toolbar_manager': self.toolbar_manager is not None,
            'connections_established': self.connections_established,
            'ready': self.is_ready()
        }


# =========================
# INTEGRATION HELPER
# =========================

def setup_grid_integration(main_window) -> GridIntegrator:
    """
    Helper function to set up grid integration for a main window

    Args:
        main_window: The main application window containing grid components

    Returns:
        GridIntegrator: Configured integrator instance
    """
    from grid_manager import GridManager

    # Create components
    grid_manager = GridManager(main_window)
    integrator = GridIntegrator(main_window)

    # Register GridManager
    integrator.set_grid_manager(grid_manager)

    # Try to find and register existing components
    if hasattr(main_window, 'grid_popup'):
        integrator.set_grid_popup(main_window.grid_popup)

    if hasattr(main_window, 'pdf_canvas'):
        integrator.set_pdf_canvas(main_window.pdf_canvas)

    if hasattr(main_window, 'toolbar_manager'):
        integrator.set_toolbar_manager(main_window.toolbar_manager)

    # Sync initial state
    integrator.sync_all_components()

    print("🔗 Grid integration setup complete")
    print(f"📊 Status: {integrator.get_status()}")

    return integrator


# =========================
# USAGE EXAMPLE
# =========================

def example_integration():
    """Example of how to integrate the GridManager with existing components"""

    print("=== Grid Integration Example ===")

    # This would typically be called in your main window initialization:
    """
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            # ... existing initialization code ...

            # Set up grid integration
            self.grid_integrator = setup_grid_integration(self)

            # The integrator will now handle all grid-related communication
            # between components automatically
    """

    print("Integration example completed!")


if __name__ == "__main__":
    example_integration()