#!/usr/bin/env python3
"""
Fix Remaining Missing Methods in main_window.py
Adds all the missing methods that toolbars and menus are trying to connect to
"""

import os
from pathlib import Path


def add_remaining_missing_methods():
    """Add all remaining missing methods to main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Adding remaining missing methods to main_window.py...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Define all the remaining missing methods
        additional_methods = '''
    @pyqtSlot()
    def save_form_data(self):
        """Save form field data to JSON file"""
        if not hasattr(self.pdf_canvas, 'get_fields_as_objects') or not self.pdf_canvas.get_fields_as_objects():
            QMessageBox.information(self, "No Data", "No form fields to save")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Form Data", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                form_data = {
                    'pdf_path': self.current_pdf_path,
                    'page': getattr(self.pdf_canvas, 'current_page', 0),
                    'zoom': getattr(self.pdf_canvas, 'zoom_level', 1.0),
                    'fields': [field.to_dict() for field in self.pdf_canvas.get_fields_as_objects()]
                }

                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(form_data, f, indent=2, ensure_ascii=False)

                self.statusBar().showMessage(f"Form data saved to {Path(file_path).name}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save form data:\\n{e}")

    @pyqtSlot()
    def load_form_data(self):
        """Load form field data from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Form Data", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    form_data = json.load(f)

                # Load the PDF if specified and different from current
                pdf_path = form_data.get('pdf_path')
                if pdf_path and pdf_path != self.current_pdf_path:
                    if Path(pdf_path).exists():
                        self.pdf_canvas.load_pdf(pdf_path)
                        self.current_pdf_path = pdf_path

                # Set page and zoom
                if 'page' in form_data and hasattr(self.pdf_canvas, 'set_page'):
                    self.pdf_canvas.set_page(form_data['page'])
                if 'zoom' in form_data and hasattr(self.pdf_canvas, 'set_zoom'):
                    self.pdf_canvas.set_zoom(form_data['zoom'])

                # Load fields
                if 'fields' in form_data and hasattr(self.pdf_canvas, 'get_field_manager'):
                    field_manager = self.pdf_canvas.get_field_manager()
                    if hasattr(field_manager, 'from_dict_list'):
                        field_manager.from_dict_list(form_data['fields'])
                        self.pdf_canvas.draw_overlay()

                self.update_document_info()
                self.statusBar().showMessage(f"Form data loaded from {Path(file_path).name}", 3000)

            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load form data:\\n{e}")

    @pyqtSlot()
    def export_pdf(self):
        """Export PDF with embedded form fields (placeholder)"""
        QMessageBox.information(
            self, "Export PDF",
            "PDF export functionality will be implemented in a future version.\\n"
            "Currently, you can save form data as JSON and reload it later."
        )

    @pyqtSlot()
    def previous_page(self):
        """Navigate to previous page"""
        if hasattr(self.pdf_canvas, 'current_page') and self.pdf_canvas.current_page > 0:
            if hasattr(self.pdf_canvas, 'set_page'):
                self.pdf_canvas.set_page(self.pdf_canvas.current_page - 1)
            self.update_document_info()

    @pyqtSlot()
    def next_page(self):
        """Navigate to next page"""
        if (hasattr(self.pdf_canvas, 'pdf_document') and 
            hasattr(self.pdf_canvas, 'current_page') and
            self.pdf_canvas.pdf_document and
            self.pdf_canvas.current_page < self.pdf_canvas.pdf_document.page_count - 1):
            if hasattr(self.pdf_canvas, 'set_page'):
                self.pdf_canvas.set_page(self.pdf_canvas.current_page + 1)
            self.update_document_info()

    @pyqtSlot()
    def zoom_in(self):
        """Increase zoom level"""
        if hasattr(self.pdf_canvas, 'zoom_level') and hasattr(self.pdf_canvas, 'set_zoom'):
            current_zoom = self.pdf_canvas.zoom_level
            new_zoom = min(current_zoom * 1.25, 5.0)
            self.pdf_canvas.set_zoom(new_zoom)
            # Update zoom combo if it exists
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText(f"{int(new_zoom * 100)}%")

    @pyqtSlot()
    def zoom_out(self):
        """Decrease zoom level"""
        if hasattr(self.pdf_canvas, 'zoom_level') and hasattr(self.pdf_canvas, 'set_zoom'):
            current_zoom = self.pdf_canvas.zoom_level
            new_zoom = max(current_zoom / 1.25, 0.1)
            self.pdf_canvas.set_zoom(new_zoom)
            # Update zoom combo if it exists
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText(f"{int(new_zoom * 100)}%")

    @pyqtSlot(str)
    def zoom_changed(self, text: str):
        """Handle zoom combo box selection"""
        try:
            zoom_percent = int(text.replace('%', ''))
            zoom_level = zoom_percent / 100.0
            if hasattr(self.pdf_canvas, 'set_zoom'):
                self.pdf_canvas.set_zoom(zoom_level)
        except ValueError:
            pass

    @pyqtSlot()
    def fit_width(self):
        """Fit PDF page to window width"""
        if (hasattr(self.pdf_canvas, 'page_pixmap') and 
            hasattr(self.pdf_canvas, 'set_zoom') and
            self.pdf_canvas.page_pixmap):
            available_width = self.scroll_area.width() - 40
            page_width = self.pdf_canvas.page_pixmap.width() / getattr(self.pdf_canvas, 'zoom_level', 1.0)
            new_zoom = available_width / page_width
            self.pdf_canvas.set_zoom(new_zoom)
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText(f"{int(new_zoom * 100)}%")

    @pyqtSlot()
    def toggle_grid(self):
        """Toggle grid display"""
        if hasattr(self.pdf_canvas, 'toggle_grid'):
            self.pdf_canvas.toggle_grid()
            if hasattr(self, 'grid_action') and hasattr(self.pdf_canvas, 'show_grid'):
                self.grid_action.setChecked(self.pdf_canvas.show_grid)

    @pyqtSlot()
    def toggle_voice(self):
        """Toggle voice recognition (placeholder)"""
        if hasattr(self, 'voice_action'):
            if self.voice_action.isChecked():
                self.statusBar().showMessage("Voice recognition activated", 2000)
            else:
                self.statusBar().showMessage("Voice recognition deactivated", 2000)

    @pyqtSlot()
    def duplicate_field(self):
        """Duplicate the currently selected field"""
        if hasattr(self.pdf_canvas, 'duplicate_selected_field'):
            new_field = self.pdf_canvas.duplicate_selected_field()
            if new_field:
                self.statusBar().showMessage(f"Duplicated field: {new_field.name}", 2000)
            else:
                self.statusBar().showMessage("No field selected to duplicate", 2000)

    @pyqtSlot()
    def delete_field(self):
        """Delete the currently selected field"""
        if hasattr(self.pdf_canvas, 'selected_field') and hasattr(self.pdf_canvas, 'delete_selected_field'):
            selected_field = self.pdf_canvas.selected_field
            if selected_field:
                field_name = selected_field.name
                if self.pdf_canvas.delete_selected_field():
                    self.statusBar().showMessage(f"Deleted field: {field_name}", 2000)
            else:
                self.statusBar().showMessage("No field selected to delete", 2000)

    @pyqtSlot()
    def select_all_fields(self):
        """Select all fields (placeholder for multiple selection)"""
        self.statusBar().showMessage("Select all fields - Feature coming soon!", 2000)

    @pyqtSlot(str)
    def align_fields(self, alignment: str):
        """Align selected fields"""
        self.statusBar().showMessage(f"Align {alignment} - Feature coming soon!", 2000)

    @pyqtSlot(str)
    def distribute_fields(self, direction: str):
        """Distribute fields evenly"""
        self.statusBar().showMessage(f"Distribute {direction} - Feature coming soon!", 2000)

    @pyqtSlot()
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table>
        <tr><td><b>Ctrl+O</b></td><td>Open PDF</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save form data</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Duplicate selected field</td></tr>
        <tr><td><b>Delete</b></td><td>Delete selected field</td></tr>
        <tr><td><b>Ctrl+G</b></td><td>Toggle grid</td></tr>
        <tr><td><b>Ctrl++</b></td><td>Zoom in</td></tr>
        <tr><td><b>Ctrl+-</b></td><td>Zoom out</td></tr>
        </table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)

    @pyqtSlot()
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>PDF Voice Editor</h3>
        <p>Enhanced version with draggable form fields</p>
        <p>Version 1.1</p>
        <p>Features:</p>
        <ul>
        <li>Interactive PDF viewing</li>
        <li>Draggable and resizable form fields</li>
        <li>Multiple field types</li>
        <li>Grid snapping</li>
        <li>Form data export/import</li>
        </ul>
        """
        QMessageBox.about(self, "About PDF Voice Editor", about_text)

    def voice_settings(self):
        """Open voice settings dialog"""
        QMessageBox.information(self, "Voice Settings", "Voice settings dialog would open here")

    def form_properties(self):
        """Open form properties dialog"""
        QMessageBox.information(self, "Form Properties", "Form properties dialog would open here")
'''

        # Find where to insert the methods (before existing methods or at end of class)
        insert_pos = content.find('\n    def open_pdf(self):')
        if insert_pos == -1:
            insert_pos = content.find('\ndef main():')
        if insert_pos == -1:
            insert_pos = content.find('if __name__ == "__main__":')
        if insert_pos == -1:
            insert_pos = len(content)

        # Insert the additional methods
        content = content[:insert_pos] + additional_methods + '\n' + content[insert_pos:]

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Added all remaining missing methods to main_window.py")
        print("  📋 Added methods:")
        print("    • save_form_data")
        print("    • load_form_data")
        print("    • export_pdf")
        print("    • previous_page, next_page")
        print("    • zoom_in, zoom_out, zoom_changed")
        print("    • fit_width")
        print("    • toggle_grid, toggle_voice")
        print("    • duplicate_field, delete_field")
        print("    • select_all_fields")
        print("    • align_fields, distribute_fields")
        print("    • show_shortcuts, show_about")
        print("    • voice_settings, form_properties")

        return True

    except Exception as e:
        print(f"❌ Error adding missing methods: {e}")
        import traceback
        traceback.print_exc()
        return False


def simplify_toolbar_creation():
    """Simplify the toolbar creation to avoid missing method errors"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Simplifying toolbar creation...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Define a simple toolbar that won't cause errors
        simple_toolbar = '''    def create_toolbar(self):
        """Create main toolbar with file and field operations"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Open action
        open_action = QAction("📁 Open", self)
        open_action.setToolTip("Open PDF file")
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        # Save action
        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save form data")
        save_action.triggered.connect(self.save_form_data)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Navigation
        prev_action = QAction("⬅️ Previous", self)
        prev_action.triggered.connect(self.previous_page)
        toolbar.addAction(prev_action)

        next_action = QAction("➡️ Next", self)
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Zoom
        zoom_out_action = QAction("🔍- Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        zoom_in_action = QAction("🔍+ Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        toolbar.addSeparator()

        # Grid toggle
        self.grid_action = QAction("📐 Grid", self)
        self.grid_action.setCheckable(True)
        self.grid_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_action)
'''

        # Find and replace the create_toolbar method
        toolbar_start = content.find('def create_toolbar(self):')
        if toolbar_start != -1:
            # Find the end of the method
            next_method = content.find('\\n    def ', toolbar_start + 1)
            if next_method == -1:
                next_method = content.find('\\n\\ndef ', toolbar_start + 1)
            if next_method == -1:
                next_method = len(content)

            # Replace the method
            before = content[:toolbar_start - 4]  # Remove leading spaces
            after = content[next_method:]
            content = before + simple_toolbar + after

            print("  ✅ Simplified create_toolbar method")

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error simplifying toolbar: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Remaining Missing Methods Fixer")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Add remaining missing methods
    if not add_remaining_missing_methods():
        print("❌ Failed to add remaining missing methods")
        return 1

    # Simplify toolbar creation
    if not simplify_toolbar_creation():
        print("❌ Failed to simplify toolbar")
        return 1

    print("\\n🎉 All remaining missing methods added successfully!")
    print("\\n🎯 Next steps:")
    print("1. Try running: python launch.py")
    print("2. If you get field_palette method errors:")
    print("   Run: python fix_field_palette_missing_methods.py")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())