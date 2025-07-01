# Project Management Mixin
# File: src/ui/project_management_mixin.py

"""
Project Management Mixin
Separates all project management functionality from the main window
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QMenuBar, QMenu, QFileDialog, QMessageBox, QDialog, QApplication
)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# Import project management classes (with safe fallbacks)
try:
    from models.project import ProjectManager, ProjectInfo
    from ui.project_dialogs import NewProjectDialog, RecentProjectsDialog, ProjectPropertiesDialog

    PROJECT_MANAGEMENT_AVAILABLE = True
except ImportError:
    print("Warning: Project management not available - running without project features")
    PROJECT_MANAGEMENT_AVAILABLE = False
    ProjectManager = None
    ProjectInfo = None
    NewProjectDialog = None
    RecentProjectsDialog = None
    ProjectPropertiesDialog = None


class ProjectManagementMixin:
    """
    Mixin class that adds project management functionality to any QMainWindow

    This mixin adds:
    - Project creation, opening, saving
    - Recent projects management
    - Auto-save functionality
    - Project-aware UI state management

    Usage:
        class MyMainWindow(QMainWindow, ProjectManagementMixin):
            def __init__(self):
                super().__init__()
                self.init_project_management()
    """

    # Project management signals
    project_created = pyqtSignal(str)  # project_path
    project_opened = pyqtSignal(str, dict)  # project_path, project_data
    project_saved = pyqtSignal(str)  # project_path
    project_closed = pyqtSignal()
    project_modified_changed = pyqtSignal(bool)  # is_modified

    def init_project_management(self):
        """Initialize project management - call this in your main window's __init__"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            self._init_project_management_disabled()
            return

        # Project management attributes
        self.project_manager = ProjectManager()
        self.current_project_path = None
        self.current_project_data = None
        self.project_modified = False

        # Store references to project-specific UI actions (set by main window)
        self.project_toolbar_actions = []

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_project)
        self.auto_save_timer.start(300000)  # Auto-save every 5 minutes

        # Connect signals
        self.setup_project_signals()

    def _init_project_management_disabled(self):
        """Initialize with project management disabled"""
        self.project_manager = None
        self.current_project_path = None
        self.current_project_data = None
        self.project_modified = False
        self.project_toolbar_actions = []

    def setup_project_signals(self):
        """Setup internal project management signals"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            return

        self.project_created.connect(self._on_project_created)
        self.project_opened.connect(self._on_project_opened)
        self.project_saved.connect(self._on_project_saved)
        self.project_closed.connect(self._on_project_closed)
        self.project_modified_changed.connect(self._on_project_modified_changed)

    # =========================
    # PROJECT MENU CREATION
    # =========================

    def create_project_menu_items(self, file_menu: QMenu):
        """Add project management items to an existing File menu"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            return self._create_basic_file_menu_items(file_menu)

        # New Project
        new_project_action = QAction("&New Project...", self)
        new_project_action.setShortcut(QKeySequence.StandardKey.New)
        new_project_action.setStatusTip("Create a new project")
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        # Open Project
        open_project_action = QAction("&Open Project...", self)
        open_project_action.setShortcut(QKeySequence.StandardKey.Open)
        open_project_action.setStatusTip("Open an existing project")
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        # Open Recent submenu
        self.recent_menu = QMenu("Open &Recent", self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()

        file_menu.addSeparator()

        # Open PDF (legacy support)
        open_pdf_action = QAction("Open &PDF Only...", self)
        open_pdf_action.setShortcut("Ctrl+Shift+O")
        open_pdf_action.setStatusTip("Open PDF file without project")
        open_pdf_action.triggered.connect(self.open_pdf_legacy)
        file_menu.addAction(open_pdf_action)

        file_menu.addSeparator()

        # Save Project
        self.save_project_action = QAction("&Save Project", self)
        self.save_project_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_project_action.setStatusTip("Save the current project")
        self.save_project_action.triggered.connect(self.save_project)
        self.save_project_action.setEnabled(False)
        file_menu.addAction(self.save_project_action)

        # Save Project As
        self.save_as_action = QAction("Save Project &As...", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.setStatusTip("Save the project with a new name")
        self.save_as_action.triggered.connect(self.save_project_as)
        self.save_as_action.setEnabled(False)
        file_menu.addAction(self.save_as_action)

        file_menu.addSeparator()

        # Close Project
        self.close_project_action = QAction("&Close Project", self)
        self.close_project_action.setShortcut("Ctrl+W")
        self.close_project_action.setStatusTip("Close the current project")
        self.close_project_action.triggered.connect(self.close_project)
        self.close_project_action.setEnabled(False)
        file_menu.addAction(self.close_project_action)

        file_menu.addSeparator()

        # Project Properties
        self.properties_action = QAction("Project &Properties...", self)
        self.properties_action.setStatusTip("View and edit project properties")
        self.properties_action.triggered.connect(self.show_project_properties)
        self.properties_action.setEnabled(False)
        file_menu.addAction(self.properties_action)

    def _create_basic_file_menu_items(self, file_menu: QMenu):
        """Create basic file menu items when project management is not available"""
        open_action = QAction("&Open PDF...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_pdf_legacy)
        file_menu.addAction(open_action)

        save_action = QAction("&Save Form Data...", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_form_data_legacy)
        file_menu.addAction(save_action)

    def create_project_toolbar_actions(self, toolbar):
        """Add project management actions to an existing toolbar"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            return self._create_basic_toolbar_actions(toolbar)

        # New Project
        new_action = QAction("📄 New", self)
        new_action.setToolTip("Create new project (Ctrl+N)")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)

        # Open Project
        open_action = QAction("📁 Open", self)
        open_action.setToolTip("Open project (Ctrl+O)")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        toolbar.addAction(open_action)

        # Arindam Save Project
        self.save_action = QAction("💾 Save", self)
        self.save_action.setToolTip("Save project (Ctrl+S)")
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_project)
        #self.save_action.setEnabled(False)
        toolbar.addAction(self.save_action)

        return [self.save_action]  # Return actions that should be managed by project state

    def _create_basic_toolbar_actions(self, toolbar):
        """Create basic toolbar actions when project management is not available"""
        open_action = QAction("📁 Open PDF", self)
        open_action.setToolTip("Open PDF file")
        open_action.triggered.connect(self.open_pdf_legacy)
        toolbar.addAction(open_action)

        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save form data")
        save_action.triggered.connect(self.save_form_data_legacy)
        toolbar.addAction(save_action)

        return []  # No project-managed actions

    # =========================
    # PROJECT OPERATIONS
    # =========================

    def new_project(self):
        """Create a new project"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            QMessageBox.warning(self, "Feature Not Available",
                                "Project management is not available.")
            return

        if not self.check_save_current_project():
            return

        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_data = dialog.get_project_data()

            try:
                # Create project info
                project_info = ProjectInfo(
                    name=project_data["name"],
                    pdf_path=project_data["pdf_path"],
                    created_date=datetime.now().isoformat(),
                    modified_date=datetime.now().isoformat(),
                    author=project_data["author"],
                    description=project_data["description"]
                )

                # Create the project
                project_path = self.project_manager.create_project(
                    pdf_path=project_data["pdf_path"],
                    project_path=project_data["project_path"],
                    project_info=project_info
                )

                # Load the new project
                project_data = self.project_manager.open_project(project_path)
                self.load_project(project_path, project_data)

                self.project_created.emit(project_path)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create project:\n{str(e)}")

    def open_project(self):
        """Open an existing project"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            self.open_pdf_legacy()
            return

        if not self.check_save_current_project():
            return

        # Show recent projects dialog first
        recent_projects = self.project_manager.get_recent_projects()

        if recent_projects:
            dialog = RecentProjectsDialog(self, recent_projects)
            dialog.project_selected.connect(self.load_project_from_path)
            dialog.exec()
        else:
            # No recent projects, go straight to file browser
            self.browse_for_project()

    def browse_for_project(self):
        """Browse for a project file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "PDF Form Projects (*.fpdf);;All Files (*)"
        )

        if file_path:
            self.load_project_from_path(file_path)

    def load_project_from_path(self, project_path: str):
        """Load a project from file path"""
        try:
            project_data = self.project_manager.open_project(project_path)
            self.load_project(project_path, project_data)
            self.project_opened.emit(project_path, project_data)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{str(e)}")

    def load_project(self, project_path: str, project_data: Dict[str, Any]):
        """Load project data into the UI"""
        self.current_project_path = project_path
        self.current_project_data = project_data
        self.project_modified = False

        # Update window title
        project_name = project_data.get("project_info", {}).get("name", "Unknown")
        self.setWindowTitle(f"PDF Voice Editor - {project_name}")

        # Enable project-specific UI elements
        self.set_project_ui_enabled(True)

        # Update status bar
        if hasattr(self, 'project_status_label'):
            self.project_status_label.setText(f"Project: {project_name}")
        self.update_modified_indicator()

        # Load PDF file
        pdf_path = project_data.get("pdf_reference", {}).get("path", "")
        if pdf_path and Path(pdf_path).exists():
            self.load_pdf_file(pdf_path)
            # Show left panel when project is loaded
            if hasattr(self, 'show_left_panel'):
                self.show_left_panel()
        else:
            QMessageBox.warning(self, "PDF Not Found",
                                f"The associated PDF file was not found:\n{pdf_path}")

        # Update recent menu
        if hasattr(self, 'update_recent_menu'):
            self.update_recent_menu()

        # Load project-specific settings
        self.load_project_settings(project_data)

    def save_project(self):
        """Save the current project"""
        if not PROJECT_MANAGEMENT_AVAILABLE or not self.current_project_path:
            # Fallback to form data saving
            self.save_form_data_legacy()
            return

        try:
            # Update project data with current form data
            self.update_project_data_before_save()

            self.project_manager.save_project(self.current_project_path, self.current_project_data)
            self.project_modified = False
            self.project_modified_changed.emit(False)
            self.project_saved.emit(self.current_project_path)

            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage("Project saved", 2000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{str(e)}")

    def save_project_as(self):
        """Save the current project with a new name"""
        if not PROJECT_MANAGEMENT_AVAILABLE or not self.current_project_data:
            return

        project_name = self.current_project_data.get("project_info", {}).get("name", "project")
        default_name = f"{project_name}.fpdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", default_name, "PDF Form Projects (*.fpdf)"
        )

        if file_path:
            try:
                # Update project path in data
                self.current_project_path = file_path
                self.current_project_data["project_info"]["name"] = Path(file_path).stem

                # Update project data with current form data
                self.update_project_data_before_save()

                self.project_manager.save_project(file_path, self.current_project_data)
                self.project_modified = False
                self.project_modified_changed.emit(False)

                # Update window title
                self.setWindowTitle(f"PDF Voice Editor - {Path(file_path).stem}")

                self.project_saved.emit(file_path)
                if hasattr(self, 'statusBar'):
                    self.statusBar().showMessage("Project saved as new file", 2000)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project:\n{str(e)}")

    def close_project(self):
        """Close the current project"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            return

        if not self.check_save_current_project():
            return

        # Clear project data
        self.current_project_path = None
        self.current_project_data = None
        self.project_modified = False

        # Reset UI
        self.setWindowTitle("PDF Voice Editor")
        self.set_project_ui_enabled(False)
        if hasattr(self, 'project_status_label'):
            self.project_status_label.setText("No project loaded")
        self.update_modified_indicator()

        # Hide left panel and clear PDF viewer
        if hasattr(self, 'hide_left_panel'):
            self.hide_left_panel()
        if hasattr(self, 'clear_pdf_viewer'):
            self.clear_pdf_viewer()

        self.project_closed.emit()

    def show_project_properties(self):
        """Show project properties dialog"""
        if not PROJECT_MANAGEMENT_AVAILABLE or not self.current_project_data:
            return

        dialog = ProjectPropertiesDialog(self, self.current_project_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_updated_data()
            self.current_project_data.update(updated_data)
            self.mark_project_modified()

            # Update window title if name changed
            new_name = updated_data.get("project_info", {}).get("name", "")
            if new_name:
                self.setWindowTitle(f"PDF Voice Editor - {new_name}")

    # =========================
    # PROJECT STATE MANAGEMENT
    # =========================

    def mark_project_modified(self):
        """Mark the current project as modified"""
        if PROJECT_MANAGEMENT_AVAILABLE:
            old_modified = self.project_modified
            self.project_modified = True
            if old_modified != self.project_modified:
                self.project_modified_changed.emit(True)

    def is_project_loaded(self) -> bool:
        """Check if a project is currently loaded"""
        return PROJECT_MANAGEMENT_AVAILABLE and self.current_project_path is not None

    def get_current_project_name(self) -> str:
        """Get the name of the current project"""
        if not self.is_project_loaded():
            return ""
        return self.current_project_data.get("project_info", {}).get("name", "Unknown")

    def check_save_current_project(self) -> bool:
        """Check if current project needs saving, prompt user if needed"""
        if not PROJECT_MANAGEMENT_AVAILABLE or not self.project_modified:
            return True

        project_name = self.get_current_project_name() or "Untitled"

        reply = QMessageBox.question(
            self, "Save Project",
            f"The project '{project_name}' has unsaved changes.\n"
            "Do you want to save them before continuing?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_project()
            return not self.project_modified  # Return True if save was successful
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False

    def set_project_ui_enabled(self, enabled: bool):
        """Enable/disable project-specific UI elements"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            return

        # Menu actions
        if hasattr(self, 'save_project_action'):
            self.save_project_action.setEnabled(enabled)
        if hasattr(self, 'save_as_action'):
            self.save_as_action.setEnabled(enabled)
        if hasattr(self, 'close_project_action'):
            self.close_project_action.setEnabled(enabled)
        if hasattr(self, 'properties_action'):
            self.properties_action.setEnabled(enabled)

        # Toolbar actions
        if hasattr(self, 'save_action'):
            self.save_action.setEnabled(enabled)
        for action in getattr(self, 'project_toolbar_actions', []):
            action.setEnabled(enabled)

    def update_modified_indicator(self):
        """Update the modified indicator in status bar"""
        if not PROJECT_MANAGEMENT_AVAILABLE or not hasattr(self, 'modified_label'):
            return

        if self.project_modified:
            self.modified_label.setText("●")  # Bullet point indicates unsaved changes
            self.modified_label.setToolTip("Project has unsaved changes")
        else:
            self.modified_label.setText("")
            self.modified_label.setToolTip("")

    # =========================
    # RECENT PROJECTS MANAGEMENT
    # =========================

    def update_recent_menu(self):
        """Update the recent projects menu"""
        if not PROJECT_MANAGEMENT_AVAILABLE or not hasattr(self, 'recent_menu'):
            return

        self.recent_menu.clear()

        recent_projects = self.project_manager.get_recent_projects()

        if not recent_projects:
            no_recent_action = QAction("No recent projects", self)
            no_recent_action.setEnabled(False)
            self.recent_menu.addAction(no_recent_action)
            return

        # Add recent projects
        for i, project in enumerate(recent_projects[:10]):  # Limit to 10 recent
            project_name = project.get("name", "Unknown")
            project_path = project.get("path", "")

            action = QAction(f"&{i + 1} {project_name}", self)
            action.setStatusTip(f"Open {project_path}")
            action.triggered.connect(
                lambda checked, path=project_path: self.load_project_from_path(path)
            )
            self.recent_menu.addAction(action)

        self.recent_menu.addSeparator()

        # Clear recent projects
        clear_action = QAction("&Clear Recent Projects", self)
        clear_action.triggered.connect(self.clear_recent_projects)
        self.recent_menu.addAction(clear_action)

    def clear_recent_projects(self):
        """Clear the recent projects list"""
        if not PROJECT_MANAGEMENT_AVAILABLE:
            return

        reply = QMessageBox.question(
            self, "Clear Recent Projects",
            "Are you sure you want to clear all recent projects?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.project_manager.clear_recent_projects()
            self.update_recent_menu()

    # =========================
    # AUTO-SAVE FUNCTIONALITY
    # =========================

    def auto_save_project(self):
        """Auto-save the current project if modified"""
        if (PROJECT_MANAGEMENT_AVAILABLE and
                self.current_project_path and
                self.project_modified):
            try:
                self.update_project_data_before_save()
                self.project_manager.save_project(self.current_project_path, self.current_project_data)
                self.project_modified = False
                self.project_modified_changed.emit(False)
                if hasattr(self, 'statusBar'):
                    self.statusBar().showMessage("Project auto-saved", 1000)
            except Exception:
                pass  # Fail silently for auto-save

    # =========================
    # INTEGRATION HOOKS
    # =========================

    def update_project_data_before_save(self):
        """
        Hook for main window to update project data before saving
        Override this in your main window to save current form data, etc.
        """
        if not self.current_project_data:
            return

        # Update modification time
        self.current_project_data["project_info"]["modified_date"] = datetime.now().isoformat()

        # Hook for subclass to add form data, etc.
        # Example:
        # self.current_project_data["form_data"] = self.get_current_form_data()
        # self.current_project_data["user_preferences"] = self.get_current_preferences()

    def load_project_settings(self, project_data: Dict[str, Any]):
        """
        Hook for main window to load project-specific settings
        Override this in your main window to restore zoom, page, etc.
        """
        preferences = project_data.get("user_preferences", {})

        # Example settings that could be restored:
        # zoom_level = preferences.get("zoom_level", 100)
        # current_page = preferences.get("current_page", 1)
        # view_mode = preferences.get("view_mode", "single_page")

        print(f"📋 Loading project settings: {len(preferences)} preferences")

    # =========================
    # LEGACY SUPPORT HOOKS
    # =========================

    def open_pdf_legacy(self):
        """
        Legacy PDF opening - override this in your main window
        This is called when opening PDF without project management
        """
        # This should call your existing open_pdf method
        if hasattr(self, 'open_pdf'):
            self.open_pdf()
        else:
            QMessageBox.information(self, "Not Implemented",
                                    "PDF opening not implemented in main window")

    def save_form_data_legacy(self):
        """
        Legacy form data saving - override this in your main window
        This is called when saving without project management
        """
        # This should call your existing save_form_data method
        if hasattr(self, 'save_form_data'):
            self.save_form_data()
        else:
            QMessageBox.information(self, "Not Implemented",
                                    "Form data saving not implemented in main window")

    def load_pdf_file(self, pdf_path: str):
        """
        PDF file loading - override this in your main window
        This is called when a project loads its associated PDF
        """
        # This should call your existing PDF loading logic
        print(f"📄 Loading PDF file: {pdf_path}")
        # Override in main window to actually load the PDF

    # =========================
    # EVENT HANDLERS
    # =========================

    def _on_project_created(self, project_path: str):
        """Handle project created event"""
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(f"Project created: {Path(project_path).name}", 3000)

    def _on_project_opened(self, project_path: str, project_data: Dict[str, Any]):
        """Handle project opened event"""
        project_name = project_data.get("project_info", {}).get("name", "Unknown")
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(f"Project opened: {project_name}", 3000)

    def _on_project_saved(self, project_path: str):
        """Handle project saved event"""
        self.update_modified_indicator()

    def _on_project_closed(self):
        """Handle project closed event"""
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage("Project closed", 2000)

    def _on_project_modified_changed(self, is_modified: bool):
        """Handle project modification state change"""
        self.update_modified_indicator()

    # =========================
    # CLEANUP
    # =========================

    def cleanup_project_management(self):
        """Cleanup project management resources - call this in closeEvent"""
        if PROJECT_MANAGEMENT_AVAILABLE and hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()

        # Check for unsaved changes
        if PROJECT_MANAGEMENT_AVAILABLE and hasattr(self, 'check_save_current_project'):
            return self.check_save_current_project()

        return True