"""
PDF Link Manager - Core link extraction and management
Location: src/core/pdf_link_manager.py
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QRectF, QUrl
from PyQt6.QtGui import QDesktopServices
import fitz  # PyMuPDF


@dataclass
class PDFLink:
    """Data structure for a PDF link"""
    link_id: str  # Unique identifier
    page_num: int  # 0-based page number where link appears
    rect: QRectF  # Link rectangle in PDF points
    link_type: str  # 'goto', 'uri', 'launch', 'gotor', 'named'

    # Type-specific data
    target_page: Optional[int] = None  # For internal links (0-based)
    target_coords: Optional[Tuple[float, float]] = None  # (x, y) in points
    uri: Optional[str] = None  # For external URLs
    file_path: Optional[str] = None  # For file links
    zoom_level: Optional[float] = None  # Target zoom

    # Display properties
    tooltip: Optional[str] = None
    is_visible: bool = True


class PDFLinkManager(QObject):
    """
    Manages PDF hyperlinks - extraction, processing, and navigation
    """

    # Signals
    linkClicked = pyqtSignal(PDFLink)  # Emitted when any link is clicked
    internalLinkClicked = pyqtSignal(int, float, float)  # page, x, y for internal navigation
    externalLinkClicked = pyqtSignal(str)  # URL for external links

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_document = None
        self.links_cache: Dict[int, List[PDFLink]] = {}  # page_num -> links
        self.link_counter = 0

    def set_pdf_document(self, pdf_document):
        """Set the PDF document and clear cache"""
        self.pdf_document = pdf_document
        self.clear_cache()
        print(f"📎 PDFLinkManager: Document set")

    def clear_cache(self):
        """Clear all cached links"""
        self.links_cache.clear()
        self.link_counter = 0
        print(f"🧹 PDFLinkManager: Cache cleared")

    def extract_page_links(self, page_num: int) -> List[PDFLink]:
        """
        Extract all links from a specific page

        Args:
            page_num: 0-based page number

        Returns:
            List of PDFLink objects
        """
        # Check cache first
        if page_num in self.links_cache:
            return self.links_cache[page_num]

        if not self.pdf_document or not hasattr(self.pdf_document, 'doc'):
            return []

        try:
            # Get PyMuPDF page object
            if page_num >= len(self.pdf_document.doc) or page_num < 0:
                return []

            page = self.pdf_document.doc[page_num]
            raw_links = page.get_links()

            print(f"📎 Extracting links from page {page_num + 1}: found {len(raw_links)} links")

            # Convert to PDFLink objects
            page_links = []
            for raw_link in raw_links:
                pdf_link = self._parse_raw_link(raw_link, page_num)
                if pdf_link:
                    page_links.append(pdf_link)

            # Cache the results
            self.links_cache[page_num] = page_links

            if page_links:
                print(f"📎 Page {page_num + 1} processed links:")
                for link in page_links[:3]:  # Show first 3
                    print(f"   {link.link_type}: {link.tooltip}")

            return page_links

        except Exception as e:
            print(f"❌ Error extracting links from page {page_num}: {e}")
            return []

    def _parse_raw_link(self, raw_link: dict, page_num: int) -> Optional[PDFLink]:
        """
        Parse a raw PyMuPDF link into a PDFLink object

        Args:
            raw_link: Raw link data from PyMuPDF
            page_num: Page number where link appears

        Returns:
            PDFLink object or None if parsing fails
        """
        try:
            # Generate unique ID
            self.link_counter += 1
            link_id = f"link_{page_num}_{self.link_counter}"

            # Extract basic properties
            rect = QRectF(
                raw_link['from'].x0,
                raw_link['from'].y0,
                raw_link['from'].width,
                raw_link['from'].height
            )

            return PDFLink(
                link_id=link_id,
                page_num=page_num,
                rect=rect,
                link_type="unknown",
                tooltip=f"Link {self.link_counter}"
            )

            # Determine link type and parse type-specific data
            link_kind = raw_link.get('kind', 0)

            if link_kind == fitz.LINK_GOTO:
                # Internal link to another page
                return self._parse_goto_link(raw_link, link_id, page_num, rect)

            elif link_kind == fitz.LINK_URI:
                # External URL link
                return self._parse_uri_link(raw_link, link_id, page_num, rect)

            elif link_kind == fitz.LINK_LAUNCH:
                # Launch file link
                return self._parse_launch_link(raw_link, link_id, page_num, rect)

            elif link_kind == fitz.LINK_GOTOR:
                # Link to external document
                return self._parse_gotor_link(raw_link, link_id, page_num, rect)

            elif link_kind == fitz.LINK_NAMED:
                # Named destination link
                return self._parse_named_link(raw_link, link_id, page_num, rect)

            else:
                print(f"⚠️ Unknown link type: {link_kind}")
                return None

        except Exception as e:
            print(f"❌ Error parsing raw link: {e}")
            return None

    def _parse_goto_link(self, raw_link: dict, link_id: str, page_num: int, rect: QRectF) -> PDFLink:
        """Parse internal goto link"""
        target_page = raw_link.get('page', 0)  # PyMuPDF uses 0-based for links!
        target_coords = (0, 0)
        zoom = None

        # Parse destination details
        if 'to' in raw_link:
            to_data = raw_link['to']
            if isinstance(to_data, (list, tuple)) and len(to_data) >= 2:
                target_coords = (float(to_data[0] or 0), float(to_data[1] or 0))
                if len(to_data) >= 3:
                    zoom = float(to_data[2]) if to_data[2] else None

        tooltip = f"Go to page {target_page + 1}"
        if target_coords != (0, 0):
            tooltip += f" at ({target_coords[0]:.0f}, {target_coords[1]:.0f})"

        return PDFLink(
            link_id=link_id,
            page_num=page_num,
            rect=rect,
            link_type='goto',
            target_page=target_page,
            target_coords=target_coords,
            zoom_level=zoom,
            tooltip=tooltip
        )

    def _parse_uri_link(self, raw_link: dict, link_id: str, page_num: int, rect: QRectF) -> PDFLink:
        """Parse external URI link"""
        uri = raw_link.get('uri', '')

        # Create user-friendly tooltip
        tooltip = f"Open: {uri}"
        if len(tooltip) > 50:
            tooltip = tooltip[:47] + "..."

        return PDFLink(
            link_id=link_id,
            page_num=page_num,
            rect=rect,
            link_type='uri',
            uri=uri,
            tooltip=tooltip
        )

    def _parse_launch_link(self, raw_link: dict, link_id: str, page_num: int, rect: QRectF) -> PDFLink:
        """Parse file launch link"""
        file_path = raw_link.get('file', '')

        tooltip = f"Open file: {file_path}"
        if len(tooltip) > 50:
            tooltip = tooltip[:47] + "..."

        return PDFLink(
            link_id=link_id,
            page_num=page_num,
            rect=rect,
            link_type='launch',
            file_path=file_path,
            tooltip=tooltip
        )

    def _parse_gotor_link(self, raw_link: dict, link_id: str, page_num: int, rect: QRectF) -> PDFLink:
        """Parse external document link"""
        file_path = raw_link.get('file', '')
        target_page = raw_link.get('page', 0)

        tooltip = f"Go to {file_path}, page {target_page + 1}"
        if len(tooltip) > 50:
            tooltip = tooltip[:47] + "..."

        return PDFLink(
            link_id=link_id,
            page_num=page_num,
            rect=rect,
            link_type='gotor',
            file_path=file_path,
            target_page=target_page,
            tooltip=tooltip
        )

    def _parse_named_link(self, raw_link: dict, link_id: str, page_num: int, rect: QRectF) -> PDFLink:
        """Parse named destination link - FIXED for actual PDF structure"""
        # FIXED: Use 'nameddest' key instead of 'name'
        name = raw_link.get('nameddest', '') or raw_link.get('name', '')

        # Extract target page (your PDFs already have this resolved!)
        target_page = raw_link.get('page', None)

        # Extract target coordinates from 'to' Point
        target_coords = None
        if 'to' in raw_link:
            to_point = raw_link['to']
            if hasattr(to_point, 'x') and hasattr(to_point, 'y'):
                target_coords = (float(to_point.x), float(to_point.y))

        # Get zoom level if available
        zoom_level = raw_link.get('zoom', None)
        if zoom_level == 0.0:
            zoom_level = None  # 0.0 means no zoom specified

        # Create user-friendly tooltip
        if target_page is not None:
            tooltip = f"Go to page {target_page + 1}"
            if target_coords and target_coords != (0.0, 0.0):
                tooltip += f" at ({target_coords[0]:.0f}, {target_coords[1]:.0f})"
            if name:
                tooltip += f" ('{name}')"
        else:
            tooltip = f"Named destination: {name}"

        return PDFLink(
            link_id=link_id,
            page_num=page_num,
            rect=rect,
            link_type='named',
            target_page=target_page,  # Now populated!
            target_coords=target_coords,  # Now populated!
            zoom_level=zoom_level,
            tooltip=tooltip
        )

    def handle_link_click(self, link: PDFLink):
        """
        Handle a link click - route to appropriate action

        Args:
            link: The PDFLink that was clicked
        """
        print(f"🖱️ Link clicked: {link.link_type} - {link.tooltip}")

        # Emit general signal
        self.linkClicked.emit(link)

        # Handle specific link types
        if link.link_type == 'goto':
            self._handle_goto_link(link)
        elif link.link_type == 'uri':
            self._handle_uri_link(link)
        elif link.link_type == 'launch':
            self._handle_launch_link(link)
        elif link.link_type == 'gotor':
            self._handle_gotor_link(link)
        elif link.link_type == 'named':
            self._handle_named_link(link)

    def _handle_goto_link(self, link: PDFLink):
        """Handle internal page navigation"""
        if link.target_page is not None:
            x, y = link.target_coords or (0, 0)
            print(f"📍 Navigating to page {link.target_page + 1} at ({x}, {y})")
            self.internalLinkClicked.emit(link.target_page, x, y)

    def _handle_uri_link(self, link: PDFLink):
        """Handle external URL"""
        if link.uri:
            print(f"🌐 Opening URL: {link.uri}")
            self.externalLinkClicked.emit(link.uri)
            QDesktopServices.openUrl(QUrl(link.uri))

    def _handle_launch_link(self, link: PDFLink):
        """Handle file launch"""
        if link.file_path:
            print(f"📁 Opening file: {link.file_path}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(link.file_path))

    def _handle_gotor_link(self, link: PDFLink):
        """Handle external document link"""
        if link.file_path:
            print(f"📄 Opening external document: {link.file_path}")
            # Could be enhanced to open specific page in the future
            QDesktopServices.openUrl(QUrl.fromLocalFile(link.file_path))

    def _handle_named_link(self, link: PDFLink):
        """Handle named destination - FIXED"""
        print(f"🏷️ Handling named destination: {link.tooltip}")

        if link.target_page is not None:
            # Perfect! Your PDFs already have resolved destinations
            x, y = link.target_coords or (0, 0)
            print(f"📍 Navigating to page {link.target_page + 1} at ({x}, {y})")

            # Emit the navigation signal (same as goto links)
            self.internalLinkClicked.emit(link.target_page, x, y)
        else:
            print(f"❌ No target page found for named destination")

    def get_links_in_area(self, page_num: int, rect: QRectF) -> List[PDFLink]:
        """
        Get all links that intersect with a given rectangle

        Args:
            page_num: Page number
            rect: Rectangle to check for intersections

        Returns:
            List of intersecting links
        """
        page_links = self.extract_page_links(page_num)
        intersecting_links = []

        for link in page_links:
            if link.rect.intersects(rect):
                intersecting_links.append(link)

        return intersecting_links

    def get_link_at_point(self, page_num: int, x: float, y: float) -> Optional[PDFLink]:
        """
        Get the first link at a specific point

        Args:
            page_num: Page number
            x, y: Point coordinates in PDF points

        Returns:
            PDFLink at the point, or None
        """
        page_links = self.extract_page_links(page_num)

        for link in page_links:
            if link.rect.contains(x, y):
                return link

        return None

    def scale_links_for_zoom(self, page_num: int, zoom_level: float) -> List[PDFLink]:
        """
        Get links scaled for a specific zoom level

        Args:
            page_num: Page number
            zoom_level: Current zoom level

        Returns:
            List of links with scaled rectangles
        """
        page_links = self.extract_page_links(page_num)
        scaled_links = []

        for link in page_links:
            # Create a copy with scaled rectangle
            scaled_rect = QRectF(
                link.rect.x() * zoom_level,
                link.rect.y() * zoom_level,
                link.rect.width() * zoom_level,
                link.rect.height() * zoom_level
            )

            # Create new link with scaled rect
            scaled_link = PDFLink(
                link_id=link.link_id,
                page_num=link.page_num,
                rect=scaled_rect,
                link_type=link.link_type,
                target_page=link.target_page,
                target_coords=link.target_coords,
                uri=link.uri,
                file_path=link.file_path,
                zoom_level=link.zoom_level,
                tooltip=link.tooltip
            )

            scaled_links.append(scaled_link)

        return scaled_links