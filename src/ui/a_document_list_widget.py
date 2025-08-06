# a_document_list_widget.py
"""
Document List Widget for PDF Research Platform
Tree widget showing all documents in the current assembly with drag-drop support
"""

from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPoint
)
from PyQt6.QtGui import QAction


class DocumentListWidget(QTreeWidget):
    """
    Tree widget showing all documents in the current assembly
    with drag-drop support and context menus
    """

    # Signals
    document_opened = pyqtSignal(str)  # Emits document path
    document_removed = pyqtSignal(str)  # Emits document path
    documents_reordered = pyqtSignal()
    document_properties_requested = pyqtSignal(str)  # Emits document path

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup_ui()
        self.setup_connections()

        # Document type icons (emoji placeholders for now)
        self.type_icons = {
            'pdf': '📄',
            'docx': '📝',
            'xlsx': '📊',
            'txt': '📃',
            'image': '🖼️',
            'default': '📄'
        }

    def setup_ui(self):
        """Setup the widget UI"""
        # Configure tree widget
        self.setHeaderLabels(["Documents", "Type", "Pages", "Annotations"])
        self.setRootIsDecorated(False)
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Enable drag and drop for reordering
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

        # Adjust column widths
        self.setColumnWidth(0, 200)  # Document name
        self.setColumnWidth(1, 60)  # Type
        self.setColumnWidth(2, 60)  # Pages
        self.setColumnWidth(3, 80)  # Annotations

        # Apply styling
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)

    def setup_connections(self):
        """Setup signal connections"""
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)

    def add_document(self, file_path: str, doc_info: Optional[Dict] = None):
        """
        Add a document to the list

        Args:
            file_path: Path to the document file
            doc_info: Optional dictionary with document metadata
        """
        path = Path(file_path)

        # Determine file type and icon
        file_type, icon = self.get_file_type_and_icon(path)

        # Create tree item
        item = QTreeWidgetItem()
        item.setText(0, f"{icon} {path.name}")
        item.setText(1, file_type.upper())
        item.setText(2, str(doc_info.get('pages', '-') if doc_info else '-'))
        item.setText(3, str(doc_info.get('annotations', 0) if doc_info else 0))

        # Store full path in user data
        item.setData(0, Qt.ItemDataRole.UserRole, str(file_path))

        # Add tooltip with full path
        item.setToolTip(0, str(file_path))

        # Set status tip for each column
        for col in range(self.columnCount()):
            item.setStatusTip(col, f"Document: {path.name}")

        self.addTopLevelItem(item)

    def get_file_type_and_icon(self, path: Path) -> tuple[str, str]:
        """
        Get file type and icon for a document

        Args:
            path: Path to the document

        Returns:
            Tuple of (file_type, icon)
        """
        extension = path.suffix.lower()[1:]  # Remove the dot

        if extension in ['pdf']:
            return 'pdf', self.type_icons['pdf']
        elif extension in ['doc', 'docx']:
            return 'docx', self.type_icons['docx']
        elif extension in ['xls', 'xlsx']:
            return 'xlsx', self.type_icons['xlsx']
        elif extension in ['txt', 'md']:
            return 'txt', self.type_icons['txt']
        elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
            return 'image', self.type_icons['image']
        else:
            return extension, self.type_icons['default']

    def remove_selected_documents(self):
        """Remove selected documents from the list"""
        selected_items = self.selectedItems()

        if not selected_items:
            return

        # Confirm removal
        count = len(selected_items)
        msg = f"Remove {count} document{'s' if count > 1 else ''} from the assembly?"

        reply = QMessageBox.question(
            self,
            "Remove Documents",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                file_path = item.data(0, Qt.ItemDataRole.UserRole)
                index = self.indexOfTopLevelItem(item)
                self.takeTopLevelItem(index)
                self.document_removed.emit(file_path)

    def update_document_info(self, file_path: str, doc_info: Dict):
        """
        Update document information in the list

        Args:
            file_path: Path to the document
            doc_info: Dictionary with updated document metadata
        """
        # Find the item
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == file_path:
                # Update columns
                if 'pages' in doc_info:
                    item.setText(2, str(doc_info['pages']))
                if 'annotations' in doc_info:
                    item.setText(3, str(doc_info['annotations']))
                break

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click to open document"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            self.document_opened.emit(file_path)

    def show_context_menu(self, position: QPoint):
        """Show context menu for document items"""
        item = self.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Open action
        open_action = QAction("📖 Open Document", self)
        open_action.triggered.connect(lambda: self.document_opened.emit(
            item.data(0, Qt.ItemDataRole.UserRole)
        ))
        menu.addAction(open_action)

        menu.addSeparator()

        # Properties action
        properties_action = QAction("ℹ️ Properties...", self)
        properties_action.triggered.connect(lambda: self.show_document_properties(item))
        menu.addAction(properties_action)

        # Rename action
        rename_action = QAction("✏️ Rename...", self)
        rename_action.triggered.connect(lambda: self.rename_document(item))
        menu.addAction(rename_action)

        menu.addSeparator()

        # Remove action
        remove_action = QAction("🗑️ Remove from Assembly", self)
        remove_action.triggered.connect(self.remove_selected_documents)
        menu.addAction(remove_action)

        menu.exec(self.mapToGlobal(position))

    def show_document_properties(self, item: QTreeWidgetItem):
        """Show document properties dialog"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        self.document_properties_requested.emit(file_path)

    def rename_document(self, item: QTreeWidgetItem):
        """Rename a document (in the assembly, not the file)"""
        # Make the item editable temporarily
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.editItem(item, 0)
        # Remove editable flag after editing
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def get_all_documents(self) -> List[str]:
        """
        Get list of all document paths

        Returns:
            List of document file paths
        """
        documents = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            if file_path:
                documents.append(file_path)
        return documents

    def get_selected_documents(self) -> List[str]:
        """
        Get list of selected document paths

        Returns:
            List of selected document file paths
        """
        documents = []
        for item in self.selectedItems():
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            if file_path:
                documents.append(file_path)
        return documents

    def clear_all(self):
        """Clear all documents from the list"""
        self.clear()

    def get_document_count(self) -> int:
        """
        Get total number of documents

        Returns:
            Number of documents in the list
        """
        return self.topLevelItemCount()

    def select_document(self, file_path: str):
        """
        Select a document in the list

        Args:
            file_path: Path to the document to select
        """
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == file_path:
                self.setCurrentItem(item)
                break

    def refresh_view(self):
        """Refresh the tree view"""
        self.viewport().update()