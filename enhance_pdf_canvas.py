#!/usr/bin/env python3
"""
Enhance PDF Canvas with Navigation Support
Safely adds navigation helper methods to the existing PDFCanvas class
"""

import os
from pathlib import Path


def enhance_pdf_canvas():
    """Add navigation helper methods to PDFCanvas class"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Enhancing PDF Canvas with navigation support...")

    try:
        # Read the current content
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if methods already exist
        if 'def get_page_count(self)' in content:
            print("✅ PDF Canvas already enhanced")
            return True

        # Define the enhanced methods to add
        enhanced_methods = '''
    # Enhanced Navigation and Information Methods
    def get_page_count(self) -> int:
        """Get total number of pages in the document"""
        if self.pdf_document:
            return self.pdf_document.page_count
        return 0

    def get_current_page_number(self) -> int:
        """Get current page number (1-based)"""
        return self.current_page + 1 if self.pdf_document else 0

    def can_go_previous(self) -> bool:
        """Check if can navigate to previous page"""
        return self.pdf_document and self.current_page > 0

    def can_go_next(self) -> bool:
        """Check if can navigate to next page"""
        return (self.pdf_document and 
                self.current_page < self.pdf_document.page_count - 1)

    def go_to_page(self, page_number: int) -> bool:
        """Navigate to specific page (1-based numbering)"""
        if not self.pdf_document:
            return False

        # Convert to 0-based indexing
        page_index = page_number - 1

        if 0 <= page_index < self.pdf_document.page_count:
            self.set_page(page_index)
            return True
        return False

    def zoom_to_level(self, zoom_percent: int) -> bool:
        """Set zoom to specific percentage (e.g., 100 for 100%)"""
        if zoom_percent < 10 or zoom_percent > 500:
            return False

        zoom_level = zoom_percent / 100.0
        self.set_zoom(zoom_level)
        return True

    def zoom_in_step(self, step: float = 1.25) -> float:
        """Zoom in by a step factor, returns new zoom level"""
        new_zoom = min(self.zoom_level * step, 5.0)
        self.set_zoom(new_zoom)
        return new_zoom

    def zoom_out_step(self, step: float = 1.25) -> float:
        """Zoom out by a step factor, returns new zoom level"""
        new_zoom = max(self.zoom_level / step, 0.1)
        self.set_zoom(new_zoom)
        return new_zoom

    def get_zoom_percent(self) -> int:
        """Get current zoom as percentage"""
        return int(self.zoom_level * 100)

    def fit_to_width(self, available_width: int) -> float:
        """Fit page to available width, returns new zoom level"""
        if not self.page_pixmap:
            return self.zoom_level

        # Calculate zoom needed to fit width
        page_width = self.page_pixmap.width() / self.zoom_level
        new_zoom = (available_width - 40) / page_width  # 40px margin
        new_zoom = max(0.1, min(new_zoom, 5.0))  # Clamp to reasonable range

        self.set_zoom(new_zoom)
        return new_zoom

    def fit_to_window(self, available_width: int, available_height: int) -> float:
        """Fit page to window size, returns new zoom level"""
        if not self.page_pixmap:
            return self.zoom_level

        # Calculate zoom needed for both width and height
        page_width = self.page_pixmap.width() / self.zoom_level
        page_height = self.page_pixmap.height() / self.zoom_level

        zoom_for_width = (available_width - 40) / page_width
        zoom_for_height = (available_height - 40) / page_height

        # Use smaller zoom to ensure page fits completely
        new_zoom = min(zoom_for_width, zoom_for_height)
        new_zoom = max(0.1, min(new_zoom, 5.0))

        self.set_zoom(new_zoom)
        return new_zoom

    def get_document_info(self) -> dict:
        """Get comprehensive document information"""
        if not self.pdf_document:
            return {
                'page_count': 0,
                'current_page': 0,
                'zoom_percent': 100,
                'field_count': 0,
                'has_document': False,
                'can_go_previous': False,
                'can_go_next': False
            }

        return {
            'page_count': self.pdf_document.page_count,
            'current_page': self.current_page + 1,
            'zoom_percent': self.get_zoom_percent(),
            'field_count': len(self.field_manager.fields),
            'has_document': True,
            'can_go_previous': self.can_go_previous(),
            'can_go_next': self.can_go_next()
        }

    def get_page_info_text(self) -> str:
        """Get formatted page information text"""
        if not self.pdf_document:
            return "No document loaded"

        current = self.current_page + 1
        total = self.pdf_document.page_count
        zoom = self.get_zoom_percent()
        fields = len(self.field_manager.fields)

        return f"Page {current} of {total} | Zoom: {zoom}% | Fields: {fields}"

    def reset_view(self):
        """Reset zoom and position to defaults"""
        self.zoom_level = 1.0
        if self.pdf_document:
            self.render_page()
'''

        # Find where to insert the methods (before the last method or at end of class)
        # Look for the end of the class before any module-level functions

        # Find the last method in the PDFCanvas class
        class_start = content.find('class PDFCanvas(QLabel):')
        if class_start == -1:
            print("❌ Could not find PDFCanvas class")
            return False

        # Find the end of the class (next class or module-level function)
        next_class = content.find('\nclass ', class_start + 1)
        module_function = content.find('\ndef ', class_start + 1)

        # Use the earliest occurrence that's not a method (starts at column 0)
        end_markers = []
        if next_class != -1:
            end_markers.append(next_class)
        if module_function != -1:
            # Check if it's really a module-level function (starts at column 0)
            line_start = content.rfind('\n', 0, module_function) + 1
            if content[line_start:module_function].strip() == '':
                end_markers.append(module_function)

        if end_markers:
            class_end = min(end_markers)
        else:
            class_end = len(content)

        # Find the last method definition within the class
        class_content = content[class_start:class_end]
        last_method = class_content.rfind('    def ')

        if last_method != -1:
            # Find the end of the last method
            method_end = class_content.find('\n\n', last_method)
            if method_end == -1:
                method_end = len(class_content)
            insert_pos = class_start + method_end
        else:
            # No methods found, insert at end of class
            insert_pos = class_end

        # Insert the enhanced methods
        content = content[:insert_pos] + enhanced_methods + '\n' + content[insert_pos:]

        # Write the updated content back to file
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Successfully enhanced PDF Canvas")
        print("  📋 Added methods:")
        print("    • get_page_count() - Get total pages")
        print("    • can_go_previous/next() - Navigation state")
        print("    • go_to_page() - Jump to specific page")
        print("    • zoom_in/out_step() - Smooth zoom controls")
        print("    • fit_to_width/window() - Smart fitting")
        print("    • get_document_info() - Comprehensive info")
        print("    • get_page_info_text() - Formatted display text")
        print("    • reset_view() - Reset zoom and position")

        return True

    except Exception as e:
        print(f"❌ Error enhancing PDF Canvas: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Enhance PDF Canvas")
    print("=" * 45)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Enhance PDF Canvas
    if enhance_pdf_canvas():
        print("\n🎉 PDF Canvas enhanced successfully!")
        print("\n🎯 Now run the navigation methods script:")
        print("  python add_navigation_methods.py")
        return 0
    else:
        print("\n❌ Failed to enhance PDF Canvas")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())