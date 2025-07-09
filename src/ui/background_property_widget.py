# File: src/ui/background_property_widget.py
"""
Background Property Widget
Provides background styling controls with consistent alignment matching Font & Text group
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QSpinBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

from ui.color_property_widget import ColorPropertyWidget


class BackgroundPropertyWidget(QWidget):
    """Widget for controlling background properties with consistent styling"""

    backgroundChanged = pyqtSignal(dict)  # Emits background properties

    def __init__(self):
        super().__init__()
        self.background_props = {}
        self.init_ui()

    def init_ui(self):
        """Initialize background property UI with consistent styling"""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Background controls using grid layout like font controls
        bg_layout = QGridLayout()
        bg_layout.setHorizontalSpacing(8)  # Same as font controls
        bg_layout.setVerticalSpacing(5)

        # Background color
        color_label = QLabel("Color:")
        color_label.setFixedWidth(50)  # Same width as font labels
        color_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        bg_layout.addWidget(color_label, 0, 0)

        self.bg_color_widget = ColorPropertyWidget("Background Color", QColor(255, 255, 255, 0), allow_transparent=True)
        bg_layout.addWidget(self.bg_color_widget, 0, 1, Qt.AlignmentFlag.AlignLeft)

        # Opacity/Transparency
        opacity_label = QLabel("Opacity:")
        opacity_label.setFixedWidth(50)  # Same width as font labels
        opacity_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        bg_layout.addWidget(opacity_label, 1, 0)

        self.opacity_spinner = QSpinBox()
        self.opacity_spinner.setRange(0, 100)
        self.opacity_spinner.setValue(100)
        self.opacity_spinner.setSuffix("%")
        self.opacity_spinner.setMaximumWidth(50)  # Same as font size spinner
        self.opacity_spinner.setMinimumWidth(50)
        bg_layout.addWidget(self.opacity_spinner, 1, 1, Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(bg_layout)
        self.setLayout(layout)

        # Connect signals
        self.bg_color_widget.colorChanged.connect(self.on_background_changed)
        self.opacity_spinner.valueChanged.connect(self.on_background_changed)

    def on_background_changed(self):
        """Handle background property changes"""
        self.background_props = {
            'color': self.bg_color_widget.get_color(),
            'opacity': self.opacity_spinner.value()
        }
        self.backgroundChanged.emit(self.background_props)

    def get_background_properties(self) -> dict:
        """Get current background properties"""
        return self.background_props.copy()

    def set_background_properties(self, bg_props: dict):
        """Set background properties"""
        self.background_props = bg_props

        # Update color
        if 'color' in bg_props:
            self.bg_color_widget.set_color(bg_props['color'])

        # Update opacity
        if 'opacity' in bg_props:
            self.opacity_spinner.setValue(bg_props['opacity'])

    def get_color(self):
        """Get current background color"""
        return self.bg_color_widget.get_color()

    def set_color(self, color):
        """Set background color"""
        self.bg_color_widget.set_color(color)

    def get_opacity(self) -> int:
        """Get current opacity percentage"""
        return self.opacity_spinner.value()

    def set_opacity(self, opacity: int):
        """Set opacity percentage (0-100)"""
        self.opacity_spinner.setValue(opacity)

    def is_transparent(self) -> bool:
        """Check if background is fully transparent"""
        return self.opacity_spinner.value() == 0

    def make_transparent(self):
        """Set background to fully transparent"""
        self.opacity_spinner.setValue(0)

    def make_opaque(self):
        """Set background to fully opaque"""
        self.opacity_spinner.setValue(100)