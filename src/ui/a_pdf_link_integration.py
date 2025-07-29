"""
Main Window Integration for PDF Hyperlinks
Complete integration of PDF hyperlink functionality into the main application
"""

from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDialogButtonBox, QTextEdit, QDockWidget
)
from PyQt6.QtCore import Qt, pyqtSlot, QUrl
from PyQt6.QtGui import QDesktopServices
import webbrowser
import os

# Import the PDF link components
from a_pdf_link_manager import PDFLinkManager, PDFLink, LinkType
from a_pdf_link_overlay_manager import PDFLinkIntegration
from a_pdf_link_control_panel import PDFLinkControlPanel, PDFLinkVoiceIntegration


class ExternalLinkConfirmDialog(QDialog):
    """Dialog for confirming external link navigation"""

    def __init__(self, url: str, parent=None):
        super().__init__(parent)

        self.url = url
        self.setWindowTitle("External Link Confirmation")
        self.setModal(True)
        self.resize(450, 200)

        layout = QVBoxLayout(self)

        # Warning message
        warning_label = QLabel("⚠️ You are about to navigate to an external website:")
        layout.addWidget(warning_label)

        # URL display
        url_display = QTextEdit()
        url_display.setPlainText(url)
        url_display.setReadOnly(True)
        url_display.setMaximumHeight(60)
        layout.addWidget(url_display)

        # Security notice
        security_label = QLabel(
            "Please verify this is a trusted website before continuing.\n"
            "Malicious websites may attempt to harm your computer."
        )
        security_label.setWordWrap(True)
        layout.addWidget(security_label)

        # Buttons
        button_box = QDialogButtonBox()

        continue_btn = QPushButton("🌐 Continue")
        continue_btn.clicked.connect(self.accept)
        button_box.addButton(continue_btn, QDialogButtonBox.ButtonRole.AcceptRole)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

        layout.addWidget(button_box)

