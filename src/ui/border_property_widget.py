from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel, QComboBox, QGridLayout, QSpinBox

from ui.color_property_widget import ColorPropertyWidget


class BorderPropertyWidget(QWidget):
    """Widget for border styling"""

    borderChanged = pyqtSignal(dict)

    def __init__(self, initial_border_props: dict = None):
        super().__init__()
        self.border_props = initial_border_props or {
            'color': QColor(100, 100, 100),
            'width': 'thin',
            'style': 'solid'
        }
        self.init_ui()

    def init_ui(self):
        """Initialize border property UI with consistent styling"""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Border controls using grid layout like font controls
        border_layout = QGridLayout()
        border_layout.setHorizontalSpacing(8)  # Same as font controls
        border_layout.setVerticalSpacing(5)

        # Border style
        style_label = QLabel("Style:")
        style_label.setFixedWidth(50)  # Same width as font labels
        style_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        border_layout.addWidget(style_label, 0, 0)

        self.style_combo = QComboBox()
        self.style_combo.setMaximumWidth(120)  # Same as font combo
        self.style_combo.setMinimumWidth(120)
        self.style_combo.addItems(['None', 'Solid', 'Dashed', 'Dotted'])
        border_layout.addWidget(self.style_combo, 0, 1, Qt.AlignmentFlag.AlignLeft)

        # Border width
        width_label = QLabel("Width:")
        width_label.setFixedWidth(50)  # Same width as font labels
        width_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        border_layout.addWidget(width_label, 1, 0)

        self.width_combo = QComboBox()
        self.width_combo.setMaximumWidth(80)  # Slightly wider for text
        self.width_combo.setMinimumWidth(80)
        self.width_combo.addItems(['hairline', 'thin', 'medium', 'thick'])
        self.width_combo.setCurrentText('thin')  # Default value
        border_layout.addWidget(self.width_combo, 1, 1, Qt.AlignmentFlag.AlignLeft)

        # Border color
        color_label = QLabel("Color:")
        color_label.setFixedWidth(50)  # Same width as font labels
        color_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        border_layout.addWidget(color_label, 2, 0)

        self.border_color_widget = ColorPropertyWidget("Border Color", QColor(0, 0, 0), allow_transparent=False)
        border_layout.addWidget(self.border_color_widget, 2, 1, Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(border_layout)
        self.setLayout(layout)

        # Connect signals
        self.style_combo.currentTextChanged.connect(self.on_border_changed)
        self.width_combo.currentTextChanged.connect(self.on_border_changed)
        self.border_color_widget.colorChanged.connect(self.on_border_changed)

    def on_border_changed(self):
        """Handle border property changes"""
        self.border_props = {
            'color': self.border_color_widget.get_color(),
            'width': self.width_combo.currentText(),  # Fixed: Added .value() and missing comma
            'style': self.style_combo.currentText()
        }
        self.borderChanged.emit(self.border_props)

    def get_border_properties(self) -> dict:
        """Get current border properties"""
        return self.border_props.copy()

    def set_border_properties(self, border_props: dict):
        """Set border properties"""
        self.border_props = border_props

        # Update UI
        self.border_color_widget.set_color(border_props.get('color', QColor(100, 100, 100)))
        self.width_combo.setVisible(border_props.get('width', 'thin'))
        self.style_combo.setCurrentText(border_props.get('style', 'solid'))