"""
Properties Panel Widget
Provides UI for editing form field properties with live updates
"""

from typing import Dict, Optional, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QTextEdit, QGroupBox, QGridLayout,
    QComboBox, QSlider, QColorDialog, QPushButton, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor

from models.field_model import FormField, FieldType


class PropertyWidget:
    """Base class for property editing widgets"""

    def __init__(self, name: str, widget, signal_name: str):
        self.name = name
        self.widget = widget
        self.signal_name = signal_name
        self._signal_connected = False

    def connect_signal(self, callback):
        """Connect the widget's change signal to callback"""
        if not self._signal_connected:
            signal = getattr(self.widget, self.signal_name)
            signal.connect(callback)
            self._signal_connected = True

    def set_value(self, value):
        """Set widget value (override in subclasses)"""
        pass

    def get_value(self):
        """Get widget value (override in subclasses)"""
        pass


class TextPropertyWidget(PropertyWidget):
    """Property widget for text values"""

    def __init__(self, name: str, initial_value: str = ""):
        widget = QLineEdit(initial_value)
        super().__init__(name, widget, "textChanged")

    def set_value(self, value):
        self.widget.blockSignals(True)
        try:
            int_value = int(float(value)) if value is not None else 0
        except (ValueError, TypeError):
            int_value = 0
        self.widget.setValue(int_value)
        self.widget.blockSignals(False)

    def get_value(self):
        return self.widget.text()


class NumberPropertyWidget(PropertyWidget):
    """Property widget for numeric values"""

    def __init__(self, name: str, initial_value: int = 0, min_val: int = 0, max_val: int = 9999):
        widget = QSpinBox()
        widget.setRange(min_val, max_val)
        widget.setValue(int(float(initial_value)) if initial_value is not None else 0)
        super().__init__(name, widget, "valueChanged")

    def set_value(self, value):
        self.widget.blockSignals(True)
        self.widget.setValue(int(value))
        self.widget.blockSignals(False)

    def get_value(self):
        return self.widget.value()


class BoolPropertyWidget(PropertyWidget):
    """Property widget for boolean values"""

    def __init__(self, name: str, initial_value: bool = False):
        widget = QCheckBox()
        widget.setChecked(initial_value)
        super().__init__(name, widget, "toggled")

    def set_value(self, value):
        self.widget.blockSignals(True)
        self.widget.setChecked(bool(value))
        self.widget.blockSignals(False)

    def get_value(self):
        return self.widget.isChecked()


class MultilineTextPropertyWidget(PropertyWidget):
    """Property widget for multiline text values"""

    def __init__(self, name: str, initial_value = ""):
        widget = QTextEdit()
        widget.setMaximumHeight(80)

        # Handle both string and list inputs
        if isinstance(initial_value, list):
            text_value = '\n'.join(initial_value)
        else:
            text_value = str(initial_value) if initial_value else ""

        widget.setPlainText(text_value)
        super().__init__(name, widget, "textChanged")

    def set_value(self, value):
        self.widget.blockSignals(True)
        if isinstance(value, list):
            self.widget.setPlainText('\n'.join(str(v) for v in value))
        else:
            self.widget.setPlainText(str(value) if value else "")
        self.widget.blockSignals(False)

    def get_value(self):
        text = self.widget.toPlainText()
        return [line.strip() for line in text.split('\n') if line.strip()]


class ChoicePropertyWidget(PropertyWidget):
    """Property widget for choice/dropdown values"""

    def __init__(self, name: str, choices: list, initial_value: str = ""):
        widget = QComboBox()
        widget.addItems(choices)
        if initial_value in choices:
            widget.setCurrentText(initial_value)
        super().__init__(name, widget, "currentTextChanged")

    def set_value(self, value):
        self.widget.blockSignals(True)
        self.widget.setCurrentText(str(value))
        self.widget.blockSignals(False)

    def get_value(self):
        return self.widget.currentText()


class PropertiesPanel(QWidget):
    """Main properties panel for editing form field properties"""

    propertyChanged = pyqtSignal(str, str, object)  # field_id, property_name, value

    def __init__(self):
        super().__init__()
        self.current_field: Optional[FormField] = None
        self.property_widgets: Dict[str, PropertyWidget] = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the properties panel UI"""
        layout = QVBoxLayout()
        layout.setSpacing(5)

        # Title
        self.title_label = QLabel("Properties")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(self.title_label)

        # Scrollable properties area
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout()
        self.properties_widget.setLayout(self.properties_layout)

        layout.addWidget(self.properties_widget)
        layout.addStretch()

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

    def show_field_properties(self, field: FormField):
        """Show properties for the selected field"""
        self.current_field = field
        self.clear_properties()

        # Field header with type and ID
        self._create_field_header(field)

        # Basic properties (always shown)
        self._create_basic_properties(field)

        # Position and size properties
        self._create_position_size_properties(field)

        # Field-specific properties
        self._create_field_specific_properties(field)

        # Advanced properties
        self._create_advanced_properties(field)

    def update_live_values(self, x: int, y: int, width: int, height: int):
        """Update position and size values during live drag operations"""
        if not self.current_field:
            return

        try:
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
            print(f"⚠️ Error in live update: {e}")

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
            print(f"✅ Updated properties panel for {field_id}")
        except Exception as e:
            print(f"⚠️ Error updating field values: {e}")

    def _create_field_header(self, field: FormField):
        """Create field header with type and ID info"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        header_layout = QVBoxLayout()

        # Field type
        type_label = QLabel(f"🏷️ {field.type.value.title()} Field")
        type_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        type_label.setStyleSheet("color: #0078d4;")
        header_layout.addWidget(type_label)

        # Field ID
        id_label = QLabel(f"ID: {field.id}")
        id_label.setFont(QFont("Arial", 8))
        id_label.setStyleSheet("color: #495057;")
        header_layout.addWidget(id_label)

        header_frame.setLayout(header_layout)
        self.properties_layout.addWidget(header_frame)

    def _create_basic_properties(self, field: FormField):
        """Create basic properties section"""
        basic_group = QGroupBox("Basic Properties")
        basic_layout = QGridLayout()

        # Field name
        basic_layout.addWidget(QLabel("Name:"), 0, 0)
        name_widget = TextPropertyWidget("name", field.name)
        name_widget.connect_signal(lambda value: self._emit_property_change("name", value))
        basic_layout.addWidget(name_widget.widget, 0, 1)
        self.property_widgets["name"] = name_widget

        # Required checkbox
        required_widget = BoolPropertyWidget("required", field.required)
        required_widget.connect_signal(lambda value: self._emit_property_change("required", value))
        basic_layout.addWidget(required_widget.widget, 1, 0, 1, 2)
        required_widget.widget.setText("Required Field")
        self.property_widgets["required"] = required_widget

        basic_group.setLayout(basic_layout)
        self.properties_layout.addWidget(basic_group)

    def _create_position_size_properties(self, field: FormField):
        """Create position and size properties section"""
        pos_group = QGroupBox("Position & Size")
        pos_layout = QGridLayout()

        # X position
        pos_layout.addWidget(QLabel("X:"), 0, 0)
        x_widget = NumberPropertyWidget("x", field.x, 0, 2000)
        x_widget.connect_signal(lambda value: self._emit_property_change("x", value))
        pos_layout.addWidget(x_widget.widget, 0, 1)
        self.property_widgets["x"] = x_widget

        # Y position
        pos_layout.addWidget(QLabel("Y:"), 1, 0)
        y_widget = NumberPropertyWidget("y", field.y, 0, 2000)
        y_widget.connect_signal(lambda value: self._emit_property_change("y", value))
        pos_layout.addWidget(y_widget.widget, 1, 1)
        self.property_widgets["y"] = y_widget

        # Width
        pos_layout.addWidget(QLabel("Width:"), 0, 2)
        width_widget = NumberPropertyWidget("width", field.width, 10, 1000)
        width_widget.connect_signal(lambda value: self._emit_property_change("width", value))
        pos_layout.addWidget(width_widget.widget, 0, 3)
        self.property_widgets["width"] = width_widget

        # Height
        pos_layout.addWidget(QLabel("Height:"), 1, 2)
        height_widget = NumberPropertyWidget("height", field.height, 10, 500)
        height_widget.connect_signal(lambda value: self._emit_property_change("height", value))
        pos_layout.addWidget(height_widget.widget, 1, 3)
        self.property_widgets["height"] = height_widget

        pos_group.setLayout(pos_layout)
        self.properties_layout.addWidget(pos_group)

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

        # Default value
        text_layout.addWidget(QLabel("Default Value:"))
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

        # Placeholder text
        text_layout.addWidget(QLabel("Placeholder:"))
        placeholder_widget = TextPropertyWidget("placeholder", field.properties.get("placeholder", ""))
        placeholder_widget.connect_signal(lambda value: self._emit_property_change("placeholder", value))
        text_layout.addWidget(placeholder_widget.widget)
        self.property_widgets["placeholder"] = placeholder_widget

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

        # Options
        dropdown_layout.addWidget(QLabel("Options (one per line):"))
        options = field.properties.get("options", ["Option 1", "Option 2", "Option 3"])
        options_widget = MultilineTextPropertyWidget("options", options)
        options_widget.connect_signal(lambda: self._emit_property_change("options", options_widget.get_value()))
        dropdown_layout.addWidget(options_widget.widget)
        self.property_widgets["options"] = options_widget

        dropdown_group.setLayout(dropdown_layout)
        self.properties_layout.addWidget(dropdown_group)

    def _create_signature_properties(self, field: FormField):
        """Create signature field specific properties"""
        sig_group = QGroupBox("Signature Properties")
        sig_layout = QVBoxLayout()

        # Signature line color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Line Color:"))

        color_btn = QPushButton("Choose Color")
        color_btn.clicked.connect(lambda: self._choose_color("line_color"))
        color_layout.addWidget(color_btn)

        sig_layout.addLayout(color_layout)

        sig_group.setLayout(sig_layout)
        self.properties_layout.addWidget(sig_group)

    def _create_date_properties(self, field: FormField):
        """Create date field specific properties"""
        date_group = QGroupBox("Date Properties")
        date_layout = QVBoxLayout()

        # Date format
        date_layout.addWidget(QLabel("Date Format:"))
        formats = ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD", "DD-MM-YYYY"]
        format_widget = ChoicePropertyWidget("date_format", formats,
                                           field.properties.get("date_format", "DD/MM/YYYY"))
        format_widget.connect_signal(lambda value: self._emit_property_change("date_format", value))
        date_layout.addWidget(format_widget.widget)
        self.property_widgets["date_format"] = format_widget

        date_group.setLayout(date_layout)
        self.properties_layout.addWidget(date_group)

    def _create_button_properties(self, field: FormField):
        """Create button specific properties"""
        button_group = QGroupBox("Button Properties")
        button_layout = QVBoxLayout()

        # Button text
        button_layout.addWidget(QLabel("Button Text:"))
        text_widget = TextPropertyWidget("value", str(field.value) if field.value else "Button")
        text_widget.connect_signal(lambda value: self._emit_property_change("value", value))
        button_layout.addWidget(text_widget.widget)
        self.property_widgets["value"] = text_widget

        # Button action
        button_layout.addWidget(QLabel("Action:"))
        actions = ["Submit", "Reset", "Custom"]
        action_widget = ChoicePropertyWidget("action", actions,
                                          field.properties.get("action", "Submit"))
        action_widget.connect_signal(lambda value: self._emit_property_change("action", value))
        button_layout.addWidget(action_widget.widget)
        self.property_widgets["action"] = action_widget

        button_group.setLayout(button_layout)
        self.properties_layout.addWidget(button_group)

    def _create_radio_properties(self, field: FormField):
        """Create radio button specific properties"""
        radio_group = QGroupBox("Radio Button Properties")
        radio_layout = QVBoxLayout()

        # Group name
        radio_layout.addWidget(QLabel("Group Name:"))
        group_widget = TextPropertyWidget("group", field.properties.get("group", "radio_group"))
        group_widget.connect_signal(lambda value: self._emit_property_change("group", value))
        radio_layout.addWidget(group_widget.widget)
        self.property_widgets["group"] = group_widget

        # Selected by default
        selected_widget = BoolPropertyWidget("selected", field.properties.get("selected", False))
        selected_widget.connect_signal(lambda value: self._emit_property_change("selected", value))
        selected_widget.widget.setText("Selected by default")
        radio_layout.addWidget(selected_widget.widget)
        self.property_widgets["selected"] = selected_widget

        radio_group.setLayout(radio_layout)
        self.properties_layout.addWidget(radio_group)

    def _create_advanced_properties(self, field: FormField):
        """Create advanced properties section"""
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QVBoxLayout()

        # Read-only option
        readonly_widget = BoolPropertyWidget("readonly", field.properties.get("readonly", False))
        readonly_widget.connect_signal(lambda value: self._emit_property_change("readonly", value))
        readonly_widget.widget.setText("Read-only")
        advanced_layout.addWidget(readonly_widget.widget)
        self.property_widgets["readonly"] = readonly_widget

        # Tab order
        advanced_layout.addWidget(QLabel("Tab Order:"))
        tab_widget = NumberPropertyWidget("tab_order", field.properties.get("tab_order", 0), 0, 100)
        tab_widget.connect_signal(lambda value: self._emit_property_change("tab_order", value))
        advanced_layout.addWidget(tab_widget.widget)
        self.property_widgets["tab_order"] = tab_widget

        advanced_group.setLayout(advanced_layout)
        self.properties_layout.addWidget(advanced_group)

    def _emit_property_change(self, property_name: str, value: Any):
        """Emit property change signal"""
        if self.current_field:
            self.propertyChanged.emit(self.current_field.id, property_name, value)

    def _choose_color(self, property_name: str):
        """Open color chooser dialog"""
        color = QColorDialog.getColor()
        if color.isValid():
            self._emit_property_change(property_name, color.name())

    def update_field_property(self, field_id: str, property_name: str, value: Any):
        """Update property widget when field changes externally"""
        if (self.current_field and
            self.current_field.id == field_id and
            property_name in self.property_widgets):

            widget = self.property_widgets[property_name]
            widget.set_value(value)

    def set_field(self, field: FormField):
        """Alias for show_field_properties to maintain compatibility"""
        self.show_field_properties(field)

    def clear_field(self):
        """Alias for show_no_selection to maintain compatibility"""
        self.show_no_selection()