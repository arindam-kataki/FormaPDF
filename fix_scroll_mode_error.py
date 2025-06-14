#!/usr/bin/env python3
"""
Fix QScrollArea Method Error for PyQt6
Replaces incorrect scroll mode methods with PyQt6-compatible ones
"""

import os
from pathlib import Path


def fix_scroll_mode_methods():
    """Fix incorrect QScrollArea methods in main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Fixing QScrollArea methods for PyQt6 compatibility...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove incorrect method calls
        incorrect_methods = [
            'self.scroll_area.setVerticalScrollMode(QScrollArea.ScrollMode.ScrollPerPixel)',
            'self.scroll_area.setHorizontalScrollMode(QScrollArea.ScrollMode.ScrollPerPixel)',
            '.setVerticalScrollMode(QScrollArea.ScrollMode.ScrollPerPixel)',
            '.setHorizontalScrollMode(QScrollArea.ScrollMode.ScrollPerPixel)'
        ]

        fixed = False
        for method in incorrect_methods:
            if method in content:
                content = content.replace(method, '# Scroll mode configuration removed (PyQt6 compatibility)')
                fixed = True
                print(f"✅ Removed: {method}")

        # Also fix in the enable_smooth_scrolling method if it exists
        if 'def enable_smooth_scrolling(self):' in content:
            # Find the method and replace incorrect calls
            method_start = content.find('def enable_smooth_scrolling(self):')
            method_end = content.find('\n    def ', method_start + 1)
            if method_end == -1:
                method_end = content.find('\ndef ', method_start + 1)
            if method_end == -1:
                method_end = len(content)

            method_content = content[method_start:method_end]

            # Replace the method with a working version
            corrected_method = '''    def enable_smooth_scrolling(self):
        """Enable smooth scrolling for the scroll area"""
        if hasattr(self, 'scroll_area'):
            # Configure scroll bar step sizes for smoother scrolling
            v_scrollbar = self.scroll_area.verticalScrollBar()
            h_scrollbar = self.scroll_area.horizontalScrollBar()

            if v_scrollbar:
                v_scrollbar.setSingleStep(10)
                v_scrollbar.setPageStep(100)
            if h_scrollbar:
                h_scrollbar.setSingleStep(10)
                h_scrollbar.setPageStep(100)'''

            content = content[:method_start] + corrected_method + content[method_end:]
            print("✅ Fixed enable_smooth_scrolling method")
            fixed = True

        # Fix the enhanced scroll area setup in create_center_panel
        if 'Enhanced scroll area configuration' in content:
            # Find and replace the problematic section
            setup_start = content.find('# Enhanced scroll area configuration')
            setup_end = content.find('self.scroll_area.setWidget(', setup_start)
            if setup_end == -1:
                setup_end = content.find('return self.scroll_area', setup_start)

            if setup_start != -1 and setup_end != -1:
                # Replace with working configuration
                working_setup = '''        # Enhanced scroll area configuration
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Configure scroll bars
        from PyQt6.QtCore import Qt
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Configure smooth scrolling via scroll bar settings
        v_scrollbar = self.scroll_area.verticalScrollBar()
        h_scrollbar = self.scroll_area.horizontalScrollBar()

        if v_scrollbar:
            v_scrollbar.setSingleStep(10)
            v_scrollbar.setPageStep(100)
        if h_scrollbar:
            h_scrollbar.setSingleStep(10)
            h_scrollbar.setPageStep(100)

'''
                content = content[:setup_start] + working_setup + content[setup_end:]
                print("✅ Fixed enhanced scroll area configuration")
                fixed = True

        # Write the corrected content back
        if fixed:
            with open(main_window_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Successfully fixed QScrollArea method errors")
        else:
            print("✅ No QScrollArea method errors found")

        return True

    except Exception as e:
        print(f"❌ Error fixing scroll mode methods: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_scroll_area_setup():
    """Verify that scroll area setup is now correct"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("🔍 Verifying scroll area setup...")

        # Check for problematic methods
        problematic_methods = [
            'setVerticalScrollMode',
            'setHorizontalScrollMode',
            'ScrollMode.ScrollPerPixel'
        ]

        issues_found = []
        for method in problematic_methods:
            if method in content:
                issues_found.append(method)

        if issues_found:
            print(f"❌ Still found problematic methods: {', '.join(issues_found)}")
            return False
        else:
            print("✅ No problematic scroll methods found")

        # Check for correct alternatives
        correct_methods = [
            'setHorizontalScrollBarPolicy',
            'setVerticalScrollBarPolicy',
            'setSingleStep',
            'setPageStep'
        ]

        for method in correct_methods:
            if method in content:
                print(f"✅ Found correct method: {method}")
            else:
                print(f"⚠️ Missing method: {method}")

        return True

    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return False


def create_minimal_scroll_setup():
    """Create a minimal, working scroll area setup if needed"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # If create_center_panel is completely broken, replace it with minimal version
        if 'def create_center_panel(self)' in content:
            method_start = content.find('def create_center_panel(self)')
            method_end = content.find('\n    def ', method_start + 1)
            if method_end == -1:
                method_end = content.find('\ndef ', method_start + 1)
            if method_end == -1:
                method_end = len(content)

            method_content = content[method_start:method_end]

            # Check if it contains problematic code
            if 'setVerticalScrollMode' in method_content or 'setHorizontalScrollMode' in method_content:
                print("🔧 Replacing broken create_center_panel method...")

                # Replace with minimal working version
                minimal_method = '''    def create_center_panel(self) -> QWidget:
        """Create center panel with PDF viewer"""
        # Simple scroll area for PDF canvas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Basic scroll bar configuration
        from PyQt6.QtCore import Qt
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # PDF canvas (with fallback)
        if PDF_CANVAS_AVAILABLE and PDFCanvas:
            self.pdf_canvas = PDFCanvas()
        else:
            # Fallback widget
            self.pdf_canvas = QLabel(
                "PDF Canvas Not Available\\n\\n"
                "Some modules are missing.\\n"
                "The application is running in limited mode.\\n\\n"
                "To fix this:\\n"
                "1. Ensure all Python files are present\\n"
                "2. Run the fix scripts\\n"
                "3. Check imports"
            )
            self.pdf_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pdf_canvas.setStyleSheet("""
                border: 2px dashed #ccc; 
                background-color: #f9f9f9; 
                color: #666;
                font-size: 14px;
                padding: 40px;
            """)

        self.scroll_area.setWidget(self.pdf_canvas)
        return self.scroll_area'''

                content = content[:method_start] + minimal_method + '\n' + content[method_end:]

                with open(main_window_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                print("✅ Replaced with minimal working create_center_panel method")
                return True

        print("✅ create_center_panel method looks okay")
        return True

    except Exception as e:
        print(f"❌ Error creating minimal scroll setup: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Fix QScrollArea Method Error")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Fix scroll mode methods
    if not fix_scroll_mode_methods():
        print("❌ Failed to fix scroll mode methods")
        return 1

    # Create minimal scroll setup if needed
    if not create_minimal_scroll_setup():
        print("❌ Failed to create minimal scroll setup")
        return 1

    # Verify the setup
    if verify_scroll_area_setup():
        print("\n🎉 QScrollArea methods fixed successfully!")
        print("\n🎯 Changes made:")
        print("  ✅ Removed incompatible setVerticalScrollMode calls")
        print("  ✅ Removed incompatible setHorizontalScrollMode calls")
        print("  ✅ Replaced with PyQt6-compatible scroll bar configuration")
        print("  ✅ Maintained smooth scrolling via scroll bar settings")
        print("\n🚀 Test the application now:")
        print("  python launch.py")
        print("\n📝 Note: Basic scrolling will work with mouse wheel and scroll bars")
        return 0
    else:
        print("\n⚠️ Some issues may remain. Please check the output above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())