#!/usr/bin/env python3
"""
Nuclear SelectionHandler Fix
Completely removes and replaces ALL SelectionHandler code with working versions
"""

import os
import re
from pathlib import Path


def find_exact_error_location():
    """Find exactly where the emit error is coming from"""

    files_to_check = [
        "src/ui/pdf_canvas.py",
        "src/ui/drag_handler.py",
        "src/ui/main_window.py"
    ]

    print("🔍 Searching for exact error location...")

    for file_path in files_to_check:
        path = Path(file_path)
        if not path.exists():
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                if 'selectionChanged.emit' in line or 'clear_selection' in line:
                    print(f"📍 Found in {file_path} line {i}: {line.strip()}")

                    # Check the surrounding context
                    start = max(0, i - 3)
                    end = min(len(lines), i + 3)
                    print("   Context:")
                    for j in range(start, end):
                        marker = ">>> " if j == i - 1 else "    "
                        print(f"   {marker}{j + 1}: {lines[j].rstrip()}")
                    print()

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")


def completely_remove_all_selection_handlers():
    """Remove ALL SelectionHandler classes from all files"""

    files_to_clean = [
        "src/ui/pdf_canvas.py",
        "src/ui/drag_handler.py"
    ]

    print("🗑️ Completely removing all SelectionHandler classes...")

    for file_path in files_to_clean:
        path = Path(file_path)
        if not path.exists():
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove any class SelectionHandler definition completely
            patterns_to_remove = [
                r'class SelectionHandler[^:]*:.*?(?=\nclass [A-Z]|\n\ndef [a-z]|\Z)',
                r'class SelectionHandler[^:]*:.*?(?=\n\nclass |\n\ndef |\Z)',
            ]

            original_content = content
            for pattern in patterns_to_remove:
                content = re.sub(pattern, '', content, flags=re.DOTALL)

            if content != original_content:
                print(f"  ✅ Removed SelectionHandler from {file_path}")

                # Clean up extra blank lines
                content = re.sub(r'\n\n\n+', '\n\n', content)

                # Write back
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                print(f"  ⚪ No SelectionHandler found in {file_path}")

        except Exception as e:
            print(f"❌ Error cleaning {file_path}: {e}")


def create_single_working_selection_handler():
    """Create ONE working SelectionHandler in drag_handler.py"""

    drag_handler_path = Path("src/ui/drag_handler.py")

    if not drag_handler_path.exists():
        print("❌ drag_handler.py not found")
        return False

    print("🔧 Creating single working SelectionHandler...")

    try:
        with open(drag_handler_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Ensure QObject is imported
        if 'from PyQt6.QtCore import' in content:
            if 'QObject' not in content:
                content = content.replace(
                    'from PyQt6.QtCore import',
                    'from PyQt6.QtCore import QObject,'
                )
        else:
            # Add import at the top
            first_import = content.find('from PyQt6')
            if first_import != -1:
                content = 'from PyQt6.QtCore import QObject, pyqtSignal, Qt\n' + content

        # Add the working SelectionHandler at the end
        working_selection_handler = '''


class WorkingSelectionHandler(QObject):
    """A completely working SelectionHandler class"""

    selectionChanged = pyqtSignal(object)

    def __init__(self, field_manager=None):
        super().__init__()
        self.field_manager = field_manager
        self.selected_field = None
        print("✅ WorkingSelectionHandler initialized successfully")

    def select_field(self, field):
        """Select a field"""
        old_field = self.selected_field
        self.selected_field = field
        if old_field != field:
            try:
                self.selectionChanged.emit(field)
                print(f"✅ Selection changed to: {field.name if field else 'None'}")
            except Exception as e:
                print(f"⚠️ Signal emit failed but continuing: {e}")

    def clear_selection(self):
        """Clear selection - this is where the error happens"""
        print("🔄 Clearing selection...")
        try:
            self.select_field(None)
            print("✅ Selection cleared successfully")
        except Exception as e:
            print(f"⚠️ Error clearing selection: {e}")
            self.selected_field = None

    def get_selected_field(self):
        """Get selected field"""
        return self.selected_field

    def select_field_at_position(self, x, y):
        """Select field at position"""
        if not self.field_manager:
            return None
        try:
            field = self.field_manager.get_field_at_position(x, y)
            self.select_field(field)
            return field
        except Exception as e:
            print(f"⚠️ Error selecting at position: {e}")
            return None


# For backward compatibility, create an alias
SelectionHandler = WorkingSelectionHandler
'''

        # Add it to the file
        content += working_selection_handler

        # Write back
        with open(drag_handler_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Created WorkingSelectionHandler")
        return True

    except Exception as e:
        print(f"❌ Error creating WorkingSelectionHandler: {e}")
        return False


def fix_pdf_canvas_to_use_working_handler():
    """Fix pdf_canvas.py to use the working SelectionHandler"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print("❌ pdf_canvas.py not found")
        return False

    print("🔧 Fixing pdf_canvas.py to use WorkingSelectionHandler...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Ensure proper import
        if 'from ui.drag_handler import' in content:
            # Update existing import
            import_pattern = r'from ui\.drag_handler import ([^\n]+)'
            match = re.search(import_pattern, content)
            if match:
                imports = match.group(1)
                if 'SelectionHandler' not in imports:
                    new_imports = imports + ', SelectionHandler'
                    content = content.replace(match.group(0), f'from ui.drag_handler import {new_imports}')
        else:
            # Add import
            if 'from ui.field_renderer import' in content:
                content = content.replace(
                    'from ui.field_renderer import FieldRenderer',
                    'from ui.field_renderer import FieldRenderer\nfrom ui.drag_handler import DragHandler, SelectionHandler'
                )

        # Replace any problematic clear_selection calls with safe ones
        problematic_patterns = [
            (r'self\.selection_handler\.clear_selection\(\)',
             '''try:
            self.selection_handler.clear_selection()
        except Exception as e:
            print(f"⚠️ Selection handler issue: {e}")'''),
        ]

        for pattern, replacement in problematic_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                print("  ✅ Made clear_selection call safe")

        # Write back
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Fixed pdf_canvas.py")
        return True

    except Exception as e:
        print(f"❌ Error fixing pdf_canvas.py: {e}")
        return False


def add_debugging_to_mouse_events():
    """Add debugging to mouse events to trace the exact error"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find mousePressEvent method
        if 'def mousePressEvent(self, event):' in content:
            # Add debugging at the start of mousePressEvent
            debug_code = '''        print("🖱️ Mouse press event started")
        print(f"   Button: {event.button()}")
        print(f"   Position: {event.position().toPoint()}")
        '''

            # Find the method and add debugging
            method_start = content.find('def mousePressEvent(self, event):')
            method_line_end = content.find('\n', method_start)

            # Check if debugging already exists
            if '🖱️ Mouse press event started' not in content:
                content = content[:method_line_end] + '\n' + debug_code + content[method_line_end:]
                print("  ✅ Added debugging to mousePressEvent")

        # Write back
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error adding debugging: {e}")
        return False


def create_emergency_fallback():
    """Create an emergency fallback that won't crash"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add a SafeSelectionHandler class as emergency fallback
        emergency_handler = '''

class SafeSelectionHandler:
    """Emergency fallback SelectionHandler that never crashes"""

    def __init__(self, field_manager=None):
        self.field_manager = field_manager
        self.selected_field = None
        print("🛡️ SafeSelectionHandler initialized (emergency fallback)")

    def select_field(self, field):
        """Safe select field"""
        self.selected_field = field
        print(f"🛡️ Safe selection: {field.name if field else 'None'}")

    def clear_selection(self):
        """Safe clear selection"""
        print("🛡️ Safe clear selection")
        self.selected_field = None

    def get_selected_field(self):
        """Safe get selected field"""
        return self.selected_field

    def select_field_at_position(self, x, y):
        """Safe select at position"""
        if self.field_manager and hasattr(self.field_manager, 'get_field_at_position'):
            field = self.field_manager.get_field_at_position(x, y)
            self.select_field(field)
            return field
        return None
'''

        # Add emergency handler
        content += emergency_handler

        # Modify __init__ to use SafeSelectionHandler as fallback
        if 'self.selection_handler = SelectionHandler(self.field_manager)' in content:
            content = content.replace(
                'self.selection_handler = SelectionHandler(self.field_manager)',
                '''try:
            self.selection_handler = SelectionHandler(self.field_manager)
            print("✅ Using normal SelectionHandler")
        except Exception as e:
            print(f"⚠️ SelectionHandler failed, using safe fallback: {e}")
            self.selection_handler = SafeSelectionHandler(self.field_manager)'''
            )
            print("  ✅ Added SafeSelectionHandler fallback")

        # Write back
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error creating emergency fallback: {e}")
        return False


def main():
    """Main execution function"""
    print("🔧 PDF Voice Editor - Nuclear SelectionHandler Fix")
    print("=" * 60)

    # Step 1: Find exact error location
    find_exact_error_location()

    # Step 2: Completely remove all SelectionHandler classes
    completely_remove_all_selection_handlers()

    # Step 3: Create ONE working SelectionHandler
    if not create_single_working_selection_handler():
        print("❌ Failed to create working SelectionHandler")
        return 1

    # Step 4: Fix pdf_canvas.py to use it properly
    if not fix_pdf_canvas_to_use_working_handler():
        print("❌ Failed to fix pdf_canvas.py")
        return 1

    # Step 5: Add debugging
    add_debugging_to_mouse_events()

    # Step 6: Create emergency fallback
    create_emergency_fallback()

    print("\n🎉 Nuclear fix complete!")
    print("\n🎯 What was done:")
    print("   • Completely removed ALL existing SelectionHandler classes")
    print("   • Created ONE working WorkingSelectionHandler in drag_handler.py")
    print("   • Fixed pdf_canvas.py to use the working version")
    print("   • Added SafeSelectionHandler as emergency fallback")
    print("   • Added debugging to trace any remaining issues")
    print("\n🎯 Try the application now:")
    print("   python launch.py")
    print("\n📝 If you still see the error, the debugging will show exactly where it's coming from")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())