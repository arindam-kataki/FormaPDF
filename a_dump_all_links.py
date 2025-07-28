#!/usr/bin/env python3
"""
Standalone script to dump ALL hyperlinks from a PDF document
Usage: python dump_all_links.py your_pdf_file.pdf
"""

import fitz  # PyMuPDF
import sys
import os
from typing import List, Dict, Any


def dump_all_links(pdf_path: str, max_links_per_page: int = 100):
    """
    Extract and dump all hyperlinks from a PDF document

    Args:
        pdf_path: Path to PDF file
        max_links_per_page: Maximum links to show per page (for very dense documents)
    """
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print(f"🔗 OPENING: {pdf_path}")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        print(f"📄 PDF has {total_pages} pages")
        print("=" * 80)

        total_links = 0
        links_by_type = {}

        # Iterate through all pages
        for page_num in range(total_pages):
            page = doc[page_num]
            raw_links = page.get_links()

            if not raw_links:
                continue

            page_links = len(raw_links)
            total_links += page_links

            print(f"\n📄 PAGE {page_num + 1} - Found {page_links} links:")
            print("-" * 40)

            # Show links for this page
            for i, raw_link in enumerate(raw_links[:max_links_per_page]):
                link_info = _parse_link_info(raw_link, page_num, doc)
                link_type = link_info['type']

                # Track link types
                links_by_type[link_type] = links_by_type.get(link_type, 0) + 1

                # Display link details
                print(f"  {i + 1:2d}. [{link_type.upper()}] {link_info['description']}")
                if link_info.get('coordinates'):
                    x, y, w, h = link_info['coordinates']
                    print(f"      📍 Position: ({x:.1f}, {y:.1f}) Size: {w:.1f}×{h:.1f}")
                if link_info.get('target'):
                    print(f"      🎯 Target: {link_info['target']}")

            if page_links > max_links_per_page:
                print(f"      ... ({page_links - max_links_per_page} more links not shown)")

        # Summary
        print("\n" + "=" * 80)
        print(f"📊 SUMMARY:")
        print(f"   Total pages scanned: {total_pages}")
        print(f"   Total links found: {total_links}")

        if links_by_type:
            print(f"   Links by type:")
            for link_type, count in sorted(links_by_type.items()):
                percentage = (count / total_links) * 100 if total_links > 0 else 0
                print(f"     • {link_type.upper()}: {count} ({percentage:.1f}%)")
        else:
            print("   ❌ No links found in this document")

        doc.close()

    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()


def _parse_link_info(raw_link: dict, page_num: int, doc) -> Dict[str, Any]:
    """Parse raw link data into readable information"""

    # Get link rectangle coordinates
    link_rect = raw_link.get('from', None)
    coordinates = None
    if link_rect:
        coordinates = (link_rect.x0, link_rect.y0, link_rect.width, link_rect.height)

    # Determine link type and extract details
    link_kind = raw_link.get('kind', 0)

    if link_kind == fitz.LINK_GOTO:
        # Internal link to another page
        target_page = raw_link.get('page', 0)
        target_coords = raw_link.get('to', [])

        target_info = f"Page {target_page + 1}"
        if isinstance(target_coords, (list, tuple)) and len(target_coords) >= 2:
            x, y = target_coords[0], target_coords[1]
            target_info += f" at ({x:.1f}, {y:.1f})"

        return {
            'type': 'goto',
            'description': f"Internal link to page {target_page + 1}",
            'target': target_info,
            'coordinates': coordinates
        }

    elif link_kind == fitz.LINK_URI:
        # External URL link
        uri = raw_link.get('uri', '')
        return {
            'type': 'uri',
            'description': f"External URL: {uri[:60]}{'...' if len(uri) > 60 else ''}",
            'target': uri,
            'coordinates': coordinates
        }

    elif link_kind == fitz.LINK_LAUNCH:
        # Launch file link
        file_path = raw_link.get('file', '')
        return {
            'type': 'launch',
            'description': f"Launch file: {os.path.basename(file_path)}",
            'target': file_path,
            'coordinates': coordinates
        }

    elif link_kind == fitz.LINK_GOTOR:
        # Link to external document
        file_path = raw_link.get('file', '')
        target_page = raw_link.get('page', 0)
        return {
            'type': 'gotor',
            'description': f"External doc: {os.path.basename(file_path)} (page {target_page + 1})",
            'target': f"{file_path} → Page {target_page + 1}",
            'coordinates': coordinates
        }

    elif link_kind == fitz.LINK_NAMED:
        # Named destination link
        name = raw_link.get('name', '')
        return {
            'type': 'named',
            'description': f"Named destination: {name}",
            'target': name,
            'coordinates': coordinates
        }

    else:
        # Unknown link type
        return {
            'type': f'unknown_{link_kind}',
            'description': f"Unknown link type ({link_kind})",
            'target': str(raw_link),
            'coordinates': coordinates
        }


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("🔗 PDF Hyperlink Dumper")
        print("Usage: python dump_all_links.py <pdf_file>")
        print("\nExample:")
        print("  python dump_all_links.py document.pdf")
        print("\nThis tool extracts and displays ALL hyperlinks from a PDF document,")
        print("including internal page links, external URLs, file links, etc.")
        return 1

    pdf_path = sys.argv[1]
    dump_all_links(pdf_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
SAMPLE OUTPUT:

🔗 OPENING: technical_manual.pdf
📄 PDF has 150 pages
================================================================================

📄 PAGE 1 - Found 5 links:
----------------------------------------
  1. [GOTO] Internal link to page 15
     📍 Position: (120.5, 680.2) Size: 85.3×12.0
     🎯 Target: Page 15 at (72.0, 720.0)
  2. [URI] External URL: https://www.example.com/documentation
     📍 Position: (200.1, 650.8) Size: 180.4×12.0
     🎯 Target: https://www.example.com/documentation
  3. [GOTO] Internal link to page 25
     📍 Position: (95.2, 620.5) Size: 95.8×12.0
     🎯 Target: Page 25 at (72.0, 700.0)

📄 PAGE 5 - Found 3 links:
----------------------------------------
  1. [LAUNCH] Launch file: config.txt
     📍 Position: (150.0, 500.0) Size: 60.0×12.0
     🎯 Target: /path/to/config.txt
  2. [GOTOR] External doc: appendix.pdf (page 1)
     📍 Position: (300.0, 400.0) Size: 80.0×12.0
     🎯 Target: appendix.pdf → Page 1

================================================================================
📊 SUMMARY:
   Total pages scanned: 150
   Total links found: 247
   Links by type:
     • GOTO: 189 (76.5%)
     • URI: 35 (14.2%)
     • LAUNCH: 15 (6.1%)
     • GOTOR: 6 (2.4%)
     • NAMED: 2 (0.8%)
"""