# File: src/ui/background_property_widget.py
"""
Background Property Widget
Provides background styling controls with consistent alignment matching Font & Text group
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QSpinBox, QCheckBox
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

        self.none_check = QCheckBox("None")
        self.none_check.setToolTip("No background color (transparent)")
        self.none_check.toggled.connect(self.on_none_toggled)
        bg_layout.addWidget(self.none_check, 0, 2, Qt.AlignmentFlag.AlignLeft)

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

        # None checkbox - similar to auto-size in font widget
        none_label = QLabel("None:")
        none_label.setFixedWidth(50)  # Same width as other labels
        none_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        bg_layout.addWidget(none_label, 2, 0)

        self.none_check = QCheckBox("No background")
        self.none_check.setToolTip("No background color (transparent)")
        self.none_check.toggled.connect(self.on_none_toggled)
        bg_layout.addWidget(self.none_check, 2, 1, Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(bg_layout)
        self.setLayout(layout)

        # Connect signals
        self.bg_color_widget.colorChanged.connect(self.on_background_changed)
        self.opacity_spinner.valueChanged.connect(self.on_background_changed)

    def on_none_toggled(self, checked: bool):
        """Handle none checkbox toggle"""
        if checked:
            # Set transparent background and disable controls
            transparent_color = QColor(0, 0, 0, 0)
            self.bg_color_widget.set_color(transparent_color)
            self.opacity_spinner.setValue(0)
            self.bg_color_widget.setEnabled(False)
            self.opacity_spinner.setEnabled(False)
        else:
            # Enable controls and set default values if currently transparent
            self.bg_color_widget.setEnabled(True)
            self.opacity_spinner.setEnabled(True)
            if self.bg_color_widget.get_color().alpha() == 0:
                # Set default white background
                self.bg_color_widget.set_color(QColor(255, 255, 255))
            if self.opacity_spinner.value() == 0:
                self.opacity_spinner.setValue(100)

        self.on_background_changed()

    def on_background_changed(self):
        """Handle background property changes"""
        # Update None checkbox state based on current values
        if hasattr(self, 'none_check'):
            current_color = self.bg_color_widget.get_color()
            current_opacity = self.opacity_spinner.value()
            is_transparent = current_color.alpha() == 0 or current_opacity == 0

            self.none_check.blockSignals(True)  # Prevent recursive calls
            self.none_check.setChecked(is_transparent)
            self.bg_color_widget.setEnabled(not is_transparent)
            self.opacity_spinner.setEnabled(not is_transparent)
            self.none_check.blockSignals(False)

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

        # Update None checkbox state
        if hasattr(self, 'none_check'):
            color = bg_props.get('color', QColor(255, 255, 255))
            opacity = bg_props.get('opacity', 100)
            is_transparent = color.alpha() == 0 or opacity == 0

            self.none_check.blockSignals(True)
            self.none_check.setChecked(is_transparent)
            self.bg_color_widget.setEnabled(not is_transparent)
            self.opacity_spinner.setEnabled(not is_transparent)
            self.none_check.blockSignals(False)

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