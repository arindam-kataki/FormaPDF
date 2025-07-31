"""
Updated PDFLinkControlPanel to work with RawLinkIntegration
Key changes:
1. Updated constructor to accept RawLinkIntegration
2. Updated signal connections to use rawLinksExtracted instead of linkExtractionCompleted
3. Added methods to handle raw links
4. Updated display methods to work with raw link data
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QTabWidget, QSpinBox, QCheckBox, QGroupBox,
    QProgressBar, QMessageBox, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont
from typing import Dict, List, Any
import csv

# Import the RawLinkIntegration and related classes
from ui.a_raw_link_overlay_manager import RawLinkIntegration
from ui.a_raw_link_manager import LinkType


class DisplayLink:
    """Simple display object for raw links in the UI"""

    def __init__(self, raw_link: dict, page_index: int, link_index: int):
        self.raw_link = raw_link
        self.page_index = page_index
        self.link_index = link_index

        # Extract basic info for display
        self.id = f"page_{page_index}_link_{link_index}"
        self.description = self._extract_description()
        self.link_type = self._extract_type()
        self.bounds = self._extract_bounds()
        self.target = self._extract_target()

    def _extract_description(self) -> str:
        """Extract description from raw link"""
        try:
            # Try to get URI or other meaningful info
            if 'uri' in self.raw_link:
                uri = self.raw_link['uri']
                if uri:
                    return f"External: {uri[:50]}..." if len(uri) > 50 else f"External: {uri}"

            if 'page' in self.raw_link:
                return f"Page: {self.raw_link['page'] + 1}"

            if 'to' in self.raw_link:
                to_info = self.raw_link['to']
                if isinstance(to_info, dict) and 'page' in to_info:
                    return f"Page: {to_info['page'] + 1}"

            return f"Link {self.link_index + 1}"

        except Exception:
            return f"Link {self.link_index + 1}"

    def _extract_type(self) -> LinkType:
        """Extract link type from raw link"""
        try:
            import fitz
            link_kind = self.raw_link.get('kind', fitz.LINK_NONE)
            type_map = {
                fitz.LINK_GOTO: LinkType.GOTO,
                fitz.LINK_URI: LinkType.URI,
                fitz.LINK_LAUNCH: LinkType.LAUNCH,
                fitz.LINK_GOTOR: LinkType.GOTOR,
                fitz.LINK_NAMED: LinkType.NAMED
            }
            return type_map.get(link_kind, LinkType.UNKNOWN)
        except:
            return LinkType.UNKNOWN

    def _extract_bounds(self):
        """Extract bounds from raw link"""
        try:
            from PyQt6.QtCore import QRectF
            link_rect = self.raw_link['from']
            return QRectF(link_rect.x0, link_rect.y0, link_rect.width, link_rect.height)
        except:
            from PyQt6.QtCore import QRectF
            return QRectF(0, 0, 0, 0)

    def _extract_target(self) -> str:
        """Extract target from raw link"""
        try:
            if 'uri' in self.raw_link:
                return self.raw_link['uri']
            if 'page' in self.raw_link:
                return f"Page {self.raw_link['page'] + 1}"
            if 'to' in self.raw_link:
                to_info = self.raw_link['to']
                if isinstance(to_info, dict) and 'page' in to_info:
                    return f"Page {to_info['page'] + 1}"
            return "Unknown"
        except:
            return "Unknown"


class LinkListWidget(QListWidget):
    """Custom list widget for displaying links"""

    linkClicked = pyqtSignal(object)  # DisplayLink
    linkDoubleClicked = pyqtSignal(object)  # DisplayLink

    def __init__(self, parent=None):
        super().__init__(parent)

        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def add_link(self, display_link: DisplayLink):
        """Add a link to the list"""
        item = QListWidgetItem()
        item.setText(f"{display_link.description} ({display_link.link_type.value})")
        item.setData(Qt.ItemDataRole.UserRole, display_link)
        self.addItem(item)

    def clear_links(self):
        """Clear all links"""
        self.clear()

    def get_selected_link(self):
        """Get currently selected link"""
        current_item = self.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def _on_item_clicked(self, item):
        """Handle item click"""
        link = item.data(Qt.ItemDataRole.UserRole)
        if link:
            self.linkClicked.emit(link)

    def _on_item_double_clicked(self, item):
        """Handle item double click"""
        link = item.data(Qt.ItemDataRole.UserRole)
        if link:
            self.linkDoubleClicked.emit(link)


class LinkStatsWidget(QWidget):
    """Widget for displaying link statistics"""

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
    Main control panel for PDF link management - UPDATED for RawLinkIntegration
    Provides UI for viewing, navigating, and managing PDF hyperlinks
    """

    # Signals
    linkActivated = pyqtSignal(object)  # DisplayLink
    linkHighlighted = pyqtSignal(object)  # DisplayLink
    overlayVisibilityChanged = pyqtSignal(bool)
    pageNavigationRequested = pyqtSignal(int)

    def __init__(self, link_integration: RawLinkIntegration, parent=None):
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

        print("📎 PDFLinkControlPanel initialized (RawLinkIntegration)")

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

    def _create_control_buttons(self, layout):
        """Create control buttons"""
        button_layout = QHBoxLayout()

        # Page navigation
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)
        self.page_spinbox.valueChanged.connect(self._on_page_changed)

        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Page:"))
        page_layout.addWidget(self.page_spinbox)

        # Overlay toggle
        self.overlay_toggle = QCheckBox("Show Link Overlays")
        self.overlay_toggle.setChecked(True)
        self.overlay_toggle.toggled.connect(self._toggle_overlay_visibility)

        # Refresh button
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.clicked.connect(self._refresh_links)

        button_layout.addLayout(page_layout)
        button_layout.addWidget(self.overlay_toggle)
        button_layout.addWidget(refresh_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _create_current_page_tab(self):
        """Create current page links tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Stats widget
        self.current_page_stats = LinkStatsWidget()
        layout.addWidget(self.current_page_stats)

        # Links list
        self.current_page_list = LinkListWidget()
        self.current_page_list.linkClicked.connect(self._on_link_clicked)
        self.current_page_list.linkDoubleClicked.connect(self._on_link_double_clicked)
        layout.addWidget(self.current_page_list)

        self.tab_widget.addTab(widget, "Current Page")

    def _create_all_links_tab(self):
        """Create all links tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Type:"))

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        for link_type in LinkType:
            self.type_filter.addItem(link_type.value)
        self.type_filter.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.type_filter)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # All links list
        self.all_links_list = LinkListWidget()
        self.all_links_list.linkClicked.connect(self._on_link_clicked)
        self.all_links_list.linkDoubleClicked.connect(self._on_link_double_clicked)
        layout.addWidget(self.all_links_list)

        self.tab_widget.addTab(widget, "All Links")

    def _create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Security settings
        security_group = QGroupBox("Security Settings")
        security_layout = QVBoxLayout(security_group)

        self.allow_external_urls = QCheckBox("Allow external URLs")
        self.allow_external_urls.setChecked(True)
        security_layout.addWidget(self.allow_external_urls)

        self.allow_file_launch = QCheckBox("Allow file launch")
        self.allow_file_launch.setChecked(True)
        security_layout.addWidget(self.allow_file_launch)

        self.confirm_external = QCheckBox("Confirm external actions")
        self.confirm_external.setChecked(True)
        security_layout.addWidget(self.confirm_external)

        layout.addWidget(security_group)

        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QVBoxLayout(perf_group)

        self.cache_links_check = QCheckBox("Cache extracted links")
        self.cache_links_check.setChecked(True)
        perf_layout.addWidget(self.cache_links_check)

        cache_size_layout = QHBoxLayout()
        cache_size_layout.addWidget(QLabel("Cache size:"))
        self.cache_size_spinbox = QSpinBox()
        self.cache_size_spinbox.setRange(10, 500)
        self.cache_size_spinbox.setValue(100)
        cache_size_layout.addWidget(self.cache_size_spinbox)
        cache_size_layout.addStretch()
        perf_layout.addLayout(cache_size_layout)

        layout.addWidget(perf_group)

        # Action buttons
        action_layout = QHBoxLayout()

        apply_button = QPushButton("✅ Apply Settings")
        apply_button.clicked.connect(self.apply_settings)
        action_layout.addWidget(apply_button)

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
        """Connect signals from link integration - UPDATED for RawLinkIntegration"""
        if self.link_integration:
            if self.link_integration.link_manager:
                # Connect to rawLinksExtracted instead of linkExtractionCompleted
                self.link_integration.link_manager.rawLinksExtracted.connect(
                    self._on_raw_links_extracted)

            if self.link_integration.overlay_manager:
                # Connect overlay manager signals if available
                if hasattr(self.link_integration.overlay_manager, 'overlaysUpdated'):
                    self.link_integration.overlay_manager.overlaysUpdated.connect(
                        self._on_overlays_updated)

    def _on_raw_links_extracted(self, page_index: int, raw_links: List[dict]):
        """Handle raw links extracted signal - NEW METHOD"""
        print(f"📎 Control panel received {len(raw_links)} raw links for page {page_index + 1}")

        # If this is the current page, update the display
        if page_index == self.current_page:
            self._update_current_page_links()

        # Update all links if needed
        self._schedule_update()

    def _create_display_link_from_raw(self, raw_link: dict, page_index: int, link_index: int) -> DisplayLink:
        """Create a DisplayLink from raw link data - NEW METHOD"""
        return DisplayLink(raw_link, page_index, link_index)

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
            if hasattr(pdf_document, '__len__'):
                self.page_spinbox.setMaximum(len(pdf_document))
            elif hasattr(pdf_document, 'doc') and hasattr(pdf_document.doc, '__len__'):
                self.page_spinbox.setMaximum(len(pdf_document.doc))
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
                    display_link = self._create_display_link_from_raw(raw_link, self.current_page, i)
                    if display_link:
                        links.append(display_link)
                        self.current_page_list.add_link(display_link)

                # Update stats
                link_types = {}
                for link in links:
                    type_name = link.link_type.value
                    link_types[type_name] = link_types.get(type_name, 0) + 1

                self.current_page_stats.update_stats(
                    total_links=len(links),
                    page_links=len(links),
                    link_types=link_types
                )

                self.current_links = links

                print(f"📎 Updated current page display: {len(links)} links")

    def _schedule_update(self):
        """Schedule a delayed update"""
        self.update_timer.start(100)  # 100ms delay

    def _perform_delayed_update(self):
        """Perform delayed update of all links"""
        # Update current page
        self._update_current_page_links()

        # Update all links tab (if needed)
        # This could be expensive, so only do it when the tab is active
        if self.tab_widget.currentIndex() == 1:  # All links tab
            self._update_all_links()

    def _update_all_links(self):
        """Update all links display"""
        self.all_links_list.clear_links()

        if not self.link_integration or not hasattr(self.link_integration, 'link_manager'):
            return

        # This could be expensive for large documents
        # Consider implementing pagination or lazy loading
        link_manager = self.link_integration.link_manager
        if hasattr(link_manager, 'pdf_document') and link_manager.pdf_document:
            doc = link_manager.pdf_document
            if hasattr(doc, '__len__'):
                doc_len = len(doc)
            elif hasattr(doc, 'doc') and hasattr(doc.doc, '__len__'):
                doc_len = len(doc.doc)
            else:
                return

            # Limit to first 20 pages for performance
            max_pages = min(doc_len, 20)

            for page_index in range(max_pages):
                if hasattr(link_manager, 'get_raw_page_links'):
                    raw_links = link_manager.get_raw_page_links(page_index)

                    for i, raw_link in enumerate(raw_links):
                        display_link = self._create_display_link_from_raw(raw_link, page_index, i)
                        if display_link:
                            self.all_links_list.add_link(display_link)

    # Event handlers
    def _on_page_changed(self, page_number):
        """Handle page change from spinbox"""
        page_index = page_number - 1
        self.set_current_page(page_index)
        self.pageNavigationRequested.emit(page_index)

    def _toggle_overlay_visibility(self):
        """Toggle overlay visibility"""
        visible = self.overlay_toggle.isChecked()
        self.overlayVisibilityChanged.emit(visible)

        if self.link_integration and hasattr(self.link_integration, 'overlay_manager'):
            if hasattr(self.link_integration.overlay_manager, 'set_overlays_visible'):
                self.link_integration.overlay_manager.set_overlays_visible(visible)

    def _refresh_links(self):
        """Refresh links for current page"""
        if self.link_integration and hasattr(self.link_integration.link_manager, 'raw_links_cache'):
            # Clear cache for current page
            cache = self.link_integration.link_manager.raw_links_cache
            if self.current_page in cache:
                del cache[self.current_page]

        # Trigger re-extraction
        self._update_current_page_links()

    def _on_link_clicked(self, display_link: DisplayLink):
        """Handle link click"""
        print(f"📎 Link clicked: {display_link.description}")
        self.linkHighlighted.emit(display_link)

    def _on_link_double_clicked(self, display_link: DisplayLink):
        """Handle link double click"""
        print(f"📎 Link double-clicked: {display_link.description}")
        self.linkActivated.emit(display_link)

        # Also trigger the raw link manager's click handler
        if self.link_integration and hasattr(self.link_integration.link_manager, 'handle_raw_link_click'):
            self.link_integration.link_manager.handle_raw_link_click(
                display_link.raw_link,
                display_link.page_index,
                display_link.link_index
            )

    def _apply_filters(self):
        """Apply filters to all links display"""
        # TODO: Implement filtering
        pass

    def _clear_cache(self):
        """Clear link cache"""
        if self.link_integration and hasattr(self.link_integration.link_manager, 'raw_links_cache'):
            self.link_integration.link_manager.raw_links_cache.clear()
            print("🧹 Link cache cleared")

    def _export_links(self):
        """Export links to file"""
        # TODO: Implement export functionality
        QMessageBox.information(self, "Export", "Export functionality not yet implemented")

    def _on_overlays_updated(self, page_index: int, overlay_count: int):
        """Handle overlay update signals"""
        print(f"📎 Overlays updated for page {page_index + 1}: {overlay_count} overlays")

    def apply_settings(self):
        """Apply current settings to link manager"""
        if not self.link_integration or not self.link_integration.link_manager:
            return

        link_manager = self.link_integration.link_manager

        # Apply security settings
        if hasattr(link_manager, 'allow_external_urls'):
            link_manager.allow_external_urls = self.allow_external_urls.isChecked()
        if hasattr(link_manager, 'allow_file_launch'):
            link_manager.allow_file_launch = self.allow_file_launch.isChecked()
        if hasattr(link_manager, 'confirm_external_actions'):
            link_manager.confirm_external_actions = self.confirm_external.isChecked()

        # Apply performance settings
        if hasattr(link_manager, 'max_cache_size'):
            link_manager.max_cache_size = self.cache_size_spinbox.value()

        print("⚙️ Link settings applied")

    def get_current_links(self) -> List[DisplayLink]:
        """Get links for current page"""
        return self.current_links.copy()

    def highlight_link(self, display_link: DisplayLink):
        """Highlight a specific link in the lists"""
        # Highlight in current page list
        for i in range(self.current_page_list.count()):
            item = self.current_page_list.item(i)
            link = item.data(Qt.ItemDataRole.UserRole)
            if link and link.id == display_link.id:
                self.current_page_list.setCurrentItem(item)
                break

        # Highlight in overlay manager
        if self.link_integration and self.link_integration.overlay_manager:
            if hasattr(self.link_integration.overlay_manager, 'highlight_link'):
                self.link_integration.overlay_manager.highlight_link(display_link)


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

        return False