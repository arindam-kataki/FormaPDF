"""
PDF Link Overlay Widget - Renders clickable link overlays
Location: src/ui/pdf_link_overlay.py
"""

from typing import List, Optional
from PyQt6.QtWidgets import QWidget, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QCursor, QMouseEvent
from src.core.a_pdf_link_manager import PDFLink, PDFLinkManager


class LinkOverlayWidget(QWidget):
    """
    Individual link overlay widget that handles one clickable link area
    """

    linkClicked = pyqtSignal(PDFLink)

    def __init__(self, link: PDFLink, parent=None):
        super().__init__(parent)
        self.link = link
        self.is_hovered = False

        # Set up widget properties
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set tooltip
        if link.tooltip:
            self.setToolTip(link.tooltip)

        # Position and size the widget
        self.setGeometry(
            int(link.rect.x()),
            int(link.rect.y()),
            int(link.rect.width()),
            int(link.rect.height())
        )

        # Style based on link type
        self.setup_styling()

    def setup_styling(self):
        """Set up visual styling based on link type"""
        # Different colors for different link types
        if self.link.link_type == 'goto':
            self.link_color = QColor(0, 100, 200, 80)  # Blue for internal links
            self.hover_color = QColor(0, 100, 200, 120)
        elif self.link.link_type == 'uri':
            self.link_color = QColor(200, 0, 100, 80)  # Red for external links
            self.hover_color = QColor(200, 0, 100, 120)
        else:
            self.link_color = QColor(100, 100, 100, 80)  # Gray for other types
            self.hover_color = QColor(100, 100, 100, 120)

    def paintEvent(self, event):
        """Paint the link overlay"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Choose color based on hover state
        color = self.hover_color if self.is_hovered else self.link_color

        # Draw semi-transparent rectangle
        painter.fillRect(self.rect(), QBrush(color))

        # Draw border
        pen = QPen(color.darker(150), 1)
        painter.setPen(pen)
        painter.drawRect(self.rect())

    def enterEvent(self, event):
        """Handle mouse enter"""
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"🖱️ Link overlay clicked: {self.link.tooltip}")
            self.linkClicked.emit(self.link)
        super().mousePressEvent(event)


class PDFLinkOverlayManager(QWidget):
    """
    Manages all link overlays for a PDF page or canvas
    """

    linkClicked = pyqtSignal(PDFLink)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.link_manager: Optional[PDFLinkManager] = None
        self.current_page = -1
        self.current_zoom = 1.0
        self.link_overlays: List[LinkOverlayWidget] = []

        # Make this widget transparent to mouse events by default
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        print("📎 PDFLinkOverlayManager initialized")

    def set_link_manager(self, link_manager: PDFLinkManager):
        """Set the link manager"""
        self.link_manager = link_manager

        # Connect to link manager signals
        if self.link_manager:
            self.link_manager.linkClicked.connect(self.linkClicked)

    def update_page_links(self, page_num: int, zoom_level: float = 1.0):
        """
        Update link overlays for a specific page

        Args:
            page_num: 0-based page number
            zoom_level: Current zoom level
        """
        return
        if not self.link_manager:
            return

        print(f"📎 Updating link overlays for page {page_num + 1} at zoom {zoom_level:.2f}")

        # Clear existing overlays
        self.clear_overlays()

        # Get scaled links for the page
        links = self.link_manager.scale_links_for_zoom(page_num, zoom_level)

        # Create overlay widgets for each link
        for link in links:
            overlay = LinkOverlayWidget(link, self)
            overlay.linkClicked.connect(self._on_link_overlay_clicked)
            overlay.show()
            self.link_overlays.append(overlay)

        self.current_page = page_num
        self.current_zoom = zoom_level

        print(f"📎 Created {len(self.link_overlays)} link overlays")

    def clear_overlays(self):
        """Clear all link overlay widgets"""
        for overlay in self.link_overlays:
            overlay.hide()
            overlay.deleteLater()

        self.link_overlays.clear()

    def _on_link_overlay_clicked(self, link: PDFLink):
        """Handle click on a link overlay"""
        if self.link_manager:
            self.link_manager.handle_link_click(link)

        # Also emit our own signal
        self.linkClicked.emit(link)

    def update_zoom(self, zoom_level: float):
        """Update overlay positions for new zoom level"""
        if self.current_page >= 0 and zoom_level != self.current_zoom:
            self.update_page_links(self.current_page, zoom_level)

    def hide_links(self):
        """Hide all link overlays"""
        for overlay in self.link_overlays:
            overlay.hide()

    def show_links(self):
        """Show all link overlays"""
        for overlay in self.link_overlays:
            overlay.show()

    def toggle_link_visibility(self, visible: bool):
        """Toggle visibility of all link overlays"""
        if visible:
            self.show_links()
        else:
            self.hide_links()

    def get_link_at_position(self, x: int, y: int) -> Optional[PDFLink]:
        """
        Get the link at a specific widget position

        Args:
            x, y: Position in widget coordinates

        Returns:
            PDFLink at position, or None
        """
        for overlay in self.link_overlays:
            if overlay.geometry().contains(x, y):
                return overlay.link

        return None

    def paintEvent(self, event):
        """Paint method - mostly transparent"""
        # This widget is mostly transparent, child overlays do the painting
        super().paintEvent(event)

    def resizeEvent(self, event):
        """Handle resize - update overlay positions"""
        super().resizeEvent(event)

        # Overlays are positioned relative to this widget, so they should
        # automatically be repositioned correctly

    def get_link_statistics(self) -> dict:
        """Get statistics about current links"""
        if not self.link_overlays:
            return {'total': 0, 'by_type': {}}

        stats = {'total': len(self.link_overlays), 'by_type': {}}

        for overlay in self.link_overlays:
            link_type = overlay.link.link_type
            stats['by_type'][link_type] = stats['by_type'].get(link_type, 0) + 1

        return stats


class PDFLinkDebugOverlay(QWidget):
    """
    Debug overlay that shows link information visually
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.links: List[PDFLink] = []
        self.show_debug = False

        # Make transparent to mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_links(self, links: List[PDFLink]):
        """Set links to debug display"""
        self.links = links
        self.update()

    def toggle_debug(self, show: bool):
        """Toggle debug display"""
        self.show_debug = show
        self.update()

    def paintEvent(self, event):
        """Paint debug information"""
        if not self.show_debug or not self.links:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw debug info for each link
        for i, link in enumerate(self.links):
            # Draw bounding rectangle
            pen = QPen(QColor(255, 0, 255), 2)  # Magenta border
            painter.setPen(pen)
            painter.drawRect(
                int(link.rect.x()),
                int(link.rect.y()),
                int(link.rect.width()),
                int(link.rect.height())
            )

            # Draw link type label
            label_pos = QPoint(int(link.rect.x()), int(link.rect.y()) - 5)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(label_pos, f"{i + 1}: {link.link_type}")

    def get_debug_info(self) -> str:
        """Get debug information as text"""
        if not self.links:
            return "No links found"

        info_lines = [f"Links found: {len(self.links)}"]

        for i, link in enumerate(self.links):
            info_lines.append(
                f"{i + 1}. {link.link_type}: {link.tooltip} "
                f"at ({link.rect.x():.0f}, {link.rect.y():.0f})"
            )

        return "\n".join(info_lines)