from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QVBoxLayout, QGroupBox, QHBoxLayout, QLabel, QWidget

from ui.border_property_widget import BorderPropertyWidget
from ui.color_property_widget import ColorPropertyWidget
from ui.font_property_widget import FontPropertyWidget
from ui.text_alignment_widget import TextAlignmentWidget


class AppearancePropertiesWidget(QWidget):
    """Complete appearance properties widget combining all appearance settings"""

    appearanceChanged = pyqtSignal(dict)

    def __init__(self, field_type: str = None):
        super().__init__()
        self.field_type = field_type
        self.appearance_props = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Font properties group
        font_group = QGroupBox("Font & Text")
        font_layout = QVBoxLayout()

        self.font_widget = FontPropertyWidget()
        self.font_widget.fontChanged.connect(self.on_appearance_changed)
        font_layout.addWidget(self.font_widget)

        # Text color
        text_color_layout = QHBoxLayout()
        text_color_layout.addWidget(QLabel("Text Color:"))
        self.text_color_widget = ColorPropertyWidget("Text Color", QColor(0, 0, 0), allow_transparent=False)
        self.text_color_widget.colorChanged.connect(self.on_appearance_changed)
        text_color_layout.addWidget(self.text_color_widget)
        font_layout.addLayout(text_color_layout)

        # Text alignment (only for text-based fields)
        if self.field_type in ['text', 'textarea', None]:
            self.alignment_widget = TextAlignmentWidget()
            self.alignment_widget.alignmentChanged.connect(self.on_appearance_changed)
            font_layout.addWidget(self.alignment_widget)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Border properties group
        border_group = QGroupBox("Border")
        border_layout = QVBoxLayout()

        self.border_widget = BorderPropertyWidget()
        self.border_widget.borderChanged.connect(self.on_appearance_changed)
        border_layout.addWidget(self.border_widget)

        border_group.setLayout(border_layout)
        layout.addWidget(border_group)

        # Background properties group
        bg_group = QGroupBox("Background")
        bg_layout = QHBoxLayout()

        bg_layout.addWidget(QLabel("Fill Color:"))
        self.bg_color_widget = ColorPropertyWidget("Background Color", QColor(255, 255, 255, 0), allow_transparent=True)
        self.bg_color_widget.colorChanged.connect(self.on_appearance_changed)
        bg_layout.addWidget(self.bg_color_widget)

        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)

        self.setLayout(layout)

    def on_appearance_changed(self):
        """Handle any appearance property change"""
        self.appearance_props = {
            'font': self.font_widget.get_font_properties(),
            'text_color': self.text_color_widget.get_color(),
            'border': self.border_widget.get_border_properties(),
            'background_color': self.bg_color_widget.get_color()
        }

        # Add alignment if available
        if hasattr(self, 'alignment_widget'):
            self.appearance_props['text_alignment'] = self.alignment_widget.get_alignment()

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
            self.text_color_widget.set_color(appearance_props['text_color'])

        # Update border properties
        if 'border' in appearance_props:
            self.border_widget.set_border_properties(appearance_props['border'])

        # Update background color
        if 'background_color' in appearance_props:
            self.bg_color_widget.set_color(appearance_props['background_color'])

        # Update alignment if available
        if hasattr(self, 'alignment_widget') and 'text_alignment' in appearance_props:
            self.alignment_widget.set_alignment(appearance_props['text_alignment'])