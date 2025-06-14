#!/usr/bin/env python3
"""
Add Missing _on_selection_changed Method
Adds the missing method that signal connections are trying to use
"""

import os
from pathlib import Path


def add_missing_method():
    """Add the missing _on_selection_changed method to PDFCanvas"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Adding missing _on_selection_changed method...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if method already exists
        if 'def _on_selection_changed(' in content:
            print("✅ _on_selection_changed method already exists")
            return True

        # Add the missing method
        missing_method = '''
    def _on_selection_changed(self, field):
        """Handle selection changes from selection handler"""
        try:
            # Update display when selection changes
            if hasattr(self, 'draw_overlay'):
                self.draw_overlay()

            # Emit field clicked signal if field is selected
            if field and hasattr(self, 'fieldClicked'):
                self.fieldClicked.emit(field.id)
        except Exception as e:
            print(f"Error in _on_selection_changed: {e}")
'''

        # Find a good place to insert the method
        # Look for other signal-related methods or near the end of the class
        insert_targets = [
            '    def _setup_signal_connections(self):',
            '    def setup_connections(self):',
            '    def mousePressEvent(self',
            '    def keyPressEvent(self',
            '    def wheelEvent(self'
        ]

        insert_pos = -1
        for target in insert_targets:
            pos = content.find(target)
            if pos != -1:
                insert_pos = pos
                break

        if insert_pos != -1:
            # Insert before the found method
            content = content[:insert_pos] + missing_method + '\n' + content[insert_pos:]
            print("✅ Added _on_selection_changed method")
        else:
            # Fallback: find the end of the class and insert there
            class_pos = content.find('class PDFCanvas')
            if class_pos != -1:
                # Find the last method in the class
                last_method = content.rfind('    def ', class_pos)
                if last_method != -1:
                    # Find the end of the last method
                    method_end = content.find('\n\n', last_method)
                    if method_end == -1:
                        # No double newline found, try single newline + non-indented line
                        search_pos = last_method + 50  # Start search after method signature
                        while search_pos < len(content):
                            newline_pos = content.find('\n', search_pos)
                            if newline_pos == -1:
                                method_end = len(content)
                                break
                            next_line_start = newline_pos + 1
                            if next_line_start >= len(content):
                                method_end = len(content)
                                break
                            next_line = content[next_line_start:content.find('\n', next_line_start)]
                            if next_line and not next_line.startswith('    ') and not next_line.startswith('\t'):
                                method_end = newline_pos
                                break
                            search_pos = newline_pos + 1
                        else:
                            method_end = len(content)

                    content = content[:method_end] + missing_method + '\n' + content[method_end:]
                    print("✅ Added _on_selection_changed method at end of class")
                else:
                    print("❌ Could not find insertion point in class")
                    return False
            else:
                print("❌ Could not find PDFCanvas class")
                return False

        # Write the updated content
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error adding method: {e}")
        import traceback
        traceback.print_exc()
        return False


def make_signal_connections_safe():
    """Make signal connections more robust to handle missing methods"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("🔧 Making signal connections safer...")

        # Find _setup_signal_connections method
        if 'def _setup_signal_connections(self):' not in content:
            print("⚠️ _setup_signal_connections method not found")
            return False

        # Replace the problematic connection with a safe version
        old_connection = 'self.selection_handler.selectionChanged.connect(self._on_selection_changed)'
        new_connection = '''# Safe connection - only connect if method exists
        if hasattr(self, '_on_selection_changed'):
            self.selection_handler.selectionChanged.connect(self._on_selection_changed)
        else:
            # Fallback: just redraw overlay on selection change
            self.selection_handler.selectionChanged.connect(
                lambda field: self.draw_overlay() if hasattr(self, 'draw_overlay') else None
            )'''

        if old_connection in content:
            content = content.replace(old_connection, new_connection)
            print("✅ Made selection signal connection safer")

            # Write the updated content
            with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error making connections safe: {e}")
        return False


def verify_fix():
    """Verify that the fix worked by testing the method exists"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check that method exists
        if 'def _on_selection_changed(' in content:
            print("✅ _on_selection_changed method found")

            # Try to compile the file
            compile(content, pdf_canvas_path, 'exec')
            print("✅ File compiles without errors")
            return True
        else:
            print("❌ _on_selection_changed method still missing")
            return False

    except SyntaxError as e:
        print(f"❌ Syntax error: {e.msg} at line {e.lineno}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Add Missing _on_selection_changed Method")
    print("=" * 65)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Add the missing method
    if not add_missing_method():
        print("❌ Failed to add missing method")
        return 1

    # Make signal connections safer
    if not make_signal_connections_safe():
        print("❌ Failed to make signal connections safe")
        # Continue anyway

    # Verify the fix
    if verify_fix():
        print("\n🎉 Missing method added successfully!")
        print("\n🎯 What was added:")
        print("  • _on_selection_changed method to handle selection changes")
        print("  • Safe error handling in the method")
        print("  • Fallback behavior if draw_overlay doesn't exist")
        print("\n🚀 Test the application now:")
        print("  python launch.py")
        print("\n📝 The app should start and you can test:")
        print("  • Opening PDF files")
        print("  • Checking if scroll bars appear")
        print("  • Testing mouse wheel scrolling")
        return 0
    else:
        print("\n❌ Fix verification failed")
        print("Check the error messages above")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())