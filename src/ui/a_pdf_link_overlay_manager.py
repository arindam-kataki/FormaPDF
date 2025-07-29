"""
PDF Link Overlay Manager - PyQt6 Implementation
Manages visual overlays for PDF hyperlinks on the canvas widget
"""

from PyQt6.QtWidgets import QWidget, QLabel, QToolTip
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QCursor, QPalette
from typing import List, Dict, Optional, Tuple
import time

from a_pdf_link_manager import PDFLinkManager, PDFLink, LinkType


class LinkOverlay(QLabel):
    """Individual overlay widget for a single hyperlink"""

    # Signals
    linkClicked = pyqtSignal(object)  # PDFLink
    linkHovered = pyqtSignal(object)  # PDFLink
    linkLeft = pyqtSignal(object)  # PDFLink

    def __init__(self, pdf_link: PDFLink, parent=None):
        super().__init__(parent)

        self.pdf_link = pdf_link
        self.is_hovered = False

        # Setup appearance based on link type
        self._setup_appearance()

        # Enable mouse tracking
        self.setMouseTracking(True)

        # Set tooltip
        self.setToolTip(self.pdf_link.description)

    def _setup_appearance(self):
        """Setup visual appearance based on link type"""
        # Base styling
        self.setStyleSheet(self._get_base_style())

        # Set cursor
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Make transparent by default
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _get_base_style(self) -> str:
        """Get CSS style based on link type"""
        if self.pdf_link.link_type == LinkType.URI:
            return """
                QLabel {
                    border: 2px dashed #0066cc;
                    background-color: rgba(0, 102, 204, 20);
                }
                QLabel:hover {
                    border: 2px solid #0066cc;
                    background-color: rgba(0, 102, 204, 40);
                }
            """
        elif self.pdf_link.link_type in [LinkType.GOTO, LinkType.NAMED]:
            return """
                QLabel {
                    border: 2px dashed #009900;
                    background-color: rgba(0, 153, 0, 20);
                }
                QLabel:hover {
                    border: 2px solid #009900;
                    background-color: rgba(0, 153, 0, 40);
                }
            """
        elif self.pdf_link.link_type in [LinkType.GOTOR, LinkType.LAUNCH]:
            return """
                QLabel {
                    border: 2px dashed #9900cc;
                    background-color: rgba(153, 0, 204, 20);
                }
                QLabel:hover {
                    border: 2px solid #9900cc;
                    background-color: rgba(153, 0, 204, 40);
                }
            """
        else:
            return """
                QLabel {
                    border: 2px dashed #666666;
                    background-color: rgba(102, 102, 102, 20);
                }
                QLabel:hover {
                    border: 2px solid #666666;
                    background-color: rgba(102, 102, 102, 40);
                }
            """

    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.linkClicked.emit(self.pdf_link)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter"""
        self.is_hovered = True
        self.linkHovered.emit(self.pdf_link)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.is_hovered = False
        self.linkLeft.emit(self.pdf_link)
        super().leaveEvent(event)

    def update_position(self, canvas_rect: QRectF, zoom_level: float, page_offset: QPointF):
        """Update overlay position based on canvas coordinates"""
        # Convert PDF coordinates to canvas coordinates
        pdf_rect = self.pdf_link.bounds

        # Scale by zoom level
        scaled_x = pdf_rect.x() * zoom_level
        scaled_y = pdf_rect.y() * zoom_level
        scaled_width = pdf_rect.width() * zoom_level
        scaled_height = pdf_rect.height() * zoom_level

        # Apply page offset
        canvas_x = scaled_x + page_offset.x()
        canvas_y = scaled_y + page_offset.y()

        # Set geometry
        self.setGeometry(int(canvas_x), int(canvas_y), int(scaled_width), int(scaled_height))


class PDFLinkOverlayManager(QObject):
    """
    Manages all link overlays for the PDF canvas
    Creates, positions, and updates overlay widgets
    """

    # Signals
    linkClicked = pyqtSignal(object)  # PDFLink
    linkHovered = pyqtSignal(object)  # PDFLink
    overlaysUpdated = pyqtSignal(int, int)  # page_index, overlay_count

    def __init__(self, canvas_widget, link_manager: PDFLinkManager, parent=None):
        super().__init__(parent)

        self.canvas_widget = canvas_widget
        self.link_manager = link_manager

        # State tracking
        self.current_page = 0
        self.current_zoom = 1.0
        self.visible_pages = []

        # Overlay management
        self.active_overlays = {}  # page_index -> List[LinkOverlay]
        self.overlay_pool = []  # Reusable overlay widgets
        self.max_pool_size = 50  # Maximum pooled overlays

        # Performance settings
        self.update_delay = 100  # ms delay for batch updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._perform_delayed_update)
        self.update_timer.setSingleShot(True)

        # Visual settings
        self.show_overlays = True
        self.overlay_opacity = 0.7

        # Connect link manager signals
        self._connect_link_manager()

        print("📎 PDFLinkOverlayManager initialized")

    def _connect_link_manager(self):
        """Connect signals from link manager"""
        if self.link_manager:
            self.link_manager.linkExtractionCompleted.connect(self._on_links_extracted)

    def set_canvas_widget(self, canvas_widget):
        """Set or update the canvas widget"""
        self.canvas_widget = canvas_widget
        self._clear_all_overlays()

    def update_page_links(self, page_index: int, zoom_level: float, visible_pages: List[int] = None):
        """Update link overlays for current page and zoom level"""
        self.current_page = page_index
        self.current_zoom = zoom_level

        if visible_pages is not None:
            self.visible_pages = visible_pages
        else:
            self.visible_pages = [page_index]

        # Delay update to batch multiple calls
        self.update_timer.start(self.update_delay)

    def _perform_delayed_update(self):
        """Perform the actual overlay update after delay"""
        if not self.show_overlays or not self.canvas_widget:
            return

        try:
            # Clear existing overlays
            self._clear_all_overlays()

            # Create overlays for visible pages
            for page_index in self.visible_pages:
                self._create_page_overlays(page_index)

            print(f"📎 Updated overlays for pages {self.visible_pages} at zoom {self.current_zoom:.2f}")

        except Exception as e:
            print(f"❌ Error updating link overlays: {e}")

    def _create_page_overlays(self, page_index: int):
        """Create overlay widgets for a specific page"""
        if not self.link_manager:
            return

        # Extract links for this page
        page_links = self.link_manager.extract_page_links(page_index)

        if not page_links:
            return

        # Calculate page offset on canvas
        page_offset = self._get_page_offset(page_index)
        if page_offset is None:
            return

        # Create overlays for each link
        page_overlays = []
        for pdf_link in page_links:
            overlay = self._get_or_create_overlay(pdf_link)
            if overlay:
                # Update position
                canvas_rect = QRectF(self.canvas_widget.rect())
                overlay.update_position(canvas_rect, self.current_zoom, page_offset)

                # Connect signals
                overlay.linkClicked.connect(self._on_overlay_clicked)
                overlay.linkHovered.connect(self._on_overlay_hovered)

                # Show overlay
                overlay.show()
                overlay.raise_()  # Bring to front

                page_overlays.append(overlay)

        # Store overlays for this page
        self.active_overlays[page_index] = page_overlays

        # Emit signal
        self.overlaysUpdated.emit(page_index, len(page_overlays))

    def _get_or_create_overlay(self, pdf_link: PDFLink) -> Optional[LinkOverlay]:
        """Get overlay from pool or create new one"""
        try:
            # Try to reuse from pool
            if self.overlay_pool:
                overlay = self.overlay_pool.pop()
                overlay.pdf_link = pdf_link
                overlay._setup_appearance()
                overlay.setToolTip(pdf_link.description)
            else:
                # Create new overlay
                overlay = LinkOverlay(pdf_link, self.canvas_widget)

            return overlay

        except Exception as e:
            print(f"❌ Error creating overlay: {e}")
            return None

    def _get_page_offset(self, page_index: int) -> Optional[QPointF]:
        """Calculate page offset on canvas"""
        if not self.canvas_widget or not hasattr(self.canvas_widget, 'layout_manager'):
            return QPointF(0, 0)  # Default offset

        try:
            layout_manager = self.canvas_widget.layout_manager
            if layout_manager and hasattr(layout_manager, 'get_page_rect'):
                page_rect = layout_manager.get_page_rect(page_index)
                if page_rect:
                    return QPointF(page_rect.x(), page_rect.y())
        except Exception as e:
            print(f"⚠️ Could not get page offset for page {page_index}: {e}")

        return QPointF(0, 0)

    def _clear_all_overlays(self):
        """Clear and hide all active overlays"""
        for page_index, overlays in self.active_overlays.items():
            for overlay in overlays:
                overlay.hide()

                # Return to pool if not full
                if len(self.overlay_pool) < self.max_pool_size:
                    self.overlay_pool.append(overlay)
                else:
                    # Delete excess overlays
                    overlay.deleteLater()

        self.active_overlays.clear()

    def _on_links_extracted(self, page_index: int, links: List[PDFLink]):
        """Handle links extracted signal from link manager"""
        if page_index in self.visible_pages:
            # Recreate overlays for this page
            self._create_page_overlays(page_index)

    def _on_overlay_clicked(self, pdf_link: PDFLink):
        """Handle overlay click"""
        self.linkClicked.emit(pdf_link)

        # Also trigger link manager's handler
        if self.link_manager:
            self.link_manager.handle_link_click(pdf_link)

    def _on_overlay_hovered(self, pdf_link: PDFLink):
        """Handle overlay hover"""
        self.linkHovered.emit(pdf_link)

    def set_overlay_visibility(self, visible: bool):
        """Show or hide all overlays"""
        self.show_overlays = visible

        if visible:
            self.update_page_links(self.current_page, self.current_zoom, self.visible_pages)
        else:
            self._clear_all_overlays()

    def set_overlay_opacity(self, opacity: float):
        """Set overlay opacity (0.0 to 1.0)"""
        self.overlay_opacity = max(0.0, min(1.0, opacity))

        # Update existing overlays
        for overlays in self.active_overlays.values():
            for overlay in overlays:
                overlay.setWindowOpacity(self.overlay_opacity)

    def get_links_at_position(self, canvas_pos: QPointF) -> List[PDFLink]:
        """Get all links at a specific canvas position"""
        found_links = []

        for overlays in self.active_overlays.values():
            for overlay in overlays:
                if overlay.geometry().contains(canvas_pos.toPoint()):
                    found_links.append(overlay.pdf_link)

        return found_links

    def highlight_link(self, pdf_link: PDFLink, highlight: bool = True):
        """Highlight or unhighlight a specific link"""
        for overlays in self.active_overlays.values():
            for overlay in overlays:
                if overlay.pdf_link.id == pdf_link.id:
                    if highlight:
                        overlay.setStyleSheet(overlay._get_base_style() + """
                            QLabel {
                                border: 3px solid #ff6600 !important;
                                background-color: rgba(255, 102, 0, 60) !important;
                            }
                        """)
                    else:
                        overlay._setup_appearance()
                    break

    def get_overlay_stats(self) -> Dict[str, int]:
        """Get statistics about current overlays"""
        total_overlays = sum(len(overlays) for overlays in self.active_overlays.values())

        return {
            'active_pages': len(self.active_overlays),
            'total_overlays': total_overlays,
            'pooled_overlays': len(self.overlay_pool),
            'current_page': self.current_page,
            'visible_pages_count': len(self.visible_pages)
        }

    def debug_print_overlays(self):
        """Debug: Print information about current overlays"""
        print("\n📎 Link Overlay Debug Info:")
        print(f"   Current page: {self.current_page}")
        print(f"   Current zoom: {self.current_zoom:.2f}")
        print(f"   Visible pages: {self.visible_pages}")
        print(f"   Active pages with overlays: {list(self.active_overlays.keys())}")

        for page_index, overlays in self.active_overlays.items():
            print(f"   📄 Page {page_index + 1}: {len(overlays)} overlays")
            for i, overlay in enumerate(overlays):
                link = overlay.pdf_link
                geom = overlay.geometry()
                print(f"      {i + 1}. {link.description}")
                print(f"         Type: {link.link_type.value}")
                print(f"         Canvas pos: ({geom.x()}, {geom.y()}, {geom.width()}, {geom.height()})")
                print(f"         Visible: {overlay.isVisible()}")


class PDFLinkIntegration(QObject):
    """
    High-level integration class that combines link manager and overlay manager
    Provides a unified interface for PDF link functionality
    """

    # Signals
    linkNavigationRequested = pyqtSignal(int, float, float)  # page, x, y
    externalLinkRequested = pyqtSignal(str)  # url
    linkStatusChanged = pyqtSignal(str)  # status message

    def __init__(self, parent=None):
        super().__init__(parent)

        # Components
        self.link_manager = PDFLinkManager(self)
        self.overlay_manager = None  # Will be set when canvas is available

        # State
        self.canvas_widget = None
        self.current_document = None

        # Connect link manager signals
        self._connect_link_manager()

        print("🔗 PDFLinkIntegration initialized")

    def _connect_link_manager(self):
        """Connect link manager signals"""
        self.link_manager.navigationRequested.connect(self.linkNavigationRequested)
        self.link_manager.externalUrlRequested.connect(self.externalLinkRequested)
        self.link_manager.externalUrlRequested.connect(
            lambda url: self.linkStatusChanged.emit(f"External link: {url}")
        )

    def integrate_with_canvas(self, canvas_widget):
        """Integrate with canvas widget"""
        self.canvas_widget = canvas_widget

        # Create overlay manager
        self.overlay_manager = PDFLinkOverlayManager(canvas_widget, self.link_manager, self)

        # Connect overlay manager signals
        self.overlay_manager.linkClicked.connect(self._on_link_clicked)
        self.overlay_manager.linkHovered.connect(self._on_link_hovered)

        print("✅ Link integration with canvas complete")

    def set_pdf_document(self, pdf_document, document_path: str = ""):
        """Set PDF document for both components"""
        self.current_document = pdf_document
        self.link_manager.set_pdf_document(pdf_document, document_path)

        if self.overlay_manager:
            # Clear existing overlays when document changes
            self.overlay_manager._clear_all_overlays()

    def update_page_view(self, page_index: int, zoom_level: float, visible_pages: List[int] = None):
        """Update view for page changes or zoom changes"""
        if self.overlay_manager:
            self.overlay_manager.update_page_links(page_index, zoom_level, visible_pages)

    def _on_link_clicked(self, pdf_link: PDFLink):
        """Handle link click from overlay"""
        self.linkStatusChanged.emit(f"Clicked: {pdf_link.description}")

    def _on_link_hovered(self, pdf_link: PDFLink):
        """Handle link hover from overlay"""
        self.linkStatusChanged.emit(f"Link: {pdf_link.description}")

    def set_links_visible(self, visible: bool):
        """Show or hide link overlays"""
        if self.overlay_manager:
            self.overlay_manager.set_overlay_visibility(visible)

    def get_page_links(self, page_index: int) -> List[PDFLink]:
        """Get links for a specific page"""
        return self.link_manager.extract_page_links(page_index)

    def handle_external_url_confirmation(self, url: str, confirmed: bool):
        """Handle external URL confirmation from UI"""
        if confirmed:
            self.link_manager._open_external_url(url)
            self.linkStatusChanged.emit(f"Opened: {url}")
        else:
            self.linkStatusChanged.emit("External link cancelled")


# Example integration with main window
def example_main_window_integration():
    """Example of how to integrate with main window"""

    # In your main window __init__:
    # self.link_integration = PDFLinkIntegration(self)
    #
    # # Connect signals
    # self.link_integration.linkNavigationRequested.connect(self.navigate_to_page)
    # self.link_integration.externalLinkRequested.connect(self.confirm_external_url)
    # self.link_integration.linkStatusChanged.connect(self.status_bar.showMessage)
    #
    # # After creating canvas:
    # self.link_integration.integrate_with_canvas(self.canvas_widget)
    #
    # # When loading document:
    # self.link_integration.set_pdf_document(self.document, file_path)
    #
    # # On page/zoom changes:
    # self.link_integration.update_page_view(page_index, zoom_level)

    pass


if __name__ == '__main__':
    print("PDFLinkOverlayManager - Use as module import")