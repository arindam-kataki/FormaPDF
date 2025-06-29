# Toolbar Manager Mixin
# File: src/ui/toolbar_manager.py

"""
Toolbar Manager Mixin
Manages all toolbar functionality and state changes based on project workflow
"""

from typing import List, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QToolBar, QToolButton, QMenu, QLabel, QWidget
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QTimer

# Import with safe fallbacks
try:
    from PyQt6.QtWidgets import QApplication

    QT_AVAILABLE = True
except ImportError:
    print("Warning: PyQt6 widgets not fully available")
    QT_AVAILABLE = False


class ToolbarManager:
    """
    Mixin class that manages adaptive toolbar functionality

    This mixin provides:
    - Adaptive toolbar that shows/hides based on project state
    - Grid controls dropdown menu
    - Document navigation controls
    - Zoom and view controls
    - Project-aware toolbar state management

    Usage:
        class MyMainWindow(QMainWindow, ToolbarManager):
            def __init__(self):
                super().__init__()
                self.init_toolbar_manager()
    """

    def init_toolbar_manager(self):
        """Initialize toolbar manager - call this in your main window's __init__"""
        print("🔧 Initializing toolbar manager...")

        # Initialize toolbar state tracking
        self.toolbar_initialized = False
        self.current_toolbar_state = "no_project"  # no_project, project_loaded, pdf_loaded

        # Store toolbar sections for visibility management
        self.project_section_actions = []
        self.document_section_actions = []
        self.view_section_actions = []
        self.tools_section_actions = []

        # Store separators for visibility control
        self.toolbar_separators = {}

        # Grid state
        self.grid_visible = False
        self.grid_spacing = 20
        self.grid_offset_x = 0
        self.grid_offset_y = 0

        print("✅ Toolbar manager initialized")

    # =========================
    # MAIN TOOLBAR CREATION
    # =========================

    def create_toolbar(self):
        """Create the main adaptive toolbar"""
        print("🔧 Creating adaptive toolbar...")

        # Remove existing toolbar if it exists
        if hasattr(self, 'main_toolbar'):
            self.removeToolBar(self.main_toolbar)

        # Create new toolbar
        self.main_toolbar = QToolBar("Main Toolbar")
        self.main_toolbar.setMovable(False)
        self.main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(self.main_toolbar)

        # Create all toolbar sections
        self._create_project_section()
        self._create_document_section()
        self._create_view_section()
        self._create_tools_section()

        # Set initial state
        self.update_toolbar_state("no_project")
        self.toolbar_initialized = True

        print("✅ Adaptive toolbar created")

    def _create_project_section(self):
        """Create project management buttons (always visible)"""
        print("  📄 Creating project section...")

        # Get project actions from ProjectManagementMixin if available
        if hasattr(self, 'create_project_toolbar_actions'):
            try:
                project_actions = self.create_project_toolbar_actions(self.main_toolbar)  # type: ignore
                self.project_section_actions = project_actions
                print(f"    ✅ Added {len(project_actions)} project actions from mixin")
            except Exception as e:
                print(f"    ⚠️ Error getting project actions: {e}")
                self._create_fallback_project_actions()
        else:
            print("    ⚠️ Project management not available, creating fallback actions")
            self._create_fallback_project_actions()

    def _create_fallback_project_actions(self):
        """Create fallback project actions when mixin not available"""
        new_action = QAction("📄 New", self)
        new_action.setToolTip("Create new project")
        new_action.triggered.connect(self._safe_call('new_project'))
        self.main_toolbar.addAction(new_action)

        open_action = QAction("📁 Open", self)
        open_action.setToolTip("Open existing project")
        open_action.triggered.connect(self._safe_call('open_project'))
        self.main_toolbar.addAction(open_action)

        self.project_section_actions = [new_action, open_action]

    def _create_document_section(self):
        """Create document navigation controls (hidden initially)"""
        print("  📖 Creating document section...")

        # Add separator
        self.main_toolbar.addSeparator()
        self.toolbar_separators['doc_sep1'] = self.main_toolbar.actions()[-1]

        # Navigation controls
        self.prev_action = QAction("⬅️ Previous", self)
        self.prev_action.setToolTip("Previous page (Left Arrow)")
        self.prev_action.setShortcut("Left")
        self.prev_action.triggered.connect(self._safe_call('previous_page'))
        self.main_toolbar.addAction(self.prev_action)

        self.next_action = QAction("➡️ Next", self)
        self.next_action.setToolTip("Next page (Right Arrow)")
        self.next_action.setShortcut("Right")
        self.next_action.triggered.connect(self._safe_call('next_page'))
        self.main_toolbar.addAction(self.next_action)

        # Page info display
        self.page_info_label = QLabel("Page 1 of 1")
        self.page_info_label.setMinimumWidth(80)
        self.page_info_label.setStyleSheet("QLabel { margin: 0 10px; color: #666; }")
        self.page_info_action = self.main_toolbar.addWidget(self.page_info_label)

        # Store document actions
        self.document_section_actions = [
            self.prev_action, self.next_action, self.page_info_action
        ]

        print(f"    ✅ Added {len(self.document_section_actions)} document actions")

    def _create_view_section(self):
        """Create view and zoom controls (hidden initially)"""
        print("  👁️ Creating view section...")

        # Add separator
        self.main_toolbar.addSeparator()
        self.toolbar_separators['view_sep1'] = self.main_toolbar.actions()[-1]

        # Zoom out
        self.zoom_out_action = QAction("🔍-", self)
        self.zoom_out_action.setToolTip("Zoom out (Ctrl+-)")
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(self._safe_call('zoom_out'))
        self.main_toolbar.addAction(self.zoom_out_action)

        # Zoom level display
        self.zoom_level_label = QLabel("100%")
        self.zoom_level_label.setMinimumWidth(50)
        self.zoom_level_label.setStyleSheet("QLabel { margin: 0 5px; color: #666; font-weight: bold; }")
        self.zoom_level_action = self.main_toolbar.addWidget(self.zoom_level_label)

        # Zoom in
        self.zoom_in_action = QAction("🔍+", self)
        self.zoom_in_action.setToolTip("Zoom in (Ctrl++)")
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(self._safe_call('zoom_in'))
        self.main_toolbar.addAction(self.zoom_in_action)

        # Fit controls
        self.fit_width_action = QAction("📏", self)
        self.fit_width_action.setToolTip("Fit to width")
        self.fit_width_action.triggered.connect(self.fit_to_width)
        self.main_toolbar.addAction(self.fit_width_action)

        self.fit_page_action = QAction("📄", self)
        self.fit_page_action.setToolTip("Fit to page")
        self.fit_page_action.triggered.connect(self.fit_to_page)
        self.main_toolbar.addAction(self.fit_page_action)

        # Second separator before grid
        self.main_toolbar.addSeparator()
        self.toolbar_separators['view_sep2'] = self.main_toolbar.actions()[-1]

        # Grid dropdown button
        self._create_grid_dropdown()

        # Store view actions
        self.view_section_actions = [
            self.zoom_out_action, self.zoom_level_action, self.zoom_in_action,
            self.fit_width_action, self.fit_page_action, self.grid_action
        ]

        print(f"    ✅ Added {len(self.view_section_actions)} view actions")

    def _create_grid_dropdown(self):
        """Create grid dropdown menu button"""
        print("    📐 Creating grid dropdown...")

        self.grid_button = QToolButton()
        self.grid_button.setText("📐 Grid")
        self.grid_button.setToolTip("Grid options and controls")
        self.grid_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        # Create the dropdown menu
        self.grid_menu = QMenu(self.grid_button)

        # Toggle grid visibility
        self.toggle_grid_action = QAction("👁️ Show Grid", self)
        self.toggle_grid_action.setCheckable(True)
        self.toggle_grid_action.setChecked(self.grid_visible)
        self.toggle_grid_action.triggered.connect(self.toggle_grid_visibility)
        self.grid_menu.addAction(self.toggle_grid_action)

        self.grid_menu.addSeparator()

        # Grid spacing controls
        self.increase_grid_action = QAction("➕ Increase Spacing", self)
        self.increase_grid_action.setToolTip("Make grid squares larger")
        self.increase_grid_action.triggered.connect(self.increase_grid_spacing)
        self.grid_menu.addAction(self.increase_grid_action)

        self.decrease_grid_action = QAction("➖ Decrease Spacing", self)
        self.decrease_grid_action.setToolTip("Make grid squares smaller")
        self.decrease_grid_action.triggered.connect(self.decrease_grid_spacing)
        self.grid_menu.addAction(self.decrease_grid_action)

        self.grid_menu.addSeparator()

        # Grid position controls
        self.move_grid_left_action = QAction("⬅️ Move Left", self)
        self.move_grid_left_action.triggered.connect(lambda: self.move_grid(-5, 0))
        self.grid_menu.addAction(self.move_grid_left_action)

        self.move_grid_right_action = QAction("➡️ Move Right", self)
        self.move_grid_right_action.triggered.connect(lambda: self.move_grid(5, 0))
        self.grid_menu.addAction(self.move_grid_right_action)

        self.move_grid_up_action = QAction("⬆️ Move Up", self)
        self.move_grid_up_action.triggered.connect(lambda: self.move_grid(0, -5))
        self.grid_menu.addAction(self.move_grid_up_action)

        self.move_grid_down_action = QAction("⬇️ Move Down", self)
        self.move_grid_down_action.triggered.connect(lambda: self.move_grid(0, 5))
        self.grid_menu.addAction(self.move_grid_down_action)

        self.grid_menu.addSeparator()

        # Reset grid
        self.reset_grid_action = QAction("🔄 Reset Grid", self)
        self.reset_grid_action.setToolTip("Reset grid to default position and spacing")
        self.reset_grid_action.triggered.connect(self.reset_grid)
        self.grid_menu.addAction(self.reset_grid_action)

        # Assign menu to button and add to toolbar
        self.grid_button.setMenu(self.grid_menu)
        self.grid_action = self.main_toolbar.addWidget(self.grid_button)

        print("      ✅ Grid dropdown created with 8 actions")

    def _create_tools_section(self):
        """Create tools section (hidden initially)"""
        print("  🛠️ Creating tools section...")

        # Add separator
        self.main_toolbar.addSeparator()
        self.toolbar_separators['tools_sep'] = self.main_toolbar.actions()[-1]

        # Voice controls
        self.voice_action = QAction("🎤 Voice", self)
        self.voice_action.setCheckable(True)
        self.voice_action.setToolTip("Toggle voice commands")
        self.voice_action.triggered.connect(self._safe_call('toggle_voice'))
        self.main_toolbar.addAction(self.voice_action)

        # Field tools (if field palette available)
        self.tools_section_actions = [self.voice_action]

        if hasattr(self, 'field_palette'):
            self.add_field_action = QAction("➕ Field", self)
            self.add_field_action.setToolTip("Add form field")
            self.add_field_action.triggered.connect(self._safe_call('add_form_field'))
            self.main_toolbar.addAction(self.add_field_action)
            self.tools_section_actions.append(self.add_field_action)

        print(f"    ✅ Added {len(self.tools_section_actions)} tool actions")

    # =========================
    # TOOLBAR STATE MANAGEMENT
    # =========================

    def update_toolbar_state(self, state: str):
        """
        Update toolbar visibility based on application state

        Args:
            state: "no_project", "project_loaded", or "pdf_loaded"
        """
        if not self.toolbar_initialized:
            print("⚠️ Toolbar not initialized, skipping state update")
            return

        print(f"🔧 Updating toolbar state: {self.current_toolbar_state} → {state}")
        self.current_toolbar_state = state

        if state == "no_project":
            self._show_project_only()
        elif state == "project_loaded":
            self._show_project_and_basic()
        elif state == "pdf_loaded":
            self._show_all_controls()
        else:
            print(f"⚠️ Unknown toolbar state: {state}")

    def _show_project_only(self):
        """Show only project management buttons"""
        print("  📄 Showing project-only toolbar")

        # Show project section
        self._set_actions_visible(self.project_section_actions, True)

        # Hide all other sections
        self._set_actions_visible(self.document_section_actions, False)
        self._set_actions_visible(self.view_section_actions, False)
        self._set_actions_visible(self.tools_section_actions, False)

        # Hide separators
        for separator in self.toolbar_separators.values():
            separator.setVisible(False)

    def _show_project_and_basic(self):
        """Show project + basic document controls (when project loaded but no PDF)"""
        print("  📖 Showing project + basic controls")

        # Show project section
        self._set_actions_visible(self.project_section_actions, True)

        # Show basic document controls (but disabled)
        self._set_actions_visible(self.document_section_actions, True, enabled=False)

        # Hide view and tools
        self._set_actions_visible(self.view_section_actions, False)
        self._set_actions_visible(self.tools_section_actions, False)

        # Show relevant separators
        self.toolbar_separators.get('doc_sep1', QAction()).setVisible(True)

    def _show_all_controls(self):
        """Show all toolbar controls (when PDF is loaded)"""
        print("  🎯 Showing all toolbar controls")

        # Show all sections
        self._set_actions_visible(self.project_section_actions, True)
        self._set_actions_visible(self.document_section_actions, True)
        self._set_actions_visible(self.view_section_actions, True)
        self._set_actions_visible(self.tools_section_actions, True)

        # Show all separators
        for separator in self.toolbar_separators.values():
            separator.setVisible(True)

    def _set_actions_visible(self, actions: List, visible: bool, enabled: bool = True):
        """Set visibility and enabled state for a list of actions"""
        for action in actions:
            try:
                if hasattr(action, 'setVisible'):
                    action.setVisible(visible)
                    if visible:
                        action.setEnabled(enabled)
                elif hasattr(action, 'widget') and action.widget():
                    # Handle widget actions (like labels)
                    action.widget().setVisible(visible)
                    if visible and hasattr(action.widget(), 'setEnabled'):
                        action.widget().setEnabled(enabled)
            except Exception as e:
                print(f"    ⚠️ Error setting action visibility: {e}")

    # =========================
    # TOOLBAR UPDATE METHODS
    # =========================

    def update_page_info(self, current_page: int = 1, total_pages: int = 1):
        """Update page information display in toolbar"""
        if hasattr(self, 'page_info_label'):
            self.page_info_label.setText(f"Page {current_page} of {total_pages}")

    def update_zoom_info(self, zoom_level: float = 1.0):
        """Update zoom level display in toolbar"""
        if hasattr(self, 'zoom_level_label'):
            self.zoom_level_label.setText(f"{int(zoom_level * 100)}%")

    def auto_update_from_pdf_canvas(self):
        """Automatically update toolbar info from PDF canvas if available"""
        if hasattr(self, 'pdf_canvas'):
            try:
                # Update page info
                current_page = getattr(self.pdf_canvas, 'current_page', 0) + 1
                total_pages = getattr(self.pdf_canvas, 'page_count', 1)
                self.update_page_info(current_page, total_pages)

                # Update zoom info
                zoom_level = getattr(self.pdf_canvas, 'zoom_level', 1.0)
                self.update_zoom_info(zoom_level)

            except Exception as e:
                print(f"⚠️ Error auto-updating from PDF canvas: {e}")

    # =========================
    # GRID CONTROL METHODS
    # =========================

    def toggle_grid_visibility(self):
        """Toggle grid visibility and update button text"""
        self.grid_visible = not self.grid_visible

        # Update action text
        self.toggle_grid_action.setText("👁️ Hide Grid" if self.grid_visible else "👁️ Show Grid")
        self.toggle_grid_action.setChecked(self.grid_visible)

        # Apply to PDF canvas if available
        if hasattr(self.pdf_canvas, 'set_grid_visible'):
            self.pdf_canvas.set_grid_visible(self.grid_visible)
        elif hasattr(self.pdf_canvas, 'toggle_grid'):
            self.pdf_canvas.toggle_grid()

        print(f"📐 Grid visibility: {self.grid_visible}")

    def increase_grid_spacing(self):
        """Increase grid spacing"""
        self.grid_spacing = min(self.grid_spacing + 5, 100)  # Max 100px
        self._apply_grid_settings()
        print(f"📐 Grid spacing increased to: {self.grid_spacing}px")

    def decrease_grid_spacing(self):
        """Decrease grid spacing"""
        self.grid_spacing = max(self.grid_spacing - 5, 5)  # Min 5px
        self._apply_grid_settings()
        print(f"📐 Grid spacing decreased to: {self.grid_spacing}px")

    def move_grid(self, dx: int, dy: int):
        """Move grid by specified offset"""
        self.grid_offset_x += dx
        self.grid_offset_y += dy
        self._apply_grid_settings()
        print(f"📐 Grid moved to offset: ({self.grid_offset_x}, {self.grid_offset_y})")

    def reset_grid(self):
        """Reset grid to default settings"""
        self.grid_spacing = 20
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self._apply_grid_settings()
        print("📐 Grid reset to defaults")

    def _apply_grid_settings(self):
        """Apply current grid settings to PDF canvas"""
        if hasattr(self.pdf_canvas, 'set_grid_settings'):
            self.pdf_canvas.set_grid_settings(
                spacing=self.grid_spacing,
                offset_x=self.grid_offset_x,
                offset_y=self.grid_offset_y
            )
        elif hasattr(self.pdf_canvas, 'update_grid'):
            self.pdf_canvas.update_grid()

    # =========================
    # VIEW CONTROL METHODS
    # =========================

    def fit_to_width(self):
        """Fit PDF to window width"""
        if hasattr(self.pdf_canvas, 'fit_to_width'):
            self.pdf_canvas.fit_to_width()
            self.auto_update_from_pdf_canvas()

    def fit_to_page(self):
        """Fit entire PDF page to window"""
        if hasattr(self.pdf_canvas, 'fit_to_page'):
            self.pdf_canvas.fit_to_page()
            self.auto_update_from_pdf_canvas()

    # =========================
    # INTEGRATION HOOKS
    # =========================

    def on_project_opened_toolbar(self, project_path: str, project_data: dict):
        """Handle project opened - update toolbar state"""
        print("📋 Toolbar: Project opened")
        self.update_toolbar_state("project_loaded")

    def on_project_closed_toolbar(self):
        """Handle project closed - update toolbar state"""
        print("📋 Toolbar: Project closed")
        self.update_toolbar_state("no_project")

    def on_pdf_loaded_toolbar(self):
        """Handle PDF loaded - show all controls"""
        print("📋 Toolbar: PDF loaded")
        self.update_toolbar_state("pdf_loaded")
        self.auto_update_from_pdf_canvas()

    def on_pdf_page_changed_toolbar(self):
        """Handle PDF page change - update page info"""
        self.auto_update_from_pdf_canvas()

    def on_pdf_zoom_changed_toolbar(self):
        """Handle PDF zoom change - update zoom info"""
        self.auto_update_from_pdf_canvas()

    # =========================
    # UTILITY METHODS
    # =========================

    def _safe_call(self, method_name: str):
        """Return a safe callable for toolbar actions"""

        def safe_callable():
            if hasattr(self, method_name):
                try:
                    method = getattr(self, method_name)
                    return method()
                except Exception as e:
                    print(f"⚠️ Error calling {method_name}: {e}")
            else:
                print(f"⚠️ Method {method_name} not found")

        return safe_callable

    def cleanup_toolbar_manager(self):
        """Cleanup toolbar resources"""
        if hasattr(self, 'main_toolbar'):
            self.removeToolBar(self.main_toolbar)
        print("🧹 Toolbar manager cleaned up")