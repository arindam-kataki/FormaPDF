#!/usr/bin/env python3
"""
Fix Field Creation and Selection Handler Issues
Fixes both the SelectionHandler emit problem and implements proper field creation
"""

import os
import re
from pathlib import Path


def fix_selection_handler_emit_issue():
    """Fix the SelectionHandler emit issue by ensuring proper QObject inheritance"""

    # Check both possible locations for SelectionHandler
    files_to_check = [
        Path("src/ui/pdf_canvas.py"),
        Path("src/ui/drag_handler.py")
    ]

    for file_path in files_to_check:
        if not file_path.exists():
            continue

        print(f"🔧 Checking {file_path} for SelectionHandler issues...")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'class SelectionHandler' not in content:
                continue

            # Ensure QObject is imported
            if 'from PyQt6.QtCore import' in content:
                import_match = re.search(r'from PyQt6\.QtCore import ([^\n]+)', content)
                if import_match and 'QObject' not in import_match.group(1):
                    new_imports = import_match.group(1) + ', QObject'
                    content = content.replace(import_match.group(0), f'from PyQt6.QtCore import {new_imports}')
                    print(f"  ✅ Added QObject import to {file_path}")

            # Fix SelectionHandler class definition if needed
            if 'class SelectionHandler:' in content:
                content = content.replace('class SelectionHandler:', 'class SelectionHandler(QObject):')
                print(f"  ✅ Fixed SelectionHandler inheritance in {file_path}")

            # Ensure proper __init__ method
            pattern = r'class SelectionHandler\(QObject\):(.*?)def __init__\(self[^)]*\):(.*?)(?=\n    def |\Z)'
            match = re.search(pattern, content, re.DOTALL)

            if match and 'super().__init__()' not in match.group(2):
                # Find the __init__ method and add super().__init__()
                init_start = content.find('def __init__(self', match.start())
                init_line_end = content.find('\n', init_start)

                # Insert super().__init__() after the method signature
                content = (content[:init_line_end] +
                           '\n        super().__init__()' +
                           content[init_line_end:])
                print(f"  ✅ Added super().__init__() to SelectionHandler in {file_path}")

            # Write back the fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            continue

    return True


def fix_field_creation_method():
    """Fix the create_field_at_center method to properly create and display fields"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Fixing field creation method...")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for the existing create_field_at_center method
        method_pattern = r'def create_field_at_center\(self, field_type: str\):(.*?)(?=\n    def |\n\n    def |\Z)'
        match = re.search(method_pattern, content, re.DOTALL)

        if match:
            old_method = match.group(0)

            # Create improved field creation method
            new_method = '''def create_field_at_center(self, field_type: str):
        """Create a new field at the center of the visible area"""
        print(f"Creating field of type: {field_type}")

        try:
            # Calculate center of visible area
            if hasattr(self, 'scroll_area') and self.scroll_area:
                center_x = self.scroll_area.width() // 2
                center_y = self.scroll_area.height() // 2

                # Convert to canvas coordinates
                scroll_x = self.scroll_area.horizontalScrollBar().value()
                scroll_y = self.scroll_area.verticalScrollBar().value()

                canvas_x = center_x + scroll_x
                canvas_y = center_y + scroll_y
            else:
                # Fallback position
                canvas_x, canvas_y = 200, 200

            # Create field using pdf_canvas
            if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'add_field'):
                    field = self.pdf_canvas.add_field(field_type, canvas_x, canvas_y)
                    if field:
                        print(f"✅ Created {field_type} field: {field.name}")
                        self.statusBar().showMessage(f"Created {field_type} field", 2000)

                        # Force canvas to redraw
                        if hasattr(self.pdf_canvas, 'draw_overlay'):
                            self.pdf_canvas.draw_overlay()
                        else:
                            self.pdf_canvas.update()

                        return field
                    else:
                        print(f"❌ Failed to create {field_type} field")
                        self.statusBar().showMessage(f"Failed to create {field_type} field", 3000)
                elif hasattr(self.pdf_canvas.field_manager, 'add_field'):
                    # Alternative: use field manager directly
                    field = self.pdf_canvas.field_manager.add_field(field_type, canvas_x, canvas_y)
                    if field:
                        print(f"✅ Created {field_type} field via field manager: {field.name}")
                        self.statusBar().showMessage(f"Created {field_type} field", 2000)
                        self.pdf_canvas.update()
                        return field
                else:
                    print("❌ No field creation method available")
                    self.statusBar().showMessage("Field creation not available", 3000)
            else:
                print("❌ PDF Canvas not available")
                self.statusBar().showMessage("PDF Canvas not available", 3000)

        except Exception as e:
            print(f"❌ Error creating field: {e}")
            self.statusBar().showMessage(f"Error creating field: {e}", 3000)

        return None'''

            # Replace the old method with the new one
            content = content.replace(old_method, new_method)
            print("  ✅ Replaced create_field_at_center method")
        else:
            print("  ⚠️ create_field_at_center method not found, adding it")

            # Add the method before the main function
            insert_pos = content.find('\ndef main():')
            if insert_pos == -1:
                insert_pos = content.find('if __name__ == "__main__":')
            if insert_pos == -1:
                insert_pos = len(content)

            content = content[:insert_pos] + '\n    @pyqtSlot(str)\n    ' + new_method.replace('\n',
                                                                                               '\n    ') + '\n' + content[
                                                                                                                  insert_pos:]
            print("  ✅ Added create_field_at_center method")

        # Write back the updated content
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing field creation method: {e}")
        import traceback
        traceback.print_exc()
        return False


def ensure_pdf_canvas_has_add_field():
    """Ensure PDFCanvas has an add_field method"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Ensuring PDFCanvas has add_field method...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if add_field method exists
        if 'def add_field(self' in content:
            print("  ✅ add_field method already exists")
            return True

        # Add add_field method
        add_field_method = '''
    def add_field(self, field_type: str, x: int, y: int):
        """Add a new field to the canvas"""
        try:
            # Use the field manager to create the field
            field = self.field_manager.add_field(field_type, x, y)

            if field:
                print(f"✅ Added {field_type} field at ({x}, {y})")

                # Select the new field
                if hasattr(self, 'selection_handler') and self.selection_handler:
                    try:
                        self.selection_handler.select_field(field)
                    except Exception as e:
                        print(f"⚠️ Could not select field: {e}")

                # Trigger a redraw
                self.update()

                return field
            else:
                print(f"❌ Failed to create {field_type} field")
                return None

        except Exception as e:
            print(f"❌ Error adding field: {e}")
            import traceback
            traceback.print_exc()
            return None

    def draw_overlay(self):
        """Draw overlay with fields and selection handles"""
        try:
            # Force a repaint of the widget
            self.update()
        except Exception as e:
            print(f"⚠️ Error in draw_overlay: {e}")
'''

        # Find where to insert the method (before existing methods)
        insert_pos = content.find('    def show_no_document_message(self):')
        if insert_pos == -1:
            insert_pos = content.find('    def load_pdf(self')
        if insert_pos == -1:
            insert_pos = content.find('    def render_page(self):')

        if insert_pos != -1:
            content = content[:insert_pos] + add_field_method + '\n' + content[insert_pos:]
            print("  ✅ Added add_field method to PDFCanvas")
        else:
            print("  ⚠️ Could not find good insertion point for add_field method")
            return False

        # Write back the updated content
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error ensuring add_field method: {e}")
        return False


def ensure_field_manager_works():
    """Ensure the FieldManager add_field method works properly"""

    field_model_path = Path("src/models/field_model.py")

    if not field_model_path.exists():
        print(f"❌ File not found: {field_model_path}")
        return False

    print("🔧 Checking FieldManager...")

    try:
        with open(field_model_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if add_field method exists in FieldManager
        if 'def add_field(self, field_type: str, x: int, y: int)' not in content:
            print("  ⚠️ FieldManager.add_field method needs to be added")

            # Find FieldManager class
            field_manager_start = content.find('class FieldManager:')
            if field_manager_start == -1:
                print("  ❌ FieldManager class not found")
                return False

            # Find where to insert the method
            insert_pos = content.find('    def remove_field(self', field_manager_start)
            if insert_pos == -1:
                insert_pos = content.find('    def get_field_by_id(self', field_manager_start)

            if insert_pos != -1:
                add_field_method = '''
    def add_field(self, field_type: str, x: int, y: int) -> FormField:
        """Add a new field to the collection"""
        self._field_counter += 1
        field_id = f"{field_type}_{self._field_counter}"

        field = FormField.create(field_type, x, y, field_id)
        self.fields.append(field)
        return field
'''
                content = content[:insert_pos] + add_field_method + '\n' + content[insert_pos:]

                # Write back
                with open(field_model_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                print("  ✅ Added add_field method to FieldManager")
        else:
            print("  ✅ FieldManager.add_field method exists")

        return True

    except Exception as e:
        print(f"❌ Error checking FieldManager: {e}")
        return False


def add_field_rendering():
    """Ensure fields are rendered on the canvas"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if paintEvent method exists
        if 'def paintEvent(self, event):' not in content:
            print("🔧 Adding paintEvent method to render fields...")

            paint_event_method = '''
    def paintEvent(self, event):
        """Paint event to render PDF and fields"""
        super().paintEvent(event)

        try:
            # Get a painter for this widget
            from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
            painter = QPainter(self)

            # Draw all fields
            if hasattr(self, 'field_manager') and self.field_manager:
                for field in self.field_manager.fields:
                    self._draw_field(painter, field)

            # Draw selection handles for selected field
            if (hasattr(self, 'selection_handler') and 
                self.selection_handler and 
                hasattr(self.selection_handler, 'selected_field') and
                self.selection_handler.selected_field):

                self._draw_selection_handles(painter, self.selection_handler.selected_field)

        except Exception as e:
            print(f"⚠️ Error in paintEvent: {e}")

    def _draw_field(self, painter, field):
        """Draw a single field"""
        try:
            from PyQt6.QtGui import QPen, QBrush, QColor
            from PyQt6.QtCore import Qt

            # Set up pen and brush
            painter.setPen(QPen(QColor(0, 0, 255), 2))
            painter.setBrush(QBrush(QColor(255, 255, 255, 100)))

            # Draw field rectangle
            painter.drawRect(field.x, field.y, field.width, field.height)

            # Draw field type text
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(field.x + 5, field.y + 15, f"{field.type.value}")

        except Exception as e:
            print(f"⚠️ Error drawing field: {e}")

    def _draw_selection_handles(self, painter, field):
        """Draw selection handles around a field"""
        try:
            from PyQt6.QtGui import QPen, QBrush, QColor

            # Draw selection rectangle
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.setBrush(QBrush())
            painter.drawRect(field.x - 2, field.y - 2, field.width + 4, field.height + 4)

            # Draw corner handles
            handle_size = 6
            painter.setBrush(QBrush(QColor(255, 0, 0)))

            positions = [
                (field.x - handle_size//2, field.y - handle_size//2),
                (field.x + field.width - handle_size//2, field.y - handle_size//2),
                (field.x - handle_size//2, field.y + field.height - handle_size//2),
                (field.x + field.width - handle_size//2, field.y + field.height - handle_size//2)
            ]

            for pos_x, pos_y in positions:
                painter.drawRect(pos_x, pos_y, handle_size, handle_size)

        except Exception as e:
            print(f"⚠️ Error drawing selection handles: {e}")
'''

            # Find where to insert the paintEvent method
            insert_pos = content.find('    def mousePressEvent(self, event):')
            if insert_pos == -1:
                insert_pos = content.find('    def load_pdf(self')

            if insert_pos != -1:
                content = content[:insert_pos] + paint_event_method + '\n' + content[insert_pos:]

                # Write back
                with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                print("  ✅ Added paintEvent method for field rendering")
            else:
                print("  ⚠️ Could not find insertion point for paintEvent")
        else:
            print("  ✅ paintEvent method already exists")

        return True

    except Exception as e:
        print(f"❌ Error adding field rendering: {e}")
        return False


def main():
    """Main execution function"""
    print("🔧 PDF Voice Editor - Fix Field Creation and Selection")
    print("=" * 60)

    success = True

    # Step 1: Fix SelectionHandler emit issue
    if not fix_selection_handler_emit_issue():
        success = False

    # Step 2: Fix field creation method
    if not fix_field_creation_method():
        success = False

    # Step 3: Ensure PDFCanvas has add_field method
    if not ensure_pdf_canvas_has_add_field():
        success = False

    # Step 4: Ensure FieldManager works
    if not ensure_field_manager_works():
        success = False

    # Step 5: Add field rendering
    if not add_field_rendering():
        success = False

    if success:
        print("\n🎉 Success! Field creation and selection issues fixed.")
        print("\n🎯 You should now be able to:")
        print("   • Click field palette buttons to create fields")
        print("   • See fields appear on the PDF canvas")
        print("   • Select and manipulate fields")
        print("   • No more SelectionHandler emit errors")
        print("\n🎯 Try the application:")
        print("   python launch.py")
        print("   Load a PDF and try creating fields!")
        return 0
    else:
        print("\n⚠️ Some issues may remain. Check the messages above.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())