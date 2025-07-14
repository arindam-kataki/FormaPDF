from typing import Dict, List, Tuple, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class PageInfo:
    """Information about a single PDF page"""

    def __init__(self, page_num: int, width: int, height: int):
        self.page_num = page_num
        self.width = width
        self.height = height
        self.rotation = 0  # Future use

    def __str__(self):
        return f"Page {self.page_num + 1}: {self.width}x{self.height}"


class PageManager(QObject):
    """
    Manages PDF page information and coordinate systems
    Centralizes page-related operations separate from field management
    """

    # Signals for page events
    pages_loaded = pyqtSignal(int)  # Number of pages loaded
    page_dimensions_changed = pyqtSignal(int, int, int)  # page_num, width, height

    def __init__(self):
        super().__init__()

        # Core page storage
        self.pages: Dict[int, PageInfo] = {}
        self.page_count = 0

        # Coordinate conversion support
        self.zoom_level = 1.0
        self.page_spacing = 20  # Default spacing between pages
        self.page_margins = {'top': 15, 'bottom': 15, 'left': 15, 'right': 15}

        print("✅ PageManager initialized")

    # ==========================================
    # PAGE LOADING AND CACHING
    # ==========================================

    def load_pages_from_pdf(self, pdf_document) -> bool:
        """
        Load and cache page information from PDF document

        Args:
            pdf_document: PDF document object (e.g., from PyMuPDF/fitz)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not pdf_document:
                print("❌ No PDF document provided")
                return False

            self.clear_pages()

            print(f"📄 Loading page information for {pdf_document.page_count} pages...")

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                width = int(page.rect.width)
                height = int(page.rect.height)

                page_info = PageInfo(page_num, width, height)
                self.pages[page_num] = page_info

                print(f"  {page_info}")

            self.page_count = len(self.pages)
            self.pages_loaded.emit(self.page_count)

            print(f"✅ Successfully loaded {self.page_count} pages")
            return True

        except Exception as e:
            print(f"❌ Error loading pages from PDF: {e}")
            return False

    def clear_pages(self):
        """Clear all cached page information"""
        self.pages.clear()
        self.page_count = 0
        print("🧹 Cleared all page information")

    # ==========================================
    # PAGE DIMENSION QUERIES
    # ==========================================

    def get_page_dimensions(self, page_num: int) -> Tuple[int, int]:
        """
        Get dimensions for a specific page

        Args:
            page_num: Page number (0-based)

        Returns:
            tuple: (width, height) in points
        """
        try:
            if page_num in self.pages:
                page_info = self.pages[page_num]
                return page_info.width, page_info.height

            # Fallback for missing page
            print(f"⚠️ No dimensions cached for page {page_num}, using letter size")
            return 612, 792  # Standard letter size

        except Exception as e:
            print(f"❌ Error getting page dimensions: {e}")
            return 612, 792

    def get_all_page_dimensions(self) -> Dict[int, Tuple[int, int]]:
        """Get dimensions for all pages"""
        return {page_num: (info.width, info.height) for page_num, info in self.pages.items()}

    def get_page_info(self, page_num: int) -> Optional[PageInfo]:
        """Get complete page information"""
        return self.pages.get(page_num)

    def has_page(self, page_num: int) -> bool:
        """Check if page information exists"""
        return page_num in self.pages

    def get_largest_page_dimensions(self) -> Tuple[int, int]:
        """Get dimensions of the largest page (for canvas sizing)"""
        if not self.pages:
            return 612, 792

        max_width = max(page.width for page in self.pages.values())
        max_height = max(page.height for page in self.pages.values())
        return max_width, max_height

    # ==========================================
    # COORDINATE CONVERSION
    # ==========================================

    def set_zoom_level(self, zoom_level: float):
        """Update zoom level for coordinate conversions"""
        self.zoom_level = zoom_level
        print(f"🔍 PageManager zoom updated to {zoom_level:.2f}x")

    def document_to_screen_coords(self, page_num: int, doc_x: float, doc_y: float) -> Tuple[int, int]:
        """
        Convert document coordinates to screen coordinates

        Args:
            page_num: Page number
            doc_x, doc_y: Document coordinates (in points)

        Returns:
            tuple: (screen_x, screen_y) accounting for zoom and page layout
        """
        try:
            # Apply zoom to document coordinates
            screen_x = int(doc_x * self.zoom_level)
            screen_y = int(doc_y * self.zoom_level)

            # Add page offset if multi-page layout
            page_offset_y = self.get_page_offset_y(page_num)
            screen_y += page_offset_y

            # Add margins
            screen_x += self.page_margins['left']

            return screen_x, screen_y

        except Exception as e:
            print(f"❌ Error converting document to screen coords: {e}")
            return int(doc_x), int(doc_y)

    def screen_to_document_coords(self, page_num: int, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """
        Convert screen coordinates to document coordinates

        Args:
            page_num: Page number
            screen_x, screen_y: Screen coordinates

        Returns:
            tuple: (doc_x, doc_y) in points
        """
        try:
            # Remove margins
            adjusted_x = screen_x - self.page_margins['left']

            # Remove page offset
            page_offset_y = self.get_page_offset_y(page_num)
            adjusted_y = screen_y - page_offset_y

            # Remove zoom
            doc_x = adjusted_x / self.zoom_level
            doc_y = adjusted_y / self.zoom_level

            return doc_x, doc_y

        except Exception as e:
            print(f"❌ Error converting screen to document coords: {e}")
            return float(screen_x), float(screen_y)

    def get_page_offset_y(self, page_num: int) -> int:
        """Calculate Y offset for a page in multi-page layout"""
        try:
            if page_num == 0:
                return self.page_margins['top']

            total_offset = self.page_margins['top']

            # Add heights of all previous pages plus spacing
            for i in range(page_num):
                if i in self.pages:
                    page_height = int(self.pages[i].height * self.zoom_level)
                    total_offset += page_height + self.page_spacing
                else:
                    # Fallback for missing page info
                    total_offset += int(792 * self.zoom_level) + self.page_spacing

            return total_offset

        except Exception as e:
            print(f"❌ Error calculating page offset: {e}")
            return 0

    # ==========================================
    # VALIDATION SUPPORT
    # ==========================================

    def validate_position_within_page(self, page_num: int, x: float, y: float,
                                      width: float = 0, height: float = 0,
                                      margin: int = 10) -> Tuple[bool, str]:
        """
        Validate if position (and optional size) fits within page boundaries

        Args:
            page_num: Page number
            x, y: Position coordinates
            width, height: Size (0 means position-only check)
            margin: Minimum margin from page edges

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not self.has_page(page_num):
                return False, f"Page {page_num + 1} not found"

            page_width, page_height = self.get_page_dimensions(page_num)

            # Check position bounds
            if x < margin:
                return False, f"Position too close to left edge (margin: {margin}px)"

            if y < margin:
                return False, f"Position too close to top edge (margin: {margin}px)"

            # Check size bounds if provided
            if width > 0 and height > 0:
                right_edge = x + width
                bottom_edge = y + height

                if right_edge > (page_width - margin):
                    overflow = right_edge - (page_width - margin)
                    return False, f"Extends {overflow:.1f}px beyond right edge of page {page_num + 1}"

                if bottom_edge > (page_height - margin):
                    overflow = bottom_edge - (page_height - margin)
                    return False, f"Extends {overflow:.1f}px beyond bottom edge of page {page_num + 1}"

            return True, f"Position valid within page {page_num + 1} bounds"

        except Exception as e:
            return False, f"Error validating position: {e}"

    # ==========================================
    # DEBUG AND UTILITY
    # ==========================================

    def debug_print_all_pages(self):
        """Debug method to print all page information"""
        print("=== PAGE MANAGER DEBUG INFO ===")
        print(f"Total pages: {self.page_count}")
        print(f"Zoom level: {self.zoom_level:.2f}x")
        print(f"Page spacing: {self.page_spacing}px")
        print(f"Margins: {self.page_margins}")
        print("Page dimensions:")

        for page_num in sorted(self.pages.keys()):
            page_info = self.pages[page_num]
            offset_y = self.get_page_offset_y(page_num)
            print(f"  {page_info} (offset Y: {offset_y})")

        if not self.pages:
            print("  No pages loaded")

        print("==============================")

    def get_page_summary(self) -> Dict:
        """Get summary information about all pages"""
        if not self.pages:
            return {'page_count': 0, 'unique_sizes': [], 'total_height': 0}

        unique_sizes = set((page.width, page.height) for page in self.pages.values())
        total_height = sum(page.height for page in self.pages.values())

        return {
            'page_count': self.page_count,
            'unique_sizes': list(unique_sizes),
            'total_height': total_height,
            'largest_page': self.get_largest_page_dimensions(),
            'has_mixed_sizes': len(unique_sizes) > 1
        }

    def __str__(self):
        summary = self.get_page_summary()
        return f"PageManager(pages={summary['page_count']}, mixed_sizes={summary['has_mixed_sizes']})"