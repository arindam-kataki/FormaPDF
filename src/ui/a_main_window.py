import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QScrollArea, QVBoxLayout,
                             QHBoxLayout, QWidget, QPushButton, QLabel, QSlider,
                             QFileDialog, QMenuBar, QStatusBar, QToolBar)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt6.QtGui import QAction


class PDFMainWindow(QMainWindow):
    """Main window - with proper scroll area and canvas size handling"""

    # Signals for document management
    documentLoaded = pyqtSignal(object)  # Emitted when document is loaded
    documentClosed = pyqtSignal()  # Emitted when document is closed

    def __init__(self):
        super().__init__()

        # Core components - only UI references
        self.document = None
        self.scroll_area = None
        self.canvas_widget = None

        # UI state tracking
        self.current_page = 0
        self.total_pages = 0
        self.zoom_percent = 100

        # Scroll update timer for performance
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self._on_scroll_timer)
        self.scroll_timer.setSingleShot(True)

        # Initialize UI
        self._setup_ui()

        # Window properties
        self.setWindowTitle("PDF Viewer")
        self.setGeometry(100, 100, 1200, 800)

    def _setup_ui(self):
        """Initialize the user interface - pure UI setup"""
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

        # Add scroll area to layout
        main_layout.addWidget(self.scroll_area)

        # Create status bar
        self._create_status_bar()

    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        open_action = QAction('Open PDF...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('View')

        fit_width_action = QAction('Fit Width', self)
        fit_width_action.triggered.connect(self._on_fit_width)
        view_menu.addAction(fit_width_action)

        fit_page_action = QAction('Fit Page', self)
        fit_page_action.triggered.connect(self._on_fit_page)
        view_menu.addAction(fit_page_action)

    def _create_toolbar(self):
        """Create the toolbar with PDF controls"""
        toolbar = QToolBar("PDF Controls")
        self.addToolBar(toolbar)

        # File operations
        open_action = QAction("Open", self)
        open_action.triggered.connect(self._on_open_file)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        # Navigation controls
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self._on_previous_page)
        self.prev_button.setEnabled(False)
        toolbar.addWidget(self.prev_button)

        self.page_label = QLabel("Page: 0 / 0")
        toolbar.addWidget(self.page_label)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self._on_next_page)
        self.next_button.setEnabled(False)
        toolbar.addWidget(self.next_button)

        toolbar.addSeparator()

        # Zoom controls
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(self._on_zoom_out)
        toolbar.addWidget(zoom_out_btn)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(25, 300)  # 25% to 300%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        toolbar.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("100%")
        toolbar.addWidget(self.zoom_label)

        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(self._on_zoom_in)
        toolbar.addWidget(zoom_in_btn)

    def _create_scroll_area(self):
        """Create the scrollable area with canvas widget"""
        self.scroll_area = QScrollArea()

        # CRITICAL: Set these properties for proper scrolling
        self.scroll_area.setWidgetResizable(False)  # Let canvas control its own size
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the canvas
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create canvas widget
        from a_canvas_widget import CanvasWidget
        self.canvas_widget = CanvasWidget()

        # Set canvas as scroll area widget
        self.scroll_area.setWidget(self.canvas_widget)

        # Connect scroll events
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll_changed)

        # Connect canvas signals immediately after creation
        self._connect_signals()

    def _create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Open a PDF file to get started")

    def _connect_signals(self):
        """Connect canvas widget signals to main window handlers"""
        if self.canvas_widget:
            # Connect canvas signals
            self.canvas_widget.pageChanged.connect(self._on_page_changed)
            self.canvas_widget.zoomChanged.connect(self._on_zoom_changed)

            # Connect document management signals
            self.documentLoaded.connect(self.canvas_widget.on_document_loaded)
            self.documentClosed.connect(self.canvas_widget.on_document_closed)

    # Event Handlers - signal-driven architecture
    def _on_open_file(self):
        """Handle file open - emit document loaded signal"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)")

        if file_path:
            try:
                from a_pdf_document import PDFDocument

                # Close existing document
                if self.document:
                    self.document.close()
                    self.documentClosed.emit()

                # Load new document
                self.document = PDFDocument(file_path)
                self.total_pages = self.document.get_page_count()

                # Emit signal for canvas to listen to
                self.documentLoaded.emit(self.document)

                # Update UI
                self.current_page = 0
                self._update_navigation_state()
                self.status_bar.showMessage(f"Loaded: {file_path}")

                # IMPORTANT: Update scroll area after document loads
                QTimer.singleShot(100, self._update_scroll_area)

            except Exception as e:
                self.status_bar.showMessage(f"Error loading PDF: {e}")
                print(f"Error loading PDF: {e}")

    def _update_scroll_area(self):
        """Update scroll area after document is loaded"""
        if self.canvas_widget and self.canvas_widget.layout_manager:
            # Get the canvas size from layout manager
            canvas_width, canvas_height = self.canvas_widget.get_canvas_size()
            print(f"📏 Setting canvas size: {canvas_width}x{canvas_height}")

            # Resize the canvas widget to match the calculated size
            self.canvas_widget.resize(canvas_width, canvas_height)

            # Force scroll area to update its scroll bars
            self.scroll_area.updateGeometry()

            # Initial viewport setup
            self._setup_initial_viewport()

            print(f"📏 Scroll area viewport: {self.scroll_area.viewport().size()}")
            print(f"📏 Canvas widget size: {self.canvas_widget.size()}")

    def _setup_initial_viewport(self):
        """Setup initial viewport and visible pages"""
        if not self.canvas_widget or not self.canvas_widget.layout_manager:
            return

        # Get scroll area viewport
        viewport = self.scroll_area.viewport()
        viewport_rect = QRectF(0, 0, viewport.width(), viewport.height())

        # Get visible pages for initial viewport
        visible_pages = self.canvas_widget.get_visible_pages_in_viewport(viewport_rect)

        # Set visible pages in canvas
        self.canvas_widget.set_visible_pages(visible_pages, viewport_rect)

        # Reset scroll to top
        self.scroll_area.verticalScrollBar().setValue(0)
        self.scroll_area.horizontalScrollBar().setValue(0)

        print(f"👁️ Initial viewport setup complete. Visible pages: {visible_pages}")

    def _on_zoom_in(self):
        """Handle zoom in - maintain current position"""
        if self.canvas_widget:
            # Save current scroll position and page
            old_scroll_y = self.scroll_area.verticalScrollBar().value()
            old_page = self.current_page

            self.canvas_widget.zoom_in()

            # Restore position after zoom
            QTimer.singleShot(100, lambda: self._restore_zoom_position(old_page, old_scroll_y))

    def _on_zoom_out(self):
        """Handle zoom out - maintain current position"""
        if self.canvas_widget:
            # Save current scroll position and page
            old_scroll_y = self.scroll_area.verticalScrollBar().value()
            old_page = self.current_page

            self.canvas_widget.zoom_out()

            # Restore position after zoom
            QTimer.singleShot(100, lambda: self._restore_zoom_position(old_page, old_scroll_y))

    def _on_zoom_slider_changed(self, value):
        """Handle zoom slider - maintain current position"""
        if self.canvas_widget:
            # Save current scroll position and page
            old_scroll_y = self.scroll_area.verticalScrollBar().value()
            old_page = self.current_page

            zoom_level = value / 100.0
            self.canvas_widget.set_zoom(zoom_level)

            # Restore position after zoom
            QTimer.singleShot(100, lambda: self._restore_zoom_position(old_page, old_scroll_y))

    def _on_fit_width(self):
        """Handle fit width - maintain current page"""
        if self.canvas_widget:
            # Save current page
            old_page = self.current_page

            available_width = self.scroll_area.viewport().width()
            self.canvas_widget.fit_to_width(available_width)

            # Navigate to the same page after fit
            QTimer.singleShot(100, lambda: self._navigate_to_page_with_margin(old_page))

    def _on_fit_page(self):
        """Handle fit page - maintain current page"""
        if self.canvas_widget:
            # Save current page
            old_page = self.current_page

            available_width = self.scroll_area.viewport().width()
            available_height = self.scroll_area.viewport().height()
            self.canvas_widget.fit_to_page(available_width, available_height)

            # Navigate to the same page after fit
            QTimer.singleShot(100, lambda: self._navigate_to_page_with_margin(old_page))

    def _restore_zoom_position(self, target_page: int, old_scroll_y: int):
        """Restore position after zoom operation"""
        try:
            if not self.canvas_widget or not self.canvas_widget.layout_manager:
                return

            # Method 1: Try to maintain relative position on the same page
            page_y = self.canvas_widget.get_page_y_position(target_page)

            # Calculate what percentage down the old page we were
            if self.canvas_widget.layout_manager:
                old_page_rect = self.canvas_widget.layout_manager.get_page_rect(target_page)
                if old_page_rect:
                    # Calculate relative position within the page (0.0 to 1.0)
                    relative_position = 0.0
                    if old_page_rect.height() > 0:
                        page_relative_y = old_scroll_y - old_page_rect.top()
                        relative_position = max(0.0, min(1.0, page_relative_y / old_page_rect.height()))

                    # Apply the same relative position to the new (zoomed) page
                    new_page_rect = self.canvas_widget.layout_manager.get_page_rect(target_page)
                    if new_page_rect:
                        new_scroll_y = new_page_rect.top() + (relative_position * new_page_rect.height())

                        # Apply top margin
                        top_margin = self.canvas_widget.layout_manager.PAGE_SPACING_VERTICAL
                        final_scroll_y = max(0, new_scroll_y - top_margin)

                        print(
                            f"🔍 Zoom position restore: page {target_page}, relative pos {relative_position:.2f}, scroll to {final_scroll_y}")
                        self.scroll_area.verticalScrollBar().setValue(int(final_scroll_y))

                        # Update scroll area after position change
                        self._update_scroll_area()
                        return

            # Fallback: Navigate to the page start with margin
            self._navigate_to_page_with_margin(target_page)

        except Exception as e:
            print(f"❌ Error restoring zoom position: {e}")
            # Final fallback: just go to the page
            self._navigate_to_page_with_margin(target_page)

    def _navigate_to_page_with_margin(self, page_index: int):
        """Navigate to a page with proper top margin"""
        if not self.canvas_widget:
            return

        try:
            page_index = max(0, min(page_index, self.total_pages - 1))
            y_position = self.canvas_widget.get_page_y_position(page_index)

            # Apply top margin
            top_margin = 0
            if self.canvas_widget.layout_manager:
                top_margin = self.canvas_widget.layout_manager.PAGE_SPACING_VERTICAL

            scroll_position = max(0, y_position - top_margin)
            self.scroll_area.verticalScrollBar().setValue(int(scroll_position))

            print(f"📍 Navigated to page {page_index + 1} with margin")

        except Exception as e:
            print(f"❌ Error navigating to page: {e}")

    def _on_previous_page(self):
        """Handle previous page - delegate to canvas with proper margin"""
        if self.canvas_widget and self.current_page > 0:
            target_page = self.current_page - 1
            y_position = self.canvas_widget.get_page_y_position(target_page)

            # FIXED: Use layout manager constants for proper spacing
            top_margin = 0
            if self.canvas_widget.layout_manager:
                top_margin = self.canvas_widget.layout_manager.PAGE_SPACING_VERTICAL

            scroll_position = max(0, y_position - top_margin)
            self.scroll_area.verticalScrollBar().setValue(int(scroll_position))

    def _on_next_page(self):
        """Handle next page - delegate to canvas with proper margin"""
        if self.canvas_widget and self.current_page < self.total_pages - 1:
            target_page = self.current_page + 1
            y_position = self.canvas_widget.get_page_y_position(target_page)

            # FIXED: Use layout manager constants for proper spacing
            top_margin = 0
            if self.canvas_widget.layout_manager:
                top_margin = self.canvas_widget.layout_manager.PAGE_SPACING_VERTICAL

            scroll_position = max(0, y_position - top_margin)
            self.scroll_area.verticalScrollBar().setValue(int(scroll_position))

    def _on_scroll_changed(self, value):
        """Handle scroll position changes"""
        # Debounce scroll updates
        self.scroll_timer.stop()
        self.scroll_timer.start(50)  # 50ms delay

    def _on_scroll_timer(self):
        """Handle scroll timer - update canvas viewport"""
        if not self.canvas_widget:
            return

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

        # Update current page tracking
        if visible_pages:
            new_current_page = visible_pages[0]
            if new_current_page != self.current_page:
                self.current_page = new_current_page
                self._update_navigation_state()

    # Signal handlers from canvas widget
    def _on_page_changed(self, page_index):
        """Handle page change signal from canvas"""
        self.current_page = page_index
        self._update_navigation_state()
        print(f"Page changed to: {page_index + 1}")

    def _on_zoom_changed(self, zoom_level):
        """Handle zoom change signal from canvas"""
        zoom_percent = int(zoom_level * 100)
        self.zoom_percent = zoom_percent

        # Update UI without triggering signal
        self.zoom_label.setText(f"{zoom_percent}%")
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(zoom_percent)
        self.zoom_slider.blockSignals(False)

        print(f"Zoom changed to: {zoom_percent}%")

    def _update_navigation_state(self):
        """Update navigation buttons and page display"""
        if self.total_pages > 0:
            self.page_label.setText(f"Page: {self.current_page + 1} / {self.total_pages}")
            self.prev_button.setEnabled(self.current_page > 0)
            self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        else:
            self.page_label.setText("Page: 0 / 0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle window close event"""
        if self.document:
            self.documentClosed.emit()
            self.document.close()
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = PDFMainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())