from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget, QCheckBox, QPushButton, QHBoxLayout

from ui.a_pdf_link_integration import PDFLinkIntegration


class PDFLinkControlPanel(QWidget):
    """
    Control panel widget for link-related settings and debugging
    """

    def __init__(self, link_integration: PDFLinkIntegration, parent=None):
        super().__init__(parent)
        self.link_integration = link_integration
        self.init_ui()

    def init_ui(self):
        """Initialize the control panel UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("🔗 PDF Links")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Link visibility toggle
        self.visibility_checkbox = QCheckBox("Show clickable link overlays")
        self.visibility_checkbox.setChecked(True)
        self.visibility_checkbox.toggled.connect(self._on_visibility_toggled)
        layout.addWidget(self.visibility_checkbox)

        # Statistics display
        self.stats_label = QLabel("No links found")
        self.stats_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.stats_label)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Links")
        refresh_btn.clicked.connect(self._refresh_links)
        layout.addWidget(refresh_btn)

        # Debug controls
        debug_layout = QHBoxLayout()

        debug_btn = QPushButton("🐛 Debug Info")
        debug_btn.clicked.connect(self._show_debug_info)
        debug_layout.addWidget(debug_btn)

        layout.addLayout(debug_layout)

        # Update statistics periodically
        self._update_statistics()

    def _on_visibility_toggled(self, visible: bool):
        """Handle visibility toggle"""
        self.link_integration.toggle_link_visibility(visible)

    def _refresh_links(self):
        """Refresh link overlays"""
        if hasattr(self.link_integration, 'overlay_manager') and self.link_integration.overlay_manager:
            current_page = self.link_integration.overlay_manager.current_page
            current_zoom = self.link_integration.overlay_manager.current_zoom

            if current_page >= 0:
                self.link_integration.overlay_manager.update_page_links(current_page, current_zoom)

        self._update_statistics()

    def _update_statistics(self):
        """Update the statistics display"""
        stats = self.link_integration.get_link_statistics()

        if stats['total'] == 0:
            self.stats_label.setText("No links found on current page")
        else:
            type_breakdown = ", ".join([f"{count} {link_type}" for link_type, count in stats['by_type'].items()])
            self.stats_label.setText(f"{stats['total']} links: {type_breakdown}")

    def _show_debug_info(self):
        """Show debug information"""
        stats = self.link_integration.get_link_statistics()

        debug_text = f"Link Statistics:\n"
        debug_text += f"Total links: {stats['total']}\n"

        for link_type, count in stats['by_type'].items():
            debug_text += f"  {link_type}: {count}\n"

        print("🐛 Link Debug Info:")
        print(debug_text)

        # Could show in a dialog if needed
        if hasattr(self.link_integration.main_window, 'statusBar'):
            self.link_integration.main_window.statusBar().showMessage(
                f"Debug: {stats['total']} links found", 3000
            )
