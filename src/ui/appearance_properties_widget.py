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

    def working_init_ui(self):
        """
        Initialize UI - create groups that can be extracted if needed
        """
        # Font properties group
        self.font_group = QGroupBox("Text")
        font_layout = QVBoxLayout()

        self.font_widget = FontPropertyWidget()
        self.font_widget.fontChanged.connect(self.on_appearance_changed)
        font_layout.addWidget(self.font_widget)

        self.font_group.setLayout(font_layout)

        # Border properties group
        self.border_group = QGroupBox("Border")
        border_layout = QVBoxLayout()

        self.border_widget = BorderPropertyWidget()
        self.border_widget.borderChanged.connect(self.on_appearance_changed)
        border_layout.addWidget(self.border_widget)

        self.border_group.setLayout(border_layout)

        # Background properties group
        self.bg_group = QGroupBox("Background")
        bg_layout = QVBoxLayout()

        self.bg_widget = BackgroundPropertyWidget()
        self.bg_widget.backgroundChanged.connect(self.on_appearance_changed)
        bg_layout.addWidget(self.bg_widget)

        self.bg_group.setLayout(bg_layout)

        # Only create and set layout if this widget will be used standalone
        if self.standalone:
            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.addWidget(self.font_group)
            layout.addWidget(self.border_group)
            layout.addWidget(self.bg_group)
            self.setLayout(layout)

    def init_ui(self):
        """Initialize UI - only create requested property groups"""

        # Font properties group (only if requested)
        if 'font' in self.show_properties:
            self.font_group = QGroupBox("Text")
            font_layout = QVBoxLayout()
            self.font_widget = FontPropertyWidget()
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

        # Alignment properties group (only if requested)
        if 'alignment' in self.show_properties:
            self.alignment_group = QGroupBox("Text Alignment")
            alignment_layout = QVBoxLayout()
            self.alignment_widget = AlignmentGridWidget()
            self.alignment_widget.alignmentChanged.connect(self.on_appearance_changed)
            alignment_layout.addWidget(self.alignment_widget)
            self.alignment_group.setLayout(alignment_layout)

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
        return [self.font_group, self.border_group, self.bg_group]

    def on_appearance_changed(self):
        """Handle any appearance property change"""
        self.appearance_props = {
            'font': self.font_widget.get_font_properties(),
            'text_color': self.font_widget.text_color_widget.get_color(),
            'border': self.border_widget.get_border_properties(),
            'background_color': self.bg_widget.bg_color_widget.get_color()
        }

        # Add alignment if available
        if hasattr(self, 'alignment_widget'):
            self.appearance_props['text_alignment'] = self.alignment_widget.get_alignment()

        # Add alignment if available (3x3 grid)
        if hasattr(self, 'alignment_widget'):
            alignment_data = {
                'combined': self.alignment_widget.get_alignment(),  # e.g., "top-left"
                'horizontal': self.alignment_widget.get_horizontal_alignment(),  # "left"
                'vertical': self.alignment_widget.get_vertical_alignment(),  # "top"
                'css': self.alignment_widget.get_css_alignment()  # CSS properties
            }
            self.appearance_props['alignment'] = alignment_data

        self.appearanceChanged.emit(self.appearance_props)

    def get_appearance_properties(self) -> dict:
        """Get all appearance properties"""
        return self.appearance_props.copy()

    def set_appearance_properties(self, appearance_props: dict):
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

        # Update alignment if available
        if hasattr(self, 'alignment_widget') and 'text_alignment' in appearance_props:
            self.alignment_widget.set_alignment(appearance_props['text_alignment'])


