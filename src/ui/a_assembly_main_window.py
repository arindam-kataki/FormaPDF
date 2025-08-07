# a_assembly_main_window.py
"""
Main Assembly Window for PDF Research Platform
Central hub for managing research assemblies with multiple documents
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QStatusBar, QMenuBar, QMenu, QMdiArea, QMdiSubWindow,
    QDockWidget, QSplitter, QTabWidget, QLabel, QPushButton, QToolButton,
    QFileDialog, QMessageBox, QProgressBar, QComboBox,
    QWidgetAction, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QSettings, QSize, QTimer, pyqtSignal, pyqtSlot,
    QThread, QObject, QPoint, QRect
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence, QCloseEvent,
    QDragEnterEvent, QDropEvent, QFont, QPixmap
)

# Import the separated document list widget
from a_document_list_widget import DocumentListWidget


class AssemblyMainWindow(QMainWindow):
    """
    Main window for managing research assemblies
    Central hub for document management, annotations, and AI integration
    """

    # Signals
    assembly_created = pyqtSignal(dict)  # Emits assembly data
    assembly_loaded = pyqtSignal(str)  # Emits assembly path
    assembly_saved = pyqtSignal(str)  # Emits assembly path
    document_opened = pyqtSignal(str)  # Emits document path

    def __init__(self):
        super().__init__()

        self.current_assembly = None
        self.current_assembly_id = None
        self.assembly_modified = False
        self.assembly_path = None

        # Initialize Assembly Manager (PostgreSQL connection)
        try:
            from a_assembly_manager import AssemblyManager
            self.assembly_manager = AssemblyManager()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Database Connection Error",
                f"Failed to connect to database:\n{str(e)}\n\n"
                "Please check your database configuration."
            )
            sys.exit(1)

        # Assembly management
        self.current_assembly = None
        self.current_assembly_id = None
        self.assembly_modified = False

        # Document management
        self.document_windows = {}  # path -> QMdiSubWindow
        self.active_document = None

        # Settings
        self.settings = QSettings("SYNAIPTIC", "PDFResearchPlatform")

        # Initialize UI
        self.init_ui()

        # Load recent assemblies from database
        try:
            self.load_recent_assemblies()
        except Exception as e:
            print(f"Exception Message: {str(e)}")

        # Setup auto-save
        self.setup_auto_save()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("SYNAIPTIC - PDF Research Platform")
        self.setGeometry(100, 100, 1400, 900)

        # Set application icon (if available)
        # self.setWindowIcon(QIcon("icons/app_icon.png"))

        # Apply application style
        self.apply_styles()

        # Create UI components
        self.create_menu_bar()
        self.create_toolbars()
        self.create_central_widget()
        self.create_dock_widgets()
        self.create_status_bar()

        # Restore window state
        self.restore_window_state()

    def apply_styles(self):
        """Apply application-wide styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QToolBar {
                background-color: #ffffff;
                border: none;
                border-bottom: 1px solid #ddd;
                padding: 5px;
                spacing: 3px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
                min-width: 80px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #ccc;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
            QStatusBar {
                background-color: #ffffff;
                border-top: 1px solid #ddd;
                padding: 2px;
            }
            QMdiArea {
                background-color: #e8e8e8;
            }
            QMdiArea QTabBar::tab {
                padding: 8px 12px;
                margin: 2px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
            }
            QMdiArea QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0066cc;
            }
        """)

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File Menu
        file_menu = self.create_file_menu(menubar)

        # Edit Menu
        edit_menu = self.create_edit_menu(menubar)

        # View Menu
        view_menu = self.create_view_menu(menubar)

        # Tools Menu
        tools_menu = self.create_tools_menu(menubar)

        # Window Menu
        window_menu = self.create_window_menu(menubar)

        # Help Menu
        help_menu = self.create_help_menu(menubar)

    def create_file_menu(self, menubar):
        """Create File menu"""
        file_menu = menubar.addMenu("&File")

        # New Assembly
        new_assembly_action = QAction("&New Assembly...", self)
        new_assembly_action.setShortcut(QKeySequence.StandardKey.New)
        new_assembly_action.setStatusTip("Create a new research assembly")
        new_assembly_action.triggered.connect(self.new_assembly)
        file_menu.addAction(new_assembly_action)

        # Open Assembly
        open_assembly_action = QAction("&Open Assembly...", self)
        open_assembly_action.setShortcut(QKeySequence.StandardKey.Open)
        open_assembly_action.setStatusTip("Open an existing assembly")
        open_assembly_action.triggered.connect(self.open_assembly)
        file_menu.addAction(open_assembly_action)

        # Recent Assemblies
        self.recent_menu = file_menu.addMenu("Recent Assemblies")

        file_menu.addSeparator()

        # Save Assembly
        self.save_assembly_action = QAction("&Save Assembly", self)
        self.save_assembly_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_assembly_action.setStatusTip("Save current assembly")
        self.save_assembly_action.triggered.connect(self.save_assembly)
        self.save_assembly_action.setEnabled(False)
        file_menu.addAction(self.save_assembly_action)

        # Save Assembly As
        self.save_as_action = QAction("Save Assembly &As...", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.setStatusTip("Save assembly with a new name")
        self.save_as_action.triggered.connect(self.save_assembly_as)
        self.save_as_action.setEnabled(False)
        file_menu.addAction(self.save_as_action)

        file_menu.addSeparator()

        # Import Documents
        self.import_docs_action = QAction("&Import Documents...", self)
        self.import_docs_action.setShortcut(QKeySequence("Ctrl+I"))
        self.import_docs_action.setStatusTip("Import documents to current assembly")
        self.import_docs_action.triggered.connect(self.import_documents)
        self.import_docs_action.setEnabled(False)
        file_menu.addAction(self.import_docs_action)

        # Export Assembly
        self.export_action = QAction("&Export Assembly...", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+E"))
        self.export_action.setStatusTip("Export assembly and documents")
        self.export_action.triggered.connect(self.export_assembly)
        self.export_action.setEnabled(False)
        file_menu.addAction(self.export_action)

        file_menu.addSeparator()

        # Close Assembly
        self.close_assembly_action = QAction("&Close Assembly", self)
        self.close_assembly_action.setShortcut(QKeySequence("Ctrl+W"))
        self.close_assembly_action.setStatusTip("Close current assembly")
        self.close_assembly_action.triggered.connect(self.close_current_assembly)
        self.close_assembly_action.setEnabled(False)
        file_menu.addAction(self.close_assembly_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        return file_menu

    def create_edit_menu(self, menubar):
        """Create Edit menu"""
        edit_menu = menubar.addMenu("&Edit")

        # Standard edit actions (to be implemented)
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setEnabled(False)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.setEnabled(False)
        edit_menu.addAction(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.setEnabled(False)
        edit_menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.setEnabled(False)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        # Find
        find_action = QAction("&Find...", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)

        # Preferences
        edit_menu.addSeparator()
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut(QKeySequence("Ctrl+,"))
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)

        return edit_menu

    def create_view_menu(self, menubar):
        """Create View menu"""
        view_menu = menubar.addMenu("&View")

        # Document panel toggle
        self.toggle_docs_action = QAction("&Document List", self)
        self.toggle_docs_action.setCheckable(True)
        self.toggle_docs_action.setChecked(True)
        self.toggle_docs_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self.toggle_docs_action.triggered.connect(self.toggle_document_panel)
        view_menu.addAction(self.toggle_docs_action)

        # Properties panel toggle (future)
        self.toggle_properties_action = QAction("&Properties Panel", self)
        self.toggle_properties_action.setCheckable(True)
        self.toggle_properties_action.setEnabled(False)
        view_menu.addAction(self.toggle_properties_action)

        view_menu.addSeparator()

        # Zoom actions
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.setEnabled(False)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.setEnabled(False)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("&Reset Zoom", self)
        zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_action.setEnabled(False)
        view_menu.addAction(zoom_reset_action)

        view_menu.addSeparator()

        # Full screen
        fullscreen_action = QAction("&Full Screen", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        return view_menu

    def create_tools_menu(self, menubar):
        """Create Tools menu"""
        tools_menu = menubar.addMenu("&Tools")

        # AI Chat
        ai_chat_action = QAction("&AI Chat Panel", self)
        ai_chat_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        ai_chat_action.setStatusTip("Open AI assistant chat panel")
        ai_chat_action.triggered.connect(self.show_ai_chat)
        tools_menu.addAction(ai_chat_action)

        # Search
        search_action = QAction("&Search Across Documents", self)
        search_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        search_action.setStatusTip("Search across all documents in assembly")
        search_action.triggered.connect(self.show_search)
        tools_menu.addAction(search_action)

        # Annotations Manager
        annotations_action = QAction("&Annotations Manager", self)
        annotations_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        annotations_action.setStatusTip("Manage all annotations")
        annotations_action.triggered.connect(self.show_annotations_manager)
        tools_menu.addAction(annotations_action)

        tools_menu.addSeparator()

        # Export Report
        export_report_action = QAction("Generate &Report...", self)
        export_report_action.setStatusTip("Generate research report")
        export_report_action.triggered.connect(self.generate_report)
        export_report_action.setEnabled(False)
        tools_menu.addAction(export_report_action)

        return tools_menu

    def create_window_menu(self, menubar):
        """Create Window menu"""
        window_menu = menubar.addMenu("&Window")

        # Window arrangement
        cascade_action = QAction("&Cascade", self)
        cascade_action.setStatusTip("Cascade document windows")
        cascade_action.triggered.connect(lambda: self.mdi_area.cascadeSubWindows())
        window_menu.addAction(cascade_action)

        tile_action = QAction("&Tile", self)
        tile_action.setStatusTip("Tile document windows")
        tile_action.triggered.connect(lambda: self.mdi_area.tileSubWindows())
        window_menu.addAction(tile_action)

        window_menu.addSeparator()

        # Close all
        close_all_action = QAction("Close &All Documents", self)
        close_all_action.setStatusTip("Close all open documents")
        close_all_action.triggered.connect(lambda: self.mdi_area.closeAllSubWindows())
        window_menu.addAction(close_all_action)

        window_menu.addSeparator()

        # Next/Previous window
        next_window_action = QAction("&Next Document", self)
        next_window_action.setShortcut(QKeySequence("Ctrl+Tab"))
        next_window_action.triggered.connect(lambda: self.mdi_area.activateNextSubWindow())
        window_menu.addAction(next_window_action)

        prev_window_action = QAction("&Previous Document", self)
        prev_window_action.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
        prev_window_action.triggered.connect(lambda: self.mdi_area.activatePreviousSubWindow())
        window_menu.addAction(prev_window_action)

        return window_menu

    def create_help_menu(self, menubar):
        """Create Help menu"""
        help_menu = menubar.addMenu("&Help")

        # Documentation
        docs_action = QAction("&Documentation", self)
        docs_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)

        # Keyboard shortcuts
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        # About
        about_action = QAction("&About SYNAIPTIC", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        about_qt_action = QAction("About &Qt", self)
        about_qt_action.triggered.connect(QApplication.aboutQt)
        help_menu.addAction(about_qt_action)

        return help_menu

    def create_toolbars(self):
        """Create application toolbars"""
        # Main toolbar
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setObjectName("MainToolbar")  # For state saving
        main_toolbar.setMovable(False)

        # Assembly operations
        self.create_assembly_toolbar_actions(main_toolbar)

        main_toolbar.addSeparator()

        # Document operations
        self.create_document_toolbar_actions(main_toolbar)

        main_toolbar.addSeparator()

        # Tools
        self.create_tools_toolbar_actions(main_toolbar)

        # Add spring to push remaining items to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_toolbar.addWidget(spacer)

        # View mode selector
        self.create_view_mode_selector(main_toolbar)

    def create_assembly_toolbar_actions(self, toolbar):
        """Create assembly-related toolbar actions"""
        # New Assembly
        new_btn = QToolButton()
        new_btn.setText("➕ New")
        new_btn.setToolTip("Create a new research assembly (Ctrl+N)")
        new_btn.clicked.connect(self.new_assembly)
        toolbar.addWidget(new_btn)

        # Open Assembly
        open_btn = QToolButton()
        open_btn.setText("📁 Open")
        open_btn.setToolTip("Open an existing assembly (Ctrl+O)")
        open_btn.clicked.connect(self.open_assembly)
        toolbar.addWidget(open_btn)

        # Save Assembly
        self.save_btn = QToolButton()
        self.save_btn.setText("💾 Save")
        self.save_btn.setToolTip("Save current assembly (Ctrl+S)")
        self.save_btn.clicked.connect(self.save_assembly)
        self.save_btn.setEnabled(False)
        toolbar.addWidget(self.save_btn)

    def create_document_toolbar_actions(self, toolbar):
        """Create document-related toolbar actions"""
        # Import Documents
        self.import_btn = QToolButton()
        self.import_btn.setText("📥 Import")
        self.import_btn.setToolTip("Import documents to assembly (Ctrl+I)")
        self.import_btn.clicked.connect(self.import_documents)
        self.import_btn.setEnabled(False)
        toolbar.addWidget(self.import_btn)

        # Remove Documents
        self.remove_btn = QToolButton()
        self.remove_btn.setText("🗑️ Remove")
        self.remove_btn.setToolTip("Remove selected documents")
        self.remove_btn.clicked.connect(self.remove_selected_documents)
        self.remove_btn.setEnabled(False)
        toolbar.addWidget(self.remove_btn)

    def create_tools_toolbar_actions(self, toolbar):
        """Create tools toolbar actions"""
        # AI Chat
        ai_btn = QToolButton()
        ai_btn.setText("🤖 AI")
        ai_btn.setToolTip("Open AI chat panel (Ctrl+Shift+A)")
        ai_btn.clicked.connect(self.show_ai_chat)
        toolbar.addWidget(ai_btn)

        # Search
        search_btn = QToolButton()
        search_btn.setText("🔍 Search")
        search_btn.setToolTip("Search across all documents (Ctrl+Shift+F)")
        search_btn.clicked.connect(self.show_search)
        toolbar.addWidget(search_btn)

        # Annotations
        annotations_btn = QToolButton()
        annotations_btn.setText("📝 Notes")
        annotations_btn.setToolTip("Manage annotations (Ctrl+Shift+N)")
        annotations_btn.clicked.connect(self.show_annotations_manager)
        toolbar.addWidget(annotations_btn)

    def create_view_mode_selector(self, toolbar):
        """Create view mode selector for toolbar"""
        toolbar.addWidget(QLabel("View:"))

        self.view_combo = QComboBox()
        self.view_combo.addItems(["Tabs", "Windows", "Split"])
        self.view_combo.setToolTip("Document view mode")
        self.view_combo.currentTextChanged.connect(self.change_view_mode)
        toolbar.addWidget(self.view_combo)

    def create_central_widget(self):
        """Create central widget with MDI area"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # MDI Area for document windows
        self.mdi_area = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
        self.mdi_area.setTabsClosable(True)
        self.mdi_area.setTabsMovable(True)
        self.mdi_area.setDocumentMode(True)

        layout.addWidget(self.mdi_area)

        # Connect MDI signals
        self.mdi_area.subWindowActivated.connect(self.on_document_activated)

    def create_dock_widgets(self):
        """Create dockable panels"""
        # Document List Dock
        self.doc_list_dock = QDockWidget("Assembly Documents", self)
        self.doc_list_dock.setObjectName("DocumentListDock")  # For state saving
        self.doc_list_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Create document list widget
        self.document_list = DocumentListWidget()
        self.document_list.document_opened.connect(self.open_document)
        self.document_list.document_removed.connect(self.remove_document)
        self.document_list.document_properties_requested.connect(self.show_document_properties)

        self.doc_list_dock.setWidget(self.document_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.doc_list_dock)

        # Make dock collapsible
        self.doc_list_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        # Connect visibility toggle
        self.doc_list_dock.visibilityChanged.connect(
            lambda visible: self.toggle_docs_action.setChecked(visible)
        )

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Assembly name label
        self.assembly_label = QLabel("No Assembly Loaded")
        self.assembly_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.status_bar.addWidget(self.assembly_label)

        # Separator
        self.status_bar.addWidget(QLabel(" | "))

        # Document count label
        self.doc_count_label = QLabel("0 documents")
        self.status_bar.addWidget(self.doc_count_label)

        # Separator
        self.status_bar.addWidget(QLabel(" | "))

        # Annotation count label
        self.annotation_count_label = QLabel("0 annotations")
        self.status_bar.addWidget(self.annotation_count_label)

        # Add stretch to push remaining items to the right
        self.status_bar.addPermanentWidget(QWidget(), 1)

        # AI status
        self.ai_status_label = QLabel("🤖 AI: Not Connected")
        self.status_bar.addPermanentWidget(self.ai_status_label)

        # Separator
        self.status_bar.addPermanentWidget(QLabel(" | "))

        # Last saved label
        self.last_saved_label = QLabel("Not Saved")
        self.status_bar.addPermanentWidget(self.last_saved_label)

    # ============================================================================
    # Assembly Management Methods (FIXED)
    # ============================================================================

    def new_assembly(self):
        """Create a new research assembly"""
        # Import here to avoid circular imports
        try:
            from ui.a_assembly_dialog import AssemblyDialog
        except ImportError:
            # If AssemblyDialog is not available, show a simple dialog
            from PyQt6.QtWidgets import QInputDialog, QMessageBox

            name, ok = QInputDialog.getText(
                self,
                "New Assembly",
                "Enter assembly name:",
                text="New Research Assembly"
            )

            if ok and name:
                # Create basic assembly structure
                self.current_assembly = {
                    'name': name,
                    'description': '',
                    'researcher': '',
                    'keywords': [],
                    'documents': []
                }
                self.current_assembly_id = 1  # Simple ID for now
                self.assembly_modified = False

                # Update UI
                self.update_ui_state()

                # Show success message
                QMessageBox.information(
                    self,
                    "Assembly Created",
                    f"Assembly '{name}' has been created.\nYou can now import documents."
                )

                # Emit signal if it exists
                if hasattr(self, 'assembly_created'):
                    self.assembly_created.emit(self.current_assembly)
            return

        # Use the full dialog if available
        dialog = AssemblyDialog(self)
        dialog.assembly_created.connect(self._on_assembly_created)

        if dialog.exec():
            print("Assembly dialog completed")

    def _on_assembly_created(self, assembly_data):
        """Handle assembly creation from dialog"""
        # Create the assembly
        self.current_assembly = assembly_data
        self.current_assembly_id = 1  # Simple ID for now
        self.assembly_modified = False

        # Update UI
        self.update_ui_state()

        # Emit signal
        if hasattr(self, 'assembly_created'):
            self.assembly_created.emit(self.current_assembly)

        # Show success message
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Assembly Created",
            f"Assembly '{assembly_data.get('name', 'Unnamed')}' has been created successfully."
        )

    def save_assembly_as(self):
        """Save assembly with a new name"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        if not self.current_assembly:
            QMessageBox.warning(
                self,
                "No Assembly",
                "No assembly to save. Please create an assembly first."
            )
            return

        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Assembly files (*.asmb);;All files (*.*)")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix("asmb")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            # For now, just show a message
            QMessageBox.information(
                self,
                "Save Assembly",
                f"Assembly would be saved to:\n{file_path}\n\n(Database implementation pending)"
            )

    def update_ui_state(self):
        """Update UI elements based on current state"""
        has_assembly = self.current_assembly is not None

        # Enable/disable actions based on assembly state
        if hasattr(self, 'save_assembly_action'):
            self.save_assembly_action.setEnabled(has_assembly)
        if hasattr(self, 'save_as_action'):
            self.save_as_action.setEnabled(has_assembly)
        if hasattr(self, 'save_btn'):
            self.save_btn.setEnabled(has_assembly)
        if hasattr(self, 'import_btn'):
            self.import_btn.setEnabled(has_assembly)

        # Update status bar
        if hasattr(self, 'assembly_label'):
            if has_assembly:
                name = self.current_assembly.get('name', 'Unnamed Assembly')
                self.assembly_label.setText(f"Assembly: {name}")
            else:
                self.assembly_label.setText("No Assembly Loaded")

        # Update document count
        if hasattr(self, 'doc_count_label'):
            doc_count = len(self.current_assembly.get('documents', [])) if has_assembly else 0
            self.doc_count_label.setText(f"{doc_count} documents")

    def setup_auto_save(self):
        """Setup auto-save timer"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_assembly)
        self.auto_save_timer.start(300000)  # Auto-save every 5 minutes

        #self.assembly_path = None
        #self.assembly_modified = True
        #self.update_ui_state()

        #self.assembly_created.emit(self.current_assembly)



    def open_assembly(self):
        """Open an existing assembly"""
        if not self.check_save_current_assembly():
            return

        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Assembly files (*.asmb);;All files (*.*)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setWindowTitle("Open Assembly")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.load_assembly(file_path)

    def load_assembly(self, file_path: str):
        """Load an assembly from database"""
        try:
            # Close current assembly first
            self.close_current_assembly()

            # Load from database via manager
            self.current_assembly = self.assembly_manager.load_assembly(file_path)
            self.current_assembly_id = self.current_assembly['id']
            self.assembly_modified = False

            # Load documents into list
            for doc in self.current_assembly.get('documents', []):
                self.document_list.add_document(
                    doc['file_path'],
                    {
                        'pages': doc.get('page_count', '-'),
                        'annotations': doc.get('annotation_count', 0)
                    }
                )

            # Add to recent assemblies
            self.add_to_recent_assemblies(file_path)

            self.update_ui_state()

            self.assembly_loaded.emit(file_path)

            self.status_bar.showMessage(
                f"Loaded assembly: {self.current_assembly.get('name', 'Unnamed')} "
                f"({len(self.current_assembly.get('documents', []))} documents)",
                3000
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Assembly",
                f"Failed to load assembly from database:\n{str(e)}"
            )

    def save_assembly(self):
        """Save current assembly to database"""
        if not self.current_assembly or not self.current_assembly_id:
            return

        try:
            # Prepare updates
            updates = {
                'name': self.current_assembly.get('name'),
                'description': self.current_assembly.get('description'),
                'researcher': self.current_assembly.get('researcher'),
                'keywords': self.current_assembly.get('keywords', [])
            }

            # Update in database
            self.assembly_manager.update_assembly(self.current_assembly_id, updates)

            self.assembly_modified = False
            self.last_saved_label.setText(f"Saved: {datetime.now().strftime('%H:%M')}")

            self.assembly_saved.emit(str(self.current_assembly_id))

            self.status_bar.showMessage("Assembly saved to database", 2000)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save assembly to database:\n{str(e)}"
            )

    def save_assembly_as(self):
        """Save assembly with new name - not typically needed with database approach"""
        if not self.current_assembly:
            return

        # In a database-driven system, this would typically create a copy
        # For now, just show a message
        QMessageBox.information(
            self,
            "Save As",
            "In the database-driven system, assemblies are automatically saved.\n\n"
            "To create a copy of an assembly, use the 'Duplicate Assembly' feature (coming soon)."
        )

    def export_assembly(self):
        """Export assembly with all documents"""
        if not self.current_assembly or not self.current_assembly_id:
            return

        # TODO: Implement assembly export with documents
        QMessageBox.information(
            self,
            "Export Assembly",
            "Assembly export functionality coming soon!\n\n"
            "This will export the assembly and all documents to a portable format."
        )

    def close_current_assembly(self):
        """Close the current assembly"""
        # Close all document windows
        self.mdi_area.closeAllSubWindows()
        self.document_windows.clear()

        # Clear document list
        self.document_list.clear_all()

        # Reset assembly data
        self.current_assembly = None
        self.current_assembly_id = None
        self.assembly_modified = False

        self.update_ui_state()

    def check_save_current_assembly(self) -> bool:
        """
        Check if current assembly needs saving

        Returns:
            True if OK to proceed, False to cancel
        """
        if self.assembly_modified:
            reply = QMessageBox.question(
                self,
                "Save Assembly?",
                "Current assembly has unsaved changes. Save before continuing?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                self.save_assembly()
                return True
            elif reply == QMessageBox.StandardButton.Discard:
                return True
            else:  # Cancel
                return False
        return True

    def auto_save_assembly(self):
        """Auto-save assembly if modified"""
        if self.assembly_modified and self.current_assembly_id:
            try:
                self.save_assembly()
                self.status_bar.showMessage("Auto-saved", 2000)
            except Exception as e:
                print(f"Auto-save failed: {e}")

    # ============================================================================
    # Document Management Methods
    # ============================================================================

    def import_documents(self):
        """Import documents into current assembly"""
        if not self.current_assembly or not self.current_assembly_id:
            QMessageBox.warning(
                self,
                "No Assembly",
                "Please create or open an assembly first.\n\n"
                "An assembly can exist without documents - you can add them anytime."
            )
            return

        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter(
            "All Documents (*.pdf *.docx *.doc *.xlsx *.xls *.txt *.md *.jpg *.png);;"
            "PDF files (*.pdf);;"
            "Word files (*.docx *.doc);;"
            "Excel files (*.xlsx *.xls);;"
            "Text files (*.txt *.md);;"
            "Images (*.jpg *.jpeg *.png *.gif *.bmp);;"
            "All files (*.*)"
        )
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setWindowTitle("Import Documents to Assembly")

        if file_dialog.exec():
            files = file_dialog.selectedFiles()

            # Progress dialog for multiple files
            progress = None
            if len(files) > 1:
                from PyQt6.QtWidgets import QProgressDialog
                progress = QProgressDialog(
                    "Importing documents...",
                    "Cancel",
                    0,
                    len(files),
                    self
                )
                progress.setWindowModality(Qt.WindowModality.WindowModal)

            imported_count = 0
            failed_files = []

            for i, file_path in enumerate(files):
                if progress:
                    progress.setValue(i)
                    progress.setLabelText(f"Importing: {Path(file_path).name}")
                    if progress.wasCanceled():
                        break

                try:
                    # Add to database via manager
                    doc_id = self.assembly_manager.add_document(
                        self.current_assembly_id,
                        file_path,
                        copy_to_assembly=True  # Copy to assembly folder
                    )

                    # Add to document list UI
                    self.document_list.add_document(file_path)
                    imported_count += 1

                except Exception as e:
                    failed_files.append((Path(file_path).name, str(e)))

            if progress:
                progress.setValue(len(files))

            # Reload assembly to get updated counts
            self.current_assembly = self.assembly_manager.load_assembly(str(self.current_assembly_id))
            self.update_ui_state()

            # Show results
            if failed_files:
                error_msg = "\n".join([f"• {name}: {error}" for name, error in failed_files])
                QMessageBox.warning(
                    self,
                    "Import Completed with Errors",
                    f"Imported {imported_count} of {len(files)} documents.\n\n"
                    f"Failed to import:\n{error_msg}"
                )
            else:
                self.status_bar.showMessage(
                    f"Successfully imported {imported_count} document{'s' if imported_count != 1 else ''}",
                    3000
                )

    def remove_selected_documents(self):
        """Remove selected documents from assembly"""
        self.document_list.remove_selected_documents()
        self.assembly_modified = True
        self.update_ui_state()

    def remove_document(self, file_path: str):
        """Remove a document from the assembly"""
        # Close window if open
        if file_path in self.document_windows:
            window = self.document_windows[file_path]
            window.close()
            del self.document_windows[file_path]

        self.assembly_modified = True
        self.update_ui_state()

    def open_document(self, file_path: str):
        """Open a document in the MDI area"""
        # Check if already open
        if file_path in self.document_windows:
            # Activate existing window
            window = self.document_windows[file_path]
            self.mdi_area.setActiveSubWindow(window)
            return

        # Create new document window
        # TODO: Create actual document viewer based on file type
        doc_widget = QLabel(f"Document Viewer\n\n{file_path}\n\n(Viewer implementation pending)")
        doc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        doc_widget.setStyleSheet("""
            QLabel { 
                background-color: white; 
                border: 1px solid #ccc;
                font-size: 14px;
                padding: 20px;
            }
        """)

        # Create MDI sub-window
        sub_window = self.mdi_area.addSubWindow(doc_widget)
        sub_window.setWindowTitle(Path(file_path).name)
        sub_window.showMaximized()

        # Track open window
        self.document_windows[file_path] = sub_window

        # Connect close signal
        sub_window.destroyed.connect(lambda: self.on_document_closed(file_path))

        self.document_opened.emit(file_path)

    def on_document_closed(self, file_path: str):
        """Handle document window closure"""
        if file_path in self.document_windows:
            del self.document_windows[file_path]

    def on_document_activated(self, window: QMdiSubWindow):
        """Handle document window activation"""
        if window:
            self.active_document = window
            # TODO: Update UI based on active document

    def show_document_properties(self, file_path: str):
        """Show document properties dialog"""
        # TODO: Implement document properties dialog
        QMessageBox.information(
            self,
            "Document Properties",
            f"Properties for:\n{file_path}\n\n(Coming soon)"
        )

    # ============================================================================
    # UI State Management
    # ============================================================================

    def update_ui_state(self):
        """Update UI elements based on current state"""
        has_assembly = self.current_assembly is not None

        # Update actions
        self.save_assembly_action.setEnabled(has_assembly)
        self.save_as_action.setEnabled(has_assembly)
        self.close_assembly_action.setEnabled(has_assembly)
        self.import_docs_action.setEnabled(has_assembly)
        self.export_action.setEnabled(has_assembly)

        # Update toolbar buttons
        self.save_btn.setEnabled(has_assembly)
        self.import_btn.setEnabled(has_assembly)
        self.remove_btn.setEnabled(has_assembly)

        if self.current_assembly:
            # Update status bar
            self.assembly_label.setText(f"📁 {self.current_assembly.get('name', 'Unnamed')}")

            doc_count = self.document_list.get_document_count()
            self.doc_count_label.setText(f"{doc_count} document{'s' if doc_count != 1 else ''}")

            # TODO: Get actual annotation count
            self.annotation_count_label.setText("0 annotations")

            # Update window title
            title = f"SYNAIPTIC - {self.current_assembly.get('name', 'Unnamed')}"
            if self.assembly_modified:
                title += " *"
            self.setWindowTitle(title)
        else:
            self.assembly_label.setText("No Assembly Loaded")
            self.doc_count_label.setText("0 documents")
            self.annotation_count_label.setText("0 annotations")
            self.setWindowTitle("SYNAIPTIC - PDF Research Platform")

    # ============================================================================
    # View Management
    # ============================================================================

    def toggle_document_panel(self, checked: bool):
        """Toggle document list panel visibility"""
        self.doc_list_dock.setVisible(checked)

    def change_view_mode(self, mode: str):
        """Change MDI area view mode"""
        if mode == "Tabs":
            self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
        elif mode == "Windows":
            self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
        elif mode == "Split":
            # TODO: Implement split view
            pass

    def toggle_fullscreen(self, checked: bool):
        """Toggle fullscreen mode"""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()

    # ============================================================================
    # Tool Windows and Dialogs
    # ============================================================================

    def show_ai_chat(self):
        """Show AI chat panel"""
        # TODO: Implement AI chat panel
        QMessageBox.information(
            self,
            "AI Assistant",
            "AI Chat panel implementation coming soon!\n\n"
            "This will provide:\n"
            "• Context-aware AI assistance\n"
            "• Document Q&A\n"
            "• Cross-document analysis\n"
            "• Research insights"
        )

    def show_search(self):
        """Show search panel"""
        # TODO: Implement search functionality
        QMessageBox.information(
            self,
            "Search",
            "Search functionality coming soon!\n\n"
            "Features will include:\n"
            "• Text search across all documents\n"
            "• Semantic search using AI\n"
            "• Search within annotations\n"
            "• Advanced filters"
        )

    def show_annotations_manager(self):
        """Show annotations manager"""
        # TODO: Implement annotations manager
        QMessageBox.information(
            self,
            "Annotations Manager",
            "Annotations manager coming soon!\n\n"
            "Manage all annotations across documents"
        )

    def show_find_dialog(self):
        """Show find dialog"""
        # TODO: Implement find dialog
        pass

    def show_preferences(self):
        """Show preferences dialog"""
        # TODO: Implement preferences dialog
        QMessageBox.information(
            self,
            "Preferences",
            "Preferences dialog coming soon!"
        )

    def generate_report(self):
        """Generate research report"""
        # TODO: Implement report generation
        QMessageBox.information(
            self,
            "Generate Report",
            "Report generation coming soon!"
        )

    def show_documentation(self):
        """Show documentation"""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation will be available soon!"
        )

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table>
        <tr><td><b>Ctrl+N</b></td><td>New Assembly</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Open Assembly</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save Assembly</td></tr>
        <tr><td><b>Ctrl+I</b></td><td>Import Documents</td></tr>
        <tr><td><b>Ctrl+W</b></td><td>Close Assembly</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Exit Application</td></tr>
        <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td><b>Ctrl+Shift+A</b></td><td>AI Chat Panel</td></tr>
        <tr><td><b>Ctrl+Shift+F</b></td><td>Search Documents</td></tr>
        <tr><td><b>Ctrl+Shift+N</b></td><td>Annotations Manager</td></tr>
        <tr><td><b>Ctrl+Shift+D</b></td><td>Toggle Document List</td></tr>
        <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
        <tr><td><b>Ctrl+Tab</b></td><td>Next Document</td></tr>
        <tr><td><b>Ctrl+Shift+Tab</b></td><td>Previous Document</td></tr>
        <tr><td><b>F11</b></td><td>Toggle Fullscreen</td></tr>
        </table>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(shortcuts_text)
        msg.exec()

    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>SYNAIPTIC PDF Research Platform</h2>
        <p><b>Version 1.0.0</b></p>
        <p>A comprehensive document research and annotation platform<br>
        with AI-powered analysis capabilities.</p>
        <p>Features:</p>
        <ul>
        <li>Multi-document assembly management</li>
        <li>Support for PDF, Word, Excel, and more</li>
        <li>AI-powered document analysis</li>
        <li>Cross-document search and insights</li>
        <li>Annotation and note-taking system</li>
        </ul>
        <p>© 2024 SYNAIPTIC. All rights reserved.</p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("About SYNAIPTIC")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.setIconPixmap(QPixmap())  # Add logo here if available
        msg.exec()

    # ============================================================================
    # Recent Assemblies Management
    # ============================================================================

    def load_recent_assemblies(self):
        """Load recent assemblies list from database"""
        try:
            # Get recent assemblies from database
            recent_assemblies = self.assembly_manager.get_recent_assemblies(10)

            self.recent_menu.clear()

            if not recent_assemblies:
                action = QAction("(No recent assemblies)", self)
                action.setEnabled(False)
                self.recent_menu.addAction(action)
            else:
                for i, assembly in enumerate(recent_assemblies, 1):
                    # Create menu text with shortcut
                    if i <= 9:
                        text = f"&{i}. {assembly['name']}"
                    else:
                        text = f"1&0. {assembly['name']}"

                    action = QAction(text, self)
                    action.setData(assembly['id'])  # Store assembly ID

                    # Create tooltip with details
                    tooltip = f"Name: {assembly['name']}\n"
                    tooltip += f"Documents: {assembly['document_count']}\n"
                    tooltip += f"Modified: {assembly['modified'][:10]}"
                    action.setToolTip(tooltip)

                    # Connect to load assembly
                    action.triggered.connect(
                        lambda checked, aid=assembly['id']: self.load_assembly(str(aid))
                    )
                    self.recent_menu.addAction(action)

                self.recent_menu.addSeparator()

                # Add clear recent action
                clear_action = QAction("Clear Recent", self)
                clear_action.triggered.connect(self.clear_recent_assemblies)
                self.recent_menu.addAction(clear_action)

        except Exception as e:
            print(f"Error loading recent assemblies: {e}")

    def add_to_recent_assemblies(self, file_path: str):
        """Add assembly to recent list"""
        recent = self.settings.value("recent_assemblies", [])

        # Remove if already in list
        if file_path in recent:
            recent.remove(file_path)

        # Add to front
        recent.insert(0, file_path)

        # Keep only last 10
        recent = recent[:10]

        self.settings.setValue("recent_assemblies", recent)

        try:
            self.load_recent_assemblies()
        except Exception as e:
            print(f"Exception Message: {str(e)}")

    def clear_recent_assemblies(self):
        """Clear recent assemblies list"""
        self.settings.setValue("recent_assemblies", [])
        try:
            self.load_recent_assemblies()
        except Exception as e:
            print(f"Exception Message: {str(e)}")

    # Window State Management
    def restore_window_state(self):
        """Restore window geometry and state"""
        geometry = self.settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)

        state = self.settings.value("window_state")
        if state:
            self.restoreState(state)

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        # Check for unsaved changes
        if not self.check_save_current_assembly():
            event.ignore()
            return

        # Save window state
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())

        # Stop auto-save timer
        self.auto_save_timer.stop()

        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("SYNAIPTIC")
    app.setOrganizationName("SYNAIPTIC")
    app.setApplicationDisplayName("PDF Research Platform")

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    window = AssemblyMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()