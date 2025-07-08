from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QLabel, QComboBox

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
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Border color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Border Color:"))

        self.color_widget = ColorPropertyWidget("Border Color", self.border_props['color'], allow_transparent=True)
        self.color_widget.colorChanged.connect(self.on_border_changed)

        color_layout.addWidget(self.color_widget)
        layout.addLayout(color_layout)

        # Border width
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))

        self.width_combo = QComboBox()
        self.width_combo.addItems(["hairline", "thin", "medium", "thick"])
        self.width_combo.setCurrentText(self.border_props['width'])
        self.width_combo.currentTextChanged.connect(self.on_border_changed)

        width_layout.addWidget(self.width_combo)
        width_layout.addStretch()
        layout.addLayout(width_layout)

        # Border style
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Style:"))

        self.style_combo = QComboBox()
        self.style_combo.addItems(["solid", "dashed", "beveled", "inset", "underline"])
        self.style_combo.setCurrentText(self.border_props['style'])
        self.style_combo.currentTextChanged.connect(self.on_border_changed)

        style_layout.addWidget(self.style_combo)
        style_layout.addStretch()
        layout.addLayout(style_layout)

        self.setLayout(layout)

    def on_border_changed(self):
        """Handle border property changes"""
        self.border_props = {
            'color': self.color_widget.get_color(),
            'width': self.width_combo.currentText(),
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
        self.color_widget.set_color(border_props.get('color', QColor(100, 100, 100)))
        self.width_combo.setCurrentText(border_props.get('width', 'thin'))
        self.style_combo.setCurrentText(border_props.get('style', 'solid'))