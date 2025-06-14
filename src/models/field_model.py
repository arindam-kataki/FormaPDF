"""
Field Data Model
Defines the structure and operations for form fields
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class FieldType(Enum):
    """Enumeration of supported field types"""
    TEXT = "text"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    SIGNATURE = "signature"
    DATE = "date"
    BUTTON = "button"


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
    required: bool = False
    value: Any = ""
    properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, field_type: str, x: int, y: int, field_id: Optional[str] = None) -> 'FormField':
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
            FieldType.BUTTON: (80, 30)
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
            height=height
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


class FieldManager:
    """Manages a collection of form fields"""

    def __init__(self):
        self.fields: List[FormField] = []
        self._field_counter = 0

    def add_field(self, field_type: str, x: int, y: int) -> FormField:
        """Add a new field to the collection"""
        self._field_counter += 1
        field_id = f"{field_type}_{self._field_counter}"

        field = FormField.create(field_type, x, y, field_id)
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

    def get_field_at_position(self, x: int, y: int) -> Optional[FormField]:
        """Get the topmost field at given position"""
        # Check fields in reverse order (topmost first)
        for field in reversed(self.fields):
            if field.contains_point(x, y):
                return field
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