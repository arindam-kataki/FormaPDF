#!/usr/bin/env python3
"""
Fix All Import Errors - Comprehensive Fix
This script fixes all the import issues we've encountered so far
"""

import os
import re
from pathlib import Path


def fix_pdf_canvas_imports():
    """Fix imports in pdf_canvas.py"""
    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Fixing pdf_canvas.py imports...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix the problematic imports
        imports_to_fix = [
            ('from field_renderer import FieldRenderer', 'from ui.field_renderer import FieldRenderer'),
            ('from drag_handler import DragHandler, SelectionHandler',
             'from ui.drag_handler import DragHandler, SelectionHandler'),
        ]

        for old_import, new_import in imports_to_fix:
            if old_import in content:
                content = content.replace(old_import, new_import)
                print(f"  ✅ Fixed: {old_import}")

        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing pdf_canvas.py: {e}")
        return False


def fix_properties_panel_typeerror():
    """Fix the TypeError in properties_panel.py"""
    properties_panel_path = Path("src/ui/properties_panel.py")

    if not properties_panel_path.exists():
        print(f"❌ File not found: {properties_panel_path}")
        return False

    print("🔧 Fixing properties_panel.py TypeError...")

    try:
        with open(properties_panel_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix the MultilineTextPropertyWidget __init__ method
        old_init = 'widget.setPlainText(initial_value)'
        new_init = '''# Handle both string and list inputs
        if isinstance(initial_value, list):
            text_value = '\\n'.join(str(v) for v in initial_value)
        else:
            text_value = str(initial_value) if initial_value else ""
        widget.setPlainText(text_value)'''

        if old_init in content:
            content = content.replace(old_init, new_init)
            print("  ✅ Fixed MultilineTextPropertyWidget.__init__")

        # Fix the set_value method
        old_set_value = "self.widget.setPlainText('\\n'.join(value))"
        new_set_value = "self.widget.setPlainText('\\n'.join(str(v) for v in value))"

        if old_set_value in content:
            content = content.replace(old_set_value, new_set_value)
            print("  ✅ Fixed set_value method")

        with open(properties_panel_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing properties_panel.py: {e}")
        return False


def fix_drag_handler_typing():
    """Fix typing issues in drag_handler.py"""
    drag_handler_path = Path("src/ui/drag_handler.py")

    if not drag_handler_path.exists():
        print(f"❌ File not found: {drag_handler_path}")
        return False

    print("🔧 Fixing drag_handler.py typing...")

    try:
        with open(drag_handler_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simplify the typing imports by removing TYPE_CHECKING complexity
        if 'TYPE_CHECKING' in content:
            # Replace complex typing with simple version
            old_imports = '''from typing import Optional, Tuple, TYPE_CHECKING
from enum import Enum
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject

from models.field_model import FormField, FieldManager
from utils.geometry_utils import (
    ResizeHandles, ResizeCalculator, BoundaryConstraints, GridUtils
)

# Type checking imports for better IDE support
if TYPE_CHECKING:
    from PyQt6.QtCore import pyqtBoundSignal'''

            new_imports = '''from typing import Optional, Tuple
from enum import Enum
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject

from models.field_model import FormField, FieldManager
from utils.geometry_utils import (
    ResizeHandles, ResizeCalculator, BoundaryConstraints, GridUtils
)'''

            content = content.replace(old_imports, new_imports)

            # Simplify the signal type hints
            content = content.replace(
                "fieldMoved: 'pyqtBoundSignal' = pyqtSignal(str, int, int)",
                "fieldMoved = pyqtSignal(str, int, int)"
            )
            content = content.replace(
                "fieldResized: 'pyqtBoundSignal' = pyqtSignal(str, int, int, int, int)",
                "fieldResized = pyqtSignal(str, int, int, int, int)"
            )
            content = content.replace(
                "cursorChanged: 'pyqtBoundSignal' = pyqtSignal(Qt.CursorShape)",
                "cursorChanged = pyqtSignal(Qt.CursorShape)"
            )
            content = content.replace(
                "selectionChanged: 'pyqtBoundSignal' = pyqtSignal(object)",
                "selectionChanged = pyqtSignal(object)"
            )

            print("  ✅ Simplified typing in drag_handler.py")

        with open(drag_handler_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing drag_handler.py: {e}")
        return False


def fix_main_window_imports():
    """Fix any import issues in main_window.py"""
    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Checking main_window.py imports...")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove the comment about fixing imports
        content = content.replace("# Fix these imports to use absolute imports (remove leading dots)", "")

        # Ensure proper imports (they should already be correct)
        required_imports = [
            "from ui.pdf_canvas import PDFCanvas",
            "from ui.field_palette import EnhancedFieldPalette",
            "from ui.properties_panel import PropertiesPanel",
            "from models.field_model import FormField",
            "from utils.icon_utils import create_app_icon, create_toolbar_icons"
        ]

        for required_import in required_imports:
            if required_import not in content:
                print(f"  ⚠️ Missing import: {required_import}")

        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("  ✅ main_window.py imports verified")
        return True

    except Exception as e:
        print(f"❌ Error checking main_window.py: {e}")
        return False


def main():
    """Main function to fix all import errors"""
    print("🔧 PDF Voice Editor - Comprehensive Import Error Fixer")
    print("=" * 65)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        print("   Make sure you're running this from the project root directory.")
        return 1

    print("Fixing all known import and type errors...\n")

    # Apply all fixes
    fixes = [
        ("PDF Canvas imports", fix_pdf_canvas_imports),
        ("Properties Panel TypeError", fix_properties_panel_typeerror),
        ("Drag Handler typing", fix_drag_handler_typing),
        ("Main Window imports", fix_main_window_imports),
    ]

    success_count = 0
    for fix_name, fix_function in fixes:
        print(f"📦 {fix_name}...")
        if fix_function():
            success_count += 1
        print()

    print("=" * 65)
    if success_count == len(fixes):
        print("🎉 All fixes applied successfully!")
        print("\n🎯 Next steps:")
        print("1. Run: python fix_main_window_safe_calls.py")
        print("2. Run: python fix_field_palette_missing_methods.py")
        print("3. Run: python launch.py")
        return 0
    else:
        print(f"⚠️ {success_count}/{len(fixes)} fixes applied successfully.")
        print("Some issues may remain. Check the error messages above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())