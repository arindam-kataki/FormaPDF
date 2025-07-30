from typing import List
from PyQt6.QtCore import QSizeF
from PyQt6.QtGui import QPixmap
import fitz  # PyMuPDF


class PDFDocument:
    """Direct PDF document handling using PyMuPDF - all implementation here"""

    def __init__(self, file_path: str):
        self.doc = fitz.open(file_path)
        self.file_path = file_path
        self._page_cache = {}  # Cache for page objects

    def __len__(self) -> int:
        """Return page count for len() compatibility"""
        return self.get_page_count()

    def get_page_count(self) -> int:
        """Return total number of pages"""
        return len(self.doc)

    def get_page_size(self, page_index: int) -> QSizeF:
        """Get page size in points (PDF native units)"""
        page = self._get_page(page_index)
        if page:
            rect = page.rect
            return QSizeF(rect.width, rect.height)
        return QSizeF(612, 792)  # Default letter size

    def get_all_page_sizes(self) -> List[QSizeF]:
        """Get all page sizes in points"""
        sizes = []
        for i in range(self.get_page_count()):
            sizes.append(self.get_page_size(i))
        return sizes

    def render_page(self, page_index: int, zoom: float, render_dpi: int = 150) -> QPixmap:
        """Render entire page at given zoom and DPI"""
        page = self._get_page(page_index)
        if not page:
            return QPixmap()

        try:
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, dpi=render_dpi)

            # Convert to QPixmap
            img_data = pix.tobytes("ppm")
            qimg = QPixmap()
            qimg.loadFromData(img_data)
            return qimg
        except Exception as e:
            print(f"Error rendering page {page_index}: {e}")
            return QPixmap()

    def render_page_region(self, page_index: int, x_points: float, y_points: float,
                           w_points: float, h_points: float, zoom: float,
                           render_dpi: int = 150) -> QPixmap:
        """Render specific region of page in points (document coordinates)"""
        page = self._get_page(page_index)
        if not page:
            return QPixmap()

        try:
            # Create clip rectangle in document coordinates (points)
            clip = fitz.Rect(x_points, y_points, x_points + w_points, y_points + h_points)
            matrix = fitz.Matrix(zoom, zoom)

            pix = page.get_pixmap(matrix=matrix, clip=clip, dpi=render_dpi)

            # Convert to QPixmap
            img_data = pix.tobytes("ppm")
            qimg = QPixmap()
            qimg.loadFromData(img_data)
            return qimg
        except Exception as e:
            print(f"Error rendering page region {page_index}: {e}")
            return QPixmap()

    def get_page_text(self, page_index: int) -> str:
        """Get text content from page"""
        page = self._get_page(page_index)
        if page:
            try:
                return page.get_text()
            except Exception as e:
                print(f"Error getting page text {page_index}: {e}")
        return ""

    def get_page_text_blocks(self, page_index: int) -> List[dict]:
        """Get text blocks with position information"""
        page = self._get_page(page_index)
        if page:
            try:
                blocks = page.get_text("dict")["blocks"]
                text_blocks = []

                for block in blocks:
                    if "lines" in block:  # Text block
                        block_info = {
                            'bbox': block['bbox'],  # (x0, y0, x1, y1) in points
                            'text': '',
                            'lines': []
                        }

                        for line in block['lines']:
                            line_text = ''
                            for span in line['spans']:
                                line_text += span['text']
                            block_info['lines'].append(line_text)
                            block_info['text'] += line_text + '\n'

                        text_blocks.append(block_info)

                return text_blocks
            except Exception as e:
                print(f"Error getting page text blocks {page_index}: {e}")
        return []

    def get_page_links(self, page_index: int) -> List[dict]:
        """Get links from page"""
        page = self._get_page(page_index)
        if page:
            try:
                return page.get_links()
            except Exception as e:
                print(f"Error getting page links {page_index}: {e}")
        return []

    def get_page_annotations(self, page_index: int) -> List[dict]:
        """Get annotations from page"""
        page = self._get_page(page_index)
        if page:
            try:
                annotations = []
                for annot in page.annots():
                    annot_info = {
                        'type': annot.type[1],  # Annotation type name
                        'rect': tuple(annot.rect),  # (x0, y0, x1, y1) in points
                        'content': annot.content,
                        'author': annot.info.get('title', ''),
                        'page': page_index
                    }
                    annotations.append(annot_info)
                return annotations
            except Exception as e:
                print(f"Error getting page annotations {page_index}: {e}")
        return []

    def get_page_form_fields(self, page_index: int) -> List[dict]:
        """Get form fields from page"""
        page = self._get_page(page_index)
        if page:
            try:
                widgets = page.widgets()
                fields = []

                for widget in widgets:
                    field_info = {
                        'name': widget.field_name or f'field_{len(fields)}',
                        'type': widget.field_type_string,
                        'rect': tuple(widget.rect),  # Already in points (x0, y0, x1, y1)
                        'value': widget.field_value or '',
                        'page': page_index,
                        'field_type_code': widget.field_type,
                        'flags': widget.field_flags
                    }
                    fields.append(field_info)

                return fields
            except Exception as e:
                print(f"Error getting page form fields {page_index}: {e}")
        return []

    def search_text(self, search_term: str, page_index: int = None) -> List[dict]:
        """Search for text in document or specific page"""
        results = []

        if page_index is not None:
            # Search single page
            page = self._get_page(page_index)
            if page:
                results.extend(self._search_page(page, search_term, page_index))
        else:
            # Search all pages
            for i in range(self.get_page_count()):
                page = self._get_page(i)
                if page:
                    results.extend(self._search_page(page, search_term, i))

        return results

    def _search_page(self, page, search_term: str, page_index: int) -> List[dict]:
        """Search for text in a single page"""
        try:
            text_instances = page.search_for(search_term)
            results = []

            for rect in text_instances:
                result = {
                    'page': page_index,
                    'rect': tuple(rect),  # (x0, y0, x1, y1) in points
                    'text': search_term
                }
                results.append(result)

            return results
        except Exception as e:
            print(f"Error searching page {page_index}: {e}")
            return []

    def get_document_info(self) -> dict:
        """Get document metadata"""
        try:
            metadata = self.doc.metadata
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'page_count': self.get_page_count(),
                'file_path': self.file_path
            }
        except Exception as e:
            print(f"Error getting document info: {e}")
            return {'page_count': self.get_page_count(), 'file_path': self.file_path}

    def _get_page(self, page_index: int):
        """Get page object with caching"""
        if page_index < 0 or page_index >= len(self.doc):
            return None

        # Use simple direct access - PyMuPDF handles page caching internally
        try:
            return self.doc[page_index]
        except Exception as e:
            print(f"Error accessing page {page_index}: {e}")
            return None

    def close(self):
        """Clean up document resources"""
        if self.doc:
            try:
                self.doc.close()
            except Exception as e:
                print(f"Error closing document: {e}")
            finally:
                self.doc = None
                self._page_cache.clear()

    def is_valid(self) -> bool:
        """Check if document is valid and open"""
        return self.doc is not None and not self.doc.is_closed

    def __del__(self):
        """Ensure document is closed on cleanup"""
        self.close()

    def __str__(self):
        """String representation"""
        if self.is_valid():
            return f"PDFDocument({self.file_path}, {self.get_page_count()} pages)"
        return "PDFDocument(closed)"