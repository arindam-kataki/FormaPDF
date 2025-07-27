"""
Toolbar Widget for PDF Voice Editor
Extracted from main window class for better organization
"""

from PyQt6.QtWidgets import (
    QToolBar, QLabel, QSpinBox, QComboBox,
    QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QKeySequence, QAction


class ToolbarWidget(QToolBar):
    """
    Custom toolbar widget with all PDF navigation and view controls
    """

    # Signals for toolbar actions
    openRequested = pyqtSignal()
    saveRequested = pyqtSignal()
    previousPageRequested = pyqtSignal()
    nextPageRequested = pyqtSignal()
    pageJumpRequested = pyqtSignal(int)  # page number (1-based)
    zoomInRequested = pyqtSignal()
    zoomOutRequested = pyqtSignal()
    zoomToLevelRequested = pyqtSignal(float)  # zoom level (e.g. 1.5 for 150%)
    fitWidthRequested = pyqtSignal()
    fitPageRequested = pyqtSignal()
    gridToggleRequested = pyqtSignal()
    infoRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)

        # Toolbar configuration
        self.setMovable(False)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # State tracking
        self.current_page = 1
        self.total_pages = 1
        self.current_zoom = 100  # percentage
        self.grid_enabled = False

        # Create all toolbar sections
        self._create_file_section()
        self._create_navigation_section()
        self._create_zoom_section()
        self._create_view_section()
        self._create_info_section()

        # Set initial state
        self._update_navigation_state()

    def _create_file_section(self):
        """Create file operations section"""
        # Open action
        self.open_action = QAction("📁 Open", self)
        self.open_action.setToolTip("Open PDF file (Ctrl+O)")
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.openRequested.emit)
        self.addAction(self.open_action)

        # Save action
        self.save_action = QAction("💾 Save", self)
        self.save_action.setToolTip("Save form data (Ctrl+S)")
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.saveRequested.emit)
        self.addAction(self.save_action)

        self.addSeparator()

    def _create_navigation_section(self):
        """Create page navigation section"""
        # Previous page
        self.prev_action = QAction("⬅️", self)
        self.prev_action.setToolTip("Previous page (Ctrl+Left)")
        self.prev_action.setShortcut("Ctrl+Left")
        self.prev_action.triggered.connect(self.previousPageRequested.emit)
        self.addAction(self.prev_action)

        # Page number input
        page_label = QLabel("Page:")
        self.addWidget(page_label)

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)
        self.page_spinbox.setValue(1)
        self.page_spinbox.setToolTip("Jump to page number")
        self.page_spinbox.valueChanged.connect(self._on_page_spinbox_changed)
        self.page_spinbox.setMinimumWidth(60)
        self.addWidget(self.page_spinbox)

        # Page count label
        self.page_count_label = QLabel("of 1")
        self.page_count_label.setStyleSheet("color: #666; margin-right: 8px;")
        self.addWidget(self.page_count_label)

        # Next page
        self.next_action = QAction("➡️", self)
        self.next_action.setToolTip("Next page (Ctrl+Right)")
        self.next_action.setShortcut("Ctrl+Right")
        self.next_action.triggered.connect(self.nextPageRequested.emit)
        self.addAction(self.next_action)

        self.addSeparator()

    def _create_zoom_section(self):
        """Create zoom controls section"""
        # Zoom out
        self.zoom_out_action = QAction("🔍-", self)
        self.zoom_out_action.setToolTip("Zoom out (Ctrl+-)")
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(self.zoomOutRequested.emit)
        self.addAction(self.zoom_out_action)

        # Zoom level dropdown
        zoom_label = QLabel("Zoom:")
        self.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.setEditable(True)
        zoom_levels = [
            "25%", "50%", "75%", "100%", "125%", "150%",
            "200%", "300%", "400%", "Fit Width", "Fit Page"
        ]
        self.zoom_combo.addItems(zoom_levels)
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setToolTip("Set zoom level")
        self.zoom_combo.currentTextChanged.connect(self._on_zoom_combo_changed)
        self.zoom_combo.setMinimumWidth(100)
        self.addWidget(self.zoom_combo)

        # Zoom in
        self.zoom_in_action = QAction("🔍+", self)
        self.zoom_in_action.setToolTip("Zoom in (Ctrl++)")
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(self.zoomInRequested.emit)
        self.addAction(self.zoom_in_action)

        self.addSeparator()

    def _create_view_section(self):
        """Create view controls section"""
        # Fit width
        self.fit_width_action = QAction("📏 Fit Width", self)
        self.fit_width_action.setToolTip("Fit page to window width (Ctrl+1)")
        self.fit_width_action.setShortcut("Ctrl+1")
        self.fit_width_action.triggered.connect(self.fitWidthRequested.emit)
        self.addAction(self.fit_width_action)

        # Fit page
        self.fit_page_action = QAction("📄 Fit Page", self)
        self.fit_page_action.setToolTip("Fit entire page in window (Ctrl+2)")
        self.fit_page_action.setShortcut("Ctrl+2")
        self.fit_page_action.triggered.connect(self.fitPageRequested.emit)
        self.addAction(self.fit_page_action)

        self.addSeparator()

        # Grid toggle
        self.grid_action = QAction("📐 Grid", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setToolTip("Toggle grid display (Ctrl+G)")
        self.grid_action.setShortcut("Ctrl+G")
        self.grid_action.triggered.connect(self._on_grid_toggle)
        self.addAction(self.grid_action)

        self.addSeparator()

    def _create_info_section(self):
        """Create info section"""
        # Info action
        self.info_action = QAction("ℹ️ Info", self)
        self.info_action.setToolTip("Show application information")
        self.info_action.triggered.connect(self.infoRequested.emit)
        self.addAction(self.info_action)

    # Signal handlers
    @pyqtSlot()
    def _on_page_spinbox_changed(self):
        """Handle page spinbox value change"""
        page_number = self.page_spinbox.value()
        if page_number != self.current_page:
            self.pageJumpRequested.emit(page_number)

    @pyqtSlot(str)
    def _on_zoom_combo_changed(self, text: str):
        """Handle zoom combo box selection"""
        text = text.strip()

        # Handle special fit options
        if text == "Fit Width":
            self.fitWidthRequested.emit()
            return
        elif text == "Fit Page":
            self.fitPageRequested.emit()
            return

        # Handle percentage values
        try:
            if text.endswith("%"):
                percent = float(text[:-1])
            else:
                percent = float(text)

            # Validate range
            if 10 <= percent <= 500:
                zoom_level = percent / 100.0
                self.zoomToLevelRequested.emit(zoom_level)
            else:
                # Reset to current zoom if invalid
                self.set_zoom_display(self.current_zoom)

        except ValueError:
            # Reset to current zoom if invalid
            self.set_zoom_display(self.current_zoom)

    @pyqtSlot()
    def _on_grid_toggle(self):
        """Handle grid toggle"""
        self.grid_enabled = not self.grid_enabled
        self.gridToggleRequested.emit()

    # Public interface for updating toolbar state
    def update_document_info(self, current_page: int, total_pages: int):
        """Update page information"""
        self.current_page = current_page
        self.total_pages = total_pages

        # Update spinbox
        self.page_spinbox.setMaximum(total_pages)
        self.page_spinbox.setValue(current_page)

        # Update page count label
        self.page_count_label.setText(f"of {total_pages}")

        # Update navigation state
        self._update_navigation_state()

    def set_zoom_display(self, zoom_percent: int):
        """Update zoom display"""
        self.current_zoom = zoom_percent
        self.zoom_combo.setCurrentText(f"{zoom_percent}%")

    def set_grid_state(self, enabled: bool):
        """Update grid toggle state"""
        self.grid_enabled = enabled
        self.grid_action.setChecked(enabled)

    def set_document_loaded(self, loaded: bool):
        """Enable/disable document-dependent actions"""
        self.prev_action.setEnabled(loaded)
        self.next_action.setEnabled(loaded)
        self.page_spinbox.setEnabled(loaded)
        self.zoom_in_action.setEnabled(loaded)
        self.zoom_out_action.setEnabled(loaded)
        self.zoom_combo.setEnabled(loaded)
        self.fit_width_action.setEnabled(loaded)
        self.fit_page_action.setEnabled(loaded)
        self.grid_action.setEnabled(loaded)
        self.save_action.setEnabled(loaded)

        if not loaded:
            # Reset to defaults when no document
            self.update_document_info(1, 1)
            self.set_zoom_display(100)
            self.set_grid_state(False)

    def _update_navigation_state(self):
        """Update navigation button states"""
        if hasattr(self, 'prev_action'):
            self.prev_action.setEnabled(self.current_page > 1)
        if hasattr(self, 'next_action'):
            self.next_action.setEnabled(self.current_page < self.total_pages)

    # Convenience methods for external updates
    def update_current_page(self, page: int):
        """Update just the current page"""
        self.update_document_info(page, self.total_pages)

    def get_current_state(self) -> dict:
        """Get current toolbar state"""
        return {
            'current_page': self.current_page,
            'total_pages': self.total_pages,
            'current_zoom': self.current_zoom,
            'grid_enabled': self.grid_enabled
        }