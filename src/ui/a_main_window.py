"""
PDF Main Window - Complete Implementation with Toolbar Widget
Main window for PDF Voice Editor using new toolbar widget
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QScrollArea, QVBoxLayout,
    QWidget, QFileDialog, QMenuBar, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction

from .a_toolbar_widget import ToolbarWidget
from .a_canvas_widget import CanvasWidget
from .a_pdf_document import PDFDocument


class PDFMainWindow(QMainWindow):
    """
    Main window for PDF Voice Editor
    Integrates canvas widget with toolbar widget for clean separation
    """

    # Signals for document management
    documentLoaded = pyqtSignal(object)  # Emitted when document is loaded
    documentClosed = pyqtSignal()  # Emitted when document is closed

    def __init__(self):
        super().__init__()

        # Core components
        self.document = None
        self.scroll_area = None
        self.canvas_widget = None
        self.toolbar_widget = None

        # UI state tracking
        self.current_page = 0
        self.total_pages = 0
        self.current_zoom = 1.0

        # Scroll update timer for performance
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self._on_scroll_timer)
        self.scroll_timer.setSingleShot(True)

        # Initialize UI
        self._setup_ui()
        self._connect_signals()

        # Window properties
        self.setWindowTitle("PDF Voice Editor")
        self.setGeometry(100, 100, 1200, 800)

        print("🏠 Main window initialized")

    def _setup_ui(self):
        """Initialize the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create UI components
        self._create_menu_bar()
        self._create_toolbar()
        self._create_scroll_area()
        self._create_status_bar()

        # Add scroll area to layout
        main_layout.addWidget(self.scroll_area)

    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        open_action = QAction('&Open PDF...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction('&Save Form Data...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_form_data)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('&View')

        zoom_in_action = QAction('Zoom &In', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.triggered.connect(self._on_zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction('Zoom &Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(self._on_zoom_out)
        view_menu.addAction(zoom_out_action)

        view_menu.addSeparator()

        fit_width_action = QAction('Fit &Width', self)
        fit_width_action.setShortcut('Ctrl+1')
        fit_width_action.triggered.connect(self._on_fit_width)
        view_menu.addAction(fit_width_action)

        fit_page_action = QAction('Fit &Page', self)
        fit_page_action.setShortcut('Ctrl+2')
        fit_page_action.triggered.connect(self._on_fit_page)
        view_menu.addAction(fit_page_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_info)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Create toolbar using toolbar widget"""
        self.toolbar_widget = ToolbarWidget(self)
        self.addToolBar(self.toolbar_widget)

    def _create_scroll_area(self):
        """Create the scrollable area with canvas widget"""
        self.scroll_area = QScrollArea()

        # Configure scroll area
        self.scroll_area.setWidgetResizable(False)  # Canvas controls its own size
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create canvas widget
        self.canvas_widget = CanvasWidget()

        # Set canvas as scroll area widget
        self.scroll_area.setWidget(self.canvas_widget)

        # Connect scroll events
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll_changed)

    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        """Connect all signals between components"""
        # Connect toolbar signals
        self._connect_toolbar_signals()

        # Connect canvas signals
        self._connect_canvas_signals()

    def _connect_toolbar_signals(self):
        """Connect toolbar signals to main window methods"""
        if not self.toolbar_widget:
            return

        # File operations
        self.toolbar_widget.openRequested.connect(self.open_pdf)
        self.toolbar_widget.saveRequested.connect(self.save_form_data)

        # Navigation
        self.toolbar_widget.previousPageRequested.connect(self._on_previous_page)
        self.toolbar_widget.nextPageRequested.connect(self._on_next_page)
        self.toolbar_widget.pageJumpRequested.connect(self._on_page_jump)

        # Zoom operations
        self.toolbar_widget.zoomInRequested.connect(self._on_zoom_in)
        self.toolbar_widget.zoomOutRequested.connect(self._on_zoom_out)
        self.toolbar_widget.zoomToLevelRequested.connect(self._on_zoom_to_level)
        self.toolbar_widget.fitWidthRequested.connect(self._on_fit_width)
        self.toolbar_widget.fitPageRequested.connect(self._on_fit_page)

        # View controls
        self.toolbar_widget.gridToggleRequested.connect(self._on_grid_toggle)
        self.toolbar_widget.infoRequested.connect(self.show_info)

    def _connect_canvas_signals(self):
        """Connect canvas signals to main window methods"""
        if not self.canvas_widget:
            return

        # Document management
        self.documentLoaded.connect(self.canvas_widget.on_document_loaded)
        self.documentClosed.connect(self.canvas_widget.on_document_closed)

        # Canvas updates
        self.canvas_widget.pageChanged.connect(self._on_page_changed)
        self.canvas_widget.zoomChanged.connect(self._on_zoom_changed)

    # ======================
    # FILE OPERATIONS
    # ======================

    @pyqtSlot()
    def open_pdf(self):
        """Open PDF file dialog and load document"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF File",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            self.load_document(file_path)

    @pyqtSlot()
    def save_form_data(self):
        """Save form data (placeholder)"""
        self.status_bar.showMessage("Save functionality not implemented yet", 2000)

    def load_document(self, file_path: str):
        """Load PDF document"""
        try:
            print(f"📄 Loading document: {file_path}")

            # Create document
            self.document = PDFDocument(file_path)
            self.total_pages = self.document.get_page_count()
            self.current_page = 0

            # Update toolbar
            if self.toolbar_widget:
                self.toolbar_widget.update_document_info(1, self.total_pages)
                self.toolbar_widget.set_document_loaded(True)

            # Emit signal to canvas
            self.documentLoaded.emit(self.document)

            # Update UI
            self.setWindowTitle(f"PDF Voice Editor - {file_path}")
            self.status_bar.showMessage(f"Loaded: {file_path} ({self.total_pages} pages)")

            print(f"✅ Document loaded: {self.total_pages} pages")

        except Exception as e:
            print(f"❌ Error loading document: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load PDF:\n{str(e)}")

    def close_document(self):
        """Close current document"""
        if self.document:
            print("📄 Closing document")

            # Close document
            self.document.close()
            self.document = None

            # Reset state
            self.current_page = 0
            self.total_pages = 0
            self.current_zoom = 1.0

            # Update toolbar
            if self.toolbar_widget:
                self.toolbar_widget.set_document_loaded(False)

            # Emit signal to canvas
            self.documentClosed.emit()

            # Update UI
            self.setWindowTitle("PDF Voice Editor")
            self.status_bar.showMessage("Ready")

    # ======================
    # NAVIGATION METHODS
    # ======================

    @pyqtSlot()
    def _on_previous_page(self):
        """Handle previous page request"""
        if self.current_page > 0:
            self._navigate_to_page(self.current_page - 1)

    @pyqtSlot()
    def _on_next_page(self):
        """Handle next page request"""
        if self.current_page < self.total_pages - 1:
            self._navigate_to_page(self.current_page + 1)

    @pyqtSlot(int)
    def _on_page_jump(self, page_number: int):
        """Handle page jump request (1-based)"""
        # Convert to 0-based indexing
        target_page = page_number - 1
        if 0 <= target_page < self.total_pages:
            self._navigate_to_page(target_page)

    def _navigate_to_page(self, page_index: int):
        """Navigate to specific page"""
        if not self.canvas_widget or not self.canvas_widget.layout_manager:
            return

        try:
            # Update current page tracking
            self.current_page = page_index

            # Get page Y position and scroll to it
            y_position = self.canvas_widget.get_page_y_position(page_index)

            # Apply top margin
            top_margin = 0
            if self.canvas_widget.layout_manager:
                top_margin = self.canvas_widget.layout_manager.PAGE_SPACING_VERTICAL

            scroll_position = max(0, y_position - top_margin)
            self.scroll_area.verticalScrollBar().setValue(int(scroll_position))

            print(f"📍 Navigated to page {page_index + 1}")

        except Exception as e:
            print(f"❌ Error navigating to page: {e}")

    # ======================
    # ZOOM METHODS
    # ======================

    @pyqtSlot()
    def _on_zoom_in(self):
        """Handle zoom in request"""
        if self.canvas_widget:
            self.canvas_widget.zoom_in()

    @pyqtSlot()
    def _on_zoom_out(self):
        """Handle zoom out request"""
        if self.canvas_widget:
            self.canvas_widget.zoom_out()

    @pyqtSlot(float)
    def _on_zoom_to_level(self, zoom_level: float):
        """Handle zoom to specific level request"""
        if self.canvas_widget:
            self.canvas_widget.set_zoom(zoom_level)

    @pyqtSlot()
    def _on_fit_width(self):
        """Handle fit width request"""
        if self.canvas_widget:
            available_width = self.scroll_area.viewport().width()
            self.canvas_widget.fit_to_width(available_width)

    @pyqtSlot()
    def _on_fit_page(self):
        """Handle fit page request"""
        if self.canvas_widget:
            available_width = self.scroll_area.viewport().width()
            available_height = self.scroll_area.viewport().height()
            self.canvas_widget.fit_to_page(available_width, available_height)

    # ======================
    # VIEW METHODS
    # ======================

    @pyqtSlot()
    def _on_grid_toggle(self):
        """Handle grid toggle request"""
        # TODO: Implement grid functionality
        self.status_bar.showMessage("Grid toggle not implemented yet", 2000)

    @pyqtSlot()
    def show_info(self):
        """Show application information"""
        QMessageBox.about(
            self,
            "About PDF Voice Editor",
            "PDF Voice Editor\n\n"
            "A voice-controlled PDF editing application\n"
            "Built with PyQt6 and PyMuPDF"
        )

    # ======================
    # SCROLL HANDLING
    # ======================

    @pyqtSlot(int)
    def _on_scroll_changed(self, value):
        """Handle scroll position changes (debounced)"""
        # Debounce scroll updates for performance
        self.scroll_timer.stop()
        self.scroll_timer.start(50)  # 50ms delay

    @pyqtSlot()
    def _on_scroll_timer(self):
        """Handle scroll timer - update canvas viewport"""
        if not self.canvas_widget:
            return

        try:
            # Get viewport rectangle
            scrollbar_v = self.scroll_area.verticalScrollBar()
            scrollbar_h = self.scroll_area.horizontalScrollBar()

            viewport = self.scroll_area.viewport()
            viewport_rect = QRectF(
                scrollbar_h.value(),
                scrollbar_v.value(),
                viewport.width(),
                viewport.height()
            )

            # Get visible pages from canvas
            visible_pages = self.canvas_widget.get_visible_pages_in_viewport(viewport_rect)

            # Update canvas viewport
            self.canvas_widget.set_visible_pages(visible_pages, viewport_rect)

        except Exception as e:
            print(f"⚠️ Error in scroll update: {e}")

    # ======================
    # CANVAS EVENT HANDLERS
    # ======================

    @pyqtSlot(int)
    def _on_page_changed(self, page_index: int):
        """Handle page change from canvas"""
        self.current_page = page_index

        # Update toolbar display
        if self.toolbar_widget:
            self.toolbar_widget.update_current_page(page_index + 1)  # Convert to 1-based

        print(f"📄 Page changed to: {page_index + 1}")

    @pyqtSlot(float)
    def _on_zoom_changed(self, zoom_level: float):
        """Handle zoom change from canvas"""
        self.current_zoom = zoom_level

        # Update toolbar display
        if self.toolbar_widget:
            zoom_percent = int(zoom_level * 100)
            self.toolbar_widget.set_zoom_display(zoom_percent)

        print(f"🔍 Zoom changed to: {zoom_level:.2f}")

    # ======================
    # WINDOW EVENTS
    # ======================

    def closeEvent(self, event):
        """Handle window close event"""
        if self.document:
            self.close_document()

        print("🏠 Main window closing")
        event.accept()

    def resizeEvent(self, event):
        """Handle window resize event"""
        super().resizeEvent(event)

        # Update scroll area when window is resized
        if hasattr(self, 'scroll_area') and self.scroll_area:
            self.scroll_area.updateGeometry()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Create and show main window
    window = PDFMainWindow()
    window.show()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())