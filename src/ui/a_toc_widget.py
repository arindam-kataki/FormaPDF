from typing import Optional, List

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidgetItem

from ..core.a_toc_extractor import TOCExtractor
from ..core.a_toc_navigator import TOCNavigator
from ..models.a_toc_entry import TOCEntry
from .a_toc_tree_widget import TOCTreeWidget


class TOCWidget(QWidget):
    """
    Complete TOC widget with controls
    Location: src/ui/toc_widget.py (same file as TOCTreeWidget)

    Main TOC UI component
    """

    # Signals
    pageNavigationRequested = pyqtSignal(int, float, float)  # page, x, y
    entrySelected = pyqtSignal(str)  # entry title

    def __init__(self, parent=None):
        super().__init__(parent)

        self.toc_extractor: Optional[TOCExtractor] = None
        self.toc_navigator: Optional[TOCNavigator] = None
        self.current_page = 0

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("📖 Table of Contents")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh table of contents")
        self.refresh_btn.setMaximumWidth(30)
        self.refresh_btn.clicked.connect(self.refresh_toc)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # TOC tree
        self.toc_tree = TOCTreeWidget()
        self.toc_tree.entryNavigationRequested.connect(self._on_entry_navigation)
        self.toc_tree.entrySelected.connect(self._on_entry_selected)
        layout.addWidget(self.toc_tree)

        # Status label
        self.status_label = QLabel("No table of contents available")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)

    def load_toc(self, pdf_document) -> bool:
        """Load TOC from PDF document"""
        if not pdf_document:
            self.status_label.setText("No document loaded")
            return False

        # Extract TOC
        self.toc_extractor = TOCExtractor(pdf_document)
        toc_entries = self.toc_extractor.extract_toc()

        if not toc_entries:
            self.status_label.setText("No table of contents found")
            return False

        # Create navigator
        self.toc_navigator = TOCNavigator(toc_entries)

        # Populate UI
        self.toc_tree.populate_from_entries(toc_entries)

        # Update status
        entry_count = len(self.toc_navigator.flat_entries)
        self.status_label.setText(f"{entry_count} entries found")

        return True

    def _on_entry_navigation(self, toc_entry):
        """Handle navigation to TOC entry - DEBUG VERSION"""
        x, y = toc_entry.coordinates

        print(f"📖 TOC NAVIGATION DEBUG:")
        print(f"   Title: {toc_entry.title}")
        print(f"   Page: {toc_entry.page} (0-based)")
        print(f"   Level: {toc_entry.level}")
        print(f"   Dest Type: {toc_entry.dest_type}")
        print(f"   Coordinates: {toc_entry.coordinates}")
        print(f"   Emitting signal: pageNavigationRequested({toc_entry.page}, {x}, {y})")

        self.pageNavigationRequested.emit(toc_entry.page, x, y)

    def _on_entry_selected(self, toc_entry: TOCEntry):
        """Handle entry selection"""
        self.entrySelected.emit(toc_entry.title)

    def refresh_toc(self):
        """Refresh table of contents"""
        if self.toc_extractor:
            # Re-extract from same document
            toc_entries = self.toc_extractor.extract_toc()
            if toc_entries:
                self.toc_navigator = TOCNavigator(toc_entries)
                self.toc_tree.populate_from_entries(toc_entries)

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

        # Connect lazy loading signal
        self.itemExpanded.connect(self._on_item_expanded)

        print(f"📖 Tree populated with {len([e for e in toc_entries if e.level == 0])} top-level entries (lazy loading)")

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
