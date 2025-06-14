#!/usr/bin/env python3
"""
Fix PDF Canvas Sizing for Scroll Bars
Ensures the PDF canvas reports correct size so scroll bars appear
"""

import os
from pathlib import Path


def fix_pdf_canvas_sizing():
    """Fix the PDF canvas sizing issues"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Fixing PDF canvas sizing for scroll bars...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if render_page method exists
        if 'def render_page(self):' not in content:
            print("❌ render_page method not found")
            return False

        # Find and replace the render_page method
        import re

        # Find the render_page method
        method_start = content.find('def render_page(self):')
        if method_start == -1:
            print("❌ Could not find render_page method")
            return False

        # Find the end of the method
        method_lines = content[method_start:].split('\n')
        method_content = []

        for i, line in enumerate(method_lines):
            method_content.append(line)
            # Stop when we hit the next method or class
            if i > 0 and line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                method_content.pop()  # Remove the line that's not part of this method
                break

        original_method = '\n'.join(method_content)

        # Create the corrected render_page method
        corrected_method = '''def render_page(self):
        """Render current PDF page to pixmap"""
        if not self.pdf_document or self.current_page >= self.pdf_document.page_count:
            return

        try:
            # Get page
            page = self.pdf_document[self.current_page]

            # Create transformation matrix for zoom
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)

            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")

            # Convert to QPixmap
            self.page_pixmap = QPixmap()
            self.page_pixmap.loadFromData(img_data)

            # *** KEY FIX: Set widget size to match pixmap ***
            pixmap_size = self.page_pixmap.size()

            # Set both minimum and actual size
            self.setMinimumSize(pixmap_size)
            self.resize(pixmap_size)

            # Update the displayed pixmap
            self.setPixmap(self.page_pixmap)

            # Update drag handler with canvas size
            if hasattr(self, 'drag_handler'):
                self.drag_handler.set_canvas_size(
                    self.page_pixmap.width(),
                    self.page_pixmap.height()
                )

            # Draw overlay (grid, fields, etc.)
            if hasattr(self, 'draw_overlay'):
                self.draw_overlay()

        except Exception as e:
            print(f"Error rendering page: {e}")'''

        # Replace the method
        content = content.replace(original_method, corrected_method)

        # Also ensure set_zoom method properly updates size
        if 'def set_zoom(self' in content:
            # Find set_zoom method and ensure it calls render_page
            set_zoom_start = content.find('def set_zoom(self')
            if set_zoom_start != -1:
                # Check if it calls render_page
                set_zoom_section = content[set_zoom_start:set_zoom_start + 1000]
                if 'self.render_page()' not in set_zoom_section:
                    # Find the end of set_zoom and add render_page call
                    lines = content[set_zoom_start:].split('\n')
                    method_lines = []

                    for i, line in enumerate(lines):
                        method_lines.append(line)
                        if i > 0 and line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                            method_lines.pop()
                            break

                    original_set_zoom = '\n'.join(method_lines)

                    # Add render_page call before the end
                    modified_lines = method_lines[:-1] if method_lines else []
                    modified_lines.append('        # Re-render with new zoom')
                    modified_lines.append('        self.render_page()')
                    modified_lines.append('')

                    modified_set_zoom = '\n'.join(modified_lines)
                    content = content.replace(original_set_zoom, modified_set_zoom)
                    print("  ✅ Added render_page call to set_zoom method")

        # Write the updated content
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Fixed PDF canvas sizing in render_page method")
        return True

    except Exception as e:
        print(f"❌ Error fixing PDF canvas sizing: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_scroll_area_debug():
    """Add debugging to see what's happening with scroll area"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find create_center_panel method
        if 'def create_center_panel(self)' not in content:
            print("⚠️ create_center_panel method not found for debugging")
            return False

        # Add debug info to scroll area setup
        debug_addition = '''

        # Debug: Print scroll area configuration
        print(f"📏 Scroll area configured:")
        print(f"  Widget resizable: {self.scroll_area.widgetResizable()}")
        print(f"  H scroll policy: {self.scroll_area.horizontalScrollBarPolicy()}")
        print(f"  V scroll policy: {self.scroll_area.verticalScrollBarPolicy()}")'''

        # Find where scroll area is configured and add debug
        if 'self.scroll_area.setWidget(self.pdf_canvas)' in content:
            insertion_point = content.find('self.scroll_area.setWidget(self.pdf_canvas)')
            line_end = content.find('\n', insertion_point)
            content = content[:line_end] + debug_addition + content[line_end:]

            with open(main_window_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Added scroll area debugging")
            return True

        return False

    except Exception as e:
        print(f"⚠️ Could not add debugging: {e}")
        return False


def add_pdf_canvas_size_debug():
    """Add debugging to PDF canvas to track size changes"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add debug to render_page method
        debug_code = '''

            # Debug: Print size information
            print(f"📏 PDF Canvas sizing:")
            print(f"  Pixmap size: {pixmap_size.width()}x{pixmap_size.height()}")
            print(f"  Widget size after resize: {self.size().width()}x{self.size().height()}")
            print(f"  Widget minimum size: {self.minimumSize().width()}x{self.minimumSize().height()}")

            # Force parent to update
            if self.parent():
                self.parent().updateGeometry()
                print(f"  Parent widget updated")'''

        # Find where pixmap size is set and add debug
        if 'self.setPixmap(self.page_pixmap)' in content:
            insertion_point = content.find('self.setPixmap(self.page_pixmap)')
            line_end = content.find('\n', insertion_point)
            content = content[:line_end] + debug_code + content[line_end:]

            with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Added PDF canvas size debugging")
            return True

        return False

    except Exception as e:
        print(f"⚠️ Could not add PDF canvas debugging: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Fix PDF Canvas Sizing for Scroll Bars")
    print("=" * 65)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Fix PDF canvas sizing
    if not fix_pdf_canvas_sizing():
        print("❌ Failed to fix PDF canvas sizing")
        return 1

    # Add debugging to track what's happening
    print("\n🔍 Adding debugging information...")
    add_scroll_area_debug()
    add_pdf_canvas_size_debug()

    print("\n🎉 PDF canvas sizing fixes applied!")
    print("\n🎯 Key changes:")
    print("  • PDF canvas now sets minimum size to match PDF dimensions")
    print("  • Canvas resizes itself when rendering pages")
    print("  • Zoom operations trigger re-rendering with new size")
    print("  • Added debugging to track size changes")
    print("\n🔍 Debugging added:")
    print("  • Console will show scroll area configuration")
    print("  • Console will show PDF canvas size changes")
    print("  • This helps identify if the fix is working")
    print("\n🚀 Test the application:")
    print("  1. Run: python launch.py")
    print("  2. Open a PDF file")
    print("  3. Look for debug messages in console")
    print("  4. Check if scroll bars appear")
    print("  5. Try mouse wheel scrolling")
    print("\n📋 Expected console output:")
    print("  📏 Scroll area configured: Widget resizable: True")
    print("  📏 PDF Canvas sizing: Pixmap size: 595x842")
    print("  📏 Widget size after resize: 595x842")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())