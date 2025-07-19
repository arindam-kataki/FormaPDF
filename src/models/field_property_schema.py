# src/models/field_property_schema.py
"""
Field Property Schema System
Centralized definition of property groups and specific properties for each field type.
This replaces hardcoded property definitions in UI classes.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from models.field_model import FieldType


class PropertyWidgetType(Enum):
    """Types of property widgets available"""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    MULTILINE_TEXT = "multiline_text"
    COLOR = "color"
    SLIDER = "slider"
    FILE = "file"


@dataclass
class PropertyDefinition:
    """Definition of a single property"""
    name: str
    label: str
    widget_type: PropertyWidgetType
    default_value: Any
    description: Optional[str] = None

    # Widget-specific configuration
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    choices: Optional[List[str]] = None
    placeholder: Optional[str] = None
    tooltip: Optional[str] = None

    # Validation
    required: bool = False
    validation_pattern: Optional[str] = None
    validation_message: Optional[str] = None


@dataclass
class PropertyGroup:
    """A group of related properties"""
    name: str
    label: str
    description: Optional[str] = None
    properties: List[PropertyDefinition] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = []


class FieldPropertySchema:
    """Central schema defining all field types and their property groups"""

    def __init__(self):
        self._universal_groups = self._define_universal_groups()
        self._field_specific_groups = self._define_field_specific_groups()
        self._field_type_mappings = self._define_field_type_mappings()

    def _define_universal_groups(self) -> Dict[str, PropertyGroup]:
        """Define property groups that ALL field types get"""
        return {
            "basic": PropertyGroup(
                name="basic",
                label="Basic Properties",
                description="Core properties available for all field types",
                properties=[
                    PropertyDefinition(
                        name="name",
                        label="Field Name",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="Unique identifier for this field",
                        required=True,
                        placeholder="Enter field name",
                        tooltip="Must start with letter, contain only letters, numbers, underscores, and dashes"
                    ),
                    PropertyDefinition(
                        name="required",
                        label="Required Field",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Whether this field must be filled out",
                        tooltip="Check to make this field mandatory"
                    ),
                    PropertyDefinition(
                        name="tab_order",
                        label="Tab Order",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=0,
                        min_value=0,
                        max_value=999,
                        description="Order for keyboard navigation",
                        tooltip="0 = auto, higher numbers = later in tab sequence"
                    ),
                    PropertyDefinition(
                        name="readonly",
                        label="Read Only",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Prevent user input",
                        tooltip="Field will display value but not accept changes"
                    )
                ]
            ),

            "position_size": PropertyGroup(
                name="position_size",
                label="Position & Size",
                description="Location and dimensions of the field",
                properties=[
                    PropertyDefinition(
                        name="x",
                        label="X Position",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=0,
                        min_value=0,
                        max_value=2000,
                        description="Horizontal position in pixels"
                    ),
                    PropertyDefinition(
                        name="y",
                        label="Y Position",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=0,
                        min_value=0,
                        max_value=2000,
                        description="Vertical position in pixels"
                    ),
                    PropertyDefinition(
                        name="width",
                        label="Width",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=150,
                        min_value=10,
                        max_value=1000,
                        description="Field width in pixels"
                    ),
                    PropertyDefinition(
                        name="height",
                        label="Height",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=25,
                        min_value=10,
                        max_value=500,
                        description="Field height in pixels"
                    )
                ]
            ),

            "appearance": PropertyGroup(
                name="appearance",
                label="Appearance",
                description="Visual styling options",
                properties=[
                    PropertyDefinition(
                        name="font_family",
                        label="Font Family",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="Arial",
                        choices=["Arial", "Times New Roman", "Courier New", "Helvetica", "Georgia"],
                        description="Font typeface for text"
                    ),
                    PropertyDefinition(
                        name="font_size",
                        label="Font Size",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=12,
                        min_value=6,
                        max_value=72,
                        description="Text size in points"
                    ),
                    PropertyDefinition(
                        name="font_bold",
                        label="Bold",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Bold text styling"
                    ),
                    PropertyDefinition(
                        name="font_italic",
                        label="Italic",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Italic text styling"
                    ),
                    PropertyDefinition(
                        name="text_color",
                        label="Text Color",
                        widget_type=PropertyWidgetType.COLOR,
                        default_value="#000000",
                        description="Color of the text"
                    ),
                    PropertyDefinition(
                        name="background_color",
                        label="Background Color",
                        widget_type=PropertyWidgetType.COLOR,
                        default_value="#FFFFFF",
                        description="Background fill color"
                    ),
                    PropertyDefinition(
                        name="border_style",
                        label="Border Style",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="solid",
                        choices=["none", "solid", "dashed", "dotted"],
                        description="Border line style"
                    ),
                    PropertyDefinition(
                        name="border_color",
                        label="Border Color",
                        widget_type=PropertyWidgetType.COLOR,
                        default_value="#CCCCCC",
                        description="Color of the border"
                    )
                ]
            )
        }

    def _define_field_specific_groups(self) -> Dict[str, PropertyGroup]:
        """Define field-type-specific property groups"""
        return {
            "text_properties": PropertyGroup(
                name="text_properties",
                label="Text Properties",
                description="Properties specific to text input fields",
                properties=[
                    PropertyDefinition(
                        name="default_value",
                        label="Default Value",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="Pre-filled text value",
                        placeholder="Enter default text"
                    ),
                    PropertyDefinition(
                        name="placeholder",
                        label="Placeholder",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="Hint text shown when field is empty",
                        placeholder="Enter placeholder text"
                    ),
                    PropertyDefinition(
                        name="multiline",
                        label="Multiline Text",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Allow multiple lines of text"
                    ),
                    PropertyDefinition(
                        name="max_length",
                        label="Maximum Length",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=0,
                        min_value=0,
                        max_value=10000,
                        description="Maximum number of characters (0 = unlimited)"
                    )
                ]
            ),

            "textarea_properties": PropertyGroup(
                name="textarea_properties",
                label="Text Area Properties",
                description="Properties for multi-line text areas",
                properties=[
                    PropertyDefinition(
                        name="rows",
                        label="Number of Rows",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=3,
                        min_value=1,
                        max_value=20,
                        description="Visible text rows"
                    ),
                    PropertyDefinition(
                        name="enable_char_limit",
                        label="Enable Character Limit",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Restrict maximum characters"
                    ),
                    PropertyDefinition(
                        name="char_limit",
                        label="Character Limit",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=1000,
                        min_value=1,
                        max_value=50000,
                        description="Maximum characters allowed"
                    )
                ]
            ),

            "checkbox_properties": PropertyGroup(
                name="checkbox_properties",
                label="Checkbox Properties",
                description="Properties for checkbox fields",
                properties=[
                    PropertyDefinition(
                        name="checked_default",
                        label="Checked by Default",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Initial checked state"
                    ),
                    PropertyDefinition(
                        name="check_value",
                        label="Checked Value",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="Yes",
                        description="Value when checkbox is checked"
                    ),
                    PropertyDefinition(
                        name="uncheck_value",
                        label="Unchecked Value",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="No",
                        description="Value when checkbox is unchecked"
                    )
                ]
            ),

            "radio_properties": PropertyGroup(
                name="radio_properties",
                label="Radio Button Properties",
                description="Properties for radio button fields",
                properties=[
                    PropertyDefinition(
                        name="radio_group",
                        label="Radio Group",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="group1",
                        description="Group name for mutually exclusive selection",
                        placeholder="Enter group name"
                    ),
                    PropertyDefinition(
                        name="radio_value",
                        label="Radio Value",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="option1",
                        description="Value when this radio button is selected"
                    ),
                    PropertyDefinition(
                        name="selected_default",
                        label="Selected by Default",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Whether this option is pre-selected"
                    )
                ]
            ),

            "dropdown_properties": PropertyGroup(
                name="dropdown_properties",
                label="Dropdown Properties",
                description="Properties for dropdown selection fields",
                properties=[
                    PropertyDefinition(
                        name="option_format",
                        label="Option Format",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="Text Only",
                        choices=["Text Only", "Value | Text"],
                        description="Format for dropdown options"
                    ),
                    PropertyDefinition(
                        name="options",
                        label="Options",
                        widget_type=PropertyWidgetType.MULTILINE_TEXT,
                        default_value=["Option 1", "Option 2", "Option 3"],
                        description="List of available options (one per line)",
                        placeholder="Enter options, one per line"
                    ),
                    PropertyDefinition(
                        name="allow_custom",
                        label="Allow Custom Values",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Allow users to enter values not in list"
                    ),
                    PropertyDefinition(
                        name="default_selection",
                        label="Default Selection",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="Pre-selected option",
                        placeholder="Enter default option"
                    )
                ]
            ),

            "listbox_properties": PropertyGroup(
                name="listbox_properties",
                label="List Box Properties",
                description="Properties for list box selection fields",
                properties=[
                    PropertyDefinition(
                        name="selection_mode",
                        label="Selection Mode",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="Single Selection",
                        choices=["Single Selection", "Multiple Selection"],
                        description="Allow single or multiple selections"
                    ),
                    PropertyDefinition(
                        name="visible_rows",
                        label="Visible Rows",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=4,
                        min_value=1,
                        max_value=20,
                        description="Number of visible options"
                    ),
                    PropertyDefinition(
                        name="options",
                        label="Options",
                        widget_type=PropertyWidgetType.MULTILINE_TEXT,
                        default_value=["Option 1", "Option 2", "Option 3"],
                        description="List of available options"
                    )
                ]
            ),

            "number_properties": PropertyGroup(
                name="number_properties",
                label="Number Properties",
                description="Properties for numeric input fields",
                properties=[
                    PropertyDefinition(
                        name="min_value",
                        label="Minimum Value",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="Smallest allowed value",
                        placeholder="Enter minimum (optional)"
                    ),
                    PropertyDefinition(
                        name="max_value",
                        label="Maximum Value",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="Largest allowed value",
                        placeholder="Enter maximum (optional)"
                    ),
                    PropertyDefinition(
                        name="decimal_places",
                        label="Decimal Places",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=2,
                        min_value=0,
                        max_value=10,
                        description="Number of decimal places"
                    ),
                    PropertyDefinition(
                        name="allow_negative",
                        label="Allow Negative Numbers",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=True,
                        description="Permit negative values"
                    ),
                    PropertyDefinition(
                        name="number_format",
                        label="Number Format",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="Standard",
                        choices=["Standard", "Currency", "Percentage"],
                        description="Display format for numbers"
                    )
                ]
            ),

            "date_properties": PropertyGroup(
                name="date_properties",
                label="Date Properties",
                description="Properties for date input fields",
                properties=[
                    PropertyDefinition(
                        name="date_format",
                        label="Date Format",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="DD/MM/YYYY",
                        choices=["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD", "DD-MM-YYYY"],
                        description="Date display format"
                    ),
                    PropertyDefinition(
                        name="min_date",
                        label="Minimum Date",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="Earliest allowed date",
                        placeholder="YYYY-MM-DD"
                    ),
                    PropertyDefinition(
                        name="max_date",
                        label="Maximum Date",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="Latest allowed date",
                        placeholder="YYYY-MM-DD"
                    ),
                    PropertyDefinition(
                        name="default_date",
                        label="Default Date",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="None",
                        choices=["None", "Today", "Custom"],
                        description="Pre-filled date value"
                    )
                ]
            ),

            "email_properties": PropertyGroup(
                name="email_properties",
                label="Email Properties",
                description="Properties for email input fields",
                properties=[
                    PropertyDefinition(
                        name="validate_email",
                        label="Validate Email Format",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=True,
                        description="Check for valid email format"
                    ),
                    PropertyDefinition(
                        name="suggest_domains",
                        label="Suggest Common Domains",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=True,
                        description="Auto-suggest @gmail.com, @yahoo.com, etc."
                    )
                ]
            ),

            "phone_properties": PropertyGroup(
                name="phone_properties",
                label="Phone Properties",
                description="Properties for phone number fields",
                properties=[
                    PropertyDefinition(
                        name="phone_format",
                        label="Phone Format",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="(XXX) XXX-XXXX",
                        choices=["(XXX) XXX-XXXX", "XXX-XXX-XXXX", "+X XXX XXX XXXX", "XXX.XXX.XXXX"],
                        description="Phone number display format"
                    ),
                    PropertyDefinition(
                        name="auto_format",
                        label="Auto-Format Input",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=True,
                        description="Automatically format as user types"
                    )
                ]
            ),

            "url_properties": PropertyGroup(
                name="url_properties",
                label="URL Properties",
                description="Properties for URL input fields",
                properties=[
                    PropertyDefinition(
                        name="validate_url",
                        label="Validate URL Format",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=True,
                        description="Check for valid URL format"
                    ),
                    PropertyDefinition(
                        name="require_protocol",
                        label="Require Protocol",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Require http:// or https://"
                    )
                ]
            ),

            "password_properties": PropertyGroup(
                name="password_properties",
                label="Password Properties",
                description="Properties for password input fields",
                properties=[
                    PropertyDefinition(
                        name="show_toggle",
                        label="Show Password Toggle",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=True,
                        description="Include show/hide password button"
                    ),
                    PropertyDefinition(
                        name="min_length",
                        label="Minimum Length",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=0,
                        min_value=0,
                        max_value=100,
                        description="Minimum password length (0 = no limit)"
                    )
                ]
            ),

            "signature_properties": PropertyGroup(
                name="signature_properties",
                label="Signature Properties",
                description="Properties for digital signature fields",
                properties=[
                    PropertyDefinition(
                        name="line_color",
                        label="Signature Line Color",
                        widget_type=PropertyWidgetType.COLOR,
                        default_value="#000000",
                        description="Color of the signature line"
                    ),
                    PropertyDefinition(
                        name="clear_button",
                        label="Show Clear Button",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=True,
                        description="Include button to clear signature"
                    ),
                    PropertyDefinition(
                        name="require_signature",
                        label="Require Digital Signature",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Require cryptographic signature"
                    )
                ]
            ),

            "button_properties": PropertyGroup(
                name="button_properties",
                label="Button Properties",
                description="Properties for button fields",
                properties=[
                    PropertyDefinition(
                        name="button_text",
                        label="Button Text",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="Click",
                        description="Text displayed on button",
                        placeholder="Enter button text"
                    ),
                    PropertyDefinition(
                        name="action_type",
                        label="Action Type",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="Submit",
                        choices=["Submit", "Reset", "Custom", "Print", "Save"],
                        description="Button action when clicked"
                    ),
                    PropertyDefinition(
                        name="custom_action",
                        label="Custom Action",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="",
                        description="JavaScript code for custom action",
                        placeholder="Enter JavaScript code"
                    )
                ]
            ),

            "file_upload_properties": PropertyGroup(
                name="file_upload_properties",
                label="File Upload Properties",
                description="Properties for file upload fields",
                properties=[
                    PropertyDefinition(
                        name="accepted_types",
                        label="Accepted File Types",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="All Files",
                        choices=["PDF", "Images (PNG, JPG)", "Documents (DOC, DOCX)", "All Files"],
                        description="Restrict file types"
                    ),
                    PropertyDefinition(
                        name="max_size_mb",
                        label="Maximum File Size (MB)",
                        widget_type=PropertyWidgetType.NUMBER,
                        default_value=10,
                        min_value=1,
                        max_value=100,
                        description="Maximum file size in megabytes"
                    ),
                    PropertyDefinition(
                        name="multiple_files",
                        label="Allow Multiple Files",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=False,
                        description="Allow selecting multiple files"
                    )
                ]
            ),

            "label_properties": PropertyGroup(
                name="label_properties",
                label="Label Properties",
                description="Properties for text label fields",
                properties=[
                    PropertyDefinition(
                        name="label_text",
                        label="Label Text",
                        widget_type=PropertyWidgetType.TEXT,
                        default_value="Label",
                        description="Text content of the label",
                        placeholder="Enter label text"
                    ),
                    PropertyDefinition(
                        name="text_alignment",
                        label="Text Alignment",
                        widget_type=PropertyWidgetType.CHOICE,
                        default_value="Left",
                        choices=["Left", "Center", "Right"],
                        description="Horizontal text alignment"
                    ),
                    PropertyDefinition(
                        name="word_wrap",
                        label="Word Wrap",
                        widget_type=PropertyWidgetType.BOOLEAN,
                        default_value=True,
                        description="Allow text to wrap to multiple lines"
                    )
                ]
            )
        }

    def _define_field_type_mappings(self) -> Dict[FieldType, List[str]]:
        """Define which property groups each field type gets"""
        return {
            FieldType.TEXT: [
                "basic", "position_size", "appearance", "text_properties", "text_format"
            ],
            FieldType.TEXTAREA: [
                "basic", "position_size", "appearance", "textarea_properties"
            ],
            #FieldType.PASSWORD: [
            #    "basic", "position_size", "appearance", "password_properties"
            #],
            FieldType.CHECKBOX: [
                "basic", "position_size", "appearance", "checkbox_properties"
            ],
            FieldType.RADIO: [
                "basic", "position_size", "appearance", "radio_properties"
            ],
            FieldType.DROPDOWN: [
                "basic", "position_size", "appearance", "dropdown_properties"
            ],
            FieldType.LIST_BOX: [
                "basic", "position_size", "appearance", "listbox_properties"
            ],
            FieldType.NUMBER: [
                "basic", "position_size", "appearance", "number_properties"
            ],
            #FieldType.EMAIL: [
            #    "basic", "position_size", "appearance", "email_properties"
            #],
            #FieldType.PHONE: [
            #    "basic", "position_size", "appearance", "phone_properties"
            #],
            #FieldType.URL: [
            #    "basic", "position_size", "appearance", "url_properties"
            #],
            FieldType.DATE: [
                "basic", "position_size", "appearance", "date_properties"
            ],
            FieldType.SIGNATURE: [
                "basic", "position_size", "appearance", "signature_properties"
            ],
            FieldType.BUTTON: [
                "basic", "position_size", "appearance", "button_properties"
            ],
            FieldType.FILE_UPLOAD: [
                "basic", "position_size", "appearance", "file_upload_properties"
            ],
            FieldType.LABEL: [
                "basic", "position_size", "appearance", "label_properties"
            ]
        }

    # Public API Methods

    def get_property_groups_for_field_type(self, field_type: FieldType) -> List[PropertyGroup]:
        """Get all property groups for a specific field type"""
        group_names = self._field_type_mappings.get(field_type, [])
        groups = []

        for group_name in group_names:
            if group_name in self._universal_groups:
                groups.append(self._universal_groups[group_name])
            elif group_name in self._field_specific_groups:
                groups.append(self._field_specific_groups[group_name])

        return groups

    def get_property_group(self, group_name: str) -> Optional[PropertyGroup]:
        """Get a specific property group by name"""
        if group_name in self._universal_groups:
            return self._universal_groups[group_name]
        elif group_name in self._field_specific_groups:
            return self._field_specific_groups[group_name]
        return None

    def get_property_definition(self, group_name: str, property_name: str) -> Optional[PropertyDefinition]:
        """Get a specific property definition"""
        group = self.get_property_group(group_name)
        if group:
            for prop in group.properties:
                if prop.name == property_name:
                    return prop
        return None

    def get_all_properties_for_field_type(self, field_type: FieldType) -> List[PropertyDefinition]:
        """Get all properties for a field type (flattened from all groups)"""
        groups = self.get_property_groups_for_field_type(field_type)
        all_properties = []

        for group in groups:
            all_properties.extend(group.properties)

        return all_properties

    def get_default_properties_dict(self, field_type: FieldType) -> Dict[str, Any]:
        """Get default property values as a dictionary for a field type"""
        properties = self.get_all_properties_for_field_type(field_type)
        return {prop.name: prop.default_value for prop in properties}

    def validate_property_value(self, field_type: FieldType, property_name: str, value: Any) -> tuple[bool, str]:
        """Validate a property value against its definition"""
        properties = self.get_all_properties_for_field_type(field_type)

        for prop in properties:
            if prop.name == property_name:
                # Basic type checking
                if prop.widget_type == PropertyWidgetType.NUMBER:
                    try:
                        num_value = float(value) if value != "" else 0
                        if prop.min_value is not None and num_value < prop.min_value:
                            return False, f"Value must be at least {prop.min_value}"
                        if prop.max_value is not None and num_value > prop.max_value:
                            return False, f"Value must be no more than {prop.max_value}"
                    except (ValueError, TypeError):
                        return False, "Value must be a number"

                elif prop.widget_type == PropertyWidgetType.CHOICE:
                    if prop.choices and value not in prop.choices:
                        return False, f"Value must be one of: {', '.join(prop.choices)}"

                elif prop.required and (value is None or value == ""):
                    return False, f"{prop.label} is required"

                return True, "Valid"

        return False, f"Unknown property: {property_name}"


# Global schema instance
FIELD_PROPERTY_SCHEMA = FieldPropertySchema()


# Convenience functions for easy access
def get_property_groups(field_type: FieldType) -> List[PropertyGroup]:
    """Get property groups for a field type"""
    return FIELD_PROPERTY_SCHEMA.get_property_groups_for_field_type(field_type)


def get_default_properties(field_type: FieldType) -> Dict[str, Any]:
    """Get default property values for a field type"""
    return FIELD_PROPERTY_SCHEMA.get_default_properties_dict(field_type)


def validate_property(field_type: FieldType, property_name: str, value: Any) -> tuple[bool, str]:
    """Validate a property value"""
    return FIELD_PROPERTY_SCHEMA.validate_property_value(field_type, property_name, value)


# Example usage:
if __name__ == "__main__":
    # Example: Get all property groups for a text field
    text_groups = get_property_groups(FieldType.TEXT)
    print(f"Text field has {len(text_groups)} property groups:")
    for group in text_groups:
        print(f"  - {group.label} ({len(group.properties)} properties)")

    # Example: Get default properties for a dropdown
    dropdown_defaults = get_default_properties(FieldType.DROPDOWN)
    print(f"\nDropdown default properties: {dropdown_defaults}")

    # Example: Validate a property value
    is_valid, message = validate_property(FieldType.NUMBER, "min_value", "abc")
    print(f"\nValidation result: {is_valid}, {message}")