#!/usr/bin/env python3
"""
Fix Missing Methods in main_window.py
Adds all the missing methods that are being called but don't exist
"""

import os
from pathlib import Path


def add_missing_methods():
    """Add all missing methods to main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Adding missing methods to main_window.py...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Define all the missing methods
        missing_methods = '''
    @pyqtSlot()
    def open_pdf(self):
        """Open PDF file dialog and load selected file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            if self.pdf_canvas.load_pdf(file_path):
                self.current_pdf_path = file_path
                self.statusBar().showMessage(f"Loaded: {Path(file_path).name}", 3000)
            else:
                QMessageBox.critical(self, "Error", "Failed to load PDF file")

    @pyqtSlot(str)
    def create_field_at_center(self, field_type: str):
        """Create a new field at the center of the visible area"""
        # Calculate center of visible area
        center_x = self.scroll_area.width() // 2
        center_y = self.scroll_area.height() // 2

        # Convert to canvas coordinates
        scroll_x = self.scroll_area.horizontalScrollBar().value()
        scroll_y = self.scroll_area.verticalScrollBar().value()

        canvas_x = center_x + scroll_x
        canvas_y = center_y + scroll_y

        # Create field
        field = self.pdf_canvas.add_field(field_type, canvas_x, canvas_y)
        self.statusBar().showMessage(f"Created {field_type} field: {field.name}", 2000)

    @pyqtSlot(str)
    def on_field_clicked(self, field_id: str):
        """Handle field selection"""
        selected_field = self.pdf_canvas.selected_field
        if selected_field:
            self.properties_panel.show_field_properties(selected_field)
            self.field_info_label.setText(f"Selected: {selected_field.name} ({selected_field.type.value})")

            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(True)
            if hasattr(self.field_palette, "highlight_field_type"):
                self.field_palette.highlight_field_type(selected_field.type.value)

    @pyqtSlot(object)
    def on_selection_changed(self, field):
        """Handle selection change"""
        if field:
            self.properties_panel.show_field_properties(field)
            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(True)
            if hasattr(self.field_palette, "highlight_field_type"):
                self.field_palette.highlight_field_type(field.type.value)
        else:
            self.properties_panel.show_no_selection()
            if hasattr(self.field_palette, "set_field_selected"):
                self.field_palette.set_field_selected(False)
            if hasattr(self.field_palette, "clear_highlights"):
                self.field_palette.clear_highlights()

    @pyqtSlot(str, int, int)
    def on_field_moved(self, field_id: str, x: int, y: int):
        """Handle field movement"""
        self.operation_label.setText(f"Moved to ({x}, {y})")
        if hasattr(self.properties_panel, 'update_field_property'):
            self.properties_panel.update_field_property(field_id, 'x', x)
            self.properties_panel.update_field_property(field_id, 'y', y)

    @pyqtSlot(str, int, int, int, int)
    def on_field_resized(self, field_id: str, x: int, y: int, width: int, height: int):
        """Handle field resize"""
        self.operation_label.setText(f"Resized to {width}×{height}")
        if hasattr(self.properties_panel, 'update_field_property'):
            self.properties_panel.update_field_property(field_id, 'x', x)
            self.properties_panel.update_field_property(field_id, 'y', y)
            self.properties_panel.update_field_property(field_id, 'width', width)
            self.properties_panel.update_field_property(field_id, 'height', height)

    @pyqtSlot(int, int)
    def on_position_clicked(self, x: int, y: int):
        """Handle position click (no field selected)"""
        self.operation_label.setText(f"Position: ({x}, {y})")
        self.field_info_label.setText("No field selected")

    @pyqtSlot(str, str, object)
    def on_property_changed(self, field_id: str, property_name: str, value):
        """Handle property changes from properties panel"""
        field_manager = self.pdf_canvas.get_field_manager()
        field = field_manager.get_field_by_id(field_id)

        if field:
            if hasattr(field, property_name):
                setattr(field, property_name, value)
            else:
                field.properties[property_name] = value

            self.pdf_canvas.draw_overlay()

    def update_document_info(self):
        """Update document information in the UI"""
        if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
            current = self.pdf_canvas.current_page + 1
            total = self.pdf_canvas.pdf_document.page_count

            zoom_percent = int(self.pdf_canvas.zoom_level * 100)
            fields_count = len(self.pdf_canvas.get_fields_as_objects())

            # Update status if we have the labels
            if hasattr(self, 'operation_label'):
                self.operation_label.setText(f"Zoom: {zoom_percent}% | Fields: {fields_count}")
        else:
            if hasattr(self, 'operation_label'):
                self.operation_label.setText("No document loaded")
'''

        # Find where to insert the methods (before the main function or end of class)
        main_func_pos = content.find('\ndef main():')
        if main_func_pos == -1:
            main_func_pos = content.find('if __name__ == "__main__":')
        if main_func_pos == -1:
            # Insert at the end of the class
            class_end = content.rfind('    def ')
            if class_end != -1:
                # Find the end of the last method
                method_end = content.find('\n\n', class_end)
                if method_end == -1:
                    method_end = len(content)
                insert_pos = method_end
            else:
                insert_pos = len(content)
        else:
            insert_pos = main_func_pos

        # Insert the missing methods
        content = content[:insert_pos] + missing_methods + '\n' + content[insert_pos:]

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Added all missing methods to main_window.py")
        print("  📋 Added methods:")
        print("    • open_pdf")
        print("    • create_field_at_center")
        print("    • on_field_clicked")
        print("    • on_selection_changed")
        print("    • on_field_moved")
        print("    • on_field_resized")
        print("    • on_position_clicked")
        print("    • on_property_changed")
        print("    • update_document_info")

        return True

    except Exception as e:
        print(f"❌ Error adding missing methods: {e}")
        import traceback
        traceback.print_exc()
        return False


def fix_setup_connections():
    """Fix the setup_connections method to handle missing signals safely"""

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
        """Setup signal connections between components"""
        # Field palette connections - safe calls
        if hasattr(self.field_palette, 'fieldRequested'):
            self.field_palette.fieldRequested.connect(self.create_field_at_center)
        if hasattr(self.field_palette, 'duplicateRequested'):
            self.field_palette.duplicateRequested.connect(lambda: print("Duplicate requested"))
        if hasattr(self.field_palette, 'deleteRequested'):
            self.field_palette.deleteRequested.connect(lambda: print("Delete requested"))
        if hasattr(self.field_palette, 'alignRequested'):
            self.field_palette.alignRequested.connect(lambda alignment: print(f"Align {alignment} requested"))

        # PDF canvas connections - safe calls
        if hasattr(self.pdf_canvas, 'fieldClicked'):
            self.pdf_canvas.fieldClicked.connect(self.on_field_clicked)
        if hasattr(self.pdf_canvas, 'fieldMoved'):
            self.pdf_canvas.fieldMoved.connect(self.on_field_moved)
        if hasattr(self.pdf_canvas, 'fieldResized'):
            self.pdf_canvas.fieldResized.connect(self.on_field_resized)
        if hasattr(self.pdf_canvas, 'positionClicked'):
            self.pdf_canvas.positionClicked.connect(self.on_position_clicked)
        if hasattr(self.pdf_canvas, 'selectionChanged'):
            self.pdf_canvas.selectionChanged.connect(self.on_selection_changed)

        # Properties panel connections - safe calls
        if hasattr(self.properties_panel, 'propertyChanged'):
            self.properties_panel.propertyChanged.connect(self.on_property_changed)
'''

        # Find and replace the existing setup_connections method
        setup_start = content.find('def setup_connections(self):')
        if setup_start != -1:
            # Find the end of the method
            next_method = content.find('\n    def ', setup_start + 1)
            if next_method == -1:
                next_method = content.find('\n\ndef ', setup_start + 1)
            if next_method == -1:
                next_method = len(content)

            # Replace the method
            before = content[:setup_start - 4]  # Remove the leading spaces
            after = content[next_method:]
            content = before + new_setup_connections + after

            print("  ✅ Fixed setup_connections method")
        else:
            # Add the method before other methods
            class_start = content.find('class PDFViewerMainWindow')
            if class_start != -1:
                first_method = content.find('\n    def ', class_start)
                if first_method != -1:
                    before = content[:first_method]
                    after = content[first_method:]
                    content = before + '\n' + new_setup_connections + after
                    print("  ✅ Added setup_connections method")

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error fixing setup_connections: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Missing Methods Fixer")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Add missing methods
    if not add_missing_methods():
        print("❌ Failed to add missing methods")
        return 1

    # Fix setup_connections
    if not fix_setup_connections():
        print("❌ Failed to fix setup_connections")
        return 1

    print("\n🎉 All missing methods added successfully!")
    print("\n🎯 Next steps:")
    print("1. Try running: python launch.py")
    print("2. If you get missing field_palette methods:")
    print("   Run: python fix_field_palette_missing_methods.py")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())