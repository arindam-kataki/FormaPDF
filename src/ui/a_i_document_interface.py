from abc import ABC, abstractmethod
from typing import List, Tuple
from PyQt6.QtCore import QSizeF
from PyQt6.QtGui import QPixmap

class DocumentInterface(ABC):
    """Abstract interface for document handling - DPI agnostic"""

    @abstractmethod
    def get_page_count(self) -> int:
        """Return total number of pages"""
        pass

    @abstractmethod
    def get_page_size(self, page_index: int) -> QSizeF:
        """Get page size in document units (points)"""
        pass

    @abstractmethod
    def get_all_page_sizes(self) -> List[QSizeF]:
        """Get all page sizes in document units (points)"""
        pass

    @abstractmethod
    def render_page(self, page_index: int, zoom: float, render_dpi: int = 150) -> QPixmap:
        """Render entire page at given zoom and DPI"""
        pass

    @abstractmethod
    def render_page_region(self, page_index: int, x_points: float, y_points: float,
                           w_points: float, h_points: float, zoom: float,
                           render_dpi: int = 150) -> QPixmap:
        """Render specific region of page in document units"""
        pass

    @abstractmethod
    def close(self):
        """Clean up document resources"""
        pass
