"""
PDF Main Window - Complete Implementation with Toolbar Widget
Main window for PDF Voice Editor using new toolbar widget
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QScrollArea, QVBoxLayout,
    QWidget, QFileDialog, QMenuBar, QStatusBar, QMessageBox, QDockWidget
)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction

from src.ui.a_toc_integration import TOCIntegration
from src.ui.a_toolbar_widget import ToolbarWidget
from src.ui.a_canvas_widget import CanvasWidget
from src.ui.a_pdf_document import PDFDocument
from src.ui.a_pdf_link_integration import PDFLinkIntegration
from ui.a_pdf_link_control_panel import PDFLinkControlPanel
from ui.a_pdf_link_menu_integration import PDFLinkMenuIntegration


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

        self.link_integration = None
        self.link_control_panel = None

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

        self.toc_integration = TOCIntegration(self)
        self.toc_integration.setup_toc_integration()

        self.setup_link_system()

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

    def setup_link_system(self):

        """Initialize the PDF link system"""
        try:
            print("🔗 Setting up PDF link system...")

            # Create link integration
            self.link_integration = PDFLinkIntegration(self)

            # Create control panel
            self.link_control_panel = PDFLinkControlPanel(self.link_integration)

            # Add to UI if there's a properties area
            self.add_link_control_to_ui()

            # Add menu items
            PDFLinkMenuIntegration.add_link_menu_items(self, self.link_integration)

            print("✅ PDF link system initialized")

        except Exception as e:
            print(f"❌ Error setting up link system: {e}")
            import traceback
            traceback.print_exc()

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

        # Links updates
        self.canvas_widget.pageChanged.connect(self._on_page_changed_links)
        self.canvas_widget.zoomChanged.connect(self._on_zoom_changed_links)

    def _add_link_control_dock(self):
        """Add link control panel as dockable widget"""
        if not self.link_control_panel:
            return

        try:
            #from PyQt6.QtWidgets import QDockWidget
            #from PyQt6.QtCore import Qt

            # Create dock widget
            dock = QDockWidget("PDF Links", self)
            dock.setWidget(self.link_control_panel)
            dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                             QDockWidget.DockWidgetFeature.DockWidgetFloatable)

            # Add to right side
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

            print("📎 Link control panel added as dock widget")

        except Exception as e:
            print(f"⚠️ Could not add link control dock: {e}")

    # ======================
    # LINK OPERATIONS
    # ======================

    def _on_page_changed_links(self, page_num: int):
        """Update link overlays when page changes"""
        if self.link_integration and self.link_integration.overlay_manager:
            self.link_integration.overlay_manager.update_page_links(page_num, self.current_zoom)

    def _on_zoom_changed_links(self, zoom_level: float):
        """Update link overlays when zoom changes"""
        if self.link_integration and self.link_integration.overlay_manager:
            self.link_integration.overlay_manager.update_page_links(self.current_page, zoom_level)

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

            # TOC INtegration
            if hasattr(self, 'toc_integration') and self.toc_integration:
                try:
                    success = self.toc_integration.load_document_toc(self.document)
                    if success:
                        print("📖 TOC loaded successfully")
                    else:
                        print("📖 No TOC found in document")
                except Exception as e:
                    print(f"⚠️ Could not load TOC: {e}")

            # CRITICAL FIX: Link integration with immediate trigger
            if hasattr(self, 'link_integration') and self.link_integration:
                print("🔗 Setting up links for new document...")

                # Set document in link manager
                self.link_integration.set_pdf_document(self.document)

                # Integrate with canvas
                self._integrate_links_with_canvas()

                # CRITICAL: Force immediate link update for page 0
                if self.link_integration.overlay_manager:
                    print(f"🔗 Force updating links for page {self.current_page}")
                    self.link_integration.overlay_manager.update_page_links(
                        self.current_page,
                        self.current_zoom
                    )

                    # Ensure overlay manager is visible and positioned correctly
                    overlay_mgr = self.link_integration.overlay_manager
                    if self.canvas_widget:
                        overlay_mgr.setGeometry(self.canvas_widget.rect())
                        overlay_mgr.show()
                        overlay_mgr.raise_()  # Bring to front

                    print(f"✅ Link overlays created: {len(overlay_mgr.link_overlays)}")

            #self.debug_link_system_comprehensive()
            self.debug_specific_pdf_links()

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
            try:
                self.document.close()
            except Exception as e:
                print(f"⚠️ Error closing document: {e}")

            self.document = None

            # Reset state
            self.current_page = 0
            self.total_pages = 0
            self.current_zoom = 1.0

            # Update toolbar
            if self.toolbar_widget:
                self.toolbar_widget.set_document_loaded(False)

            # Emit signal to canvas
            try:
                self.documentClosed.emit()
            except Exception as e:
                print(f"⚠️ Error emitting document closed signal: {e}")

            # Update UI
            self.setWindowTitle("PDF Voice Editor")
            if hasattr(self, 'status_bar'):
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
    def _deprecated_01_on_page_jump(self, page_number: int):
        """Handle page jump request (1-based)"""
        # Convert to 0-based indexing
        target_page = page_number - 1
        if 0 <= target_page < self.total_pages:
            self._navigate_to_page(target_page)

    def _deprecated_01_navigate_to_page(self, page_index: int):
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
        print("🏠 Main window closing")

        # Stop any pending operations first
        if hasattr(self, 'scroll_timer'):
            self.scroll_timer.stop()

        # Close document and clear canvas before closing window
        if self.document:
            self.close_document()

        # Clear canvas widget to prevent further operations
        if self.canvas_widget:
            self.canvas_widget._clear_document()

        event.accept()

    def resizeEvent(self, event):
        """Handle window resize event"""
        super().resizeEvent(event)

        # Update scroll area when window is resized
        if hasattr(self, 'scroll_area') and self.scroll_area:
            self.scroll_area.updateGeometry()

    def deprecated_01_navigate_to_page_with_coordinates(self, page_num: int, x: float = 0, y: float = 0):
        """
        Navigate to specific page and coordinates from TOC

        Args:
            page_num: 0-based page index (TOC page numbers are 0-based)
            x: X coordinate on page in points (from left edge)
            y: Y coordinate on page in points (from bottom edge)

        Returns:
            bool: True if navigation successful, False otherwise
        """
        print(f"📖 TOC NAVIGATION START:")
        print(f"   Requested page: {page_num} (0-based)")
        print(f"   Document page: {page_num + 1}")
        print(f"   Coordinates: x={x:.1f}, y={y:.1f} points")

        try:
            # STEP 1: Validate Prerequisites
            if not self.document:
                print("❌ No document loaded")
                return False

            total_pages = self.document.get_page_count()
            if page_num < 0 or page_num >= total_pages:
                print(f"❌ Invalid page: {page_num}, total pages: {total_pages}")
                return False

            if not hasattr(self, 'canvas_widget') or not self.canvas_widget:
                print("❌ No canvas widget available")
                return False

            if not hasattr(self.canvas_widget, 'layout_manager') or not self.canvas_widget.layout_manager:
                print("❌ No layout manager available")
                return False

            print(f"✅ Prerequisites validated")

            # STEP 2: Get Page Layout Information
            page_rect = self.canvas_widget.layout_manager.get_page_rect(page_num)
            if not page_rect:
                print(f"❌ Could not get page rectangle for page {page_num}")
                return False

            print(f"📐 Page {page_num} layout:")
            print(f"   Page rect: x={page_rect.x():.1f}, y={page_rect.y():.1f}")
            print(f"   Page size: w={page_rect.width():.1f}, h={page_rect.height():.1f}")

            # STEP 3: Calculate Target Scroll Position
            # Convert PDF coordinates (bottom-left origin) to screen coordinates (top-left origin)
            page_height = page_rect.height()
            screen_y_offset = page_height - y  # Convert bottom-origin to top-origin

            target_x = page_rect.left() + x
            target_y = page_rect.top() + screen_y_offset

            print(f"📍 Coordinate conversion:")
            print(f"   PDF Y (from bottom): {y:.1f}")
            print(f"   Screen Y offset (from top): {screen_y_offset:.1f}")
            print(f"   Target scroll position: x={target_x:.1f}, y={target_y:.1f}")

            # STEP 4: Perform Navigation
            if not hasattr(self, 'scroll_area') or not self.scroll_area:
                print("❌ No scroll area available")
                return False

            # Get scrollbars
            h_scrollbar = self.scroll_area.horizontalScrollBar()
            v_scrollbar = self.scroll_area.verticalScrollBar()

            current_x = h_scrollbar.value()
            current_y = v_scrollbar.value()

            print(f"📜 Scroll navigation:")
            print(f"   Current position: x={current_x}, y={current_y}")
            print(f"   Target position: x={int(target_x)}, y={int(target_y)}")

            # Set new scroll positions
            h_scrollbar.setValue(int(target_x))
            v_scrollbar.setValue(int(target_y))

            # STEP 5: Update Canvas State
            old_page = getattr(self.canvas_widget, 'current_page', 0)
            self.canvas_widget.current_page = page_num  # Keep 0-based - NO +1!

            print(f"📄 Page state update:")
            print(f"   Old page: {old_page} (0-based) → New page: {page_num} (0-based)")

            # Emit page change signal
            if hasattr(self.canvas_widget, 'pageChanged'):
                self.canvas_widget.pageChanged.emit(page_num)  # Emit 0-based

            # STEP 6: Update UI Components
            # Update toolbar (toolbar expects 1-based for display)
            if hasattr(self, 'toolbar_widget') and self.toolbar_widget:
                display_page = page_num + 1  # Convert to 1-based for UI display only
                if hasattr(self.toolbar_widget, 'update_current_page'):
                    self.toolbar_widget.update_current_page(display_page)

            # Update status bar
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.showMessage(f"Navigated to page {page_num + 1}", 2000)

            # Force canvas repaint
            if hasattr(self.canvas_widget, 'update'):
                self.canvas_widget.update()

            print(f"✅ NAVIGATION SUCCESSFUL: page {old_page + 1} → {page_num + 1}")
            return True

        except Exception as e:
            print(f"❌ NAVIGATION ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

    def navigate_to_page_with_coordinates(self, page_num: int, x: float = 0, y: float = 0):
        """
        FIXED navigation with proper bounds checking and coordinate handling

        Args:
            page_num: 0-based page index (TOC standard)
            x, y: Coordinates in points

        Returns:
            bool: True if navigation successful, False otherwise
        """
        print(f"📍 NAVIGATE TO PAGE FIX:")
        print(f"   Input page (0-based): {page_num}")
        print(f"   Coordinates: ({x:.1f}, {y:.1f}) points")

        try:
            if not self.document:
                print("❌ No document loaded")
                return False

            total_pages = self.document.get_page_count()

            # CRITICAL FIX: Bounds checking
            if page_num < 0 or page_num >= total_pages:
                print(f"❌ Invalid page: {page_num}, valid range: 0-{total_pages - 1}")
                # Clamp to valid range
                page_num = max(0, min(page_num, total_pages - 1))
                print(f"   → Clamped to page: {page_num}")

            print(f"   Final page (0-based): {page_num}")
            print(f"   Display page (1-based): {page_num + 1}")

            # Navigate to the page using internal 0-based indexing
            self._navigate_to_page(page_num)  # This should expect 0-based

            # Update UI to show correct page number (1-based)
            if hasattr(self, 'toolbar_widget') and self.toolbar_widget:
                self.toolbar_widget.update_current_page(page_num + 1)

            # Update internal tracking
            self.current_page = page_num

            # Show status message
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(f"Navigated to page {page_num + 1}", 2000)

            print(f"   ✅ Navigation successful to page {page_num + 1}")
            return True

        except Exception as e:
            print(f"❌ Navigation error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _on_page_jump(self, page_number: int):
        """
        FIXED page jump handler for UI controls (spinbox, etc.)

        Args:
            page_number: 1-based page number from UI controls
        """
        print(f"🎯 PAGE JUMP FIX:")
        print(f"   UI page (1-based): {page_number}")

        if not self.document:
            print("❌ No document loaded")
            return

        total_pages = self.document.get_page_count()

        # Validate 1-based input
        if page_number < 1 or page_number > total_pages:
            print(f"❌ Invalid page jump: {page_number}, valid range: 1-{total_pages}")
            return

        # Convert 1-based UI input to 0-based internal
        target_page = page_number - 1
        print(f"   Internal page (0-based): {target_page}")

        # Navigate using 0-based index
        self._navigate_to_page(target_page)

        # Update UI tracking
        self.current_page = target_page

        print(f"   ✅ Jumped to page {page_number}")

    def _navigate_to_page(self, page_index: int):
        """
        FIXED core navigation method

        Args:
            page_index: 0-based page index
        """
        if not self.canvas_widget or not hasattr(self.canvas_widget, 'layout_manager'):
            print("❌ Canvas widget or layout manager not available")
            return

        try:
            print(f"📄 Navigating to internal page {page_index} (display: {page_index + 1})")

            # Update current page tracking FIRST
            self.current_page = page_index

            # Get page Y position and scroll to it
            if hasattr(self.canvas_widget, 'get_page_y_position'):
                y_position = self.canvas_widget.get_page_y_position(page_index)

                # Apply top margin if available
                top_margin = 0
                if hasattr(self.canvas_widget, 'layout_manager') and self.canvas_widget.layout_manager:
                    top_margin = getattr(self.canvas_widget.layout_manager, 'PAGE_SPACING_VERTICAL', 0)

                scroll_position = max(0, y_position - top_margin)

                # Scroll to position
                if hasattr(self, 'scroll_area') and self.scroll_area:
                    self.scroll_area.verticalScrollBar().setValue(int(scroll_position))
                    print(f"   Scrolled to position: {scroll_position}")

            # Update toolbar display
            if hasattr(self, 'toolbar_widget') and self.toolbar_widget:
                self.toolbar_widget.update_current_page(page_index + 1)  # Convert to 1-based for display

            print(f"✅ Successfully navigated to page {page_index + 1}")

        except Exception as e:
            print(f"❌ Error in _navigate_to_page: {e}")
            import traceback
            traceback.print_exc()

    # Additional helper method for debugging
    def debug_page_navigation(self):
        """Debug current page state"""
        print(f"\n🔍 PAGE NAVIGATION DEBUG:")
        print(f"   Current page (internal): {getattr(self, 'current_page', 'Unknown')}")
        print(f"   Current page (display): {getattr(self, 'current_page', 0) + 1}")

        if hasattr(self, 'document') and self.document:
            print(f"   Total pages: {self.document.get_page_count()}")
        else:
            print(f"   No document loaded")

        if hasattr(self, 'toolbar_widget') and self.toolbar_widget:
            print(f"   Toolbar shows: {getattr(self.toolbar_widget, 'current_page_display', 'Unknown')}")

        print()

    def navigate_to_page_with_coordinates(self, page_index: int, x: float = 0, y: float = 0):
        """
        CORRECTED - Expects 0-based page_index from TOC

        Args:
            page_index: 0-based page index (DO NOT add +1)
        """
        print(f"📍 NAVIGATE (FIXED):")
        print(f"   Input page_index: {page_index} (0-based)")

        try:
            if not self.document:
                return False

            total_pages = self.document.get_page_count()
            if page_index < 0 or page_index >= total_pages:
                print(f"❌ Invalid page_index: {page_index}")
                return False

            print(f"   Navigating to page index: {page_index}")
            print(f"   Will display as: Page {page_index + 1}")

            # Use page_index directly in navigation
            self._navigate_to_page(page_index)  # 0-based input expected

            # Update UI display (add +1 only for display)
            if hasattr(self, 'toolbar_widget'):
                self.toolbar_widget.update_current_page(page_index + 1)

            self.current_page = page_index
            return True

        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False

    def _navigate_to_page(self, page_index: int):
        """
        Core navigation - expects 0-based page_index
        """
        print(f"📄 Core navigation to page_index: {page_index}")

        # Your existing navigation logic here
        # Make sure it treats page_index as 0-based
        if hasattr(self, 'canvas_widget'):
            # Example navigation code
            y_position = self.canvas_widget.get_page_y_position(page_index)
            if hasattr(self, 'scroll_area'):
                self.scroll_area.verticalScrollBar().setValue(int(y_position))

        self.current_page = page_index

    def add_link_control_to_ui(self):
        """Add link control panel to UI"""
        if not self.link_control_panel:
            return

        # Option 1: Add to properties panel if it exists
        if hasattr(self, 'properties_panel') and self.properties_panel:
            try:
                # Add as a collapsible section or direct widget
                self.properties_panel.layout().addWidget(self.link_control_panel)
                print("📎 Added link controls to properties panel")
                return
            except:
                pass

        # Option 2: Add to right panel if it exists
        if hasattr(self, 'right_panel') and self.right_panel:
            try:
                self.right_panel.addWidget(self.link_control_panel)
                print("📎 Added link controls to right panel")
                return
            except:
                pass

        # Option 3: Create as dockable widget
        try:
            from PyQt6.QtWidgets import QDockWidget
            dock = QDockWidget("PDF Links", self)
            dock.setWidget(self.link_control_panel)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            print("📎 Added link controls as dock widget")
        except Exception as e:
            print(f"⚠️ Could not add link controls to UI: {e}")

    def connect_link_system_to_canvas(self):
        """Connect link system to PDF canvas"""
        if not self.link_integration:
            return

        # Find the canvas widget
        canvas_widget = None

        # Try different canvas widget names
        canvas_candidates = ['canvas_widget', 'pdf_canvas', 'canvas']
        for attr_name in canvas_candidates:
            if hasattr(self, attr_name):
                canvas_widget = getattr(self, attr_name)
                break

        if not canvas_widget:
            print("❌ No canvas widget found for link integration")
            return

        try:
            print(f"🔗 Connecting link system to {type(canvas_widget).__name__}")

            # Integrate with canvas
            self.link_integration.integrate_with_canvas(canvas_widget)

            # Set PDF document if available
            if hasattr(canvas_widget, 'document') and canvas_widget.document:
                self.link_integration.set_pdf_document(canvas_widget.document)
            elif hasattr(canvas_widget, 'pdf_document') and canvas_widget.pdf_document:
                self.link_integration.set_pdf_document(canvas_widget.pdf_document)

            print("✅ Link system connected to canvas")

        except Exception as e:
            print(f"❌ Error connecting link system: {e}")
            import traceback
            traceback.print_exc()

    def _integrate_links_with_canvas(self):
        """Connect link system to canvas widget"""
        if not (self.link_integration and self.canvas_widget):
            return

        try:
            print("🔗 Connecting link system to canvas...")

            # Integrate with canvas
            self.link_integration.integrate_with_canvas(self.canvas_widget)

            # Set document if available
            if self.document:
                self.link_integration.set_pdf_document(self.document)

            print("✅ Link system connected to canvas")

        except Exception as e:
            print(f"❌ Error connecting link system: {e}")

    def handle_internal_link_navigation(self, page_num: int, x: float, y: float):
        """Handle internal PDF link navigation"""
        try:
            print(f"🔗 Navigating to page {page_num + 1} at coordinates ({x}, {y})")

            # Try various navigation methods
            if hasattr(self, 'navigate_to_page_with_coordinates'):
                return self.navigate_to_page_with_coordinates(page_num, x, y)
            elif hasattr(self, 'navigate_to_page'):
                return self.navigate_to_page(page_num)
            elif hasattr(self, 'canvas_widget') and hasattr(self.canvas_widget, 'set_page'):
                self.canvas_widget.set_page(page_num)
                self.statusBar().showMessage(f"Navigated to page {page_num + 1}", 2000)
                return True
            elif hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'set_page'):
                self.pdf_canvas.set_page(page_num)
                self.statusBar().showMessage(f"Navigated to page {page_num + 1}", 2000)
                return True
            else:
                self.statusBar().showMessage(f"Link to page {page_num + 1} clicked", 2000)
                print("❌ No navigation method available")
                return False

        except Exception as e:
            print(f"❌ Error navigating to internal link: {e}")
            self.statusBar().showMessage("Navigation failed", 2000)
            return False

    def handle_external_link(self, url: str):
        """Handle external URL links"""
        try:
            print(f"🌐 Opening external link: {url}")

            from PyQt6.QtGui import QDesktopServices
            from PyQt6.QtCore import QUrl

            success = QDesktopServices.openUrl(QUrl(url))

            if success:
                self.statusBar().showMessage(f"Opened: {url}", 3000)
            else:
                self.statusBar().showMessage("Failed to open link", 2000)

            return success

        except Exception as e:
            print(f"❌ Error opening external link: {e}")
            self.statusBar().showMessage("Link failed to open", 2000)
            return False

    # !/usr/bin/env python3
    """
    PDF Link Debug Script - Diagnose why links aren't drawing
    Add this to your PDFMainWindow class to debug the link system
    """

    def debug_link_system_comprehensive(self):
        """
        Comprehensive link system debug - call after loading a PDF
        Add this method to your PDFMainWindow class
        """
        print("\n" + "=" * 60)
        print("🔍 COMPREHENSIVE LINK SYSTEM DEBUG")
        print("=" * 60)

        # 1. Check basic integration
        print("\n1️⃣ BASIC INTEGRATION CHECK:")
        components = {
            "link_integration": getattr(self, 'link_integration', None),
            "link_control_panel": getattr(self, 'link_control_panel', None),
            "canvas_widget": getattr(self, 'canvas_widget', None),
            "document": getattr(self, 'document', None),
        }

        for name, obj in components.items():
            status = "✅" if obj else "❌"
            print(f"   {status} {name}: {type(obj).__name__ if obj else 'None'}")

        if not all(components.values()):
            print("❌ CRITICAL: Basic components missing!")
            return

        # 2. Check document compatibility
        print("\n2️⃣ DOCUMENT COMPATIBILITY:")
        doc = self.document
        doc_checks = {
            "has_doc_attr": hasattr(doc, 'doc'),
            "doc_is_fitz": hasattr(doc, 'doc') and str(type(doc.doc)).find('fitz') >= 0,
            "page_count": getattr(doc, 'page_count', 0) > 0,
        }

        for check, result in doc_checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")

        if hasattr(doc, 'doc'):
            print(f"   📄 PyMuPDF doc type: {type(doc.doc)}")
            print(f"   📄 Page count: {getattr(doc, 'page_count', 'unknown')}")

        # 3. Test link extraction
        print("\n3️⃣ LINK EXTRACTION TEST:")
        link_manager = self.link_integration.link_manager

        try:
            # Test on page 0
            page_num = 0
            print(f"   🔍 Testing link extraction on page {page_num + 1}...")

            # Check if document is set in link manager
            print(f"   📎 Link manager document: {link_manager.pdf_document}")

            # Try extracting links
            links = link_manager.extract_page_links(page_num)
            print(f"   📎 Links found: {len(links)}")

            if links:
                print(f"   📎 First 3 links:")
                for i, link in enumerate(links[:3]):
                    print(f"      {i + 1}. {link.link_type}: {link.tooltip}")
                    print(f"         Rect: {link.rect}")
            else:
                print("   ⚠️  No links found - checking raw PyMuPDF...")

                # Direct PyMuPDF test
                if hasattr(doc, 'doc') and len(doc.doc) > page_num:
                    page = doc.doc[page_num]
                    raw_links = page.get_links()
                    print(f"   📎 Raw PyMuPDF links: {len(raw_links)}")

                    if raw_links:
                        print(f"   📎 First raw link: {raw_links[0]}")
                    else:
                        print("   ⚠️  This PDF has no hyperlinks!")

        except Exception as e:
            print(f"   ❌ Link extraction error: {e}")
            import traceback
            traceback.print_exc()

        # 4. Check overlay manager
        print("\n4️⃣ OVERLAY MANAGER CHECK:")
        overlay_mgr = self.link_integration.overlay_manager

        if overlay_mgr:
            print(f"   ✅ Overlay manager exists: {type(overlay_mgr).__name__}")
            print(f"   📎 Parent widget: {overlay_mgr.parent()}")
            print(f"   📎 Current page: {overlay_mgr.current_page}")
            print(f"   📎 Current zoom: {overlay_mgr.current_zoom}")
            print(f"   📎 Overlay count: {len(overlay_mgr.link_overlays)}")
            print(f"   📎 Geometry: {overlay_mgr.geometry()}")
            print(f"   📎 Visible: {overlay_mgr.isVisible()}")

            # Check individual overlays
            if overlay_mgr.link_overlays:
                print(f"   📎 First 3 overlays:")
                for i, overlay in enumerate(overlay_mgr.link_overlays[:3]):
                    print(f"      {i + 1}. Visible: {overlay.isVisible()}")
                    print(f"         Geometry: {overlay.geometry()}")
                    print(f"         Parent: {overlay.parent()}")
            else:
                print("   ⚠️  No overlay widgets created")
        else:
            print("   ❌ No overlay manager!")

        # 5. Test canvas integration
        print("\n5️⃣ CANVAS INTEGRATION CHECK:")
        canvas = self.canvas_widget

        print(f"   📐 Canvas geometry: {canvas.geometry()}")
        print(f"   📐 Canvas visible: {canvas.isVisible()}")

        # Check if overlay manager covers canvas
        if overlay_mgr and canvas:
            canvas_rect = canvas.geometry()
            overlay_rect = overlay_mgr.geometry()
            print(f"   📐 Canvas rect: {canvas_rect}")
            print(f"   📐 Overlay rect: {overlay_rect}")

            covers = (overlay_rect.width() >= canvas_rect.width() * 0.8 and
                      overlay_rect.height() >= canvas_rect.height() * 0.8)
            status = "✅" if covers else "❌"
            print(f"   {status} Overlay covers canvas: {covers}")

        # 6. Test signal connections
        print("\n6️⃣ SIGNAL CONNECTION CHECK:")
        try:
            # Check if signals are connected
            signals_to_check = [
                (canvas, 'pageChanged'),
                (canvas, 'zoomChanged'),
            ]

            for obj, signal_name in signals_to_check:
                if hasattr(obj, signal_name):
                    signal = getattr(obj, signal_name)
                    # Check if signal has receivers (connected slots)
                    receiver_count = signal.receivers()
                    print(f"   📡 {signal_name}: {receiver_count} receivers")
                else:
                    print(f"   ❌ {signal_name}: Signal doesn't exist")

        except Exception as e:
            print(f"   ⚠️  Signal check error: {e}")

        # 7. Manual trigger test
        print("\n7️⃣ MANUAL TRIGGER TEST:")
        try:
            current_page = getattr(self, 'current_page', 0)
            current_zoom = getattr(self, 'current_zoom', 1.0)

            print(f"   🔧 Force triggering link update...")
            print(f"   📄 Page: {current_page}, Zoom: {current_zoom}")

            if overlay_mgr:
                overlay_mgr.update_page_links(current_page, current_zoom)
                print(f"   🔧 After manual trigger:")
                print(f"      Overlays: {len(overlay_mgr.link_overlays)}")

                # Make overlays more visible for testing
                for overlay in overlay_mgr.link_overlays:
                    overlay.setStyleSheet("background-color: rgba(255, 0, 0, 100); border: 2px solid red;")
                    overlay.show()
                    overlay.raise_()
                    print(f"      Made overlay visible: {overlay.geometry()}")

        except Exception as e:
            print(f"   ❌ Manual trigger error: {e}")
            import traceback
            traceback.print_exc()

        # 8. Final recommendations
        print("\n8️⃣ RECOMMENDATIONS:")

        if not links:
            print("   💡 Try loading a PDF with known hyperlinks (research paper, web page)")

        if overlay_mgr and not overlay_mgr.link_overlays:
            print("   💡 No overlays created - check link extraction")

        if overlay_mgr and overlay_mgr.link_overlays and not any(o.isVisible() for o in overlay_mgr.link_overlays):
            print("   💡 Overlays exist but not visible - check positioning/z-order")

        print("\n" + "=" * 60)
        print("🔍 DEBUG COMPLETE - Check output above for issues")
        print("=" * 60 + "\n")

    # USAGE:
    # 1. Add this method to your PDFMainWindow class
    # 2. Load a PDF with hyperlinks
    # 3. Call: self.debug_link_system_comprehensive()
    # 4. Check the console output for the specific issue

    def force_link_visibility_test(self):
        """
        Force make links visible with bright red overlays for testing
        Add this method to your PDFMainWindow class
        """
        print("🔴 FORCING LINK VISIBILITY TEST...")

        if not (hasattr(self, 'link_integration') and self.link_integration):
            print("❌ No link integration")
            return

        overlay_mgr = self.link_integration.overlay_manager
        if not overlay_mgr:
            print("❌ No overlay manager")
            return

        # Force update links
        current_page = getattr(self, 'current_page', 0)
        overlay_mgr.update_page_links(current_page, 1.0)

        # Make overlays super visible
        for i, overlay in enumerate(overlay_mgr.link_overlays):
            # Set bright red background
            overlay.setStyleSheet("""
                background-color: rgba(255, 0, 0, 150);
                border: 3px solid red;
            """)

            # Ensure visibility
            overlay.show()
            overlay.raise_()
            overlay.setVisible(True)

            # Print overlay info
            print(f"🔴 Overlay {i + 1}: {overlay.geometry()}, visible={overlay.isVisible()}")

        print(f"🔴 Made {len(overlay_mgr.link_overlays)} overlays bright red")

        if not overlay_mgr.link_overlays:
            print("❌ No overlays to make visible - check link extraction")

    # USAGE:
    # Call: self.force_link_visibility_test()
    # This will make any existing link overlays bright red and very visible

    # !/usr/bin/env python3
    """
    PDF Link Detection Debug - For your specific PDF with known links
    Add this to your PDFMainWindow class to debug why links aren't detected
    """

    def debug_specific_pdf_links(self):
        """
        Debug why links aren't being detected in your specific PDF
        Call this after loading the PDF with the government URLs
        """
        print("\n" + "🔍" * 60)
        print("DEBUGGING SPECIFIC PDF LINK DETECTION")
        print("🔍" * 60)

        # Step 1: Verify document setup
        print("\n1️⃣ DOCUMENT VERIFICATION:")
        if not hasattr(self, 'document') or not self.document:
            print("❌ No document loaded!")
            return

        doc = self.document
        print(f"   📄 Document type: {type(doc)}")
        print(f"   📄 Has 'doc' attribute: {hasattr(doc, 'doc')}")

        if hasattr(doc, 'doc'):
            fitz_doc = doc.doc
            print(f"   📄 PyMuPDF doc type: {type(fitz_doc)}")
            print(f"   📄 Page count: {len(fitz_doc)}")
        else:
            print("❌ CRITICAL: Document wrapper missing 'doc' attribute!")
            print("   This is likely the main issue!")
            return

        # Step 2: Direct PyMuPDF link extraction test
        print("\n2️⃣ DIRECT PYMUPDF TEST:")
        try:
            page = fitz_doc[0]  # First page
            raw_links = page.get_links()
            print(f"   📎 Raw links found: {len(raw_links)}")

            if raw_links:
                print("   📎 First few raw links:")
                for i, link in enumerate(raw_links[:3]):
                    print(f"      {i + 1}. Kind: {link.get('kind', 'unknown')}")
                    print(f"         URI: {link.get('uri', 'none')}")
                    print(f"         From: {link.get('from', 'none')}")
                    print(f"         Page: {link.get('page', 'none')}")
                    print()
            else:
                print("❌ No raw links found by PyMuPDF!")
                print("   This means the PDF links aren't embedded as hyperlink annotations")

        except Exception as e:
            print(f"❌ Error accessing PyMuPDF page: {e}")
            return

        # Step 3: Test link manager
        print("\n3️⃣ LINK MANAGER TEST:")
        if not (hasattr(self, 'link_integration') and self.link_integration):
            print("❌ No link integration!")
            return

        link_manager = self.link_integration.link_manager
        print(f"   🔗 Link manager exists: {link_manager is not None}")
        print(f"   🔗 Link manager document: {link_manager.pdf_document}")

        # Check if document is properly set
        if link_manager.pdf_document != doc:
            print("❌ ISSUE: Link manager has different document!")
            print(f"   Expected: {doc}")
            print(f"   Got: {link_manager.pdf_document}")

        # Try manual link extraction
        try:
            links = link_manager.extract_page_links(0)
            print(f"   🔗 Parsed links: {len(links)}")

            if links:
                for i, link in enumerate(links[:3]):
                    print(f"      {i + 1}. {link.link_type}: {link.tooltip}")
                    print(f"         Rect: {link.rect}")

        except Exception as e:
            print(f"❌ Link extraction error: {e}")
            import traceback
            traceback.print_exc()

        # Step 4: Check if links are text annotations instead
        print("\n4️⃣ CHECKING FOR TEXT ANNOTATIONS:")
        try:
            page = fitz_doc[0]
            annots = page.annots()
            print(f"   📝 Total annotations: {len(list(annots))}")

            page.reload_page()  # Reload to reset annotation iterator
            for i, annot in enumerate(page.annots()):
                print(f"      {i + 1}. Type: {annot.type[1]}")  # (type_num, type_name)
                if annot.type[1] in ['Link', 'Widget']:
                    print(f"         Content: {annot.info.get('content', 'none')}")
                    print(f"         URI: {annot.info.get('uri', 'none')}")

        except Exception as e:
            print(f"⚠️ Annotation check error: {e}")

        # Step 5: Check if URLs are just text (not clickable)
        print("\n5️⃣ TEXT ANALYSIS:")
        try:
            page = fitz_doc[0]
            text_dict = page.get_text("dict")

            print("   🔍 Searching for URL text patterns...")
            url_count = 0

            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            text = span.get("text", "")
                            if "http" in text.lower() or "www." in text.lower():
                                url_count += 1
                                print(f"      Found URL text: {text[:60]}...")

            print(f"   📊 URL-like text found: {url_count}")

            if url_count > 0 and len(raw_links) == 0:
                print("   💡 DIAGNOSIS: URLs exist as text but not as clickable links!")
                print("      This PDF has URL text but no embedded hyperlink annotations.")

        except Exception as e:
            print(f"⚠️ Text analysis error: {e}")

        # Step 6: Final diagnosis
        print("\n6️⃣ DIAGNOSIS:")

        if not hasattr(doc, 'doc'):
            print("   🎯 PRIMARY ISSUE: Document wrapper missing PyMuPDF 'doc' attribute")
            print("   🔧 FIX: Ensure your PDFDocument class exposes the PyMuPDF document")

        elif len(raw_links) == 0:
            print("   🎯 PRIMARY ISSUE: PDF has URL text but no clickable hyperlinks")
            print("   💡 This is common - many PDFs show URLs as text without making them clickable")
            print("   💡 The PDF creator would need to add actual hyperlink annotations")

        else:
            print("   🎯 Links exist but something else is wrong")
            print("   🔧 Check overlay manager positioning and visibility")

        print("\n" + "🔍" * 60)

    def test_document_wrapper_fix(self):
        """
        Test if your PDFDocument wrapper properly exposes PyMuPDF document
        """
        print("\n🔧 TESTING DOCUMENT WRAPPER...")

        if not hasattr(self, 'document') or not self.document:
            print("❌ No document loaded")
            return

        doc = self.document

        # Check various possible attribute names
        possible_attrs = ['doc', '_doc', 'fitz_doc', '_fitz_doc', 'pdf_doc', '_pdf_doc', 'document']

        print("   🔍 Checking for PyMuPDF document in wrapper:")
        for attr in possible_attrs:
            if hasattr(doc, attr):
                obj = getattr(doc, attr)
                print(f"   ✅ Found {attr}: {type(obj)}")

                # Test if it's a PyMuPDF document
                if hasattr(obj, 'get_page_count') or hasattr(obj, '__len__'):
                    print(f"      📄 This looks like PyMuPDF document!")

                    # Test link extraction
                    try:
                        if hasattr(obj, '__getitem__'):  # Can access pages like obj[0]
                            page = obj[0]
                            links = page.get_links()
                            print(f"      🔗 Test extraction: {len(links)} links found")
                    except Exception as e:
                        print(f"      ❌ Test extraction failed: {e}")
            else:
                print(f"   ❌ No {attr}")

        # Test if we can fix it by updating link manager
        if hasattr(self, 'link_integration') and self.link_integration:
            print("\n   🔧 Testing manual document update...")
            for attr in possible_attrs:
                if hasattr(doc, attr):
                    test_doc = getattr(doc, attr)
                    if hasattr(test_doc, '__getitem__'):  # Looks like PyMuPDF doc
                        print(f"   🧪 Testing with {attr}...")

                        # Create a test document wrapper
                        class TestWrapper:
                            def __init__(self, fitz_doc):
                                self.doc = fitz_doc
                                self.page_count = len(fitz_doc)

                        test_wrapper = TestWrapper(test_doc)

                        # Test with link manager
                        try:
                            self.link_integration.link_manager.set_pdf_document(test_wrapper)
                            links = self.link_integration.link_manager.extract_page_links(0)
                            print(f"   ✅ SUCCESS: Found {len(links)} links with {attr}!")

                            if links:
                                print(f"      First link: {links[0].tooltip}")
                                return True

                        except Exception as e:
                            print(f"   ❌ Failed with {attr}: {e}")

        return False

    # USAGE INSTRUCTIONS:
    # 1. Add both methods to your PDFMainWindow class
    # 2. Load your PDF with the government URLs
    # 3. Call: self.debug_specific_pdf_links()
    # 4. If document wrapper issue found, call: self.test_document_wrapper_fix()
    # 5. Check console output for specific diagnosis

def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Create and show main window
    window = PDFMainWindow()
    window.show()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())