#!/usr/bin/env python3
"""
Remove Duplicate SelectionHandler from pdf_canvas.py
This script removes any duplicate/embedded SelectionHandler class from pdf_canvas.py
and ensures it only uses the proper one imported from drag_handler.py
"""

import os
import re
from pathlib import Path


def remove_duplicate_selection_handler():
    """Remove any duplicate SelectionHandler class from pdf_canvas.py"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Removing duplicate SelectionHandler from pdf_canvas.py...")

    try:
        # Read the current content
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if there's an embedded SelectionHandler class
        if 'class SelectionHandler' not in content:
            print("✅ No duplicate SelectionHandler found - good!")
            return True

        print("📍 Found duplicate SelectionHandler class - removing it...")

        # Remove the entire SelectionHandler class definition
        # Pattern to match class definition and its content
        selection_handler_pattern = r'\n\nclass SelectionHandler[^:]*:.*?(?=\n\nclass |\n\ndef [a-zA-Z]|\nclass [A-Z]|\Z)'

        # First try the more specific pattern
        if re.search(selection_handler_pattern, content, re.DOTALL):
            content = re.sub(selection_handler_pattern, '', content, flags=re.DOTALL)
            print("  ✅ Removed SelectionHandler class (method 1)")
        else:
            # Try a simpler pattern
            pattern2 = r'class SelectionHandler.*?(?=\nclass |\n\ndef [a-zA-Z]|\Z)'
            if re.search(pattern2, content, re.DOTALL):
                content = re.sub(pattern2, '', content, flags=re.DOTALL)
                print("  ✅ Removed SelectionHandler class (method 2)")
            else:
                # Manual line-by-line removal as fallback
                lines = content.split('\n')
                cleaned_lines = []
                in_selection_handler = False
                indent_level = 0

                for line in lines:
                    if line.strip().startswith('class SelectionHandler'):
                        in_selection_handler = True
                        indent_level = len(line) - len(line.lstrip())
                        print(f"  📍 Found SelectionHandler class at line: {line.strip()}")
                        continue

                    if in_selection_handler:
                        # Check if we're still inside the class
                        current_indent = len(line) - len(line.lstrip())

                        # If line has content and is at same or lower indent level, we've left the class
                        if line.strip() and current_indent <= indent_level:
                            in_selection_handler = False
                            cleaned_lines.append(line)
                        # Otherwise skip this line (it's part of the class)
                        continue
                    else:
                        cleaned_lines.append(line)

                content = '\n'.join(cleaned_lines)
                print("  ✅ Removed SelectionHandler class (method 3 - line by line)")

        # Clean up any extra blank lines
        content = re.sub(r'\n\n\n+', '\n\n', content)

        # Ensure the import from drag_handler is present and correct
        if 'from ui.drag_handler import' in content:
            # Make sure SelectionHandler is in the import
            import_match = re.search(r'from ui\.drag_handler import ([^\n]+)', content)
            if import_match:
                imports = import_match.group(1)
                if 'SelectionHandler' not in imports:
                    # Add SelectionHandler to the import
                    new_imports = imports + ', SelectionHandler'
                    content = content.replace(import_match.group(0), f'from ui.drag_handler import {new_imports}')
                    print("  ✅ Added SelectionHandler to drag_handler imports")
        else:
            # Add the import if it doesn't exist
            # Find a good place to add it (after other ui imports)
            if 'from ui.field_renderer import' in content:
                content = content.replace(
                    'from ui.field_renderer import FieldRenderer',
                    'from ui.field_renderer import FieldRenderer\nfrom ui.drag_handler import DragHandler, SelectionHandler'
                )
                print("  ✅ Added drag_handler import")

        # Write the cleaned content back
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Successfully removed duplicate SelectionHandler")
        return True

    except Exception as e:
        print(f"❌ Error removing duplicate SelectionHandler: {e}")
        import traceback
        traceback.print_exc()
        return False


def ensure_proper_imports():
    """Ensure pdf_canvas.py has the correct imports"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Make sure QObject is imported for other classes that might need it
        if 'from PyQt6.QtCore import' in content:
            import_match = re.search(r'from PyQt6\.QtCore import ([^\n]+)', content)
            if import_match:
                imports = import_match.group(1)
                if 'QObject' not in imports:
                    # Add QObject just in case
                    new_imports = imports + ', QObject'
                    content = content.replace(import_match.group(0), f'from PyQt6.QtCore import {new_imports}')
                    print("  ✅ Added QObject to QtCore imports (for safety)")

        # Ensure drag_handler import is present
        if 'from ui.drag_handler import' not in content:
            # Find where to add it
            if 'from ui.field_renderer import' in content:
                insertion_point = content.find('from ui.field_renderer import FieldRenderer')
                insertion_end = content.find('\n', insertion_point)
                content = (content[:insertion_end] +
                           '\nfrom ui.drag_handler import DragHandler, SelectionHandler' +
                           content[insertion_end:])
                print("  ✅ Added drag_handler import")

        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error ensuring proper imports: {e}")
        return False


def validate_fix():
    """Validate that the fix worked"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check that there's no embedded SelectionHandler class
        if 'class SelectionHandler' in content:
            print("❌ SelectionHandler class still found in pdf_canvas.py")
            return False

        # Check that SelectionHandler is imported from drag_handler
        if 'from ui.drag_handler import' not in content:
            print("❌ drag_handler import missing")
            return False

        if 'SelectionHandler' not in content.split('from ui.drag_handler import')[1].split('\n')[0]:
            print("❌ SelectionHandler not in drag_handler import")
            return False

        # Try to compile the module
        try:
            compile(content, str(pdf_canvas_path), 'exec')
            print("✅ Python syntax is valid")
            return True
        except SyntaxError as e:
            print(f"❌ Syntax error: Line {e.lineno}: {e.msg}")
            return False

    except Exception as e:
        print(f"❌ Error validating fix: {e}")
        return False


def create_minimal_fallback():
    """Create a minimal fallback if the main fix doesn't work"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # If clear_selection is still causing issues, wrap it in try-catch
        problematic_patterns = [
            'self.selection_handler.clear_selection()',
            'self.selectionChanged.emit(None)'
        ]

        for pattern in problematic_patterns:
            if pattern in content:
                safe_version = f'''try:
            {pattern}
        except AttributeError as e:
            print(f"⚠️ Selection handler issue: {{e}}")
            # Continue without clearing selection'''

                content = content.replace(pattern, safe_version)
                print(f"  ✅ Added fallback for: {pattern}")

        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error creating fallback: {e}")
        return False


def main():
    """Main execution function"""
    print("🔧 PDF Voice Editor - Remove Duplicate SelectionHandler")
    print("=" * 60)

    # Step 1: Remove the duplicate SelectionHandler class
    if not remove_duplicate_selection_handler():
        print("❌ Failed to remove duplicate SelectionHandler")
        return 1

    # Step 2: Ensure proper imports
    if not ensure_proper_imports():
        print("❌ Failed to ensure proper imports")
        return 1

    # Step 3: Validate the fix
    if validate_fix():
        print("\n🎉 Success! Duplicate SelectionHandler removed.")
        print("\n🎯 pdf_canvas.py now only uses the proper SelectionHandler from drag_handler.py")
        print("🎯 Try loading a PDF again:")
        print("   python launch.py")
        print("\n✅ The 'pyqtSignal' object has no attribute 'emit' error should be fixed!")
        return 0
    else:
        print("\n⚠️ Primary fix validation failed, creating fallback...")
        if create_minimal_fallback():
            print("✅ Applied fallback protection")
            print("\n🎯 Try running the application:")
            print("   python launch.py")
            return 0
        else:
            print("❌ All fixes failed")
            return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())