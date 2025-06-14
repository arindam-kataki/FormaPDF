#!/usr/bin/env python3
"""
Fix Main Window Safe Method Calls
Makes all method calls to field_palette safe by checking if methods exist first
"""

import os
from pathlib import Path


def fix_main_window_method_calls():
    """Make field_palette method calls safe in main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Making method calls safe in main_window.py...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # List of replacements to make method calls safe
        replacements = [
            # clear_highlights method calls
            (
                'self.field_palette.clear_highlights()',
                'if hasattr(self.field_palette, "clear_highlights"):\n            self.field_palette.clear_highlights()'
            ),
            # highlight_field_type method calls
            (
                'self.field_palette.highlight_field_type(field_type, True)',
                'if hasattr(self.field_palette, "highlight_field_type"):\n            self.field_palette.highlight_field_type(field_type, True)'
            ),
            (
                'self.field_palette.highlight_field_type(selected_field.type.value)',
                'if hasattr(self.field_palette, "highlight_field_type"):\n            self.field_palette.highlight_field_type(selected_field.type.value)'
            ),
            (
                'self.field_palette.highlight_field_type(field.type.value)',
                'if hasattr(self.field_palette, "highlight_field_type"):\n            self.field_palette.highlight_field_type(field.type.value)'
            ),
            # set_field_selected method calls
            (
                'self.field_palette.set_field_selected(True)',
                'if hasattr(self.field_palette, "set_field_selected"):\n            self.field_palette.set_field_selected(True)'
            ),
            (
                'self.field_palette.set_field_selected(False)',
                'if hasattr(self.field_palette, "set_field_selected"):\n            self.field_palette.set_field_selected(False)'
            ),
        ]

        # Apply all replacements
        changes_made = 0
        for old_code, new_code in replacements:
            if old_code in content:
                content = content.replace(old_code, new_code)
                changes_made += 1
                print(f"  ✅ Made safe: {old_code[:50]}...")

        # Also add a safety wrapper function at the top of the class if not present
        safety_wrapper = '''    def _safe_call_field_palette(self, method_name: str, *args, **kwargs):
        """Safely call a method on field_palette if it exists"""
        if hasattr(self.field_palette, method_name):
            method = getattr(self.field_palette, method_name)
            return method(*args, **kwargs)
        return None

'''

        # Find the PDFViewerMainWindow class and add the safety wrapper
        class_start = content.find('class PDFViewerMainWindow(QMainWindow):')
        if class_start != -1 and '_safe_call_field_palette' not in content:
            # Find the first method in the class
            first_method = content.find('    def ', class_start)
            if first_method != -1:
                content = content[:first_method] + safety_wrapper + content[first_method:]
                print("  ✅ Added safety wrapper method")
                changes_made += 1

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Made {changes_made} method calls safe in main_window.py")
        return True

    except Exception as e:
        print(f"❌ Error fixing main_window.py: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Main Window Safe Calls Fixer")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        print("   Make sure you're running this from the project root directory.")
        return 1

    # Apply the fix
    if fix_main_window_method_calls():
        print("\n🎉 Fix applied successfully!")
        print("\n🎯 Next steps:")
        print("1. Run: python fix_field_palette_missing_methods.py")
        print("2. Then run: python launch.py")
        print("3. If you get other errors, let me know!")
        return 0
    else:
        print("\n❌ Fix failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())