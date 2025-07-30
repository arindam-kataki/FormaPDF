"""
PDF Link Manager - Complete Python Implementation (FIXED for PDFDocument)
Handles all PDF hyperlink extraction, parsing, and management using PyMuPDF
Compatible with custom PDFDocument class that has get_page_count() method
"""

import fitz  # PyMuPDF
import os
import webbrowser
import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QRectF, QPointF


class LinkType(Enum):
    """PDF link types"""
    GOTO = "goto"          # Internal page navigation
    URI = "uri"            # External URL
    LAUNCH = "launch"      # Launch file
    GOTOR = "gotor"        # External document
    NAMED = "named"        # Named destination
    UNKNOWN = "unknown"    # Unknown type


@dataclass
class PDFLink:
    """Represents a PDF hyperlink with all necessary information"""
    id: str
    link_type: LinkType
    bounds: QRectF  # Rectangle in PDF coordinates (points)
    page_index: int
    description: str
    target: Dict[str, Any]
    raw_link: Dict[str, Any]

    def __post_init__(self):
        """Ensure bounds is QRectF"""
        if not isinstance(self.bounds, QRectF):
            # Convert from dictionary or tuple if needed
            if isinstance(self.bounds, dict):
                self.bounds = QRectF(
                    self.bounds.get('x', 0),
                    self.bounds.get('y', 0),
                    self.bounds.get('width', 0),
                    self.bounds.get('height', 0)
                )
            elif isinstance(self.bounds, (list, tuple)) and len(self.bounds) >= 4:
                self.bounds = QRectF(*self.bounds[:4])


class PDFLinkManager(QObject):
    """
    Manages PDF hyperlink extraction, parsing, and navigation
    Integrates with PyMuPDF and provides Qt signals for UI updates
    FIXED to work with custom PDFDocument class
    """

    # Signals
    linkClicked = pyqtSignal(object)  # PDFLink
    navigationRequested = pyqtSignal(int, float, float)  # page, x, y
    externalUrlRequested = pyqtSignal(str)  # url
    externalFileRequested = pyqtSignal(str, int)  # file_path, page
    linkExtractionCompleted = pyqtSignal(int, list)  # page_index, links

    def __init__(self, parent=None):
        super().__init__(parent)

        # Core state
        self.pdf_document = None  # Custom PDFDocument or fitz.Document
        self.document_path = ""
        self.page_links_cache = {}  # Cache for extracted links
        self.named_destinations = {}  # Cache for named destinations

        # Security settings
        self.allow_external_urls = True
        self.allow_file_launch = True
        self.confirm_external_actions = True

        # Performance settings
        self.cache_links = True
        self.max_cache_size = 1000  # Maximum cached pages

        print("🔗 PDFLinkManager initialized")

    def set_pdf_document(self, pdf_document, document_path: str = ""):
        """Set the PDF document for link extraction - FIXED for custom PDFDocument"""
        try:
            self.pdf_document = pdf_document
            self.document_path = document_path

            # Clear caches
            self.page_links_cache.clear()
            self.named_destinations.clear()

            # Extract named destinations if available
            if pdf_document:
                self._extract_named_destinations()
                print(f"🔗 PDF document set: {document_path}")

                # Get page count - handle both PyMuPDF docs and custom PDFDocument objects
                if hasattr(pdf_document, 'get_page_count'):
                    page_count = pdf_document.get_page_count()
                elif hasattr(pdf_document, 'doc') and pdf_document.doc:
                    page_count = len(pdf_document.doc)
                else:
                    page_count = len(pdf_document) if hasattr(pdf_document, '__len__') else 0

                print(f"📖 Document has {page_count} pages")

        except Exception as e:
            print(f"❌ Error setting PDF document: {e}")

    def extract_page_links(self, page_index: int) -> List[PDFLink]:
        """Extract all links from a specific page - FIXED for custom PDFDocument"""
        # Get the actual PyMuPDF document object

        import time
        start_time = time.perf_counter()

        fitz_doc = None
        if hasattr(self.pdf_document, 'doc'):
            fitz_doc = self.pdf_document.doc  # Custom PDFDocument class
        elif hasattr(self.pdf_document, '__getitem__'):
            fitz_doc = self.pdf_document  # Direct PyMuPDF document

        if not fitz_doc:
            print(f"❌ Cannot access PyMuPDF document for page {page_index}")
            return []

        # Validate page index
        if page_index < 0 or page_index >= len(fitz_doc):
            print(f"❌ Invalid page index: {page_index} (document has {len(fitz_doc)} pages)")
            return []

        # Check cache first
        if self.cache_links and page_index in self.page_links_cache:
            return self.page_links_cache[page_index]

        try:
            extraction_start = time.perf_counter()
            page = fitz_doc[page_index]
            raw_links = page.get_links()
            extraction_time = time.perf_counter() - extraction_start

            pdf_links = []
            parsing_start = time.perf_counter()
            for i, raw_link in enumerate(raw_links):
                pdf_link = self._parse_raw_link_minimal(raw_link, page_index, i)
                if pdf_link:
                    pdf_links.append(pdf_link)

            # Cache the results
            if self.cache_links:
                self._manage_cache_size()
                self.page_links_cache[page_index] = pdf_links

            parsing_time = time.perf_counter() - parsing_start
            total_time = time.perf_counter() - start_time

            print(f"🔗 Page {page_index + 1}: Extracted {len(pdf_links)} links")

            # Emit signal
            self.linkExtractionCompleted.emit(page_index, pdf_links)

            parse_full = False

            mode = "FULL" if parse_full else "MINIMAL"
            print(f"🔗 Page {page_index + 1}: {len(pdf_links)} links ({mode})")
            print(f"   📊 Extraction: {extraction_time * 1000:.2f}ms")
            print(f"   🔧 Parsing: {parsing_time * 1000:.2f}ms")
            print(f"   ⏱️ Total: {total_time * 1000:.2f}ms")
            print(
                f"   🚀 Per link: {(parsing_time / len(pdf_links) * 1000):.2f}ms" if pdf_links else "   🚀 Per link: 0ms")

            return pdf_links

        except Exception as e:
            print(f"❌ Error extracting links from page {page_index}: {e}")
            return []

    def _parse_raw_link_minimal(self, raw_link: dict, page_index: int, link_index: int) -> PDFLink:
        """Ultra-fast parsing - bounds and reference only"""

        # Extract bounds (only thing needed for overlays)
        try:
            link_rect = raw_link['from']
        except KeyError:
            link_rect = fitz.Rect(0, 0, 0, 0)
        bounds = QRectF(link_rect.x0, link_rect.y0, link_rect.width, link_rect.height)

        # Generate ID
        link_id = f"link_{page_index}_{link_index}"

        # Just store the raw reference - no processing at all
        return PDFLink(
            id=link_id,
            link_type=LinkType.UNKNOWN,  # Don't even detect type
            bounds=bounds,
            page_index=page_index,
            description="Link",  # Generic description
            target={'_raw_data': raw_link, '_parsed': False},
            raw_link=raw_link
        )

    def _get_basic_link_type(self, link_kind: int) -> LinkType:
        """Fast link type detection"""
        type_map = {
            fitz.LINK_GOTO: LinkType.GOTO,
            fitz.LINK_URI: LinkType.URI,
            fitz.LINK_LAUNCH: LinkType.LAUNCH,
            fitz.LINK_GOTOR: LinkType.GOTOR,
            fitz.LINK_NAMED: LinkType.NAMED
        }
        return type_map.get(link_kind, LinkType.UNKNOWN)

    def _parse_raw_link(self, raw_link: dict, page_index: int, link_index: int) -> Optional[PDFLink]:
        """Parse raw PyMuPDF link data into PDFLink object"""
        try:
            # Extract bounds
            link_rect = raw_link.get('from', fitz.Rect(0, 0, 0, 0))
            bounds = QRectF(link_rect.x0, link_rect.y0, link_rect.width, link_rect.height)

            # Generate unique ID
            link_id = f"link_{page_index}_{link_index}"

            # Determine link type and extract details
            link_kind = raw_link.get('kind', fitz.LINK_NONE)

            if link_kind == fitz.LINK_GOTO:
                return self._parse_goto_link(raw_link, page_index, link_id, bounds)
            elif link_kind == fitz.LINK_URI:
                return self._parse_uri_link(raw_link, page_index, link_id, bounds)
            elif link_kind == fitz.LINK_LAUNCH:
                return self._parse_launch_link(raw_link, page_index, link_id, bounds)
            elif link_kind == fitz.LINK_GOTOR:
                return self._parse_gotor_link(raw_link, page_index, link_id, bounds)
            elif link_kind == fitz.LINK_NAMED:
                return self._parse_named_link(raw_link, page_index, link_id, bounds)
            else:
                return self._parse_unknown_link(raw_link, page_index, link_id, bounds)

        except Exception as e:
            print(f"❌ Error parsing link {link_index} on page {page_index}: {e}")
            return None

    def _parse_goto_link(self, raw_link: dict, page_index: int, link_id: str, bounds: QRectF) -> PDFLink:
        """Parse internal page navigation link"""
        target_page = raw_link.get('page', 0)
        target_coords = raw_link.get('to', [])

        target = {
            'page': target_page,
            'x': target_coords[0] if len(target_coords) > 0 else 72.0,
            'y': target_coords[1] if len(target_coords) > 1 else 720.0
        }

        description = f"Go to page {target_page + 1}"
        if len(target_coords) >= 2:
            description += f" at ({target['x']:.1f}, {target['y']:.1f})"

        return PDFLink(
            id=link_id,
            link_type=LinkType.GOTO,
            bounds=bounds,
            page_index=page_index,
            description=description,
            target=target,
            raw_link=raw_link
        )

    def _parse_uri_link(self, raw_link: dict, page_index: int, link_id: str, bounds: QRectF) -> PDFLink:
        """Parse external URL link"""
        uri = raw_link.get('uri', '')

        # Clean and validate URI
        if not uri.startswith(('http://', 'https://', 'mailto:', 'ftp://')):
            if '.' in uri and not uri.startswith('www.'):
                uri = 'http://' + uri

        target = {'url': uri}
        description = f"External URL: {uri[:50]}{'...' if len(uri) > 50 else ''}"

        return PDFLink(
            id=link_id,
            link_type=LinkType.URI,
            bounds=bounds,
            page_index=page_index,
            description=description,
            target=target,
            raw_link=raw_link
        )

    def _parse_launch_link(self, raw_link: dict, page_index: int, link_id: str, bounds: QRectF) -> PDFLink:
        """Parse file launch link"""
        file_path = raw_link.get('file', '')

        target = {'file_path': file_path}
        description = f"Launch file: {os.path.basename(file_path)}"

        return PDFLink(
            id=link_id,
            link_type=LinkType.LAUNCH,
            bounds=bounds,
            page_index=page_index,
            description=description,
            target=target,
            raw_link=raw_link
        )

    def _parse_gotor_link(self, raw_link: dict, page_index: int, link_id: str, bounds: QRectF) -> PDFLink:
        """Parse external document link"""
        file_path = raw_link.get('file', '')
        target_page = raw_link.get('page', 0)

        target = {
            'file_path': file_path,
            'page': target_page
        }

        filename = os.path.basename(file_path)
        description = f"External doc: {filename} (page {target_page + 1})"

        return PDFLink(
            id=link_id,
            link_type=LinkType.GOTOR,
            bounds=bounds,
            page_index=page_index,
            description=description,
            target=target,
            raw_link=raw_link
        )

    def _parse_named_link(self, raw_link: dict, page_index: int, link_id: str, bounds: QRectF) -> PDFLink:
        """Parse named destination link"""
        name = raw_link.get('name', '')

        # Try to resolve named destination
        resolved_target = self._resolve_named_destination(name)

        target = {
            'name': name,
            'resolved': resolved_target
        }

        description = f"Named destination: {name}"
        if resolved_target:
            description += f" → Page {resolved_target.get('page', 0) + 1}"

        return PDFLink(
            id=link_id,
            link_type=LinkType.NAMED,
            bounds=bounds,
            page_index=page_index,
            description=description,
            target=target,
            raw_link=raw_link
        )

    def _parse_unknown_link(self, raw_link: dict, page_index: int, link_id: str, bounds: QRectF) -> PDFLink:
        """Parse unknown link type"""
        link_kind = raw_link.get('kind', -1)

        target = {'raw_data': str(raw_link)}
        description = f"Unknown link type ({link_kind})"

        return PDFLink(
            id=link_id,
            link_type=LinkType.UNKNOWN,
            bounds=bounds,
            page_index=page_index,
            description=description,
            target=target,
            raw_link=raw_link
        )

    def _extract_named_destinations(self):
        """Extract all named destinations from the document - FIXED for custom PDFDocument"""
        # Get the actual PyMuPDF document object
        fitz_doc = None
        if hasattr(self.pdf_document, 'doc'):
            fitz_doc = self.pdf_document.doc  # Custom PDFDocument class
        elif hasattr(self.pdf_document, '__getitem__'):
            fitz_doc = self.pdf_document  # Direct PyMuPDF document

        if not fitz_doc:
            print("⚠️ Cannot access PyMuPDF document for named destinations")
            return

        try:
            # Method 1: Try to get named destinations directly
            if hasattr(fitz_doc, 'get_toc'):
                toc = fitz_doc.get_toc()
                for item in toc:
                    if len(item) >= 3:
                        title, page, dest = item[0], item[1], item[2] if len(item) > 2 else None
                        if dest and isinstance(dest, dict):
                            self.named_destinations[title] = dest

            # Method 2: Parse from document catalog (if available)
            # This would require more advanced PDF parsing

            print(f"📍 Extracted {len(self.named_destinations)} named destinations")

        except Exception as e:
            print(f"⚠️ Could not extract named destinations: {e}")

    def _resolve_named_destination(self, name: str) -> Optional[Dict[str, Any]]:
        """Resolve a named destination to page and coordinates - FIXED for custom PDFDocument"""
        if name in self.named_destinations:
            return self.named_destinations[name]

        # Get the actual PyMuPDF document object
        fitz_doc = None
        if hasattr(self.pdf_document, 'doc'):
            fitz_doc = self.pdf_document.doc  # Custom PDFDocument class
        elif hasattr(self.pdf_document, '__getitem__'):
            fitz_doc = self.pdf_document  # Direct PyMuPDF document

        # Try document resolution if available
        if fitz_doc and hasattr(fitz_doc, 'resolve_dest'):
            try:
                dest = fitz_doc.resolve_dest(name)
                if dest:
                    resolved = {
                        'page': dest.get('page', 0),
                        'x': dest.get('to', [72.0])[0] if dest.get('to') else 72.0,
                        'y': dest.get('to', [72.0, 720.0])[1] if len(dest.get('to', [])) > 1 else 720.0
                    }
                    # Cache the result
                    self.named_destinations[name] = resolved
                    return resolved
            except:
                pass

        return None

    def _manage_cache_size(self):
        """Manage link cache size to prevent memory issues"""
        if len(self.page_links_cache) > self.max_cache_size:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self.page_links_cache.keys())[:-self.max_cache_size//2]
            for key in keys_to_remove:
                del self.page_links_cache[key]

    def handle_link_click(self, pdf_link: PDFLink) -> bool:
        """Handle a link click and perform appropriate action"""
        try:
            print(f"🔗 Handling link click: {pdf_link.description}")

            if pdf_link.link_type == LinkType.GOTO:
                return self._handle_goto_link(pdf_link)
            elif pdf_link.link_type == LinkType.URI:
                return self._handle_uri_link(pdf_link)
            elif pdf_link.link_type == LinkType.LAUNCH:
                return self._handle_launch_link(pdf_link)
            elif pdf_link.link_type == LinkType.GOTOR:
                return self._handle_gotor_link(pdf_link)
            elif pdf_link.link_type == LinkType.NAMED:
                return self._handle_named_link(pdf_link)
            else:
                print(f"⚠️ Unknown link type: {pdf_link.link_type}")
                return False

        except Exception as e:
            print(f"❌ Error handling link click: {e}")
            return False

    def _handle_goto_link(self, pdf_link: PDFLink) -> bool:
        """Handle internal page navigation - FIXED for custom PDFDocument"""
        target = pdf_link.target
        page = target.get('page', 0)
        x = target.get('x', 72.0)
        y = target.get('y', 720.0)

        # Validate page number - handle both document types
        max_pages = 0
        if hasattr(self.pdf_document, 'get_page_count'):
            max_pages = self.pdf_document.get_page_count()
        elif hasattr(self.pdf_document, 'doc') and self.pdf_document.doc:
            max_pages = len(self.pdf_document.doc)
        elif self.pdf_document and hasattr(self.pdf_document, '__len__'):
            max_pages = len(self.pdf_document)

        if 0 <= page < max_pages:
            self.navigationRequested.emit(page, x, y)
            print(f"📄 Navigating to page {page + 1} at ({x:.1f}, {y:.1f})")
            return True
        else:
            print(f"❌ Invalid page number: {page} (max: {max_pages})")
            return False

    def _handle_uri_link(self, pdf_link: PDFLink) -> bool:
        """Handle external URL link"""
        if not self.allow_external_urls:
            print("🚫 External URLs are disabled")
            return False

        url = pdf_link.target.get('url', '')

        if self.confirm_external_actions:
            # Emit signal for UI confirmation
            self.externalUrlRequested.emit(url)
        else:
            # Open directly
            self._open_external_url(url)

        return True

    def _handle_launch_link(self, pdf_link: PDFLink) -> bool:
        """Handle file launch link"""
        if not self.allow_file_launch:
            print("🚫 File launch is disabled")
            return False

        file_path = pdf_link.target.get('file_path', '')

        # Security check
        if not self._is_safe_file_path(file_path):
            print(f"🚫 File path not allowed: {file_path}")
            return False

        return self._launch_file(file_path)

    def _handle_gotor_link(self, pdf_link: PDFLink) -> bool:
        """Handle external document link"""
        file_path = pdf_link.target.get('file_path', '')
        page = pdf_link.target.get('page', 0)

        if self.confirm_external_actions:
            # Emit signal for UI confirmation
            self.externalFileRequested.emit(file_path, page)
        else:
            # Open directly
            self._open_external_document(file_path, page)

        return True

    def _handle_named_link(self, pdf_link: PDFLink) -> bool:
        """Handle named destination link"""
        resolved = pdf_link.target.get('resolved')

        if resolved:
            page = resolved.get('page', 0)
            x = resolved.get('x', 72.0)
            y = resolved.get('y', 720.0)

            self.navigationRequested.emit(page, x, y)
            print(f"📍 Navigating to named destination: {pdf_link.target.get('name')}")
            return True
        else:
            print(f"❌ Could not resolve named destination: {pdf_link.target.get('name')}")
            return False

    def _open_external_url(self, url: str):
        """Open external URL in default browser"""
        try:
            webbrowser.open(url)
            print(f"🌐 Opened URL: {url}")
        except Exception as e:
            print(f"❌ Error opening URL: {e}")

    def _launch_file(self, file_path: str) -> bool:
        """Launch external file"""
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux and others
                subprocess.run(['xdg-open', file_path])

            print(f"📁 Launched file: {file_path}")
            return True

        except Exception as e:
            print(f"❌ Error launching file: {e}")
            return False

    def _open_external_document(self, file_path: str, page: int = 0):
        """Open external PDF document at specific page"""
        try:
            # For now, just launch the file
            # Advanced implementations could try to open at specific page
            self._launch_file(file_path)
            print(f"📚 Opened external document: {file_path} (page {page + 1})")
        except Exception as e:
            print(f"❌ Error opening external document: {e}")

    def _is_safe_file_path(self, file_path: str) -> bool:
        """Check if file path is safe to launch"""
        if not file_path:
            return False

        # Block potentially dangerous extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js']
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in dangerous_extensions:
            return False

        # Allow common document types
        safe_extensions = ['.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                          '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']

        return file_ext in safe_extensions

    def get_all_page_links(self) -> Dict[int, List[PDFLink]]:
        """Get links for all pages (cached or extract) - FIXED for custom PDFDocument"""
        all_links = {}

        # Get page count - handle both document types
        page_count = 0
        if hasattr(self.pdf_document, 'get_page_count'):
            page_count = self.pdf_document.get_page_count()
        elif hasattr(self.pdf_document, 'doc') and self.pdf_document.doc:
            page_count = len(self.pdf_document.doc)
        elif self.pdf_document and hasattr(self.pdf_document, '__len__'):
            page_count = len(self.pdf_document)

        if page_count == 0:
            return all_links

        for page_index in range(page_count):
            all_links[page_index] = self.extract_page_links(page_index)

        return all_links

    def clear_cache(self):
        """Clear all cached links"""
        self.page_links_cache.clear()
        print("🧹 Link cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about current cache state"""
        return {
            'cached_pages': len(self.page_links_cache),
            'total_cached_links': sum(len(links) for links in self.page_links_cache.values()),
            'named_destinations': len(self.named_destinations),
            'max_cache_size': self.max_cache_size
        }


# Example usage and testing
if __name__ == '__main__':
    import sys

    def test_link_manager():
        """Test the link manager with a sample PDF"""
        if len(sys.argv) != 2:
            print("Usage: python a_pdf_link_manager.py <pdf_file>")
            return

        pdf_path = sys.argv[1]

        # Create link manager
        link_manager = PDFLinkManager()

        # Open PDF
        try:
            doc = fitz.open(pdf_path)
            link_manager.set_pdf_document(doc, pdf_path)

            # Extract links from first few pages
            for page_index in range(min(3, len(doc))):
                links = link_manager.extract_page_links(page_index)
                print(f"\n📄 Page {page_index + 1}:")
                for link in links:
                    print(f"  🔗 {link.description}")
                    print(f"     Type: {link.link_type.value}")
                    print(f"     Bounds: ({link.bounds.x():.1f}, {link.bounds.y():.1f}, "
                          f"{link.bounds.width():.1f}, {link.bounds.height():.1f})")

            # Show cache info
            cache_info = link_manager.get_cache_info()
            print(f"\n📊 Cache Info: {cache_info}")

        except Exception as e:
            print(f"❌ Error: {e}")

    test_link_manager()