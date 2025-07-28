#!/usr/bin/env python3
"""
TOC Navigation System - FIXED Data Model
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TOCEntry:
    """
    FIXED TOC Entry with consistent page display and internal storage
    """
    title: str
    page: int  # ALWAYS 0-based internally - this is the key fix!
    level: int = 0  # Nesting level (0 = top level)
    dest_type: str = "page"  # "page", "xyz", "fit", etc.
    coordinates: Tuple[float, float] = (0, 0)  # (x, y) on page
    children: List['TOCEntry'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def add_child(self, child: 'TOCEntry'):
        """Add a child entry"""
        self.children.append(child)
        child.level = self.level + 1

    def get_display_title(self) -> str:
        """
        FIXED: Get formatted title with CORRECT page display

        Key fix: Always show 1-based page numbers to user, even though
        we store 0-based internally
        """
        # Add level indicator for nested entries
        level_prefix = "  " * self.level if self.level > 0 else ""

        # Add child count for parent entries
        child_info = f" ({len(self.children)} items)" if self.children else ""

        # CRITICAL FIX: Always display 1-based page numbers to users
        # Internal storage is 0-based, but users expect 1-based display
        display_page = self.page + 1

        return f"{level_prefix}{self.title} → p.{display_page}{child_info}"

    def get_internal_page(self) -> int:
        """Get the internal 0-based page number"""
        return self.page

    def get_display_page(self) -> int:
        """Get the user-facing 1-based page number"""
        return self.page + 1

    def __str__(self):
        """String representation with proper page numbering"""
        indent = "  " * self.level
        display_page = self.page + 1  # Show 1-based to users
        return f"{indent}{self.title} (page {display_page})"

    def debug_info(self) -> str:
        """Debug information showing both internal and display page numbers"""
        return (f"TOCEntry(title='{self.title}', "
                f"internal_page={self.page}, "
                f"display_page={self.page + 1}, "
                f"level={self.level}, "
                f"coords={self.coordinates})")

    @classmethod
    def create_from_raw(cls, title: str, raw_page: int, level: int = 0,
                        dest_type: str = "page", coordinates: Tuple[float, float] = (0, 0)):
        """
        Create TOC entry from raw page number (handles conversion if needed)

        Args:
            title: Entry title
            raw_page: Page number (assumed to be 0-based from PyMuPDF)
            level: Nesting level
            dest_type: Destination type
            coordinates: Page coordinates
        """
        # Ensure we store 0-based internally
        internal_page = max(0, raw_page)  # Clamp to non-negative

        return cls(
            title=title.strip(),
            page=internal_page,  # Store 0-based
            level=level,
            dest_type=dest_type,
            coordinates=coordinates
        )