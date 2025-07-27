"""
Dock widget container for TOC
"""

from PyQt6.QtWidgets import QDockWidget, QMainWindow
from PyQt6.QtCore import Qt, pyqtSignal

from .a_toc_widget import TOCWidget


class TOCDockWidget(QDockWidget):
    """
    Dock widget containing TOC widget
    Location: src/ui/toc_dock.py

    Provides dockable TOC panel for main window
    """

    pageNavigationRequested = pyqtSignal(int, float, float)  # page, x, y

    def __init__(self, parent: QMainWindow = None):
        super().__init__("Table of Contents", parent)

        # Create TOC widget
        self.toc_widget = TOCWidget()
        self.setWidget(self.toc_widget)

        # Connect signals
        self.toc_widget.pageNavigationRequested.connect(self.pageNavigationRequested)

        # Configure dock
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

    def load_document_toc(self, pdf_document) -> bool:
        """Load TOC for document"""
        return self.toc_widget.load_toc(pdf_document)

    def update_current_page(self, page_num: int):
        """Update current page highlight"""
        # TODO: Implement current page highlighting
        pass