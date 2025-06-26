"""
Enhanced Field Palette with Tab Control
Reorganizes the field palette into a tabbed interface with Controls and Properties tabs
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
    QLabel, QComboBox, QScrollArea, QPushButton, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from ui.properties_panel import PropertiesPanel  # Existing properties panel


class ControlsTab(QWidget):
    """Tab containing form controls that can be added to the form"""

    fieldRequested = pyqtSignal(str)
    duplicateRequested = pyqtSignal()
    deleteRequested = pyqtSignal()
    alignRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.selected_field_type = None
        self.field_buttons = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the controls tab UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Field Types Section
        self._create_field_types_section(layout)

        # Field Preview Section
        self._create_preview_section(layout)

        # Quick Actions Section
        self._create_quick_actions_section(layout)

        layout.addStretch()
        self.setLayout(layout)

    def _create_field_types_section(self, parent_layout):
        """Create the field types selection section"""
        field_group = QGroupBox("Form Controls")
        field_layout = QVBoxLayout()

        # Create scrollable area for field buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(200)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(5)

        # Define field types with icons and descriptions
        field_types = [
            ("text", "📝", "Text Field", "Single line text input"),
            ("textarea", "📄", "Text Area", "Multi-line text input"),
            ("checkbox", "☑️", "Checkbox", "Checkable box"),
            ("radio", "🔘", "Radio Button", "Single selection option"),
            ("dropdown", "📋", "Dropdown", "Selection list"),
            ("date", "📅", "Date Field", "Date picker"),
            ("number", "🔢", "Number Field", "Numeric input"),
            ("email", "📧", "Email Field", "Email address input"),
            ("signature", "✍️", "Signature", "Digital signature area"),
            ("image", "🖼️", "Image", "Image placeholder"),
        ]

        for field_type, icon, name, description in field_types:
            btn = QPushButton(f"{icon} {name}")
            btn.setToolTip(description)
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda checked, ft=field_type: self._on_field_button_clicked(ft))

            # Store button reference
            self.field_buttons[field_type] = btn
            scroll_layout.addWidget(btn)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        field_layout.addWidget(scroll_area)

        field_group.setLayout(field_layout)
        parent_layout.addWidget(field_group)

        # Apply styling
        self._apply_field_button_styles()

    def _create_preview_section(self, parent_layout):
        """Create the field preview section"""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel("Select a control type to see preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(80)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 12px;
            }
        """)

        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        parent_layout.addWidget(preview_group)

    def _create_quick_actions_section(self, parent_layout):
        """Create the quick actions section"""
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()

        # Create action buttons
        action_buttons = [
            ("📋 Duplicate", "duplicateRequested", "Create a copy of selected field"),
            ("🗑️ Delete", "deleteRequested", "Delete selected field"),
        ]

        for text, signal_name, tooltip in action_buttons:
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setEnabled(False)  # Disabled by default
            btn.clicked.connect(lambda checked, sig=signal_name: getattr(self, sig).emit())
            actions_layout.addWidget(btn)

            # Store reference for enabling/disabling
            setattr(self, f"_{signal_name}_btn", btn)

        # Alignment buttons
        align_frame = QFrame()
        align_layout = QHBoxLayout()
        align_layout.setContentsMargins(0, 0, 0, 0)

        align_label = QLabel("Align:")
        align_layout.addWidget(align_label)

        align_buttons = [
            ("⬅️", "left"), ("➡️", "right"), ("⬆️", "top"), ("⬇️", "bottom")
        ]

        for icon, alignment in align_buttons:
            btn = QPushButton(icon)
            btn.setFixedSize(30, 25)
            btn.setToolTip(f"Align {alignment}")
            btn.setEnabled(False)
            btn.clicked.connect(lambda checked, a=alignment: self.alignRequested.emit(a))
            align_layout.addWidget(btn)
            setattr(self, f"_align_{alignment}_btn", btn)

        align_frame.setLayout(align_layout)
        actions_layout.addWidget(align_frame)

        actions_group.setLayout(actions_layout)
        parent_layout.addWidget(actions_group)

    def _apply_field_button_styles(self):
        """Apply consistent styling to field buttons"""
        style = """
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """
        self.setStyleSheet(style)

    def _on_field_button_clicked(self, field_type: str):
        """Handle field button click"""
        # Clear previous selection
        self.clear_highlights()

        # Set new selection
        self.selected_field_type = field_type
        self.highlight_field_type(field_type, True)

        # Update preview
        self._update_preview(field_type)

        # Emit signal
        self.fieldRequested.emit(field_type)
        print(f"✅ Field type {field_type} selected and ready for placement")

    def _update_preview(self, field_type: str):
        """Update the preview based on selected field type"""
        previews = {
            "text": "📝 [Text Input Field]",
            "textarea": "📄 [Multi-line Text Area]",
            "checkbox": "☑️ [✓] Checkbox",
            "radio": "🔘 ( ) Radio Button",
            "dropdown": "📋 [Select Option ▼]",
            "date": "📅 [MM/DD/YYYY]",
            "number": "🔢 [123]",
            "email": "📧 [user@example.com]",
            "signature": "✍️ [Signature Area]",
            "image": "🖼️ [Image Placeholder]",
        }

        preview_text = previews.get(field_type, f"[{field_type.title()} Field]")
        self.preview_label.setText(preview_text)

    def clear_highlights(self):
        """Clear all field type highlights"""
        for field_type, button in self.field_buttons.items():
            self.highlight_field_type(field_type, False)

    def highlight_field_type(self, field_type: str, highlight: bool = True):
        """Highlight a specific field type"""
        if field_type not in self.field_buttons:
            return

        button = self.field_buttons[field_type]

        if highlight:
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 2px solid #0078d4;
                    border-radius: 4px;
                    background-color: #e3f2fd;
                    color: #0078d4;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #bbdefb;
                    border-color: #0056b3;
                }
            """)
        else:
            button.setStyleSheet("")  # Reset to default

    def set_field_selected(self, has_selection: bool):
        """Enable/disable action buttons based on field selection"""
        # Enable/disable quick action buttons
        for attr_name in dir(self):
            if attr_name.startswith('_') and attr_name.endswith('_btn'):
                btn = getattr(self, attr_name, None)
                if btn:
                    btn.setEnabled(has_selection)

    def reset_selection(self):
        """Reset field type selection"""
        self.clear_highlights()
        self.selected_field_type = None
        self.preview_label.setText("Select a control type to see preview")

    def get_selected_field_type(self):
        """Get the currently selected field type"""
        return self.selected_field_type


class PropertiesTab(QWidget):
    """Tab containing properties for the selected form control"""

    propertyChanged = pyqtSignal(str, str, object)  # field_id, property_name, value

    def __init__(self):
        super().__init__()
        self.current_field = None
        self.field_manager = None  # Will be set by parent
        self.init_ui()

    def init_ui(self):
        """Initialize the properties tab UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Control Selection Section
        self._create_control_selection_section(layout)

        # Properties Panel
        self._create_properties_section(layout)

        layout.addStretch()
        self.setLayout(layout)

    def _create_control_selection_section(self, parent_layout):
        """Create the control selection dropdown section"""
        selection_group = QGroupBox("Selected Control")
        selection_layout = QVBoxLayout()

        # Dropdown for selecting controls
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Control:"))

        self.control_dropdown = QComboBox()
        self.control_dropdown.addItem("No controls available", None)
        self.control_dropdown.currentTextChanged.connect(self._on_control_selected)
        dropdown_layout.addWidget(self.control_dropdown)

        selection_layout.addLayout(dropdown_layout)

        # Info label
        self.control_info_label = QLabel("Select a control to edit its properties")
        self.control_info_label.setStyleSheet("color: #666; font-size: 11px;")
        selection_layout.addWidget(self.control_info_label)

        selection_group.setLayout(selection_layout)
        parent_layout.addWidget(selection_group)

    def _create_properties_section(self, parent_layout):
        """Create the properties editing section"""
        # Use existing PropertiesPanel or create a placeholder
        try:
            self.properties_panel = PropertiesPanel()
            self.properties_panel.propertyChanged.connect(self.propertyChanged)
            parent_layout.addWidget(self.properties_panel)
        except:
            # Fallback if PropertiesPanel not available
            properties_group = QGroupBox("Properties")
            properties_layout = QVBoxLayout()

            self.properties_placeholder = QLabel("Properties panel will appear here when a control is selected")
            self.properties_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.properties_placeholder.setStyleSheet("""
                QLabel {
                    border: 2px dashed #ccc;
                    border-radius: 4px;
                    background-color: #f9f9f9;
                    color: #666;
                    font-size: 12px;
                    padding: 20px;
                }
            """)

            properties_layout.addWidget(self.properties_placeholder)
            properties_group.setLayout(properties_layout)
            parent_layout.addWidget(properties_group)

            self.properties_panel = None

    def _on_control_selected(self, control_text):
        """Called when dropdown selection changes - DON'T propagate"""
        print(f"🔽 Dropdown selected: '{control_text}'")

        if control_text == "No controls available":
            # Highlight nothing, don't propagate (user just selected dropdown)
            self.highlight_control(None, propagate_to_properties=False)
            return

        # Find the field
        field_id = self.control_dropdown.currentData()
        if field_id and self.field_manager:
            field = self.field_manager.get_field_by_id(field_id)
            if field:
                # Highlight WITHOUT propagation (just visual + dropdown update)
                self.highlight_control(field, propagate_to_properties=False)

                # ONLY NOW update properties display (locally)
                self._update_properties_display(field)

    def _notify_main_window_selection(self, field):
        """Notify the main window that a field has been selected from dropdown"""
        try:
            # Find the main window
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'on_field_selected') or hasattr(parent, 'pdf_canvas'):
                    main_window = parent
                    break
                parent = parent.parent()

            if main_window:
                print(f"  Found main window: {type(main_window).__name__}")

                # Method 1: Call the main window's field selection handler directly
                if hasattr(main_window, 'on_field_selected'):
                    main_window.on_field_selected(field)
                    print("  ✅ Called main_window.on_field_selected()")

                # Method 2: Update the canvas selection if available
                if hasattr(main_window, 'pdf_canvas') and main_window.pdf_canvas:
                    canvas = main_window.pdf_canvas

                    # Update the canvas selection handler
                    if hasattr(canvas, 'selection_handler'):
                        canvas.selection_handler.select_field(field)
                        print("  ✅ Updated canvas selection_handler")

                    # Update the enhanced drag handler if available
                    if hasattr(canvas, 'enhanced_drag_handler'):
                        canvas.enhanced_drag_handler.select_field(field)
                        print("  ✅ Updated enhanced_drag_handler")

                    # Trigger a repaint to show selection
                    canvas.update()
                    print("  ✅ Triggered canvas repaint")

                # Method 3: Update the field palette if it has other tabs
                if hasattr(main_window, 'field_palette'):
                    palette = main_window.field_palette
                    if hasattr(palette, 'controls_tab'):
                        # Update the controls tab to reflect selection
                        palette.controls_tab.set_field_selected(field is not None)
                        print("  ✅ Updated controls tab selection state")
            else:
                print("  ⚠️ Could not find main window")

        except Exception as e:
            print(f"  ❌ Error notifying main window of selection: {e}")
            import traceback
            traceback.print_exc()

    def set_field_manager(self, field_manager):
        """Set the field manager reference"""
        print(f"📝 Setting field manager: {field_manager}")  # ← ADD THIS
        print(f"  Field manager has {len(getattr(field_manager, 'fields', []))} fields")  # ← ADD THIS
        self.field_manager = field_manager
        self.refresh_control_list()

    def refresh_control_list(self):
        """Refresh the list of available controls"""
        print("🔄 Refreshing control list...")
        print(f"  DEBUG: self.field_manager = {self.field_manager}")  # ← ADD THIS
        self.control_dropdown.clear()

        if not self.field_manager:
            print("  ⚠️ No field manager available")
            self.control_dropdown.addItem("No controls available", None)
            return

        # Try different methods to get fields
        fields = []
        if hasattr(self.field_manager, 'get_all_fields'):
            fields = self.field_manager.get_all_fields()
        elif hasattr(self.field_manager, 'fields'):
            fields = self.field_manager.fields
        else:
            print("  ⚠️ Field manager has no recognizable fields method")
            self.control_dropdown.addItem("No controls available", None)
            return

        if not fields:
            print("  ℹ️ No fields found in field manager")
            self.control_dropdown.addItem("No controls available", None)
            return

        print(f"  ✅ Found {len(fields)} fields")
        for field in fields:
            try:
                # Get field type safely
                field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                if hasattr(field_type, 'value'):
                    field_type = field_type.value

                # Get field ID safely
                field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))

                display_text = f"{str(field_type).title()} - {field_id}"

                if hasattr(field, 'properties') and isinstance(field.properties, dict) and 'name' in field.properties:
                    display_text = f"{str(field_type).title()} - {field.properties['name']}"

                self.control_dropdown.addItem(display_text, field_id)
                print(f"    Added: {display_text}")

            except Exception as e:
                print(f"  ⚠️ Error adding field to dropdown: {e}")
                continue

    def set_selected_field(self, field):
        """Called externally to set selected field - ALWAYS propagate"""
        print(f"🔧 External field selection: {field.id if field else 'None'}")

        # This is coming from outside (canvas click, etc.) so propagate
        self.highlight_control(field, propagate_to_properties=True)

    def highlight_control(self, field, propagate_to_properties=True):
        """Highlight a control and optionally propagate to main window"""
        print(f"🎯 Highlighting control: {field.id if field else 'None'} (propagate={propagate_to_properties})")

        # Always update these locally
        self.current_field = field
        self._update_dropdown_selection(field)
        self._update_canvas_highlighting(field)

        # ALWAYS update properties display (user expects to see them!)
        self._update_properties_display(field)
        print("  📋 Properties panel updated")

        # Only notify main window if propagate is True
        if propagate_to_properties:
            print("  📤 Propagating to main window...")
            self._notify_main_window(field)
        else:
            print("  🚫 Not propagating to main window")

    def _update_dropdown_selection(self, field):
        """Update dropdown selection without triggering signals"""
        # Block signals to prevent recursion
        self.control_dropdown.blockSignals(True)

        try:
            if not field:
                # Select "No controls available" item
                if self.control_dropdown.count() > 0:
                    self.control_dropdown.setCurrentIndex(0)
            else:
                # Find matching item
                field_id = getattr(field, 'id', getattr(field, 'name', None))
                if field_id:
                    for i in range(self.control_dropdown.count()):
                        if self.control_dropdown.itemData(i) == field_id:
                            self.control_dropdown.setCurrentIndex(i)
                            break
            print("  ✅ Dropdown selection updated (signals blocked)")
        finally:
            # Always restore signals
            self.control_dropdown.blockSignals(False)

    def _update_canvas_highlighting(self, field):
        """Debug version to see exactly what's happening"""
        try:
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'pdf_canvas'):
                canvas = main_window.pdf_canvas

                field_id = getattr(field, 'id', 'None') if field else 'None'
                print(f"  🔧 Updating canvas highlighting to: {field_id}")

                # BEFORE: Check current state
                print(f"  📋 BEFORE UPDATE:")
                if hasattr(canvas, 'selection_handler'):
                    current = getattr(canvas.selection_handler, 'selected_field', None)
                    current_id = getattr(current, 'id', 'None') if current else 'None'
                    print(f"    Selection handler has: {current_id}")

                if hasattr(canvas, 'enhanced_drag_handler'):
                    if hasattr(canvas.enhanced_drag_handler, 'selected_fields'):
                        current_list = canvas.enhanced_drag_handler.selected_fields
                        current_ids = [getattr(f, 'id', 'unknown') for f in current_list]
                        print(f"    Enhanced drag handler has: {current_ids}")

                # UPDATE: Apply new selection
                print(f"  🔄 APPLYING UPDATE:")
                if hasattr(canvas, 'selection_handler'):
                    canvas.selection_handler.selected_field = field
                    print(f"    Set selection_handler.selected_field = {field_id}")

                if hasattr(canvas, 'enhanced_drag_handler'):
                    if hasattr(canvas.enhanced_drag_handler, 'selected_fields'):
                        canvas.enhanced_drag_handler.selected_fields = [field] if field else []
                        print(f"    Set enhanced_drag_handler.selected_fields = [{field_id}]")

                # AFTER: Verify update took effect
                print(f"  📋 AFTER UPDATE:")
                if hasattr(canvas, 'selection_handler'):
                    new_current = getattr(canvas.selection_handler, 'selected_field', None)
                    new_current_id = getattr(new_current, 'id', 'None') if new_current else 'None'
                    print(f"    Selection handler now has: {new_current_id}")

                if hasattr(canvas, 'enhanced_drag_handler'):
                    if hasattr(canvas.enhanced_drag_handler, 'selected_fields'):
                        new_list = canvas.enhanced_drag_handler.selected_fields
                        new_ids = [getattr(f, 'id', 'unknown') for f in new_list]
                        print(f"    Enhanced drag handler now has: {new_ids}")

                # FORCE VISUAL UPDATE
                if hasattr(canvas, 'draw_overlay'):
                    canvas.draw_overlay()
                    print(f"    ✅ draw_overlay() called")

                canvas.update()
                print(f"    ✅ update() called")

        except Exception as e:
            print(f"  ❌ Error updating canvas highlighting: {e}")

    def _notify_main_window(self, field):
        """Notify main window of selection (only when propagating)"""
        try:
            main_window = self._find_main_window()
            if main_window:
                # Update status bar
                if field and hasattr(main_window, 'field_info_label'):
                    field_type = getattr(field, 'field_type', 'unknown')
                    if hasattr(field_type, 'value'):
                        field_type = field_type.value
                    main_window.field_info_label.setText(f"Selected: {field_type} - {field.id}")
                elif hasattr(main_window, 'field_info_label'):
                    main_window.field_info_label.setText("No field selected")

                print("  ✅ Main window notified")
        except Exception as e:
            print(f"  ⚠️ Error notifying main window: {e}")

    def _find_main_window(self):
        """Find the main window by traversing parent hierarchy"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'pdf_canvas') or hasattr(parent, 'on_field_selected'):
                return parent
            parent = parent.parent()
        return None

    def _update_properties_display(self, field):
        """Update the properties display for the selected field"""
        try:
            if self.properties_panel:
                if field:
                    # Use the correct method name that exists in PropertiesPanel
                    self.properties_panel.show_field_properties(field)

                    # Get field info safely
                    field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                    if hasattr(field_type, 'value'):
                        field_type = field_type.value

                    field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))

                    self.control_info_label.setText(f"Editing: {str(field_type).title()} ({field_id})")
                else:
                    # Use the correct method name for clearing
                    self.properties_panel.show_no_selection()
                    self.control_info_label.setText("Select a control to edit its properties")
            else:
                # Update placeholder
                if field:
                    field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                    if hasattr(field_type, 'value'):
                        field_type = field_type.value
                    field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))
                    self.properties_placeholder.setText(f"Properties for {str(field_type).title()} field:\n{field_id}")
                else:
                    self.properties_placeholder.setText("Properties panel will appear here when a control is selected")

        except Exception as e:
            print(f"❌ Error updating properties display: {e}")
            import traceback
            traceback.print_exc()

    def add_field_to_list(self, field):
        """Add a new field to the control list"""
        if self.control_dropdown.itemText(0) == "No controls available":
            self.control_dropdown.clear()

        display_text = f"{field.field_type.title()} - {field.id}"
        if hasattr(field, 'properties') and 'name' in field.properties:
            display_text = f"{field.field_type.title()} - {field.properties['name']}"

        self.control_dropdown.addItem(display_text, field.id)

    def remove_field_from_list(self, field_id):
        """Remove a field from the control list"""
        for i in range(self.control_dropdown.count()):
            if self.control_dropdown.itemData(i) == field_id:
                self.control_dropdown.removeItem(i)
                # Clear current selection if removed field was selected
                if (hasattr(self, 'current_field') and
                        self.current_field and
                        getattr(self.current_field, 'id', None) == field_id):
                    self.current_field = None
                    self._update_properties_display(None)
                    print(f"  ✅ Cleared selection for deleted field: {field_id}")
                break

        if self.control_dropdown.count() == 0:
            self.control_dropdown.addItem("No controls available", None)

    def refresh_and_select_field(self, field_id):
        """Refresh the dropdown and select a specific field - useful for external calls"""
        print(f"🔄 Refreshing dropdown and selecting field: {field_id}")

        # First refresh the dropdown to ensure it has latest data
        self.refresh_control_list()

        # Then try to select the field
        if field_id and self.field_manager:
            field = self.field_manager.get_field_by_id(field_id)
            if field:
                self.set_selected_field(field)
                return True

        return False

class TabbedFieldPalette(QWidget):
    """Main tabbed field palette widget"""

    fieldRequested = pyqtSignal(str)
    duplicateRequested = pyqtSignal()
    deleteRequested = pyqtSignal()
    alignRequested = pyqtSignal(str)
    propertyChanged = pyqtSignal(str, str, object)

    def __init__(self):
        super().__init__()
        self.field_manager = None
        self.init_ui()

    def init_ui(self):
        """Initialize the tabbed interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.controls_tab = ControlsTab()
        self.properties_tab = PropertiesTab()

        # Add tabs to widget
        self.tab_widget.addTab(self.controls_tab, "Controls")
        self.tab_widget.addTab(self.properties_tab, "Properties")

        # Connect signals
        self.controls_tab.fieldRequested.connect(self.fieldRequested)
        self.controls_tab.duplicateRequested.connect(self.duplicateRequested)
        self.controls_tab.deleteRequested.connect(self.deleteRequested)
        self.controls_tab.alignRequested.connect(self.alignRequested)
        self.properties_tab.propertyChanged.connect(self.propertyChanged)

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        # Apply styling
        self._apply_tab_styles()

    def _apply_tab_styles(self):
        """Apply styling to the tab widget"""
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)

    def set_field_manager(self, field_manager):
        """Set the field manager for both tabs"""
        self.field_manager = field_manager
        self.properties_tab.set_field_manager(field_manager)

    def set_field_selected(self, has_selection: bool, field=None):
        """Update both tabs based on field selection"""
        self.controls_tab.set_field_selected(has_selection)

        if has_selection and field:
            self.properties_tab.set_selected_field(field)
            # Switch to properties tab when a field is selected
            self.tab_widget.setCurrentIndex(1)
        elif not has_selection:
            self.properties_tab.set_selected_field(None)

    def add_field_to_list(self, field):
        """Add a new field to the properties tab"""
        self.properties_tab.add_field_to_list(field)

    def remove_field_from_list(self, field_id):
        """Remove a field from the properties tab"""
        self.properties_tab.remove_field_from_list(field_id)

    def refresh_control_list(self):
        """Refresh the control list in properties tab"""
        self.properties_tab.refresh_control_list()

    def clear_highlights(self):
        """Clear highlights in controls tab"""
        self.controls_tab.clear_highlights()

    def highlight_field_type(self, field_type: str):
        """Highlight a field type in controls tab"""
        self.controls_tab.highlight_field_type(field_type, True)

    def reset_selection(self):
        """Reset selection in controls tab"""
        self.controls_tab.reset_selection()

    def get_selected_field_type(self):
        """Get selected field type from controls tab"""
        return self.controls_tab.get_selected_field_type()