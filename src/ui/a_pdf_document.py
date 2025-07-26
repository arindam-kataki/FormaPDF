from typing import List
from PyQt6.QtCore import QSizeF
from PyQt6.QtGui import QPixmap
import fitz  # PyMuPDF

class PDFDocument:
    """Direct PDF document handling using PyMuPDF"""

    def __init__(self, file_path: str):
        self.doc = fitz.open(file_path)
        self.file_path = file_path

    def get_page_count(self) -> int:
        """Return total number of pages"""
        return len(self.doc)

    def get_page_size(self, page_index: int) -> QSizeF:
        """Get page size in points (PDF native units)"""
        page = self.doc[page_index]
        rect = page.rect
        return QSizeF(rect.width, rect.height)

    def get_all_page_sizes(self) -> List[QSizeF]:
        """Get all page sizes in points"""
        sizes = []
        for i in range(len(self.doc)):
            sizes.append(self.get_page_size(i))
        return sizes

    def render_page(self, page_index: int, zoom: float, render_dpi: int = 150) -> QPixmap:
        """Render entire page at given zoom and DPI"""
        page = self.doc[page_index]
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, dpi=render_dpi)

        # Convert to QPixmap
        img_data = pix.tobytes("ppm")
        qimg = QPixmap()
        qimg.loadFromData(img_data)
        return qimg

    def render_page_region(self, page_index: int, x_points: float, y_points: float,
                           w_points: float, h_points: float, zoom: float,
                           render_dpi: int = 150) -> QPixmap:
        """Render specific region of page in points (document coordinates)"""
        page = self.doc[page_index]

        # Create clip rectangle in document coordinates (points)
        clip = fitz.Rect(x_points, y_points, x_points + w_points, y_points + h_points)
        matrix = fitz.Matrix(zoom, zoom)

        pix = page.get_pixmap(matrix=matrix, clip=clip, dpi=render_dpi)

        # Convert to QPixmap
        img_data = pix.tobytes("ppm")
        qimg = QPixmap()
        qimg.loadFromData(img_data)
        return qimg

    def get_page_text(self, page_index: int) -> str:
        """Get text content from page"""
        page = self.doc[page_index]
        return page.get_text()

    def get_page_links(self, page_index: int) -> List[dict]:
        """Get links from page"""
        page = self.doc[page_index]
        return page.get_links()

    def get_page_annotations(self, page_index: int) -> List:
        """Get annotations from page"""
        page = self.doc[page_index]
        return [annot for annot in page.annots()]

    def get_page_form_fields(self, page_index: int) -> List[dict]:
        """Get form fields from page"""
        page = self.doc[page_index]
        widgets = page.widgets()
        fields = []

        for widget in widgets:
            field_info = {
                'name': widget.field_name,
                'type': widget.field_type_string,
                'rect': widget.rect,  # Already in points
                'value': widget.field_value,
                'page': page_index
            }
            fields.append(field_info)

        return fields

    def close(self):
        """Clean up document resources"""
        if self.doc:
            self.doc.close()
            self.doc = None

    def __del__(self):
        """Ensure document is closed on cleanup"""
        self.close()