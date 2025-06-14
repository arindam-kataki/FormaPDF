#!/usr/bin/env python3
"""
Fix Missing toolbar.show() Call
Adds the missing toolbar.show() call to make toolbar visible
"""

import os
from pathlib import Path


def add_toolbar_show():
    """Add toolbar.show() call to the create_toolbar method"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Adding toolbar.show() call...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if toolbar.show() already exists
        if 'toolbar.show()' in content:
            print("✅ toolbar.show() already exists")
            return True

        # Find the create_toolbar method
        toolbar_method_start = content.find('def create_toolbar(self):')
        if toolbar_method_start == -1:
            print("❌ create_toolbar method not found")
            return False

        # Find the end of the create_toolbar method
        next_method = content.find('\n    def ', toolbar_method_start + 1)
        if next_method == -1:
            next_method = content.find('\n\n    def ', toolbar_method_start + 1)
        if next_method == -1:
            next_method = content.find('\ndef ', toolbar_method_start + 1)
        if next_method == -1:
            next_method = len(content)

        # Get the method content
        method_content = content[toolbar_method_start:next_method]

        # Find the last line that's not empty or a comment
        lines = method_content.split('\n')
        insert_line_index = len(lines) - 1

        # Find the last substantive line (not empty, not just whitespace)
        while insert_line_index > 0:
            line = lines[insert_line_index].strip()
            if line and not line.startswith('#'):
                break
            insert_line_index -= 1

        # Add toolbar.show() after the last action or configuration
        show_call = '\n        \n        # Make sure toolbar is visible\n        toolbar.show()\n        print("🔧 Toolbar created and should be visible")'

        # Insert the show call before the method ends
        lines.insert(insert_line_index + 1, '        ')
        lines.insert(insert_line_index + 2, '        # Make sure toolbar is visible')
        lines.insert(insert_line_index + 3, '        toolbar.show()')
        lines.insert(insert_line_index + 4, '        print("🔧 Toolbar created and should be visible")')

        # Reconstruct the method
        new_method_content = '\n'.join(lines)

        # Replace the old method with the new one
        content = content[:toolbar_method_start] + new_method_content + content[next_method:]

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Added toolbar.show() call to create_toolbar method")
        return True

    except Exception as e:
        print(f"❌ Error adding toolbar.show(): {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_fix():
    """Verify that the fix was applied correctly"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'toolbar.show()' in content:
            print("✅ toolbar.show() call found")

            # Check if it's in the right place (within create_toolbar method)
            toolbar_method_start = content.find('def create_toolbar(self):')
            if toolbar_method_start != -1:
                next_method = content.find('\n    def ', toolbar_method_start + 1)
                if next_method == -1:
                    next_method = len(content)

                method_content = content[toolbar_method_start:next_method]
                if 'toolbar.show()' in method_content:
                    print("✅ toolbar.show() is correctly placed in create_toolbar method")
                    return True
                else:
                    print("❌ toolbar.show() found but not in create_toolbar method")
                    return False
            else:
                print("❌ create_toolbar method not found")
                return False
        else:
            print("❌ toolbar.show() call not found")
            return False

    except Exception as e:
        print(f"❌ Error verifying fix: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Fix Missing toolbar.show()")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Add toolbar.show() call
    if not add_toolbar_show():
        print("❌ Failed to add toolbar.show() call")
        return 1

    # Verify the fix
    if verify_fix():
        print("\n🎉 Toolbar show() call added successfully!")
        print("\n🎯 Now test the application:")
        print("1. Run: python launch.py")
        print("2. The toolbar should now be visible at the top of the window")
        print("3. You should see: 📁 💾 ⬅️ ➡️ 🔍- 🔍+ 📏 📐 ℹ️")
        return 0
    else:
        print("\n❌ Fix verification failed")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())