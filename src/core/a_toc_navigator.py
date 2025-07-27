from typing import Optional, List

from models.a_toc_entry import TOCEntry


class TOCNavigator:
    """
    Navigation logic for TOC entries
    Location: src/core/toc_extractor.py (same file as TOCExtractor)

    Business logic for TOC navigation without UI dependencies
    """

    def __init__(self, toc_entries: List[TOCEntry]):
        self.toc_entries = toc_entries
        self.flat_entries = self._flatten_entries(toc_entries)

    def _flatten_entries(self, entries: List[TOCEntry]) -> List[TOCEntry]:
        """Create flat list of all entries for easy searching"""
        flat = []
        for entry in entries:
            flat.append(entry)
            flat.extend(self._flatten_entries(entry.children))
        return flat

    def find_entry_by_page(self, page_num: int) -> Optional[TOCEntry]:
        """Find best matching TOC entry for given page"""
        best_match = None
        for entry in self.flat_entries:
            if entry.page <= page_num:
                if not best_match or entry.page > best_match.page:
                    best_match = entry
        return best_match

    def get_next_entry(self, current_page: int) -> Optional[TOCEntry]:
        """Get next TOC entry after current page"""
        for entry in self.flat_entries:
            if entry.page > current_page:
                return entry
        return None

    def get_previous_entry(self, current_page: int) -> Optional[TOCEntry]:
        """Get previous TOC entry before current page"""
        previous = None
        for entry in self.flat_entries:
            if entry.page >= current_page:
                break
            previous = entry
        return previous