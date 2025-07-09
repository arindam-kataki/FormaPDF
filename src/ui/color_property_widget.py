"""
Appearance Property Widgets
UI components for field appearance settings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QButtonGroup, QRadioButton,
    QColorDialog, QGroupBox, QGridLayout, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter


class ColorPropertyWidget(QWidget):
    """Widget for selecting colors with preview"""

    colorChanged = pyqtSignal(QColor)

    def __init__(self, property_name: str, initial_color: QColor = None, allow_transparent: bool = True):
        super().__init__()
        self.property_name = property_name
        self.current_color = initial_color or QColor(0, 0, 0)
        self.allow_transparent = allow_transparent
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Color preview button
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 25)
        self.color_button.clicked.connect(self.select_color)
        self.update_color_button()

        # Color description label
        self.color_label = QLabel()
        self.update_color_label()

        layout.addWidget(self.color_button)
        layout.addWidget(self.color_label)
        layout.addStretch()

        if self.allow_transparent:
            # Transparent/None button
            self.transparent_btn = QPushButton("None")
            self.transparent_btn.setFixedSize(50, 25)
            self.transparent_btn.clicked.connect(self.set_transparent)
            layout.addWidget(self.transparent_btn)

        self.setLayout(layout)

    def update_color_button(self):
        """Update the color preview button"""
        if self.current_color.alpha() == 0:
            # Transparent - show checkerboard pattern
            pixmap = QPixmap(40, 25)
            painter = QPainter(pixmap)
            painter.fillRect(0, 0, 40, 25, QColor(255, 255, 255))

            # Draw checkerboard
            checker_size = 5
            for x in range(0, 40, checker_size * 2):
                for y in range(0, 25, checker_size * 2):
                    painter.fillRect(x, y, checker_size, checker_size, QColor(200, 200, 200))
                    painter.fillRect(x + checker_size, y + checker_size, checker_size, checker_size,
                                     QColor(200, 200, 200))

            painter.end()
            self.color_button.setStyleSheet("")
            self.color_button.setText("None")
        else:
            # Solid color
            self.color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgb({self.current_color.red()}, {self.current_color.green()}, {self.current_color.blue()});
                    border: 1px solid #ccc;
                    border-radius: 3px;
                }}
            """)
            self.color_button.setText("")

    def update_color_label(self):
        """Update the color description label"""
        #if self.current_color.alpha() == 0:
        #    self.color_label.setText("Transparent")
        #else:
        #    rgb_text = f"RGB({self.current_color.red()}, {self.current_color.green()}, {self.current_color.blue()})"
        self.color_label.setText("")

    def select_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(self.current_color, self, f"Select {self.property_name}")
        if color.isValid():
            self.set_color(color)

    def set_color(self, color: QColor):
        """Set the current color"""
        self.current_color = color
        self.update_color_button()
        self.update_color_label()
        self.colorChanged.emit(color)

    def set_transparent(self):
        """Set color to transparent"""
        transparent_color = QColor(0, 0, 0, 0)
        self.set_color(transparent_color)

    def get_color(self) -> QColor:
        """Get the current color"""
        return self.current_color