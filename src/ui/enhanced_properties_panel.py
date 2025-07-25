"""
Updated Properties Panel with Appearance Settings
Enhanced properties panel that includes font, border, and background appearance settings
"""
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QGroupBox, QGridLayout, QPushButton,
    QSizePolicy, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor

from models.field_model import FormField, FieldType
from ui.appearance_properties_widget import AppearancePropertiesWidget
from ui.property_widgets import ChoicePropertyWidget, MultilineTextPropertyWidget
from ui.text_format_widget import TextFormatWidget
import json

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
        self.control_dropdown = None
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

    def set_control_dropdown(self, dropdown):
        """Set reference to the control dropdown"""
        self.control_dropdown = dropdown

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
        self.text_format_widget = None  # ← ADD THIS LINE

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
        # self._create_field_specific_properties(field)

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
        """Create basic properties with improved horizontal layout"""
        basic_group = QGroupBox("Basic Properties")
        basic_layout = QVBoxLayout()

        # Field Name (label and control on same line)
        name_layout = QHBoxLayout()
        name_label = QLabel("Field Name:")
        name_label.setFixedWidth(80)  # Fixed width for alignment
        name_widget = TextPropertyWidget("name", field.name)
        #name_widget.connect_signal(lambda value: self._emit_property_change("name", value))
        name_widget.widget.editingFinished.connect(lambda: self.handle_name_change(name_widget.widget.text()))
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_widget.widget)
        basic_layout.addLayout(name_layout)
        self.property_widgets["name"] = name_widget

        # Tooltip (label and control on same line)
        tooltip_layout = QHBoxLayout()
        tooltip_label = QLabel("Tooltip:")
        tooltip_label.setFixedWidth(80)
        tooltip_widget = TextPropertyWidget("tooltip", field.tooltip)
        tooltip_widget.connect_signal(lambda value: self._emit_property_change("tooltip", value))
        tooltip_layout.addWidget(tooltip_label)
        tooltip_layout.addWidget(tooltip_widget.widget)
        basic_layout.addLayout(tooltip_layout)
        self.property_widgets["tooltip"] = tooltip_widget

        map_to_layout = QHBoxLayout()
        map_to_label = QLabel("Map to:")
        map_to_label.setFixedWidth(80)

        self.field_manager = self._get_field_manager()

        # Get field-specific choices from field manager
        if hasattr(self, 'field_manager') and self.field_manager:
            map_to_choices = self.field_manager.get_mapping_choices_for_field_type(field.type)
            default_mapping = self.field_manager.get_default_mapping(field.type)
        else:
            # Fallback if field_manager not available
            map_to_choices = ["None"]
            default_mapping = "Auto"

        # Get current value or use default
        current_map_to = getattr(field, 'map_to', default_mapping)

        map_to_widget = ChoicePropertyWidget("map_to", map_to_choices, current_map_to)
        map_to_widget.connect_signal(lambda value: self._emit_property_change("map_to", value))
        map_to_layout.addWidget(map_to_label)
        map_to_layout.addWidget(map_to_widget.widget)
        basic_layout.addLayout(map_to_layout)
        self.property_widgets["map_to"] = map_to_widget

        # Visibility (label and control on same line)
        visibility_layout = QHBoxLayout()
        visibility_label = QLabel("Visibility:")
        visibility_label.setFixedWidth(80)
        visibility_choices = ["Visible", "Hidden", "Visible But Doesn't Print", "Hidden But Printable"]
        visibility_widget = ChoicePropertyWidget("visibility", visibility_choices, field.visibility)
        visibility_widget.connect_signal(lambda value: self._emit_property_change("visibility", value))
        visibility_layout.addWidget(visibility_label)
        visibility_layout.addWidget(visibility_widget.widget)
        #basic_layout.addLayout(visibility_layout)
        self.property_widgets["visibility"] = visibility_widget

        # Orientation (label, smaller dropdown, and "degrees" label on same line)
        orientation_layout = QHBoxLayout()
        orientation_label = QLabel("Orientation:")
        orientation_label.setFixedWidth(80)
        orientation_choices = ["0°", "90°", "180°", "270°"]
        orientation_widget = ChoicePropertyWidget("orientation", orientation_choices, field.orientation)
        orientation_widget.connect_signal(lambda value: self._emit_property_change("orientation", value))

        # Make the dropdown smaller
        orientation_widget.widget.setFixedWidth(70)  # Smaller dropdown width

        # Add "degrees" label
        degrees_label = QLabel("degrees")
        degrees_label.setStyleSheet("color: #666; font-style: italic;")  # Subtle styling

        orientation_layout.addWidget(orientation_label)
        orientation_layout.addWidget(orientation_widget.widget)
        orientation_layout.addWidget(degrees_label)
        orientation_layout.addStretch()  # Push everything to the left

        #basic_layout.addLayout(orientation_layout)
        self.property_widgets["orientation"] = orientation_widget

        # Required and Read Only checkboxes on same line
        checkboxes_layout = QHBoxLayout()

        # Required checkbox
        required_widget = BoolPropertyWidget("required", field.required)
        required_widget.connect_signal(lambda value: self._emit_property_change("required", value))
        required_widget.widget.setText("Required")
        checkboxes_layout.addWidget(required_widget.widget)
        self.property_widgets["required"] = required_widget

        # Read Only checkbox (after required)
        readonly_widget = BoolPropertyWidget("read_only", field.read_only)
        readonly_widget.connect_signal(lambda value: self._emit_property_change("read_only", value))
        readonly_widget.widget.setText("Read only")
        checkboxes_layout.addWidget(readonly_widget.widget)
        self.property_widgets["read_only"] = readonly_widget

        # Add stretch to push checkboxes to the left
        checkboxes_layout.addStretch()

        basic_layout.addLayout(checkboxes_layout)

        # Locked checkbox - last control in the group
        locked_widget = BoolPropertyWidget("locked", field.locked)
        locked_widget.connect_signal(lambda value: self._emit_property_change("locked", value))
        locked_widget.widget.setText("Locked")
        basic_layout.addWidget(locked_widget.widget)
        self.property_widgets["locked"] = locked_widget

        basic_group.setLayout(basic_layout)
        self.properties_layout.addWidget(basic_group)

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

    def _create_position_size_properties(self, field: FormField):
        """Create position and size properties"""
        pos_group = QGroupBox("Position & Size")
        pos_layout = QGridLayout()
        pos_layout.setHorizontalSpacing(8)  # Reduced gap between label and spinner
        pos_layout.setVerticalSpacing(5)
        pos_layout.setContentsMargins(10, 10, 10, 10)

        # Set fixed width for labels to align spinners
        label_width = 50

        # X position
        x_label = QLabel("X:")
        x_label.setFixedWidth(label_width)
        x_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pos_layout.addWidget(x_label, 0, 0)
        x_widget = NumberPropertyWidget("x", field.x, 0, 999)
        x_widget.widget.setMaximumWidth(50)
        x_widget.widget.setMinimumWidth(50)
        x_widget.connect_signal(lambda value: self._emit_geometry_change())
        pos_layout.addWidget(x_widget.widget, 0, 1, Qt.AlignmentFlag.AlignLeft)
        self.property_widgets["x"] = x_widget

        # Y position
        y_label = QLabel("Y:")
        y_label.setFixedWidth(label_width)
        y_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pos_layout.addWidget(y_label, 1, 0)
        y_widget = NumberPropertyWidget("y", field.y, 0, 999)
        y_widget.widget.setMaximumWidth(50)
        y_widget.widget.setMinimumWidth(50)
        y_widget.connect_signal(lambda value: self._emit_geometry_change())
        pos_layout.addWidget(y_widget.widget, 1, 1, Qt.AlignmentFlag.AlignLeft)
        self.property_widgets["y"] = y_widget

        # Width
        width_label = QLabel("Width:")
        width_label.setFixedWidth(label_width)
        width_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pos_layout.addWidget(width_label, 2, 0)
        width_widget = NumberPropertyWidget("width", field.width, 10, 999)
        width_widget.widget.setMaximumWidth(50)
        width_widget.widget.setMinimumWidth(50)
        width_widget.connect_signal(lambda value: self._emit_geometry_change())
        pos_layout.addWidget(width_widget.widget, 2, 1, Qt.AlignmentFlag.AlignLeft)
        self.property_widgets["width"] = width_widget

        # Height
        height_label = QLabel("Height:")
        height_label.setFixedWidth(label_width)
        height_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        pos_layout.addWidget(height_label, 3, 0)
        height_widget = NumberPropertyWidget("height", field.height, 10, 200)
        height_widget.widget.setMaximumWidth(50)
        height_widget.widget.setMinimumWidth(50)
        height_widget.connect_signal(lambda value: self._emit_geometry_change())
        pos_layout.addWidget(height_widget.widget, 3, 1, Qt.AlignmentFlag.AlignLeft)
        self.property_widgets["height"] = height_widget

        pos_group.setLayout(pos_layout)
        self.properties_layout.addWidget(pos_group)

    def _create_appearance_properties(self, field: FormField):
        """Create appearance properties with field-specific selection"""

        # Determine which appearance properties to show for this field type
        appearance_props = self._get_appearance_properties_for_field_type(field.type)

        # Create appearance widget with selective properties
        self.appearance_widget = AppearancePropertiesWidget(
            field_type=field.type.value,
            show_properties=appearance_props,  # ← Key change: pass specific properties
            standalone=False
        )
        self.appearance_widget.appearanceChanged.connect(self._on_appearance_changed)

        # Load existing appearance properties from field
        existing_appearance = field.properties.get('appearance', {})
        if existing_appearance:
            self.appearance_widget.set_appearance_properties(existing_appearance)
            print(f"   Dumping field appearance properties")
            for key, value in existing_appearance.items():
                print(f"   {key}: {type(value).__name__} = {value}")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        print(f"     {sub_key}: {type(sub_value).__name__} = {sub_value}")

        # Add the individual groups directly to main properties layout
        for group in self.appearance_widget.get_groups():
            self.properties_layout.addWidget(group)


    def _get_appearance_properties_for_field_type(self, field_type: FieldType) -> list:
        """Return list of appearance properties to show for each field type"""

        if field_type == FieldType.TEXT:
            return ['font', 'formatting-text'] #, 'border', 'background', 'alignment']

        elif field_type == FieldType.BUTTON:
            return ['font', 'formatting'] #, 'border', 'background']  # No alignment for buttons

        elif field_type == FieldType.SIGNATURE:
            return ['font']  # Only border for signatures

        elif field_type == FieldType.LABEL:
            return ['font', 'formatting'] #'background', 'alignment']  # No border for labels

        elif field_type == FieldType.CHECKBOX:
            return ['font','formatting']  # Minimal appearance for checkboxes

        elif field_type == FieldType.DROPDOWN:
            return ['font', 'formatting'] # 'border', 'background']

        elif field_type == FieldType.LIST_BOX:
            return ['font', 'formatting'] # 'border', 'background']

        #elif field_type == FieldType.DATE:
        #    return ['font', 'border', 'background']

        #elif field_type == FieldType.NUMBER:
        #    return ['font', 'border', 'background', 'alignment']

        #elif field_type == FieldType.EMAIL:
        #    return ['font', 'border', 'background', 'alignment']

        #elif field_type == FieldType.PHONE:
        #    return ['font', 'border', 'background', 'alignment']

        #elif field_type == FieldType.URL:
        #    return ['font', 'border', 'background', 'alignment']

        elif field_type == FieldType.RADIO:
            return ['border']  # Minimal for radio buttons

        elif field_type == FieldType.FILE_UPLOAD:
            return ['font', 'formatting'] #'border', 'background']

        #elif field_type == FieldType.PASSWORD:
        #    return ['font', 'border', 'background']

        else:
            return ['font']  # Default fallback

    def _create_field_specific_properties(self, field: FormField):

        """Create field type-specific properties"""
        if field.type == FieldType.TEXT:
            self._create_text_field_properties(field)
            self._create_text_format_properties(field)
        elif field.type == FieldType.CHECKBOX:
            self._create_checkbox_properties(field)
        elif field.type == FieldType.DROPDOWN:
            self._create_dropdown_properties(field)
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
        elif field.type == FieldType.NUMBER:
            self._create_number_properties(field)
        elif field.type == FieldType.EMAIL:
            self._create_email_properties(field)
        elif field.type == FieldType.PHONE:
            self._create_phone_properties(field)
        elif field.type == FieldType.URL:
            self._create_url_properties(field)
        elif field.type == FieldType.PASSWORD:
            self._create_password_properties(field)
        elif field.type == FieldType.TEXTAREA:
            self._create_textarea_properties(field)
        elif field.type == FieldType.FILE_UPLOAD:
            self._create_file_upload_properties(field)
        elif field.type == FieldType.LABEL:
            self._create_label_properties(field)

    def _create_text_field_properties(self, field: FormField):
        """Create text field specific properties"""
        text_group = QGroupBox("Text Properties_21")
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

    def _create_text_format_properties(self, field: FormField):
        """Create text format properties"""

        # Get current format configuration from field
        current_format = {
            'category': getattr(field, 'format_category', 'None'),
            'settings': {}
        }

        # Parse format_settings if it exists
        format_settings_json = getattr(field, 'format_settings', '{}')
        try:
            current_format['settings'] = json.loads(format_settings_json)
        except (json.JSONDecodeError, AttributeError):
            current_format['settings'] = {}

        # Get input_type if it exists
        input_type = getattr(field, 'input_type', 'text')
        current_format['input_type'] = input_type

        # Create format widget group
        format_group = QGroupBox("Text Format")
        format_layout = QVBoxLayout()
        format_layout.setSpacing(8)
        format_layout.setContentsMargins(10, 10, 10, 10)

        # Create the text format widget
        self.text_format_widget = TextFormatWidget(current_format)
        self.text_format_widget.formatChanged.connect(self._on_text_format_changed)

        format_layout.addWidget(self.text_format_widget)
        format_group.setLayout(format_layout)

        # Add to properties layout
        self.properties_layout.addWidget(format_group)

    def _on_text_format_changed(self, format_config: dict):
        """Handle text format configuration changes"""
        if not self.current_field:
            return

        print(f"DEBUG: Text format changed: {format_config}")  # ← Debug line, remove later

        # Update field properties
        self.current_field.format_category = format_config.get('category', 'None')
        self.current_field.format_settings = json.dumps(format_config.get('settings', {}))

        # Handle input_type for password masking
        if 'input_type' in format_config:
            self.current_field.input_type = format_config['input_type']

        # Emit property changed signals (if the method exists)
        if hasattr(self, '_emit_property_change'):
            self._emit_property_change('format_category', self.current_field.format_category)
            self._emit_property_change('format_settings', self.current_field.format_settings)
            self._emit_property_change('input_type', getattr(self.current_field, 'input_type', 'text'))

        # Emit field changed signal (if the method exists)
        if hasattr(self, 'field_changed'):
            self.field_changed.emit(self.current_field)

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
        """Create dropdown properties with smart validation"""
        dropdown_group = QGroupBox("Dropdown Properties")
        dropdown_layout = QVBoxLayout()

        # === OPTION FORMAT CHOICE ===
        format_label = QLabel("Option Format:")
        dropdown_layout.addWidget(format_label)

        format_options = ["Text Only", "Value | Text"]
        format_widget = ChoicePropertyWidget("option_format", format_options,
                                             field.properties.get("option_format", "Text Only"))
        format_widget.connect_signal(self._on_format_changed)  # Connect to handler
        dropdown_layout.addWidget(format_widget.widget)
        self.property_widgets["option_format"] = format_widget

        # === OPTIONS INPUT ===
        options_label = QLabel("Options:")
        self.help_text_label = QLabel()  # Make it accessible for updates
        self._update_help_text(format_widget.get_value())  # Set initial help
        dropdown_layout.addWidget(options_label)
        dropdown_layout.addWidget(self.help_text_label)

        options = field.properties.get("options", ["Option 1", "Option 2", "Option 3"])
        options_widget = MultilineTextPropertyWidget("options", options)
        options_widget.connect_signal(lambda: self._emit_property_change("options", options_widget.get_value()))
        dropdown_layout.addWidget(options_widget.widget)
        self.property_widgets["options"] = options_widget

        # === ALLOW CUSTOM INPUT (Smart Default) ===
        # Auto-set based on format, but user can override
        default_allow_custom = format_widget.get_value() == "Value | Text"
        custom_widget = BoolPropertyWidget("allow_custom",
                                           field.properties.get("allow_custom", default_allow_custom))
        custom_widget.connect_signal(lambda value: self._emit_property_change("allow_custom", value))
        custom_widget.widget.setText("Allow users to enter custom values")
        dropdown_layout.addWidget(custom_widget.widget)
        self.property_widgets["allow_custom"] = custom_widget

        dropdown_group.setLayout(dropdown_layout)
        self.properties_layout.addWidget(dropdown_group)

    def _create_list_box_properties(self, field: FormField):
        """Create list box specific properties - complete implementation"""
        listbox_group = QGroupBox("List Box Properties")
        listbox_layout = QVBoxLayout()

        # === OPTION FORMAT CHOICE ===
        format_label = QLabel("Option Format:")
        listbox_layout.addWidget(format_label)

        format_options = ["Text Only", "Value | Text"]
        format_widget = ChoicePropertyWidget("option_format", format_options,
                                             field.properties.get("option_format", "Text Only"))
        format_widget.connect_signal(self._on_format_changed)
        listbox_layout.addWidget(format_widget.widget)
        self.property_widgets["option_format"] = format_widget

        # === OPTIONS INPUT ===
        options_label = QLabel("Options:")
        self.help_text_label = QLabel()
        self._update_help_text(format_widget.get_value())
        listbox_layout.addWidget(options_label)
        listbox_layout.addWidget(self.help_text_label)

        options = field.properties.get("options", ["Option 1", "Option 2", "Option 3"])
        options_widget = MultilineTextPropertyWidget("options", options)
        options_widget.connect_signal(lambda: self._emit_property_change("options", options_widget.get_value()))
        listbox_layout.addWidget(options_widget.widget)
        self.property_widgets["options"] = options_widget

        # === SELECTION MODE (List Box Specific) ===
        mode_label = QLabel("Selection Mode:")
        listbox_layout.addWidget(mode_label)
        mode_options = ["Single Selection", "Multiple Selection"]
        mode_widget = ChoicePropertyWidget("selection_mode", mode_options,
                                           field.properties.get("selection_mode", "Single Selection"))
        mode_widget.connect_signal(lambda value: self._emit_property_change("selection_mode", value))
        listbox_layout.addWidget(mode_widget.widget)
        self.property_widgets["selection_mode"] = mode_widget

        # === VISIBLE ROWS (List Box Specific) ===
        rows_label = QLabel("Visible Rows:")
        listbox_layout.addWidget(rows_label)
        rows_widget = TextPropertyWidget("visible_rows", str(field.properties.get("visible_rows", "4")))
        rows_widget.connect_signal(lambda value: self._emit_property_change("visible_rows", value))
        listbox_layout.addWidget(rows_widget.widget)
        self.property_widgets["visible_rows"] = rows_widget

        # === DEFAULT SELECTION ===
        default_label = QLabel("Default Selection:")
        listbox_layout.addWidget(default_label)
        default_widget = TextPropertyWidget("default_selection", field.properties.get("default_selection", ""))
        default_widget.connect_signal(lambda value: self._emit_property_change("default_selection", value))
        listbox_layout.addWidget(default_widget.widget)
        self.property_widgets["default_selection"] = default_widget

        # === ALLOW CUSTOM INPUT (Smart Default) ===
        default_allow_custom = format_widget.get_value() == "Text Only"
        custom_widget = BoolPropertyWidget("allow_custom",
                                           field.properties.get("allow_custom", default_allow_custom))
        custom_widget.connect_signal(lambda value: self._emit_property_change("allow_custom", value))
        custom_widget.widget.setText("Allow users to enter custom values")
        listbox_layout.addWidget(custom_widget.widget)
        self.property_widgets["allow_custom"] = custom_widget

        listbox_group.setLayout(listbox_layout)
        self.properties_layout.addWidget(listbox_group)

    def _on_format_changed(self, format_value):
        """Handle format change - update help text and custom input default"""
        self._update_help_text(format_value)

        # CORRECTED: Auto-update "Allow Custom" based on format
        if "allow_custom" in self.property_widgets:
            custom_widget = self.property_widgets["allow_custom"]
            if format_value == "Text Only":
                custom_widget.widget.setChecked(True)  # DEFAULT: Allow free text
                custom_widget.widget.setEnabled(True)
            else:  # Value | Text
                custom_widget.widget.setChecked(False)  # DEFAULT: Restrict to mappings
                custom_widget.widget.setEnabled(False)

        self._emit_property_change("option_format", format_value)

    def _update_help_text(self, format_choice):
        """Update help text based on selected format"""
        if format_choice == "Text Only":
            help_text = ("Format: One option per line\n"
                         "Example:\n"
                         "Red\n"
                         "Blue\n"
                         "Green\n"
                         "→ Users can type any text + select from list")
        else:  # Value | Text
            help_text = ("Format: value | display text (one per line)\n"
                         "Example:\n"
                         "R | Red\n"
                         "B | Blue\n"
                         "G | Green\n"
                         "→ Users restricted to these exact mappings")

        self.help_text_label.setText(help_text)
        self.help_text_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic; padding: 5px;")

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

    def _on_map_to_changed(self, map_to_value: str):
        """Handle Map to dropdown change - update field behavior and display"""
        try:
            # First emit the property change as usual
            self._emit_property_change("map_to", map_to_value)

            # Then update the field's display/behavior based on selection
            if hasattr(self, 'current_field') and self.current_field:
                self._update_field_display_for_mapping(self.current_field, map_to_value)

            print(f"🔄 Map to changed: {map_to_value}")

        except Exception as e:
            print(f"❌ Error handling map to change: {e}")


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

    def question_update_field_property(self, field_id: str, property_name: str, value: Any):
        """Update property widget when field changes externally"""
        if (self.current_field and
            self.current_field.id == field_id and
            property_name in self.property_widgets):

            widget = self.property_widgets[property_name]
            widget.set_value(value)
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

    def _create_number_properties(self, field: FormField):
        """Create number field properties"""
        number_group = QGroupBox("Number Properties")
        number_layout = QVBoxLayout()

        # Min value
        min_label = QLabel("Minimum Value:")
        number_layout.addWidget(min_label)
        min_widget = NumberPropertyWidget("min_value", field.properties.get("min_value", 0), -999999, 999999)
        min_widget.connect_signal(lambda value: self._emit_property_change("min_value", value))
        number_layout.addWidget(min_widget.widget)
        self.property_widgets["min_value"] = min_widget

        # Max value
        max_label = QLabel("Maximum Value:")
        number_layout.addWidget(max_label)
        max_widget = NumberPropertyWidget("max_value", field.properties.get("max_value", 100), -999999, 999999)
        max_widget.connect_signal(lambda value: self._emit_property_change("max_value", value))
        number_layout.addWidget(max_widget.widget)
        self.property_widgets["max_value"] = max_widget

        # Decimal places
        decimal_widget = BoolPropertyWidget("allow_decimal", field.properties.get("allow_decimal", False))
        decimal_widget.connect_signal(lambda value: self._emit_property_change("allow_decimal", value))
        decimal_widget.widget.setText("Allow decimal numbers")
        number_layout.addWidget(decimal_widget.widget)
        self.property_widgets["allow_decimal"] = decimal_widget

        number_group.setLayout(number_layout)
        self.properties_layout.addWidget(number_group)

    def _create_email_properties(self, field: FormField):
        """Create email field properties"""
        email_group = QGroupBox("Email Properties")
        email_layout = QVBoxLayout()

        # Validation
        validate_widget = BoolPropertyWidget("validate_email", field.properties.get("validate_email", True))
        validate_widget.connect_signal(lambda value: self._emit_property_change("validate_email", value))
        validate_widget.widget.setText("Validate email format")
        email_layout.addWidget(validate_widget.widget)
        self.property_widgets["validate_email"] = validate_widget

        email_group.setLayout(email_layout)
        self.properties_layout.addWidget(email_group)

    def _create_phone_properties(self, field: FormField):
        """Create phone field properties"""
        phone_group = QGroupBox("Phone Properties")
        phone_layout = QVBoxLayout()

        # Format
        format_label = QLabel("Phone Format:")
        phone_layout.addWidget(format_label)
        formats = ["(XXX) XXX-XXXX", "XXX-XXX-XXXX", "+X XXX XXX XXXX", "XXX.XXX.XXXX"]
        format_widget = ChoicePropertyWidget("phone_format", formats,
                                             field.properties.get("phone_format", "(XXX) XXX-XXXX"))
        format_widget.connect_signal(lambda value: self._emit_property_change("phone_format", value))
        phone_layout.addWidget(format_widget.widget)
        self.property_widgets["phone_format"] = format_widget

        phone_group.setLayout(phone_layout)
        self.properties_layout.addWidget(phone_group)

    def _create_url_properties(self, field: FormField):
        """Create URL field properties"""
        url_group = QGroupBox("URL Properties")
        url_layout = QVBoxLayout()

        # Validation
        validate_widget = BoolPropertyWidget("validate_url", field.properties.get("validate_url", True))
        validate_widget.connect_signal(lambda value: self._emit_property_change("validate_url", value))
        validate_widget.widget.setText("Validate URL format")
        url_layout.addWidget(validate_widget.widget)
        self.property_widgets["validate_url"] = validate_widget

        url_group.setLayout(url_layout)
        self.properties_layout.addWidget(url_group)

    def _create_password_properties(self, field: FormField):
        """Create password field properties"""
        password_group = QGroupBox("Password Properties")
        password_layout = QVBoxLayout()

        # Show/hide toggle
        show_toggle_widget = BoolPropertyWidget("show_toggle", field.properties.get("show_toggle", True))
        show_toggle_widget.connect_signal(lambda value: self._emit_property_change("show_toggle", value))
        show_toggle_widget.widget.setText("Show password toggle button")
        password_layout.addWidget(show_toggle_widget.widget)
        self.property_widgets["show_toggle"] = show_toggle_widget

        password_group.setLayout(password_layout)
        self.properties_layout.addWidget(password_group)

    def _create_textarea_properties(self, field: FormField):
        """Create textarea field properties"""
        textarea_group = QGroupBox("Text Area Properties")
        textarea_layout = QVBoxLayout()

        # Rows
        rows_label = QLabel("Number of Rows:")
        textarea_layout.addWidget(rows_label)
        rows_widget = NumberPropertyWidget("rows", field.properties.get("rows", 3), 1, 20)
        rows_widget.connect_signal(lambda value: self._emit_property_change("rows", value))
        textarea_layout.addWidget(rows_widget.widget)
        self.property_widgets["rows"] = rows_widget

        # Character limit
        char_limit_widget = BoolPropertyWidget("enable_char_limit", field.properties.get("enable_char_limit", False))
        char_limit_widget.connect_signal(lambda value: self._emit_property_change("enable_char_limit", value))
        char_limit_widget.widget.setText("Enable character limit")
        textarea_layout.addWidget(char_limit_widget.widget)
        self.property_widgets["enable_char_limit"] = char_limit_widget

        textarea_group.setLayout(textarea_layout)
        self.properties_layout.addWidget(textarea_group)

    def _create_file_upload_properties(self, field: FormField):
        """Create file upload field properties"""
        file_group = QGroupBox("File Upload Properties")
        file_layout = QVBoxLayout()

        # Accepted file types
        types_label = QLabel("Accepted File Types:")
        file_layout.addWidget(types_label)
        file_types = ["PDF", "Images (PNG, JPG)", "Documents (DOC, DOCX)", "All Files"]
        types_widget = ChoicePropertyWidget("accepted_types", file_types,
                                            field.properties.get("accepted_types", "All Files"))
        types_widget.connect_signal(lambda value: self._emit_property_change("accepted_types", value))
        file_layout.addWidget(types_widget.widget)
        self.property_widgets["accepted_types"] = types_widget

        # Max file size
        size_label = QLabel("Max File Size (MB):")
        file_layout.addWidget(size_label)
        size_widget = NumberPropertyWidget("max_size_mb", field.properties.get("max_size_mb", 10), 1, 100)
        size_widget.connect_signal(lambda value: self._emit_property_change("max_size_mb", value))
        file_layout.addWidget(size_widget.widget)
        self.property_widgets["max_size_mb"] = size_widget

        # Multiple files
        multiple_widget = BoolPropertyWidget("multiple_files", field.properties.get("multiple_files", False))
        multiple_widget.connect_signal(lambda value: self._emit_property_change("multiple_files", value))
        multiple_widget.widget.setText("Allow multiple file selection")
        file_layout.addWidget(multiple_widget.widget)
        self.property_widgets["multiple_files"] = multiple_widget

        file_group.setLayout(file_layout)
        self.properties_layout.addWidget(file_group)

    def _create_label_properties(self, field: FormField):
        """Create label field properties"""
        label_group = QGroupBox("Label Properties")
        label_layout = QVBoxLayout()

        # Label text - this is the only label-specific property needed
        text_label = QLabel("Label Text:")
        label_layout.addWidget(text_label)
        text_widget = TextPropertyWidget("label_text", field.properties.get("label_text", "Label"))
        text_widget.connect_signal(lambda value: self._emit_property_change("label_text", value))
        label_layout.addWidget(text_widget.widget)
        self.property_widgets["label_text"] = text_widget

        # Word wrap
        wrap_widget = BoolPropertyWidget("word_wrap", field.properties.get("word_wrap", True))
        wrap_widget.connect_signal(lambda value: self._emit_property_change("word_wrap", value))
        wrap_widget.widget.setText("Enable word wrap")
        label_layout.addWidget(wrap_widget.widget)
        self.property_widgets["word_wrap"] = wrap_widget

        label_group.setLayout(label_layout)
        self.properties_layout.addWidget(label_group)

    def _create_validation_properties(self, field: FormField):
        """Create validation properties"""
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout()

        # Required field
        required_widget = BoolPropertyWidget("required", field.properties.get("required", False))
        required_widget.connect_signal(lambda value: self._emit_property_change("required", value))
        required_widget.widget.setText("Required field")
        validation_layout.addWidget(required_widget.widget)
        self.property_widgets["required"] = required_widget

        # Custom validation message
        message_label = QLabel("Validation Message:")
        validation_layout.addWidget(message_label)
        message_widget = TextPropertyWidget("validation_message", field.properties.get("validation_message", ""))
        message_widget.connect_signal(lambda value: self._emit_property_change("validation_message", value))
        validation_layout.addWidget(message_widget.widget)
        self.property_widgets["validation_message"] = message_widget

        validation_group.setLayout(validation_layout)
        self.properties_layout.addWidget(validation_group)

    def _create_accessibility_properties(self, field: FormField):
        """Create accessibility properties"""
        a11y_group = QGroupBox("Accessibility")
        a11y_layout = QVBoxLayout()

        # Alt text
        alt_label = QLabel("Alt Text:")
        a11y_layout.addWidget(alt_label)
        alt_widget = TextPropertyWidget("alt_text", field.properties.get("alt_text", ""))
        alt_widget.connect_signal(lambda value: self._emit_property_change("alt_text", value))
        a11y_layout.addWidget(alt_widget.widget)
        self.property_widgets["alt_text"] = alt_widget

        # Tab order
        tab_label = QLabel("Tab Order:")
        a11y_layout.addWidget(tab_label)
        tab_widget = NumberPropertyWidget("tab_order", field.properties.get("tab_order", 0), 0, 999)
        tab_widget.connect_signal(lambda value: self._emit_property_change("tab_order", value))
        a11y_layout.addWidget(tab_widget.widget)
        self.property_widgets["tab_order"] = tab_widget

        a11y_group.setLayout(a11y_layout)
        self.properties_layout.addWidget(a11y_group)

    def _create_number_properties(self, field: FormField):
        """Create number field properties"""
        number_group = QGroupBox("Number Properties")
        number_layout = QVBoxLayout()

        # Min value - TEXT BOX
        min_label = QLabel("Minimum Value:")
        number_layout.addWidget(min_label)
        min_widget = TextPropertyWidget("min_value", str(field.properties.get("min_value", "")))
        min_widget.connect_signal(lambda value: self._emit_property_change("min_value", value))
        number_layout.addWidget(min_widget.widget)
        self.property_widgets["min_value"] = min_widget

        # Max value - TEXT BOX
        max_label = QLabel("Maximum Value:")
        number_layout.addWidget(max_label)
        max_widget = TextPropertyWidget("max_value", str(field.properties.get("max_value", "")))
        max_widget.connect_signal(lambda value: self._emit_property_change("max_value", value))
        number_layout.addWidget(max_widget.widget)
        self.property_widgets["max_value"] = max_widget

        # Default value - TEXT BOX
        default_label = QLabel("Default Value:")
        number_layout.addWidget(default_label)
        default_widget = TextPropertyWidget("default_value", str(field.properties.get("default_value", "")))
        default_widget.connect_signal(lambda value: self._emit_property_change("default_value", value))
        number_layout.addWidget(default_widget.widget)
        self.property_widgets["default_value"] = default_widget

        # Decimal places - TEXT BOX
        decimal_label = QLabel("Decimal Places:")
        number_layout.addWidget(decimal_label)
        decimal_widget = TextPropertyWidget("decimal_places", str(field.properties.get("decimal_places", "2")))
        decimal_widget.connect_signal(lambda value: self._emit_property_change("decimal_places", value))
        number_layout.addWidget(decimal_widget.widget)
        self.property_widgets["decimal_places"] = decimal_widget

        # Allow negative - CHECKBOX
        negative_widget = BoolPropertyWidget("allow_negative", field.properties.get("allow_negative", True))
        negative_widget.connect_signal(lambda value: self._emit_property_change("allow_negative", value))
        negative_widget.widget.setText("Allow negative numbers")
        number_layout.addWidget(negative_widget.widget)
        self.property_widgets["allow_negative"] = negative_widget

        number_group.setLayout(number_layout)
        self.properties_layout.addWidget(number_group)

    def handle_name_change(self, value):
        """Handle name field changes with validation"""
        if not self.current_field:
            return

        # Get the current name
        current_name = self.current_field.name

        # IMPORTANT: Skip validation if name hasn't actually changed
        if value == current_name:
            print(f"✅ Name unchanged: '{value}' - skipping validation")
            return

        # Validate the new name
        is_valid, error_message = self.validate_control_name(value, self.current_field)

        if not is_valid:
            # Show error message
            self.show_error_message_box(error_message)

            # Revert to original name and select text
            if "name" in self.property_widgets:
                name_widget = self.property_widgets["name"]
                name_widget.widget.setText(current_name)
                name_widget.widget.selectAll()
                name_widget.widget.setFocus()
        else:
            # Valid name - update field and emit signal
            old_name = self.current_field.name
            self.current_field.name = value

            # Update dropdown display
            self.refresh_control_dropdown_item(self.current_field.id, value)

            self._emit_property_change("name", value)
            print(f"✅ Renamed control {self.current_field.id}: '{old_name}' -> '{value}'")

    def validate_control_name(self, new_name, current_control_id=None):
        """Validate control name according to requirements"""
        import re

        # Check for empty/null
        if not new_name or not new_name.strip():
            return False, "Name cannot be empty"

        name = new_name.strip()

        # Check minimum length
        if len(name) < 1:
            return False, "Name cannot be empty"

        # Check maximum length
        if len(name) > 50:
            return False, "Name too long (maximum 50 characters)"

        # Check starts with letter
        if not name[0].isalpha():
            return False, "Name must start with a letter (A-Z, a-z)"

        # Check alphanumeric + underscore + dash only
        if not re.match(r'^[A-Za-z][A-Za-z0-9_-]*$', name):
            return False, "Name can only contain letters, numbers, underscores (_), and dashes (-)"

        # Check for consecutive dashes
        if '--' in name:
            return False, "Consecutive dashes (--) are not allowed"

        # Check for periods (PDF SFN issue)
        if '.' in name:
            return False, "Periods (.) are not allowed in field names"

        # Check uniqueness (case-insensitive)
        if self.is_name_duplicate(name, current_control_id):
            return False, f"Name '{name}' is already in use"

        return True, "Valid name"

    def show_error_message_box(self, error_message):
        """Show error message with appropriate formatting"""
        from PyQt6.QtWidgets import QMessageBox

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Invalid Field Name")

        # Customize message based on error type
        if "cannot be empty" in error_message:
            msg_box.setText("Field Name Required")
            msg_box.setInformativeText("Please enter a name for this field.")
        elif "too long" in error_message:
            msg_box.setText("Name Too Long")
            msg_box.setInformativeText(f"{error_message}\n\nPlease use a shorter name.")
        elif "must start with" in error_message:
            msg_box.setText("Invalid Name Format")
            msg_box.setInformativeText(f"{error_message}\n\nExample: Field1, MyControl, Button_A")
        elif "can only contain" in error_message:
            msg_box.setText("Invalid Characters")
            msg_box.setInformativeText(f"{error_message}\n\nAllowed: letters, numbers, underscores (_), dashes (-)")
        else:
            msg_box.setText(error_message)

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def is_name_duplicate(self, name, exclude_control_id=None):
        """Check if name already exists (case-insensitive)"""
        if not hasattr(self, 'field_manager') or not self.field_manager:
            self.field_manager = self._get_field_manager()

        if not self.field_manager:
            return False  # Can't check if no field manager

        existing_names = []
        for field in self.field_manager.get_all_fields():
            if exclude_control_id is None or field.id != exclude_control_id:
                existing_names.append(field.name.lower())

        return name.lower() in existing_names

    def _get_field_manager(self):
        """Get field manager from parent hierarchy"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'field_manager'):
                return parent.field_manager
            parent = parent.parent()
        return None

    def refresh_control_dropdown_item(self, control_id, new_name):
        """Reload entire dropdown list, sort it, and select the renamed item without events"""
        if not hasattr(self, 'control_dropdown') or not self.control_dropdown:
            print("⚠️ No control dropdown reference available")
            return

        # Block signals to prevent events during rebuild
        self.control_dropdown.blockSignals(True)

        try:
            # Clear the dropdown
            self.control_dropdown.clear()

            # Get all fields from field manager
            if not hasattr(self, 'field_manager') or not self.field_manager:
                self.field_manager = self._get_field_manager()

            if not self.field_manager:
                self.control_dropdown.addItem("No controls available", None)
                return

            # Get all fields
            fields = []
            if hasattr(self.field_manager, 'get_all_fields'):
                fields = self.field_manager.get_all_fields()
            elif hasattr(self.field_manager, 'fields'):
                fields = self.field_manager.fields

            if not fields:
                self.control_dropdown.addItem("No controls available", None)
                return

            # Create list of (display_text, field_id) tuples for sorting
            dropdown_items = []
            for field in fields:
                try:
                    # Since control name and ID are the same, just use the name
                    field_name = getattr(field, 'name', getattr(field, 'id', 'unknown'))
                    dropdown_items.append((field_name, field.id))
                except Exception as e:
                    print(f"⚠️ Error processing field for dropdown: {e}")
                    continue

            # Sort by display text (field name)
            dropdown_items.sort(key=lambda x: x[0].lower())

            # Add sorted items to dropdown
            selected_index = -1
            for i, (display_text, field_id) in enumerate(dropdown_items):
                self.control_dropdown.addItem(display_text, field_id)

                # Track which index to select (the renamed field)
                if field_id == control_id:
                    selected_index = i

            # Set selection to the renamed item (without triggering events)
            if selected_index >= 0:
                self.control_dropdown.setCurrentIndex(selected_index)

            print(f"✅ Dropdown reloaded and sorted, selected: {new_name}")

        except Exception as e:
            print(f"❌ Error refreshing dropdown: {e}")

        finally:
            # Re-enable signals
            self.control_dropdown.blockSignals(False)