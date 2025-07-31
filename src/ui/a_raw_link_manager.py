"""
Raw Link Manager - Ultra-Fast Implementation
Caches raw PyMuPDF link data and parses only on click for maximum performance
"""

import fitz  # PyMuPDF
import time
import webbrowser
import os
import subprocess
import platform
from typing import List, Dict, Any, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QRectF, QPointF
from enum import Enum


class LinkType(Enum):
    """PDF link types"""
    GOTO = "goto"
    URI = "uri"
    LAUNCH = "launch"
    GOTOR = "gotor"
    NAMED = "named"
    UNKNOWN = "unknown"


class RawLinkManager(QObject):
    """
    Ultra-fast link manager that caches raw PyMuPDF data
    Parses link details only when clicked for maximum performance
    """

    # Signals
    navigationRequested = pyqtSignal(int, float, float)  # page, x, y
    externalUrlRequested = pyqtSignal(str)  # url
    externalFileRequested = pyqtSignal(str, int)  # file_path, page
    rawLinksExtracted = pyqtSignal(int, list)  # page_index, raw_links

    def __init__(self, parent=None):
        super().__init__(parent)

        # Core state
        self.pdf_document = None
        self.document_path = ""

        # Raw link cache - stores PyMuPDF data directly
        self.raw_links_cache = {}  # page_index -> List[dict]
        self.parsed_cache = {}  # (page_index, link_index) -> parsed_data

        # Performance tracking
        self.timing_stats = {
            'raw_extraction_times': [],
            'parse_on_click_times': [],
            'total_links_extracted': 0
        }

        # Settings
        self.allow_external_urls = True
        self.allow_file_launch = True
        self.confirm_external_actions = True
        self.max_cache_size = 100  # Max cached pages

        print("🚀 RawLinkManager initialized (ultra-fast mode)")

    def set_pdf_document(self, pdf_document, document_path: str = ""):
        """Set PDF document and clear caches"""
        try:
            self.pdf_document = pdf_document
            self.document_path = document_path

            # Clear all caches
            self.raw_links_cache.clear()
            self.parsed_cache.clear()
            self.timing_stats['total_links_extracted'] = 0

            print(f"🔗 Raw link manager set for: {document_path}")

            if pdf_document:
                # Get page count
                if hasattr(pdf_document, 'get_page_count'):
                    page_count = pdf_document.get_page_count()
                elif hasattr(pdf_document, 'doc') and pdf_document.doc:
                    page_count = len(pdf_document.doc)
                else:
                    page_count = len(pdf_document) if hasattr(pdf_document, '__len__') else 0

                print(f"📖 Document ready: {page_count} pages")

        except Exception as e:
            print(f"❌ Error setting PDF document: {e}")

    def get_raw_page_links(self, page_index: int) -> List[dict]:
        """Get raw links for a page (cached or extracted) - FIXED for PDFDocument"""
        # Check cache first
        if page_index in self.raw_links_cache:
            cached_links = self.raw_links_cache[page_index]
            print(f"🔗 Page {page_index + 1}: {len(cached_links)} raw links (cached)")
            return cached_links

        if not self.pdf_document:
            print(f"❌ No PDF document loaded")
            return []

        try:
            start_time = time.perf_counter()

            # ✅ FIXED: Get the actual PyMuPDF document object
            fitz_doc = None
            if hasattr(self.pdf_document, 'doc'):
                fitz_doc = self.pdf_document.doc  # Custom PDFDocument class
            elif hasattr(self.pdf_document, '__getitem__'):
                fitz_doc = self.pdf_document  # Direct PyMuPDF document
            else:
                print(f"❌ Cannot access PyMuPDF document - unknown document type")
                return []

            if not fitz_doc:
                print(f"❌ Cannot access PyMuPDF document for page {page_index}")
                return []

            # Validate page index
            if page_index < 0 or page_index >= len(fitz_doc):
                print(f"❌ Invalid page index: {page_index} (document has {len(fitz_doc)} pages)")
                return []

            # ✅ FIXED: Use fitz_doc instead of self.pdf_document
            page = fitz_doc[page_index]
            raw_links = page.get_links()

            # Cache raw data
            self._manage_cache_size()
            self.raw_links_cache[page_index] = raw_links

            # Update stats
            extraction_time = time.perf_counter() - start_time
            self.timing_stats['raw_extraction_times'].append(extraction_time)
            self.timing_stats['total_links_extracted'] += len(raw_links)

            print(f"🔗 Page {page_index + 1}: {len(raw_links)} raw links - {extraction_time * 1000:.2f}ms")

            # ✅ ADD THIS: Emit signal for control panel
            self.rawLinksExtracted.emit(page_index, raw_links)

            return raw_links

        except Exception as e:
            print(f"❌ Error getting raw links for page {page_index}: {e}")
            import traceback
            traceback.print_exc()  # This will help debug the exact error
            return []

    # 5. OPTIONAL: Add this method for better debug integration
    def get_link_stats(self) -> Dict[str, Any]:
        """Get comprehensive link statistics"""
        stats = self.get_performance_stats()
        cache_info = self.get_cache_info()

        return {
            **stats,
            **cache_info,
            'extraction_count': len(self.timing_stats['raw_extraction_times']),
            'parse_count': len(self.timing_stats['parse_on_click_times']),
            'cache_hit_ratio': self._calculate_cache_hit_ratio()
        }

    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        # This is a simple estimation
        total_requests = len(self.timing_stats['raw_extraction_times'])
        if total_requests == 0:
            return 0.0

        # Estimate cache hits (this is approximate)
        cache_hits = max(0, total_requests - len(self.raw_links_cache))
        return cache_hits / total_requests if total_requests > 0 else 0.0

    def get_link_bounds(self, raw_link: dict) -> QRectF:
        """Extract bounds from raw link - ultra-fast"""
        try:
            link_rect = raw_link['from']  # Direct access
            return QRectF(link_rect.x0, link_rect.y0, link_rect.width, link_rect.height)
        except (KeyError, AttributeError):
            return QRectF(0, 0, 0, 0)

    def get_basic_link_type(self, raw_link: dict) -> LinkType:
        """Get basic link type without full parsing"""
        try:
            link_kind = raw_link.get('kind', fitz.LINK_NONE)
            type_map = {
                fitz.LINK_GOTO: LinkType.GOTO,
                fitz.LINK_URI: LinkType.URI,
                fitz.LINK_LAUNCH: LinkType.LAUNCH,
                fitz.LINK_GOTOR: LinkType.GOTOR,
                fitz.LINK_NAMED: LinkType.NAMED
            }
            return type_map.get(link_kind, LinkType.UNKNOWN)
        except:
            return LinkType.UNKNOWN

    def handle_raw_link_click(self, raw_link: dict, page_index: int, link_index: int) -> bool:
        """Handle click on raw link - parse only now"""

        start_time = time.perf_counter()

        try:
            # Check if already parsed
            cache_key = (page_index, link_index)
            if cache_key in self.parsed_cache:
                parsed_data = self.parsed_cache[cache_key]
            else:
                # Parse now for the first time
                parsed_data = self._parse_raw_link_on_demand(raw_link)
                self.parsed_cache[cache_key] = parsed_data

            # Execute action based on link type
            success = self._execute_link_action(parsed_data, raw_link)

            # Update timing stats
            parse_time = time.perf_counter() - start_time
            self.timing_stats['parse_on_click_times'].append(parse_time)

            print(f"🔗 Parsed and executed link in {parse_time * 1000:.2f}ms")
            return success

        except Exception as e:
            print(f"❌ Error handling raw link click: {e}")
            return False

    def _parse_raw_link_on_demand(self, raw_link: dict) -> dict:
        """Parse raw link details only when needed"""

        link_kind = raw_link.get('kind', fitz.LINK_NONE)

        if link_kind == fitz.LINK_GOTO:
            return {
                'type': LinkType.GOTO,
                'target_page': raw_link.get('page', 0),
                'target_x': raw_link.get('to', [72.0])[0] if raw_link.get('to') else 72.0,
                'target_y': raw_link.get('to', [72.0, 720.0])[1] if len(raw_link.get('to', [])) > 1 else 720.0,
                'description': f"Go to page {raw_link.get('page', 0) + 1}"
            }

        elif link_kind == fitz.LINK_URI:
            uri = raw_link.get('uri', '')
            # Clean URI if needed
            if not uri.startswith(('http://', 'https://', 'mailto:', 'ftp://')):
                if '.' in uri and not uri.startswith('www.'):
                    uri = 'http://' + uri

            return {
                'type': LinkType.URI,
                'url': uri,
                'description': f"External URL: {uri[:50]}{'...' if len(uri) > 50 else ''}"
            }

        elif link_kind == fitz.LINK_LAUNCH:
            file_path = raw_link.get('file', '')
            return {
                'type': LinkType.LAUNCH,
                'file_path': file_path,
                'description': f"Launch file: {os.path.basename(file_path)}"
            }

        elif link_kind == fitz.LINK_GOTOR:
            file_path = raw_link.get('file', '')
            target_page = raw_link.get('page', 0)
            return {
                'type': LinkType.GOTOR,
                'file_path': file_path,
                'target_page': target_page,
                'description': f"External doc: {os.path.basename(file_path)} (page {target_page + 1})"
            }

        elif link_kind == fitz.LINK_NAMED:
            name = raw_link.get('name', '')
            return {
                'type': LinkType.NAMED,
                'name': name,
                'description': f"Named destination: {name}"
            }

        else:
            return {
                'type': LinkType.UNKNOWN,
                'description': f"Unknown link type ({link_kind})"
            }

    def _execute_link_action(self, parsed_data: dict, raw_link: dict) -> bool:
        """Execute the parsed link action"""

        link_type = parsed_data['type']

        if link_type == LinkType.GOTO:
            page = parsed_data['target_page']
            x = parsed_data['target_x']
            y = parsed_data['target_y']

            # Validate page number
            max_pages = 0
            if hasattr(self.pdf_document, 'get_page_count'):
                max_pages = self.pdf_document.get_page_count()
            elif hasattr(self.pdf_document, 'doc') and self.pdf_document.doc:
                max_pages = len(self.pdf_document.doc)

            if 0 <= page < max_pages:
                self.navigationRequested.emit(page, x, y)
                print(f"📄 Navigating to page {page + 1} at ({x:.1f}, {y:.1f})")
                return True
            else:
                print(f"❌ Invalid page number: {page}")
                return False

        elif link_type == LinkType.URI:
            if not self.allow_external_urls:
                print("🚫 External URLs are disabled")
                return False

            url = parsed_data['url']
            if self.confirm_external_actions:
                self.externalUrlRequested.emit(url)
            else:
                self._open_external_url(url)
            return True

        elif link_type == LinkType.LAUNCH:
            if not self.allow_file_launch:
                print("🚫 File launch is disabled")
                return False

            file_path = parsed_data['file_path']
            if self._is_safe_file_path(file_path):
                return self._launch_file(file_path)
            else:
                print(f"🚫 File path not allowed: {file_path}")
                return False

        elif link_type == LinkType.GOTOR:
            file_path = parsed_data['file_path']
            page = parsed_data['target_page']

            if self.confirm_external_actions:
                self.externalFileRequested.emit(file_path, page)
            else:
                self._open_external_document(file_path, page)
            return True

        elif link_type == LinkType.NAMED:
            # Try to resolve named destination
            name = parsed_data['name']
            resolved = self._resolve_named_destination(name, raw_link)
            if resolved:
                self.navigationRequested.emit(resolved['page'], resolved['x'], resolved['y'])
                print(f"📍 Navigating to named destination: {name}")
                return True
            else:
                print(f"❌ Could not resolve named destination: {name}")
                return False

        else:
            print(f"⚠️ Unknown link type: {link_type}")
            return False

    def _resolve_named_destination(self, name: str, raw_link: dict) -> Optional[dict]:
        """Try to resolve named destination"""
        # This could be enhanced with more sophisticated resolution
        # For now, just return None to indicate unresolved
        return None

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

    def _manage_cache_size(self):
        """Manage cache size to prevent memory issues"""
        if len(self.raw_links_cache) > self.max_cache_size:
            # Remove oldest entries
            keys_to_remove = list(self.raw_links_cache.keys())[:-self.max_cache_size // 2]
            for key in keys_to_remove:
                del self.raw_links_cache[key]

    def clear_cache(self):
        """Clear all caches"""
        self.raw_links_cache.clear()
        self.parsed_cache.clear()
        print("🧹 Raw link caches cleared")

    def get_performance_stats(self) -> dict:
        """Get performance statistics"""
        stats = self.timing_stats.copy()

        if stats['raw_extraction_times']:
            stats['avg_extraction_time'] = sum(stats['raw_extraction_times']) / len(stats['raw_extraction_times'])
            stats['total_extraction_time'] = sum(stats['raw_extraction_times'])

        if stats['parse_on_click_times']:
            stats['avg_parse_time'] = sum(stats['parse_on_click_times']) / len(stats['parse_on_click_times'])
            stats['total_parse_time'] = sum(stats['parse_on_click_times'])

        stats['cached_pages'] = len(self.raw_links_cache)
        stats['parsed_links'] = len(self.parsed_cache)

        return stats

    def print_performance_report(self):
        """Print detailed performance report"""
        stats = self.get_performance_stats()

        print("\n📊 Raw Link Manager Performance Report:")
        print("=" * 50)
        print(f"Total links extracted: {stats['total_links_extracted']}")
        print(f"Cached pages: {stats['cached_pages']}")
        print(f"Parsed links: {stats['parsed_links']}")

        if 'avg_extraction_time' in stats:
            print(f"Avg extraction time: {stats['avg_extraction_time'] * 1000:.2f}ms")
            print(f"Total extraction time: {stats['total_extraction_time'] * 1000:.2f}ms")

        if 'avg_parse_time' in stats:
            print(f"Avg parse time: {stats['avg_parse_time'] * 1000:.2f}ms")
            print(f"Total parse time: {stats['total_parse_time'] * 1000:.2f}ms")

        if stats['total_links_extracted'] > 0:
            extraction_per_link = (stats.get('total_extraction_time', 0) / stats['total_links_extracted']) * 1000
            print(f"Time per link extraction: {extraction_per_link:.3f}ms")

        print("=" * 50)

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about current cache state"""
        total_cached_links = 0
        for page_links in self.raw_links_cache.values():
            total_cached_links += len(page_links)

        return {
            'cached_pages': len(self.raw_links_cache),
            'total_cached_links': total_cached_links,
            'named_destinations': 0,
            'max_cache_size': self.max_cache_size,
            'parsed_cache_size': len(self.parsed_cache)
        }

    def extract_page_links(self, page_index: int) -> List[dict]:
        """Extract page links - compatibility method"""
        return self.get_raw_page_links(page_index)

# Example usage
if __name__ == '__main__':
    import sys


    def test_raw_link_manager():
        """Test the raw link manager with a sample PDF"""
        if len(sys.argv) != 2:
            print("Usage: python raw_link_manager.py <pdf_file>")
            return

        pdf_path = sys.argv[1]

        # Create raw link manager
        link_manager = RawLinkManager()

        # Open PDF
        try:
            doc = fitz.open(pdf_path)
            link_manager.set_pdf_document(doc, pdf_path)

            # Test raw extraction speed
            for page_index in range(min(3, len(doc))):
                raw_links = link_manager.get_raw_page_links(page_index)
                print(f"📄 Page {page_index + 1}: {len(raw_links)} raw links")

                # Test click handling on first link
                if raw_links:
                    first_link = raw_links[0]
                    print(f"   Testing click on first link...")
                    link_manager.handle_raw_link_click(first_link, page_index, 0)

            # Show performance report
            link_manager.print_performance_report()

        except Exception as e:
            print(f"❌ Error: {e}")


    test_raw_link_manager()