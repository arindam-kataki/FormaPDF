# src/ui/text_format_widget.py
"""
Text Field Format Widget for FormaPDF
Matches properties panel styling - no nested groups, consistent label/control layout
Fixed individual settings storage/restoration
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QTextEdit
)

from models.field_model import FieldType


class TextFormatWidget(QWidget):
    """Widget for configuring text field formatting options"""

    formatChanged = pyqtSignal(dict)  # Emits format configuration

    # Format categories (simplified)
    FORMAT_CATEGORIES = {
        'None': 'None',
        'Number': 'Number',
        'Percentage': 'Percentage',
        'Date': 'Date',
        'Time': 'Time',
        'Special': 'Special',
        'Custom': 'Custom'
    }

    # International number separator styles (simplified labels)
    SEPARATOR_STYLES = {
        'comma_dot': {
            'label': '1,234.56',
            'thousands': ',',
            'decimal': '.'
        },
        'dot_comma': {
            'label': '1.234,56',
            'thousands': '.',
            'decimal': ','
        },
        'space_comma': {
            'label': '1 234,56',
            'thousands': ' ',
            'decimal': ','
        },
        'space_dot': {
            'label': '1 234.56',
            'thousands': ' ',
            'decimal': '.'
        },
        'dot_only': {
            'label': '1234.56',
            'thousands': '',
            'decimal': '.'
        },
        'comma_only': {
            'label': '1234,56',
            'thousands': '',
            'decimal': ','
        }
    }

    # Special format patterns
    SPECIAL_PATTERNS = {
        'phone_us': {'mask': '(999) 999-9999', 'sample': '(555) 123-4567'},
        'phone_intl': {'mask': '+9 999 999 9999', 'sample': '+1 555 123 4567'},
        'ssn': {'mask': '999-99-9999', 'sample': '123-45-6789'},
        'zip_us': {'mask': '99999', 'sample': '12345'},
        'zip_plus4': {'mask': '99999-9999', 'sample': '12345-6789'},
        'credit_card': {'mask': '9999 9999 9999 9999', 'sample': '1234 5678 9012 3456'},
        'isbn': {'mask': '999-9-999-99999-9', 'sample': '978-0-123-45678-9'},
        'custom_mask': {'mask': '', 'sample': 'Custom pattern...'}
    }

    # Date format options
    DATE_FORMATS = [
        'MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD', 'DD-MM-YYYY',
        'MMM DD, YYYY', 'DD MMM YYYY', 'YYYY/MM/DD', 'MM-DD-YYYY'
    ]

    # Time format options
    TIME_FORMATS = [
        'HH:MM', 'HH:MM:SS', 'H:MM AM/PM', 'H:MM:SS AM/PM'
    ]

    def __init__(self, initial_format: Dict[str, Any] = None):
        super().__init__()

        # Current format configuration
        self.format_config = initial_format or {
            'category': 'None',
            'settings': {}
        }

        # UI components
        self.category_combo = None
        self.options_layout = None
        self.preview_label = None
        self._loading_config = False  # Flag to prevent unwanted updates during load

        self.init_ui()
        self.load_format_config(self.format_config)

    def init_ui(self):
        """Initialize the user interface to match properties panel style"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to match other groups

        # Create format selection (label + dropdown on same line)
        self.create_format_selection(layout)

        # Options container (no scrollable area, just direct layout)
        options_widget = QWidget()
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(8)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        options_widget.setLayout(self.options_layout)

        layout.addWidget(options_widget)

        # Preview section (simplified)
        self.create_preview_section(layout)

        self.setLayout(layout)

    def create_format_selection(self, parent_layout):
        """Create format category selection - label + dropdown style"""
        # Create horizontal layout for label + dropdown
        format_layout = QHBoxLayout()
        format_layout.setSpacing(8)

        # Label (same width as other property labels)
        format_label = QLabel("Format:")
        format_label.setFixedWidth(80)  # Match other property labels
        format_layout.addWidget(format_label)

        # Dropdown (simplified - just category names)
        self.category_combo = QComboBox()
        self.category_combo.setMaximumWidth(120)  # Match other dropdowns

        for category in self.FORMAT_CATEGORIES.keys():
            self.category_combo.addItem(category, category)  # Just the name, no description

        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        format_layout.addWidget(self.category_combo)

        # Add stretch to push everything left
        format_layout.addStretch()

        parent_layout.addLayout(format_layout)

    def create_preview_section(self, parent_layout):
        """Create simplified preview section"""
        # Preview label (same style as other property labels)
        preview_label = QLabel("Preview:")
        preview_label.setFixedWidth(80)

        # Preview value (simplified)
        self.preview_label = QLabel("Sample text")
        self.preview_label.setStyleSheet(
            "background-color: #f5f5f5; border: 1px solid #ccc; "
            "padding: 4px; font-family: 'Courier New', monospace; font-size: 11px;"
        )
        self.preview_label.setMinimumHeight(25)

        # Horizontal layout for preview
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(8)
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.preview_label)
        preview_layout.addStretch()

        parent_layout.addLayout(preview_layout)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Safely get a setting value"""
        return self.format_config.get('settings', {}).get(key, default)

    def on_category_changed(self):
        """Handle format category change"""
        if self._loading_config:  # Skip during initial load
            return

        category = self.category_combo.currentData()
        if category:
            # Only reset settings if category actually changed
            old_category = self.format_config.get('category', 'None')
            self.format_config['category'] = category

            # Only clear settings if category changed (not on initial load)
            if old_category != category:
                self.format_config['settings'] = {}

            self.update_options_ui()
            self.update_preview()
            self.formatChanged.emit(self.format_config)

    def update_options_ui(self):
        """Update options UI to match properties panel style"""
        category = self.format_config.get('category', 'None')

        # Clear existing options
        self.clear_layout(self.options_layout)

        # Add category-specific options with property panel styling
        if category == 'Number':
            self.create_number_options_simple()
        elif category == 'Percentage':
            self.create_percentage_options_simple()
        elif category == 'Date':
            self.create_date_options_simple()
        elif category == 'Time':
            self.create_time_options_simple()
        elif category == 'Special':
            self.create_special_options_simple()
        elif category == 'Custom':
            self.create_custom_options_simple()
        # None category shows no additional options

    def create_number_options_simple(self):
        """Create simplified number formatting options"""

        # Separator style
        separator_combo = self.create_separator_combo()
        self.add_property_row("Separator:", separator_combo)

        # Decimal places
        decimal_spin = QSpinBox()
        decimal_spin.setRange(0, 10)
        decimal_spin.setValue(self.get_setting('decimal_places', 2))
        decimal_spin.setMaximumWidth(60)
        decimal_spin.valueChanged.connect(lambda v: self.update_setting('decimal_places', v))
        self.add_property_row("Decimal Places:", decimal_spin)

        # Currency symbol
        currency_edit = QLineEdit()
        currency_edit.setMaximumWidth(80)
        currency_edit.setPlaceholderText("$, €, ¥")
        currency_edit.setText(self.get_setting('currency_symbol', ''))
        currency_edit.textChanged.connect(lambda t: self.update_setting('currency_symbol', t))
        self.add_property_row("Currency:", currency_edit)

        # Negative style
        negative_combo = QComboBox()
        negative_combo.setMaximumWidth(120)
        negative_options = ['Minus', 'Red', 'Parentheses', 'Red Parentheses']
        negative_combo.addItems(negative_options)

        # Set current value
        current_negative = self.get_setting('negative_style', 'minus')
        # Convert stored value back to display format
        display_negative = current_negative.replace('_', ' ').title()
        if display_negative in negative_options:
            negative_combo.setCurrentText(display_negative)

        negative_combo.currentTextChanged.connect(
            lambda t: self.update_setting('negative_style', t.lower().replace(' ', '_')))
        self.add_property_row("Negative:", negative_combo)

    def create_percentage_options_simple(self):
        """Create simplified percentage formatting options"""

        # Separator style
        separator_combo = self.create_separator_combo()
        self.add_property_row("Separator:", separator_combo)

        # Decimal places
        decimal_spin = QSpinBox()
        decimal_spin.setRange(0, 10)
        decimal_spin.setValue(self.get_setting('decimal_places', 2))
        decimal_spin.setMaximumWidth(60)
        decimal_spin.valueChanged.connect(lambda v: self.update_setting('decimal_places', v))
        self.add_property_row("Decimal Places:", decimal_spin)

        # Multiply by 100 checkbox
        multiply_check = QCheckBox("Multiply by 100")
        multiply_check.setChecked(self.get_setting('multiply_by_100', True))
        multiply_check.toggled.connect(lambda checked: self.update_setting('multiply_by_100', checked))
        self.options_layout.addWidget(multiply_check)

        # Space before % checkbox
        space_check = QCheckBox("Space before %")
        space_check.setChecked(self.get_setting('space_before_percent', False))
        space_check.toggled.connect(lambda checked: self.update_setting('space_before_percent', checked))
        self.options_layout.addWidget(space_check)

    def create_date_options_simple(self):
        """Create simplified date formatting options"""

        # Date format
        format_combo = QComboBox()
        format_combo.setMaximumWidth(140)
        format_combo.addItems(self.DATE_FORMATS)

        # Set current value
        current_format = self.get_setting('date_format', 'MM/DD/YYYY')
        if current_format in self.DATE_FORMATS:
            format_combo.setCurrentText(current_format)

        format_combo.currentTextChanged.connect(lambda t: self.update_setting('date_format', t))
        self.add_property_row("Format:", format_combo)

        # Validate checkbox
        validate_check = QCheckBox("Validate input")
        validate_check.setChecked(self.get_setting('validate_date', True))
        validate_check.toggled.connect(lambda checked: self.update_setting('validate_date', checked))
        self.options_layout.addWidget(validate_check)

        # Date range inputs
        min_date_edit = QLineEdit()
        min_date_edit.setMaximumWidth(100)
        min_date_edit.setPlaceholderText("YYYY-MM-DD")
        min_date_edit.setText(self.get_setting('min_date', ''))
        min_date_edit.textChanged.connect(lambda t: self.update_setting('min_date', t))
        self.add_property_row("Min Date:", min_date_edit)

        max_date_edit = QLineEdit()
        max_date_edit.setMaximumWidth(100)
        max_date_edit.setPlaceholderText("YYYY-MM-DD")
        max_date_edit.setText(self.get_setting('max_date', ''))
        max_date_edit.textChanged.connect(lambda t: self.update_setting('max_date', t))
        self.add_property_row("Max Date:", max_date_edit)

    def create_time_options_simple(self):
        """Create simplified time formatting options"""

        # Time format
        format_combo = QComboBox()
        format_combo.setMaximumWidth(120)
        format_combo.addItems(self.TIME_FORMATS)

        # Set current value
        current_format = self.get_setting('time_format', 'HH:MM')
        if current_format in self.TIME_FORMATS:
            format_combo.setCurrentText(current_format)

        format_combo.currentTextChanged.connect(lambda t: self.update_setting('time_format', t))
        self.add_property_row("Format:", format_combo)

        # 24 hour checkbox
        hour24_check = QCheckBox("24 Hour Format")
        hour24_check.setChecked(self.get_setting('hour24_format', True))
        hour24_check.toggled.connect(lambda checked: self.update_setting('hour24_format', checked))
        self.options_layout.addWidget(hour24_check)

        # Show seconds checkbox
        seconds_check = QCheckBox("Show Seconds")
        seconds_check.setChecked(self.get_setting('show_seconds', False))
        seconds_check.toggled.connect(lambda checked: self.update_setting('show_seconds', checked))
        self.options_layout.addWidget(seconds_check)

        # Validate checkbox
        validate_check = QCheckBox("Validate input")
        validate_check.setChecked(self.get_setting('validate_time', True))
        validate_check.toggled.connect(lambda checked: self.update_setting('validate_time', checked))
        self.options_layout.addWidget(validate_check)

    def create_special_options_simple(self):
        """Create simplified special formatting options"""

        # Pattern selection
        pattern_combo = QComboBox()
        pattern_combo.setMaximumWidth(150)

        for key in self.SPECIAL_PATTERNS.keys():
            display_name = key.replace('_', ' ').title()
            pattern_combo.addItem(display_name, key)

        # Set current value
        current_pattern = self.get_setting('pattern', 'phone_us')
        for i in range(pattern_combo.count()):
            if pattern_combo.itemData(i) == current_pattern:
                pattern_combo.setCurrentIndex(i)
                break

        pattern_combo.currentTextChanged.connect(lambda: self.update_setting('pattern', pattern_combo.currentData()))
        self.add_property_row("Pattern:", pattern_combo)

        # Custom mask (for custom patterns)
        mask_edit = QLineEdit()
        mask_edit.setMaximumWidth(120)
        mask_edit.setPlaceholderText("(999) 999-9999")
        mask_edit.setText(self.get_setting('custom_mask', ''))
        mask_edit.textChanged.connect(lambda t: self.update_setting('custom_mask', t))
        self.add_property_row("Custom Mask:", mask_edit)

        # Placeholder character
        placeholder_edit = QLineEdit()
        placeholder_edit.setMaximumWidth(30)
        placeholder_edit.setText(self.get_setting('placeholder_char', '_'))
        placeholder_edit.textChanged.connect(lambda t: self.update_setting('placeholder_char', t))
        self.add_property_row("Placeholder:", placeholder_edit)

        # Keep mask checkbox
        keep_mask_check = QCheckBox("Keep mask in value")
        keep_mask_check.setChecked(self.get_setting('keep_mask', False))
        keep_mask_check.toggled.connect(lambda checked: self.update_setting('keep_mask', checked))
        self.options_layout.addWidget(keep_mask_check)

    def create_custom_options_simple(self):
        """Create simplified custom formatting options"""

        # Format script (smaller text area)
        format_edit = QTextEdit()
        format_edit.setMaximumHeight(60)
        format_edit.setPlaceholderText("JavaScript formatting code...")
        format_edit.setPlainText(self.get_setting('format_script', ''))
        format_edit.textChanged.connect(lambda: self.update_setting('format_script', format_edit.toPlainText()))
        self.add_property_row("Format Script:", format_edit)

        # Keystroke script
        keystroke_edit = QTextEdit()
        keystroke_edit.setMaximumHeight(60)
        keystroke_edit.setPlaceholderText("JavaScript keystroke validation...")
        keystroke_edit.setPlainText(self.get_setting('keystroke_script', ''))
        keystroke_edit.textChanged.connect(
            lambda: self.update_setting('keystroke_script', keystroke_edit.toPlainText()))
        self.add_property_row("Keystroke Script:", keystroke_edit)

        # Validation script
        validation_edit = QTextEdit()
        validation_edit.setMaximumHeight(60)
        validation_edit.setPlaceholderText("JavaScript validation...")
        validation_edit.setPlainText(self.get_setting('validation_script', ''))
        validation_edit.textChanged.connect(
            lambda: self.update_setting('validation_script', validation_edit.toPlainText()))
        self.add_property_row("Validation Script:", validation_edit)

    def create_separator_combo(self):
        """Create separator style combo with simplified labels"""
        separator_combo = QComboBox()
        separator_combo.setMaximumWidth(100)

        for key, config in self.SEPARATOR_STYLES.items():
            separator_combo.addItem(config['label'], key)

        # Set current selection from stored value
        current_style = self.get_setting('separator_style', 'comma_dot')
        for i in range(separator_combo.count()):
            if separator_combo.itemData(i) == current_style:
                separator_combo.setCurrentIndex(i)
                break

        separator_combo.currentTextChanged.connect(
            lambda: self.update_setting('separator_style', separator_combo.currentData())
        )
        return separator_combo

    def add_property_row(self, label_text: str, widget):
        """Add a property row with consistent styling"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)

        # Label with fixed width
        label = QLabel(label_text)
        label.setFixedWidth(80)  # Match other property labels
        row_layout.addWidget(label)

        # Widget
        row_layout.addWidget(widget)

        # Stretch to push everything left
        row_layout.addStretch()

        self.options_layout.addLayout(row_layout)

    def update_setting(self, key: str, value: Any):
        """Update a format setting and refresh preview"""
        if 'settings' not in self.format_config:
            self.format_config['settings'] = {}

        self.format_config['settings'][key] = value
        print(f"DEBUG: Updated setting {key} = {value}")  # Debug line
        print(f"DEBUG: Current settings: {self.format_config['settings']}")  # Debug line

        self.update_preview()
        self.formatChanged.emit(self.format_config)

    def update_preview(self):
        """Update preview based on current format configuration"""
        category = self.format_config.get('category', 'None')
        settings = self.format_config.get('settings', {})

        try:
            if category == 'None':
                preview = "Sample text input"
            elif category == 'Number':
                preview = self.preview_number(1234.56, settings)
            elif category == 'Percentage':
                preview = self.preview_percentage(0.1234, settings)
            elif category == 'Date':
                preview = self.preview_date(settings)
            elif category == 'Time':
                preview = self.preview_time(settings)
            elif category == 'Special':
                preview = self.preview_special(settings)
            elif category == 'Custom':
                preview = "Custom formatted value"
            else:
                preview = "Unknown format"

            self.preview_label.setText(preview)

        except Exception as e:
            self.preview_label.setText(f"Preview error: {str(e)}")

    def preview_number(self, value: float, settings: Dict[str, Any]) -> str:
        """Generate number format preview"""
        separator_style = settings.get('separator_style', 'comma_dot')
        decimal_places = settings.get('decimal_places', 2)
        currency_symbol = settings.get('currency_symbol', '')

        # Get separator configuration
        sep_config = self.SEPARATOR_STYLES.get(separator_style, self.SEPARATOR_STYLES['comma_dot'])
        thousands_sep = sep_config['thousands']
        decimal_sep = sep_config['decimal']

        # Format number
        formatted = f"{value:.{decimal_places}f}"

        # Replace decimal separator
        if decimal_sep != '.':
            parts = formatted.split('.')
            formatted = decimal_sep.join(parts)

        # Add thousands separator (simplified)
        if thousands_sep and decimal_sep in formatted:
            parts = formatted.split(decimal_sep)
            integer_part = parts[0]

            # Add thousands separators every 3 digits from right
            if len(integer_part) > 3:
                chars = list(integer_part)
                for i in range(len(chars) - 3, 0, -3):
                    chars.insert(i, thousands_sep)
                integer_part = ''.join(chars)

            formatted = integer_part + decimal_sep + parts[1] if len(parts) > 1 else integer_part

        # Add currency symbol
        if currency_symbol:
            formatted = currency_symbol + formatted

        return formatted

    def preview_percentage(self, value: float, settings: Dict[str, Any]) -> str:
        """Generate percentage format preview"""
        multiply = settings.get('multiply_by_100', True)
        space_before = settings.get('space_before_percent', False)
        decimal_places = settings.get('decimal_places', 2)

        # Apply multiplication
        if multiply:
            value = value * 100

        # Format as number first
        number_preview = self.preview_number(value, settings)

        # Add percentage symbol
        if space_before:
            return number_preview + " %"
        else:
            return number_preview + "%"

    def preview_date(self, settings: Dict[str, Any]) -> str:
        """Generate date format preview"""
        from datetime import datetime

        format_str = settings.get('date_format', 'MM/DD/YYYY')

        # Use current date for preview
        now = datetime.now()

        # Simple format replacement (for preview only)
        preview = format_str
        preview = preview.replace('YYYY', str(now.year))
        preview = preview.replace('MM', f"{now.month:02d}")
        preview = preview.replace('DD', f"{now.day:02d}")
        preview = preview.replace('MMM', now.strftime('%b'))

        return preview

    def preview_time(self, settings: Dict[str, Any]) -> str:
        """Generate time format preview"""
        from datetime import datetime

        format_str = settings.get('time_format', 'HH:MM')
        hour24 = settings.get('hour24_format', True)

        # Use current time for preview
        now = datetime.now()

        if hour24:
            return now.strftime(format_str.replace('H', '%H').replace('M', '%M').replace('S', '%S'))
        else:
            return now.strftime(format_str.replace('H', '%I').replace('M', '%M').replace('S', '%S') + ' %p')

    def preview_special(self, settings: Dict[str, Any]) -> str:
        """Generate special format preview"""
        pattern = settings.get('pattern', 'phone_us')

        if pattern in self.SPECIAL_PATTERNS:
            return self.SPECIAL_PATTERNS[pattern]['sample']
        elif pattern == 'custom_mask':
            custom_mask = settings.get('custom_mask', '')
            return custom_mask if custom_mask else 'Custom pattern...'
        else:
            return 'Unknown pattern'

    def load_format_config(self, config: Dict[str, Any]):
        """Load format configuration into UI"""
        self._loading_config = True  # Prevent change signals during load

        self.format_config = config.copy() if config else {'category': 'None', 'settings': {}}

        # Set category dropdown
        category = self.format_config.get('category', 'None')
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == category:
                self.category_combo.setCurrentIndex(i)
                break

        # Update options UI with current settings
        self.update_options_ui()
        self.update_preview()

        self._loading_config = False  # Re-enable change signals

    def get_format_config(self) -> Dict[str, Any]:
        """Get current format configuration"""
        return self.format_config.copy()

    def clear_layout(self, layout):
        """Recursively clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())