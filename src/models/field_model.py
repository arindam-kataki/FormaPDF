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


"""
Enhanced FieldManager class with centralized field management using lists
Handles all field creation, deletion, and selection operations
"""

from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

class FieldManager(QObject):
    """Central authority for all field management operations"""

    # Signals for field events
    field_added = pyqtSignal(object)  # FormField
    field_removed = pyqtSignal(str)  # field_id
    fields_cleared = pyqtSignal()
    selection_changed = pyqtSignal(list)  # list of selected fields

    def __init__(self):
        super().__init__()
        # Master list of all created fields
        self.all_fields: List[FormField] = []

        # List of currently selected fields (supports multi-selection)
        self.selected_fields: List[FormField] = []

        # Field counter for generating unique IDs
        self._field_counter = 0

        print("✅ FieldManager initialized with list-based field management")

    # ==========================================
    # FIELD CREATION AND DELETION
    # ==========================================

    def create_field(self, field_type: str, x: int, y: int, page_num: int = 0, **kwargs) -> FormField:
        """
        Create a new field and add it to the master list

        Args:
            field_type: Type of field to create (text, signature, checkbox, etc.)
            x, y: Position coordinates
            page_num: PDF page number
            **kwargs: Additional field properties

        Returns:
            Created FormField instance
        """
        try:
            # Generate unique field ID
            self._field_counter += 1
            field_id = f"{field_type}_{self._field_counter}"

            # Map string types to FieldType enum if needed
            field_type_enum = self._get_field_type_enum(field_type)

            # Create the field
            field = FormField.create(field_type_enum, x, y, field_id, page_num=page_num, **kwargs)

            # Add to master list
            self.all_fields.append(field)

            # Emit signal
            self.field_added.emit(field)

            print(f"✅ Created field: {field_id} at ({x}, {y}) on page {page_num}")
            return field

        except Exception as e:
            print(f"❌ Error creating field: {e}")
            raise

    def add_field(self, field: FormField) -> bool:
        """
        Add an existing field to the manager

        Args:
            field: FormField instance to add

        Returns:
            True if successful, False otherwise
        """
        try:
            if field not in self.all_fields:
                self.all_fields.append(field)
                self.field_added.emit(field)
                print(f"✅ Added existing field: {field.id}")
                return True
            else:
                print(f"⚠️ Field already exists: {field.id}")
                return False

        except Exception as e:
            print(f"❌ Error adding field: {e}")
            return False

    def remove_field(self, field_or_id) -> bool:
        """
        Remove a field from all lists

        Args:
            field_or_id: FormField instance or field ID string

        Returns:
            True if successful, False otherwise
        """
        try:
            field_to_remove = None

            # Handle both field object and field ID
            if isinstance(field_or_id, str):
                field_to_remove = self.get_field_by_id(field_or_id)
                field_id = field_or_id
            else:
                field_to_remove = field_or_id
                field_id = getattr(field_to_remove, 'id', 'unknown')

            if not field_to_remove:
                print(f"⚠️ Field not found for removal: {field_or_id}")
                return False

            # Remove from all fields list
            if field_to_remove in self.all_fields:
                self.all_fields.remove(field_to_remove)
                print(f"✅ Removed field from all_fields: {field_id}")

            # Remove from selected fields list if present
            if field_to_remove in self.selected_fields:
                self.selected_fields.remove(field_to_remove)
                self.selection_changed.emit(self.selected_fields.copy())
                print(f"✅ Removed field from selected_fields: {field_id}")

            # Emit removal signal
            self.field_removed.emit(field_id)

            return True

        except Exception as e:
            print(f"❌ Error removing field: {e}")
            return False

    def clear_all_fields(self):
        """Remove all fields from the manager"""
        try:
            self.all_fields.clear()
            self.selected_fields.clear()
            self._field_counter = 0

            self.fields_cleared.emit()
            self.selection_changed.emit([])

            print("✅ Cleared all fields")

        except Exception as e:
            print(f"❌ Error clearing fields: {e}")

    # ==========================================
    # FIELD SELECTION MANAGEMENT
    # ==========================================

    def select_field(self, field: Optional[FormField], multi_select: bool = False):
        """
        Select a field (or clear selection if None)

        Args:
            field: FormField to select, or None to clear selection
            multi_select: Whether to add to existing selection or replace it
        """
        try:
            if field is None:
                # Clear selection
                self.selected_fields.clear()
                print("✅ Cleared field selection")
            elif multi_select:
                # Add to selection if not already selected
                if field not in self.selected_fields:
                    self.selected_fields.append(field)
                    print(f"✅ Added field to selection: {field.id}")
                else:
                    # Remove from selection if already selected (toggle behavior)
                    self.selected_fields.remove(field)
                    print(f"✅ Removed field from selection: {field.id}")
            else:
                # Replace entire selection
                self.selected_fields = [field]
                print(f"✅ Selected field: {field.id}")

            # Emit selection change signal
            self.selection_changed.emit(self.selected_fields.copy())

        except Exception as e:
            print(f"❌ Error selecting field: {e}")

    def select_fields_by_ids(self, field_ids: List[str]):
        """Select multiple fields by their IDs"""
        try:
            fields_to_select = []
            for field_id in field_ids:
                field = self.get_field_by_id(field_id)
                if field:
                    fields_to_select.append(field)

            self.selected_fields = fields_to_select
            self.selection_changed.emit(self.selected_fields.copy())

            print(f"✅ Selected {len(fields_to_select)} fields by ID")

        except Exception as e:
            print(f"❌ Error selecting fields by ID: {e}")

    def select_field_at_position(self, x: int, y: int, page_num: int = 0, multi_select: bool = False,
                                 zoom_level: float = 1.0, coordinate_type: str = "document") -> Optional[FormField]:
        """
        Select field at given position (zoom-aware)

        Args:
            x, y: Position coordinates
            page_num: PDF page number
            multi_select: Whether to add to existing selection
            zoom_level: Current zoom level for coordinate conversion
            coordinate_type: "document" or "screen" coordinates

        Returns:
            Selected field or None
        """
        try:
            field = self.get_field_at_position(x, y, page_num, zoom_level=zoom_level, coordinate_type=coordinate_type)
            if field:
                self.select_field(field, multi_select)
            return field

        except Exception as e:
            print(f"❌ Error selecting field at position: {e}")
            return None

    def toggle_field_selection(self, field: FormField):
        """Toggle field selection state"""
        try:
            if field in self.selected_fields:
                self.selected_fields.remove(field)
                print(f"✅ Deselected field: {field.id}")
            else:
                self.selected_fields.append(field)
                print(f"✅ Selected field: {field.id}")

            self.selection_changed.emit(self.selected_fields.copy())

        except Exception as e:
            print(f"❌ Error toggling field selection: {e}")

    def clear_selection(self):
        """Clear all selected fields"""
        self.select_field(None)

    # ==========================================
    # FIELD RETRIEVAL AND QUERIES
    # ==========================================

    def get_all_fields(self) -> List[FormField]:
        """Get all fields in the manager"""
        return self.all_fields.copy()

    def get_selected_fields(self) -> List[FormField]:
        """Get currently selected fields"""
        return self.selected_fields.copy()

    def get_selected_field(self) -> Optional[FormField]:
        """Get the first selected field (for single-selection compatibility)"""
        return self.selected_fields[0] if self.selected_fields else None

    def get_field_by_id(self, field_id: str) -> Optional[FormField]:
        """Find field by ID"""
        try:
            for field in self.all_fields:
                if getattr(field, 'id', None) == field_id:
                    return field
            return None
        except Exception as e:
            print(f"❌ Error finding field by ID: {e}")
            return None

    def get_field_at_position(self, x: int, y: int, page_num: int = 0, tolerance: int = 5, zoom_level: float = 1.0,
                              coordinate_type: str = "document") -> Optional[FormField]:
        """
        Find field at given position with tolerance (zoom-aware)

        Args:
            x, y: Position coordinates
            page_num: PDF page number
            tolerance: Pixel tolerance for position matching
            zoom_level: Current zoom level for coordinate conversion
            coordinate_type: "document" or "screen" coordinates

        Returns:
            Field at position or None
        """
        try:
            # Convert screen coordinates to document coordinates if needed
            if coordinate_type == "screen":
                doc_x = x / zoom_level
                doc_y = y / zoom_level
                # Scale tolerance for zoom level
                doc_tolerance = tolerance / zoom_level
            else:
                doc_x = x
                doc_y = y
                doc_tolerance = tolerance

            for field in self.all_fields:
                # Check if field is on the right page
                field_page = getattr(field, 'page_num', getattr(field, 'page_number', 0))
                if field_page != page_num:
                    continue

                # Get field bounds in document coordinates
                field_x = getattr(field, 'x', 0)
                field_y = getattr(field, 'y', 0)
                field_width = getattr(field, 'width', 100)
                field_height = getattr(field, 'height', 30)

                # Check if position is within field bounds (with zoom-aware tolerance)
                if (field_x - doc_tolerance <= doc_x <= field_x + field_width + doc_tolerance and
                        field_y - doc_tolerance <= doc_y <= field_y + field_height + doc_tolerance):
                    return field

            return None

        except Exception as e:
            print(f"❌ Error finding field at position: {e}")
            return None

    def get_fields_by_type(self, field_type: str) -> List[FormField]:
        """Get all fields of a specific type"""
        try:
            matching_fields = []
            for field in self.all_fields:
                field_type_str = str(getattr(field, 'field_type', '')).lower()
                if field_type_str == field_type.lower():
                    matching_fields.append(field)
            return matching_fields

        except Exception as e:
            print(f"❌ Error getting fields by type: {e}")
            return []

    def get_fields_in_screen_area(self, screen_rect, page_num: int = 0, zoom_level: float = 1.0) -> List[FormField]:
        """
        Get all fields within a screen area (zoom-aware)

        Args:
            screen_rect: QRect in screen coordinates
            page_num: PDF page number
            zoom_level: Current zoom level

        Returns:
            List of fields in the area
        """
        try:
            # Convert screen rect to document coordinates
            doc_x = screen_rect.x() / zoom_level
            doc_y = screen_rect.y() / zoom_level
            doc_width = screen_rect.width() / zoom_level
            doc_height = screen_rect.height() / zoom_level

            matching_fields = []
            for field in self.all_fields:
                # Check if field is on the right page
                field_page = getattr(field, 'page_num', getattr(field, 'page_number', 0))
                if field_page != page_num:
                    continue

                # Get field bounds in document coordinates
                field_x = getattr(field, 'x', 0)
                field_y = getattr(field, 'y', 0)
                field_width = getattr(field, 'width', 100)
                field_height = getattr(field, 'height', 30)

                # Check if field intersects with the area
                if (field_x < doc_x + doc_width and field_x + field_width > doc_x and
                        field_y < doc_y + doc_height and field_y + field_height > doc_y):
                    matching_fields.append(field)

            return matching_fields

        except Exception as e:
            print(f"❌ Error getting fields in screen area: {e}")
            return []

    def get_fields_on_page(self, page_num: int) -> List[FormField]:
        """Get all fields on a specific page"""
        try:
            page_fields = []
            for field in self.all_fields:
                field_page = getattr(field, 'page_num', getattr(field, 'page_number', 0))
                if field_page == page_num:
                    page_fields.append(field)
            return page_fields

        except Exception as e:
            print(f"❌ Error getting fields on page: {e}")
            return []

    def convert_field_to_screen_bounds(self, field: FormField, zoom_level: float = 1.0) -> dict:
        """
        Convert field document coordinates to screen bounds (zoom-aware)

        Args:
            field: FormField to convert
            zoom_level: Current zoom level

        Returns:
            Dict with screen coordinates: {x, y, width, height}
        """
        try:
            doc_x = getattr(field, 'x', 0)
            doc_y = getattr(field, 'y', 0)
            doc_width = getattr(field, 'width', 100)
            doc_height = getattr(field, 'height', 30)

            return {
                'x': int(doc_x * zoom_level),
                'y': int(doc_y * zoom_level),
                'width': int(doc_width * zoom_level),
                'height': int(doc_height * zoom_level)
            }

        except Exception as e:
            print(f"❌ Error converting field to screen bounds: {e}")
            return {'x': 0, 'y': 0, 'width': 100, 'height': 30}

    def get_field_count(self) -> int:
        """Get total number of fields"""
        return len(self.all_fields)

    def get_selected_count(self) -> int:
        """Get number of selected fields"""
        return len(self.selected_fields)

    def has_fields(self) -> bool:
        """Check if any fields exist"""
        return len(self.all_fields) > 0

    def has_selection(self) -> bool:
        """Check if any fields are selected"""
        return len(self.selected_fields) > 0

    def duplicate_field(self, field: FormField, offset_x: int = 20, offset_y: int = 20) -> Optional[FormField]:
        """
        Duplicate a field with position offset

        Args:
            field: Field to duplicate
            offset_x, offset_y: Position offset for the duplicate

        Returns:
            Duplicated field or None
        """
        try:
            # Get field properties
            field_type = getattr(field, 'field_type', FieldType.TEXT)
            x = getattr(field, 'x', 0) + offset_x
            y = getattr(field, 'y', 0) + offset_y
            page_num = getattr(field, 'page_num', 0)

            # Copy properties
            properties = getattr(field, 'properties', {}).copy()

            # Create duplicate
            duplicate = self.create_field(
                field_type=str(field_type).split('.')[-1].lower(),
                x=x, y=y, page_num=page_num,
                **properties
            )

            print(f"✅ Duplicated field: {field.id} -> {duplicate.id}")
            return duplicate

        except Exception as e:
            print(f"❌ Error duplicating field: {e}")
            return None

    def _get_field_type_enum(self, field_type: str) -> FieldType:
        """Convert string field type to FieldType enum"""
        type_mapping = {
            'text': FieldType.TEXT,
            'signature': FieldType.SIGNATURE,
            'checkbox': FieldType.CHECKBOX,
            'radio': FieldType.RADIO,
            'dropdown': FieldType.DROPDOWN,
            'date': FieldType.DATE,
            'number': FieldType.NUMBER
        }

        return type_mapping.get(field_type.lower(), FieldType.TEXT)

    def get_field_summary(self) -> Dict[str, Any]:
        """Get summary information about all fields"""
        try:
            summary = {
                'total_fields': len(self.all_fields),
                'selected_fields': len(self.selected_fields),
                'fields_by_type': {},
                'fields_by_page': {}
            }

            # Count by type
            for field in self.all_fields:
                field_type = str(getattr(field, 'field_type', 'unknown'))
                summary['fields_by_type'][field_type] = summary['fields_by_type'].get(field_type, 0) + 1

            # Count by page
            for field in self.all_fields:
                page_num = getattr(field, 'page_num', 0)
                summary['fields_by_page'][f'page_{page_num}'] = summary['fields_by_page'].get(f'page_{page_num}', 0) + 1

            return summary

        except Exception as e:
            print(f"❌ Error generating field summary: {e}")
            return {'total_fields': 0, 'selected_fields': 0, 'fields_by_type': {}, 'fields_by_page': {}}

    def __str__(self) -> str:
        """String representation of the field manager"""
        return f"FieldManager(fields={len(self.all_fields)}, selected={len(self.selected_fields)})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"FieldManager(all_fields={len(self.all_fields)}, "
                f"selected_fields={len(self.selected_fields)}, "
                f"field_counter={self._field_counter})")


# Legacy compatibility properties (deprecated - use lists instead)
@property
def fields(self):
    """Legacy compatibility - use all_fields instead"""
    print("⚠️ DEPRECATED: Use all_fields instead of fields")
    return self.all_fields


@property
def selected_field(self):
    """Legacy compatibility - use get_selected_field() instead"""
    print("⚠️ DEPRECATED: Use get_selected_field() instead of selected_field")
    return self.get_selected_field()


# Add deprecated properties to class
FieldManager.fields = fields
FieldManager.selected_field = selected_field


class deprecated_FieldManager:
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
