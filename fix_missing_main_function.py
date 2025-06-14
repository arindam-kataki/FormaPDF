#!/usr/bin/env python3
"""
Fix Missing Main Function in main_window.py
Adds the missing main() function that launch.py is trying to import
"""

import os
from pathlib import Path


def add_main_function():
    """Add the missing main function to main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Adding missing main function to main_window.py...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if main function already exists
        if 'def main():' in content:
            print("  ✅ main() function already exists")
            return True

        # Define the main function
        main_function = '''

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("PDF Voice Editor - Enhanced")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("PDF Tools")

    # Set application icon if available
    try:
        app.setWindowIcon(create_app_icon(32))
    except:
        pass  # Icon creation might fail, continue without it

    # Create and show main window
    window = PDFViewerMainWindow()
    window.show()

    # Add some sample fields for demonstration if no PDF is loaded
    try:
        if not window.current_pdf_path:
            canvas = window.pdf_canvas
            if hasattr(canvas, 'add_field'):
                canvas.add_field('text', 150, 100)
                canvas.add_field('checkbox', 150, 150)
                canvas.add_field('dropdown', 150, 200)
                canvas.add_field('signature', 150, 250)
            window.update_document_info()
    except:
        pass  # Sample fields creation might fail, continue without them

    print("🎉 Enhanced PDF Voice Editor started!")
    print("Features available:")
    print("  • Drag fields to move them around")
    print("  • Drag resize handles to change size")
    print("  • Use arrow keys for precise movement")
    print("  • Ctrl+D to duplicate selected field")
    print("  • Delete key to remove selected field")
    print("  • Grid snapping for alignment")
    print("  • Form data save/load")

    # Run the application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
'''

        # Add the main function at the end of the file
        content = content.rstrip() + main_function + '\n'

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Added main() function to main_window.py")
        return True

    except Exception as e:
        print(f"❌ Error adding main function: {e}")
        import traceback
        traceback.print_exc()
        return False


def fix_imports_in_main_window():
    """Fix any missing imports in main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Checking and fixing imports in main_window.py...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Required imports that might be missing
        required_imports = [
            "import sys",
            "import json",
            "from pathlib import Path",
            "from typing import Optional",
            "from PyQt6.QtWidgets import QApplication",
        ]

        # Check which imports are missing
        missing_imports = []
        for required_import in required_imports:
            if required_import not in content:
                missing_imports.append(required_import)

        if missing_imports:
            # Find the import section (after the docstring, before the first class)
            import_section_end = content.find('class PDFViewerMainWindow')
            if import_section_end == -1:
                import_section_end = content.find('from ui.pdf_canvas')

            if import_section_end != -1:
                # Insert missing imports before the class definition
                imports_to_add = '\\n'.join(missing_imports) + '\\n\\n'
                content = content[:import_section_end] + imports_to_add + content[import_section_end:]

                print(f"  ✅ Added {len(missing_imports)} missing imports")
                for imp in missing_imports:
                    print(f"    • {imp}")
            else:
                # Add imports at the beginning after docstring
                docstring_end = content.find('"""', content.find('"""') + 3)
                if docstring_end != -1:
                    docstring_end += 3
                    imports_to_add = '\\n\\n' + '\\n'.join(missing_imports) + '\\n'
                    content = content[:docstring_end] + imports_to_add + content[docstring_end:]
                    print(f"  ✅ Added {len(missing_imports)} missing imports at top")
        else:
            print("  ✅ All required imports are present")

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing imports: {e}")
        return False


def validate_main_window_structure():
    """Validate that main_window.py has the correct structure"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔍 Validating main_window.py structure...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for required components
        checks = [
            ("PDFViewerMainWindow class", "class PDFViewerMainWindow"),
            ("main function", "def main():"),
            ("QApplication import", "QApplication"),
            ("sys import", "import sys"),
        ]

        all_good = True
        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"  ✅ {check_name} found")
            else:
                print(f"  ❌ {check_name} missing")
                all_good = False

        # Try to compile the code
        try:
            compile(content, main_window_path, 'exec')
            print("  ✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"  ❌ Syntax error at line {e.lineno}: {e.msg}")
            all_good = False

        return all_good

    except Exception as e:
        print(f"❌ Error validating structure: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Missing Main Function Fixer")
    print("=" * 55)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Fix imports first
    if not fix_imports_in_main_window():
        print("❌ Failed to fix imports")
        return 1

    # Add missing main function
    if not add_main_function():
        print("❌ Failed to add main function")
        return 1

    # Validate the structure
    if validate_main_window_structure():
        print("\\n🎉 main_window.py is now complete and valid!")
        print("\\n🎯 Next steps:")
        print("1. Try running: python launch.py")
        print("2. If you get field_palette method errors:")
        print("   Run: python fix_field_palette_missing_methods.py")
    else:
        print("\\n⚠️ Some issues remain in main_window.py")
        print("Check the validation results above.")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())