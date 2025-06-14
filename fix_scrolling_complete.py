#!/usr/bin/env python3
"""
Complete Scrolling Fix
Fixes all aspects of scrolling in the PDF viewer
"""

import os
from pathlib import Path


def fix_pdf_canvas_sizing():
    """Fix the core issue: PDF canvas must resize itself to enable scroll bars"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Step 1: Fixing PDF canvas sizing...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if render_page method exists
        if 'def render_page(self):' not in content:
            print("❌ render_page method not found - cannot fix sizing")
            return False

        # Fix the render_page method to properly size the widget
        sizing_fix = '''
        # *** CRITICAL FIX: Set widget size to match PDF content ***
        if self.page_pixmap:
            pixmap_size = self.page_pixmap.size()

            # Set both minimum size and actual size
            self.setMinimumSize(pixmap_size)
            self.resize(pixmap_size)

            # Force parent to recognize size change
            if self.parent():
                self.parent().updateGeometry()

            print(f"📏 PDF Canvas sized to: {pixmap_size.width()}x{pixmap_size.height()}")'''

        # Find where to insert the sizing fix in render_page
        if 'self.setPixmap(self.page_pixmap)' in content:
            insertion_point = content.find('self.setPixmap(self.page_pixmap)')
            line_end = content.find('\n', insertion_point)
            content = content[:line_end] + sizing_fix + content[line_end:]
            print("  ✅ Added sizing fix to render_page method")
        else:
            print("  ⚠️ Could not find setPixmap call to insert sizing fix")

        # Ensure set_zoom calls render_page
        if 'def set_zoom(self' in content and 'self.render_page()' not in content[content.find(
                'def set_zoom(self'):content.find('def set_zoom(self') + 500]:
            # Find set_zoom method and add render_page call
            set_zoom_start = content.find('def set_zoom(self')
            method_end = content.find('\n    def ', set_zoom_start + 1)
            if method_end == -1:
                method_end = content.find('\ndef ', set_zoom_start + 1)
            if method_end == -1:
                method_end = len(content)

            # Add render_page call before method end
            render_call = '\n        # Re-render with new zoom level\n        self.render_page()'
            content = content[:method_end - 1] + render_call + content[method_end - 1:]
            print("  ✅ Added render_page call to set_zoom method")

        # Write back the updated content
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing PDF canvas sizing: {e}")
        return False


def fix_wheel_event():
    """Fix wheel event to properly handle scrolling vs zooming"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("🔧 Step 2: Fixing wheel event handling...")

        # Check if wheelEvent exists
        if 'def wheelEvent(self' not in content:
            # Add wheel event method
            wheel_method = '''
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming and scrolling"""
        modifiers = event.modifiers()

        # Ctrl + Wheel = Zoom
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()

            if delta > 0:
                new_zoom = min(self.zoom_level * 1.15, 5.0)
            else:
                new_zoom = max(self.zoom_level / 1.15, 0.1)

            if new_zoom != self.zoom_level:
                self.set_zoom(new_zoom)

            event.accept()
        else:
            # Regular wheel = Pass to parent for scrolling
            super().wheelEvent(event)'''

            # Find a good insertion point
            insert_pos = content.find('    def keyPressEvent(self')
            if insert_pos == -1:
                insert_pos = content.find('    def mousePressEvent(self')
            if insert_pos == -1:
                insert_pos = content.rfind('    def ')
                if insert_pos != -1:
                    # Find end of last method
                    method_end = content.find('\n\n', insert_pos)
                    if method_end != -1:
                        insert_pos = method_end

            if insert_pos != -1:
                content = content[:insert_pos] + wheel_method + '\n' + content[insert_pos:]
                print("  ✅ Added wheelEvent method")
            else:
                print("  ❌ Could not find insertion point for wheelEvent")
                return False
        else:
            # Fix existing wheelEvent to properly pass events to parent
            wheel_start = content.find('def wheelEvent(self')
            if wheel_start != -1:
                # Check if it properly calls super() for regular scrolling
                wheel_section = content[wheel_start:wheel_start + 1000]
                if 'super().wheelEvent(event)' not in wheel_section:
                    # Need to fix the event handling
                    # Replace event.ignore() with super().wheelEvent(event)
                    content = content.replace('event.ignore()', 'super().wheelEvent(event)')
                    print("  ✅ Fixed wheelEvent to pass events to parent")

        # Write back the updated content
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing wheel event: {e}")
        return False


def fix_scroll_area_setup():
    """Fix scroll area configuration in main window"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("🔧 Step 3: Fixing scroll area setup...")

        # Find create_center_panel method
        if 'def create_center_panel(self)' not in content:
            print("  ❌ create_center_panel method not found")
            return False

        # Ensure proper scroll area configuration
        scroll_config = '''
        # Configure scroll area for proper scrolling
        from PyQt6.QtCore import Qt
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)

        # Configure scroll bar step sizes
        v_scrollbar = self.scroll_area.verticalScrollBar()
        h_scrollbar = self.scroll_area.horizontalScrollBar()

        if v_scrollbar:
            v_scrollbar.setSingleStep(20)
            v_scrollbar.setPageStep(200)
        if h_scrollbar:
            h_scrollbar.setSingleStep(20)
            h_scrollbar.setPageStep(200)'''

        # Find where scroll area is created and add configuration
        if 'self.scroll_area = QScrollArea()' in content:
            insertion_point = content.find('self.scroll_area = QScrollArea()')
            line_end = content.find('\n', insertion_point)

            # Check if configuration already exists
            if 'setHorizontalScrollBarPolicy' not in content[line_end:line_end + 500]:
                content = content[:line_end] + scroll_config + content[line_end:]
                print("  ✅ Added scroll area configuration")
            else:
                print("  ✅ Scroll area configuration already exists")

        # Write back the updated content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing scroll area setup: {e}")
        return False


def add_debug_output():
    """Add debug output to verify scrolling is working"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("🔧 Step 4: Adding debug output...")

        # Add debug to render_page if sizing fix was added
        if 'PDF Canvas sized to:' in content:
            print("  ✅ Debug output already added")
            return True

        # Add debug output to track when scrolling should work
        debug_code = '''

        # Debug: Check if scrolling should be enabled
        if self.parent() and hasattr(self.parent(), 'viewport'):
            viewport_size = self.parent().viewport().size()
            widget_size = self.size()
            print(f"📏 Viewport: {viewport_size.width()}x{viewport_size.height()}")
            print(f"📏 Widget: {widget_size.width()}x{widget_size.height()}")
            print(f"📏 Scrolling needed: H={widget_size.width() > viewport_size.width()}, V={widget_size.height() > viewport_size.height()}")'''

        # Find where to insert debug (after sizing is set)
        if 'print(f"📏 PDF Canvas sized to:' in content:
            insertion_point = content.find('print(f"📏 PDF Canvas sized to:')
            line_end = content.find('\n', insertion_point)
            content = content[:line_end] + debug_code + content[line_end:]
            print("  ✅ Added scrolling debug output")

        # Write back the updated content
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error adding debug output: {e}")
        return False


def verify_scrolling_setup():
    """Verify that all scrolling components are in place"""

    print("🔍 Step 5: Verifying scrolling setup...")

    # Check PDF Canvas
    pdf_canvas_path = Path("src/ui/pdf_canvas.py")
    if pdf_canvas_path.exists():
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            pdf_content = f.read()

        pdf_checks = [
            ("Canvas sizing in render_page", "setMinimumSize(pixmap_size)" in pdf_content),
            ("Wheel event handling", "def wheelEvent(self" in pdf_content),
            ("Zoom calls render_page", "self.render_page()" in pdf_content),
        ]

        for check_name, check_result in pdf_checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")

    # Check Main Window
    main_window_path = Path("src/ui/main_window.py")
    if main_window_path.exists():
        with open(main_window_path, 'r', encoding='utf-8') as f:
            main_content = f.read()

        main_checks = [
            ("Scroll area creation", "QScrollArea()" in main_content),
            ("Scroll bar policies", "setHorizontalScrollBarPolicy" in main_content),
            ("Widget resizable", "setWidgetResizable(True)" in main_content),
        ]

        for check_name, check_result in main_checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")

    print("\n🎯 Scrolling should work if all checks above are ✅")


def main():
    """Main function to fix all scrolling issues"""
    print("🔧 PDF Voice Editor - Complete Scrolling Fix")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    print("🎯 Fixing scrolling in 5 steps...")
    print()

    # Step 1: Fix PDF canvas sizing (MOST IMPORTANT)
    if not fix_pdf_canvas_sizing():
        print("❌ Failed step 1 - scrolling will not work")
        return 1

    # Step 2: Fix wheel event handling
    if not fix_wheel_event():
        print("❌ Failed step 2 - mouse wheel may not work")
        # Continue anyway

    # Step 3: Fix scroll area setup
    if not fix_scroll_area_setup():
        print("❌ Failed step 3 - scroll area may not be configured properly")
        # Continue anyway

    # Step 4: Add debug output
    if not add_debug_output():
        print("❌ Failed step 4 - won't have debug info")
        # Continue anyway

    # Step 5: Verify setup
    verify_scrolling_setup()

    print("\n🎉 Scrolling fix complete!")
    print("\n🎯 Expected behavior after fix:")
    print("  1. Open a PDF file")
    print("  2. If PDF is larger than window, scroll bars should appear")
    print("  3. Mouse wheel should scroll vertically")
    print("  4. Shift + mouse wheel should scroll horizontally")
    print("  5. Ctrl + mouse wheel should zoom")
    print("\n🔍 Debug info will show in console:")
    print("  📏 PDF Canvas sized to: [width]x[height]")
    print("  📏 Viewport: [width]x[height]")
    print("  📏 Scrolling needed: H=True/False, V=True/False")
    print("\n🚀 Test now:")
    print("  python launch.py")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())