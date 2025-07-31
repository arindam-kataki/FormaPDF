"""
PDF Link Control Panel - PyQt6 Widget
User interface for managing and interacting with PDF hyperlinks
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QCheckBox, QSlider, QGroupBox, QTextEdit, QComboBox,
    QSpinBox, QProgressBar, QToolButton, QFrame, QSplitter, QTabWidget,
    QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QAction
from typing import List, Optional, Dict, Any

from a_pdf_link_manager import PDFLink, LinkType, PDFLinkManager
from a_pdf_link_overlay_manager import PDFLinkIntegration

class LinkListWidget(QListWidget):
    """Custom list widget for displaying PDF links"""

    linkActivated = pyqtSignal(object)  # PDFLink
    linkHovered = pyqtSignal(object)  # PDFLink

    def __init__(self, parent=None):
        super().__init__(parent)

        # Setup appearance
        self.setAlternatingRowColors(True)
        self.setMouseTracking(True)

        # Connect signals
        self.itemClicked.connect(self._on_item_clicked)
        self.itemEntered.connect(self._on_item_entered)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def add_link(self, pdf_link: PDFLink):
        """Add a PDF link to the list"""
        item = QListWidgetItem()

        # Set text
        display_text = f"{self._get_link_icon(pdf_link.link_type)} {pdf_link.description}"
        item.setText(display_text)

        # Store link data
        item.setData(Qt.ItemDataRole.UserRole, pdf_link)

        # Set tooltip
        tooltip = self._create_link_tooltip(pdf_link)
        item.setToolTip(tooltip)

        # Set color based on link type
        color = self._get_link_color(pdf_link.link_type)
        item.setForeground(color)

        self.addItem(item)

    def clear_links(self):
        """Clear all links from the list"""
        self.clear()

    def _get_link_icon(self, link_type: LinkType) -> str:
        """Get emoji icon for link type"""
        icons = {
            LinkType.GOTO: "📄",
            LinkType.URI: "🌐",
            LinkType.LAUNCH: "📁",
            LinkType.GOTOR: "📚",
            LinkType.NAMED: "📍",
            LinkType.UNKNOWN: "❓"
        }
        return icons.get(link_type, "🔗")

    def _get_link_color(self, link_type: LinkType) -> QColor:
        """Get color for link type"""
        colors = {
            LinkType.GOTO: QColor(0, 153, 0),  # Green
            LinkType.URI: QColor(0, 102, 204),  # Blue
            LinkType.LAUNCH: QColor(153, 0, 204),  # Purple
            LinkType.GOTOR: QColor(153, 0, 204),  # Purple
            LinkType.NAMED: QColor(0, 153, 0),  # Green
            LinkType.UNKNOWN: QColor(102, 102, 102)  # Gray
        }
        return colors.get(link_type, QColor(0, 0, 0))

    def _create_link_tooltip(self, pdf_link: PDFLink) -> str:
        """Create detailed tooltip for link"""
        tooltip = f"<b>{pdf_link.description}</b><br>"
        tooltip += f"Type: {pdf_link.link_type.value.title()}<br>"
        tooltip += f"Page: {pdf_link.page_index + 1}<br>"
        tooltip += f"Position: ({pdf_link.bounds.x():.1f}, {pdf_link.bounds.y():.1f})<br>"
        tooltip += f"Size: {pdf_link.bounds.width():.1f} × {pdf_link.bounds.height():.1f}"

        # Add target info
        if pdf_link.link_type == LinkType.GOTO:
            target_page = pdf_link.target.get('page', 0)
            tooltip += f"<br>Target: Page {target_page + 1}"
        elif pdf_link.link_type == LinkType.URI:
            url = pdf_link.target.get('url', '')
            tooltip += f"<br>URL: {url[:50]}{'...' if len(url) > 50 else ''}"

        return tooltip

    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click"""
        pdf_link = item.data(Qt.ItemDataRole.UserRole)
        if pdf_link:
            self.linkActivated.emit(pdf_link)

    def _on_item_entered(self, item: QListWidgetItem):
        """Handle item hover"""
        pdf_link = item.data(Qt.ItemDataRole.UserRole)
        if pdf_link:
            self.linkHovered.emit(pdf_link)

    def _show_context_menu(self, position):
        """Show context menu for link"""
        item = self.itemAt(position)
        if not item:
            return

        pdf_link = item.data(Qt.ItemDataRole.UserRole)
        if not pdf_link:
            return

        menu = QMenu(self)

        # Add actions based on link type
        if pdf_link.link_type in [LinkType.GOTO, LinkType.NAMED]:
            navigate_action = QAction("📄 Navigate", self)
            navigate_action.triggered.connect(lambda: self.linkActivated.emit(pdf_link))
            menu.addAction(navigate_action)

        elif pdf_link.link_type == LinkType.URI:
            open_action = QAction("🌐 Open URL", self)
            open_action.triggered.connect(lambda: self.linkActivated.emit(pdf_link))
            menu.addAction(open_action)

            copy_action = QAction("📋 Copy URL", self)
            copy_action.triggered.connect(lambda: self._copy_url(pdf_link))
            menu.addAction(copy_action)

        # Common actions
        menu.addSeparator()

        info_action = QAction("ℹ️ Link Info", self)
        info_action.triggered.connect(lambda: self._show_link_info(pdf_link))
        menu.addAction(info_action)

        menu.exec(self.mapToGlobal(position))

    def _copy_url(self, pdf_link: PDFLink):
        """Copy URL to clipboard"""
        if pdf_link.link_type == LinkType.URI:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(pdf_link.target.get('url', ''))

    def _show_link_info(self, pdf_link: PDFLink):
        """Show detailed link information dialog"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Link Information")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        # Create info text
        info_text = QTextEdit()
        info_text.setReadOnly(True)

        info_html = f"""
        <h3>Link Details</h3>
        <table>
        <tr><td><b>ID:</b></td><td>{pdf_link.id}</td></tr>
        <tr><td><b>Type:</b></td><td>{pdf_link.link_type.value.title()}</td></tr>
        <tr><td><b>Page:</b></td><td>{pdf_link.page_index + 1}</td></tr>
        <tr><td><b>Description:</b></td><td>{pdf_link.description}</td></tr>
        <tr><td><b>X Position:</b></td><td>{pdf_link.bounds.x():.2f}</td></tr>
        <tr><td><b>Y Position:</b></td><td>{pdf_link.bounds.y():.2f}</td></tr>
        <tr><td><b>Width:</b></td><td>{pdf_link.bounds.width():.2f}</td></tr>
        <tr><td><b>Height:</b></td><td>{pdf_link.bounds.height():.2f}</td></tr>
        </table>

        <h4>Target Information</h4>
        <pre>{str(pdf_link.target)}</pre>

        <h4>Raw Link Data</h4>
        <pre>{str(pdf_link.raw_link)}</pre>
        """

        info_text.setHtml(info_html)
        layout.addWidget(info_text)

        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.exec()


class LinkStatsWidget(QWidget):
    """Widget showing link statistics"""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Stats labels
        self.total_links_label = QLabel("Total Links: 0")
        self.page_links_label = QLabel("This Page: 0")
        self.link_types_label = QLabel("Types: None")

        layout.addWidget(self.total_links_label)
        layout.addWidget(self.page_links_label)
        layout.addWidget(self.link_types_label)

        # Progress bar for link extraction
        self.extraction_progress = QProgressBar()
        self.extraction_progress.setVisible(False)
        layout.addWidget(self.extraction_progress)

    def update_stats(self, total_links: int, page_links: int, link_types: Dict[str, int]):
        """Update displayed statistics"""
        self.total_links_label.setText(f"Total Links: {total_links}")
        self.page_links_label.setText(f"This Page: {page_links}")

        # Format link types
        if link_types:
            types_text = ", ".join([f"{t}: {c}" for t, c in link_types.items()])
            self.link_types_label.setText(f"Types: {types_text}")
        else:
            self.link_types_label.setText("Types: None")

    def show_extraction_progress(self, visible: bool = True):
        """Show or hide extraction progress bar"""
        self.extraction_progress.setVisible(visible)
        if visible:
            self.extraction_progress.setRange(0, 0)  # Indeterminate


class PDFLinkControlPanel(QWidget):
    """
    Main control panel for PDF link management
    Provides UI for viewing, navigating, and managing PDF hyperlinks
    """

    # Signals
    linkActivated = pyqtSignal(object)  # PDFLink
    linkHighlighted = pyqtSignal(object)  # PDFLink
    overlayVisibilityChanged = pyqtSignal(bool)
    pageNavigationRequested = pyqtSignal(int)

    def __init__(self, link_integration: PDFLinkIntegration, parent=None):
        super().__init__(parent)

        self.link_integration = link_integration
        self.current_page = 0
        self.current_links = []

        # Setup UI
        self._setup_ui()
        self._connect_signals()

        # Timer for delayed updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._perform_delayed_update)
        self.update_timer.setSingleShot(True)

        print("📎 PDFLinkControlPanel initialized")

    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("PDF Links")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Control buttons
        self._create_control_buttons(layout)

        # Tabs for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Current page links tab
        self._create_current_page_tab()

        # All links tab
        self._create_all_links_tab()

        # Settings tab
        self._create_settings_tab()

        # Stats widget
        self.stats_widget = LinkStatsWidget()
        layout.addWidget(self.stats_widget)

    def _create_control_buttons(self, layout):
        """Create control buttons"""
        button_layout = QHBoxLayout()

        # Toggle overlay visibility
        self.overlay_toggle = QPushButton("👁️ Show Links")
        self.overlay_toggle.setCheckable(True)
        self.overlay_toggle.setChecked(True)
        self.overlay_toggle.clicked.connect(self._toggle_overlay_visibility)
        button_layout.addWidget(self.overlay_toggle)

        # Refresh links
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._refresh_links)
        button_layout.addWidget(self.refresh_button)

        layout.addLayout(button_layout)

    def _create_current_page_tab(self):
        """Create tab for current page links"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Page selector
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Page:"))

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.valueChanged.connect(self._on_page_changed)
        page_layout.addWidget(self.page_spinbox)

        page_layout.addStretch()
        layout.addLayout(page_layout)

        # Current page links list
        self.current_page_list = LinkListWidget()
        self.current_page_list.linkActivated.connect(self.linkActivated)
        self.current_page_list.linkHovered.connect(self.linkHighlighted)
        layout.addWidget(self.current_page_list)

        self.tab_widget.addTab(widget, "Current Page")

    def _create_all_links_tab(self):
        """Create tab for all document links"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self.link_type_filter = QComboBox()
        self.link_type_filter.addItems(
            ["All Types", "Internal Links", "External URLs", "File Links", "Named Destinations"])
        self.link_type_filter.currentTextChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.link_type_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # All links list
        self.all_links_list = LinkListWidget()
        self.all_links_list.linkActivated.connect(self.linkActivated)
        self.all_links_list.linkHovered.connect(self.linkHighlighted)
        layout.addWidget(self.all_links_list)

        self.tab_widget.addTab(widget, "All Links")

    def _create_settings_tab(self):
        """Create tab for link settings"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Overlay settings group
        overlay_group = QGroupBox("Overlay Settings")
        overlay_layout = QVBoxLayout(overlay_group)

        # Overlay opacity
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)

        self.opacity_label = QLabel("70%")
        opacity_layout.addWidget(self.opacity_label)
        overlay_layout.addLayout(opacity_layout)

        # Show tooltips
        self.show_tooltips_check = QCheckBox("Show tooltips on hover")
        self.show_tooltips_check.setChecked(True)
        overlay_layout.addWidget(self.show_tooltips_check)

        layout.addWidget(overlay_group)

        # Security settings group
        security_group = QGroupBox("Security Settings")
        security_layout = QVBoxLayout(security_group)

        self.allow_external_urls = QCheckBox("Allow external URLs")
        self.allow_external_urls.setChecked(True)
        security_layout.addWidget(self.allow_external_urls)

        self.allow_file_launch = QCheckBox("Allow file launching")
        self.allow_file_launch.setChecked(False)
        security_layout.addWidget(self.allow_file_launch)

        self.confirm_external = QCheckBox("Confirm external actions")
        self.confirm_external.setChecked(True)
        security_layout.addWidget(self.confirm_external)

        layout.addWidget(security_group)

        # Performance settings group
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QVBoxLayout(performance_group)

        self.cache_links_check = QCheckBox("Cache extracted links")
        self.cache_links_check.setChecked(True)
        performance_layout.addWidget(self.cache_links_check)

        # Cache size
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(QLabel("Max cache size:"))

        self.cache_size_spinbox = QSpinBox()
        self.cache_size_spinbox.setRange(10, 10000)
        self.cache_size_spinbox.setValue(1000)
        cache_layout.addWidget(self.cache_size_spinbox)

        cache_layout.addStretch()
        performance_layout.addLayout(cache_layout)

        layout.addWidget(performance_group)

        # Action buttons
        action_layout = QHBoxLayout()

        clear_cache_button = QPushButton("🧹 Clear Cache")
        clear_cache_button.clicked.connect(self._clear_cache)
        action_layout.addWidget(clear_cache_button)

        export_links_button = QPushButton("📤 Export Links")
        export_links_button.clicked.connect(self._export_links)
        action_layout.addWidget(export_links_button)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        layout.addStretch()
        self.tab_widget.addTab(widget, "Settings")

    def _connect_signals(self):
        """Connect signals from link integration"""
        if self.link_integration:
            if self.link_integration.link_manager:
                self.link_integration.link_manager.linkExtractionCompleted.connect(
                    self._on_links_extracted)

            if self.link_integration.overlay_manager:
                self.link_integration.overlay_manager.overlaysUpdated.connect(
                    self._on_overlays_updated)

    def set_current_page(self, page_index: int):
        """Set current page and update display"""
        self.current_page = page_index
        self.page_spinbox.setValue(page_index + 1)
        self._update_current_page_links()

    def set_document(self, pdf_document, document_path: str = ""):
        """Set PDF document"""
        if self.link_integration:
            self.link_integration.set_pdf_document(pdf_document, document_path)

        # Update page spinner range
        if pdf_document:
            self.page_spinbox.setMaximum(len(pdf_document))
        else:
            self.page_spinbox.setMaximum(1)

        # Clear existing content
        self.current_page_list.clear_links()
        self.all_links_list.clear_links()

        # Trigger update
        self._schedule_update()

    def _update_current_page_links(self):
        """Update links display for current page - UPDATED for raw links"""
        self.current_page_list.clear_links()

        if self.link_integration and hasattr(self.link_integration, 'link_manager'):
            # Get raw links instead of PDFLink objects
            if hasattr(self.link_integration.link_manager, 'get_raw_page_links'):
                # New raw link manager
                raw_links = self.link_integration.link_manager.get_raw_page_links(self.current_page)

                # Convert raw links to display format
                links = []
                for i, raw_link in enumerate(raw_links):
                    # Create minimal display object
                    display_link = self._create_display_link_from_raw(raw_link, self.current_page, i)
                    if display_link:
                        links.append(display_link)
                        self.current_page_list.add_link(display_link)

                self.current_links = links
            else:
                # Fallback to old method
                links = self.link_integration.get_page_links(self.current_page)
                self.current_links = links

                for link in links:
                    self.current_page_list.add_link(link)

            # Update stats
            self._update_stats()

    def _update_current_page_links_full(self):
        """Update links display for current page"""
        self.current_page_list.clear_links()

        if self.link_integration and self.link_integration.link_manager:
            links = self.link_integration.get_page_links(self.current_page)
            self.current_links = links

            for link in links:
                self.current_page_list.add_link(link)

            # Update stats
            self._update_stats()

    def _create_display_link_from_raw(self, raw_link: dict, page_index: int, link_index: int):
        """Create a minimal display object from raw link data"""
        try:
            from .a_pdf_link_manager import PDFLink, LinkType
            from PyQt6.QtCore import QRectF

            # Extract bounds
            link_rect = raw_link.get('from', None)
            if link_rect:
                bounds = QRectF(link_rect.x0, link_rect.y0, link_rect.width, link_rect.height)
            else:
                bounds = QRectF(0, 0, 0, 0)

            # Get basic type
            link_kind = raw_link.get('kind', 0)
            type_map = {
                1: LinkType.GOTO,
                2: LinkType.URI,
                3: LinkType.LAUNCH,
                4: LinkType.GOTOR,
                5: LinkType.NAMED
            }
            link_type = type_map.get(link_kind, LinkType.UNKNOWN)

            # Create basic description
            if link_kind == 1:  # GOTO
                description = f"Go to page {raw_link.get('page', 0) + 1}"
            elif link_kind == 2:  # URI
                uri = raw_link.get('uri', '')
                description = f"External URL: {uri[:50]}{'...' if len(uri) > 50 else ''}"
            else:
                description = f"{link_type.value.title()} link"

            # Create minimal PDFLink for display compatibility
            return PDFLink(
                id=f"raw_link_{page_index}_{link_index}",
                link_type=link_type,
                bounds=bounds,
                page_index=page_index,
                description=description,
                target={'_raw_data': raw_link, '_parsed': False},
                raw_link=raw_link
            )

        except Exception as e:
            print(f"❌ Error creating display link: {e}")
            return None

    def _update_all_links(self):
        """Update display of all document links"""
        self.all_links_list.clear_links()

        if not self.link_integration or not self.link_integration.link_manager:
            return

        # Show progress
        self.stats_widget.show_extraction_progress(True)

        # Extract all links (this might take time for large documents)
        try:
            all_links = self.link_integration.link_manager.get_all_page_links()

            for page_index, page_links in all_links.items():
                for link in page_links:
                    self.all_links_list.add_link(link)

            self._apply_filter()  # Apply current filter

        except Exception as e:
            print(f"❌ Error updating all links: {e}")
        finally:
            self.stats_widget.show_extraction_progress(False)

    def _apply_filter(self):
        """Apply filter to all links list"""
        filter_text = self.link_type_filter.currentText()

        # Show all items first
        for i in range(self.all_links_list.count()):
            item = self.all_links_list.item(i)
            item.setHidden(False)

        # Apply filter
        if filter_text != "All Types":
            filter_types = {
                "Internal Links": [LinkType.GOTO, LinkType.NAMED],
                "External URLs": [LinkType.URI],
                "File Links": [LinkType.LAUNCH, LinkType.GOTOR],
                "Named Destinations": [LinkType.NAMED]
            }

            allowed_types = filter_types.get(filter_text, [])

            for i in range(self.all_links_list.count()):
                item = self.all_links_list.item(i)
                pdf_link = item.data(Qt.ItemDataRole.UserRole)

                if pdf_link and pdf_link.link_type not in allowed_types:
                    item.setHidden(True)

    def _update_stats(self):
        """Update statistics display"""
        if not self.link_integration or not self.link_integration.link_manager:
            return

        # Count links by type for current page
        link_types = {}
        for link in self.current_links:
            type_name = link.link_type.value
            link_types[type_name] = link_types.get(type_name, 0) + 1

        # Get total links (from cache info)
        cache_info = self.link_integration.link_manager.get_cache_info()
        total_links = cache_info.get('total_cached_links', 0)

        self.stats_widget.update_stats(total_links, len(self.current_links), link_types)

    def _schedule_update(self):
        """Schedule a delayed update"""
        self.update_timer.start(200)  # 200ms delay

    def _perform_delayed_update(self):
        """Perform the actual update after delay"""
        self._update_current_page_links()

        # Only update all links if that tab is visible
        if self.tab_widget.currentIndex() == 1:  # All Links tab
            self._update_all_links()

    @pyqtSlot()
    def _toggle_overlay_visibility(self):
        """Toggle overlay visibility"""
        visible = self.overlay_toggle.isChecked()

        if self.link_integration:
            self.link_integration.set_links_visible(visible)

        # Update button text
        self.overlay_toggle.setText("👁️ Hide Links" if visible else "👁️ Show Links")

        self.overlayVisibilityChanged.emit(visible)

    @pyqtSlot()
    def _refresh_links(self):
        """Refresh link extraction"""
        if self.link_integration and self.link_integration.link_manager:
            self.link_integration.link_manager.clear_cache()

        self._schedule_update()

    @pyqtSlot(int)
    def _on_page_changed(self, page_number: int):
        """Handle page number change"""
        page_index = page_number - 1
        if page_index != self.current_page:
            self.current_page = page_index
            self.pageNavigationRequested.emit(page_index)
            self._update_current_page_links()

    @pyqtSlot(int)
    def _on_opacity_changed(self, value: int):
        """Handle opacity slider change"""
        opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")

        if self.link_integration and self.link_integration.overlay_manager:
            self.link_integration.overlay_manager.set_overlay_opacity(opacity)

    @pyqtSlot(int, list)
    def _on_links_extracted(self, page_index: int, links: List[PDFLink]):
        """Handle links extracted signal"""
        if page_index == self.current_page:
            self._update_current_page_links()

    @pyqtSlot(int, int)
    def _on_overlays_updated(self, page_index: int, overlay_count: int):
        """Handle overlays updated signal"""
        print(f"📎 Page {page_index + 1}: {overlay_count} overlays updated")

    @pyqtSlot()
    def _clear_cache(self):
        """Clear link cache"""
        if self.link_integration and self.link_integration.link_manager:
            self.link_integration.link_manager.clear_cache()
            self._schedule_update()

            QMessageBox.information(self, "Cache Cleared",
                                    "Link cache has been cleared successfully.")

    @pyqtSlot()
    def _export_links(self):
        """Export links to file"""
        if not self.link_integration or not self.link_integration.link_manager:
            QMessageBox.warning(self, "Export Error", "No links available to export.")
            return

        from PyQt6.QtWidgets import QFileDialog
        import json
        import csv

        # Get save file path
        file_path, filter_type = QFileDialog.getSaveFileName(
            self, "Export Links", "",
            "JSON Files (*.json);;CSV Files (*.csv);;Text Files (*.txt)"
        )

        if not file_path:
            return

        try:
            all_links = self.link_integration.link_manager.get_all_page_links()

            if filter_type.startswith("JSON"):
                self._export_as_json(file_path, all_links)
            elif filter_type.startswith("CSV"):
                self._export_as_csv(file_path, all_links)
            else:
                self._export_as_text(file_path, all_links)

            QMessageBox.information(self, "Export Complete",
                                    f"Links exported successfully to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export links:\n{str(e)}")

    def _export_as_json(self, file_path: str, all_links: Dict[int, List[PDFLink]]):
        """Export links as JSON"""
        import json

        export_data = {}
        for page_index, links in all_links.items():
            export_data[f"page_{page_index + 1}"] = []

            for link in links:
                link_data = {
                    "id": link.id,
                    "type": link.link_type.value,
                    "description": link.description,
                    "bounds": {
                        "x": link.bounds.x(),
                        "y": link.bounds.y(),
                        "width": link.bounds.width(),
                        "height": link.bounds.height()
                    },
                    "target": link.target
                }
                export_data[f"page_{page_index + 1}"].append(link_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def _export_as_csv(self, file_path: str, all_links: Dict[int, List[PDFLink]]):
        """Export links as CSV"""
        import csv

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(['Page', 'ID', 'Type', 'Description', 'X', 'Y', 'Width', 'Height', 'Target'])

            # Write data
            for page_index, links in all_links.items():
                for link in links:
                    writer.writerow([
                        page_index + 1,
                        link.id,
                        link.link_type.value,
                        link.description,
                        f"{link.bounds.x():.2f}",
                        f"{link.bounds.y():.2f}",
                        f"{link.bounds.width():.2f}",
                        f"{link.bounds.height():.2f}",
                        str(link.target)
                    ])

    def _export_as_text(self, file_path: str, all_links: Dict[int, List[PDFLink]]):
        """Export links as text"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("PDF Links Export\n")
            f.write("=" * 50 + "\n\n")

            for page_index, links in all_links.items():
                f.write(f"Page {page_index + 1}:\n")
                f.write("-" * 20 + "\n")

                if not links:
                    f.write("  No links found\n\n")
                    continue

                for i, link in enumerate(links, 1):
                    f.write(f"  {i}. {link.description}\n")
                    f.write(f"     Type: {link.link_type.value}\n")
                    f.write(f"     Position: ({link.bounds.x():.1f}, {link.bounds.y():.1f})\n")
                    f.write(f"     Size: {link.bounds.width():.1f} × {link.bounds.height():.1f}\n")
                    f.write(f"     Target: {link.target}\n\n")

                f.write("\n")

    def apply_settings(self):
        """Apply current settings to link manager"""
        if not self.link_integration or not self.link_integration.link_manager:
            return

        link_manager = self.link_integration.link_manager

        # Apply security settings
        link_manager.allow_external_urls = self.allow_external_urls.isChecked()
        link_manager.allow_file_launch = self.allow_file_launch.isChecked()
        link_manager.confirm_external_actions = self.confirm_external.isChecked()

        # Apply performance settings
        link_manager.cache_links = self.cache_links_check.isChecked()
        link_manager.max_cache_size = self.cache_size_spinbox.value()

        print("⚙️ Link settings applied")

    def get_current_links(self) -> List[PDFLink]:
        """Get links for current page"""
        return self.current_links.copy()

    def highlight_link(self, pdf_link: PDFLink):
        """Highlight a specific link in the lists"""
        # Highlight in current page list
        for i in range(self.current_page_list.count()):
            item = self.current_page_list.item(i)
            link = item.data(Qt.ItemDataRole.UserRole)
            if link and link.id == pdf_link.id:
                self.current_page_list.setCurrentItem(item)
                break

        # Highlight in overlay manager
        if self.link_integration and self.link_integration.overlay_manager:
            self.link_integration.overlay_manager.highlight_link(pdf_link)


# Voice Control Integration for Link Panel
class PDFLinkVoiceIntegration:
    """Voice control integration for the link control panel"""

    def __init__(self, control_panel: PDFLinkControlPanel):
        self.control_panel = control_panel
        self.voice_commands = {
            'show_links': ['show links', 'display links', 'enable overlays'],
            'hide_links': ['hide links', 'disable overlays', 'turn off links'],
            'next_link': ['next link', 'go to next link'],
            'previous_link': ['previous link', 'go to previous link'],
            'click_link': ['click link', 'activate link', 'follow link'],
            'refresh_links': ['refresh links', 'reload links', 'update links'],
            'export_links': ['export links', 'save links']
        }

    def handle_voice_command(self, command_text: str) -> bool:
        """Handle voice command for link operations"""
        command_lower = command_text.lower().strip()

        # Check for link visibility commands
        if any(cmd in command_lower for cmd in self.voice_commands['show_links']):
            self.control_panel.overlay_toggle.setChecked(True)
            self.control_panel._toggle_overlay_visibility()
            return True

        elif any(cmd in command_lower for cmd in self.voice_commands['hide_links']):
            self.control_panel.overlay_toggle.setChecked(False)
            self.control_panel._toggle_overlay_visibility()
            return True

        # Check for link navigation commands
        elif any(cmd in command_lower for cmd in self.voice_commands['refresh_links']):
            self.control_panel._refresh_links()
            return True

        elif any(cmd in command_lower for cmd in self.voice_commands['export_links']):
            self.control_panel._export_links()
            return True

        # Check for numbered link commands
        elif 'link' in command_lower and any(char.isdigit() for char in command_lower):
            return self._handle_numbered_link_command(command_lower)

        # Check for page navigation
        elif 'page' in command_lower and any(char.isdigit() for char in command_lower):
            return self._handle_page_navigation_command(command_lower)

        return False

    def _handle_numbered_link_command(self, command: str) -> bool:
        """Handle commands like 'click link 1', 'activate link 2'"""
        import re

        # Extract number from command
        numbers = re.findall(r'\d+', command)
        if not numbers:
            return False

        link_number = int(numbers[0]) - 1  # Convert to 0-based index

        # Get current page links
        current_links = self.control_panel.get_current_links()

        if 0 <= link_number < len(current_links):
            pdf_link = current_links[link_number]
            self.control_panel.linkActivated.emit(pdf_link)
            return True

        return False

    def _handle_page_navigation_command(self, command: str) -> bool:
        """Handle commands like 'go to page 5'"""
        import re

        numbers = re.findall(r'\d+', command)
        if not numbers:
            return False

        page_number = int(numbers[0])
        self.control_panel.page_spinbox.setValue(page_number)
        return True


if __name__ == '__main__':
    print("PDFLinkControlPanel - Use as module import")