#!/usr/bin/env python3
"""
TOC Navigation System - File Organization Guide
Recommended placement for each class following clean architecture
"""

# ============================================================================
# src/models/toc_entry.py
# ============================================================================
"""
Data model classes - pure data structures with no UI dependencies
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TOCEntry:
    """
    Data model for a table of contents entry
    Location: src/models/toc_entry.py

    Pure data structure - no UI or business logic dependencies
    """
    title: str
    page: int  # 0-based page index
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
        """Get formatted title for display"""
        return f"{self.title} (page {self.page + 1})"

    def __str__(self):
        indent = "  " * self.level
        return f"{indent}{self.title} (page {self.page + 1})"
