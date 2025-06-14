#!/usr/bin/env python3
"""
Add Jump-to-Page and Set-Zoom Controls to Toolbar
Enhances the toolbar with page number input and zoom percentage selector
"""

import os
from pathlib import Path


def add_page_zoom_controls():
    """Add page number input and zoom controls to the toolbar"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Adding jump-to-page and set-zoom controls to toolbar...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Enhanced toolbar with page and zoom controls
        enhanced_toolbar = '''    def create_toolbar(self):
        """Create complete toolbar with page jump and zoom controls"""
        # Create main toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # File operations
        open_action = QAction("📁 Open", self)
        open_action.setToolTip("Open PDF file (Ctrl+O)")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save form data (Ctrl+S)")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_form_data)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Navigation controls with page input
        prev_action = QAction("⬅️", self)
        prev_action.setToolTip("Previous page")
        prev_action.triggered.connect(self.previous_page)
        toolbar.addAction(prev_action)

        # Page input control
        from PyQt6.QtWidgets import QSpinBox, QLabel
        page_label = QLabel("Page:")
        toolbar.addWidget(page_label)

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)  # Will be updated when PDF loads
        self.page_spinbox.setValue(1)
        self.page_spinbox.setToolTip("Jump to page number")
        self.page_spinbox.valueChanged.connect(self.jump_to_page)
        self.page_spinbox.setMinimumWidth(60)
        toolbar.addWidget(self.page_spinbox)

        # Page count label
        self.page_count_label = QLabel("of 1")
        self.page_count_label.setStyleSheet("color: #666; margin-right: 8px;")
        toolbar.addWidget(self.page_count_label)

        next_action = QAction("➡️", self)
        next_action.setToolTip("Next page")
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Zoom controls with percentage selector
        zoom_out_action = QAction("🔍-", self)
        zoom_out_action.setToolTip("Zoom out")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        # Zoom percentage dropdown
        from PyQt6.QtWidgets import QComboBox
        zoom_label = QLabel("Zoom:")
        toolbar.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.setEditable(True)
        zoom_levels = ["25%", "50%", "75%", "100%", "125%", "150%", "200%", "300%", "400%", "Fit Width", "Fit Page"]
        self.zoom_combo.addItems(zoom_levels)
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setToolTip("Set zoom level")
        self.zoom_combo.currentTextChanged.connect(self.set_zoom_level)
        self.zoom_combo.setMinimumWidth(100)
        toolbar.addWidget(self.zoom_combo)

        zoom_in_action = QAction("🔍+", self)
        zoom_in_action.setToolTip("Zoom in")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        toolbar.addSeparator()

        # Quick fit actions
        fit_width_action = QAction("📏 Fit Width", self)
        fit_width_action.setToolTip("Fit page to window width")
        fit_width_action.triggered.connect(self.fit_width)
        toolbar.addAction(fit_width_action)

        fit_page_action = QAction("📄 Fit Page", self)
        fit_page_action.setToolTip("Fit entire page in window")
        fit_page_action.triggered.connect(self.fit_page)
        toolbar.addAction(fit_page_action)

        toolbar.addSeparator()

        # View controls
        self.grid_action = QAction("📐", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setToolTip("Toggle grid display")
        self.grid_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_action)

        toolbar.addSeparator()

        # Info
        info_action = QAction("ℹ️", self)
        info_action.setToolTip("Show application information")
        info_action.triggered.connect(self.show_info)
        toolbar.addAction(info_action)

        # Ensure toolbar is visible
        toolbar.show()
        print("🔧 Enhanced toolbar created with page jump and zoom controls")'''

        # Find and replace the existing create_toolbar method
        toolbar_start = content.find('    def create_toolbar(self):')
        if toolbar_start == -1:
            print("❌ create_toolbar method not found")
            return False

        # Find the end of the current create_toolbar method
        next_method = content.find('\n    def ', toolbar_start + 1)
        if next_method == -1:
            next_method = content.find('\n\n    def ', toolbar_start + 1)
        if next_method == -1:
            next_method = content.find('\ndef ', toolbar_start + 1)
        if next_method == -1:
            next_method = len(content)

        # Replace the existing method
        content = content[:toolbar_start] + enhanced_toolbar + '\n' + content[next_method:]
        print("✅ Replaced toolbar with enhanced version including page/zoom controls")

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error adding page/zoom controls: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_control_methods():
    """Add the methods to handle page jump and zoom setting"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if methods already exist
        if 'def jump_to_page(self)' in content and 'def set_zoom_level(self)' in content:
            print("✅ Control methods already exist")
            return True

        print("🔧 Adding page jump and zoom control methods...")

        # New methods for page and zoom controls
        control_methods = '''
    # Page and Zoom Control Methods
    @pyqtSlot(int)
    def jump_to_page(self, page_number: int):
        """Jump to specific page number"""
        if hasattr(self.pdf_canvas, 'go_to_page'):
            if self.pdf_canvas.go_to_page(page_number):
                self.statusBar().showMessage(f"Jumped to page {page_number}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Invalid page number", 1000)
        else:
            self.statusBar().showMessage("Page navigation not available", 1000)

    @pyqtSlot(str)
    def set_zoom_level(self, zoom_text: str):
        """Set zoom level from dropdown selection"""
        if not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        try:
            if zoom_text == "Fit Width":
                self.fit_width()
            elif zoom_text == "Fit Page":
                self.fit_page()
            elif zoom_text.endswith('%'):
                # Extract percentage value
                percent_str = zoom_text.replace('%', '').strip()
                percent = int(percent_str)
                zoom_level = percent / 100.0
                zoom_level = max(0.1, min(zoom_level, 5.0))  # Clamp to reasonable range

                self.pdf_canvas.set_zoom(zoom_level)
                self.statusBar().showMessage(f"Zoom set to {percent}%", 1000)
                self.update_document_info()
            else:
                # Try to parse as number
                percent = float(zoom_text)
                zoom_level = percent / 100.0
                zoom_level = max(0.1, min(zoom_level, 5.0))

                self.pdf_canvas.set_zoom(zoom_level)
                self.statusBar().showMessage(f"Zoom set to {int(percent)}%", 1000)
                self.update_document_info()

        except ValueError:
            self.statusBar().showMessage("Invalid zoom value", 1000)

    @pyqtSlot()
    def fit_page(self):
        """Fit entire page in window"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Fit page not available", 1000)
            return

        try:
            # Calculate zoom to fit both width and height
            available_width = self.scroll_area.width() - 40
            available_height = self.scroll_area.height() - 40
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)

            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            page_height = self.pdf_canvas.page_pixmap.height() / current_zoom

            zoom_for_width = available_width / page_width
            zoom_for_height = available_height / page_height

            # Use smaller zoom to ensure page fits completely
            new_zoom = min(zoom_for_width, zoom_for_height)
            new_zoom = max(0.1, min(new_zoom, 5.0))

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)

            # Update zoom combo
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText(f"{zoom_percent}%")

            self.statusBar().showMessage(f"Fit page: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Fit page failed", 1000)

    def update_page_controls(self):
        """Update page number controls based on current document"""
        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                current_page = getattr(self.pdf_canvas, 'current_page', 0) + 1
                total_pages = self.pdf_canvas.pdf_document.page_count

                # Update page spinbox
                if hasattr(self, 'page_spinbox'):
                    self.page_spinbox.setMaximum(total_pages)
                    self.page_spinbox.setValue(current_page)

                # Update page count label
                if hasattr(self, 'page_count_label'):
                    self.page_count_label.setText(f"of {total_pages}")

            else:
                # No document loaded
                if hasattr(self, 'page_spinbox'):
                    self.page_spinbox.setMaximum(1)
                    self.page_spinbox.setValue(1)

                if hasattr(self, 'page_count_label'):
                    self.page_count_label.setText("of 1")

        except Exception as e:
            pass  # Fail silently

    def update_zoom_controls(self):
        """Update zoom controls based on current zoom level"""
        try:
            if hasattr(self.pdf_canvas, 'zoom_level'):
                current_zoom = self.pdf_canvas.zoom_level
                zoom_percent = int(current_zoom * 100)

                # Update zoom combo
                if hasattr(self, 'zoom_combo'):
                    self.zoom_combo.setCurrentText(f"{zoom_percent}%")

        except Exception as e:
            pass  # Fail silently
'''

        # Find where to insert the new methods
        # Look for other method definitions
        method_insert_pos = content.find('    def update_document_info(self):')
        if method_insert_pos == -1:
            method_insert_pos = content.find('    @pyqtSlot()')
        if method_insert_pos == -1:
            method_insert_pos = content.find('\ndef main():')

        if method_insert_pos != -1:
            # Insert the new methods
            content = content[:method_insert_pos] + control_methods + '\n' + content[method_insert_pos:]
            print("✅ Added page jump and zoom control methods")
        else:
            print("⚠️ Could not find good insertion point for methods")

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Error adding control methods: {e}")
        return False


def update_document_info_method():
    """Update the update_document_info method to also update page/zoom controls"""

    main_window_path = Path("src/ui/main_window.py")

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if update_document_info already calls the control updates
        if 'self.update_page_controls()' in content:
            print("✅ update_document_info already calls control updates")
            return True

        # Find the update_document_info method
        method_start = content.find('    def update_document_info(self):')
        if method_start == -1:
            print("⚠️ update_document_info method not found")
            return True  # Not critical

        # Find the end of the method
        next_method = content.find('\n    def ', method_start + 1)
        if next_method == -1:
            next_method = content.find('\ndef ', method_start + 1)
        if next_method == -1:
            next_method = len(content)

        method_content = content[method_start:next_method]

        # Add control updates at the end of the method
        control_updates = '''

        # Update page and zoom controls
        self.update_page_controls()
        self.update_zoom_controls()'''

        # Insert before the method ends
        insert_pos = next_method - 1
        content = content[:insert_pos] + control_updates + content[insert_pos:]

        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Updated update_document_info to refresh page/zoom controls")
        return True

    except Exception as e:
        print(f"❌ Error updating document info method: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Add Page Jump and Set Zoom Controls")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Add enhanced toolbar with page/zoom controls
    if not add_page_zoom_controls():
        print("❌ Failed to add page/zoom controls to toolbar")
        return 1

    # Add the control methods
    if not add_control_methods():
        print("❌ Failed to add control methods")
        return 1

    # Update document info method
    if not update_document_info_method():
        print("❌ Failed to update document info method")
        return 1

    print("\n🎉 Page jump and zoom controls added successfully!")
    print("\n🎯 New toolbar features:")
    print("  📁 Open | 💾 Save")
    print("  ⬅️ | Page: [___] of N | ➡️")
    print("  🔍- | Zoom: [100%▼] | 🔍+")
    print("  📏 Fit Width | 📄 Fit Page")
    print("  📐 Grid | ℹ️ Info")
    print("\n🎯 New functionality:")
    print("  • Type page number to jump directly")
    print("  • Select zoom level from dropdown (25% - 400%)")
    print("  • 'Fit Width' and 'Fit Page' options in zoom dropdown")
    print("  • Page controls update when navigating")
    print("\n🚀 Test it now:")
    print("  python launch.py")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())