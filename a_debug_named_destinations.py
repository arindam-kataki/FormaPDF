#!/usr/bin/env python3
"""
Named Destination Debug Tool for PDFs
This tool helps debug and understand named destinations in PDF documents
"""

import fitz  # PyMuPDF
import sys
import os
from typing import Dict, List, Any, Optional


def debug_named_destinations(pdf_path: str):
    """
    Comprehensive debug analysis of named destinations in a PDF
    """
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return

    try:
        print(f"🏷️ DEBUGGING NAMED DESTINATIONS: {pdf_path}")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"📄 Document has {total_pages} pages")
        print("=" * 80)

        # Part 1: Extract all named destinations from document-level
        print("🔍 PART 1: DOCUMENT-LEVEL NAMED DESTINATIONS")
        print("-" * 50)

        try:
            # Get document catalog and named destinations
            doc_dict = doc.pdf_catalog()
            if doc_dict:
                print(f"📖 Document catalog found")
                _debug_document_destinations(doc, doc_dict)
            else:
                print("❌ No document catalog found")
        except Exception as e:
            print(f"❌ Error accessing document catalog: {e}")

        # Part 2: Find named destination links on pages
        print(f"\n🔍 PART 2: NAMED DESTINATION LINKS ON PAGES")
        print("-" * 50)

        named_links = []
        for page_num in range(total_pages):
            page = doc[page_num]
            raw_links = page.get_links()

            page_named_links = []
            for link in raw_links:
                if link.get('kind') == fitz.LINK_NAMED:
                    page_named_links.append(link)
                    named_links.append((page_num, link))

            if page_named_links:
                print(f"📄 Page {page_num + 1}: {len(page_named_links)} named links")
                for i, link in enumerate(page_named_links):
                    _debug_named_link_details(link, i + 1)

        # Part 3: Resolution analysis
        print(f"\n🔍 PART 3: NAMED DESTINATION RESOLUTION")
        print("-" * 50)

        if named_links:
            print(f"Found {len(named_links)} named destination links total")
            _analyze_named_destination_resolution(doc, named_links)
        else:
            print("❌ No named destination links found in document")

        # Part 4: Show raw PDF structure (if possible)
        print(f"\n🔍 PART 4: RAW PDF STRUCTURE ANALYSIS")
        print("-" * 50)
        _debug_pdf_structure(doc)

        doc.close()

    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()


def _debug_document_destinations(doc, doc_dict):
    """Debug document-level named destinations"""
    try:
        # Look for Names dictionary
        if 'Names' in doc_dict:
            names_dict = doc_dict['Names']
            print(f"📂 Names dictionary found: {names_dict}")

            if 'Dests' in names_dict:
                dests_dict = names_dict['Dests']
                print(f"🎯 Destinations dictionary found: {dests_dict}")
                # Try to resolve the destinations tree
                _resolve_destinations_tree(doc, dests_dict)
            else:
                print("❌ No 'Dests' entry in Names dictionary")
        else:
            print("❌ No 'Names' dictionary in document catalog")

        # Also check for direct Dests entry
        if 'Dests' in doc_dict:
            direct_dests = doc_dict['Dests']
            print(f"🎯 Direct Dests dictionary found: {direct_dests}")

    except Exception as e:
        print(f"❌ Error analyzing document destinations: {e}")


def _resolve_destinations_tree(doc, dests_dict):
    """Try to resolve the destinations name tree"""
    try:
        # Named destinations are stored in a name tree structure
        # This is complex - try to get some basic info
        print(f"🌳 Attempting to resolve destinations tree...")

        # PyMuPDF might have helper methods
        if hasattr(doc, 'resolve_names'):
            names = doc.resolve_names()
            if names:
                print(f"✅ Resolved {len(names)} named destinations:")
                for name, dest in names.items():
                    print(f"   '{name}' → {dest}")
            else:
                print("❌ No named destinations resolved")
        else:
            print("❌ PyMuPDF version doesn't support resolve_names()")

    except Exception as e:
        print(f"❌ Error resolving destinations tree: {e}")


def _debug_named_link_details(raw_link: dict, link_num: int):
    """Debug details of a single named destination link"""
    print(f"   Link {link_num}:")
    print(f"     🏷️ Name: '{raw_link.get('name', 'UNKNOWN')}'")
    print(f"     📍 From rect: {raw_link.get('from', 'UNKNOWN')}")

    # Show all available keys in the raw link
    print(f"     🔑 Available keys: {list(raw_link.keys())}")

    # Try to show raw values
    for key, value in raw_link.items():
        if key not in ['from', 'name', 'kind']:
            print(f"     📝 {key}: {value}")


def _analyze_named_destination_resolution(doc, named_links: List[tuple]):
    """Analyze how to resolve named destinations to actual locations"""
    print(f"🧩 Analyzing resolution for {len(named_links)} named links...")

    unique_names = set()
    for page_num, link in named_links:
        name = link.get('name', '')
        if name:
            unique_names.add(name)

    print(f"📋 Unique destination names found: {len(unique_names)}")
    for name in sorted(unique_names):
        print(f"   • '{name}'")

        # Try different resolution approaches
        resolved_location = _try_resolve_named_destination(doc, name)
        if resolved_location:
            print(f"     ✅ Resolved to: {resolved_location}")
        else:
            print(f"     ❌ Could not resolve")


def _try_resolve_named_destination(doc, name: str) -> Optional[Dict[str, Any]]:
    """Try various methods to resolve a named destination"""

    # Method 1: Try PyMuPDF's built-in resolution
    try:
        if hasattr(doc, 'resolve_dest'):
            dest = doc.resolve_dest(name)
            if dest:
                return {'method': 'resolve_dest', 'result': dest}
    except:
        pass

    # Method 2: Try searching through outline/TOC
    try:
        toc = doc.get_toc()
        for level, title, dest in toc:
            if isinstance(dest, str) and dest == name:
                return {'method': 'toc_match', 'title': title, 'level': level}
    except:
        pass

    # Method 3: Manual parsing (would need more complex implementation)
    try:
        # This would require parsing the PDF structure manually
        # For now, just indicate that manual parsing would be needed
        return {'method': 'manual_parsing_needed', 'name': name}
    except:
        pass

    return None


def _debug_pdf_structure(doc):
    """Debug raw PDF structure for named destinations"""
    try:
        print("📊 PDF Structure Analysis:")

        # Show document metadata
        metadata = doc.metadata
        if metadata:
            print(f"   📄 Title: {metadata.get('title', 'N/A')}")
            print(f"   👤 Author: {metadata.get('author', 'N/A')}")
            print(f"   🛠️ Producer: {metadata.get('producer', 'N/A')}")

        # Check if we can access xref table
        try:
            xref_count = doc.xref_length()
            print(f"   📑 XRef entries: {xref_count}")
        except:
            print("   ❌ Cannot access XRef table")

        # Check for JavaScript (sometimes contains named destination logic)
        try:
            js = doc.embfile_names()
            if js:
                print(f"   📜 Embedded files: {len(js)}")
            else:
                print("   📜 No embedded files")
        except:
            print("   ❌ Cannot check embedded files")

    except Exception as e:
        print(f"❌ Error analyzing PDF structure: {e}")


def enhanced_named_link_parser(raw_link: dict, page_num: int, doc) -> Dict[str, Any]:
    """
    Enhanced parser for named destination links with detailed debugging
    """
    name = raw_link.get('name', '')

    # Basic link info
    result = {
        'name': name,
        'page_num': page_num,
        'raw_link': raw_link,
        'resolved': False,
        'resolution_method': None,
        'target_page': None,
        'target_coords': None,
        'debug_info': []
    }

    result['debug_info'].append(f"Parsing named destination: '{name}'")

    # Try to resolve the named destination
    if name:
        # Method 1: Direct resolution
        try:
            if hasattr(doc, 'resolve_dest'):
                dest = doc.resolve_dest(name)
                if dest:
                    result['resolved'] = True
                    result['resolution_method'] = 'PyMuPDF resolve_dest'
                    result['target_page'] = dest.get('page', 0) if isinstance(dest, dict) else 0
                    result['debug_info'].append(f"✅ Resolved via resolve_dest: {dest}")
        except Exception as e:
            result['debug_info'].append(f"❌ resolve_dest failed: {e}")

        # Method 2: Search TOC for matching name
        if not result['resolved']:
            try:
                toc = doc.get_toc()
                for level, title, dest in toc:
                    if name.lower() in title.lower() or title.lower() in name.lower():
                        result['resolved'] = True
                        result['resolution_method'] = 'TOC title match'
                        if isinstance(dest, (list, tuple)) and dest:
                            result['target_page'] = dest[0]
                            result['target_coords'] = (dest[1], dest[2]) if len(dest) >= 3 else (0, 0)
                        result['debug_info'].append(f"✅ Found TOC match: '{title}'")
                        break
            except Exception as e:
                result['debug_info'].append(f"❌ TOC search failed: {e}")

        # Method 3: Look for page labels that match
        if not result['resolved']:
            try:
                for p in range(len(doc)):
                    page = doc[p]
                    page_label = page.get_label()
                    if page_label and (name in page_label or page_label in name):
                        result['resolved'] = True
                        result['resolution_method'] = 'Page label match'
                        result['target_page'] = p
                        result['debug_info'].append(f"✅ Page label match: '{page_label}' on page {p + 1}")
                        break
            except Exception as e:
                result['debug_info'].append(f"❌ Page label search failed: {e}")

    if not result['resolved']:
        result['debug_info'].append(f"❌ Could not resolve named destination '{name}'")

    return result


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("🏷️ Named Destination Debug Tool")
        print("Usage: python debug_named_destinations.py <pdf_file>")
        print("\nThis tool provides comprehensive debugging of named destinations")
        print("in PDF documents, including link analysis and resolution attempts.")
        return 1

    pdf_path = sys.argv[1]
    debug_named_destinations(pdf_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())