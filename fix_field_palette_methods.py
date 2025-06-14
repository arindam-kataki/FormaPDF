"""
Fix missing methods in EnhancedFieldPalette
"""


def fix_field_palette_methods():
    """Add missing methods to EnhancedFieldPalette class"""

    from pathlib import Path

    field_palette_path = Path("src/ui/field_palette.py")

    if not field_palette_path.exists():
        print(f"File not found: {field_palette_path}")
        return False

    print("Adding missing methods to EnhancedFieldPalette...")

    try:
        # Read the file
        with open(field_palette_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if clear_highlights method exists
        if 'def clear_highlights(self):' not in content:
            # Add the missing method to EnhancedFieldPalette class
            # Find the end of the EnhancedFieldPalette class
            enhanced_class_end = content.find('class EnhancedFieldPalette')
            if enhanced_class_end != -1:
                # Find the end of the class (next class or end of file)
                next_class = content.find('\nclass ', enhanced_class_end + 1)
                if next_class == -1:
                    next_class = len(content)

                # Find a good place to insert the method (before the last method)
                insert_pos = content.rfind('    def ', enhanced_class_end, next_class)
                if insert_pos != -1:
                    # Find the end of that method
                    method_end = content.find('\n\n', insert_pos)
                    if method_end == -1:
                        method_end = next_class

                    # Insert the missing methods
                    missing_methods = '''
    def clear_highlights(self):
        """Clear all field type highlights"""
        self.field_palette.clear_highlights()

    def highlight_field_type(self, field_type: str):
        """Highlight a field type in the palette"""
        self.field_palette.clear_highlights()
        if field_type:
            self.field_palette.highlight_field_type(field_type, True)
            self.preview_widget.set_field_type(field_type)
'''

                    content = content[:method_end] + missing_methods + content[method_end:]
                    print("  ✅ Added clear_highlights and highlight_field_type methods")

        # Also check if FieldPalette class has the required methods
        if 'def clear_highlights(self):' not in content:
            # Find the FieldPalette class
            field_palette_class = content.find('class FieldPalette(QWidget):')
            if field_palette_class != -1:
                # Find the end of the FieldPalette class
                next_class = content.find('\nclass ', field_palette_class + 1)
                if next_class == -1:
                    # Look for EnhancedFieldPalette class instead
                    next_class = content.find('\nclass EnhancedFieldPalette', field_palette_class + 1)
                if next_class == -1:
                    next_class = len(content)

                # Find the last method in FieldPalette class
                insert_pos = content.rfind('    def ', field_palette_class, next_class)
                if insert_pos != -1:
                    method_end = content.find('\n\n', insert_pos)
                    if method_end == -1 or method_end > next_class:
                        method_end = next_class

                    # Add missing methods to FieldPalette
                    base_methods = '''
    def clear_highlights(self):
        """Clear all field type highlights"""
        for field_type in self.field_buttons:
            self.highlight_field_type(field_type, False)

    def highlight_field_type(self, field_type: str, highlight: bool = True):
        """Highlight a specific field type"""
        if field_type in self.field_buttons:
            button = self.field_buttons[field_type]
            if highlight:
                button.setStyleSheet(button.styleSheet() + """
                    QPushButton {
                        background-color: #e3f2fd;
                        border-color: #0078d4;
                        border-width: 2px;
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

                    content = content[:method_end] + base_methods + content[method_end:]
                    print("  ✅ Added missing methods to FieldPalette class")

        # Write back the fixed content
        with open(field_palette_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ field_palette.py methods added!")
        return True

    except Exception as e:
        print(f"Error fixing field_palette.py: {e}")
        return False


if __name__ == "__main__":
    fix_field_palette_methods()