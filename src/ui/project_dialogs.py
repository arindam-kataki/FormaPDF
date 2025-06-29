from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QGridLayout, QGroupBox,
    QCheckBox, QSplitter, QFileDialog, QMessageBox, QFormLayout,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import os


class NewProjectDialog(QDialog):
    """Dialog for creating a new project"""

    def __init__(self, parent=None, pdf_path: str = None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.project_path = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # PDF File selection
        pdf_group = QGroupBox("PDF File")
        pdf_layout = QFormLayout(pdf_group)

        self.pdf_path_edit = QLineEdit()
        if self.pdf_path:
            self.pdf_path_edit.setText(self.pdf_path)

        pdf_browse_btn = QPushButton("Browse...")
        pdf_browse_btn.clicked.connect(self.browse_pdf)

        pdf_file_layout = QHBoxLayout()
        pdf_file_layout.addWidget(self.pdf_path_edit)
        pdf_file_layout.addWidget(pdf_browse_btn)

        pdf_layout.addRow("PDF File:", pdf_file_layout)
        layout.addWidget(pdf_group)

        # Project details
        project_group = QGroupBox("Project Details")
        project_layout = QFormLayout(project_group)

        self.project_name_edit = QLineEdit()
        self.project_name_edit.textChanged.connect(self.update_project_path)

        self.author_edit = QLineEdit()
        self.author_edit.setText(os.getenv("USER", os.getenv("USERNAME", "")))

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)

        project_layout.addRow("Project Name:", self.project_name_edit)
        project_layout.addRow("Author:", self.author_edit)
        project_layout.addRow("Description:", self.description_edit)

        layout.addWidget(project_group)

        # Project file location
        location_group = QGroupBox("Project Location")
        location_layout = QFormLayout(location_group)

        self.project_path_edit = QLineEdit()

        location_browse_btn = QPushButton("Browse...")
        location_browse_btn.clicked.connect(self.browse_project_location)

        location_layout_h = QHBoxLayout()
        location_layout_h.addWidget(self.project_path_edit)
        location_layout_h.addWidget(location_browse_btn)

        location_layout.addRow("Save As:", location_layout_h)
        layout.addWidget(location_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)

        layout.addWidget(buttons)

        # Connect signals for validation
        self.pdf_path_edit.textChanged.connect(self.validate_form)
        self.project_name_edit.textChanged.connect(self.validate_form)

        # Initial validation
        self.validate_form()

        if self.pdf_path:
            self.update_project_path()

    def browse_pdf(self):
        """Browse for PDF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF File", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.pdf_path_edit.setText(file_path)
            # Auto-fill project name from PDF filename
            if not self.project_name_edit.text():
                pdf_name = Path(file_path).stem
                self.project_name_edit.setText(pdf_name)

    def browse_project_location(self):
        """Browse for project save location"""
        if self.project_name_edit.text():
            default_name = f"{self.project_name_edit.text()}.fpdf"
        else:
            default_name = "project.fpdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", default_name, "PDF Form Projects (*.fpdf)"
        )
        if file_path:
            self.project_path_edit.setText(file_path)

    def update_project_path(self):
        """Auto-update project path based on PDF location and project name"""
        if self.pdf_path_edit.text() and self.project_name_edit.text():
            pdf_path = Path(self.pdf_path_edit.text())
            if pdf_path.exists():
                project_name = self.project_name_edit.text()
                project_path = pdf_path.parent / f"{project_name}.fpdf"
                self.project_path_edit.setText(str(project_path))

    def validate_form(self):
        """Validate form and enable/disable OK button"""
        pdf_valid = Path(self.pdf_path_edit.text()).exists() if self.pdf_path_edit.text() else False
        name_valid = bool(self.project_name_edit.text().strip())

        self.ok_button.setEnabled(pdf_valid and name_valid)

    def get_project_data(self) -> Dict[str, Any]:
        """Get project data from form"""
        return {
            "pdf_path": self.pdf_path_edit.text(),
            "project_path": self.project_path_edit.text(),
            "name": self.project_name_edit.text().strip(),
            "author": self.author_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip()
        }


class RecentProjectsDialog(QDialog):
    """Dialog for opening recent projects"""

    project_selected = pyqtSignal(str)

    def __init__(self, parent=None, recent_projects: List[Dict[str, str]] = None):
        super().__init__(parent)
        self.recent_projects = recent_projects or []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Open Recent Project")
        self.setModal(True)
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Recent Projects")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Projects table
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(4)
        self.projects_table.setHorizontalHeaderLabels([
            "Project Name", "PDF File", "Last Opened", "Created"
        ])

        # Configure table
        header = self.projects_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.projects_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.projects_table.setAlternatingRowColors(True)
        self.projects_table.doubleClicked.connect(self.open_selected_project)

        # Context menu
        self.projects_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.projects_table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.projects_table)

        # Populate table
        self.populate_projects_table()

        # Buttons
        button_layout = QHBoxLayout()

        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected_project)
        open_btn.setDefault(True)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_project)

        clear_btn = QPushButton("Clear Recent")
        clear_btn.clicked.connect(self.clear_recent)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(open_btn)
        button_layout.addWidget(browse_btn)
        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Enable open button only when selection exists
        self.projects_table.selectionModel().selectionChanged.connect(
            lambda: open_btn.setEnabled(bool(self.projects_table.selectedIndexes()))
        )
        open_btn.setEnabled(False)

    def populate_projects_table(self):
        """Populate the projects table with recent projects"""
        self.projects_table.setRowCount(len(self.recent_projects))

        for row, project in enumerate(self.recent_projects):
            # Project name
            name_item = QTableWidgetItem(project.get("name", "Unknown"))
            self.projects_table.setItem(row, 0, name_item)

            # PDF file path
            pdf_path = project.get("pdf_path", "")
            pdf_name = Path(pdf_path).name if pdf_path else "Unknown"
            pdf_item = QTableWidgetItem(pdf_name)
            pdf_item.setToolTip(pdf_path)
            self.projects_table.setItem(row, 1, pdf_item)

            # Last opened
            last_opened = project.get("last_opened", "")
            if last_opened:
                try:
                    dt = datetime.fromisoformat(last_opened.replace("Z", "+00:00"))
                    last_opened_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    last_opened_str = "Unknown"
            else:
                last_opened_str = "Unknown"

            last_opened_item = QTableWidgetItem(last_opened_str)
            self.projects_table.setItem(row, 2, last_opened_item)

            # Created
            created = project.get("created", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    created_str = dt.strftime("%Y-%m-%d")
                except:
                    created_str = "Unknown"
            else:
                created_str = "Unknown"

            created_item = QTableWidgetItem(created_str)
            self.projects_table.setItem(row, 3, created_item)

            # Store full project path for later use
            name_item.setData(Qt.ItemDataRole.UserRole, project.get("path", ""))

    def show_context_menu(self, position):
        """Show context menu for project items"""
        item = self.projects_table.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_selected_project)
        menu.addAction(open_action)

        menu.addSeparator()

        remove_action = QAction("Remove from Recent", self)
        remove_action.triggered.connect(self.remove_selected_project)
        menu.addAction(remove_action)

        show_location_action = QAction("Show in File Explorer", self)
        show_location_action.triggered.connect(self.show_project_location)
        menu.addAction(show_location_action)

        menu.exec(self.projects_table.mapToGlobal(position))

    def open_selected_project(self):
        """Open the selected project"""
        current_row = self.projects_table.currentRow()
        if current_row >= 0:
            name_item = self.projects_table.item(current_row, 0)
            project_path = name_item.data(Qt.ItemDataRole.UserRole)
            if project_path and Path(project_path).exists():
                self.project_selected.emit(project_path)
                self.accept()
            else:
                QMessageBox.warning(self, "File Not Found",
                                    f"Project file not found:\n{project_path}")

    def remove_selected_project(self):
        """Remove selected project from recent list"""
        current_row = self.projects_table.currentRow()
        if current_row >= 0:
            name_item = self.projects_table.item(current_row, 0)
            project_path = name_item.data(Qt.ItemDataRole.UserRole)

            # Remove from data
            self.recent_projects = [p for p in self.recent_projects
                                    if p.get("path") != project_path]

            # Refresh table
            self.populate_projects_table()

    def show_project_location(self):
        """Show project file in file explorer"""
        current_row = self.projects_table.currentRow()
        if current_row >= 0:
            name_item = self.projects_table.item(current_row, 0)
            project_path = name_item.data(Qt.ItemDataRole.UserRole)

            if project_path and Path(project_path).exists():
                # Platform-specific file explorer opening
                import subprocess
                import sys

                if sys.platform == "win32":
                    subprocess.Popen(f'explorer /select,"{project_path}"')
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", "-R", project_path])
                else:
                    subprocess.Popen(["xdg-open", str(Path(project_path).parent)])

    def browse_project(self):
        """Browse for a project file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "PDF Form Projects (*.fpdf)"
        )
        if file_path:
            self.project_selected.emit(file_path)
            self.accept()

    def clear_recent(self):
        """Clear all recent projects"""
        reply = QMessageBox.question(
            self, "Clear Recent Projects",
            "Are you sure you want to clear all recent projects?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.recent_projects.clear()
            self.populate_projects_table()


class ProjectPropertiesDialog(QDialog):
    """Dialog for viewing/editing project properties"""

    def __init__(self, parent=None, project_data: Dict[str, Any] = None):
        super().__init__(parent)
        self.project_data = project_data or {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Project Properties")
        self.setModal(True)
        self.resize(500, 600)

        layout = QVBoxLayout(self)

        # Create tab-like sections using group boxes
        # General Information
        general_group = QGroupBox("General Information")
        general_layout = QFormLayout(general_group)

        self.name_edit = QLineEdit()
        self.author_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)

        # Load current data
        project_info = self.project_data.get("project_info", {})
        self.name_edit.setText(project_info.get("name", ""))
        self.author_edit.setText(project_info.get("author", ""))
        self.description_edit.setPlainText(project_info.get("description", ""))

        general_layout.addRow("Name:", self.name_edit)
        general_layout.addRow("Author:", self.author_edit)
        general_layout.addRow("Description:", self.description_edit)

        layout.addWidget(general_group)

        # File Information
        file_group = QGroupBox("File Information")
        file_layout = QFormLayout(file_group)

        pdf_ref = self.project_data.get("pdf_reference", {})

        pdf_path_label = QLabel(pdf_ref.get("path", "Unknown"))
        pdf_path_label.setWordWrap(True)
        pdf_path_label.setStyleSheet("QLabel { color: #666; }")

        pdf_size = pdf_ref.get("size_bytes", 0)
        if pdf_size > 0:
            if pdf_size > 1024 * 1024:
                size_str = f"{pdf_size / (1024 * 1024):.1f} MB"
            elif pdf_size > 1024:
                size_str = f"{pdf_size / 1024:.1f} KB"
            else:
                size_str = f"{pdf_size} bytes"
        else:
            size_str = "Unknown"

        file_layout.addRow("PDF File:", pdf_path_label)
        file_layout.addRow("File Size:", QLabel(size_str))

        layout.addWidget(file_group)

        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)

        history = self.project_data.get("history", {})

        created = history.get("created", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                created_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                created_str = "Unknown"
        else:
            created_str = "Unknown"

        last_opened = history.get("last_opened", "")
        if last_opened:
            try:
                dt = datetime.fromisoformat(last_opened.replace("Z", "+00:00"))
                last_opened_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                last_opened_str = "Unknown"
        else:
            last_opened_str = "Unknown"

        save_count = history.get("save_count", 0)
        total_edits = history.get("total_edits", 0)

        stats_layout.addRow("Created:", QLabel(created_str))
        stats_layout.addRow("Last Opened:", QLabel(last_opened_str))
        stats_layout.addRow("Times Saved:", QLabel(str(save_count)))
        stats_layout.addRow("Total Edits:", QLabel(str(total_edits)))

        layout.addWidget(stats_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_updated_data(self) -> Dict[str, Any]:
        """Get updated project data"""
        updated_data = self.project_data.copy()

        # Update project info
        if "project_info" not in updated_data:
            updated_data["project_info"] = {}

        updated_data["project_info"]["name"] = self.name_edit.text().strip()
        updated_data["project_info"]["author"] = self.author_edit.text().strip()
        updated_data["project_info"]["description"] = self.description_edit.toPlainText().strip()
        updated_data["project_info"]["modified_date"] = datetime.now().isoformat()

        return updated_data