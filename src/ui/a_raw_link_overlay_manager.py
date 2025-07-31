"""
Raw Overlay Manager - Ultra-Fast Rendering
Creates overlays directly from raw PyMuPDF data for maximum performance
"""

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QCursor
from typing import List, Dict, Optional, Tuple
import time


class RawLinkOverlay(QLabel):
    """Lightweight overlay widget for raw links"""

    # Signals
    rawLinkClicked = pyqtSignal(dict, int, int)  # raw_link, page_index, link_index
    rawLinkHovered = pyqtSignal(dict, int, int)  # raw_link, page_index, link_index

    def __init__(self, raw_link: dict, page_index: int, link_index: int, parent=None):
        super().__init__(parent)

        self.raw_link = raw_link
        self.page_index = page_index
        self.link_index = link_index

        # Setup appearance
        self._setup_appearance()

        # Enable mouse tracking
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _setup_appearance(self):
        """Setup visual appearance based on raw link type"""
        try:
            # Get basic link type from raw data
            link_kind = self.raw_link.get('kind', 0)

            # Choose style based on link type
            if link_kind == 1:  # GOTO
                style = """
                    QLabel {
                        border: 2px dashed #009900;
                        background-color: rgba(0, 153, 0, 20);
                    }
                    QLabel:hover {
                        border: 2px solid #009900;
                        background-color: rgba(0, 153, 0, 40);
                    }
                """
            elif link_kind == 2:  # URI
                style = """
                    QLabel {
                        border: 2px dashed #0066cc;
                        background-color: rgba(0, 102, 204, 20);
                    }
                    QLabel:hover {
                        border: 2px solid #0066cc;
                        background-color: rgba(0, 102, 204, 40);
                    }
                """
            else:  # Other types
                style = """
                    QLabel {
                        border: 2px dashed #9900cc;
                        background-color: rgba(153, 0, 204, 20);
                    }
                    QLabel:hover {
                        border: 2px solid #9900cc;
                        background-color: rgba(153, 0, 204, 40);
                    }
                """

            self.setStyleSheet(style)

            # Make transparent background
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        except Exception as e:
            print(f"❌ Error setting overlay appearance: {e}")

    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.rawLinkClicked.emit(self.raw_link, self.page_index, self.link_index)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter"""
        self.rawLinkHovered.emit(self.raw_link, self.page_index, self.link_index)
        super().enterEvent(event)

    def _setup_appearance(self):
        """Setup visual appearance - cursor only, no hover effects"""
        try:
            # Just set the cursor, no visual styling
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            # Make the overlay invisible but still capture mouse events
            self.setStyleSheet("QLabel { background-color: transparent; border: none; }")

            # Enable mouse tracking
            self.setMouseTracking(True)

        except Exception as e:
            print(f"❌ Error setting overlay appearance: {e}")

    # Also simplify the mouse events:

    def enterEvent(self, event):
        """Handle mouse enter - signal only"""
        self.rawLinkHovered.emit(self.raw_link, self.page_index, self.link_index)
        # Don't call super() to avoid any default hover handling

    def leaveEvent(self, event):
        """Handle mouse leave - no action needed"""
        pass

class RawLinkOverlayManager(QObject):
    """
    Ultra-fast overlay manager that works directly with raw PyMuPDF data
    No PDFLink objects created during rendering for maximum performance
    """

    # Signals
    rawLinkClicked = pyqtSignal(dict, int, int)  # raw_link, page_index, link_index
    rawLinkHovered = pyqtSignal(dict, int, int)  # raw_link, page_index, link_index
    overlaysCreated = pyqtSignal(int, int)  # page_index, overlay_count

    def __init__(self, canvas_widget, raw_link_manager, parent=None):
        super().__init__(parent)

        self.canvas_widget = canvas_widget
        self.raw_link_manager = raw_link_manager

        # State tracking
        self.current_page = 0
        self.current_zoom = 1.0
        self.visible_pages = []

        # Overlay management
        self.active_overlays = {}  # page_index -> List[RawLinkOverlay]
        self.overlay_pool = []  # Reusable overlay widgets
        self.max_pool_size = 50  # Maximum pooled overlays

        # Performance settings
        self.update_delay = 50  # ms delay for batch updates (reduced from 100)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._perform_delayed_update)
        self.update_timer.setSingleShot(True)

        # Visual settings
        self.show_overlays = True

        # Performance tracking
        self.overlay_creation_times = []

        # Connect raw link manager signals
        self._connect_raw_link_manager()

        print("🚀 RawLinkOverlayManager initialized (ultra-fast mode)")

    def _connect_raw_link_manager(self):
        """Connect signals from raw link manager"""
        if self.raw_link_manager:
            self.raw_link_manager.rawLinksExtracted.connect(self._on_raw_links_extracted)

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
            start_time = time.perf_counter()

            # Clear existing overlays
            self._clear_all_overlays()

            # Create overlays for visible pages
            total_overlays = 0
            for page_index in self.visible_pages:
                overlays_created = self._create_page_overlays_raw(page_index)
                total_overlays += overlays_created

            elapsed = time.perf_counter() - start_time
            self.overlay_creation_times.append(elapsed)

            print(f"🎨 Updated {total_overlays} overlays for pages {self.visible_pages} in {elapsed * 1000:.2f}ms")

        except Exception as e:
            print(f"❌ Error updating raw link overlays: {e}")

    def _create_page_overlays_raw(self, page_index: int) -> int:
        """Create overlay widgets directly from raw link data"""

        # Get raw links (ultra-fast, cached)
        raw_links = self.raw_link_manager.get_raw_page_links(page_index)

        if not raw_links:
            return 0

        start_time = time.perf_counter()

        # Calculate page offset on canvas
        page_offset = self._get_page_offset(page_index)
        if page_offset is None:
            return 0

        # Create overlays for each raw link
        page_overlays = []
        overlays_created = 0

        for link_index, raw_link in enumerate(raw_links):
            overlay = self._create_raw_overlay(raw_link, page_index, link_index, page_offset)
            if overlay:
                page_overlays.append(overlay)
                overlays_created += 1

        # Store overlays for this page
        self.active_overlays[page_index] = page_overlays

        elapsed = time.perf_counter() - start_time

        print(f"🎨 Created {overlays_created} raw overlays for page {page_index + 1} in {elapsed * 1000:.2f}ms")

        # Emit signal
        self.overlaysCreated.emit(page_index, overlays_created)

        return overlays_created

    def _create_raw_overlay(self, raw_link: dict, page_index: int, link_index: int, page_offset: QPointF) -> Optional[
        RawLinkOverlay]:
        """Create overlay directly from raw link data - ultra-fast"""

        try:
            # Extract bounds directly from raw data (no bounds checking for speed)
            link_rect = raw_link['from']  # Direct access

            # Calculate overlay position
            x = link_rect.x0 * self.current_zoom + page_offset.x()
            y = link_rect.y0 * self.current_zoom + page_offset.y()
            w = link_rect.width * self.current_zoom
            h = link_rect.height * self.current_zoom

            # Get overlay from pool or create new
            overlay = self._get_or_create_raw_overlay(raw_link, page_index, link_index)
            if not overlay:
                return None

            # Set position and show
            overlay.setGeometry(int(x), int(y), int(w), int(h))
            overlay.show()
            overlay.raise_()  # Bring to front

            return overlay

        except Exception as e:
            print(f"❌ Error creating raw overlay: {e}")
            return None

    def _get_or_create_raw_overlay(self, raw_link: dict, page_index: int, link_index: int) -> Optional[RawLinkOverlay]:
        """Get overlay from pool or create new one"""
        try:
            # Try to reuse from pool
            if self.overlay_pool:
                overlay = self.overlay_pool.pop()
                # Update overlay data
                overlay.raw_link = raw_link
                overlay.page_index = page_index
                overlay.link_index = link_index
                overlay._setup_appearance()
            else:
                # Create new overlay
                overlay = RawLinkOverlay(raw_link, page_index, link_index, self.canvas_widget)

                # Connect signals
                overlay.rawLinkClicked.connect(self._on_raw_overlay_clicked)
                overlay.rawLinkHovered.connect(self._on_raw_overlay_hovered)

            return overlay

        except Exception as e:
            print(f"❌ Error getting/creating raw overlay: {e}")
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

    def _on_raw_links_extracted(self, page_index: int, raw_links: List[dict]):
        """Handle raw links extracted signal"""
        if page_index in self.visible_pages:
            # Recreate overlays for this page
            self._create_page_overlays_raw(page_index)

    def _on_raw_overlay_clicked(self, raw_link: dict, page_index: int, link_index: int):
        """Handle raw overlay click"""
        self.rawLinkClicked.emit(raw_link, page_index, link_index)

        # Also trigger raw link manager's handler (this does the parsing)
        if self.raw_link_manager:
            self.raw_link_manager.handle_raw_link_click(raw_link, page_index, link_index)

    def _on_raw_overlay_hovered(self, raw_link: dict, page_index: int, link_index: int):
        """Handle raw overlay hover"""
        self.rawLinkHovered.emit(raw_link, page_index, link_index)

    def set_overlay_visibility(self, visible: bool):
        """Show or hide all overlays"""
        self.show_overlays = visible

        if visible:
            self.update_page_links(self.current_page, self.current_zoom, self.visible_pages)
        else:
            self._clear_all_overlays()

    def get_raw_links_at_position(self, canvas_pos: QPointF) -> List[Tuple[dict, int, int]]:
        """Get all raw links at a specific canvas position"""
        found_links = []

        for overlays in self.active_overlays.values():
            for overlay in overlays:
                if overlay.geometry().contains(canvas_pos.toPoint()):
                    found_links.append((overlay.raw_link, overlay.page_index, overlay.link_index))

        return found_links

    def get_overlay_stats(self) -> Dict[str, int]:
        """Get statistics about current overlays"""
        total_overlays = sum(len(overlays) for overlays in self.active_overlays.values())

        stats = {
            'active_pages': len(self.active_overlays),
            'total_overlays': total_overlays,
            'pooled_overlays': len(self.overlay_pool),
            'current_page': self.current_page,
            'visible_pages_count': len(self.visible_pages)
        }

        # Add performance stats
        if self.overlay_creation_times:
            stats['avg_creation_time_ms'] = sum(self.overlay_creation_times) * 1000 / len(self.overlay_creation_times)
            stats['total_creation_time_ms'] = sum(self.overlay_creation_times) * 1000

        return stats

    def print_performance_report(self):
        """Print overlay performance report"""
        stats = self.get_overlay_stats()

        print("\n🎨 Raw Overlay Manager Performance Report:")
        print("=" * 50)
        print(f"Active pages: {stats['active_pages']}")
        print(f"Total overlays: {stats['total_overlays']}")
        print(f"Pooled overlays: {stats['pooled_overlays']}")

        if 'avg_creation_time_ms' in stats:
            print(f"Avg creation time: {stats['avg_creation_time_ms']:.2f}ms")
            print(f"Total creation time: {stats['total_creation_time_ms']:.2f}ms")

        if stats['total_overlays'] > 0 and 'total_creation_time_ms' in stats:
            time_per_overlay = stats['total_creation_time_ms'] / stats['total_overlays']
            print(f"Time per overlay: {time_per_overlay:.3f}ms")

        print("=" * 50)


class RawLinkIntegration(QObject):
    """
    High-level integration class for raw link functionality
    Provides a unified interface compatible with existing code
    """

    # Signals for compatibility with existing code
    linkNavigationRequested = pyqtSignal(int, float, float)  # page, x, y
    externalLinkRequested = pyqtSignal(str)  # url
    linkStatusChanged = pyqtSignal(str)  # status message
    linkExtractionCompleted = pyqtSignal(int, list)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Components
        from .a_raw_link_manager import RawLinkManager
        self.link_manager = RawLinkManager(self)
        self.overlay_manager = None  # Will be set when canvas is available

        # State
        self.canvas_widget = None
        self.current_document = None

        # Connect link manager signals
        self._connect_link_manager()

        print("🚀 RawLinkIntegration initialized (ultra-fast mode)")

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

        # Create raw overlay manager
        self.overlay_manager = RawLinkOverlayManager(canvas_widget, self.link_manager, self)

        # Connect overlay manager signals
        self.overlay_manager.rawLinkClicked.connect(self._on_raw_link_clicked)
        self.overlay_manager.rawLinkHovered.connect(self._on_raw_link_hovered)

        print("✅ Raw link integration with canvas complete")

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

    def _on_raw_link_clicked(self, raw_link: dict, page_index: int, link_index: int):
        """Handle raw link click from overlay"""
        try:
            # Get basic description for status
            link_kind = raw_link.get('kind', 0)
            if link_kind == 1:  # GOTO
                desc = f"Internal link (page {raw_link.get('page', 0) + 1})"
            elif link_kind == 2:  # URI
                desc = f"External URL: {raw_link.get('uri', '')[:30]}..."
            else:
                desc = f"Link (type {link_kind})"

            self.linkStatusChanged.emit(f"Clicked: {desc}")
        except:
            self.linkStatusChanged.emit("Link clicked")

    def _on_raw_link_hovered(self, raw_link: dict, page_index: int, link_index: int):
        """Handle raw link hover from overlay"""
        try:
            # Get basic description for status
            link_kind = raw_link.get('kind', 0)
            if link_kind == 1:  # GOTO
                desc = f"Go to page {raw_link.get('page', 0) + 1}"
            elif link_kind == 2:  # URI
                desc = f"External: {raw_link.get('uri', '')[:40]}..."
            else:
                desc = f"Link (type {link_kind})"

            self.linkStatusChanged.emit(f"Hover: {desc}")
        except:
            self.linkStatusChanged.emit("Link")

    def set_links_visible(self, visible: bool):
        """Show or hide link overlays"""
        if self.overlay_manager:
            self.overlay_manager.set_overlay_visibility(visible)

    def get_page_links(self, page_index: int) -> List[dict]:
        """Get raw links for a specific page"""
        return self.link_manager.get_raw_page_links(page_index)

    def print_performance_report(self):
        """Print comprehensive performance report"""
        print("\n🚀 Raw Link System Performance Report:")
        print("=" * 60)

        if self.link_manager:
            self.link_manager.print_performance_report()

        if self.overlay_manager:
            self.overlay_manager.print_performance_report()


if __name__ == '__main__':
    print("RawLinkOverlayManager - Use as module import")