#!/usr/bin/env python3
"""
Add Comprehensive Scrolling Functionality
Adds mouse wheel, keyboard, and enhanced scroll area functionality
"""

import os
from pathlib import Path


def add_scrolling_to_pdf_canvas():
    """Add scrolling event handling to PDFCanvas"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Adding scrolling functionality to PDF Canvas...")

    try:
        # Read the current content
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if scrolling methods already exist
        if 'def wheelEvent(self' in content:
            print("✅ Wheel event handling already exists")
            return True

        # Add scrolling methods
        scrolling_methods = '''
    # Scrolling Event Handlers
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming and scrolling"""
        modifiers = event.modifiers()

        # Ctrl + Wheel = Zoom
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Get the angle delta (positive = zoom in, negative = zoom out)
            delta = event.angleDelta().y()

            if delta > 0:
                # Zoom in
                new_zoom = min(self.zoom_level * 1.15, 5.0)
            else:
                # Zoom out
                new_zoom = max(self.zoom_level / 1.15, 0.1)

            if new_zoom != self.zoom_level:
                # Store the mouse position relative to the widget
                mouse_pos = event.position().toPoint()

                # Set new zoom
                self.set_zoom(new_zoom)

                # Emit signal to notify main window of zoom change
                if hasattr(self, 'zoomChanged'):
                    self.zoomChanged.emit(new_zoom)

            # Accept the event to prevent default scrolling
            event.accept()

        # Shift + Wheel = Horizontal scroll
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Let the parent scroll area handle horizontal scrolling
            event.ignore()

        # Regular wheel = Vertical scroll
        else:
            # Let the parent scroll area handle vertical scrolling
            event.ignore()

    def keyPressEvent(self, event):
        """Enhanced keyboard event handling including scrolling"""
        key = event.key()
        modifiers = event.modifiers()

        # Handle field manipulation if a field is selected
        selected_field = self.selection_handler.get_selected_field()
        if selected_field:
            # Arrow keys for movement (existing functionality)
            if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
                step = 10 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1

                dx, dy = 0, 0
                if key == Qt.Key.Key_Up:
                    dy = -step
                elif key == Qt.Key.Key_Down:
                    dy = step
                elif key == Qt.Key.Key_Left:
                    dx = -step
                elif key == Qt.Key.Key_Right:
                    dx = step

                # Move the field
                new_x = selected_field.x + dx
                new_y = selected_field.y + dy
                selected_field.x = max(0, min(new_x, self.width() - selected_field.width))
                selected_field.y = max(0, min(new_y, self.height() - selected_field.height))

                self.draw_overlay()
                event.accept()
                return

        # Scrolling keyboard shortcuts (when no field is selected)
        scroll_handled = False

        # Page Up/Down for vertical scrolling
        if key == Qt.Key.Key_PageUp:
            self.scroll_page(-1)
            scroll_handled = True
        elif key == Qt.Key.Key_PageDown:
            self.scroll_page(1)
            scroll_handled = True

        # Home/End for horizontal scrolling
        elif key == Qt.Key.Key_Home:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.scroll_to_top()
            else:
                self.scroll_to_left()
            scroll_handled = True
        elif key == Qt.Key.Key_End:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.scroll_to_bottom()
            else:
                self.scroll_to_right()
            scroll_handled = True

        # Arrow keys for scrolling (when no field selected)
        elif key == Qt.Key.Key_Up and not selected_field:
            self.scroll_vertical(-50)
            scroll_handled = True
        elif key == Qt.Key.Key_Down and not selected_field:
            self.scroll_vertical(50)
            scroll_handled = True
        elif key == Qt.Key.Key_Left and not selected_field:
            self.scroll_horizontal(-50)
            scroll_handled = True
        elif key == Qt.Key.Key_Right and not selected_field:
            self.scroll_horizontal(50)
            scroll_handled = True

        # Zoom shortcuts
        elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.zoom_in_step()
                scroll_handled = True
        elif key == Qt.Key.Key_Minus:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.zoom_out_step()
                scroll_handled = True
        elif key == Qt.Key.Key_0:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                self.set_zoom(1.0)  # Reset to 100%
                scroll_handled = True

        if scroll_handled:
            event.accept()
        else:
            # Pass to parent for other events
            super().keyPressEvent(event)

    def scroll_page(self, direction: int):
        """Scroll by one page height"""
        if hasattr(self.parent(), 'verticalScrollBar'):
            scroll_bar = self.parent().verticalScrollBar()
            page_step = scroll_bar.pageStep()
            current_value = scroll_bar.value()
            new_value = current_value + (page_step * direction)
            scroll_bar.setValue(new_value)

    def scroll_vertical(self, delta: int):
        """Scroll vertically by delta pixels"""
        if hasattr(self.parent(), 'verticalScrollBar'):
            scroll_bar = self.parent().verticalScrollBar()
            current_value = scroll_bar.value()
            scroll_bar.setValue(current_value + delta)

    def scroll_horizontal(self, delta: int):
        """Scroll horizontally by delta pixels"""
        if hasattr(self.parent(), 'horizontalScrollBar'):
            scroll_bar = self.parent().horizontalScrollBar()
            current_value = scroll_bar.value()
            scroll_bar.setValue(current_value + delta)

    def scroll_to_top(self):
        """Scroll to top of document"""
        if hasattr(self.parent(), 'verticalScrollBar'):
            self.parent().verticalScrollBar().setValue(0)

    def scroll_to_bottom(self):
        """Scroll to bottom of document"""
        if hasattr(self.parent(), 'verticalScrollBar'):
            scroll_bar = self.parent().verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())

    def scroll_to_left(self):
        """Scroll to left edge of document"""
        if hasattr(self.parent(), 'horizontalScrollBar'):
            self.parent().horizontalScrollBar().setValue(0)

    def scroll_to_right(self):
        """Scroll to right edge of document"""
        if hasattr(self.parent(), 'horizontalScrollBar'):
            scroll_bar = self.parent().horizontalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())

    def center_on_point(self, x: int, y: int):
        """Center the view on a specific point"""
        if hasattr(self.parent(), 'ensureVisible'):
            # QScrollArea method to ensure a point is visible
            margin = 50  # Margin around the point
            self.parent().ensureVisible(x, y, margin, margin)
'''

        # Find where to insert the methods (after existing methods)
        # Look for the end of the class
        insert_pos = content.rfind('    def ')
        if insert_pos != -1:
            # Find the end of the last method
            method_end = content.find('\n\n', insert_pos)
            if method_end == -1:
                method_end = len(content)
            insert_pos = method_end
        else:
            insert_pos = len(content)

        # Insert the scrolling methods
        content = content[:insert_pos] + scrolling_methods + '\n' + content[insert_pos:]

        # Write the updated content back to file
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Added scrolling functionality to PDF Canvas")
        return True

    except Exception as e:
        print(f"❌ Error adding scrolling to PDF Canvas: {e}")
        import traceback
        traceback.print_exc()
        return False


def enhance_scroll_area_setup():
    """Enhance the scroll area setup in main window"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if enhanced scroll area setup already exists
        if 'setHorizontalScrollBarPolicy' in content:
            print("✅ Enhanced scroll area setup already exists")
            return True

        print("🔧 Enhancing scroll area setup...")

        # Find the create_center_panel method
        method_start = content.find('def create_center_panel(self)')
        if method_start == -1:
            print("⚠️ create_center_panel method not found")
            return True

        # Find the scroll area creation
        scroll_area_pos = content.find('self.scroll_area = QScrollArea()', method_start)
        if scroll_area_pos == -1:
            print("⚠️ QScrollArea creation not found")
            return True

        # Find the end of the current scroll area setup
        setup_end = content.find('self.scroll_area.setWidget(', scroll_area_pos)
        if setup_end == -1:
            setup_end = content.find('return self.scroll_area', scroll_area_pos)
        if setup_end == -1:
            return True

        # Enhanced scroll area setup
        enhanced_setup = '''        # Enhanced scroll area configuration
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Configure scroll bars
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Enable smooth scrolling
        self.scroll_area.setVerticalScrollMode(QScrollArea.ScrollMode.ScrollPerPixel)
        self.scroll_area.setHorizontalScrollMode(QScrollArea.ScrollMode.ScrollPerPixel)

        # Set scroll bar step sizes for smooth scrolling
        self.scroll_area.verticalScrollBar().setSingleStep(20)
        self.scroll_area.horizontalScrollBar().setSingleStep(20)

'''

        # Replace the basic setup with enhanced setup
        basic_setup_end = content.find('\n', scroll_area_pos)
        basic_setup_end = content.find('\n', basic_setup_end + 1)  # Skip the next line too

        content = content[:basic_setup_end] + '\n' + enhanced_setup + content[basic_setup_end:]

        # Write back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Enhanced scroll area setup")
        return True

    except Exception as e:
        print(f"❌ Error enhancing scroll area: {e}")
        return False


def add_scroll_shortcuts_to_main_window():
    """Add scroll-related keyboard shortcuts to main window"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if scroll shortcuts already exist
        if 'def setup_scroll_shortcuts(self)' in content:
            print("✅ Scroll shortcuts already exist")
            return True

        print("🔧 Adding scroll shortcuts to main window...")

        # Add scroll shortcuts method
        scroll_shortcuts_method = '''
    def setup_scroll_shortcuts(self):
        """Setup keyboard shortcuts for scrolling"""
        from PyQt6.QtGui import QShortcut

        # Zoom shortcuts
        zoom_in_shortcut = QShortcut("Ctrl++", self)
        zoom_in_shortcut.activated.connect(self.zoom_in)

        zoom_out_shortcut = QShortcut("Ctrl+-", self)
        zoom_out_shortcut.activated.connect(self.zoom_out)

        zoom_reset_shortcut = QShortcut("Ctrl+0", self)
        zoom_reset_shortcut.activated.connect(self.reset_zoom)

        # Fit shortcuts
        fit_width_shortcut = QShortcut("Ctrl+1", self)
        fit_width_shortcut.activated.connect(self.fit_width)

        fit_page_shortcut = QShortcut("Ctrl+2", self)
        fit_page_shortcut.activated.connect(self.fit_page)

        # Page navigation shortcuts
        next_page_shortcut = QShortcut("Ctrl+Right", self)
        next_page_shortcut.activated.connect(self.next_page)

        prev_page_shortcut = QShortcut("Ctrl+Left", self)
        prev_page_shortcut.activated.connect(self.previous_page)

        # Alternative page navigation
        page_down_shortcut = QShortcut("Page_Down", self)
        page_down_shortcut.activated.connect(self.next_page)

        page_up_shortcut = QShortcut("Page_Up", self)
        page_up_shortcut.activated.connect(self.previous_page)

    @pyqtSlot()
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if hasattr(self.pdf_canvas, 'set_zoom'):
            self.pdf_canvas.set_zoom(1.0)
            self.statusBar().showMessage("Zoom reset to 100%", 1000)
            self.update_document_info()

            # Update zoom combo if it exists
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText("100%")
        else:
            self.statusBar().showMessage("Zoom not available", 1000)

    def enable_smooth_scrolling(self):
        """Enable smooth scrolling for the scroll area"""
        if hasattr(self, 'scroll_area'):
            # Configure for smooth pixel-based scrolling
            self.scroll_area.setVerticalScrollMode(QScrollArea.ScrollMode.ScrollPerPixel)
            self.scroll_area.setHorizontalScrollMode(QScrollArea.ScrollMode.ScrollPerPixel)

            # Set reasonable step sizes
            v_scrollbar = self.scroll_area.verticalScrollBar()
            h_scrollbar = self.scroll_area.horizontalScrollBar()

            v_scrollbar.setSingleStep(20)
            v_scrollbar.setPageStep(200)
            h_scrollbar.setSingleStep(20)
            h_scrollbar.setPageStep(200)
'''

        # Find where to insert the methods
        method_insert_pos = content.find('    def update_document_info(self):')
        if method_insert_pos == -1:
            method_insert_pos = content.find('    def get_navigation_state(self):')
        if method_insert_pos == -1:
            method_insert_pos = content.find('\ndef main():')

        if method_insert_pos != -1:
            content = content[:method_insert_pos] + scroll_shortcuts_method + '\n' + content[method_insert_pos:]
            print("✅ Added scroll shortcuts methods")
        else:
            print("⚠️ Could not find insertion point for scroll methods")

        # Add call to setup_scroll_shortcuts in init_ui if not already there
        if 'self.setup_scroll_shortcuts()' not in content:
            init_ui_pos = content.find('def init_ui(self):')
            if init_ui_pos != -1:
                # Find a good place to add the call (after toolbar/status bar setup)
                insert_pos = content.find('self.create_status_bar()', init_ui_pos)
                if insert_pos != -1:
                    line_end = content.find('\n', insert_pos)
                    if line_end != -1:
                        content = content[
                                  :line_end] + '\n        self.setup_scroll_shortcuts()\n        self.enable_smooth_scrolling()' + content[
                                                                                                                                   line_end:]
                        print("✅ Added scroll shortcuts setup call to init_ui")

        # Write back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error adding scroll shortcuts: {e}")
        return False


def add_missing_imports():
    """Add missing imports for scrolling functionality"""

    paths_to_check = [
        Path("src/ui/pdf_canvas.py"),
        Path("src/ui/main_window.py")
    ]

    for path in paths_to_check:
        if not path.exists():
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for QScrollArea import in main_window.py
            if path.name == "main_window.py" and "QScrollArea" not in content:
                # Find PyQt6.QtWidgets import
                widgets_import = content.find('from PyQt6.QtWidgets import (')
                if widgets_import != -1:
                    import_end = content.find(')', widgets_import)
                    if import_end != -1 and "QScrollArea" not in content[widgets_import:import_end]:
                        # Add QScrollArea to the import
                        content = content[:import_end] + ', QScrollArea' + content[import_end:]

                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✅ Added QScrollArea import to {path.name}")

        except Exception as e:
            print(f"⚠️ Error checking imports in {path.name}: {e}")

    return True


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Add Comprehensive Scrolling Functionality")
    print("=" * 65)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Add missing imports
    if not add_missing_imports():
        print("❌ Failed to add missing imports")
        return 1

    # Add scrolling functionality to PDF Canvas
    if not add_scrolling_to_pdf_canvas():
        print("❌ Failed to add scrolling to PDF Canvas")
        return 1

    # Enhance scroll area setup
    if not enhance_scroll_area_setup():
        print("❌ Failed to enhance scroll area setup")
        return 1

    # Add scroll shortcuts to main window
    if not add_scroll_shortcuts_to_main_window():
        print("❌ Failed to add scroll shortcuts")
        return 1

    print("\n🎉 Comprehensive scrolling functionality added!")
    print("\n🎯 New scrolling features:")
    print("  🖱️ Mouse Wheel:")
    print("    • Wheel = Vertical scroll")
    print("    • Shift + Wheel = Horizontal scroll")
    print("    • Ctrl + Wheel = Zoom in/out")
    print("\n  ⌨️ Keyboard:")
    print("    • Arrow keys = Scroll (when no field selected)")
    print("    • Page Up/Down = Page scroll")
    print("    • Home/End = Horizontal scroll edges")
    print("    • Ctrl+Home/End = Top/bottom of document")
    print("    • Ctrl +/- = Zoom")
    print("    • Ctrl+0 = Reset zoom to 100%")
    print("    • Ctrl+1 = Fit width")
    print("    • Ctrl+2 = Fit page")
    print("\n  🎛️ Enhanced scroll area:")
    print("    • Smooth pixel-based scrolling")
    print("    • Adaptive scroll bar policies")
    print("    • Optimized step sizes")
    print("\n🚀 Test it now:")
    print("  python launch.py")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())