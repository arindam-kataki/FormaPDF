"""
PDF Main Window - Complete Implementation with Toolbar Widget
Main window for PDF Voice Editor using new toolbar widget
"""

import sys
import webbrowser

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QScrollArea, QVBoxLayout,
    QWidget, QFileDialog, QMenuBar, QStatusBar, QMessageBox, QDockWidget, QDialog
)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, pyqtSlot, QUrl
from PyQt6.QtGui import QAction, QDesktopServices

from src.ui.a_toc_integration import TOCIntegration
from src.ui.a_toolbar_widget import ToolbarWidget
from src.ui.a_canvas_widget import CanvasWidget
from src.ui.a_pdf_document import PDFDocument
from ui.a_pdf_link_control_panel import PDFLinkControlPanel, PDFLinkVoiceIntegration
from ui.a_pdf_link_integration import ExternalLinkConfirmDialog
from ui.a_pdf_link_manager import PDFLink
from ui.a_link_debug_control_panel import LinkDebugControlPanel
#from ui.a_pdf_link_overlay_manager import PDFLinkIntegration
from ui.a_raw_link_overlay_manager import RawLinkIntegration

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
        self.link_menu_integration = None
        self.link_debug_panel = None
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

        self._setup_link_system()
        self.setup_link_debug_panel()

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

    def _setup_link_system(self):
        """Setup the ultra-fast raw PDF link system"""
        print("🚀 Setting up ultra-fast raw PDF link system...")

        try:
            # Create RAW link integration (ultra-fast)
            self.link_integration = RawLinkIntegration(self)

            # Connect main signals (same as before)
            self.link_integration.linkNavigationRequested.connect(self._handle_link_navigation)
            self.link_integration.externalLinkRequested.connect(self._handle_external_link_request)
            self.link_integration.linkStatusChanged.connect(self._update_link_status)

            # Create and setup link control panel (same as before)
            self.link_control_panel = PDFLinkControlPanel(self.link_integration, self)

            # Connect control panel signals (same as before)
            self.link_control_panel.linkActivated.connect(self._handle_link_activation)
            self.link_control_panel.linkHighlighted.connect(self._handle_link_highlight)
            self.link_control_panel.overlayVisibilityChanged.connect(self._handle_overlay_visibility)
            self.link_control_panel.pageNavigationRequested.connect(self._handle_page_navigation)

            # Add control panel to UI as dock widget (same as before)
            self._add_link_control_dock()

            print("✅ Ultra-fast raw PDF link system setup complete")

        except Exception as e:
            print(f"❌ Error setting up raw link system: {e}")
            import traceback
            traceback.print_exc()

    def _setup_link_system_full(self):
        """Setup the complete PDF link system"""
        print("🔗 Setting up PDF link system...")

        # Create link integration
        self.link_integration = None #PDFLinkIntegration(self)

        # Connect main signals
        self.link_integration.linkNavigationRequested.connect(self._handle_link_navigation)
        self.link_integration.externalLinkRequested.connect(self._handle_external_link_request)
        self.link_integration.linkStatusChanged.connect(self._update_link_status)

        # Create and setup link control panel
        self.link_control_panel = PDFLinkControlPanel(self.link_integration, self)

        # Connect control panel signals
        self.link_control_panel.linkActivated.connect(self._handle_link_activation)
        self.link_control_panel.linkHighlighted.connect(self._handle_link_highlight)
        self.link_control_panel.overlayVisibilityChanged.connect(self._handle_overlay_visibility)
        self.link_control_panel.pageNavigationRequested.connect(self._handle_page_navigation)

        # Add control panel to UI as dock widget
        self._add_link_control_dock()

        print("✅ PDF link system setup complete")

    def _add_link_control_dock(self):
        """Add link control panel as dockable widget"""
        try:
            # Create dock widget
            dock = QDockWidget("PDF Links", self)
            dock.setWidget(self.link_control_panel)
            dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable |
                QDockWidget.DockWidgetFeature.DockWidgetFloatable
            )

            # Add to right side (adjust as needed for your layout)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

            print("📎 Link control panel added as dock widget")

        except Exception as e:
            print(f"⚠️ Could not add link control dock: {e}")

    def _update_link_status(self, status_message: str):
        """Update status bar with link information"""
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.showMessage(status_message, 2000)
        else:
            print(f"🔗 Link Status: {status_message}")

    def _setup_voice_integration(self):
        """Setup voice control for link functionality"""
        # Create voice integration
        self.link_voice_integration = PDFLinkVoiceIntegration(self.link_control_panel)

        # If you have existing voice control system, integrate with it
        # self.voice_handler.add_command_handler(self.link_voice_integration.handle_voice_command)

        print("🎤 Link voice integration setup complete")

    def integrate_links_with_canvas(self):
        """Integrate links with the canvas widget"""
        if hasattr(self, 'canvas_widget') and self.link_integration:
            print("🔗 Integrating links with canvas...")

            # Integrate with canvas
            self.link_integration.integrate_with_canvas(self.canvas_widget)

            # Connect canvas signals for link updates
            if hasattr(self.canvas_widget, 'pageChanged'):
                self.canvas_widget.pageChanged.connect(self._on_page_changed_links)

            if hasattr(self.canvas_widget, 'zoomChanged'):
                self.canvas_widget.zoomChanged.connect(self._on_zoom_changed_links)

            if hasattr(self, 'scroll_area') and self.scroll_area:
                scrollbar = self.scroll_area.verticalScrollBar()
                scrollbar.valueChanged.connect(self._on_scroll_changed_links)

            print("✅ Link-canvas integration complete")

    def _update_links_for_current_page(self):
        """Update link overlays for current page"""
        if self.link_integration and hasattr(self, 'current_page'):
            current_page = getattr(self, 'current_page', 0)
            current_zoom = getattr(self, 'current_zoom', 1.0)

            # Update link overlays
            self.link_integration.update_page_view(current_page, current_zoom)

            # Update control panel
            self.link_control_panel.set_current_page(current_page)

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

    def _on_scroll_changed_links(self):
        """Handle scroll change for link overlays"""
        if self.link_integration and self.link_integration.overlay_manager and self.canvas_widget:
            # Get current visible pages from canvas
            visible_pages = getattr(self.canvas_widget, 'visible_pages', [])
            current_page = getattr(self.canvas_widget, 'current_page', 0)
            zoom_level = getattr(self.canvas_widget, 'zoom_level', 1.0)

            # Only update if visible pages actually changed
            if hasattr(self, '_last_visible_pages'):
                if self._last_visible_pages == visible_pages:
                    return  # No change, skip update

            self._last_visible_pages = visible_pages.copy()

            print(f"🔗 Scroll changed - updating overlays for visible pages {visible_pages}")
            self.link_integration.overlay_manager.update_page_links(
                current_page, zoom_level, visible_pages
            )

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

                    # FIXED: Link integration
                    if hasattr(self, 'link_integration') and self.link_integration:
                        print("🔗 Setting up links for new document...")

                        # CRITICAL: Ensure canvas integration is set up
                        self._integrate_links_with_canvas()

                        # Set document in link manager
                        self.link_integration.set_pdf_document(self.document)

                        # Force immediate link update for page 0
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

                            print("✅ Link overlays set up for page 0")
                        else:
                            print("❌ ERROR: overlay_manager still None after integration attempt")

            # Add link-specific loading
            if hasattr(self, 'document') and hasattr(self, 'link_integration') and self.link_integration:
                print("🔗 Setting up links for new document...")

                # Set document in link system
                self.link_integration.set_pdf_document(self.document, file_path)

                # Update link control panel
                if hasattr(self, 'link_control_panel') and self.link_control_panel:
                    self.link_control_panel.set_document(self.document, file_path)
                    self.link_control_panel.apply_settings()

                # Integrate with canvas if available
                if hasattr(self, 'canvas_widget'):
                    self.integrate_links_with_canvas()

                # Update links for current page
                if hasattr(self, 'current_page'):
                    self._on_page_changed_links(self.current_page)

                print(f"✅ Links loaded for document: {file_path}")

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
            self.canvas_widget.set_visible_pages_optimized(visible_pages, viewport_rect)

            if visible_pages:
                viewport_center_y = viewport_rect.y() + (viewport_rect.height() / 2)
                center_page = self.canvas_widget.get_page_at_position(viewport_center_y)
                print(f"📄 Page changed to -------------------------------------: {center_page + 1}")

                if center_page != getattr(self, 'current_page', 0):
                    self.current_page = center_page
                    display_page = center_page + 1

                    if hasattr(self, 'toolbar_widget') and self.toolbar_widget:
                        if hasattr(self.toolbar_widget, 'page_spinbox'):
                            self.toolbar_widget.page_spinbox.blockSignals(True)
                            self.toolbar_widget.page_spinbox.setValue(display_page)
                            self.toolbar_widget.page_spinbox.blockSignals(False)
                            print(f"✅ Updated toolbar widget spinner to {display_page}")
                        elif hasattr(self.toolbar_widget, 'update_document_info'):
                            # Use the proper update method
                            total_pages = self.canvas_widget.document.get_page_count() if self.canvas_widget.document else 1
                            self.toolbar_widget.update_document_info(display_page, total_pages)
                            print(f"✅ Updated via toolbar update_document_info to {display_page}")

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

    def _navigate_to_page_with_coordinates(self, page_num: int, x: float = 0, y: float = 0):
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

    def _navigate_to_page_with_coordinates(self, page_num: int, x: float = 0, y: float = 0):
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

    def setup_link_debug_panel(self):
        """Add link debug panel to UI"""
        if hasattr(self, 'link_integration') and self.link_integration:
            # Create debug panel
            self.link_debug_panel = LinkDebugControlPanel(self.link_integration)

            # Add to your UI layout (adjust based on your layout structure)
            # Option 1: Add to sidebar
            if hasattr(self, 'sidebar_layout'):
                self.sidebar_layout.addWidget(self.link_debug_panel)

            # Option 2: Add to properties panel
            elif hasattr(self, 'properties_panel'):
                self.properties_panel.addWidget(self.link_debug_panel)

            # Option 3: Create as separate dock widget
            else:
                from PyQt6.QtWidgets import QDockWidget
                dock = QDockWidget("Link Debug", self)
                dock.setWidget(self.link_debug_panel)
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

            print("🐛 Link debug panel added to UI")

    # ======================
    # LINK METHODS
    # ======================


    # ======================
    # LINK EVENT HANDLERS
    # ======================

    @pyqtSlot(int, float, float)
    def _handle_link_navigation(self, page_index: int, x: float, y: float):
        """Handle internal link navigation from overlays"""
        try:
            print(f"📄 Link navigation requested: Page {page_index + 1} at ({x:.1f}, {y:.1f})")

            # Validate page bounds
            if hasattr(self, 'document') and self.document:
                total_pages = self.document.get_page_count()
                if page_index < 0 or page_index >= total_pages:
                    print(f"❌ Invalid page index: {page_index} (max: {total_pages - 1})")
                    page_index = max(0, min(page_index, total_pages - 1))
                    print(f"   → Clamped to page: {page_index}")

            # Try different navigation methods in order of preference
            success = False

            # Method 1: navigate_to_page_with_coordinates (if available)
            if hasattr(self, 'navigate_to_page_with_coordinates'):
                print(f"   → Using navigate_to_page_with_coordinates({page_index}, {x}, {y})")
                self.navigate_to_page_with_coordinates(page_index, x, y)
                success = True

            # Method 2: _navigate_to_page (internal method)
            elif hasattr(self, '_navigate_to_page'):
                print(f"   → Using _navigate_to_page({page_index})")
                self._navigate_to_page(page_index)
                success = True

            # Method 3: navigate_to_page (public method)
            elif hasattr(self, 'navigate_to_page'):
                print(f"   → Using navigate_to_page({page_index})")
                self.navigate_to_page(page_index)
                success = True

            # Method 4: _on_page_jump (UI-based navigation)
            elif hasattr(self, '_on_page_jump'):
                print(f"   → Using _on_page_jump({page_index + 1})")  # Convert to 1-based for UI
                self._on_page_jump(page_index + 1)
                success = True

            # Method 5: Direct canvas scroll (fallback)
            elif hasattr(self, 'canvas_widget') and self.canvas_widget:
                print(f"   → Using direct canvas scroll to page {page_index}")
                if hasattr(self.canvas_widget, 'scroll_to_page'):
                    self.canvas_widget.scroll_to_page(page_index)
                    success = True
                elif hasattr(self.canvas_widget, 'layout_manager'):
                    # Get page Y position and scroll there
                    page_rect = self.canvas_widget.layout_manager.get_page_rect(page_index)
                    if page_rect and hasattr(self, 'scroll_area'):
                        self.scroll_area.verticalScrollBar().setValue(int(page_rect.y()))
                        success = True

            if not success:
                print("❌ No navigation method available")
                return False

            # Update current page tracking
            self.current_page = page_index

            # Update UI components
            self._update_ui_after_navigation(page_index)

            # Show status message
            if hasattr(self, 'status_bar') or hasattr(self, 'statusBar'):
                status_bar = getattr(self, 'status_bar', None) or self.statusBar()
                status_bar.showMessage(f"Navigated to page {page_index + 1}", 3000)

            print(f"✅ Successfully navigated to page {page_index + 1}")
            return True

        except Exception as e:
            print(f"❌ Error handling link navigation: {e}")
            import traceback
            traceback.print_exc()
            return False

    @pyqtSlot(str)
    def _handle_external_link_request(self, url: str):
        """Handle external URL link request"""
        try:
            # Show confirmation dialog
            dialog = ExternalLinkConfirmDialog(url, self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Open URL
                success = QDesktopServices.openUrl(QUrl(url))

                if success:
                    self.status_bar.showMessage(f"Opened external link: {url}", 3000)
                    print(f"🌐 Opened external URL: {url}")
                else:
                    # Fallback to webbrowser
                    webbrowser.open(url)
                    self.status_bar.showMessage(f"Opened external link (fallback): {url}", 3000)
            else:
                self.status_bar.showMessage("External link cancelled", 2000)

        except Exception as e:
            print(f"❌ Error handling external link: {e}")
            QMessageBox.warning(self, "Link Error", f"Failed to open external link:\n{str(e)}")

    @pyqtSlot(object)
    def _handle_link_activation(self, pdf_link: PDFLink):
        """Handle link activation from control panel"""
        try:
            print(f"🔗 Activating link: {pdf_link.description}")

            # Let the link manager handle the click
            if self.link_integration and self.link_integration.link_manager:
                success = self.link_integration.link_manager.handle_link_click(pdf_link)

                if success:
                    self.status_bar.showMessage(f"Activated: {pdf_link.description}", 3000)
                else:
                    self.status_bar.showMessage(f"Failed to activate link", 2000)

        except Exception as e:
            print(f"❌ Error activating link: {e}")

    @pyqtSlot(object)
    def _handle_link_highlight(self, pdf_link: PDFLink):
        """Handle link highlight from control panel"""
        try:
            # Highlight the link in overlay manager
            if self.link_integration and self.link_integration.overlay_manager:
                self.link_integration.overlay_manager.highlight_link(pdf_link)

            # Update status with link info
            self.status_bar.showMessage(f"Link: {pdf_link.description}")

        except Exception as e:
            print(f"❌ Error highlighting link: {e}")

    @pyqtSlot(bool)
    def _handle_overlay_visibility(self, visible: bool):
        """Handle overlay visibility change"""
        try:
            if self.link_integration:
                self.link_integration.set_links_visible(visible)

            status_msg = "Link overlays shown" if visible else "Link overlays hidden"
            self.status_bar.showMessage(status_msg, 2000)

        except Exception as e:
            print(f"❌ Error handling overlay visibility: {e}")

    @pyqtSlot(int)
    def _handle_page_navigation(self, page_index: int):
        """Handle page navigation from control panel"""
        try:
            # Navigate using existing method
            if hasattr(self, 'navigate_to_page'):
                self.navigate_to_page(page_index)
            elif hasattr(self, '_on_page_jump'):
                self._on_page_jump(page_index + 1)  # Convert to 1-based

        except Exception as e:
            print(f"❌ Error handling page navigation: {e}")

    @pyqtSlot(str)
    def _update_link_status(self, status_message: str):
        """Update status bar with link information"""
        self.status_bar.showMessage(status_message, 2000)

    def _update_ui_after_navigation(self, page_index: int):
        """Update UI components after navigation - Using blockSignals() pattern"""
        try:
            print(f"🔄 Updating UI for page {page_index + 1} (using blockSignals)")

            # Update toolbar page spinner
            if hasattr(self, 'toolbar_widget') and self.toolbar_widget:
                if hasattr(self.toolbar_widget, 'page_spinbox'):
                    spinner = self.toolbar_widget.page_spinbox
                    spinner.blockSignals(True)
                    spinner.setValue(page_index + 1)
                    spinner.blockSignals(False)
                    print(f"   ✅ Updated toolbar spinner: {page_index + 1}")

                elif hasattr(self.toolbar_widget, 'update_current_page'):
                    # If it has a safe update method, use it
                    self.toolbar_widget.update_current_page(page_index + 1)
                    print(f"   ✅ Updated toolbar via update_current_page: {page_index + 1}")

            # Update main page spinbox (if separate from toolbar)
            if hasattr(self, 'page_spinbox'):
                self.page_spinbox.blockSignals(True)
                self.page_spinbox.setValue(page_index + 1)
                self.page_spinbox.blockSignals(False)
                print(f"   ✅ Updated main page spinner: {page_index + 1}")

            # Update link control panel page spinner
            if hasattr(self, 'link_control_panel') and self.link_control_panel:
                if hasattr(self.link_control_panel, 'page_spinbox'):
                    spinner = self.link_control_panel.page_spinbox
                    spinner.blockSignals(True)
                    spinner.setValue(page_index + 1)
                    spinner.blockSignals(False)
                    print(f"   ✅ Updated link panel spinner: {page_index + 1}")

                # Update current page (this should be safe)
                self.link_control_panel.set_current_page(page_index)
                print(f"   ✅ Updated link panel current page: {page_index}")

            # Update other navigation controls
            if hasattr(self, 'navigation_widget'):
                if hasattr(self.navigation_widget, 'page_input'):
                    self.navigation_widget.page_input.blockSignals(True)
                    self.navigation_widget.page_input.setValue(page_index + 1)
                    self.navigation_widget.page_input.blockSignals(False)
                    print(f"   ✅ Updated navigation widget: {page_index + 1}")

            # Update canvas overlays for new page (this should be safe)
            if hasattr(self, 'canvas_widget') and self.canvas_widget:
                self.canvas_widget.draw_link_overlays()
                print(f"   ✅ Updated canvas overlays")

            print(f"🔄 UI update completed for page {page_index + 1}")

        except Exception as e:
            print(f"⚠️ Error updating UI after navigation: {e}")

def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Create and show main window
    window = PDFMainWindow()
    window.show()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())