"""
UI components for TOC display and interaction
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QAction

from ..models.a_toc_entry import TOCEntry

class TOCTreeWidget(QTreeWidget):
    """
    Specialized tree widget for TOC display
    Location: src/ui/toc_widget.py

    Focused on TOC-specific tree behavior
    """

    # Signals
    entryNavigationRequested = pyqtSignal(TOCEntry)  # Navigate to entry
    entrySelected = pyqtSignal(TOCEntry)  # Entry selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Configure tree widget appearance"""
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Connect signals
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def populate_from_entries(self, toc_entries: List[TOCEntry]):
        """Populate tree from TOC entries"""
        self.clear()

        for entry in toc_entries:
            item = self._create_tree_item(entry)
            self.addTopLevelItem(item)

        self.expandAll()

    def _create_tree_item(self, toc_entry: TOCEntry) -> QTreeWidgetItem:
        """Create tree item from TOC entry"""
        item = QTreeWidgetItem([toc_entry.get_display_title()])
        item.setData(0, Qt.ItemDataRole.UserRole, toc_entry)

        # Style top-level entries
        if toc_entry.level == 0:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        # Add children
        for child_entry in toc_entry.children:
            child_item = self._create_tree_item(child_entry)
            item.addChild(child_item)

        return item

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item selection"""
        toc_entry = item.data(0, Qt.ItemDataRole.UserRole)
        if toc_entry:
            self.entrySelected.emit(toc_entry)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle navigation request"""
        toc_entry = item.data(0, Qt.ItemDataRole.UserRole)
        if toc_entry:
            self.entryNavigationRequested.emit(toc_entry)

    def _show_context_menu(self, position: QPoint):
        """Show context menu"""
        item = self.itemAt(position)
        if not item:
            return

        toc_entry = item.data(0, Qt.ItemDataRole.UserRole)
        if not toc_entry:
            return

        menu = QMenu(self)

        # Navigate action
        navigate_action = QAction("📍 Go to Page", self)
        navigate_action.triggered.connect(
            lambda: self.entryNavigationRequested.emit(toc_entry)
        )
        menu.addAction(navigate_action)

        # Copy title
        copy_action = QAction("📋 Copy Title", self)
        copy_action.triggered.connect(
            lambda: self._copy_to_clipboard(toc_entry.title)
        )
        menu.addAction(copy_action)

        menu.exec(self.mapToGlobal(position))

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)

