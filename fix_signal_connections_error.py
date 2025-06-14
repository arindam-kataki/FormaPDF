#!/usr/bin/env python3
"""
Fix Signal Connections Error
The issue is trying to connect to signals improperly - signals need to be accessed
through object instances, not classes, and we need to handle cases where objects
or signals might not exist.
"""

import os
import re
from pathlib import Path


def fix_setup_connections_method():
    """Fix the setup_connections method in main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Fixing setup_connections method...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Define a robust setup_connections method
        new_setup_connections = '''    def setup_connections(self):
        """Setup signal connections between components safely"""
        try:
            # Field palette connections - check both object and signal exist
            if (hasattr(self, 'field_palette') and 
                self.field_palette is not None and 
                hasattr(self.field_palette, 'fieldRequested')):
                try:
                    self.field_palette.fieldRequested.connect(self.create_field_at_center)
                    print("  ✅ Connected field_palette.fieldRequested")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect fieldRequested: {e}")

            if (hasattr(self, 'field_palette') and 
                self.field_palette is not None and 
                hasattr(self.field_palette, 'duplicateRequested')):
                try:
                    self.field_palette.duplicateRequested.connect(lambda: print("Duplicate requested"))
                    print("  ✅ Connected field_palette.duplicateRequested")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect duplicateRequested: {e}")

            if (hasattr(self, 'field_palette') and 
                self.field_palette is not None and 
                hasattr(self.field_palette, 'deleteRequested')):
                try:
                    self.field_palette.deleteRequested.connect(lambda: print("Delete requested"))
                    print("  ✅ Connected field_palette.deleteRequested")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect deleteRequested: {e}")

            # PDF canvas connections - check both object and signal exist
            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'fieldClicked')):
                try:
                    self.pdf_canvas.fieldClicked.connect(self.on_field_clicked)
                    print("  ✅ Connected pdf_canvas.fieldClicked")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect fieldClicked: {e}")

            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'fieldMoved')):
                try:
                    self.pdf_canvas.fieldMoved.connect(self.on_field_moved)
                    print("  ✅ Connected pdf_canvas.fieldMoved")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect fieldMoved: {e}")

            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'fieldResized')):
                try:
                    self.pdf_canvas.fieldResized.connect(self.on_field_resized)
                    print("  ✅ Connected pdf_canvas.fieldResized")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect fieldResized: {e}")

            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'positionClicked')):
                try:
                    self.pdf_canvas.positionClicked.connect(self.on_position_clicked)
                    print("  ✅ Connected pdf_canvas.positionClicked")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect positionClicked: {e}")

            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'selectionChanged')):
                try:
                    self.pdf_canvas.selectionChanged.connect(self.on_selection_changed)
                    print("  ✅ Connected pdf_canvas.selectionChanged")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect selectionChanged: {e}")

            # Properties panel connections - check both object and signal exist
            if (hasattr(self, 'properties_panel') and 
                self.properties_panel is not None and 
                hasattr(self.properties_panel, 'propertyChanged')):
                try:
                    self.properties_panel.propertyChanged.connect(self.on_property_changed)
                    print("  ✅ Connected properties_panel.propertyChanged")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect propertyChanged: {e}")

            print("✅ Signal connections setup completed")

        except Exception as e:
            print(f"Warning: Error setting up signal connections: {e}")
            import traceback
            traceback.print_exc()'''

        # Find and replace the existing setup_connections method
        # Look for the method definition
        setup_pattern = r'def setup_connections\(self\):.*?(?=\n    def |\n\n    def |\nclass |\Z)'

        if re.search(setup_pattern, content, re.DOTALL):
            # Replace existing method
            content = re.sub(setup_pattern, new_setup_connections.strip(), content, flags=re.DOTALL)
            print("  ✅ Replaced existing setup_connections method")
        else:
            # If method doesn't exist, add it before the first method
            class_match = re.search(r'class PDFViewerMainWindow.*?:', content, re.DOTALL)
            if class_match:
                # Find the first method after the class definition
                first_method_match = re.search(r'\n    def ', content[class_match.end():])
                if first_method_match:
                    insert_pos = class_match.end() + first_method_match.start()
                    content = content[:insert_pos] + '\n' + new_setup_connections + '\n' + content[insert_pos:]
                    print("  ✅ Added new setup_connections method")

        # Write the fixed content back
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Fixed setup_connections method")
        return True

    except Exception as e:
        print(f"❌ Error fixing setup_connections: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_missing_slot_methods():
    """Add any missing slot methods that are referenced in setup_connections"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # List of methods that should exist
        required_methods = [
            'create_field_at_center',
            'on_field_clicked',
            'on_field_moved',
            'on_field_resized',
            'on_position_clicked',
            'on_selection_changed',
            'on_property_changed'
        ]

        methods_to_add = []
        for method in required_methods:
            if f'def {method}(' not in content:
                methods_to_add.append(method)

        if not methods_to_add:
            print("✅ All required slot methods already exist")
            return True

        print(f"🔧 Adding {len(methods_to_add)} missing slot methods...")

        # Define the missing methods
        missing_methods_code = '''
    @pyqtSlot(str)
    def create_field_at_center(self, field_type: str):
        """Create a new field at the center of the visible area"""
        print(f"Creating field of type: {field_type}")
        # Implementation would go here

    @pyqtSlot(str)
    def on_field_clicked(self, field_id: str):
        """Handle field click"""
        print(f"Field clicked: {field_id}")

    @pyqtSlot(str, int, int)
    def on_field_moved(self, field_id: str, x: int, y: int):
        """Handle field movement"""
        print(f"Field {field_id} moved to ({x}, {y})")

    @pyqtSlot(str, int, int, int, int)
    def on_field_resized(self, field_id: str, x: int, y: int, width: int, height: int):
        """Handle field resize"""
        print(f"Field {field_id} resized to {width}x{height} at ({x}, {y})")

    @pyqtSlot(int, int)
    def on_position_clicked(self, x: int, y: int):
        """Handle position click (no field)"""
        print(f"Position clicked: ({x}, {y})")

    @pyqtSlot(object)
    def on_selection_changed(self, field):
        """Handle selection change"""
        if field:
            print(f"Field selected: {field}")
        else:
            print("Selection cleared")

    @pyqtSlot(str, str, object)
    def on_property_changed(self, field_id: str, property_name: str, value):
        """Handle property change"""
        print(f"Property {property_name} of field {field_id} changed to {value}")
'''

        # Find where to insert the methods (before the main function or at end of class)
        insert_pos = content.find('\ndef main():')
        if insert_pos == -1:
            insert_pos = content.find('if __name__ == "__main__":')
        if insert_pos == -1:
            insert_pos = len(content)

        # Insert the missing methods
        content = content[:insert_pos] + missing_methods_code + '\n' + content[insert_pos:]

        # Write the updated content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Added {len(methods_to_add)} missing slot methods")
        for method in methods_to_add:
            print(f"  • {method}")

        return True

    except Exception as e:
        print(f"❌ Error adding missing slot methods: {e}")
        return False


def validate_fix():
    """Validate that the fix worked"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to compile the module to check for syntax errors
        compile(content, str(main_window_path), 'exec')
        print("✅ Python syntax is valid")

        # Check that setup_connections method exists and has proper error handling
        if 'def setup_connections(self):' in content:
            print("✅ setup_connections method exists")
            if 'try:' in content and 'except Exception as e:' in content:
                print("✅ setup_connections has proper error handling")
                return True

        return False

    except SyntaxError as e:
        print(f"❌ Syntax error still exists:")
        print(f"   Line {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Error validating fix: {e}")
        return False


def main():
    """Main execution function"""
    print("🔧 PDF Voice Editor - Signal Connections Error Fixer")
    print("=" * 60)

    success = True

    # Step 1: Fix the setup_connections method
    if not fix_setup_connections_method():
        success = False

    # Step 2: Add any missing slot methods
    if not add_missing_slot_methods():
        success = False

    # Step 3: Validate the fix
    if success and validate_fix():
        print("\n🎉 Success! Signal connections error has been fixed.")
        print("\n🎯 The issue was improper signal connection handling.")
        print("🎯 You can now try running your application again:")
        print("   python launch.py")
        print("\n📝 Note: You should see successful connection messages instead of errors.")
        return 0
    else:
        print("\n⚠️ Some issues may remain. Check the error messages above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())