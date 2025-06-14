#!/usr/bin/env python3
"""
Fix Field Palette Missing Methods
Adds the missing clear_highlights() and highlight_field_type() methods
"""

import os
from pathlib import Path


def fix_field_palette_methods():
    """Add missing methods to FieldPalette and EnhancedFieldPalette classes"""

    field_palette_path = Path("src/ui/field_palette.py")

    if not field_palette_path.exists():
        print(f"❌ File not found: {field_palette_path}")
        return False

    print("🔧 Adding missing methods to field_palette.py...")

    try:
        # Read the current content
        with open(field_palette_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if methods already exist
        if 'def clear_highlights(self):' in content and content.count('def clear_highlights') >= 2:
            print("✅ Methods already exist, skipping...")
            return True

        # Method to add to FieldPalette class
        field_palette_methods = '''
    def clear_highlights(self):
        """Clear all field type highlights"""
        if hasattr(self, 'field_buttons'):
            for field_type in self.field_buttons:
                self.highlight_field_type(field_type, False)

    def highlight_field_type(self, field_type: str, highlight: bool = True):
        """Highlight a specific field type (e.g., when selected)"""
        if not hasattr(self, 'field_buttons') or field_type not in self.field_buttons:
            return

        button = self.field_buttons[field_type]

        if highlight:
            # Apply highlighted style
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 2px solid #0078d4;
                    border-radius: 4px;
                    background-color: #e3f2fd;
                    color: #0078d4;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #bbdefb;
                    border-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #90caf9;
                }
            """)
        else:
            # Reset to default style
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #0078d4;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)
'''

        # Method to add to EnhancedFieldPalette class
        enhanced_field_palette_methods = '''
    def clear_highlights(self):
        """Clear all field type highlights"""
        if hasattr(self.field_palette, 'clear_highlights'):
            self.field_palette.clear_highlights()

    def highlight_field_type(self, field_type: str):
        """Highlight a field type in the palette"""
        # Clear existing highlights first
        if hasattr(self.field_palette, 'clear_highlights'):
            self.field_palette.clear_highlights()

        # Highlight the selected field type
        if field_type and hasattr(self.field_palette, 'highlight_field_type'):
            self.field_palette.highlight_field_type(field_type, True)

        # Update preview widget
        if hasattr(self, 'preview_widget') and field_type:
            self.preview_widget.set_field_type(field_type)
'''

        # Find and modify FieldPalette class
        field_palette_class_start = content.find('class FieldPalette(QWidget):')
        if field_palette_class_start != -1:
            # Find the end of the FieldPalette class (before next class)
            next_class = content.find('\nclass ', field_palette_class_start + 1)
            if next_class == -1:
                next_class = len(content)

            # Find the last method in FieldPalette class
            field_palette_class_content = content[field_palette_class_start:next_class]

            # Look for the set_field_selected method or similar as insertion point
            insertion_point = field_palette_class_content.rfind('    def ')
            if insertion_point != -1:
                # Find the end of that method
                method_end = field_palette_class_content.find('\n\n', insertion_point)
                if method_end == -1:
                    method_end = len(field_palette_class_content)

                # Insert the new methods
                insert_pos = field_palette_class_start + method_end
                content = content[:insert_pos] + field_palette_methods + content[insert_pos:]
                print("  ✅ Added methods to FieldPalette class")

                # Adjust next_class position due to insertion
                next_class += len(field_palette_methods)

        # Find and modify EnhancedFieldPalette class
        enhanced_class_start = content.find('class EnhancedFieldPalette(QWidget):')
        if enhanced_class_start != -1:
            # Find the end of the EnhancedFieldPalette class
            enhanced_next_class = content.find('\nclass ', enhanced_class_start + 1)
            if enhanced_next_class == -1:
                enhanced_next_class = len(content)

            # Find the last method in EnhancedFieldPalette class
            enhanced_class_content = content[enhanced_class_start:enhanced_next_class]

            # Look for the _on_field_requested method or similar as insertion point
            insertion_point = enhanced_class_content.rfind('    def ')
            if insertion_point != -1:
                # Find the end of that method
                method_end = enhanced_class_content.find('\n\n', insertion_point)
                if method_end == -1:
                    method_end = len(enhanced_class_content)

                # Insert the new methods
                insert_pos = enhanced_class_start + method_end
                content = content[:insert_pos] + enhanced_field_palette_methods + content[insert_pos:]
                print("  ✅ Added methods to EnhancedFieldPalette class")

        # Write the updated content back to file
        with open(field_palette_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Successfully added missing methods to field_palette.py")
        return True

    except Exception as e:
        print(f"❌ Error fixing field_palette.py: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Field Palette Method Fixer")
    print("=" * 55)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        print("   Make sure you're running this from the project root directory.")
        return 1

    # Apply the fix
    if fix_field_palette_methods():
        print("\n🎉 Fix applied successfully!")
        print("\n🎯 Next steps:")
        print("1. Run: python launch.py")
        print("2. If you get other errors, let me know!")
        return 0
    else:
        print("\n❌ Fix failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())