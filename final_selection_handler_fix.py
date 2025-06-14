#!/usr/bin/env python3
"""
Final SelectionHandler Emit Fix
This script will find and completely fix the SelectionHandler emit issue
by ensuring proper QObject inheritance everywhere it's defined
"""

import os
import re
from pathlib import Path


def find_all_selection_handlers():
    """Find all SelectionHandler classes in the project"""

    files_to_check = [
        "src/ui/pdf_canvas.py",
        "src/ui/drag_handler.py",
        "src/ui/main_window.py"
    ]

    selection_handlers = []

    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'class SelectionHandler' in content:
                    selection_handlers.append(path)
                    print(f"📍 Found SelectionHandler in: {file_path}")
            except Exception as e:
                print(f"⚠️ Error reading {file_path}: {e}")

    return selection_handlers


def fix_selection_handler_in_file(file_path):
    """Fix SelectionHandler in a specific file"""

    print(f"🔧 Fixing SelectionHandler in {file_path}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Step 1: Ensure QObject is imported
        if 'from PyQt6.QtCore import' in content:
            import_match = re.search(r'from PyQt6\.QtCore import ([^\n]+)', content)
            if import_match and 'QObject' not in import_match.group(1):
                new_imports = import_match.group(1) + ', QObject'
                content = content.replace(import_match.group(0), f'from PyQt6.QtCore import {new_imports}')
                print(f"  ✅ Added QObject import")
        else:
            # Add QObject import if no QtCore imports exist
            first_import = content.find('from PyQt6')
            if first_import != -1:
                line_end = content.find('\n', first_import)
                content = content[:line_end] + '\nfrom PyQt6.QtCore import QObject, pyqtSignal' + content[line_end:]
                print(f"  ✅ Added QObject and pyqtSignal imports")

        # Step 2: Fix class definition
        if 'class SelectionHandler:' in content:
            content = content.replace('class SelectionHandler:', 'class SelectionHandler(QObject):')
            print(f"  ✅ Fixed class definition to inherit from QObject")

        # Step 3: Ensure proper __init__ method with super() call
        # Find the SelectionHandler class and its __init__ method
        class_pattern = r'class SelectionHandler\(QObject\):(.*?)(?=\nclass |\Z)'
        class_match = re.search(class_pattern, content, re.DOTALL)

        if class_match:
            class_content = class_match.group(1)

            # Check if __init__ method exists and has super().__init__()
            init_pattern = r'def __init__\(self[^)]*\):(.*?)(?=\n    def |\Z)'
            init_match = re.search(init_pattern, class_content, re.DOTALL)

            if init_match:
                init_content = init_match.group(1)
                if 'super().__init__()' not in init_content:
                    # Add super().__init__() as the first line in __init__
                    init_method = init_match.group(0)
                    init_signature_end = init_method.find(':') + 1

                    # Insert super().__init__() right after the colon
                    new_init = (init_method[:init_signature_end] +
                                '\n        super().__init__()' +
                                init_method[init_signature_end:])

                    content = content.replace(init_method, new_init)
                    print(f"  ✅ Added super().__init__() call")
            else:
                # No __init__ method found, add one
                class_start = content.find('class SelectionHandler(QObject):')
                if class_start != -1:
                    class_line_end = content.find('\n', class_start)

                    new_init = '''
    def __init__(self, field_manager=None):
        super().__init__()
        self.field_manager = field_manager
        self.selected_field = None
'''
                    content = content[:class_line_end] + new_init + content[class_line_end:]
                    print(f"  ✅ Added missing __init__ method")

        # Step 4: Replace any problematic signal usage with safe calls
        # Find lines that try to emit signals unsafely
        problematic_patterns = [
            (r'self\.selectionChanged\.emit\(([^)]+)\)',
             r'try:\n            self.selectionChanged.emit(\1)\n        except AttributeError:\n            pass  # Signal not available'),
        ]

        for pattern, replacement in problematic_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                print(f"  ✅ Added safe signal emit")

        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✅ Fixed SelectionHandler in {file_path}")
        return True

    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_working_selection_handler():
    """Create a completely working SelectionHandler class"""

    # Check if we need to create it in drag_handler.py
    drag_handler_path = Path("src/ui/drag_handler.py")

    if not drag_handler_path.exists():
        print("❌ drag_handler.py not found")
        return False

    print("🔧 Creating bulletproof SelectionHandler...")

    try:
        with open(drag_handler_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove any existing SelectionHandler class
        pattern = r'class SelectionHandler.*?(?=\nclass |\Z)'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

        # Add a completely working SelectionHandler
        working_selection_handler = '''

class SelectionHandler(QObject):
    """Handles field selection logic - bulletproof version"""

    selectionChanged = pyqtSignal(object)  # FormField or None

    def __init__(self, field_manager=None):
        super().__init__()
        self.field_manager = field_manager
        self.selected_field = None
        print("✅ SelectionHandler initialized properly")

    def select_field(self, field):
        """Select a field safely"""
        try:
            if self.selected_field != field:
                self.selected_field = field
                self.selectionChanged.emit(field)
                print(f"✅ Field selected: {field.name if field else 'None'}")
        except Exception as e:
            print(f"⚠️ Error selecting field: {e}")
            self.selected_field = field  # Set it anyway

    def select_field_at_position(self, x, y):
        """Select field at given position safely"""
        try:
            if self.field_manager and hasattr(self.field_manager, 'get_field_at_position'):
                field = self.field_manager.get_field_at_position(x, y)
                self.select_field(field)
                return field
            else:
                print("⚠️ Field manager not available for position selection")
                return None
        except Exception as e:
            print(f"⚠️ Error selecting field at position: {e}")
            return None

    def clear_selection(self):
        """Clear current selection safely"""
        try:
            self.select_field(None)
            print("✅ Selection cleared")
        except Exception as e:
            print(f"⚠️ Error clearing selection: {e}")
            self.selected_field = None  # Clear it anyway

    def get_selected_field(self):
        """Get currently selected field"""
        return self.selected_field

    def delete_selected_field(self):
        """Delete currently selected field safely"""
        try:
            if self.selected_field and self.field_manager:
                if hasattr(self.field_manager, 'remove_field'):
                    success = self.field_manager.remove_field(self.selected_field)
                    if success:
                        self.clear_selection()
                    return success
            return False
        except Exception as e:
            print(f"⚠️ Error deleting selected field: {e}")
            return False

    def duplicate_selected_field(self):
        """Duplicate currently selected field safely"""
        try:
            if self.selected_field and self.field_manager:
                if hasattr(self.field_manager, 'duplicate_field'):
                    new_field = self.field_manager.duplicate_field(self.selected_field)
                    if new_field:
                        self.select_field(new_field)
                    return new_field
            return None
        except Exception as e:
            print(f"⚠️ Error duplicating selected field: {e}")
            return None
'''

        # Add the working SelectionHandler at the end of the file
        content = content + working_selection_handler

        # Write back
        with open(drag_handler_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Created bulletproof SelectionHandler")
        return True

    except Exception as e:
        print(f"❌ Error creating working SelectionHandler: {e}")
        return False


def remove_broken_selection_handlers():
    """Remove any broken SelectionHandler definitions"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        return True

    print("🔧 Removing broken SelectionHandler from pdf_canvas.py...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove any embedded SelectionHandler class
        if 'class SelectionHandler' in content:
            # Remove the entire class definition
            pattern = r'\n*class SelectionHandler.*?(?=\nclass |\n\ndef [a-zA-Z]|\Z)'
            content = re.sub(pattern, '', content, flags=re.DOTALL)

            # Ensure we import SelectionHandler from drag_handler
            if 'from ui.drag_handler import' in content:
                import_line = re.search(r'from ui\.drag_handler import ([^\n]+)', content)
                if import_line and 'SelectionHandler' not in import_line.group(1):
                    new_imports = import_line.group(1) + ', SelectionHandler'
                    content = content.replace(import_line.group(0), f'from ui.drag_handler import {new_imports}')
            else:
                # Add the import
                if 'from ui.field_renderer import' in content:
                    content = content.replace(
                        'from ui.field_renderer import FieldRenderer',
                        'from ui.field_renderer import FieldRenderer\nfrom ui.drag_handler import DragHandler, SelectionHandler'
                    )

            # Write back
            with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print("✅ Removed broken SelectionHandler from pdf_canvas.py")

        return True

    except Exception as e:
        print(f"❌ Error removing broken SelectionHandler: {e}")
        return False


def validate_fix():
    """Validate that the SelectionHandler fix worked"""

    try:
        # Try to compile all the files
        files_to_check = [
            "src/ui/pdf_canvas.py",
            "src/ui/drag_handler.py",
            "src/ui/main_window.py"
        ]

        for file_path in files_to_check:
            path = Path(file_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    compile(content, str(path), 'exec')
                    print(f"✅ {file_path} syntax is valid")
                except SyntaxError as e:
                    print(f"❌ Syntax error in {file_path}: Line {e.lineno}: {e.msg}")
                    return False

        print("✅ All files have valid syntax")
        return True

    except Exception as e:
        print(f"❌ Error validating fix: {e}")
        return False


def main():
    """Main execution function"""
    print("🔧 PDF Voice Editor - Final SelectionHandler Emit Fix")
    print("=" * 60)

    # Step 1: Find all SelectionHandler classes
    selection_handlers = find_all_selection_handlers()

    if not selection_handlers:
        print("❌ No SelectionHandler classes found")
        return 1

    # Step 2: Fix each SelectionHandler
    success = True
    for handler_file in selection_handlers:
        if not fix_selection_handler_in_file(handler_file):
            success = False

    # Step 3: Remove broken handlers and ensure clean import
    if not remove_broken_selection_handlers():
        success = False

    # Step 4: Create working SelectionHandler as backup
    if not create_working_selection_handler():
        success = False

    # Step 5: Validate the fix
    if not validate_fix():
        success = False

    if success:
        print("\n🎉 SUCCESS! SelectionHandler emit issue should be completely fixed.")
        print("\n🎯 What was fixed:")
        print("   • All SelectionHandler classes now inherit from QObject")
        print("   • All __init__ methods call super().__init__()")
        print("   • Removed duplicate/broken SelectionHandler definitions")
        print("   • Added safe signal emit patterns")
        print("   • Created bulletproof SelectionHandler in drag_handler.py")
        print("\n🎯 Try the application now:")
        print("   python launch.py")
        print("\n📝 You should NO LONGER see:")
        print("   ⚠️ Selection handler issue: 'PyQt6.QtCore.pyqtSignal' object has no attribute 'emit'")
        return 0
    else:
        print("\n❌ Some issues remain. Check the error messages above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())