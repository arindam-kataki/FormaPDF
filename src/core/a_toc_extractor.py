"""
Business logic for TOC extraction and management
"""

from typing import List, Dict, Optional, Any
from ..models.a_toc_entry import TOCEntry
import fitz  # PyMuPDF


class TOCExtractor:
    """
    Core business logic for extracting TOC from PDF documents
    Location: src/core/toc_extractor.py

    Pure business logic - no UI dependencies
    """

    def __init__(self, pdf_document):
        self.pdf_document = pdf_document

    def extract_toc(self) -> List[TOCEntry]:
        """Extract table of contents from PDF document"""

        if not self.pdf_document or not hasattr(self.pdf_document, 'doc'):
            return []

        try:
            # Get TOC from PyMuPDF
            toc_data = self.pdf_document.doc.get_toc(simple=False)

            if not toc_data:
                return []

            # Convert to our TOC structure
            entries = []
            entry_stack = []  # Stack for nesting

            for toc_item in toc_data:
                level = toc_item[0] - 1  # Convert to 0-based
                title = toc_item[1]
                page_info = toc_item[2]

                # Parse destination
                page_num, dest_type, coords = self._parse_destination(page_info)

                # Create entry
                entry = TOCEntry(
                    title=title.strip(),
                    page=page_num,
                    level=level,
                    dest_type=dest_type,
                    coordinates=coords
                )

                # Handle nesting
                if level == 0:
                    entries.append(entry)
                    entry_stack = [entry]
                else:
                    # Find parent at correct level
                    while len(entry_stack) > level:
                        entry_stack.pop()

                    if entry_stack:
                        parent = entry_stack[-1]
                        parent.add_child(entry)
                        entry_stack.append(entry)
                    else:
                        # Fallback - treat as top level
                        entries.append(entry)
                        entry_stack = [entry]

            return entries

        except Exception as e:
            print(f"Error extracting TOC: {e}")
            return []

    def _parse_destination(self, dest_info) -> tuple:
        """Parse destination information from PyMuPDF - FIXED VERSION"""
        try:
            print(f"🔍 Parsing destination: {dest_info} (type: {type(dest_info)})")

            if isinstance(dest_info, dict):
                # Dictionary format
                page_num = dest_info.get('page', 0)
                dest_type = dest_info.get('to', '').split()[0] if dest_info.get('to') else 'page'

                # Extract coordinates
                to_parts = dest_info.get('to', '').split()
                if len(to_parts) >= 3:
                    try:
                        x = float(to_parts[1]) if to_parts[1] != 'null' else 0
                        y = float(to_parts[2]) if to_parts[2] != 'null' else 0
                        coordinates = (x, y)
                    except ValueError:
                        coordinates = (0, 0)
                else:
                    coordinates = (0, 0)

                print(f"📍 Dict format: page={page_num}, type={dest_type}, coords={coordinates}")
                return page_num, dest_type, coordinates

            elif isinstance(dest_info, (list, tuple)):
                # List/tuple format: [page, x, y, zoom] or [page]
                if len(dest_info) >= 1:
                    page_num = int(dest_info[0]) if dest_info[0] is not None else 0

                    # Extract coordinates if available
                    if len(dest_info) >= 3:
                        try:
                            x = float(dest_info[1]) if dest_info[1] is not None else 0
                            y = float(dest_info[2]) if dest_info[2] is not None else 0
                            coordinates = (x, y)
                        except (ValueError, TypeError):
                            coordinates = (0, 0)
                    else:
                        coordinates = (0, 0)

                    print(f"📍 List format: page={page_num}, coords={coordinates}")
                    return page_num, 'page', coordinates
                else:
                    print("📍 Empty list, defaulting to page 0")
                    return 0, 'page', (0, 0)

            elif isinstance(dest_info, (int, float)):
                # Simple page number
                page_num = int(dest_info)
                print(f"📍 Simple format: page={page_num}")
                return page_num, 'page', (0, 0)

            else:
                print(f"📍 Unknown format, defaulting to page 0")
                return 0, 'page', (0, 0)

        except Exception as e:
            print(f"❌ Error parsing destination: {e}")
            return 0, 'page', (0, 0)
