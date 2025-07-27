"""
Integration helper for main window
"""
from typing import Optional

from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from .a_toc_dock import TOCDockWidget


class TOCIntegration:
    """
    Helper class for integrating TOC with main window
    Location: src/ui/toc_integration.py

    Handles main window integration and event wiring
    """

    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.toc_dock: Optional[TOCDockWidget] = None

    def setup_toc_integration(self):
        """Set up complete TOC integration"""

        # Create TOC dock
        self.toc_dock = TOCDockWidget(self.main_window)

        # Add to main window
        self.main_window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.toc_dock)

        # Connect navigation
        self.toc_dock.pageNavigationRequested.connect(self._handle_navigation)

        # Add menu actions
        self._add_toc_menu_actions()

        print("📖 TOC integration complete")

    def _handle_navigation(self, page_num: int, x: float, y: float):
        """Handle TOC navigation request"""
        # Delegate to main window navigation method
        if hasattr(self.main_window, 'navigate_to_page_with_coordinates'):
            self.main_window.navigate_to_page_with_coordinates(page_num, x, y)
        elif hasattr(self.main_window, 'jump_to_page'):
            self.main_window.jump_to_page(page_num + 1)  # Convert to 1-based

    def _add_toc_menu_actions(self):
        """Add TOC toggle to View menu"""
        # Find or create View menu
        menu_bar = self.main_window.menuBar()
        view_menu = None

        for action in menu_bar.actions():
            if action.text() == "View":
                view_menu = action.menu()
                break

        if not view_menu:
            view_menu = menu_bar.addMenu("View")

        # Add TOC toggle
        toc_action = QAction("📖 Table of Contents", self.main_window)
        toc_action.setCheckable(True)
        toc_action.setChecked(True)
        toc_action.toggled.connect(self.toc_dock.setVisible)

        view_menu.addAction(toc_action)

        # Sync with dock visibility
        self.toc_dock.visibilityChanged.connect(toc_action.setChecked)

    def load_document_toc(self, pdf_document):
        """Load TOC when document changes"""
        if self.toc_dock:
            success = self.toc_dock.load_document_toc(pdf_document)
            if success:
                self.toc_dock.show()
            return success
        return False
