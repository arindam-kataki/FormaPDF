# a_assembly_integration.py
"""
Assembly Integration Mixin for SYNAIPTIC Research Platform
Integrates assembly management into the main application window

File: src/ui/assembly_management_mixin.py (when moved to match existing structure)
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

from PyQt6.QtWidgets import (
    QMenuBar, QMenu, QMessageBox, QDialog, QToolBar, QLabel,
    QComboBox, QPushButton, QHBoxLayout, QWidget, QVBoxLayout
)
from PyQt6.QtGui import QAction, QKeySequence, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# Import assembly management classes (with safe fallbacks matching project pattern)
try:
    from a_assembly_manager import AssemblyManager
    from a_assembly_dialog import NewAssemblyDialog, AssemblyPropertiesDialog
    from a_database_models import DatabaseConfig

    ASSEMBLY_MANAGEMENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Assembly management not available - running without assembly features - {e}")
    ASSEMBLY_MANAGEMENT_AVAILABLE = False
    AssemblyManager = None
    NewAssemblyDialog = None
    AssemblyPropertiesDialog = None

logger = logging.getLogger(__name__)


class AssemblyManagementMixin:
    """
    Mixin class that adds assembly management functionality to any QMainWindow

    This mixin adds:
    - Assembly creation, opening, management
    - Assembly selector in toolbar
    - Database-driven assembly storage
    - Integration with existing UI patterns

    Usage:
        class MyMainWindow(QMainWindow, AssemblyManagementMixin):
            def __init__(self):
                super().__init__()
                self.init_assembly_management()

    Pattern matches existing ProjectManagementMixin for consistency.
    """

    # Assembly management signals (matching project pattern)
    assembly_created = pyqtSignal(int, str, object)  # assembly_id, assembly_guid, assembly_path
    assembly_opened = pyqtSignal(int, dict)  # assembly_id, assembly_data
    assembly_saved = pyqtSignal(int)  # assembly_id
    assembly_closed = pyqtSignal()
    assembly_modified_changed = pyqtSignal(bool)  # is_modified

    def init_assembly_management(self):
        """Initialize assembly management system (matches project pattern)"""
        if not ASSEMBLY_MANAGEMENT_AVAILABLE:
            logger.warning("⚠️ Assembly management not available - running without assembly features")
            return

        try:
            # Initialize assembly manager
            self.assembly_manager = AssemblyManager()

            # Current assembly state (matches project pattern)
            self.current_assembly_id = None
            self.current_assembly_data = None
            self.current_assembly_path = None
            self.assembly_modified = False

            # Initialize UI components
            self._create_assembly_menu()
            self._create_assembly_toolbar()

            # Auto-refresh timer (matches project pattern)
            self.assembly_refresh_timer = QTimer()
            self.assembly_refresh_timer.timeout.connect(self._update_recent_assemblies_menu)
            self.assembly_refresh_timer.start(30000)  # Refresh every 30 seconds

            logger.info("✅ Assembly management initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize assembly management: {e}")
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize assembly management:\n{str(e)}"
            )

    def _create_assembly_menu(self):
        """Create assembly-related menu items"""
        if not hasattr(self, 'menubar'):
            self.menubar = self.menuBar()

        # Assembly menu
        assembly_menu = self.menubar.addMenu("&Assembly")

        # New Assembly action
        new_assembly_action = QAction("&New Assembly...", self)
        new_assembly_action.setShortcut(QKeySequence.StandardKey.New)
        new_assembly_action.setStatusTip("Create a new research assembly")
        new_assembly_action.triggered.connect(self.create_new_assembly)
        assembly_menu.addAction(new_assembly_action)

        # Open Assembly action
        open_assembly_action = QAction("&Open Assembly...", self)
        open_assembly_action.setShortcut(QKeySequence.StandardKey.Open)
        open_assembly_action.setStatusTip("Open an existing assembly")
        open_assembly_action.triggered.connect(self.open_assembly_dialog)
        assembly_menu.addAction(open_assembly_action)

        assembly_menu.addSeparator()

        # Recent Assemblies submenu
        self.recent_assemblies_menu = assembly_menu.addMenu("&Recent Assemblies")
        self._update_recent_assemblies_menu()

        assembly_menu.addSeparator()

        # Assembly Properties action
        self.assembly_properties_action = QAction("Assembly &Properties...", self)
        self.assembly_properties_action.setStatusTip("View or edit assembly properties")
        self.assembly_properties_action.triggered.connect(self.show_assembly_properties)
        self.assembly_properties_action.setEnabled(False)
        assembly_menu.addAction(self.assembly_properties_action)

        # Close Assembly action
        self.close_assembly_action = QAction("&Close Assembly", self)
        self.close_assembly_action.setShortcut(QKeySequence("Ctrl+W"))
        self.close_assembly_action.setStatusTip("Close current assembly")
        self.close_assembly_action.triggered.connect(self.close_current_assembly)
        self.close_assembly_action.setEnabled(False)
        assembly_menu.addAction(self.close_assembly_action)

    def _create_assembly_toolbar(self):
        """Create assembly toolbar section"""
        if not hasattr(self, 'main_toolbar'):
            self.main_toolbar = self.addToolBar("Main")

        # Assembly selector widget
        assembly_widget = QWidget()
        assembly_layout = QHBoxLayout(assembly_widget)
        assembly_layout.setContentsMargins(5, 0, 5, 0)

        # Assembly label
        assembly_label = QLabel("Assembly:")
        assembly_label.setStyleSheet("font-weight: bold; color: #555;")
        assembly_layout.addWidget(assembly_label)

        # Assembly selector combo box
        self.assembly_selector = QComboBox()
        self.assembly_selector.setMinimumWidth(200)
        self.assembly_selector.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
        """)
        self.assembly_selector.currentIndexChanged.connect(self._on_assembly_selected)
        assembly_layout.addWidget(self.assembly_selector)

        # New Assembly button
        new_assembly_btn = QPushButton("+ New")
        new_assembly_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 5px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        new_assembly_btn.clicked.connect(self.create_new_assembly)
        assembly_layout.addWidget(new_assembly_btn)

        # Add Documents button (enabled only when assembly is selected)
        self.add_documents_btn = QPushButton("+ Documents")
        self.add_documents_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 5px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.add_documents_btn.clicked.connect(self.add_documents_to_assembly)
        self.add_documents_btn.setEnabled(False)
        assembly_layout.addWidget(self.add_documents_btn)

        # Add to toolbar
        self.main_toolbar.addWidget(assembly_widget)
        self.main_toolbar.addSeparator()

        # Load assemblies into selector
        self._refresh_assembly_selector()

    def create_new_assembly(self):
        """Create a new research assembly"""
        if not ASSEMBLY_MANAGEMENT_AVAILABLE:
            QMessageBox.information(
                self,
                "Feature Unavailable",
                "Assembly management is not available."
            )
            return

        dialog = NewAssemblyDialog(self)
        dialog.assembly_created.connect(self._on_assembly_dialog_created)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.info("✅ Assembly creation dialog completed")

    def _on_assembly_dialog_created(self, signal_type: str, assembly_data: Dict[str, Any]):
        """Handle assembly creation from dialog"""
        try:
            # Create assembly using manager
            assembly_id, assembly_guid, assembly_path = self.assembly_manager.create_assembly(assembly_data)

            # Refresh UI
            self._refresh_assembly_selector()
            self._select_assembly_in_combo(assembly_id)

            # Emit signal
            self.assembly_created.emit(assembly_id, assembly_guid, assembly_path)

            # Show success message
            QMessageBox.information(
                self,
                "Assembly Created",
                f"Assembly '{assembly_data['name']}' has been created successfully."
            )

            logger.info(f"✅ Assembly created: {assembly_data['name']} (ID: {assembly_id})")

        except Exception as e:
            logger.error(f"❌ Error creating assembly: {e}")
            QMessageBox.critical(
                self,
                "Assembly Creation Failed",
                f"Failed to create assembly:\n{str(e)}"
            )

    def open_assembly_dialog(self):
        """Show dialog to select and open an assembly"""
        try:
            assemblies = self.assembly_manager.get_all_assemblies()

            if not assemblies:
                QMessageBox.information(
                    self,
                    "No Assemblies",
                    "No assemblies found. Create a new assembly first."
                )
                return

            # For now, use a simple selection. Could be enhanced with a custom dialog
            from PyQt6.QtWidgets import QInputDialog

            assembly_names = [f"{a['name']} (ID: {a['id']})" for a in assemblies]

            selected_name, ok = QInputDialog.getItem(
                self,
                "Open Assembly",
                "Select assembly to open:",
                assembly_names,
                0,
                False
            )

            if ok and selected_name:
                # Extract assembly ID from selection
                assembly_id = int(selected_name.split("(ID: ")[1].rstrip(")"))
                self.open_assembly_by_id(assembly_id)

        except Exception as e:
            logger.error(f"❌ Error opening assembly dialog: {e}")
            QMessageBox.critical(
                self,
                "Open Assembly Failed",
                f"Failed to open assembly dialog:\n{str(e)}"
            )

    def open_assembly_by_id(self, assembly_id: int):
        """Open a specific assembly by ID"""
        try:
            assembly_data = self.assembly_manager.get_assembly_by_id(assembly_id)

            if not assembly_data:
                QMessageBox.warning(
                    self,
                    "Assembly Not Found",
                    f"Assembly with ID {assembly_id} not found."
                )
                return

            # Set current assembly
            self.current_assembly_id = assembly_id
            self.current_assembly_data = assembly_data
            self.current_assembly_path = self.assembly_manager.get_assembly_path(assembly_id)

            # Update UI
            self._select_assembly_in_combo(assembly_id)
            self._update_assembly_ui_state()

            # Emit signal
            self.assembly_opened.emit(assembly_id, assembly_data)

            logger.info(f"✅ Opened assembly: {assembly_data['name']} (ID: {assembly_id})")

        except Exception as e:
            logger.error(f"❌ Error opening assembly {assembly_id}: {e}")
            QMessageBox.critical(
                self,
                "Open Assembly Failed",
                f"Failed to open assembly:\n{str(e)}"
            )

    def close_current_assembly(self):
        """Close the currently open assembly"""
        if self.current_assembly_id is None:
            return

        # Clear current assembly state
        self.current_assembly_id = None
        self.current_assembly_data = None
        self.current_assembly_path = None

        # Update UI
        self.assembly_selector.setCurrentIndex(0)  # "No Assembly" option
        self._update_assembly_ui_state()

        # Emit signal
        self.assembly_closed.emit()

        logger.info("✅ Closed current assembly")

    def show_assembly_properties(self):
        """Show properties dialog for current assembly"""
        if not self.current_assembly_data:
            return

        dialog = AssemblyPropertiesDialog(self, self.current_assembly_data)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_updated_data()

            # Update assembly
            success = self.assembly_manager.update_assembly(
                self.current_assembly_id,
                updated_data
            )

            if success:
                # Refresh current data
                self.current_assembly_data = self.assembly_manager.get_assembly_by_id(
                    self.current_assembly_id
                )

                # Refresh UI
                self._refresh_assembly_selector()
                self._select_assembly_in_combo(self.current_assembly_id)

                QMessageBox.information(
                    self,
                    "Properties Updated",
                    "Assembly properties have been updated successfully."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Update Failed",
                    "Failed to update assembly properties."
                )

    def add_documents_to_assembly(self):
        """Add documents to the current assembly"""
        if not self.current_assembly_id:
            QMessageBox.warning(
                self,
                "No Assembly Selected",
                "Please select an assembly first."
            )
            return

        # This will be implemented when document import is ready
        QMessageBox.information(
            self,
            "Feature Coming Soon",
            "Document import functionality will be implemented next."
        )

    def _refresh_assembly_selector(self):
        """Refresh the assembly selector combo box"""
        try:
            self.assembly_selector.clear()

            # Add "No Assembly" option
            self.assembly_selector.addItem("No Assembly Selected", None)

            # Add all assemblies
            assemblies = self.assembly_manager.get_all_assemblies()
            for assembly in assemblies:
                display_text = f"{assembly['name']} ({assembly['document_count']} docs)"
                self.assembly_selector.addItem(display_text, assembly['id'])

        except Exception as e:
            logger.error(f"❌ Error refreshing assembly selector: {e}")

    def _select_assembly_in_combo(self, assembly_id: int):
        """Select specific assembly in combo box"""
        for i in range(self.assembly_selector.count()):
            if self.assembly_selector.itemData(i) == assembly_id:
                self.assembly_selector.setCurrentIndex(i)
                break

    def _on_assembly_selected(self, index: int):
        """Handle assembly selection change"""
        assembly_id = self.assembly_selector.itemData(index)

        if assembly_id is None:
            # "No Assembly" selected
            self.close_current_assembly()
        elif assembly_id != self.current_assembly_id:
            # Different assembly selected
            self.open_assembly_by_id(assembly_id)

    def _update_assembly_ui_state(self):
        """Update UI state based on current assembly"""
        has_assembly = self.current_assembly_id is not None

        # Enable/disable assembly-specific actions
        self.assembly_properties_action.setEnabled(has_assembly)
        self.close_assembly_action.setEnabled(has_assembly)
        self.add_documents_btn.setEnabled(has_assembly)

        # Update status bar if it exists
        if hasattr(self, 'statusbar'):
            if has_assembly:
                assembly_name = self.current_assembly_data.get('name', 'Unknown')
                doc_count = self.current_assembly_data.get('document_count', 0)
                self.statusbar.showMessage(
                    f"Assembly: {assembly_name} | Documents: {doc_count}"
                )
            else:
                self.statusbar.showMessage("No assembly selected")

    def _update_recent_assemblies_menu(self):
        """Update the recent assemblies menu"""
        if not hasattr(self, 'recent_assemblies_menu'):
            return

        try:
            self.recent_assemblies_menu.clear()

            recent_assemblies = self.assembly_manager.get_recent_assemblies(10)

            if not recent_assemblies:
                no_recent_action = QAction("No recent assemblies", self)
                no_recent_action.setEnabled(False)
                self.recent_assemblies_menu.addAction(no_recent_action)
                return

            for assembly in recent_assemblies:
                action_text = f"{assembly['name']} ({assembly['document_count']} docs)"
                action = QAction(action_text, self)
                action.setData(assembly['id'])
                action.triggered.connect(
                    lambda checked, aid=assembly['id']: self.open_assembly_by_id(aid)
                )
                self.recent_assemblies_menu.addAction(action)

        except Exception as e:
            logger.error(f"❌ Error updating recent assemblies menu: {e}")

    def get_current_assembly_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently open assembly"""
        if not self.current_assembly_data:
            return None

        return {
            "id": self.current_assembly_id,
            "name": self.current_assembly_data.get('name'),
            "path": self.current_assembly_path,
            "document_count": self.current_assembly_data.get('document_count', 0),
            "research_type": self.current_assembly_data.get('research_type'),
            "data": self.current_assembly_data
        }