# a_assembly_dialog.py
"""
Assembly Creation Dialog for SYNAIPTIC Research Platform
Creates new research assemblies with database storage and GUID-based file organization
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QComboBox, QFormLayout, QGroupBox, QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any
import uuid
import os


class AssemblyDialog(QDialog):
    """Dialog for creating a new research assembly"""

    assembly_created = pyqtSignal(str, dict)  # assembly_id, assembly_data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.assembly_data = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Create New Assembly")
        self.setModal(True)
        self.resize(550, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
                font-size: 11pt;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #3498db;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        # Header
        header_label = QLabel("Create New Research Assembly")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(header_label)

        # Assembly Details Group
        details_group = QGroupBox("📁 Assembly Details")
        details_layout = QFormLayout(details_group)
        details_layout.setSpacing(15)

        # Assembly Name
        self.assembly_name_edit = QLineEdit()
        self.assembly_name_edit.setPlaceholderText("e.g., Legal Contract Review 2025")
        details_layout.addRow("Assembly Name:", self.assembly_name_edit)

        # Research Type
        self.research_type_combo = QComboBox()
        self.research_type_combo.addItems([
            "Legal Document Analysis",
            "Academic Research",
            "Medical Case Review",
            "Technical Documentation",
            "Investment Research",
            "Business Analysis",
            "Regulatory Compliance",
            "Patent Research",
            "General Research"
        ])
        details_layout.addRow("Research Type:", self.research_type_combo)

        # Researcher Name
        self.researcher_edit = QLineEdit()
        self.researcher_edit.setText(os.getenv("USER", os.getenv("USERNAME", "")))
        self.researcher_edit.setPlaceholderText("Primary researcher name")
        details_layout.addRow("Researcher:", self.researcher_edit)

        main_layout.addWidget(details_group)

        # Research Goals Group
        goals_group = QGroupBox("🎯 Research Goals")
        goals_layout = QFormLayout(goals_group)
        goals_layout.setSpacing(15)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Describe your research objectives, methodology, and expected outcomes...\n\n"
            "Example: Comprehensive analysis of merger agreement terms, risk assessment "
            "of contractual obligations, and competitive clause evaluation."
        )
        self.description_edit.setMaximumHeight(120)
        goals_layout.addRow("Description:", self.description_edit)

        # Keywords
        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("merger, liability, intellectual property, warranties")
        goals_layout.addRow("Keywords:", self.keywords_edit)

        main_layout.addWidget(goals_group)

        # AI Configuration Group
        ai_group = QGroupBox("🤖 AI Configuration")
        ai_layout = QFormLayout(ai_group)
        ai_layout.setSpacing(15)

        # AI Provider
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems([
            "GPT-4 (OpenAI)",
            "Claude-3 (Anthropic)",
            "GPT-3.5 (OpenAI)",
            "Local Model",
            "Gemini (Google)",
            "None (Manual Only)"
        ])
        ai_layout.addRow("AI Provider:", self.ai_provider_combo)

        main_layout.addWidget(ai_group)

        # Storage Information (Read-only display)
        storage_group = QGroupBox("💾 Storage Information")
        storage_layout = QVBoxLayout(storage_group)

        storage_info = QLabel(
            "Assembly will be stored in the application's managed storage.\n"
            "A unique identifier will be generated for organization and backup."
        )
        storage_info.setStyleSheet("color: #6c757d; font-style: italic; padding: 10px;")
        storage_info.setWordWrap(True)
        storage_layout.addWidget(storage_info)

        main_layout.addWidget(storage_group)

        # Dialog Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Customize button appearance
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Create Assembly")
        self.ok_button.setEnabled(False)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)

        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        main_layout.addWidget(button_box)

        # Connect validation
        self.assembly_name_edit.textChanged.connect(self.validate_form)
        self.validate_form()

    def validate_form(self):
        """Validate form input and enable/disable OK button"""
        assembly_name = self.assembly_name_edit.text().strip()

        # Enable OK button only if assembly name is provided
        is_valid = len(assembly_name) >= 3
        self.ok_button.setEnabled(is_valid)

        # Update placeholder styling based on validation
        if assembly_name and len(assembly_name) < 3:
            self.assembly_name_edit.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #dc3545;
                    background-color: #fff5f5;
                }
            """)
        else:
            self.assembly_name_edit.setStyleSheet("")

    def get_assembly_data(self) -> Dict[str, Any]:
        """Get assembly data from the form"""
        return {
            "name": self.assembly_name_edit.text().strip(),
            "research_type": self.research_type_combo.currentText(),
            "researcher": self.researcher_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "keywords": self.keywords_edit.text().strip(),
            "ai_provider": self.ai_provider_combo.currentText(),
            "guid": str(uuid.uuid4())  # Generate GUID for file system
        }

    def accept(self):
        """Handle dialog acceptance with validation"""
        assembly_data = self.get_assembly_data()

        # Final validation
        if not assembly_data["name"]:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Assembly name is required."
            )
            return

        if len(assembly_data["name"]) < 3:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Assembly name must be at least 3 characters long."
            )
            return

        # Check for duplicate names (if assembly manager is available)
        if hasattr(self.parent(), 'assembly_manager'):
            try:
                if self.parent().assembly_manager.is_assembly_name_duplicate(assembly_data["name"]):
                    # Offer to auto-generate unique name
                    reply = QMessageBox.question(
                        self,
                        "Duplicate Name",
                        f"Assembly name '{assembly_data['name']}' already exists.\n\n"
                        "Would you like to create a unique name automatically?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        unique_name = self.parent().assembly_manager.generate_unique_assembly_name(
                            assembly_data["name"]
                        )
                        assembly_data["name"] = unique_name
                        self.assembly_name_edit.setText(unique_name)

                        QMessageBox.information(
                            self,
                            "Name Updated",
                            f"Assembly name changed to: '{unique_name}'"
                        )
                    else:
                        return  # User chose not to proceed
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"Could not check for duplicate names: {str(e)}"
                )
                return

        # Emit signal with assembly data
        self.assembly_created.emit("new_assembly", assembly_data)
        super().accept()


class AssemblyPropertiesDialog(QDialog):
    """Dialog for viewing/editing assembly properties"""

    def __init__(self, parent=None, assembly_data: Dict[str, Any] = None):
        super().__init__(parent)
        self.assembly_data = assembly_data or {}
        self.init_ui()

    def init_ui(self):
        """Initialize the properties dialog UI"""
        self.setWindowTitle("Assembly Properties")
        self.setModal(True)
        self.resize(500, 600)

        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Assembly Properties")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # General Information
        general_group = QGroupBox("General Information")
        general_layout = QFormLayout(general_group)

        self.name_edit = QLineEdit()
        self.researcher_edit = QLineEdit()
        self.research_type_edit = QLineEdit()
        self.research_type_edit.setReadOnly(True)

        # Load current data
        self.name_edit.setText(self.assembly_data.get("name", ""))
        self.researcher_edit.setText(self.assembly_data.get("researcher", ""))
        self.research_type_edit.setText(self.assembly_data.get("research_type", ""))

        general_layout.addRow("Name:", self.name_edit)
        general_layout.addRow("Researcher:", self.researcher_edit)
        general_layout.addRow("Research Type:", self.research_type_edit)

        layout.addWidget(general_group)

        # Research Goals
        goals_group = QGroupBox("Research Goals")
        goals_layout = QFormLayout(goals_group)

        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(self.assembly_data.get("description", ""))
        self.description_edit.setMaximumHeight(100)

        self.keywords_edit = QLineEdit()
        self.keywords_edit.setText(self.assembly_data.get("keywords", ""))

        goals_layout.addRow("Description:", self.description_edit)
        goals_layout.addRow("Keywords:", self.keywords_edit)

        layout.addWidget(goals_group)

        # Statistics (Read-only)
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)

        document_count = self.assembly_data.get("document_count", 0)
        created_date = self.assembly_data.get("created_at", "Unknown")
        assembly_guid = self.assembly_data.get("guid", "Unknown")

        stats_layout.addRow("Documents:", QLabel(str(document_count)))
        stats_layout.addRow("Created:", QLabel(created_date))
        stats_layout.addRow("Assembly ID:", QLabel(assembly_guid))

        layout.addWidget(stats_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_updated_data(self) -> Dict[str, Any]:
        """Get updated assembly data from the form"""
        updated_data = self.assembly_data.copy()
        updated_data.update({
            "name": self.name_edit.text().strip(),
            "researcher": self.researcher_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "keywords": self.keywords_edit.text().strip()
        })
        return updated_data