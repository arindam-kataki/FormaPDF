import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QScrollArea, QVBoxLayout,
                             QHBoxLayout, QWidget, QPushButton, QLabel, QSlider,
                             QFileDialog, QMenuBar, QStatusBar, QToolBar)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QAction


class PDFMainWindow(QMainWindow):
    """Main window - pure UI container with minimal logic"""

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
        self._connect_signals()

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
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create canvas widget
        from a_canvas_widget import CanvasWidget
        self.canvas_widget = CanvasWidget()

        # Set canvas as scroll area widget
        self.scroll_area.setWidget(self.canvas_widget)

        # Connect scroll events
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll_changed)

    def _create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        """Connect canvas widget signals to main window handlers"""
        # Connect after canvas is created
        pass  # Will be connected in _create_scroll_area via canvas creation

    # Event Handlers - delegate to canvas widget
    def _on_open_file(self):
        """Handle file open - delegate to canvas"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)")

        if file_path:
            try:
                from a_pdf_document import PDFDocument

                # Close existing document
                if self.document:
                    self.document.close()

                # Load new document
                self.document = PDFDocument(file_path)
                self.total_pages = self.document.get_page_count()

                # Load into canvas widget
                self.canvas_widget.load_document(self.document)

                # Connect canvas signals after document is loaded
                self.canvas_widget.pageChanged.connect(self._on_page_changed)
                self.canvas_widget.zoomChanged.connect(self._on_zoom_changed)

                # Update UI
                self.current_page = 0
                self._update_navigation_state()
                self.status_bar.showMessage(f"Loaded: {file_path}")

                # Reset scroll to top
                self.scroll_area.verticalScrollBar().setValue(0)

            except Exception as e:
                self.status_bar.showMessage(f"Error loading PDF: {e}")

    def _on_zoom_in(self):
        """Handle zoom in - delegate to canvas"""
        if self.canvas_widget:
            self.canvas_widget.zoom_in()

    def _on_zoom_out(self):
        """Handle zoom out - delegate to canvas"""
        if self.canvas_widget:
            self.canvas_widget.zoom_out()

    def _on_zoom_slider_changed(self, value):
        """Handle zoom slider - delegate to canvas"""
        if self.canvas_widget:
            zoom_level = value / 100.0
            self.canvas_widget.set_zoom(zoom_level)

    def _on_fit_width(self):
        """Handle fit width - delegate to canvas"""
        if self.canvas_widget:
            available_width = self.scroll_area.viewport().width()
            self.canvas_widget.fit_to_width(available_width)

    def _on_fit_page(self):
        """Handle fit page - delegate to canvas"""
        if self.canvas_widget:
            available_width = self.scroll_area.viewport().width()
            available_height = self.scroll_area.viewport().height()
            self.canvas_widget.fit_to_page(available_width, available_height)

    def _on_previous_page(self):
        """Handle previous page - delegate to canvas"""
        if self.canvas_widget and self.current_page > 0:
            target_page = self.current_page - 1
            y_position = self.canvas_widget.get_page_y_position(target_page)
            self.scroll_area.verticalScrollBar().setValue(int(y_position))

    def _on_next_page(self):
        """Handle next page - delegate to canvas"""
        if self.canvas_widget and self.current_page < self.total_pages - 1:
            target_page = self.current_page + 1
            y_position = self.canvas_widget.get_page_y_position(target_page)
            self.scroll_area.verticalScrollBar().setValue(int(y_position))

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

    def _on_zoom_changed(self, zoom_level):
        """Handle zoom change signal from canvas"""
        zoom_percent = int(zoom_level * 100)
        self.zoom_percent = zoom_percent

        # Update UI without triggering signal
        self.zoom_label.setText(f"{zoom_percent}%")
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(zoom_percent)
        self.zoom_slider.blockSignals(False)

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