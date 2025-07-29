"""
Canvas Widget - Based on Working Reference
File: src/ui/a_canvas_widget.py

Restored to working state but with timer cancellation fix
"""

import time
from collections import deque
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPainter, QPixmap, QPen, QBrush
from typing import Optional, List, Tuple, Set


class CanvasWidget(QWidget):
    """Canvas widget for rendering PDF pages - based on working reference"""

    # Signals
    pageChanged = pyqtSignal(int)  # Emitted when current page changes
    zoomChanged = pyqtSignal(float)  # Emitted when zoom level changes
    mousePositionChanged = pyqtSignal(int, float, float)  # page, doc_x, doc_y

    def __init__(self, parent=None):
        """Initialize Canvas Widget - based on working reference"""
        super().__init__(parent)

        # ========================================
        # CORE COMPONENTS
        # ========================================
        self.document = None
        self.layout_manager = None
        self.zoom_level = 1.0
        self.current_page = 0

        # ========================================
        # RENDERING STATE
        # ========================================
        self.rendered_pages = {}  # Cache for rendered page pixmaps
        self.visible_pages = []  # Currently visible page indices
        self.viewport_rect = QRectF()

        # ========================================
        # PERFORMANCE OPTIMIZATION (FIXED TIMER)
        # ========================================
        # Queue-based render timer (NO CANCELLATION)
        self.pending_render_pages = set()  # Pages queued for rendering
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._process_render_queue)
        self.render_timer.setSingleShot(True)
        self.needs_render = False

        # Paint loop prevention
        self.is_painting = False
        self.paint_count = 0
        self._last_paint_time = 0.0

        # ========================================
        # CACHE MANAGEMENT
        # ========================================
        self._cache_cleanup_timer = QTimer()
        self._cache_cleanup_timer.timeout.connect(self._periodic_cache_cleanup)
        self._cache_cleanup_timer.start(10000)  # Cleanup every 10 seconds

        # Cache size limits
        self._max_cached_pages = 10  # Maximum pages to keep in cache
        self._cache_adjacent_pages = 2  # Number of adjacent pages to cache

        # ========================================
        # UI SETTINGS AND STYLING
        # ========================================
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #2b2b2b;")

        # ========================================
        # MOUSE AND INTERACTION STATE
        # ========================================
        self._mouse_pressed = False
        self._last_mouse_position = None
        self._drag_start_position = None

        print("🎨 Canvas widget initialized")

    # ========================================
    # DOCUMENT MANAGEMENT
    # ========================================

    @pyqtSlot(object)
    def on_document_loaded(self, document):
        """Handle document loaded signal from main window"""
        print(f"📄 Canvas: Document loaded with {document.get_page_count()} pages")
        self._load_document(document)

    @pyqtSlot()
    def on_document_closed(self):
        """Handle document closed signal from main window"""
        print("❌ Canvas: Document closed")
        self._clear_document()

    def _load_document(self, document):
        """Internal method to load document into canvas"""
        print("🔄 Loading document into canvas...")
        self.document = document

        if document:
            try:
                # Use external layout manager (was working correctly)
                from src.ui.a_layout_manager import LayoutManager
                print("📐 Creating layout manager...")
                self.layout_manager = LayoutManager(document, self.zoom_level)

                # Get canvas size info
                width, height = self.layout_manager.get_canvas_size()
                print(f"📏 Canvas size calculated: {width}x{height}")

                self._update_canvas_size()
                self.current_page = 0
                self.pageChanged.emit(0)

                # Set initial visible pages
                print("🔍 Setting initial visible pages...")
                visible_pages = [0]  # Start with just first page
                if self.document.get_page_count() > 1:
                    visible_pages.append(1)

                print(f"👁️ Initial visible pages: {visible_pages}")
                self.visible_pages = visible_pages
                self.schedule_render()

                print("✅ Document loaded successfully into canvas")
            except Exception as e:
                print(f"❌ Error loading document into canvas: {e}")
                import traceback
                traceback.print_exc()
        else:
            self._clear_document()

    def _clear_document(self):
        """Internal method to clear document from canvas"""
        print("🧹 Clearing document from canvas...")
        self.document = None
        self.layout_manager = None
        self.rendered_pages.clear()
        self.visible_pages.clear()
        self.current_page = 0
        self.update()

    def load_pdf(self, file_path: str) -> bool:
        """Compatibility method for old main window - loads via PDFDocument"""
        try:
            from src.ui.a_pdf_document import PDFDocument

            print(f"🔧 Canvas loading PDF: {file_path}")

            # Create and set document
            document = PDFDocument(file_path)
            self.set_document(document)

            # Create external layout manager (was working)
            if not self.layout_manager:
                from src.ui.a_layout_manager import LayoutManager
                print("📐 Creating external layout manager...")
                layout_manager = LayoutManager(document, self.zoom_level)
                self.set_layout_manager(layout_manager)
            else:
                self.layout_manager.set_document(document)
                self.layout_manager.set_zoom(self.zoom_level)

            # Update canvas size
            self._update_canvas_size()

            # Initial render of first page
            if document.get_page_count() > 0:
                self.set_visible_pages_optimized([0], QRectF(0, 0, 400, 300))

            print(f"✅ Canvas loaded PDF: {document.get_page_count()} pages")
            return True

        except Exception as e:
            print(f"❌ Canvas PDF loading error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def set_document(self, document):
        """Set the PDF document"""
        self.document = document
        self.rendered_pages.clear()  # Clear cache when document changes
        self.current_page = 0
        print(f"📄 Document set: {document.get_page_count()} pages" if document else "📄 Document cleared")

    def set_layout_manager(self, layout_manager):
        """Set the layout manager"""
        self.layout_manager = layout_manager
        self._update_canvas_size()
        print("📐 Layout manager set")

    # ========================================
    # SMART RENDERING WITH QUEUE (FIXED)
    # ========================================

    def set_visible_pages_optimized(self, page_indices: List[int], viewport_rect: QRectF):
        """Smart rendering with inline optimization logic - FIXED timer"""
        if self.is_painting:
            print("⏸️ Skipping page update - currently painting")
            return

        # INLINE SMART LOGIC (no external optimizer):
        pages_to_render = []
        cached_pages = []

        for page_idx in page_indices:
            if page_idx not in self.rendered_pages:
                pages_to_render.append(page_idx)
            else:
                cached_pages.append(page_idx)

        # Update state immediately
        self.visible_pages = page_indices
        self.viewport_rect = viewport_rect

        # Log smart optimization results
        if pages_to_render and cached_pages:
            print(f"🎨 Smart render: NEW {pages_to_render}, CACHED {cached_pages}")
        elif pages_to_render:
            print(f"🎨 Smart render: NEW {pages_to_render}")
        elif cached_pages:
            print(f"🎨 Smart render: ALL CACHED {cached_pages}")

        # Queue pages for rendering (FIXED - NO timer cancellation!)
        if pages_to_render:
            self._queue_render_pages(pages_to_render)

        # Update current page tracking
        if page_indices and self.current_page not in page_indices:
            # Only change if current page is far from visible range
            if not any(abs(self.current_page - p) <= 1 for p in page_indices):
                new_page = page_indices[0]
                if new_page != self.current_page:
                    self.current_page = new_page
                    self.pageChanged.emit(new_page)

        # Trigger immediate paint (shows cached pages instantly)
        self.update()

    def _queue_render_pages(self, pages_to_render: List[int]):
        """Queue pages for rendering - FIXED: NEVER cancel existing timer"""

        # Add pages to queue
        self.pending_render_pages.update(pages_to_render)
        print(f"📥 Queued pages: {pages_to_render} (queue size: {len(self.pending_render_pages)})")

        # Start timer ONLY if not already running (FIXED - no cancellation!)
        if not self.render_timer.isActive():
            print("⏰ Starting render timer")
            self.render_timer.start(50)  # 50ms processing interval

    def _process_render_queue(self):
        """Process render queue - called every 50ms when timer fires"""

        if not self.pending_render_pages:
            print("📭 Render queue empty")
            return

        if self.is_painting:
            print("⏸️ Skipping queue processing - currently painting")
            return

        # Get all pending pages and clear queue
        pages_to_render = list(self.pending_render_pages)
        self.pending_render_pages.clear()

        print(f"🎨 Processing render queue: {pages_to_render}")

        # Render pages that still need rendering
        rendered_count = 0
        for page_idx in pages_to_render:
            if page_idx not in self.rendered_pages:
                self._render_page(page_idx)
                rendered_count += 1

        # Basic cache cleanup
        self._periodic_cache_cleanup()

        print(f"✅ Rendered {rendered_count}/{len(pages_to_render)} pages")

        # Trigger repaint to show newly rendered content
        self.update()

    # ========================================
    # BACKWARD COMPATIBILITY (FROM REFERENCE)
    # ========================================

    def schedule_render(self):
        """Schedule a render update (with debouncing) - for compatibility"""
        if self.is_painting:  # Don't schedule during painting
            return

        print("⏰ Scheduling render...")
        self.needs_render = True

        # Use queue system instead of old timer cancellation
        if self.visible_pages:
            self._queue_render_pages(self.visible_pages)

    def set_visible_pages(self, page_indices: List[int], viewport_rect: QRectF):
        """Backward compatibility method - redirects to optimized version"""
        print(f"👁️ Setting visible pages (compat): {page_indices}")
        self.set_visible_pages_optimized(page_indices, viewport_rect)

    # ========================================
    # PAGE RENDERING
    # ========================================

    def _render_page(self, page_index: int):
        """Render a single page to pixmap"""
        try:
            if not self.document:
                return

            print(f"🖼️ Rendering page {page_index} at zoom {self.zoom_level:.2f}")

            # Calculate render DPI based on zoom (from reference)
            base_dpi = 72  # PDF native DPI
            render_dpi = int(base_dpi * self.zoom_level)

            print(f"📐 Using render DPI: {render_dpi} (zoom: {self.zoom_level:.2f})")

            # Render page to pixmap (from reference)
            pixmap = self.document.render_page(page_index, 1.0, render_dpi)  # Use zoom=1.0, control via DPI

            if not pixmap.isNull():
                self.rendered_pages[page_index] = pixmap
                print(f"✅ Page {page_index} rendered: {pixmap.width()}x{pixmap.height()}")
            else:
                print(f"❌ Failed to render page {page_index}")

        except Exception as e:
            print(f"❌ Error rendering page {page_index}: {e}")
            import traceback
            traceback.print_exc()

    def _periodic_cache_cleanup(self):
        """Periodic cache cleanup to prevent memory bloat - from reference"""
        try:
            if not hasattr(self, 'rendered_pages'):
                return

            initial_cache_size = len(self.rendered_pages)

            if initial_cache_size > self._max_cached_pages:
                # Keep only the most recently used pages
                pages_to_keep = set(self.visible_pages)

                # Add adjacent pages
                for page_idx in self.visible_pages:
                    for offset in range(-self._cache_adjacent_pages, self._cache_adjacent_pages + 1):
                        adjacent_page = page_idx + offset
                        if adjacent_page >= 0:  # Will check upper bound when we have document
                            pages_to_keep.add(adjacent_page)

                # Remove excess pages
                pages_to_remove = []
                for page_idx in self.rendered_pages.keys():
                    if page_idx not in pages_to_keep:
                        pages_to_remove.append(page_idx)

                # Remove oldest pages first (simple LRU)
                pages_to_remove.sort()
                excess_count = initial_cache_size - self._max_cached_pages
                for page_idx in pages_to_remove[:excess_count]:
                    del self.rendered_pages[page_idx]

                if pages_to_remove:
                    print(f"🧹 Periodic cache cleanup: Removed {len(pages_to_remove[:excess_count])} pages")

        except Exception as e:
            print(f"❌ Cache cleanup error: {e}")

    # ========================================
    # PAINT EVENT (FROM REFERENCE)
    # ========================================

    def paintEvent(self, event):
        """Paint the visible pages - with loop prevention and debugging (from reference)"""

        # CRITICAL: Prevent infinite paint loops
        if self.is_painting:
            print("🔄 Paint event blocked - already painting")
            return

        self.is_painting = True
        self.paint_count += 1

        print(f"🎨 Paint event #{self.paint_count}. Visible pages: {self.visible_pages}")

        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Paint background
            painter.fillRect(self.rect(), QBrush(Qt.GlobalColor.darkGray))

            if not self.document or not self.layout_manager:
                self._paint_no_document(painter)
                return

            # Paint visible pages
            pages_painted = 0
            for page_index in self.visible_pages:
                if self._paint_page(painter, page_index):
                    pages_painted += 1

            print(f"🎨 Paint complete. Pages painted: {pages_painted}")

        finally:
            # ALWAYS reset painting flag
            self.is_painting = False

    def _paint_no_document(self, painter):
        """Paint message when no document is loaded (from reference)"""
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No document loaded")
        print("🎨 Painted 'no document' message")

    def _paint_page(self, painter, page_index: int) -> bool:
        """Paint a single page - returns True if painted (from reference)"""
        page_rect = self.layout_manager.get_page_rect(page_index)
        if not page_rect:
            print(f"❌ No page rect for page {page_index}")
            return False

        print(f"🎨 Painting page {page_index} at rect {page_rect}")

        # Draw page background
        painter.fillRect(page_rect, QBrush(Qt.GlobalColor.white))

        # Draw page border
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawRect(page_rect)

        # Draw rendered content if available
        if page_index in self.rendered_pages:
            pixmap = self.rendered_pages[page_index]
            print(f"🖼️ Drawing pixmap for page {page_index}: {pixmap.width()}x{pixmap.height()}")

            # Scale pixmap to fit page rect exactly (from reference)
            painter.drawPixmap(page_rect.toRect(), pixmap)
            print(f"✅ Pixmap scaled and drawn for page {page_index}")
        else:
            # Draw loading indicator
            painter.setPen(QPen(Qt.GlobalColor.gray))
            painter.drawText(page_rect, Qt.AlignmentFlag.AlignCenter, f"Loading page {page_index + 1}...")
            print(f"⏳ Loading indicator drawn for page {page_index}")

        return True

    # ========================================
    # ZOOM CONTROLS (FROM REFERENCE)
    # ========================================

    def set_zoom(self, zoom_level: float, maintain_position: bool = True, goto_current_page: bool = False,
                 goto_page_top_with_margin: bool = False):
        """Set zoom level with position control (from reference)"""
        zoom_level = max(0.1, min(5.0, zoom_level))

        if abs(self.zoom_level - zoom_level) > 0.01:
            print(f"🔍 Setting zoom to {zoom_level:.2f}")

            # Clear old cache when zoom changes (different DPI needed)
            self.rendered_pages.clear()

            # Update zoom
            old_zoom = self.zoom_level
            self.zoom_level = zoom_level

            # Update layout manager
            if self.layout_manager:
                self.layout_manager.set_zoom(zoom_level)
                self._update_canvas_size()

            # Re-queue visible pages for rendering at new zoom
            if self.visible_pages:
                self._queue_render_pages(self.visible_pages)

            self.zoomChanged.emit(zoom_level)

    def _get_scroll_area(self):
        """Get the scroll area containing this canvas (from reference)"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'verticalScrollBar') and hasattr(parent, 'viewport'):
                return parent
            parent = parent.parent()
        return None

    def zoom_in(self, factor: float = 1.25):
        """Zoom in by factor"""
        self.set_zoom(self.zoom_level * factor)

    def zoom_out(self, factor: float = 1.25):
        """Zoom out by factor"""
        self.set_zoom(self.zoom_level / factor)

    def fit_to_width(self, available_width: int):
        """Fit page to available width"""
        if not self.document:
            return

        page_size = self.document.get_page_size(0)
        zoom = (available_width - 40) / page_size.width()  # 40px margin
        self.set_zoom(zoom)

    def fit_to_page(self, available_width: int, available_height: int):
        """Fit entire page to window"""
        if not self.document:
            return

        page_size = self.document.get_page_size(0)
        zoom_w = (available_width - 40) / page_size.width()
        zoom_h = (available_height - 40) / page_size.height()
        zoom = min(zoom_w, zoom_h)
        self.set_zoom(zoom, maintain_position=False)

    # ========================================
    # LAYOUT INTEGRATION (FROM REFERENCE)
    # ========================================

    def _update_canvas_size(self):
        """Update canvas size based on layout (from reference)"""
        if self.layout_manager:
            width, height = self.layout_manager.get_canvas_size()
            print(f"📏 Updating canvas size to: {width}x{height}")
            self.resize(max(width, 400), max(height, 300))
            print(f"📏 Canvas widget size: {self.size()}")

    def get_visible_pages_in_viewport(self, viewport_rect: QRectF) -> List[int]:
        """Get list of page indices visible in viewport (from reference)"""
        if self.layout_manager:
            visible = self.layout_manager.get_visible_pages(viewport_rect)
            print(f"🔍 Visible pages in viewport {viewport_rect}: {visible}")
            return visible
        return []

    def get_page_at_position(self, y_position: float) -> int:
        """Get page index at Y position (from reference)"""
        if self.layout_manager:
            return self.layout_manager.get_page_at_position(y_position)
        return 0

    def get_page_y_position(self, page_index: int) -> float:
        """Get Y position of page start (from reference)"""
        if self.layout_manager:
            return self.layout_manager.get_page_y_position(page_index)
        return 0.0

    def get_current_page_from_scroll(self, scroll_y: float) -> int:
        """Get current page based on scroll position (from reference)"""
        """Get current page based on scroll position - FIXED"""
        viewport_height = self.scroll_area.viewport().height()
        center_y = scroll_y + (viewport_height / 2)
        return self.get_page_at_position(center_y)

    def get_canvas_size(self) -> tuple:
        """Get total canvas size needed (from reference)"""
        if self.layout_manager:
            size = self.layout_manager.get_canvas_size()
            print(f"📏 Canvas size: {size}")
            return size
        return (400, 300)

    # ========================================
    # COORDINATE CONVERSION (FROM REFERENCE)
    # ========================================

    def document_to_canvas_coordinates(self, page_index: int, doc_x: float, doc_y: float) -> tuple:
        """Convert document coordinates to canvas coordinates (from reference)"""
        if self.layout_manager:
            from PyQt6.QtCore import QPointF
            doc_point = QPointF(doc_x, doc_y)
            canvas_point = self.layout_manager.document_to_canvas(page_index, doc_point)
            return (canvas_point.x(), canvas_point.y())
        return (0, 0)

    def canvas_to_document_coordinates(self, page_index: int, canvas_x: float, canvas_y: float) -> tuple:
        """Convert canvas coordinates to document coordinates (from reference)"""
        if self.layout_manager:
            from PyQt6.QtCore import QPointF
            canvas_point = QPointF(canvas_x, canvas_y)
            doc_point = self.layout_manager.canvas_to_document(page_index, canvas_point)
            return (doc_point.x(), doc_point.y())
        return (0, 0)

    def get_page_at_canvas_position(self, canvas_x: float, canvas_y: float) -> Optional[int]:
        """Get page index at canvas position (from reference)"""
        if not self.layout_manager:
            return None

        for i in range(self.document.get_page_count() if self.document else 0):
            page_rect = self.layout_manager.get_page_rect(i)
            if page_rect and page_rect.contains(canvas_x, canvas_y):
                return i
        return None

    # ========================================
    # MOUSE EVENTS (FROM REFERENCE)
    # ========================================

    def mousePressEvent(self, event):
        """Handle mouse press events (from reference)"""
        if event.button() == Qt.MouseButton.LeftButton and self.layout_manager:
            # Determine which page was clicked and document coordinates
            page_index = self.get_page_at_canvas_position(event.position().x(), event.position().y())

            if page_index is not None:
                doc_x, doc_y = self.canvas_to_document_coordinates(
                    page_index, event.position().x(), event.position().y()
                )

                # Emit signal with page and document coordinates
                self.mousePositionChanged.emit(page_index, doc_x, doc_y)
                print(f"🖱️ Clicked on page {page_index + 1} at document coords ({doc_x:.1f}, {doc_y:.1f})")

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events (from reference)"""
        if self.layout_manager:
            page_index = self.get_page_at_canvas_position(event.position().x(), event.position().y())
            if page_index is not None:
                doc_x, doc_y = self.canvas_to_document_coordinates(
                    page_index, event.position().x(), event.position().y()
                )
                # Could emit mouse move signal here if needed

        super().mouseMoveEvent(event)