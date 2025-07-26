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
        self.setWindowTitle(f"FormaPDF - {project_name}")

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
                self.statusBar().showMessage("Project saved to " + self.current_project_path, 2000)

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
                self.setWindowTitle(f"FormaPDF - {Path(file_path).stem}")

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
        self.setWindowTitle("FormaPDF - PDF Form Editor")
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
                self.setWindowTitle(f"FormaPDF - {new_name}")

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
        Enhanced version with PROPER appearance/formatting serialization
        Replace your existing method with this version
        """
        if not self.current_project_data:
            return

        try:
            from datetime import datetime

            # Update modification time
            self.current_project_data["project_info"]["modified_date"] = datetime.now().isoformat()

            # ===== FIND THE FIELD MANAGER =====
            field_manager = None
            all_fields = []

            print("🔍 Looking for field_manager...")

            if hasattr(self, 'field_manager') and self.field_manager:
                field_manager = self.field_manager
                print(f"✅ Found field_manager in main window")
            elif hasattr(self, 'pdf_canvas') and self.pdf_canvas and hasattr(self.pdf_canvas, 'field_manager'):
                field_manager = self.pdf_canvas.field_manager
                print(f"✅ Found field_manager in pdf_canvas")
            else:
                print("❌ No field_manager found")

            # Get fields from field_manager
            if field_manager:
                if hasattr(field_manager, 'get_all_fields'):
                    all_fields = field_manager.get_all_fields()
                    print(f"✅ Got {len(all_fields)} fields from get_all_fields()")
                elif hasattr(field_manager, 'all_fields'):
                    all_fields = field_manager.all_fields
                    print(f"✅ Got {len(all_fields)} fields from all_fields")

            # ===== ENHANCED FIELD SERIALIZATION WITH APPEARANCE =====
            if all_fields:
                print(f"🔄 Serializing {len(all_fields)} fields with appearance properties...")

                enhanced_field_definitions = []
                form_data = {}

                for i, field in enumerate(all_fields):
                    try:
                        # Get field attributes safely
                        field_id = getattr(field, 'id', f'field_{i}')
                        field_type = getattr(field, 'type', 'text')
                        if hasattr(field_type, 'value'):
                            field_type = field_type.value
                        else:
                            field_type = str(field_type)

                        # ===== EXTRACT APPEARANCE PROPERTIES =====
                        appearance_properties = {}
                        field_properties = getattr(field, 'properties', {})

                        print(f"  🎨 Processing appearance for field {field_id}...")
                        print(f"    Field properties keys: {list(field_properties.keys())}")

                        # Check if appearance properties exist in field.properties
                        if 'appearance' in field_properties:
                            appearance_properties = field_properties['appearance'].copy()
                            print(f"    ✅ Found appearance properties: {list(appearance_properties.keys())}")
                        else:
                            print(f"    ⚠️ No 'appearance' key in field properties")

                            # Check for individual appearance properties at root level
                            appearance_keys = [
                                'font_family', 'font_size', 'font_bold', 'font_italic', 'text_color',
                                'background_color', 'border_style', 'border_color', 'border_width'
                            ]

                            for key in appearance_keys:
                                if key in field_properties:
                                    appearance_properties[key] = field_properties[key]
                                    print(f"    ✅ Found root-level appearance property: {key}")

                        # Check for nested font/border/background properties
                        if 'font' in field_properties:
                            if 'font' not in appearance_properties:
                                appearance_properties['font'] = {}
                            appearance_properties['font'].update(field_properties['font'])
                            print(f"    ✅ Found font properties: {field_properties['font']}")

                        if 'border' in field_properties:
                            if 'border' not in appearance_properties:
                                appearance_properties['border'] = {}
                            appearance_properties['border'].update(field_properties['border'])
                            print(f"    ✅ Found border properties: {field_properties['border']}")

                        if 'background' in field_properties:
                            if 'background' not in appearance_properties:
                                appearance_properties['background'] = {}
                            appearance_properties['background'].update(field_properties['background'])
                            print(f"    ✅ Found background properties: {field_properties['background']}")

                        serializable_appearance = self._serialize_qcolor_properties(appearance_properties)


                        # Create enhanced field data
                        enhanced_field_data = {
                            'id': field_id,
                            'type': field_type,
                            'name': getattr(field, 'name', f'field_{i}'),
                            'display_name': getattr(field, 'display_name', getattr(field, 'name', f'field_{i}')),

                            # Position and size
                            'geometry': {
                                'x': getattr(field, 'x', 0),
                                'y': getattr(field, 'y', 0),
                                'width': getattr(field, 'width', 100),
                                'height': getattr(field, 'height', 25),
                                'page_number': getattr(field, 'page_number', 0)
                            },

                            # Basic properties
                            'basic_properties': {
                                'required': getattr(field, 'required', False),
                                'read_only': getattr(field, 'read_only', False),
                                'locked': getattr(field, 'locked', False),
                                'tooltip': getattr(field, 'tooltip', ''),
                                'visibility': getattr(field, 'visibility', 'Visible'),
                                'orientation': getattr(field, 'orientation', '0'),
                                'value': getattr(field, 'value', ''),
                                'input_type': getattr(field, 'input_type', 'text'),
                                'map_to': getattr(field, 'map_to', 'Auto')
                            },

                            # ===== ENHANCED APPEARANCE SERIALIZATION =====
                            #'appearance_properties': appearance_properties,  # ← NEW: Dedicated appearance section
                            'appearance_properties': serializable_appearance,  # ✅ Contains hex strings

                            # Custom properties (everything else)
                            'custom_properties': {k: v for k, v in field_properties.items()
                                                  if k not in ['appearance', 'font', 'border', 'background']},

                            # Format settings
                            'format_settings': {
                                'format_category': getattr(field, 'format_category', 'None'),
                                'format_settings': getattr(field, 'format_settings', '{}')
                            },

                            # Property groups (existing method)
                            'property_groups': self._get_basic_property_groups(field) if hasattr(self,
                                                                                                 '_get_basic_property_groups') else {},

                            # Metadata
                            'metadata': {
                                'created_date': datetime.now().isoformat(),
                                'field_version': '2.1',  # Increment version for appearance support
                                'schema_version': '1.0',
                                'has_appearance_data': len(appearance_properties) > 0
                            }
                        }

                        enhanced_field_definitions.append(enhanced_field_data)

                        # Collect form data
                        form_data[field_id] = getattr(field, 'value', '')

                        print(f"  ✅ Serialized field: {field_id} (appearance: {len(appearance_properties)} props)")

                    except Exception as e:
                        print(f"❌ Error serializing field {i}: {e}")
                        # Fallback to basic field data
                        try:
                            basic_field = {
                                'id': getattr(field, 'id', f'field_{i}'),
                                'type': str(getattr(field, 'type', 'text')),
                                'name': getattr(field, 'name', f'field_{i}'),
                                'x': getattr(field, 'x', 0),
                                'y': getattr(field, 'y', 0),
                                'width': getattr(field, 'width', 100),
                                'height': getattr(field, 'height', 25),
                                'page_number': getattr(field, 'page_number', 0),
                                'value': getattr(field, 'value', ''),
                                'properties': getattr(field, 'properties', {}),
                                'appearance_properties': {}  # Empty appearance for fallback
                            }
                            enhanced_field_definitions.append(basic_field)
                            form_data[basic_field['id']] = basic_field['value']
                        except:
                            print(f"❌ Complete failure for field {i}")

                # Store field definitions
                self.current_project_data["field_definitions"] = enhanced_field_definitions

                # Store form data
                self.current_project_data["form_data"] = form_data

                # Create field summary
                field_summary = {
                    'total_fields': len(all_fields),
                    'fields_by_type': {},
                    'fields_by_page': {},
                    'appearance_fields': 0,  # Count fields with appearance data
                    'serialization_date': datetime.now().isoformat(),
                    'schema_version': '2.1'
                }

                # Count by type and page, and appearance
                for field_def in enhanced_field_definitions:
                    try:
                        field_type = field_def.get('type', 'unknown')
                        page_num = str(field_def.get('geometry', {}).get('page_number', 0))

                        field_summary['fields_by_type'][field_type] = field_summary['fields_by_type'].get(field_type,
                                                                                                          0) + 1
                        field_summary['fields_by_page'][page_num] = field_summary['fields_by_page'].get(page_num, 0) + 1

                        if field_def.get('appearance_properties'):
                            field_summary['appearance_fields'] += 1
                    except:
                        pass

                self.current_project_data["field_summary"] = field_summary

                print(f"✅ Enhanced serialization complete: {len(enhanced_field_definitions)} fields")
                print(f"📊 Fields with appearance data: {field_summary['appearance_fields']}")

            else:
                print("⚠️ No fields found to serialize")
                self.current_project_data["field_definitions"] = []
                self.current_project_data["form_data"] = {}

            # ===== USER PREFERENCES =====
            user_preferences = {}

            try:
                if hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'zoom_factor'):
                    user_preferences['zoom_level'] = int(self.pdf_canvas.zoom_factor * 100)
            except:
                pass

            try:
                if hasattr(self, 'current_page'):
                    user_preferences['current_page'] = self.current_page
                elif hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'current_page'):
                    user_preferences['current_page'] = self.pdf_canvas.current_page
            except:
                user_preferences['current_page'] = 0

            try:
                if hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'show_grid'):
                    user_preferences['show_grid'] = self.pdf_canvas.show_grid
                else:
                    user_preferences['show_grid'] = False
            except:
                user_preferences['show_grid'] = False

            try:
                if hasattr(self, 'left_panel') and hasattr(self.left_panel, 'isVisible'):
                    user_preferences['left_panel_visible'] = self.left_panel.isVisible()
                else:
                    user_preferences['left_panel_visible'] = True
            except:
                user_preferences['left_panel_visible'] = True

            self.current_project_data["user_preferences"] = user_preferences

            # ===== UPDATE HISTORY =====
            history = self.current_project_data.get("history", {})
            history["total_edits"] = history.get("total_edits", 0) + 1
            history["last_save"] = datetime.now().isoformat()
            self.current_project_data["history"] = history

            print("🎉 Enhanced project save complete with appearance properties!")

        except Exception as e:
            print(f"❌ Error in enhanced save: {e}")
            import traceback
            traceback.print_exc()
            # Basic fallback
            self.current_project_data["project_info"]["modified_date"] = datetime.now().isoformat()

    def _get_basic_property_groups(self, field):
        """
        Helper method for basic property groups - HARDCODED
        Add this method to project_management_mixin.py
        """
        try:
            # Get field properties (hardcoded)
            field_properties = getattr(field, 'properties', {})
            field_type = getattr(field, 'type', 'text')
            if hasattr(field_type, 'value'):
                field_type = field_type.value
            else:
                field_type = str(field_type)

            # Basic property groups based on field type (hardcoded)
            property_groups = {}

            # Basic properties for all fields (hardcoded)
            property_groups['basic'] = {
                'name': 'basic',
                'label': 'Basic Properties',
                'properties': {
                    'name': {'value': getattr(field, 'name', ''), 'label': 'Field Name'},
                    'required': {'value': getattr(field, 'required', False), 'label': 'Required'},
                    'read_only': {'value': getattr(field, 'read_only', False), 'label': 'Read Only'},
                    'tooltip': {'value': getattr(field, 'tooltip', ''), 'label': 'Tooltip'}
                }
            }

            # Type-specific properties (hardcoded)
            if field_type in ['text', 'email', 'phone', 'url']:
                property_groups['text_properties'] = {
                    'name': 'text_properties',
                    'label': 'Text Properties',
                    'properties': {
                        'max_length': {'value': field_properties.get('max_length', 100), 'label': 'Max Length'},
                        'placeholder': {'value': field_properties.get('placeholder', ''), 'label': 'Placeholder'},
                        'multiline': {'value': field_properties.get('multiline', False), 'label': 'Multiline'}
                    }
                }
            elif field_type == 'number':
                property_groups['number_properties'] = {
                    'name': 'number_properties',
                    'label': 'Number Properties',
                    'properties': {
                        'min_value': {'value': field_properties.get('min_value', 0), 'label': 'Minimum Value'},
                        'max_value': {'value': field_properties.get('max_value', 1000), 'label': 'Maximum Value'},
                        'decimal_places': {'value': field_properties.get('decimal_places', 0),
                                           'label': 'Decimal Places'}
                    }
                }
            elif field_type in ['dropdown', 'radio', 'checkbox']:
                property_groups['choice_properties'] = {
                    'name': 'choice_properties',
                    'label': 'Choice Properties',
                    'properties': {
                        'options': {'value': field_properties.get('options', []), 'label': 'Options'},
                        'default_value': {'value': field_properties.get('default_value', ''), 'label': 'Default Value'}
                    }
                }

            return property_groups

        except Exception as e:
            print(f"❌ Error getting basic property groups: {e}")
            return {}

    def _serialize_field_property_groups(self, field):
        """
        Helper method to serialize property groups for a specific field
        Add this as a new method in project_management_mixin.py
        """
        try:
            property_groups = self._property_schema.get_property_groups_for_field_type(field.type)
            groups_data = {}

            for group in property_groups:
                group_data = {
                    'name': group.name,
                    'label': group.label,
                    'description': group.description,
                    'properties': {}
                }

                # Serialize each property in the group
                for prop in group.properties:
                    prop_value = field.properties.get(prop.name, prop.default_value)
                    group_data['properties'][prop.name] = {
                        'value': prop_value,
                        'default_value': prop.default_value,
                        'widget_type': prop.widget_type.value,
                        'label': prop.label,
                        'description': prop.description
                    }

                    # Add additional property metadata if available
                    if hasattr(prop, 'choices') and prop.choices:
                        group_data['properties'][prop.name]['choices'] = prop.choices
                    if hasattr(prop, 'min_value') and prop.min_value is not None:
                        group_data['properties'][prop.name]['min_value'] = prop.min_value
                    if hasattr(prop, 'max_value') and prop.max_value is not None:
                        group_data['properties'][prop.name]['max_value'] = prop.max_value
                    if hasattr(prop, 'placeholder') and prop.placeholder:
                        group_data['properties'][prop.name]['placeholder'] = prop.placeholder

                groups_data[group.name] = group_data

            return groups_data

        except Exception as e:
            print(f"❌ Error serializing property groups: {e}")
            return {}

    def load_project_settings(self, project_data: Dict[str, Any]):
        """
        Complete enhanced method that loads field settings, restores fields, and refreshes UI
        Replace the existing load_project_settings() method in project_management_mixin.py
        """
        try:
            print("🔄 Loading project settings with field restoration and UI refresh...")

            # ===== FIND THE FIELD MANAGER =====
            field_manager = None

            print("🔍 Looking for field_manager to restore fields...")

            if hasattr(self, 'field_manager') and self.field_manager:
                field_manager = self.field_manager
                print(f"✅ Found field_manager in main window")
            elif hasattr(self, 'pdf_canvas') and self.pdf_canvas and hasattr(self.pdf_canvas, 'field_manager'):
                field_manager = self.pdf_canvas.field_manager
                print(f"✅ Found field_manager in pdf_canvas")
            else:
                print("❌ No field_manager found for restoration")

            # ===== RESTORE FIELDS =====
            field_definitions = project_data.get("field_definitions", [])

            if field_definitions and field_manager:
                print(f"🔄 Restoring {len(field_definitions)} fields...")

                # Clear existing fields first (hardcoded)
                if hasattr(field_manager, 'clear_all_fields'):
                    field_manager.clear_all_fields()
                    print("✅ Cleared existing fields")
                elif hasattr(field_manager, 'all_fields'):
                    field_manager.all_fields.clear()
                    if hasattr(field_manager, 'selected_fields'):
                        field_manager.selected_fields.clear()
                    print("✅ Cleared existing fields (direct)")

                # Restore each field (hardcoded)
                restored_count = 0
                for i, field_data in enumerate(field_definitions):
                    try:
                        # Create field from saved data (hardcoded restoration)
                        restored_field = self._restore_field_from_data(field_data)

                        if restored_field:
                            # Add field to manager (hardcoded)
                            if hasattr(field_manager, 'add_field'):
                                field_manager.add_field(restored_field)
                            elif hasattr(field_manager, 'all_fields'):
                                field_manager.all_fields.append(restored_field)

                            restored_count += 1
                            print(f"✅ Restored field {i + 1}/{len(field_definitions)}: {restored_field.id}")
                        else:
                            print(f"❌ Failed to restore field {i + 1}")

                    except Exception as e:
                        print(f"❌ Error restoring field {i + 1}: {e}")
                        continue

                print(f"🎉 Restored {restored_count}/{len(field_definitions)} fields successfully")

                # ADD THIS:
                # Update field counter to prevent ID collisions
                if hasattr(field_manager, '_update_field_counter_from_restored_fields'):
                    field_manager._update_field_counter_from_restored_fields()
                elif hasattr(field_manager, '_field_counter'):
                    # Manual counter update if method doesn't exist
                    max_counter = 0
                    for field in (field_manager.all_fields if hasattr(field_manager, 'all_fields') else []):
                        field_id = getattr(field, 'id', '')
                        import re
                        match = re.search(r'_(\d+)$', field_id)
                        if match:
                            max_counter = max(max_counter, int(match.group(1)))
                    field_manager._field_counter = max_counter
                    print(f"✅ Updated field counter to {max_counter}")

                # Emit field manager signals if available (hardcoded)
                try:
                    if hasattr(field_manager, 'field_list_changed'):
                        field_manager.field_list_changed.emit()
                    print("✅ Emitted field_list_changed signal")
                except:
                    pass

            elif field_definitions and not field_manager:
                print(f"⚠️ Found {len(field_definitions)} fields to restore but no field_manager available")
            else:
                print("📝 No fields to restore")

            # ===== RESTORE FORM DATA =====
            form_data = project_data.get("form_data", {})
            if form_data and field_manager:
                print(f"🔄 Restoring form data for {len(form_data)} fields...")

                # Get all fields from manager (hardcoded)
                all_fields = []
                if hasattr(field_manager, 'get_all_fields'):
                    all_fields = field_manager.get_all_fields()
                elif hasattr(field_manager, 'all_fields'):
                    all_fields = field_manager.all_fields

                # Restore field values (hardcoded)
                restored_values = 0
                for field_id, value in form_data.items():
                    for field in all_fields:
                        if getattr(field, 'id', '') == field_id:
                            field.value = value
                            restored_values += 1
                            print(f"✅ Restored value for {field_id}: '{value}'")
                            break

                print(f"✅ Form data restoration complete: {restored_values}/{len(form_data)} values restored")

            # ===== RESTORE USER PREFERENCES =====
            preferences = project_data.get("user_preferences", {})
            print(f"🔄 Restoring {len(preferences)} user preferences...")

            # Restore zoom level (hardcoded)
            zoom_level = preferences.get("zoom_level", 100)
            try:
                if hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'set_zoom'):
                    self.pdf_canvas.set_zoom(zoom_level / 100.0)
                    print(f"✅ Restored zoom level: {zoom_level}%")
                elif hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'zoom_factor'):
                    self.pdf_canvas.zoom_factor = zoom_level / 100.0
                    print(f"✅ Set zoom factor: {zoom_level}%")
            except Exception as e:
                print(f"⚠️ Could not restore zoom: {e}")

            # Restore current page (hardcoded)
            current_page = preferences.get("current_page", 1)
            try:
                if hasattr(self, 'go_to_page'):
                    self.go_to_page(current_page)
                    print(f"✅ Restored current page: {current_page}")
                elif hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'current_page'):
                    self.pdf_canvas.current_page = current_page
                    print(f"✅ Set current page: {current_page}")
                elif hasattr(self, 'current_page'):
                    self.current_page = current_page
                    print(f"✅ Set current page property: {current_page}")
            except Exception as e:
                print(f"⚠️ Could not restore page: {e}")

            # Restore grid visibility (hardcoded)
            show_grid = preferences.get("show_grid", False)
            try:
                if hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'set_grid_visible'):
                    self.pdf_canvas.set_grid_visible(show_grid)
                    print(f"✅ Restored grid visibility: {show_grid}")
                elif hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'show_grid'):
                    self.pdf_canvas.show_grid = show_grid
                    print(f"✅ Set grid visibility: {show_grid}")
            except Exception as e:
                print(f"⚠️ Could not restore grid: {e}")

            # Restore left panel state (hardcoded)
            left_panel_visible = preferences.get("left_panel_visible", True)
            try:
                if hasattr(self, 'left_panel'):
                    if left_panel_visible:
                        if hasattr(self.left_panel, 'show'):
                            self.left_panel.show()
                        elif hasattr(self.left_panel, 'setVisible'):
                            self.left_panel.setVisible(True)
                    else:
                        if hasattr(self.left_panel, 'hide'):
                            self.left_panel.hide()
                        elif hasattr(self.left_panel, 'setVisible'):
                            self.left_panel.setVisible(False)
                    print(f"✅ Restored left panel visibility: {left_panel_visible}")
            except Exception as e:
                print(f"⚠️ Could not restore panel: {e}")

            # ===== REFRESH UI CONTROLS =====
            print("🔄 Refreshing UI controls after field restoration...")

            try:
                # Refresh the Properties tab dropdown list
                if hasattr(self, 'field_palette') and self.field_palette:
                    print("  🔄 Found field_palette, refreshing Properties tab...")

                    if hasattr(self.field_palette, 'properties_tab'):
                        properties_tab = self.field_palette.properties_tab
                        print("  🔄 Found properties_tab, updating dropdown...")

                        # Set field manager reference if not already set
                        if not hasattr(properties_tab, 'field_manager') or not properties_tab.field_manager:
                            if field_manager:
                                properties_tab.field_manager = field_manager
                                print("  ✅ Set field_manager on properties_tab")

                        # Refresh the control dropdown list
                        if hasattr(properties_tab, 'refresh_control_list'):
                            properties_tab.refresh_control_list()
                            print("  ✅ Called refresh_control_list()")
                        elif hasattr(properties_tab, 'control_dropdown'):
                            # Manual refresh if refresh_control_list doesn't exist
                            self._manual_refresh_dropdown(properties_tab)
                            print("  ✅ Manual dropdown refresh completed")

                        # Check dropdown count after refresh
                        if hasattr(properties_tab, 'control_dropdown'):
                            count = properties_tab.control_dropdown.count()
                            print(f"  📊 Dropdown now has {count} items")

                    else:
                        print("  ⚠️ No properties_tab found in field_palette")

                    # Update field palette connections
                    if hasattr(self.field_palette, 'set_field_manager') and field_manager:
                        self.field_palette.set_field_manager(field_manager)
                        print("  ✅ Updated field_palette field_manager")

                else:
                    print("  ⚠️ No field_palette found")

                # Refresh the tabbed field palette connections
                if hasattr(self, '_ensure_field_manager_integration'):
                    self._ensure_field_manager_integration()
                    print("  ✅ Called _ensure_field_manager_integration()")

                # Force canvas refresh to show restored fields
                if hasattr(self, 'pdf_canvas'):
                    if hasattr(self.pdf_canvas, 'update'):
                        self.pdf_canvas.update()
                        print("  ✅ Refreshed PDF canvas")
                    if hasattr(self.pdf_canvas, 'repaint'):
                        self.pdf_canvas.repaint()
                        print("  ✅ Repainted PDF canvas")

                print("✅ UI controls refresh completed successfully!")

            except Exception as e:
                print(f"❌ Error refreshing UI controls: {e}")
                import traceback
                traceback.print_exc()

            print("🎉 Project settings loaded successfully with field restoration and UI refresh!")

        except Exception as e:
            print(f"❌ Error loading project settings: {e}")
            import traceback
            traceback.print_exc()

    def _manual_refresh_dropdown(self, properties_tab):
        """
        Manual dropdown refresh when refresh_control_list() doesn't exist
        Add this helper method to project_management_mixin.py
        """
        try:
            dropdown = properties_tab.control_dropdown
            field_manager = getattr(properties_tab, 'field_manager', None)

            if not field_manager:
                print("    ❌ No field_manager for manual refresh")
                return

            # Block signals during update
            dropdown.blockSignals(True)

            try:
                # Clear existing items
                dropdown.clear()

                # Get all fields
                all_fields = []
                if hasattr(field_manager, 'get_all_fields'):
                    all_fields = field_manager.get_all_fields()
                elif hasattr(field_manager, 'all_fields'):
                    all_fields = field_manager.all_fields

                print(f"    🔄 Manual refresh: found {len(all_fields)} fields")

                if not all_fields:
                    dropdown.addItem("No controls available", None)
                    print("    📝 Added 'No controls available' placeholder")
                else:
                    # Add "No controls selected" as first option
                    dropdown.addItem("No controls selected", None)

                    # Add each field to dropdown
                    for field in all_fields:
                        try:
                            field_id = getattr(field, 'id', 'unknown')
                            field_type = getattr(field, 'type', 'unknown')
                            if hasattr(field_type, 'value'):
                                field_type = field_type.value
                            else:
                                field_type = str(field_type)

                            display_text = f"{field_type.title()} - {field_id}"
                            dropdown.addItem(display_text, field_id)
                            print(f"    ✅ Added: {display_text}")

                        except Exception as e:
                            print(f"    ❌ Error adding field to dropdown: {e}")
                            continue

                    print(f"    ✅ Manual refresh complete: {dropdown.count()} items")

            finally:
                # Re-enable signals
                dropdown.blockSignals(False)

        except Exception as e:
            print(f"❌ Error in manual dropdown refresh: {e}")

    def _restore_field_from_data(self, field_data: Dict[str, Any]):
        """
        Enhanced field restoration that includes appearance properties
        Update your existing method with this version
        """
        try:
            from src.models.field_model import FormField, FieldType

            # Check if this is enhanced format with appearance data
            if 'geometry' in field_data and 'basic_properties' in field_data:
                # Enhanced format
                geometry = field_data['geometry']
                basic_props = field_data.get('basic_properties', {})
                custom_props = field_data.get('custom_properties', {})
                format_settings = field_data.get('format_settings', {})

                # ===== RESTORE APPEARANCE PROPERTIES =====
                appearance_props = field_data.get('appearance_properties', {})

                # Combine all properties for the field
                all_properties = custom_props.copy()

                # Add appearance properties
                if appearance_props:
                    all_properties['appearance'] = appearance_props
                    print(f"  🎨 Restoring appearance properties: {list(appearance_props.keys())}")

                    # Also add individual appearance properties for compatibility
                    for key, value in appearance_props.items():
                        if isinstance(value, dict):
                            all_properties[key] = value
                        else:
                            all_properties[key] = value

                # Create field with enhanced data
                field = FormField(
                    id=field_data['id'],
                    type=FieldType(field_data['type']),
                    name=field_data['name'],
                    x=geometry['x'],
                    y=geometry['y'],
                    width=geometry['width'],
                    height=geometry['height'],
                    page_number=geometry.get('page_number', 0),
                    required=basic_props.get('required', False),
                    read_only=basic_props.get('read_only', False),
                    locked=basic_props.get('locked', False),
                    tooltip=basic_props.get('tooltip', ''),
                    visibility=basic_props.get('visibility', 'Visible'),
                    orientation=basic_props.get('orientation', '0'),
                    value=basic_props.get('value', ''),
                    properties=all_properties,  # ← Include appearance properties
                    format_category=format_settings.get('format_category', 'None'),
                    format_settings=format_settings.get('format_settings', '{}'),
                    input_type=basic_props.get('input_type', 'text'),
                    map_to=basic_props.get('map_to', 'Auto')
                )

                # Restore property group values
                property_groups = field_data.get('property_groups', {})
                for group_name, group_data in property_groups.items():
                    properties = group_data.get('properties', {})
                    for prop_name, prop_data in properties.items():
                        if 'value' in prop_data:
                            field.properties[prop_name] = prop_data['value']

                print(f"✅ Restored enhanced format field with appearance: {field.id}")
                return field

            else:
                # Legacy format
                if hasattr(FormField, 'from_dict'):
                    field = FormField.from_dict(field_data)
                    print(f"✅ Restored legacy format field: {field.id}")
                    return field
                else:
                    # Manual legacy restoration
                    field = FormField(
                        id=field_data.get('id', 'unknown'),
                        type=FieldType(field_data.get('type', 'text')),
                        name=field_data.get('name', 'unknown'),
                        x=field_data.get('x', 0),
                        y=field_data.get('y', 0),
                        width=field_data.get('width', 100),
                        height=field_data.get('height', 25),
                        page_number=field_data.get('page_number', 0),
                        required=field_data.get('required', False),
                        value=field_data.get('value', ''),
                        properties=field_data.get('properties', {})
                    )
                    print(f"✅ Restored manual legacy field: {field.id}")
                    return field

        except Exception as e:
            print(f"❌ Error restoring field from data: {e}")
            return None

    def _serialize_qcolor_properties(self, properties_dict: dict) -> dict:
        """Convert QColor objects to JSON-serializable hex strings"""
        from PyQt6.QtGui import QColor

        def convert_value(value):
            if isinstance(value, QColor):
                return value.name()  # Returns "#RRGGBB" format
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            else:
                return value

        return convert_value(properties_dict)

    def _deserialize_qcolor_properties(self, properties_dict: dict) -> dict:
        """Convert hex strings back to QColor objects"""
        from PyQt6.QtGui import QColor

        def convert_value(value):
            if isinstance(value, str) and value.startswith('#') and len(value) in [4, 7, 9]:
                if all(c in '0123456789ABCDEFabcdef' for c in value[1:]):
                    return QColor(value)
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            return value

        return convert_value(properties_dict)

    def _deserialize_enhanced_field(self, field_data: Dict[str, Any]):
        """
        Helper method to deserialize enhanced field format
        Add this as a new method in project_management_mixin.py
        """
        try:
            from src.models.field_model import FormField, FieldType

            # Extract enhanced field data
            geometry = field_data['geometry']
            basic_props = field_data.get('basic_properties', {})
            custom_props = field_data.get('custom_properties', {})
            format_settings = field_data.get('format_settings', {})

            # Create field with enhanced data
            field = FormField(
                id=field_data['id'],
                type=FieldType(field_data['type']),
                name=field_data['name'],
                x=geometry['x'],
                y=geometry['y'],
                width=geometry['width'],
                height=geometry['height'],
                page_number=geometry.get('page_number', 0),
                required=basic_props.get('required', False),
                read_only=basic_props.get('read_only', False),
                locked=basic_props.get('locked', False),
                tooltip=basic_props.get('tooltip', ''),
                visibility=basic_props.get('visibility', 'Visible'),
                orientation=basic_props.get('orientation', '0'),
                value=basic_props.get('value', ''),
                properties=custom_props,
                format_category=format_settings.get('format_category', 'None'),
                format_settings=format_settings.get('format_settings', '{}'),
                input_type=basic_props.get('input_type', 'text'),
                map_to=basic_props.get('map_to', 'Auto')
            )

            # Restore property group values
            property_groups = field_data.get('property_groups', {})
            for group_name, group_data in property_groups.items():
                properties = group_data.get('properties', {})
                for prop_name, prop_data in properties.items():
                    if 'value' in prop_data:
                        field.properties[prop_name] = prop_data['value']

            return field

        except Exception as e:
            print(f"❌ Error deserializing enhanced field: {e}")
            # Fallback to basic deserialization
            return FormField.from_dict(field_data)

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