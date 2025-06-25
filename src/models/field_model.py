"""
Field Data Model
Defines the structure and operations for form fields
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import QRect
from click import clear


class FieldType(Enum):
    """Enumeration of supported field types"""
    TEXT = "text"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    SIGNATURE = "signature"
    DATE = "date"
    BUTTON = "button"
    NUMBER = "number",
    EMAIL = "email",
    LABEL = "label",
    FILE_UPLOAD = "file upload",
    PHONE= "phone",
    URL = "url",
    TEXTAREA = "textarea",
    PASSWORD = "password"





@dataclass
class FormField:
    """Data model for a form field"""
    id: str
    type: FieldType
    name: str
    x: int
    y: int
    width: int
    height: int
    page_number: int = 0
    required: bool = False
    value: Any = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, field_type: str, x: int, y: int, field_id: Optional[str] = None, page_number:int = 0) -> 'FormField':
        """Create a new form field with default dimensions"""
        if field_id is None:
            field_id = f"{field_type}_{id(cls)}"

        # Default sizes for different field types
        default_sizes = {
            FieldType.TEXT: (150, 25),
            FieldType.CHECKBOX: (20, 20),
            FieldType.DROPDOWN: (120, 25),
            FieldType.SIGNATURE: (200, 50),
            FieldType.DATE: (100, 25),
            FieldType.RADIO: (20, 20),
            FieldType.BUTTON: (80, 30),
            FieldType.NUMBER: (100, 25),
            FieldType.EMAIL: (200, 25),
            FieldType.LABEL: (100, 25)
        }

        field_type_enum = FieldType(field_type)
        width, height = default_sizes.get(field_type_enum, (100, 25))

        return cls(
            id=field_id,
            type=field_type_enum,
            name=field_id,
            x=x,
            y=y,
            width=width,
            height=height,
            page_number=page_number
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary for serialization"""
        return {
            'id': self.id,
            'type': self.type.value,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'page_number': self.page_number,
            'required': self.required,
            'value': self.value,
            'properties': self.properties.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormField':
        """Create field from dictionary"""
        return cls(
            id=data['id'],
            type=FieldType(data['type']),
            name=data['name'],
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            page_number=data.get('page_number', 0),
            required=data.get('required', False),
            value=data.get('value', ''),
            properties=data.get('properties', {})
        )

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within field bounds"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

    def move_to(self, x: int, y: int):
        """Move field to new position"""
        self.x = x
        self.y = y

    def resize_to(self, width: int, height: int):
        """Resize field to new dimensions"""
        self.width = max(10, width)  # Minimum width
        self.height = max(10, height)  # Minimum height

    def duplicate(self, offset_x: int = 20, offset_y: int = 20) -> 'FormField':
        """Create a duplicate of this field with offset"""
        new_field = FormField(
            id=f"{self.type.value}_{id(self)}",
            type=self.type,
            name=f"{self.name}_copy",
            x=self.x + offset_x,
            y=self.y + offset_y,
            width=self.width,
            height=self.height,
            required=self.required,
            value=self.value,
            properties=self.properties.copy()
        )
        return new_field

    def __hash__(self):
        """Make FormField hashable using its ID"""
        return hash(self.id)

    def __eq__(self, other):
        """Compare FormFields by ID"""
        if not isinstance(other, FormField):
            return False
        return self.id == other.id

    def get_screen_rect(self, zoom_level):
        """Get field rectangle in screen coordinates"""
        return QRect(
            int(self.x * zoom_level),
            int(self.y * zoom_level),
            int(self.width * zoom_level),
            int(self.height * zoom_level)
        )

class FieldManager:
    """Manages a collection of form fields"""

    def __init__(self):
        self.fields: List[FormField] = []
        self._field_counter = 0

    def add_field(self, field_type: str, x: int, y: int, page_number: int = 0) -> FormField:
        """Add a new field to the collection"""
        self._field_counter += 1
        field_id = f"{field_type}_{self._field_counter}"

        field = FormField.create(field_type, x, y, field_id, page_number)  # ← Add page_number
        self.fields.append(field)
        return field

    def remove_field(self, field: FormField) -> bool:
        """Remove a field from the collection"""
        if field in self.fields:
            self.fields.remove(field)
            return True
        return False

    def get_field_by_id(self, field_id: str) -> Optional[FormField]:
        """Get field by ID"""
        for field in self.fields:
            if field.id == field_id:
                return field
        return None

    def get_field_at_position(self, x: int, y: int, page_number: Optional[int] = None, tolerance: int = 2) -> Optional[
        FormField]:
        """Get the topmost field at given position with improved detection"""
        print(f"🔍 Checking for field at position ({x}, {y}) on page {page_number}")

        # Filter fields by page if specified
        if page_number is not None:
            fields_to_check = [f for f in self.fields if f.page_number == page_number]
            print(f"   Checking {len(fields_to_check)} fields on page {page_number}")
        else:
            fields_to_check = self.fields
            print(f"   Checking all {len(fields_to_check)} fields")

        # Check fields in reverse order (topmost first)
        for i, field in enumerate(reversed(fields_to_check)):
            try:
                # Add some tolerance for edge detection
                field_left = field.x - tolerance
                field_right = field.x + field.width + tolerance
                field_top = field.y - tolerance
                field_bottom = field.y + field.height + tolerance

                if (field_left <= x <= field_right and
                        field_top <= y <= field_bottom):
                    print(f"✅ Found field: {field.name} at ({field.x}, {field.y}) on page {field.page_number}")
                    return field
                else:
                    print(
                        f"   Field {field.name}: ({field.x}, {field.y}, {field.width}x{field.height}) on page {field.page_number} - no match")

            except Exception as e:
                print(f"⚠️ Error checking field {i}: {e}")
                continue

        print("   No field found at position")
        return None

    def duplicate_field(self, field: FormField) -> Optional[FormField]:
        """Duplicate a field"""
        if field in self.fields:
            new_field = field.duplicate()
            self.fields.append(new_field)
            return new_field
        return None

    def clear_all(self):
        """Remove all fields"""
        self.fields.clear()
        self._field_counter = 0

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert all fields to list of dictionaries"""
        return [field.to_dict() for field in self.fields]

    def from_dict_list(self, field_data: List[Dict[str, Any]]):
        """Load fields from list of dictionaries"""
        self.clear_all()
        for data in field_data:
            field = FormField.from_dict(data)
            self.fields.append(field)
            # Update counter to avoid ID conflicts
            if field.id.split('_')[-1].isdigit():
                counter = int(field.id.split('_')[-1])
                self._field_counter = max(self._field_counter, counter)

    def get_fields_for_page(self, page_number: int) -> List[FormField]:
        """Get all fields for a specific page"""
        return [field for field in self.fields if field.page_number == page_number]

    def get_field_count_for_page(self, page_number: int) -> int:
        """Get count of fields on a specific page"""
        return len(self.get_fields_for_page(page_number))

    def move_field_to_page(self, field: FormField, new_page: int) -> bool:
        """Move a field to a different page"""
        if field in self.fields:
            field.page_number = new_page
            return True
        return False

    def get_all_fields(self) -> List[FormField]:
        """Get all fields in the manager"""
        return self.fields.copy()

