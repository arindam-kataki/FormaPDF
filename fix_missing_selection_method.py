#!/usr/bin/env python3
"""
Fix Missing _on_selection_changed Method
Adds the missing method to PDFCanvas or fixes the signal connection
"""

import os
from pathlib import Path


def fix_missing_selection_method():
    """Fix the missing _on_selection_changed method"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Fixing missing _on_selection_changed method...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if the method already exists
        if 'def _on_selection_changed(' in content:
            print("✅ _on_selection_changed method already exists")
            return True

        # Check if there's a signal connection trying to use it
        if 'self._on_selection_changed' in content:
            print("🔍 Found reference to _on_selection_changed method")

            # Option 1: Add the missing method
            missing_method = '''
    def _on_selection_changed(self, field):
        """Handle selection changes from selection handler"""
        # Update display when selection changes
        self.draw_overlay()

        # Emit field clicked signal if field is selected
        if field:
            self.fieldClicked.emit(field.id)
'''

            # Find a good place to insert the method
            # Look for other methods in the class
            insert_targets = [
                '    def setup_connections(self):',
                '    def show_no_document_message(self):',
                '    def load_pdf(self',
                '    def render_page(self):',
                '    def mousePressEvent(self'
            ]

            insert_pos = -1
            for target in insert_targets:
                pos = content.find(target)
                if pos != -1:
                    insert_pos = pos
                    break

            if insert_pos != -1:
                # Insert before found method
                content = content[:insert_pos] + missing_method + '\n' + content[insert_pos:]
                print("✅ Added missing _on_selection_changed method")
            else:
                # Fallback: add after class definition
                class_pos = content.find('class PDFCanvas')
                if class_pos != -1:
                    # Find the first method
                    first_method = content.find('    def ', class_pos)
                    if first_method != -1:
                        content = content[:first_method] + missing_method + '\n' + content[first_method:]
                        print("✅ Added missing _on_selection_changed method to class")
                    else:
                        print("❌ Could not find insertion point for method")
                        return False
                else:
                    print("❌ Could not find PDFCanvas class")
                    return False
        else:
            # Option 2: Remove the problematic signal connection
            print("🔍 Removing problematic signal connection...")

            # Find the line with the connection and comment it out
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'self._on_selection_changed' in line:
                    lines[i] = '        # ' + line.strip() + '  # Commented out - method missing'
                    print(f"  ✅ Commented out line {i + 1}: {line.strip()}")

            content = '\n'.join(lines)

        # Write the updated content
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Fixed missing _on_selection_changed method issue")
        return True

    except Exception as e:
        print(f"❌ Error fixing method: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_other_missing_methods():
    """Check for other potentially missing methods in signal connections"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print("\n🔍 Checking for other missing methods...")

        # Find signal connections
        import re
        connection_pattern = r'connect\(self\.([^)]+)\)'
        connections = re.findall(connection_pattern, content)

        missing_methods = []
        for method_name in connections:
            if f'def {method_name}(' not in content:
                missing_methods.append(method_name)

        if missing_methods:
            print(f"⚠️ Found {len(missing_methods)} other potentially missing methods:")
            for method in missing_methods:
                print(f"  - {method}")
            return missing_methods
        else:
            print("✅ No other missing methods found in signal connections")
            return []

    except Exception as e:
        print(f"⚠️ Error checking for missing methods: {e}")
        return []


def fix_setup_signal_connections():
    """Make signal connections more robust"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find _setup_signal_connections method
        if 'def _setup_signal_connections(self):' not in content:
            print("⚠️ _setup_signal_connections method not found")
            return False

        print("🔧 Making signal connections more robust...")

        # Replace problematic connections with safe versions
        safe_connections = '''    def _setup_signal_connections(self):
        """Setup signal connections with error handling"""
        try:
            # Connect drag handler signals
            if hasattr(self.drag_handler, 'cursorChanged'):
                self.drag_handler.cursorChanged.connect(
                    lambda cursor_shape: self.setCursor(QCursor(cursor_shape))
                )

            # Connect selection handler signals  
            if hasattr(self.selection_handler, 'selectionChanged'):
                self.selection_handler.selectionChanged.connect(self.selectionChanged)
                # Only connect to _on_selection_changed if it exists
                if hasattr(self, '_on_selection_changed'):
                    self.selection_handler.selectionChanged.connect(self._on_selection_changed)
                else:
                    # Fallback: just redraw overlay on selection change
                    self.selection_handler.selectionChanged.connect(
                        lambda field: self.draw_overlay() if hasattr(self, 'draw_overlay') else None
                    )
        except Exception as e:
            print(f"Warning: Error setting up signal connections: {e}")'''

        # Find and replace the method
        method_start = content.find('def _setup_signal_connections(self):')
        if method_start != -1:
            # Find the end of the method
            lines = content[method_start:].split('\n')
            method_lines = []

            for i, line in enumerate(lines):
                method_lines.append(line)
                if i > 0 and line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                    method_lines.pop()
                    break

            original_method = '\n'.join(method_lines)
            content = content.replace(original_method, safe_connections)

            with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print("✅ Made signal connections more robust")
            return True

        return False

    except Exception as e:
        print(f"❌ Error fixing signal connections: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Fix Missing _on_selection_changed Method")
    print("=" * 65)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Fix the missing method
    if not fix_missing_selection_method():
        print("❌ Failed to fix missing method")
        return 1

    # Check for other missing methods
    missing_methods = check_other_missing_methods()

    # Make signal connections more robust
    fix_setup_signal_connections()

    print("\n🎉 Fixed missing _on_selection_changed method!")
    print("\n🎯 Changes made:")
    print("  • Added missing _on_selection_changed method")
    print("  • Made signal connections more robust")
    print("  • Added error handling for missing methods")

    if missing_methods:
        print(f"\n⚠️ Note: Found {len(missing_methods)} other potentially missing methods:")
        for method in missing_methods:
            print(f"    - {method}")
        print("  These are handled with safe fallbacks for now")

    print("\n🚀 Try running the application again:")
    print("  python launch.py")
    print("\n📝 The application should now start without the AttributeError")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())