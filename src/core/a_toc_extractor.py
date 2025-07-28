"""
Business logic for TOC extraction and management - FIXED VERSION
"""

from typing import List, Dict, Optional, Any
import time
from ..models.a_toc_entry import TOCEntry
import fitz  # PyMuPDF


class TOCExtractor:
    """
    FIXED TOC Extractor with proper page number validation and timing
    """

    def __init__(self, pdf_document):
        self.pdf_document = pdf_document
        self.last_extraction_time = 0.0

    def extract_toc(self) -> List[TOCEntry]:
        """Extract TOC with page number validation and timing"""

        start_time = time.time()

        if not self.pdf_document or not hasattr(self.pdf_document, 'doc'):
            self.last_extraction_time = time.time() - start_time
            return []

        try:
            # Get raw TOC data
            pdf_read_start = time.time()
            toc_data = self.pdf_document.doc.get_toc(simple=True)  # Use simple=True for speed
            pdf_read_time = time.time() - pdf_read_start

            print(f"🚀 PDF TOC read time: {pdf_read_time:.3f}s")

            if not toc_data:
                self.last_extraction_time = time.time() - start_time
                print(f"🕒 Total extraction time (no TOC): {self.last_extraction_time:.3f}s")
                return []

            # CRITICAL FIX: Get actual page count for validation
            total_pages = len(self.pdf_document.doc)
            print(f"📊 PDF has {total_pages} pages total (0-based: 0-{total_pages-1})")

            conversion_start = time.time()
            entries = []
            entry_stack = []
            invalid_pages = 0
            processed_count = 0

            for i, toc_item in enumerate(toc_data):
                # Progress for large TOCs
                if i > 0 and i % 100 == 0:
                    print(f"📊 Processed {i}/{len(toc_data)} TOC entries...")

                level = toc_item[0] - 1  # Convert to 0-based
                title = toc_item[1].strip()
                raw_page_info = toc_item[2]

                # CRITICAL FIX: Validate and correct page numbers
                raw_page_num, dest_type, coords = self._parse_destination_safe(raw_page_info)

                # PyMuPDF sometimes returns incorrect page numbers - validate against actual PDF
                if raw_page_num >= total_pages:
                    print(f"⚠️  TOC entry '{title}' points to page {raw_page_num + 1}, but PDF only has {total_pages} pages")
                    corrected_page = min(raw_page_num, total_pages - 1)
                    print(f"    → Correcting to page {corrected_page + 1}")
                    invalid_pages += 1
                else:
                    corrected_page = raw_page_num

                # Ensure page is never negative
                final_page = max(0, corrected_page)

                # Debug output for first few entries
                if i < 5:
                    print(f"📖 TOC Entry {i+1}: '{title}' → Page {final_page + 1} (0-based: {final_page})")

                entry = TOCEntry(
                    title=title,
                    page=final_page,  # Always 0-based internally
                    level=level,
                    dest_type=dest_type,
                    coordinates=coords
                )

                # Handle nesting efficiently
                if level == 0:
                    entries.append(entry)
                    entry_stack = [entry]
                else:
                    # Trim stack efficiently
                    if len(entry_stack) > level:
                        entry_stack = entry_stack[:level]

                    if entry_stack:
                        entry_stack[-1].add_child(entry)
                        entry_stack.append(entry)
                    else:
                        # Fallback - treat as top level
                        entries.append(entry)
                        entry_stack = [entry]

                processed_count += 1

            conversion_time = time.time() - conversion_start
            self.last_extraction_time = time.time() - start_time

            # Summary output
            if invalid_pages > 0:
                print(f"⚠️  FIXED {invalid_pages} invalid page references in TOC")

            print(f"🚀 TOC conversion time: {conversion_time:.3f}s")
            print(f"🚀 Total extraction time: {self.last_extraction_time:.3f}s")
            print(f"✅ TOC extraction complete: {len(entries)} top-level entries, {processed_count} total entries")
            print(f"🚀 Performance: {processed_count / self.last_extraction_time:.0f} entries/second")

            return entries

        except Exception as e:
            self.last_extraction_time = time.time() - start_time
            print(f"❌ Error extracting TOC: {e}")
            print(f"🕒 Failed extraction time: {self.last_extraction_time:.3f}s")
            return []

    def _parse_destination_safe(self, dest_info) -> tuple:
        """FIXED safe destination parsing with bounds checking"""
        try:
            if isinstance(dest_info, dict):
                page_num = dest_info.get('page', 0)
                return max(0, page_num), 'page', (0, 0)

            elif isinstance(dest_info, (list, tuple)) and dest_info:
                page_num = int(dest_info[0]) if dest_info[0] is not None else 0
                coords = (0, 0)
                if len(dest_info) >= 3:
                    try:
                        coords = (float(dest_info[1] or 0), float(dest_info[2] or 0))
                    except (ValueError, TypeError):
                        pass
                return max(0, page_num), 'page', coords

            elif isinstance(dest_info, (int, float)):
                return max(0, int(dest_info)), 'page', (0, 0)

            else:
                return 0, 'page', (0, 0)

        except Exception:
            return 0, 'page', (0, 0)

    def get_last_extraction_time(self) -> float:
        """Get the time taken for the last extraction"""
        return self.last_extraction_time

    def get_performance_stats(self) -> dict:
        """Get performance statistics"""
        return {
            'last_time': self.last_extraction_time,
            'entries_per_second': 0 if self.last_extraction_time == 0 else len(self.toc_entries) / self.last_extraction_time
        }

    # Optional: Debug method to test specific PDF
    def debug_toc_pages(self):
        """Debug method to check all TOC page numbers"""
        if not self.pdf_document:
            return

        print(f"\n🔍 DEBUGGING TOC PAGE NUMBERS:")
        raw_toc = self.pdf_document.doc.get_toc()
        total_pages = len(self.pdf_document.doc)

        for i, entry in enumerate(raw_toc[:20]):  # First 20 entries
            level, title, dest = entry
            if isinstance(dest, (list, tuple)) and dest:
                page_num = dest[0] if dest[0] is not None else 0
                status = "✅ Valid" if page_num < total_pages else "❌ INVALID"
                print(f"  {i+1:2d}. '{title[:30]}...' → Page {page_num+1} ({status})")

        print(f"📄 PDF has {total_pages} pages (valid range: 1-{total_pages})\n")