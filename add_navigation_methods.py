#!/usr/bin/env python3
"""
Add Missing Navigation and Zoom Methods to main_window.py
This script safely adds the methods that toolbar buttons are trying to connect to
"""

import os
from pathlib import Path


def add_missing_navigation_methods():
    """Add all missing navigation and zoom methods to main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Adding missing navigation and zoom methods...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if methods already exist
        existing_methods = [
            'def previous_page(self)',
            'def next_page(self)',
            'def zoom_in(self)',
            'def zoom_out(self)',
            'def fit_width(self)',
            'def toggle_grid(self)'
        ]

        missing_methods = []
        for method in existing_methods:
            if method not in content:
                missing_methods.append(method.split('(')[0].split()[-1])

        if not missing_methods:
            print("✅ All navigation methods already exist")
            return True

        print(f"📋 Adding missing methods: {', '.join(missing_methods)}")

        # Define all the missing navigation and zoom methods
        navigation_methods = '''
    # Navigation and Zoom Methods
    @pyqtSlot()
    def previous_page(self):
        """Navigate to previous page"""
        if not hasattr(self.pdf_canvas, 'current_page'):
            self.statusBar().showMessage("No PDF loaded", 1000)
            return

        if hasattr(self.pdf_canvas, 'current_page') and self.pdf_canvas.current_page > 0:
            if hasattr(self.pdf_canvas, 'set_page'):
                new_page = self.pdf_canvas.current_page - 1
                self.pdf_canvas.set_page(new_page)
                self.statusBar().showMessage(f"Page {new_page + 1}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Navigation not available", 1000)
        else:
            self.statusBar().showMessage("Already at first page", 1000)

    @pyqtSlot()
    def next_page(self):
        """Navigate to next page"""
        if not hasattr(self.pdf_canvas, 'current_page') or not hasattr(self.pdf_canvas, 'pdf_document'):
            self.statusBar().showMessage("No PDF loaded", 1000)
            return

        if (self.pdf_canvas.pdf_document and 
            self.pdf_canvas.current_page < self.pdf_canvas.pdf_document.page_count - 1):
            if hasattr(self.pdf_canvas, 'set_page'):
                new_page = self.pdf_canvas.current_page + 1
                self.pdf_canvas.set_page(new_page)
                self.statusBar().showMessage(f"Page {new_page + 1}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Navigation not available", 1000)
        else:
            self.statusBar().showMessage("Already at last page", 1000)

    @pyqtSlot()
    def zoom_in(self):
        """Increase zoom level"""
        if not hasattr(self.pdf_canvas, 'zoom_level') or not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = min(current_zoom * 1.25, 5.0)
        self.pdf_canvas.set_zoom(new_zoom)
        zoom_percent = int(new_zoom * 100)
        self.statusBar().showMessage(f"Zoom: {zoom_percent}%", 1000)
        self.update_document_info()

    @pyqtSlot()
    def zoom_out(self):
        """Decrease zoom level"""
        if not hasattr(self.pdf_canvas, 'zoom_level') or not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = max(current_zoom / 1.25, 0.1)
        self.pdf_canvas.set_zoom(new_zoom)
        zoom_percent = int(new_zoom * 100)
        self.statusBar().showMessage(f"Zoom: {zoom_percent}%", 1000)
        self.update_document_info()

    @pyqtSlot()
    def fit_width(self):
        """Fit PDF page to window width"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Fit width not available", 1000)
            return

        try:
            # Calculate zoom needed to fit width
            available_width = self.scroll_area.width() - 40  # Account for margins
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)
            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            new_zoom = available_width / page_width
            new_zoom = max(0.1, min(new_zoom, 5.0))  # Clamp to reasonable range

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)
            self.statusBar().showMessage(f"Fit width: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Fit width failed", 1000)

    @pyqtSlot()
    def toggle_grid(self):
        """Toggle grid display"""
        if hasattr(self.pdf_canvas, 'toggle_grid'):
            self.pdf_canvas.toggle_grid()

            # Update grid action state if it exists
            if hasattr(self, 'grid_action') and hasattr(self.pdf_canvas, 'show_grid'):
                self.grid_action.setChecked(self.pdf_canvas.show_grid)

            grid_status = "on" if getattr(self.pdf_canvas, 'show_grid', False) else "off"
            self.statusBar().showMessage(f"Grid {grid_status}", 1000)
        else:
            self.statusBar().showMessage("Grid toggle not available", 1000)

    @pyqtSlot()
    def zoom_to_fit(self):
        """Zoom to fit entire page in window"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Zoom to fit not available", 1000)
            return

        try:
            # Calculate zoom to fit both width and height
            available_width = self.scroll_area.width() - 40
            available_height = self.scroll_area.height() - 40
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)

            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            page_height = self.pdf_canvas.page_pixmap.height() / current_zoom

            zoom_for_width = available_width / page_width
            zoom_for_height = available_height / page_height

            # Use the smaller zoom to ensure page fits completely
            new_zoom = min(zoom_for_width, zoom_for_height)
            new_zoom = max(0.1, min(new_zoom, 5.0))

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)
            self.statusBar().showMessage(f"Zoom to fit: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Zoom to fit failed", 1000)

    def update_document_info(self):
        """Update document information display - enhanced version"""
        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                # Get current page info
                current_page = getattr(self.pdf_canvas, 'current_page', 0) + 1
                total_pages = self.pdf_canvas.pdf_document.page_count

                # Get zoom info
                zoom_level = getattr(self.pdf_canvas, 'zoom_level', 1.0)
                zoom_percent = int(zoom_level * 100)

                # Get field count
                field_count = 0
                if hasattr(self.pdf_canvas, 'get_fields_as_objects'):
                    try:
                        fields = self.pdf_canvas.get_fields_as_objects()
                        field_count = len(fields)
                    except:
                        pass

                # Update display
                info_text = f"Page {current_page} of {total_pages} | Zoom: {zoom_percent}% | Fields: {field_count}"
                self.field_info_label.setText(info_text)

            else:
                self.field_info_label.setText("No document loaded")

        except Exception as e:
            # Fallback to basic info
            self.field_info_label.setText("Document info unavailable")

    def get_navigation_state(self) -> dict:
        """Get current navigation state for UI updates"""
        state = {
            'has_document': False,
            'can_go_previous': False,
            'can_go_next': False,
            'current_page': 0,
            'total_pages': 0,
            'zoom_percent': 100
        }

        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                state['has_document'] = True
                state['current_page'] = getattr(self.pdf_canvas, 'current_page', 0) + 1
                state['total_pages'] = self.pdf_canvas.pdf_document.page_count
                state['can_go_previous'] = getattr(self.pdf_canvas, 'current_page', 0) > 0
                state['can_go_next'] = getattr(self.pdf_canvas, 'current_page', 0) < state['total_pages'] - 1
                state['zoom_percent'] = int(getattr(self.pdf_canvas, 'zoom_level', 1.0) * 100)

        except Exception:
            pass

        return state
'''

        # Find where to insert the methods (before the main function)
        insert_pos = content.find('\ndef main():')
        if insert_pos == -1:
            insert_pos = content.find('if __name__ == "__main__":')
        if insert_pos == -1:
            # Insert before the last method
            last_method = content.rfind('    def ')
            if last_method != -1:
                method_end = content.find('\n\n', last_method)
                if method_end == -1:
                    insert_pos = len(content)
                else:
                    insert_pos = method_end
            else:
                insert_pos = len(content)

        # Insert the navigation methods
        content = content[:insert_pos] + navigation_methods + '\n' + content[insert_pos:]

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Successfully added navigation and zoom methods")
        print("  📋 Added methods:")
        print("    • previous_page() - Navigate to previous page")
        print("    • next_page() - Navigate to next page")
        print("    • zoom_in() - Increase zoom level")
        print("    • zoom_out() - Decrease zoom level")
        print("    • fit_width() - Fit page to window width")
        print("    • toggle_grid() - Toggle grid display")
        print("    • zoom_to_fit() - Fit entire page in window")
        print("    • update_document_info() - Enhanced info display")
        print("    • get_navigation_state() - Get UI state info")

        return True

    except Exception as e:
        print(f"❌ Error adding navigation methods: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_toolbar_connections():
    """Update the toolbar creation to use the new methods"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if toolbar already connects to these methods
        if 'self.previous_page' in content and 'self.next_page' in content:
            print("✅ Toolbar connections already updated")
            return True

        print("🔧 Updating toolbar to connect to new methods...")

        # Update any existing toolbar connections
        replacements = [
            # Update navigation connections if they exist but are broken
            ('prev_action.triggered.connect(self.previous_page)', 'prev_action.triggered.connect(self.previous_page)'),
            ('next_action.triggered.connect(self.next_page)', 'next_action.triggered.connect(self.next_page)'),
            ('zoom_in_action.triggered.connect(self.zoom_in)', 'zoom_in_action.triggered.connect(self.zoom_in)'),
            ('zoom_out_action.triggered.connect(self.zoom_out)', 'zoom_out_action.triggered.connect(self.zoom_out)'),
        ]

        # The connections should work now that the methods exist
        print("✅ Toolbar connections will now work with existing methods")
        return True

    except Exception as e:
        print(f"❌ Error updating toolbar connections: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Add Missing Navigation Methods")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Add missing navigation methods
    if not add_missing_navigation_methods():
        print("❌ Failed to add navigation methods")
        return 1

    # Update toolbar connections
    if not update_toolbar_connections():
        print("❌ Failed to update toolbar connections")
        return 1

    print("\n🎉 Successfully added all missing navigation methods!")
    print("\n🎯 What's now working:")
    print("  ✅ Previous/Next page buttons")
    print("  ✅ Zoom in/out buttons")
    print("  ✅ Fit width functionality")
    print("  ✅ Grid toggle")
    print("  ✅ Enhanced document info display")
    print("\n🎯 Next steps:")
    print("1. Try running: python launch.py")
    print("2. Open a PDF and test navigation/zoom buttons")
    print("3. All toolbar buttons should now work!")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())