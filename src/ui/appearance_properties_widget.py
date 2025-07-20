from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QVBoxLayout, QGroupBox, QHBoxLayout, QLabel, QWidget

from ui.background_property_widget import BackgroundPropertyWidget
from ui.border_property_widget import BorderPropertyWidget
from ui.color_property_widget import ColorPropertyWidget
from ui.font_property_widget import FontPropertyWidget
from ui.text_alignment_widget import TextAlignmentWidget
from ui.alignment_grid_widget import AlignmentGridWidget

class AppearancePropertiesWidget(QWidget):
    """Complete appearance properties widget combining all appearance settings"""

    appearanceChanged = pyqtSignal(dict)

    def __init__(self, field_type: str = None, show_properties=None, standalone=True):
        super().__init__()
        self.field_type = field_type
        self.show_properties = show_properties or ['font', 'border', 'background', 'alignment']
        self.appearance_props = {}
        self.standalone = standalone
        self.init_ui()

    def init_ui(self):
        """Initialize UI - only create requested property groups"""

        # Font properties group (only if requested)
        if 'font' in self.show_properties:
            self.font_group = QGroupBox("Formatting")
            font_layout = QVBoxLayout()
            show_text_alignment = 'alignment' in self.show_properties
            self.font_widget = FontPropertyWidget(
                initial_font_props=None,
                show_alignment=show_text_alignment
            )
            self.font_widget.fontChanged.connect(self.on_appearance_changed)
            font_layout.addWidget(self.font_widget)
            self.font_group.setLayout(font_layout)

        # Border properties group (only if requested)
        if 'border' in self.show_properties:
            self.border_group = QGroupBox("Border")
            border_layout = QVBoxLayout()
            self.border_widget = BorderPropertyWidget()
            self.border_widget.borderChanged.connect(self.on_appearance_changed)
            border_layout.addWidget(self.border_widget)
            self.border_group.setLayout(border_layout)

        # Background properties group (only if requested)
        if 'background' in self.show_properties:
            self.bg_group = QGroupBox("Background")
            bg_layout = QVBoxLayout()
            self.bg_widget = BackgroundPropertyWidget()
            self.bg_widget.backgroundChanged.connect(self.on_appearance_changed)
            bg_layout.addWidget(self.bg_widget)
            self.bg_group.setLayout(bg_layout)

        # Set up layout only if standalone
        if self.standalone:
            main_layout = QVBoxLayout()
            self.setLayout(main_layout)

            # Add only the created groups
            for group_name in self.show_properties:
                if hasattr(self, f'{group_name}_group'):
                    main_layout.addWidget(getattr(self, f'{group_name}_group'))

    def get_groups(self):
        """Return the individual group widgets for extraction"""
        groups = []
        if hasattr(self, 'font_group'):
            groups.append(self.font_group)
        if hasattr(self, 'border_group'):
            groups.append(self.border_group)
        if hasattr(self, 'bg_group'):
            groups.append(self.bg_group)
        return groups

    def on_appearance_changed(self):
        """Handle any appearance property change"""
        self.appearance_props = {}

        # Get font properties (includes alignment if enabled)
        if hasattr(self, 'font_widget'):
            self.appearance_props['font'] = self.font_widget.get_font_properties()

        # Get border properties
        if hasattr(self, 'border_widget'):
            self.appearance_props['border'] = self.border_widget.get_border_properties()

        # Get background properties
        if hasattr(self, 'bg_widget'):
            self.appearance_props['background'] = self.bg_widget.get_background_properties()

        self.appearanceChanged.emit(self.appearance_props)



    def get_appearance_properties(self) -> dict:
        """Get all appearance properties"""
        return self.appearance_props.copy()

    def set_appearance_properties(self, appearance_props: dict):
        """Set all appearance properties"""
        # Block the main widget's signal during restoration
        self.blockSignals(True)

        try:
            self.appearance_props = appearance_props

            # Your existing code here...
            if hasattr(self, 'font_widget') and 'font' in appearance_props:
                self.font_widget.set_font_properties(appearance_props['font'])

            if hasattr(self, 'border_widget') and 'border' in appearance_props:
                self.border_widget.set_border_properties(appearance_props['border'])

            if hasattr(self, 'bg_widget') and 'background' in appearance_props:
                self.bg_widget.set_background_properties(appearance_props['background'])

        finally:
            self.blockSignals(False)

    def deprecated_set_appearance_properties(self, appearance_props: dict):
        """Set all appearance properties"""
        self.appearance_props = appearance_props

        # Update font properties
        if 'font' in appearance_props:
            self.font_widget.set_font_properties(appearance_props['font'])

        # Update text color
        if 'text_color' in appearance_props:
            self.font_widget.text_color_widget.set_color(appearance_props['text_color'])

        # Update border properties
        if 'border' in appearance_props:
            self.border_widget.set_border_properties(appearance_props['border'])

        # Update background color
        if 'background_color' in appearance_props:
            self.bg_widget.set_color(appearance_props['background_color'])


