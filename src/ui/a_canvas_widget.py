from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPainter, QPixmap, QPen, QBrush
from typing import Optional, List


class CanvasWidget(QWidget):
    """Canvas widget for rendering PDF pages - fixed paint loop issue"""

    # Signals
    pageChanged = pyqtSignal(int)  # Emitted when current page changes
    zoomChanged = pyqtSignal(float)  # Emitted when zoom level changes
    mousePositionChanged = pyqtSignal(int, float, float)  # page, doc_x, doc_y

    def __init__(self, parent=None):
        super().__init__(parent)

        # Core components
        self.document = None
        self.layout_manager = None
        self.zoom_level = 1.0
        self.current_page = 0

        # Rendering state
        self.rendered_pages = {}  # Cache for rendered page pixmaps
        self.visible_pages = []  # Currently visible page indices
        self.viewport_rect = QRectF()

        # Performance optimization
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._perform_render)
        self.render_timer.setSingleShot(True)
        self.needs_render = False

        # CRITICAL: Prevent infinite paint loops
        self.is_painting = False
        self.paint_count = 0

        # UI settings
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

        # Background
        self.setStyleSheet("background-color: #2b2b2b;")

        print("🎨 Canvas widget initialized")

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
                from a_layout_manager import LayoutManager
                print("📐 Creating layout manager...")
                self.layout_manager = LayoutManager(document, self.zoom_level)

                # Get canvas size info
                width, height = self.layout_manager.get_canvas_size()
                print(f"📏 Canvas size calculated: {width}x{height}")

                self._update_canvas_size()
                self.current_page = 0
                self.pageChanged.emit(0)
                self._document_loaded = True

                # Set initial visible pages - simplified
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
        self._document_loaded = False
        self.update()

    def set_zoom(self, zoom_level: float, maintain_position: bool = True, goto_current_page: bool = False,
                 goto_page_top_with_margin: bool = False):
        """
        Set zoom level with position control

        Args:
            zoom_level: New zoom level (0.1 to 5.0)
            maintain_position: If True, maintain current scroll position proportionally
            goto_current_page: If True, scroll to current page top after zoom (for fit operations)
            goto_page_top_with_margin: If True, go to page top with proper inter-page margin
        """
        zoom_level = max(0.1, min(5.0, zoom_level))

        if abs(self.zoom_level - zoom_level) > 0.01:
            print(
                f"🔍 Setting zoom to {zoom_level:.2f}, maintain_position={maintain_position}, goto_current_page={goto_current_page}, goto_page_top_with_margin={goto_page_top_with_margin}")

            # STEP 1: Stop timer to prevent conflicts
            self.render_timer.stop()
            self.needs_render = False

            # STEP 2: Capture current state (only if maintaining position)
            scroll_area = self._get_scroll_area()
            x_ratio, y_ratio = 0, 0
            viewport_width, viewport_height = 0, 0

            if maintain_position and not goto_current_page and not goto_page_top_with_margin and scroll_area and self.layout_manager:
                # Current canvas dimensions
                old_canvas_width, old_canvas_height = self.layout_manager.get_canvas_size()

                # Current scroll position
                current_scroll_x = scroll_area.horizontalScrollBar().value()
                current_scroll_y = scroll_area.verticalScrollBar().value()

                # Current viewport size
                viewport_width = scroll_area.viewport().width()
                viewport_height = scroll_area.viewport().height()

                # Calculate proportional position within canvas
                x_ratio = current_scroll_x / max(old_canvas_width, viewport_width) if old_canvas_width > 0 else 0
                y_ratio = current_scroll_y / max(old_canvas_height, viewport_height) if old_canvas_height > 0 else 0

                print(f"📐 Saving position ratios: x={x_ratio:.3f}, y={y_ratio:.3f}")

            # STEP 3: Update zoom level and layout
            self.zoom_level = zoom_level

            if self.layout_manager:
                self.layout_manager.set_zoom(zoom_level)
                self._update_canvas_size()

            # STEP 4: Apply position strategy
            if scroll_area and self.layout_manager:
                if goto_page_top_with_margin:
                    # Show page at top of display area WITH the inter-page gap visible
                    current_page = getattr(self, 'current_page', 0)

                    if current_page == 0:
                        # For first page, scroll to absolute top (Y=0) to show the top margin + page
                        scroll_y = 0
                        print(f"📐 Fit page: First page - scrolling to absolute top (0)")
                    else:
                        # For other pages, get the page position and show gap above it
                        page_y = self.layout_manager.get_page_y_position(current_page)
                        inter_page_margin = getattr(self.layout_manager, 'PAGE_SPACING_VERTICAL', 15)
                        scroll_y = max(0, page_y - inter_page_margin)
                        print(
                            f"📐 Fit page: Page {current_page} - page_y={page_y}, gap={inter_page_margin}, scroll_to={scroll_y}")

                    scroll_area.horizontalScrollBar().setValue(0)  # Reset horizontal
                    scroll_area.verticalScrollBar().setValue(int(scroll_y))

                elif goto_current_page:
                    # Go to current page top (original behavior)
                    current_page = getattr(self, 'current_page', 0)
                    page_y = self.layout_manager.get_page_y_position(current_page)

                    print(f"📐 Going to current page {current_page} at y={page_y}")
                    scroll_area.horizontalScrollBar().setValue(0)  # Reset horizontal
                    scroll_area.verticalScrollBar().setValue(int(page_y))

                elif maintain_position:
                    # Maintain proportional position
                    new_canvas_width, new_canvas_height = self.layout_manager.get_canvas_size()

                    # Apply same ratios to new canvas size
                    effective_canvas_width = max(new_canvas_width, viewport_width)
                    effective_canvas_height = max(new_canvas_height, viewport_height)

                    new_scroll_x = x_ratio * effective_canvas_width
                    new_scroll_y = y_ratio * effective_canvas_height

                    # Clamp to valid scroll range
                    max_scroll_x = max(0, new_canvas_width - viewport_width)
                    max_scroll_y = max(0, new_canvas_height - viewport_height)

                    new_scroll_x = max(0, min(new_scroll_x, max_scroll_x))
                    new_scroll_y = max(0, min(new_scroll_y, max_scroll_y))

                    print(f"📐 Maintaining position: scroll=({new_scroll_x:.1f},{new_scroll_y:.1f})")

                    # Apply new scroll position
                    scroll_area.horizontalScrollBar().setValue(int(new_scroll_x))
                    scroll_area.verticalScrollBar().setValue(int(new_scroll_y))

                # If neither maintain_position nor goto_current_page nor goto_page_top_with_margin, keep current scroll values

            # STEP 5: Clear old cache and recalculate visible pages
            self.rendered_pages.clear()

            # Recalculate what's visible at new zoom and scroll position
            if scroll_area and self.layout_manager:
                final_scroll_x = scroll_area.horizontalScrollBar().value()
                final_scroll_y = scroll_area.verticalScrollBar().value()

                viewport_rect = QRectF(
                    final_scroll_x,
                    final_scroll_y,
                    scroll_area.viewport().width(),
                    scroll_area.viewport().height()
                )

                visible_pages = self.layout_manager.get_visible_pages(viewport_rect)
                self.visible_pages = visible_pages
                print(f"🔍 Visible pages after zoom: {visible_pages}")

            # STEP 6: Render visible pages at new zoom
            if self.visible_pages and not self.is_painting:
                for page_index in self.visible_pages:
                    if 0 <= page_index < self.document.get_page_count():
                        print(f"🖼️ Rendering page {page_index} for zoom change...")
                        self._render_page(page_index)

            print("✅ Zoom complete")
            self.zoomChanged.emit(zoom_level)

    def deprecated_01_set_zoom(self, zoom_level: float):
        """Set zoom level while maintaining visual reference point"""
        zoom_level = max(0.1, min(5.0, zoom_level))

        if abs(self.zoom_level - zoom_level) > 0.01:
            print(f"🔍 Setting zoom to {zoom_level:.2f}")

            # STEP 1: Stop timer to prevent conflicts
            self.render_timer.stop()
            self.needs_render = False

            # STEP 2: Capture current visual state BEFORE zoom
            old_zoom = self.zoom_level
            scroll_area = self._get_scroll_area()

            if scroll_area and self.layout_manager:
                # Current canvas dimensions
                old_canvas_width, old_canvas_height = self.layout_manager.get_canvas_size()

                # Current scroll position (top-left of viewport)
                current_scroll_x = scroll_area.horizontalScrollBar().value()
                current_scroll_y = scroll_area.verticalScrollBar().value()

                # Current viewport size
                viewport_width = scroll_area.viewport().width()
                viewport_height = scroll_area.viewport().height()

                # Calculate proportional position within canvas
                # Edge case: if canvas smaller than viewport, ratio could be > 1
                x_ratio = current_scroll_x / max(old_canvas_width, viewport_width) if old_canvas_width > 0 else 0
                y_ratio = current_scroll_y / max(old_canvas_height, viewport_height) if old_canvas_height > 0 else 0

                print(f"📐 BEFORE zoom: canvas=({old_canvas_width}x{old_canvas_height}), "
                      f"scroll=({current_scroll_x},{current_scroll_y}), "
                      f"ratios=({x_ratio:.3f},{y_ratio:.3f})")

            # STEP 3: Update zoom level and layout
            self.zoom_level = zoom_level

            if self.layout_manager:
                self.layout_manager.set_zoom(zoom_level)
                self._update_canvas_size()

                # Get NEW canvas dimensions after zoom
                new_canvas_width, new_canvas_height = self.layout_manager.get_canvas_size()

            # STEP 4: Calculate new scroll position to maintain ratios
            if scroll_area and self.layout_manager:
                # Apply same ratios to new canvas size
                # Edge case handling: ensure canvas is at least as big as viewport
                effective_canvas_width = max(new_canvas_width, viewport_width)
                effective_canvas_height = max(new_canvas_height, viewport_height)

                new_scroll_x = x_ratio * effective_canvas_width
                new_scroll_y = y_ratio * effective_canvas_height

                # Clamp to valid scroll range
                max_scroll_x = max(0, new_canvas_width - viewport_width)
                max_scroll_y = max(0, new_canvas_height - viewport_height)

                new_scroll_x = max(0, min(new_scroll_x, max_scroll_x))
                new_scroll_y = max(0, min(new_scroll_y, max_scroll_y))

                print(f"📐 AFTER zoom: canvas=({new_canvas_width}x{new_canvas_height}), "
                      f"new_scroll=({new_scroll_x:.1f},{new_scroll_y:.1f})")

                # Apply new scroll position
                scroll_area.horizontalScrollBar().setValue(int(new_scroll_x))
                scroll_area.verticalScrollBar().setValue(int(new_scroll_y))

            # STEP 5: Clear old cache and recalculate visible pages
            self.rendered_pages.clear()

            # Recalculate what's visible at new zoom and scroll position
            if scroll_area and self.layout_manager:
                final_scroll_x = scroll_area.horizontalScrollBar().value()
                final_scroll_y = scroll_area.verticalScrollBar().value()

                viewport_rect = QRectF(
                    final_scroll_x,
                    final_scroll_y,
                    viewport_width,
                    viewport_height
                )

                visible_pages = self.layout_manager.get_visible_pages(viewport_rect)
                self.visible_pages = visible_pages
                print(f"🔍 Visible pages after proportional zoom: {visible_pages}")

            # STEP 6: Render visible pages at new zoom
            if self.visible_pages and not self.is_painting:
                for page_index in self.visible_pages:
                    if 0 <= page_index < self.document.get_page_count():
                        print(f"🖼️ Rendering page {page_index} for zoom change...")
                        self._render_page(page_index)

            print("✅ Proportional zoom complete")
            self.zoomChanged.emit(zoom_level)

    def _get_scroll_area(self):
        """Get the scroll area containing this canvas"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'verticalScrollBar') and hasattr(parent, 'viewport'):
                return parent
            parent = parent.parent()
        return None

    def deprecated_02_set_zoom(self, zoom_level: float):
        """Set zoom level and update layout - FIXED: Preserve current page"""
        zoom_level = max(0.1, min(5.0, zoom_level))  # Clamp zoom range

        if abs(self.zoom_level - zoom_level) > 0.01:  # Avoid unnecessary updates
            print(f"🔍 Setting zoom to {zoom_level:.2f}")

            # FIXED: Preserve current page during zoom operation
            preserved_page = self._get_actual_current_page()
            print(f"📄 Preserving page {preserved_page} during zoom")

            self.zoom_level = zoom_level

            if self.layout_manager:
                self.layout_manager.set_zoom(zoom_level)
                self._update_canvas_size()
                self.rendered_pages.clear()  # Clear cache for new zoom

                # FIXED: Restore the preserved page
                self.current_page = preserved_page
                print(f"📄 Page preserved: {self.current_page}")

                self.schedule_render()

            self.zoomChanged.emit(zoom_level)

    def deprecated_01_set_zoom(self, zoom_level: float):
        """Set zoom level and update layout"""
        zoom_level = max(0.1, min(5.0, zoom_level))  # Clamp zoom range

        if abs(self.zoom_level - zoom_level) > 0.01:  # Avoid unnecessary updates
            print(f"🔍 Setting zoom to {zoom_level:.2f}")
            self.zoom_level = zoom_level

            if self.layout_manager:
                self.layout_manager.set_zoom(zoom_level)
                self._update_canvas_size()
                self.rendered_pages.clear()  # Clear cache for new zoom
                self.schedule_render()

            self.zoomChanged.emit(zoom_level)

    def get_zoom(self) -> float:
        """Get current zoom level"""
        return self.zoom_level

    def get_zoom_percent(self) -> int:
        """Get zoom as percentage"""
        return int(self.zoom_level * 100)

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
        self.set_zoom(zoom)

        self.set_zoom(zoom, maintain_position=False, goto_page_top_with_margin=True)

    def set_visible_pages(self, page_indices: List[int], viewport_rect: QRectF):
        """Set which pages are currently visible"""
        if self.is_painting:
            return

        print(f"👁️ Setting visible pages: {page_indices}")
        self.visible_pages = page_indices
        self.viewport_rect = viewport_rect
        self.schedule_render()

        # ✅ ONLY update current page if it's genuinely not visible
        # Don't automatically jump to first visible page during zoom
        if page_indices and self.current_page not in page_indices:
            # Only change if current page is far from visible range
            if not any(abs(self.current_page - p) <= 1 for p in page_indices):
                new_page = page_indices[0]
                if new_page != self.current_page:
                    self.current_page = new_page
                    self.pageChanged.emit(new_page)

    def deprecated_01_set_visible_pages(self, page_indices: List[int], viewport_rect: QRectF):
        """Set which pages are currently visible"""
        # Prevent updates during painting
        if self.is_painting:
            return

        print(f"👁️ Setting visible pages: {page_indices}")
        self.visible_pages = page_indices
        self.viewport_rect = viewport_rect
        self.schedule_render()

        # Update current page if needed
        if page_indices and self.current_page not in page_indices:
            new_page = page_indices[0]  # Use first visible page
            if new_page != self.current_page:
                self.current_page = new_page
                self.pageChanged.emit(new_page)

    def get_page_at_position(self, y_position: float) -> int:
        """Get page index at Y position"""
        if self.layout_manager:
            return self.layout_manager.get_page_at_position(y_position)
        return 0

    def get_page_y_position(self, page_index: int) -> float:
        """Get Y position of page start"""
        if self.layout_manager:
            return self.layout_manager.get_page_y_position(page_index)
        return 0.0

    def get_current_page_from_scroll(self, scroll_y: float) -> int:
        """Get current page based on scroll position"""
        return self.get_page_at_position(scroll_y + 100)  # Add offset for better detection

    def get_visible_pages_in_viewport(self, viewport_rect: QRectF) -> List[int]:
        """Get list of page indices visible in viewport"""
        if self.layout_manager:
            visible = self.layout_manager.get_visible_pages(viewport_rect)
            print(f"🔍 Visible pages in viewport {viewport_rect}: {visible}")
            return visible
        return []

    def get_canvas_size(self) -> tuple:
        """Get total canvas size needed"""
        if self.layout_manager:
            size = self.layout_manager.get_canvas_size()
            print(f"📏 Canvas size: {size}")
            return size
        return (400, 300)

    def document_to_canvas_coordinates(self, page_index: int, doc_x: float, doc_y: float) -> tuple:
        """Convert document coordinates to canvas coordinates"""
        if self.layout_manager:
            from PyQt6.QtCore import QPointF
            doc_point = QPointF(doc_x, doc_y)
            canvas_point = self.layout_manager.document_to_canvas(page_index, doc_point)
            return (canvas_point.x(), canvas_point.y())
        return (0, 0)

    def canvas_to_document_coordinates(self, page_index: int, canvas_x: float, canvas_y: float) -> tuple:
        """Convert canvas coordinates to document coordinates"""
        if self.layout_manager:
            from PyQt6.QtCore import QPointF
            canvas_point = QPointF(canvas_x, canvas_y)
            doc_point = self.layout_manager.canvas_to_document(page_index, canvas_point)
            return (doc_point.x(), doc_point.y())
        return (0, 0)

    def get_page_at_canvas_position(self, canvas_x: float, canvas_y: float) -> Optional[int]:
        """Get page index at canvas position"""
        if not self.layout_manager:
            return None

        for i in range(self.document.get_page_count() if self.document else 0):
            page_rect = self.layout_manager.get_page_rect(i)
            if page_rect and page_rect.contains(canvas_x, canvas_y):
                return i
        return None

    def schedule_render(self):
        """Schedule a render update (with debouncing)"""
        if self.is_painting:  # Don't schedule during painting
            return

        print("⏰ Scheduling render...")
        self.needs_render = True
        self.render_timer.stop()
        self.render_timer.start(100)  # Increased delay to 100ms

    def _perform_render(self):
        """Perform the actual rendering - normal operation"""
        if self.is_painting:
            print("⏸️ Skipping render - currently painting")
            return

        print("🎨 Performing render...")
        if not self.needs_render or not self.document or not self.layout_manager:
            print("❌ Render cancelled - missing components")
            return

        self.needs_render = False
        print(f"🎨 Rendering pages: {self.visible_pages}")

        # Simple logic - render visible pages that aren't cached
        for page_index in self.visible_pages:
            if page_index not in self.rendered_pages:
                print(f"🖼️ Rendering page {page_index}...")
                self._render_page(page_index)

        # Normal cache cleanup
        pages_to_keep = set(self.visible_pages)
        for page_idx in self.visible_pages:
            pages_to_keep.add(max(0, page_idx - 1))
            pages_to_keep.add(min(self.document.get_page_count() - 1, page_idx + 1))

        pages_to_remove = [p for p in self.rendered_pages.keys() if p not in pages_to_keep]
        for page_idx in pages_to_remove:
            del self.rendered_pages[page_idx]

        print(f"🎨 Render complete. Cached pages: {list(self.rendered_pages.keys())}")

        if not self.is_painting:
            self.update()

        print("🎨 Performing render...")
        if not self.needs_render or not self.document or not self.layout_manager:
            print("❌ Render cancelled - missing components")
            return

        self.needs_render = False

        print(f"🎨 Rendering pages: {self.visible_pages}")

        # Render visible pages that aren't cached
        for page_index in self.visible_pages:
            if page_index not in self.rendered_pages:
                print(f"🖼️ Rendering page {page_index}...")
                self._render_page(page_index)

        # Clean up cache - keep only visible pages + 2 adjacent
        pages_to_keep = set(self.visible_pages)
        for page_idx in self.visible_pages:
            pages_to_keep.add(max(0, page_idx - 1))
            pages_to_keep.add(min(self.document.get_page_count() - 1, page_idx + 1))

        # Remove pages not in keep list
        pages_to_remove = [p for p in self.rendered_pages.keys() if p not in pages_to_keep]
        for page_idx in pages_to_remove:
            del self.rendered_pages[page_idx]

        print(f"🎨 Render complete. Cached pages: {list(self.rendered_pages.keys())}")

        # Only call update if not currently painting
        if not self.is_painting:
            self.update()  # Trigger paint event

    def _render_page(self, page_index: int):
        """Render a single page"""
        try:
            print(f"🖼️ Rendering page {page_index} at zoom {self.zoom_level:.2f}")

            # CRITICAL FIX: Use consistent DPI calculation
            # Calculate render DPI based on zoom to match layout manager expectations
            base_dpi = 72  # PDF native DPI
            render_dpi = int(base_dpi * self.zoom_level)

            print(f"📐 Using render DPI: {render_dpi} (zoom: {self.zoom_level:.2f})")

            pixmap = self.document.render_page(page_index, 1.0, render_dpi)  # Use zoom=1.0, control via DPI
            print(f"✅ Page {page_index} rendered: {pixmap.width()}x{pixmap.height()}")

            self.rendered_pages[page_index] = pixmap
        except Exception as e:
            print(f"❌ Error rendering page {page_index}: {e}")
            import traceback
            traceback.print_exc()

    def _update_canvas_size(self):
        """Update canvas size based on layout"""
        if self.layout_manager:
            width, height = self.layout_manager.get_canvas_size()
            print(f"📏 Updating canvas size to: {width}x{height}")
            self.resize(max(width, 400), max(height, 300))
            print(f"📏 Canvas widget size: {self.size()}")

    # Add to paintEvent() method for debugging
    def paintEvent(self, event):
        """Paint the visible pages - with loop prevention and debugging"""

        # Debug: What triggered this paint event?
        import traceback
        stack = traceback.extract_stack()
        recent_calls = [frame.name for frame in stack[-5:]]
        print(f"🎨 Paint event #{self.paint_count + 1} triggered by: {' -> '.join(recent_calls)}")

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
        """Paint message when no document is loaded"""
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No document loaded")
        print("🎨 Painted 'no document' message")

    def _paint_page(self, painter, page_index: int) -> bool:
        """Paint a single page - returns True if painted"""
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

            # FIXED: Scale pixmap to fit page rect exactly
            painter.drawPixmap(page_rect.toRect(), pixmap)
            print(f"✅ Pixmap scaled and drawn for page {page_index}")
        else:
            # Draw loading indicator
            painter.setPen(QPen(Qt.GlobalColor.gray))
            painter.drawText(page_rect, Qt.AlignmentFlag.AlignCenter, f"Loading page {page_index + 1}...")
            print(f"⏳ Loading indicator drawn for page {page_index}")

        return True

    def mousePressEvent(self, event):
        """Handle mouse press events"""
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
        """Handle mouse move events"""
        if self.layout_manager:
            page_index = self.get_page_at_canvas_position(event.position().x(), event.position().y())
            if page_index is not None:
                doc_x, doc_y = self.canvas_to_document_coordinates(
                    page_index, event.position().x(), event.position().y()
                )
                # Could emit mouse move signal here if needed

        super().mouseMoveEvent(event)

    def _get_actual_current_page(self) -> int:
        """Get the actual current page from scroll position"""
        try:
            # Try to get scroll position from parent scroll area
            parent = self.parent()
            while parent:
                if hasattr(parent, 'verticalScrollBar'):
                    scroll_y = parent.verticalScrollBar().value()
                    viewport_height = parent.viewport().height() if hasattr(parent, 'viewport') else 400

                    # Calculate page at center of viewport
                    center_y = scroll_y + (viewport_height / 2)
                    actual_page = self.get_page_at_position(center_y)

                    print(f"📍 Actual current page: scroll_y={scroll_y}, center_y={center_y}, page={actual_page}")
                    return actual_page
                parent = parent.parent()

            # Fallback to stored current_page
            return max(0, self.current_page)

        except Exception as e:
            print(f"⚠️ Error getting actual current page: {e}")
            return max(0, self.current_page)

