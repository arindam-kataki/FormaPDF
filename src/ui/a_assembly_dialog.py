# a_assembly_dialog.py
"""
Assembly Creation and Properties Dialog for PDF Research Platform
Provides UI for creating new assemblies and editing assembly properties
"""

from typing import Dict, Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QTextEdit, QComboBox, QPushButton, QLabel,
    QDialogButtonBox, QMessageBox, QListWidget, QListWidgetItem,
    QTabWidget, QWidget, QCheckBox, QSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QIcon


class AssemblyDialog(QDialog):
    """
    Dialog for creating new assemblies or editing assembly properties
    """

    # Signals
    assembly_created = pyqtSignal(dict)  # Emits assembly data
    assembly_updated = pyqtSignal(dict)  # Emits updated assembly data

    def __init__(self, parent=None, assembly_data: Optional[Dict] = None):
        """
        Initialize assembly dialog

        Args:
            parent: Parent widget
            assembly_data: Existing assembly data for editing (None for new)
        """
        super().__init__(parent)

        self.assembly_data = assembly_data or {}
        self.is_new = assembly_data is None

        # Settings
        self.settings = QSettings("SYNAIPTIC", "PDFResearchPlatform")

        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize the user interface"""
        # Set dialog properties
        self.setWindowTitle("New Research Assembly" if self.is_new else "Assembly Properties")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #0066cc;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)

        # Create layout
        layout = QVBoxLayout(self)

        # Create tab widget for organized sections
        self.tab_widget = QTabWidget()

        # General tab
        general_tab = self.create_general_tab()
        self.tab_widget.addTab(general_tab, "General")

        # Research Settings tab
        research_tab = self.create_research_tab()
        self.tab_widget.addTab(research_tab, "Research Settings")

        # AI Configuration tab
        ai_tab = self.create_ai_tab()
        self.tab_widget.addTab(ai_tab, "AI Configuration")

        # Storage tab (only for new assemblies)
        if self.is_new:
            storage_tab = self.create_storage_tab()
            self.tab_widget.addTab(storage_tab, "Storage")

        layout.addWidget(self.tab_widget)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept_dialog)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def create_general_tab(self) -> QWidget:
        """Create general information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Basic Information Group
        info_group = QGroupBox("Basic Information")
        info_layout = QFormLayout(info_group)

        # Assembly name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter a descriptive name for your research")
        info_layout.addRow("Name:*", self.name_edit)

        # Researcher name
        self.researcher_edit = QLineEdit()
        self.researcher_edit.setPlaceholderText("Your name or team name")
        default_researcher = self.settings.value("default_researcher", "")
        self.researcher_edit.setText(default_researcher)
        info_layout.addRow("Researcher:", self.researcher_edit)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "Describe the purpose and scope of this research assembly..."
        )
        self.description_edit.setMaximumHeight(100)
        info_layout.addRow("Description:", self.description_edit)

        layout.addWidget(info_group)

        # Keywords Group
        keywords_group = QGroupBox("Keywords and Tags")
        keywords_layout = QVBoxLayout(keywords_group)

        # Keywords input
        keyword_input_layout = QHBoxLayout()
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Enter keyword and press Add")
        self.keyword_edit.returnPressed.connect(self.add_keyword)
        keyword_input_layout.addWidget(self.keyword_edit)

        self.add_keyword_btn = QPushButton("Add")
        self.add_keyword_btn.clicked.connect(self.add_keyword)
        keyword_input_layout.addWidget(self.add_keyword_btn)

        keywords_layout.addLayout(keyword_input_layout)

        # Keywords list
        self.keywords_list = QListWidget()
        self.keywords_list.setMaximumHeight(80)
        self.keywords_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.keywords_list.customContextMenuRequested.connect(self.show_keyword_menu)
        keywords_layout.addWidget(self.keywords_list)

        # Remove keyword button
        self.remove_keyword_btn = QPushButton("Remove Selected")
        self.remove_keyword_btn.clicked.connect(self.remove_keyword)
        keywords_layout.addWidget(self.remove_keyword_btn)

        layout.addWidget(keywords_group)

        # Assembly Type
        type_group = QGroupBox("Research Type")
        type_layout = QFormLayout(type_group)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "General Research",
            "Legal Document Analysis",
            "Academic Literature Review",
            "Medical Case Study",
            "Technical Documentation",
            "Financial Analysis",
            "Patent Research",
            "Market Research",
            "Historical Research",
            "Other"
        ])
        type_layout.addRow("Type:", self.type_combo)

        layout.addWidget(type_group)

        layout.addStretch()

        return widget

    def create_research_tab(self) -> QWidget:
        """Create research settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Document Settings
        doc_group = QGroupBox("Document Settings")
        doc_layout = QFormLayout(doc_group)

        # Auto-import settings
        self.auto_ocr_check = QCheckBox("Automatically OCR scanned documents")
        self.auto_ocr_check.setChecked(True)
        doc_layout.addRow(self.auto_ocr_check)

        self.extract_metadata_check = QCheckBox("Extract document metadata on import")
        self.extract_metadata_check.setChecked(True)
        doc_layout.addRow(self.extract_metadata_check)

        self.create_thumbnails_check = QCheckBox("Generate document thumbnails")
        self.create_thumbnails_check.setChecked(True)
        doc_layout.addRow(self.create_thumbnails_check)

        layout.addWidget(doc_group)

        # Annotation Settings
        annotation_group = QGroupBox("Annotation Settings")
        annotation_layout = QFormLayout(annotation_group)

        # Default annotation color
        self.annotation_color_combo = QComboBox()
        self.annotation_color_combo.addItems([
            "Yellow",
            "Green",
            "Blue",
            "Pink",
            "Orange",
            "Purple"
        ])
        annotation_layout.addRow("Default Color:", self.annotation_color_combo)

        # Auto-save annotations
        self.auto_save_annotations_check = QCheckBox("Auto-save annotations")
        self.auto_save_annotations_check.setChecked(True)
        annotation_layout.addRow(self.auto_save_annotations_check)

        layout.addWidget(annotation_group)

        # Search Settings
        search_group = QGroupBox("Search and Indexing")
        search_layout = QFormLayout(search_group)

        self.index_on_import_check = QCheckBox("Index documents on import")
        self.index_on_import_check.setChecked(True)
        search_layout.addRow(self.index_on_import_check)

        self.semantic_search_check = QCheckBox("Enable semantic search (requires AI)")
        self.semantic_search_check.setChecked(True)
        search_layout.addRow(self.semantic_search_check)

        layout.addWidget(search_group)

        layout.addStretch()

        return widget

    def create_ai_tab(self) -> QWidget:
        """Create AI configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # AI Provider Settings
        provider_group = QGroupBox("AI Provider")
        provider_layout = QFormLayout(provider_group)

        # AI Provider selection
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems([
            "GPT-4 (OpenAI)",
            "GPT-3.5 Turbo (OpenAI)",
            "Claude 3 (Anthropic)",
            "Local LLM (Ollama)",
            "None (Disable AI features)"
        ])
        provider_layout.addRow("Provider:", self.ai_provider_combo)

        # API Key (if needed)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter API key (leave empty to use default)")
        provider_layout.addRow("API Key:", self.api_key_edit)

        # Test connection button
        self.test_ai_btn = QPushButton("Test Connection")
        self.test_ai_btn.clicked.connect(self.test_ai_connection)
        provider_layout.addRow("", self.test_ai_btn)

        layout.addWidget(provider_group)

        # AI Features
        features_group = QGroupBox("AI Features")
        features_layout = QVBoxLayout(features_group)

        self.ai_chat_check = QCheckBox("Enable AI Chat Assistant")
        self.ai_chat_check.setChecked(True)
        features_layout.addWidget(self.ai_chat_check)

        self.ai_summary_check = QCheckBox("Enable automatic document summarization")
        self.ai_summary_check.setChecked(True)
        features_layout.addWidget(self.ai_summary_check)

        self.ai_insights_check = QCheckBox("Generate research insights")
        self.ai_insights_check.setChecked(True)
        features_layout.addWidget(self.ai_insights_check)

        self.ai_translation_check = QCheckBox("Enable document translation")
        features_layout.addWidget(self.ai_translation_check)

        layout.addWidget(features_group)

        # Token Limits
        limits_group = QGroupBox("Usage Limits")
        limits_layout = QFormLayout(limits_group)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 100000)
        self.max_tokens_spin.setValue(4000)
        self.max_tokens_spin.setSuffix(" tokens")
        limits_layout.addRow("Max tokens per request:", self.max_tokens_spin)

        self.monthly_limit_spin = QSpinBox()
        self.monthly_limit_spin.setRange(0, 1000000)
        self.monthly_limit_spin.setValue(0)
        self.monthly_limit_spin.setSpecialValueText("Unlimited")
        self.monthly_limit_spin.setSuffix(" tokens")
        limits_layout.addRow("Monthly limit:", self.monthly_limit_spin)

        layout.addWidget(limits_group)

        layout.addStretch()

        return widget

    def create_storage_tab(self) -> QWidget:
        """Create storage configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Storage Location
        location_group = QGroupBox("Storage Location")
        location_layout = QVBoxLayout(location_group)

        # Default location radio
        self.default_location_radio = QCheckBox("Use default location")
        self.default_location_radio.setChecked(True)
        self.default_location_radio.toggled.connect(self.toggle_custom_location)
        location_layout.addWidget(self.default_location_radio)

        # Default path display
        default_path = self.settings.value(
            "default_assembly_path",
            "~/Documents/SYNAIPTIC Research"
        )
        self.default_path_label = QLabel(f"Default: {default_path}")
        self.default_path_label.setStyleSheet("QLabel { color: #666; margin-left: 20px; }")
        location_layout.addWidget(self.default_path_label)

        # Custom location
        custom_layout = QHBoxLayout()
        self.custom_location_edit = QLineEdit()
        self.custom_location_edit.setEnabled(False)
        self.custom_location_edit.setPlaceholderText("Select custom location...")
        custom_layout.addWidget(self.custom_location_edit)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setEnabled(False)
        self.browse_btn.clicked.connect(self.browse_location)
        custom_layout.addWidget(self.browse_btn)

        location_layout.addLayout(custom_layout)

        layout.addWidget(location_group)

        # Storage Options
        options_group = QGroupBox("Storage Options")
        options_layout = QVBoxLayout(options_group)

        self.copy_documents_check = QCheckBox("Copy imported documents to assembly folder")
        self.copy_documents_check.setChecked(True)
        self.copy_documents_check.setToolTip(
            "If unchecked, documents will be referenced from their original location"
        )
        options_layout.addWidget(self.copy_documents_check)

        self.compress_images_check = QCheckBox("Compress images to save space")
        self.compress_images_check.setChecked(False)
        options_layout.addWidget(self.compress_images_check)

        self.backup_check = QCheckBox("Enable automatic backups")
        self.backup_check.setChecked(True)
        options_layout.addWidget(self.backup_check)

        layout.addWidget(options_group)

        # Backup Settings
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QFormLayout(backup_group)

        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems([
            "Every save",
            "Hourly",
            "Daily",
            "Weekly"
        ])
        self.backup_frequency_combo.setCurrentIndex(2)  # Daily
        backup_layout.addRow("Frequency:", self.backup_frequency_combo)

        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 100)
        self.backup_count_spin.setValue(5)
        backup_layout.addRow("Keep last:", self.backup_count_spin)

        layout.addWidget(backup_group)

        layout.addStretch()

        return widget

    def load_data(self):
        """Load existing assembly data into form"""
        if not self.assembly_data:
            return

        # General tab
        self.name_edit.setText(self.assembly_data.get('name', ''))
        self.researcher_edit.setText(self.assembly_data.get('researcher', ''))
        self.description_edit.setPlainText(self.assembly_data.get('description', ''))

        # Keywords
        keywords = self.assembly_data.get('keywords', [])
        for keyword in keywords:
            self.keywords_list.addItem(keyword)

        # Research type
        research_type = self.assembly_data.get('research_type', 'General Research')
        index = self.type_combo.findText(research_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        # AI provider
        ai_provider = self.assembly_data.get('ai_provider', 'GPT-4 (OpenAI)')
        index = self.ai_provider_combo.findText(ai_provider)
        if index >= 0:
            self.ai_provider_combo.setCurrentIndex(index)

    def add_keyword(self):
        """Add keyword to list"""
        keyword = self.keyword_edit.text().strip()
        if keyword:
            # Check for duplicates
            for i in range(self.keywords_list.count()):
                if self.keywords_list.item(i).text() == keyword:
                    return

            self.keywords_list.addItem(keyword)
            self.keyword_edit.clear()

    def remove_keyword(self):
        """Remove selected keyword"""
        current_item = self.keywords_list.currentItem()
        if current_item:
            self.keywords_list.takeItem(self.keywords_list.row(current_item))

    def show_keyword_menu(self, position):
        """Show context menu for keywords"""
        # TODO: Implement keyword context menu
        pass

    def toggle_custom_location(self, checked):
        """Toggle custom location controls"""
        self.custom_location_edit.setEnabled(not checked)
        self.browse_btn.setEnabled(not checked)

    def browse_location(self):
        """Browse for custom storage location"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Assembly Storage Location",
            self.custom_location_edit.text() or ""
        )

        if folder:
            self.custom_location_edit.setText(folder)

    def test_ai_connection(self):
        """Test AI provider connection"""
        provider = self.ai_provider_combo.currentText()

        # TODO: Implement actual connection test
        QMessageBox.information(
            self,
            "AI Connection Test",
            f"Testing connection to {provider}...\n\n"
            "Connection test will be implemented with AI integration."
        )

    def validate_input(self) -> bool:
        """
        Validate user input

        Returns:
            True if input is valid
        """
        # Check required fields
        if not self.name_edit.text().strip():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter an assembly name."
            )
            self.name_edit.setFocus()
            return False

        # Check for valid storage location if custom
        if not self.default_location_radio.isChecked():
            location = self.custom_location_edit.text().strip()
            if not location:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Please select a storage location."
                )
                self.custom_location_edit.setFocus()
                return False

        return True

    def accept_dialog(self):
        """Accept dialog and emit signal"""
        if not self.validate_input():
            return

        # Gather all data
        assembly_data = {
            'name': self.name_edit.text().strip(),
            'researcher': self.researcher_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'keywords': [
                self.keywords_list.item(i).text()
                for i in range(self.keywords_list.count())
            ],
            'research_type': self.type_combo.currentText(),
            'ai_provider': self.ai_provider_combo.currentText(),
            'ai_features': {
                'chat': self.ai_chat_check.isChecked(),
                'summary': self.ai_summary_check.isChecked(),
                'insights': self.ai_insights_check.isChecked(),
                'translation': self.ai_translation_check.isChecked()
            },
            'document_settings': {
                'auto_ocr': self.auto_ocr_check.isChecked(),
                'extract_metadata': self.extract_metadata_check.isChecked(),
                'create_thumbnails': self.create_thumbnails_check.isChecked()
            },
            'annotation_settings': {
                'default_color': self.annotation_color_combo.currentText(),
                'auto_save': self.auto_save_annotations_check.isChecked()
            },
            'search_settings': {
                'index_on_import': self.index_on_import_check.isChecked(),
                'semantic_search': self.semantic_search_check.isChecked()
            }
        }

        # Add storage settings for new assemblies
        if self.is_new:
            assembly_data['storage'] = {
                'use_default': self.default_location_radio.isChecked(),
                'custom_location': self.custom_location_edit.text() if not self.default_location_radio.isChecked() else None,
                'copy_documents': self.copy_documents_check.isChecked(),
                'compress_images': self.compress_images_check.isChecked(),
                'backup': {
                    'enabled': self.backup_check.isChecked(),
                    'frequency': self.backup_frequency_combo.currentText(),
                    'keep_count': self.backup_count_spin.value()
                }
            }

        # Save default researcher for future use
        if self.researcher_edit.text().strip():
            self.settings.setValue("default_researcher", self.researcher_edit.text().strip())

        # Emit appropriate signal
        if self.is_new:
            self.assembly_created.emit(assembly_data)
        else:
            self.assembly_updated.emit(assembly_data)

        self.accept()