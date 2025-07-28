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
        self.itemExpanded.connect(self._on_item_expanded)

    def populate_from_entries(self, toc_entries: List[TOCEntry]):
        """Populate tree with lazy loading - only top level initially"""
        self.clear()

        # Store full TOC data for lazy loading
        self.full_toc_entries = toc_entries

        # Only add top-level entries initially
        for entry in toc_entries:
            if entry.level == 0:  # Only top-level entries
                item = self._create_tree_item_lazy(entry)
                self.addTopLevelItem(item)

        print(f"📖 Tree populated with {len([e for e in toc_entries if e.level == 0])} top-level entries (lazy loading)")

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
            print(f"📖 DOUBLE-CLICK DEBUG:")
            print(f"   Entry: {toc_entry.title}")
            print(f"   Page: {toc_entry.page}")
            print(f"   Coordinates: {toc_entry.coordinates}")
            print(f"   About to emit: entryNavigationRequested")
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

    def _create_tree_item_lazy(self, toc_entry: TOCEntry) -> QTreeWidgetItem:
        """Create tree item with lazy loading support"""
        item = QTreeWidgetItem([toc_entry.get_display_title()])
        item.setData(0, Qt.ItemDataRole.UserRole, toc_entry)

        # Style top-level entries
        if toc_entry.level == 0:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        # Add placeholder child if this entry has children
        if toc_entry.children:
            placeholder = QTreeWidgetItem(["Loading..."])
            placeholder.setData(0, Qt.ItemDataRole.UserRole, "placeholder")
            item.addChild(placeholder)

        return item

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion - load children on demand"""
        toc_entry = item.data(0, Qt.ItemDataRole.UserRole)

        if not isinstance(toc_entry, TOCEntry):
            return

        # Check if children are already loaded (not placeholders)
        if item.childCount() > 0:
            first_child = item.child(0)
            child_data = first_child.data(0, Qt.ItemDataRole.UserRole)

            # If first child is placeholder, load real children
            if child_data == "placeholder":
                # Remove placeholder
                item.removeChild(first_child)

                # Add real children
                for child_entry in toc_entry.children:
                    child_item = self._create_tree_item_lazy(child_entry)
                    item.addChild(child_item)

                print(f"📖 Loaded {len(toc_entry.children)} children for: {toc_entry.title}")