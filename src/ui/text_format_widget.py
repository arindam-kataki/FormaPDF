# src/ui/text_format_widget.py
"""
Text Field Format Widget for FormaPDF
Adobe Acrobat Pro compatible formatting with international number support
"""

from typing import Dict, Any, Optional, List
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QTextEdit,
    QGroupBox, QPushButton, QFrame, QScrollArea
)

from models.field_model import FieldType
from models.field_property_schema import PropertyDefinition, PropertyGroup, PropertyWidgetType


class TextFormatWidget(QWidget):
    """Widget for configuring text field formatting options"""

    formatChanged = pyqtSignal(dict)  # Emits format configuration

    # Adobe Acrobat Pro format categories
    FORMAT_CATEGORIES = {
        'None': 'No formatting applied',
        'Number': 'Format as numeric values',
        'Percentage': 'Format as percentage values',
        'Date': 'Format as date values',
        'Time': 'Format as time values',
        'Special': 'Special format patterns',
        'Custom': 'Custom formatting with JavaScript'
    }

    # International number separator styles
    SEPARATOR_STYLES = {
        'comma_dot': {
            'label': 'Comma + Dot (1,234.56)',
            'thousands': ',',
            'decimal': '.',
            'regions': ['US', 'UK', 'Canada', 'Australia']
        },
        'dot_comma': {
            'label': 'Dot + Comma (1.234,56)',
            'thousands': '.',
            'decimal': ',',
            'regions': ['Germany', 'France', 'Italy', 'Spain']
        },
        'space_comma': {
            'label': 'Space + Comma (1 234,56)',
            'thousands': ' ',
            'decimal': ',',
            'regions': ['France', 'Russia', 'Norway']
        },
        'space_dot': {
            'label': 'Space + Dot (1 234.56)',
            'thousands': ' ',
            'decimal': '.',
            'regions': ['Sweden', 'Finland']
        },
        'apostrophe_dot': {
            'label': "Apostrophe + Dot (1'234.56)",
            'thousands': "'",
            'decimal': '.',
            'regions': ['Switzerland']
        },
        'dot_only': {
            'label': 'Dot Only (1234.56)',
            'thousands': '',
            'decimal': '.',
            'regions': ['Simple format']
        },
        'comma_only': {
            'label': 'Comma Only (1234,56)',
            'thousands': '',
            'decimal': ',',
            'regions': ['Simple format']
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
        'MMM DD, YYYY', 'DD MMM YYYY', 'YYYY/MM/DD', 'MM-DD-YYYY',
        'MMMM DD, YYYY', 'DD MMMM YYYY', 'DDD, MMM DD, YYYY'
    ]

    # Time format options
    TIME_FORMATS = [
        'HH:MM', 'HH:MM:SS', 'H:MM AM/PM', 'H:MM:SS AM/PM',
        'HH.MM', 'HH,MM'
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
        self.options_scroll = None
        self.options_widget = None
        self.preview_label = None

        self.init_ui()
        self.load_format_config(self.format_config)

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title = QLabel("Text Field Format")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(title)

        # Format category selection
        self.create_category_section(layout)

        # Options container (scrollable)
        self.create_options_section(layout)

        # Preview section
        self.create_preview_section(layout)

        self.setLayout(layout)

    def create_category_section(self, parent_layout):
        """Create format category selection section"""
        group = QGroupBox("Format Category")
        group_layout = QVBoxLayout()

        # Category dropdown
        self.category_combo = QComboBox()
        self.category_combo.setMaximumWidth(250)

        for category, description in self.FORMAT_CATEGORIES.items():
            self.category_combo.addItem(f"{category} - {description}", category)

        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        group_layout.addWidget(self.category_combo)

        group.setLayout(group_layout)
        parent_layout.addWidget(group)

    def create_options_section(self, parent_layout):
        """Create scrollable options section"""
        group = QGroupBox("Format Options")
        group_layout = QVBoxLayout()

        # Scrollable area for options
        self.options_scroll = QScrollArea()
        self.options_scroll.setWidgetResizable(True)
        self.options_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.options_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.options_scroll.setMaximumHeight(200)

        # Options container widget
        self.options_widget = QWidget()
        self.options_scroll.setWidget(self.options_widget)

        group_layout.addWidget(self.options_scroll)
        group.setLayout(group_layout)
        parent_layout.addWidget(group)

    def create_preview_section(self, parent_layout):
        """Create preview section"""
        group = QGroupBox("Preview")
        group_layout = QVBoxLayout()

        self.preview_label = QLabel("Sample formatted value")
        self.preview_label.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #dee2e6; "
            "padding: 8px; font-family: 'Courier New', monospace;"
        )
        self.preview_label.setWordWrap(True)

        group_layout.addWidget(self.preview_label)
        group.setLayout(group_layout)
        parent_layout.addWidget(group)

    def on_category_changed(self):
        """Handle format category change"""
        category = self.category_combo.currentData()
        if category:
            self.format_config['category'] = category
            self.format_config['settings'] = {}
            self.update_options_ui()
            self.update_preview()
            self.formatChanged.emit(self.format_config)

    def update_options_ui(self):
        """Update options UI based on selected category"""
        category = self.format_config.get('category', 'None')

        # Clear existing options
        if self.options_widget.layout():
            self.clear_layout(self.options_widget.layout())

        # Create new layout
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Add category-specific options
        if category == 'Number':
            self.create_number_options(layout)
        elif category == 'Percentage':
            self.create_percentage_options(layout)
        elif category == 'Date':
            self.create_date_options(layout)
        elif category == 'Time':
            self.create_time_options(layout)
        elif category == 'Special':
            self.create_special_options(layout)
        elif category == 'Custom':
            self.create_custom_options(layout)
        else:  # None
            no_options = QLabel("No formatting options available")
            no_options.setStyleSheet("color: #6c757d; font-style: italic;")
            layout.addWidget(no_options)

        self.options_widget.setLayout(layout)

    def create_number_options(self, layout):
        """Create number formatting options"""
        grid = QGridLayout()
        row = 0

        # Separator style
        grid.addWidget(QLabel("Separator Style:"), row, 0)
        separator_combo = QComboBox()
        separator_combo.setMaximumWidth(200)

        for key, config in self.SEPARATOR_STYLES.items():
            separator_combo.addItem(config['label'], key)

        separator_combo.currentTextChanged.connect(
            lambda: self.update_setting('separator_style', separator_combo.currentData())
        )
        grid.addWidget(separator_combo, row, 1)
        row += 1

        # Decimal places
        grid.addWidget(QLabel("Decimal Places:"), row, 0)
        decimal_spin = QSpinBox()
        decimal_spin.setRange(0, 10)
        decimal_spin.setValue(2)
        decimal_spin.setMaximumWidth(60)
        decimal_spin.valueChanged.connect(
            lambda v: self.update_setting('decimal_places', v)
        )
        grid.addWidget(decimal_spin, row, 1)
        row += 1

        # Negative number style
        grid.addWidget(QLabel("Negative Numbers:"), row, 0)
        negative_combo = QComboBox()
        negative_combo.setMaximumWidth(150)
        negative_combo.addItems(['Minus Sign', 'Red Color', 'Parentheses', 'Red Parentheses'])
        negative_combo.currentTextChanged.connect(
            lambda: self.update_setting('negative_style', negative_combo.currentText().lower().replace(' ', '_'))
        )
        grid.addWidget(negative_combo, row, 1)
        row += 1

        # Currency symbol
        grid.addWidget(QLabel("Currency Symbol:"), row, 0)
        currency_edit = QLineEdit()
        currency_edit.setMaximumWidth(60)
        currency_edit.setPlaceholderText("$, €, ¥")
        currency_edit.textChanged.connect(
            lambda t: self.update_setting('currency_symbol', t)
        )
        grid.addWidget(currency_edit, row, 1)

        # Symbol position
        position_combo = QComboBox()
        position_combo.setMaximumWidth(80)
        position_combo.addItems(['Before', 'After'])
        position_combo.currentTextChanged.connect(
            lambda: self.update_setting('symbol_position', position_combo.currentText().lower())
        )
        grid.addWidget(position_combo, row, 2)
        row += 1

        # Show leading zero
        leading_zero_check = QCheckBox("Show Leading Zero")
        leading_zero_check.setChecked(True)
        leading_zero_check.toggled.connect(
            lambda checked: self.update_setting('leading_zero', checked)
        )
        grid.addWidget(leading_zero_check, row, 0, 1, 2)

        layout.addLayout(grid)

    def create_percentage_options(self, layout):
        """Create percentage formatting options"""
        grid = QGridLayout()
        row = 0

        # Separator style (inherit from number format)
        grid.addWidget(QLabel("Separator Style:"), row, 0)
        separator_combo = QComboBox()
        separator_combo.setMaximumWidth(200)

        for key, config in self.SEPARATOR_STYLES.items():
            if config['decimal'] in ['.', ',']:  # Only show relevant separators for percentages
                separator_combo.addItem(config['label'], key)

        separator_combo.currentTextChanged.connect(
            lambda: self.update_setting('separator_style', separator_combo.currentData())
        )
        grid.addWidget(separator_combo, row, 1)
        row += 1

        # Decimal places
        grid.addWidget(QLabel("Decimal Places:"), row, 0)
        decimal_spin = QSpinBox()
        decimal_spin.setRange(0, 10)
        decimal_spin.setValue(2)
        decimal_spin.setMaximumWidth(60)
        decimal_spin.valueChanged.connect(
            lambda v: self.update_setting('decimal_places', v)
        )
        grid.addWidget(decimal_spin, row, 1)
        row += 1

        # Multiply by 100
        multiply_check = QCheckBox("Multiply by 100 (0.25 → 25%)")
        multiply_check.setChecked(True)
        multiply_check.toggled.connect(
            lambda checked: self.update_setting('multiply_by_100', checked)
        )
        grid.addWidget(multiply_check, row, 0, 1, 2)
        row += 1

        # Space before %
        space_check = QCheckBox("Space before % symbol")
        space_check.toggled.connect(
            lambda checked: self.update_setting('space_before_percent', checked)
        )
        grid.addWidget(space_check, row, 0, 1, 2)

        layout.addLayout(grid)

    def create_date_options(self, layout):
        """Create date formatting options"""
        grid = QGridLayout()
        row = 0

        # Date format
        grid.addWidget(QLabel("Date Format:"), row, 0)
        format_combo = QComboBox()
        format_combo.setMaximumWidth(150)
        format_combo.addItems(self.DATE_FORMATS)
        format_combo.currentTextChanged.connect(
            lambda: self.update_setting('date_format', format_combo.currentText())
        )
        grid.addWidget(format_combo, row, 1)
        row += 1

        # Validate date
        validate_check = QCheckBox("Validate date input")
        validate_check.setChecked(True)
        validate_check.toggled.connect(
            lambda checked: self.update_setting('validate_date', checked)
        )
        grid.addWidget(validate_check, row, 0, 1, 2)
        row += 1

        # Date range
        grid.addWidget(QLabel("Min Date:"), row, 0)
        min_date_edit = QLineEdit()
        min_date_edit.setPlaceholderText("YYYY-MM-DD")
        min_date_edit.setMaximumWidth(100)
        min_date_edit.textChanged.connect(
            lambda t: self.update_setting('min_date', t)
        )
        grid.addWidget(min_date_edit, row, 1)
        row += 1

        grid.addWidget(QLabel("Max Date:"), row, 0)
        max_date_edit = QLineEdit()
        max_date_edit.setPlaceholderText("YYYY-MM-DD")
        max_date_edit.setMaximumWidth(100)
        max_date_edit.textChanged.connect(
            lambda t: self.update_setting('max_date', t)
        )
        grid.addWidget(max_date_edit, row, 1)

        layout.addLayout(grid)

    def create_time_options(self, layout):
        """Create time formatting options"""
        grid = QGridLayout()
        row = 0

        # Time format
        grid.addWidget(QLabel("Time Format:"), row, 0)
        format_combo = QComboBox()
        format_combo.setMaximumWidth(120)
        format_combo.addItems(self.TIME_FORMATS)
        format_combo.currentTextChanged.connect(
            lambda: self.update_setting('time_format', format_combo.currentText())
        )
        grid.addWidget(format_combo, row, 1)
        row += 1

        # 24 hour format
        hour24_check = QCheckBox("24 Hour Format")
        hour24_check.setChecked(True)
        hour24_check.toggled.connect(
            lambda checked: self.update_setting('hour24_format', checked)
        )
        grid.addWidget(hour24_check, row, 0, 1, 2)
        row += 1

        # Show seconds
        seconds_check = QCheckBox("Show Seconds")
        seconds_check.toggled.connect(
            lambda checked: self.update_setting('show_seconds', checked)
        )
        grid.addWidget(seconds_check, row, 0, 1, 2)
        row += 1

        # Validate time
        validate_check = QCheckBox("Validate time input")
        validate_check.setChecked(True)
        validate_check.toggled.connect(
            lambda checked: self.update_setting('validate_time', checked)
        )
        grid.addWidget(validate_check, row, 0, 1, 2)

        layout.addLayout(grid)

    def create_special_options(self, layout):
        """Create special formatting options"""
        grid = QGridLayout()
        row = 0

        # Pattern selection
        grid.addWidget(QLabel("Special Pattern:"), row, 0)
        pattern_combo = QComboBox()
        pattern_combo.setMaximumWidth(180)

        for key, config in self.SPECIAL_PATTERNS.items():
            pattern_combo.addItem(key.replace('_', ' ').title(), key)

        pattern_combo.currentTextChanged.connect(
            lambda: self.update_setting('pattern', pattern_combo.currentData())
        )
        grid.addWidget(pattern_combo, row, 1)
        row += 1

        # Custom mask (for custom_mask pattern)
        grid.addWidget(QLabel("Custom Mask:"), row, 0)
        mask_edit = QLineEdit()
        mask_edit.setPlaceholderText("(999) 999-9999")
        mask_edit.setMaximumWidth(120)
        mask_edit.textChanged.connect(
            lambda t: self.update_setting('custom_mask', t)
        )
        grid.addWidget(mask_edit, row, 1)
        row += 1

        # Placeholder character
        grid.addWidget(QLabel("Placeholder Char:"), row, 0)
        placeholder_edit = QLineEdit()
        placeholder_edit.setText("_")
        placeholder_edit.setMaximumWidth(30)
        placeholder_edit.textChanged.connect(
            lambda t: self.update_setting('placeholder_char', t)
        )
        grid.addWidget(placeholder_edit, row, 1)
        row += 1

        # Keep mask in value
        keep_mask_check = QCheckBox("Keep mask characters in value")
        keep_mask_check.toggled.connect(
            lambda checked: self.update_setting('keep_mask', checked)
        )
        grid.addWidget(keep_mask_check, row, 0, 1, 2)

        layout.addLayout(grid)

    def create_custom_options(self, layout):
        """Create custom JavaScript formatting options"""
        grid = QGridLayout()
        row = 0

        # Format script
        grid.addWidget(QLabel("Format Script:"), row, 0)
        row += 1

        format_edit = QTextEdit()
        format_edit.setMaximumHeight(60)
        format_edit.setPlaceholderText("JavaScript code for formatting...")
        format_edit.textChanged.connect(
            lambda: self.update_setting('format_script', format_edit.toPlainText())
        )
        grid.addWidget(format_edit, row, 0, 1, 2)
        row += 1

        # Keystroke script
        grid.addWidget(QLabel("Keystroke Script:"), row, 0)
        row += 1

        keystroke_edit = QTextEdit()
        keystroke_edit.setMaximumHeight(60)
        keystroke_edit.setPlaceholderText("JavaScript code for keystroke validation...")
        keystroke_edit.textChanged.connect(
            lambda: self.update_setting('keystroke_script', keystroke_edit.toPlainText())
        )
        grid.addWidget(keystroke_edit, row, 0, 1, 2)
        row += 1

        # Validation script
        grid.addWidget(QLabel("Validation Script:"), row, 0)
        row += 1

        validation_edit = QTextEdit()
        validation_edit.setMaximumHeight(60)
        validation_edit.setPlaceholderText("JavaScript code for validation...")
        validation_edit.textChanged.connect(
            lambda: self.update_setting('validation_script', validation_edit.toPlainText())
        )
        grid.addWidget(validation_edit, row, 0, 1, 2)

        layout.addLayout(grid)

    def update_setting(self, key: str, value: Any):
        """Update a format setting and refresh preview"""
        if 'settings' not in self.format_config:
            self.format_config['settings'] = {}

        self.format_config['settings'][key] = value
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
        symbol_position = settings.get('symbol_position', 'before')

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

        # Add thousands separator
        if thousands_sep:
            parts = formatted.split(decimal_sep)
            integer_part = parts[0]

            # Add thousands separators (simplified)
            if len(integer_part) > 3:
                # Insert separators every 3 digits from right
                chars = list(integer_part)
                for i in range(len(chars) - 3, 0, -3):
                    chars.insert(i, thousands_sep)
                integer_part = ''.join(chars)

            if len(parts) > 1:
                formatted = integer_part + decimal_sep + parts[1]
            else:
                formatted = integer_part

        # Add currency symbol
        if currency_symbol:
            if symbol_position == 'before':
                formatted = currency_symbol + formatted
            else:
                formatted = formatted + currency_symbol

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
        preview = preview.replace('MMMM', now.strftime('%B'))
        preview = preview.replace('DDD', now.strftime('%a'))

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
        self.format_config = config

        # Set category
        category = config.get('category', 'None')
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == category:
                self.category_combo.setCurrentIndex(i)
                break

        # Update options and preview
        self.update_options_ui()
        self.update_preview()

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


# Property definition for integration with field schema
def create_text_format_property_group() -> PropertyGroup:
    """Create property group for text format configuration"""
    return PropertyGroup(
        name="text_format",
        label="Text Format",
        description="Configure text field formatting options",
        properties=[
            PropertyDefinition(
                name="format_category",
                label="Format Category",
                widget_type=PropertyWidgetType.CHOICE,
                default_value="None",
                choices=list(TextFormatWidget.FORMAT_CATEGORIES.keys()),
                description="Type of formatting to apply"
            ),
            PropertyDefinition(
                name="format_settings",
                label="Format Settings",
                widget_type=PropertyWidgetType.TEXT,  # JSON string
                default_value="{}",
                description="Category-specific format configuration"
            )
        ]
    )