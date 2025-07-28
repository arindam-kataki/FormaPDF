#!/usr/bin/env python3
"""
Standalone script to print TOC labels and page numbers
Usage: python print_toc.py your_pdf_file.pdf
"""

import fitz  # PyMuPDF
import sys
import os


def print_toc_labels_and_pages(pdf_path: str, max_entries: int = 50):
    """
    Print detailed TOC labels and page numbers from a PDF

    Args:
        pdf_path: Path to PDF file
        max_entries: Maximum number of entries to display
    """
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print(f"📖 OPENING: {pdf_path}")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        print(f"📄 PDF has {total_pages} pages")
        print("=" * 80)

        # Get TOC
        raw_toc = doc.get_toc()

        if not raw_toc:
            print("❌ No table of contents found in this PDF")
            doc.close()
            return

        print(f"📋 Found {len(raw_toc)} TOC entries")
        print(f"📝 Showing first {min(max_entries, len(raw_toc))} entries:")
        print("-" * 80)

        # Header
        print(f"{'#':<4} {'✓':<2} {'Level':<6} {'Page':<6} {'Title'}")
        print("-" * 80)

        for i, entry in enumerate(raw_toc[:max_entries]):
            level, title, dest = entry

            # Extract page number with detailed info
            if isinstance(dest, dict):
                page_num = dest.get('page', 0)
                dest_info = f"dict: {dest}"
            elif isinstance(dest, (list, tuple)) and dest:
                page_num = dest[0] if dest[0] is not None else 0
                if len(dest) >= 3:
                    dest_info = f"list: [page={dest[0]}, x={dest[1]}, y={dest[2]}]"
                else:
                    dest_info = f"list: {dest}"
            elif isinstance(dest, int):
                page_num = dest
                dest_info = f"int: {dest}"
            else:
                page_num = 0
                dest_info = f"unknown: {dest}"

            # Validation
            is_valid = 0 <= page_num < total_pages
            status = "✅" if is_valid else "❌"

            # Format title with indentation
            indent = "  " * (level - 1) if level > 0 else ""
            display_title = f"{indent}{title}"

            # Truncate long titles
            if len(display_title) > 50:
                display_title = display_title[:47] + "..."

            print(f"{i + 1:<4} {status:<2} {level:<6} {page_num + 1:<6} {display_title}")

            # Show destination details for problematic entries
            if not is_valid or i < 5:  # First 5 entries or invalid ones
                print(f"     {'':>2} {'':>6} {'':>6} └─ Raw dest: {dest_info}")
                if not is_valid:
                    print(
                        f"     {'':>2} {'':>6} {'':>6} └─ ⚠️  Page {page_num + 1} doesn't exist (PDF has {total_pages} pages)")

        if len(raw_toc) > max_entries:
            print(f"... ({len(raw_toc) - max_entries} more entries not shown)")

        print("-" * 80)

        # Summary
        invalid_count = sum(1 for _, _, dest in raw_toc
                            if (dest[0] if isinstance(dest, (list, tuple)) and dest
                                else dest if isinstance(dest, int)
        else dest.get('page', 0) if isinstance(dest, dict)
        else 0) >= total_pages)

        print(f"📊 SUMMARY:")
        print(f"   Total entries: {len(raw_toc)}")
        print(f"   Valid entries: {len(raw_toc) - invalid_count}")
        print(f"   Invalid entries: {invalid_count}")

        if invalid_count > 0:
            print(f"   ⚠️  {invalid_count} entries point to non-existent pages!")

        # Look for specific entries
        print(f"\n🔍 SEARCHING FOR SPECIFIC ENTRIES:")
        search_terms = ["binding", "contents", "index", "appendix", "chapter"]

        for term in search_terms:
            found = []
            for i, (level, title, dest) in enumerate(raw_toc):
                if term.lower() in title.lower():
                    if isinstance(dest, (list, tuple)) and dest:
                        page_num = dest[0] if dest[0] is not None else 0
                    elif isinstance(dest, int):
                        page_num = dest
                    else:
                        page_num = dest.get('page', 0) if isinstance(dest, dict) else 0

                    found.append((i + 1, title, page_num + 1))

            if found:
                print(f"   📖 '{term.title()}' entries:")
                for entry_num, title, page in found[:3]:  # First 3 matches
                    print(f"      #{entry_num}: '{title}' → Page {page}")

        doc.close()

    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("📖 TOC Label and Page Printer")
        print("Usage: python print_toc.py <pdf_file>")
        print("\nExample:")
        print("  python print_toc.py document.pdf")
        return 1

    pdf_path = sys.argv[1]
    print_toc_labels_and_pages(pdf_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
SAMPLE OUTPUT:

📖 OPENING: document.pdf
📄 PDF has 45 pages
================================================================================
📋 Found 23 TOC entries
📝 Showing first 23 entries:
--------------------------------------------------------------------------------
#    ✓  Level  Page   Title
--------------------------------------------------------------------------------
1    ✅  1      3      Introduction
     └─ Raw dest: list: [page=2, x=0, y=792]
2    ✅  1      5      Chapter 1: Getting Started
     └─ Raw dest: list: [page=4, x=0, y=792]
3    ✅  2      7        1.1 Installation
     └─ Raw dest: list: [page=6, x=0, y=650]
4    ❌  1      50     Bindings
     └─ Raw dest: list: [page=49, x=0, y=792]
     └─ ⚠️  Page 50 doesn't exist (PDF has 45 pages)
...

📊 SUMMARY:
   Total entries: 23
   Valid entries: 22
   Invalid entries: 1
   ⚠️  1 entries point to non-existent pages!

🔍 SEARCHING FOR SPECIFIC ENTRIES:
   📖 'Binding' entries:
      #4: 'Bindings' → Page 50
"""