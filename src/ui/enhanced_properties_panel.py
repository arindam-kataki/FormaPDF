"""
Updated Properties Panel with Appearance Settings
Enhanced properties panel that includes font, border, and background appearance settings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QGroupBox, QGridLayout, QPushButton,
    QSizePolicy, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor

from models.field_model import FormField, FieldType
from ui.appearance_properties_widget import AppearancePropertiesWidget


class PropertyWidget:
    """Base class for property widgets"""

    def __init__(self, property_name: str, widget):
        self.property_name = property_name
        self.widget = widget
        self._signal_callback = None

    def connect_signal(self, callback):
        """Connect the widget's signal to a callback"""
        self._signal_callback = callback

    def get_value(self):
        """Get the current value - override in subclasses"""
        return None

    def set_value(self, value):
        """Set the value - override in subclasses"""
        pass


class TextPropertyWidget(PropertyWidget):
    """Property widget for text input"""

    def __init__(self, property_name: str, initial_value: str = ""):
        widget = QLineEdit(initial_value)
        super().__init__(property_name, widget)
        self.widget.textChanged.connect(self._on_value_changed)

    def _on_value_changed(self, value):
        if self._signal_callback:
            self._signal_callback(value)

    def get_value(self):
        return self.widget.text()

    def set_value(self, value):
        self.widget.setText(str(value))


class BoolPropertyWidget(PropertyWidget):
    """Property widget for boolean input"""

    def __init__(self, property_name: str, initial_value: bool = False):
        widget = QCheckBox()
        super().__init__(property_name, widget)
        self.widget.setChecked(initial_value)
        self.widget.toggled.connect(self._on_value_changed)

    def _on_value_changed(self, value):
        if self._signal_callback:
            self._signal_callback(value)

    def get_value(self):
        return self.widget.isChecked()

    def set_value(self, value):
        self.widget.setChecked(bool(value))


class NumberPropertyWidget(PropertyWidget):
    """Property widget for numeric input"""

    def __init__(self, property_name: str, initial_value: int = 0, min_val: int = 0, max_val: int = 2000):
        widget = QSpinBox()
        super().__init__(property_name, widget)
        self.widget.setRange(min_val, max_val)
        self.widget.setValue(initial_value)
        self.widget.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, value):
        if self._signal_callback:
            self._signal_callback(value)

    def get_value(self):
        return self.widget.value()

    def set_value(self, value):
        self.widget.setValue(int(value))


class EnhancedPropertiesPanel(QWidget):
    """Enhanced properties panel with appearance settings"""

    propertyChanged = pyqtSignal(str, object)  # property_name, value
    appearanceChanged = pyqtSignal(dict)  # appearance_properties

    def __init__(self):
        super().__init__()
        self.current_field = None
        self.property_widgets = {}
        self.appearance_widget = None
        self.init_ui()

    def init_ui(self):
        """Initialize the properties panel UI - maximize height"""
        layout = QVBoxLayout()
        layout.setSpacing(0)  # Reduce spacing to maximize content area
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to use full space

        # Create scrollable area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Set size policy to expand and use all available space
        from PyQt6.QtWidgets import QSizePolicy
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set minimum size to ensure it's usable
        scroll_area.setMinimumHeight(200)

        # Remove frame to maximize content area
        scroll_area.setFrameStyle(0)

        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout()
        self.properties_layout.setSpacing(5)
        self.properties_layout.setContentsMargins(5, 5, 5, 5)
        self.properties_widget.setLayout(self.properties_layout)

        # Set size policy for the properties widget
        self.properties_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        scroll_area.setWidget(self.properties_widget)
        layout.addWidget(scroll_area)

        # Set size policy for the main panel to expand vertically
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setLayout(layout)
        self.show_no_selection()

    def show_no_selection(self):
        """Show message when no field is selected"""
        self.clear_properties()
        self.current_field = None

        message = QLabel(
            "No control selected\n\n"
            "💡 Tips:\n"
            "• Click on a control to edit properties\n"
            "• Drag controls to move them\n"
            "• Drag handles to resize them\n"
            "• Use arrow keys for precise movement\n"
            "• Click outside any control to deselect"
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("""
            color: #6c757d; 
            font-style: italic; 
            padding: 20px;
            background-color: #f8f9fa;
            border: 1px dashed #dee2e6;
            border-radius: 4px;
        """)
        self.properties_layout.addWidget(message)

    def clear_properties(self):
        """Clear all property widgets"""
        while self.properties_layout.count():
            child = self.properties_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.property_widgets.clear()
        self.appearance_widget = None

    def show_field_properties(self, field: FormField):
        """Show properties for the selected field"""
        self.current_field = field
        self.clear_properties()

        # Field header with type and ID
        #self._create_field_header(field)

        # Basic properties (always shown)
        self._create_basic_properties(field)

        # Position and size properties
        self._create_position_size_properties(field)

        # Appearance properties (NEW)
        self._create_appearance_properties(field)

        # Field-specific properties
        self._create_field_specific_properties(field)

        # Add stretch to push everything to top
        self.properties_layout.addStretch()

    def _create_field_header(self, field: FormField):
        """Create field header with type and ID info"""
        header_group = QGroupBox(f"{field.type.value.title()} Field Properties")
        header_layout = QVBoxLayout()

        # Field ID (read-only)
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Field ID:"))
        id_label = QLabel(field.id)
        id_label.setStyleSheet("font-family: monospace; background-color: #f5f5f5; padding: 2px;")
        id_layout.addWidget(id_label)
        id_layout.addStretch()
        header_layout.addLayout(id_layout)

        header_group.setLayout(header_layout)
        self.properties_layout.addWidget(header_group)

    def _create_basic_properties(self, field: FormField):
        """Create basic field properties"""
        basic_group = QGroupBox("Basic Properties")
        basic_layout = QVBoxLayout()

        # Field name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_widget = TextPropertyWidget("name", field.name)
        name_widget.connect_signal(lambda value: self._emit_property_change("name", value))
        name_layout.addWidget(name_widget.widget)
        basic_layout.addLayout(name_layout)
        self.property_widgets["name"] = name_widget

        # Required field
        required_widget = BoolPropertyWidget("required", field.required)
        required_widget.connect_signal(lambda value: self._emit_property_change("required", value))
        required_widget.widget.setText("Required Field")
        basic_layout.addWidget(required_widget.widget)
        self.property_widgets["required"] = required_widget

        basic_group.setLayout(basic_layout)
        self.properties_layout.addWidget(basic_group)

    def _create_position_size_properties(self, field: FormField):
        """Create position and size properties"""
        pos_group = QGroupBox("Position & Size")
        pos_layout = QGridLayout()

        # X position
        pos_layout.addWidget(QLabel("X:"), 0, 0)
        x_widget = NumberPropertyWidget("x", field.x, 0, 2000)
        x_widget.connect_signal(lambda value: self._emit_geometry_change())
        pos_layout.addWidget(x_widget.widget, 0, 1)
        self.property_widgets["x"] = x_widget

        # Y position
        pos_layout.addWidget(QLabel("Y:"), 1, 0)
        y_widget = NumberPropertyWidget("y", field.y, 0, 2000)
        y_widget.connect_signal(lambda value: self._emit_geometry_change())
        pos_layout.addWidget(y_widget.widget, 1, 1)
        self.property_widgets["y"] = y_widget

        # Width
        pos_layout.addWidget(QLabel("Width:"), 0, 2)
        width_widget = NumberPropertyWidget("width", field.width, 10, 500)
        width_widget.connect_signal(lambda value: self._emit_geometry_change())
        pos_layout.addWidget(width_widget.widget, 0, 3)
        self.property_widgets["width"] = width_widget

        # Height
        pos_layout.addWidget(QLabel("Height:"), 1, 2)
        height_widget = NumberPropertyWidget("height", field.height, 10, 200)
        height_widget.connect_signal(lambda value: self._emit_geometry_change())
        pos_layout.addWidget(height_widget.widget, 1, 3)
        self.property_widgets["height"] = height_widget

        pos_group.setLayout(pos_layout)
        self.properties_layout.addWidget(pos_group)

    def _create_appearance_properties(self, field: FormField):
        """Create appearance properties by using individual groups"""
        # Create appearance widget without standalone layout
        self.appearance_widget = AppearancePropertiesWidget(field.type.value, standalone=False)
        self.appearance_widget.appearanceChanged.connect(self._on_appearance_changed)

        # Load existing appearance properties from field
        existing_appearance = field.properties.get('appearance', {})
        if existing_appearance:
            self.appearance_widget.set_appearance_properties(existing_appearance)

        # Add the individual groups directly to main properties layout
        for group in self.appearance_widget.get_groups():
            self.properties_layout.addWidget(group)

    def _create_field_specific_properties(self, field: FormField):
        """Create field type-specific properties"""
        if field.type == FieldType.TEXT:
            self._create_text_field_properties(field)
        elif field.type == FieldType.CHECKBOX:
            self._create_checkbox_properties(field)
        elif field.type == FieldType.DROPDOWN:
            self._create_dropdown_properties(field)
        elif field.type == FieldType.SIGNATURE:
            self._create_signature_properties(field)
        elif field.type == FieldType.DATE:
            self._create_date_properties(field)
        elif field.type == FieldType.BUTTON:
            self._create_button_properties(field)
        elif field.type == FieldType.RADIO:
            self._create_radio_properties(field)

    def _create_text_field_properties(self, field: FormField):
        """Create text field specific properties"""
        text_group = QGroupBox("Text Properties")
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        text_layout.setContentsMargins(10, 10, 10, 10)

        # Default value
        default_label = QLabel("Default Value:")
        text_layout.addWidget(default_label)

        value_widget = TextPropertyWidget("value", str(field.value))
        value_widget.connect_signal(lambda value: self._emit_property_change("value", value))
        text_layout.addWidget(value_widget.widget)
        self.property_widgets["value"] = value_widget

        # Multiline option
        multiline_widget = BoolPropertyWidget("multiline", field.properties.get("multiline", False))
        multiline_widget.connect_signal(lambda value: self._emit_property_change("multiline", value))
        multiline_widget.widget.setText("Multiline Text")
        text_layout.addWidget(multiline_widget.widget)
        self.property_widgets["multiline"] = multiline_widget

        text_group.setLayout(text_layout)
        self.properties_layout.addWidget(text_group)

    def _create_checkbox_properties(self, field: FormField):
        """Create checkbox specific properties"""
        checkbox_group = QGroupBox("Checkbox Properties")
        checkbox_layout = QVBoxLayout()

        # Checked by default
        checked_widget = BoolPropertyWidget("checked", field.properties.get("checked", False))
        checked_widget.connect_signal(lambda value: self._emit_property_change("checked", value))
        checked_widget.widget.setText("Checked by default")
        checkbox_layout.addWidget(checked_widget.widget)
        self.property_widgets["checked"] = checked_widget

        checkbox_group.setLayout(checkbox_layout)
        self.properties_layout.addWidget(checkbox_group)

    def _create_dropdown_properties(self, field: FormField):
        """Create dropdown specific properties"""
        dropdown_group = QGroupBox("Dropdown Properties")
        dropdown_layout = QVBoxLayout()

        # Options list (simplified for now)
        options_label = QLabel("Options: (Feature in development)")
        options_label.setStyleSheet("color: #666; font-style: italic;")
        dropdown_layout.addWidget(options_label)

        dropdown_group.setLayout(dropdown_layout)
        self.properties_layout.addWidget(dropdown_group)

    def _create_signature_properties(self, field: FormField):
        """Create signature field properties"""
        sig_group = QGroupBox("Signature Properties")
        sig_layout = QVBoxLayout()

        info_label = QLabel("Signature field ready for digital signing")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        sig_layout.addWidget(info_label)

        sig_group.setLayout(sig_layout)
        self.properties_layout.addWidget(sig_group)

    def _create_date_properties(self, field: FormField):
        """Create date field properties"""
        date_group = QGroupBox("Date Properties")
        date_layout = QVBoxLayout()

        # Date format (simplified)
        format_label = QLabel("Format: DD/MM/YYYY (default)")
        format_label.setStyleSheet("color: #666; font-style: italic;")
        date_layout.addWidget(format_label)

        date_group.setLayout(date_layout)
        self.properties_layout.addWidget(date_group)

    def _create_button_properties(self, field: FormField):
        """Create button field properties"""
        button_group = QGroupBox("Button Properties")
        button_layout = QVBoxLayout()

        # Button text
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Button Text:"))
        button_text_widget = TextPropertyWidget("button_text", field.properties.get("button_text", "Click"))
        button_text_widget.connect_signal(lambda value: self._emit_property_change("button_text", value))
        text_layout.addWidget(button_text_widget.widget)
        button_layout.addLayout(text_layout)
        self.property_widgets["button_text"] = button_text_widget

        button_group.setLayout(button_layout)
        self.properties_layout.addWidget(button_group)

    def _create_radio_properties(self, field: FormField):
        """Create radio button properties"""
        radio_group = QGroupBox("Radio Button Properties")
        radio_layout = QVBoxLayout()

        # Group name
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Group:"))
        group_widget = TextPropertyWidget("radio_group", field.properties.get("radio_group", "group1"))
        group_widget.connect_signal(lambda value: self._emit_property_change("radio_group", value))
        group_layout.addWidget(group_widget.widget)
        radio_layout.addLayout(group_layout)
        self.property_widgets["radio_group"] = group_widget

        radio_group.setLayout(radio_layout)
        self.properties_layout.addWidget(radio_group)

    def _emit_property_change(self, property_name: str, value):
        """Emit property change signal"""
        self.propertyChanged.emit(property_name, value)

    def _emit_geometry_change(self):
        """Emit combined geometry change"""
        if self.current_field:
            geometry = {
                'x': self.property_widgets["x"].get_value(),
                'y': self.property_widgets["y"].get_value(),
                'width': self.property_widgets["width"].get_value(),
                'height': self.property_widgets["height"].get_value()
            }
            self.propertyChanged.emit("geometry", geometry)

    def _on_appearance_changed(self, appearance_props: dict):
        """Handle appearance property changes"""
        self.appearanceChanged.emit(appearance_props)
        # Also emit as regular property change for field update
        self._emit_property_change("appearance", appearance_props)

    def get_current_field(self) -> FormField:
        """Get the currently selected field"""
        return self.current_field

    def update_field_property(self, property_name: str, value):
        """Update a field property and refresh UI if needed"""
        if self.current_field and property_name in self.property_widgets:
            self.property_widgets[property_name].set_value(value)

    # Add this method to the EnhancedPropertiesPanel class in src/ui/enhanced_properties_panel.py

    def update_field_position_size(self, field_id: str, x: int, y: int, width: int, height: int):
        """Update field position and size from external changes (move/resize operations)"""
        if not self.current_field or self.current_field.id != field_id:
            return

        try:
            # Block signals to prevent feedback loop during updates
            self._block_property_signals(True)

            # Update the actual field object
            self.current_field.x = x
            self.current_field.y = y
            self.current_field.width = width
            self.current_field.height = height

            # Update the UI widgets to reflect the changes
            if "x" in self.property_widgets:
                self.property_widgets["x"].set_value(x)
            if "y" in self.property_widgets:
                self.property_widgets["y"].set_value(y)
            if "width" in self.property_widgets:
                self.property_widgets["width"].set_value(width)
            if "height" in self.property_widgets:
                self.property_widgets["height"].set_value(height)

            print(f"✅ Enhanced Properties panel updated for {field_id}: ({x}, {y}) {width}×{height}")

        except Exception as e:
            print(f"⚠️ Error updating enhanced properties panel: {e}")
        finally:
            # Ensure signals are re-enabled even if there's an error
            self._block_property_signals(False)

    def _block_property_signals(self, block: bool):
        """Block or unblock property widget signals to prevent feedback loops"""
        try:
            for widget in self.property_widgets.values():
                if hasattr(widget, 'widget') and hasattr(widget.widget, 'blockSignals'):
                    widget.widget.blockSignals(block)
        except Exception as e:
            print(f"⚠️ Error blocking/unblocking signals: {e}")

    def update_live_values(self, x: int, y: int, width: int, height: int):
        """Update position and size values during live drag operations"""
        if not self.current_field:
            return

        try:
            # Block signals to prevent triggering property changes during live updates
            self._block_property_signals(True)

            # Update position and size widgets without triggering signals
            if "x" in self.property_widgets:
                self.property_widgets["x"].set_value(x)
            if "y" in self.property_widgets:
                self.property_widgets["y"].set_value(y)
            if "width" in self.property_widgets:
                self.property_widgets["width"].set_value(width)
            if "height" in self.property_widgets:
                self.property_widgets["height"].set_value(height)

        except Exception as e:
            print(f"⚠️ Error in enhanced live update: {e}")
        finally:
            # Always re-enable signals
            self._block_property_signals(False)

    def update_field_values(self, field_id: str, x: int, y: int, width: int, height: int):
        """Update field values after operation completion"""
        if not self.current_field or self.current_field.id != field_id:
            return

        try:
            # Update the actual field object
            self.current_field.x = x
            self.current_field.y = y
            self.current_field.width = width
            self.current_field.height = height

            # Update the UI widgets
            self.update_live_values(x, y, width, height)
            print(f"✅ Updated enhanced properties panel for {field_id}")
        except Exception as e:
            print(f"⚠️ Error updating enhanced field values: {e}")