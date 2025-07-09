# File: src/ui/alignment_grid_widget.py
"""
3x3 Alignment Grid Widget
Provides a visual 3x3 grid for selecting both horizontal and vertical alignment
"""

from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton, QButtonGroup, QVBoxLayout, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


# Alternative implementation with text-based icons for better compatibility
class AlignmentGridWidget(QWidget):
    """3x3 grid widget using text-based icons for better compatibility"""

    alignmentChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_alignment = "middle-center"
        self.init_ui()

    def init_ui(self):
        """Initialize with text-based icons"""
        layout = QVBoxLayout()

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)

        # Text-based icons that work across all systems
        self.alignment_map = {
            (0, 0): ("top-left", "◤"),
            (0, 1): ("top-center", "▲"),
            (0, 2): ("top-right", "◥"),
            (1, 0): ("middle-left", "◀"),
            (1, 1): ("middle-center", "●"),
            (1, 2): ("middle-right", "▶"),
            (2, 0): ("bottom-left", "◣"),
            (2, 1): ("bottom-center", "▼"),
            (2, 2): ("bottom-right", "◢")
        }

        self.buttons = {}
        for (row, col), (alignment, icon) in self.alignment_map.items():
            button = QPushButton(icon)
            button.setFixedSize(28, 28)
            button.setCheckable(True)
            button.setToolTip(alignment.replace('-', ' ').title())
            button.clicked.connect(lambda checked, a=alignment: self.set_alignment(a))

            button.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ccc;
                    background-color: #f8f9fa;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #0078d4;
                }
                QPushButton:checked {
                    background-color: #0078d4;
                    color: white;
                    border-color: #0078d4;
                }
            """)

            grid_layout.addWidget(button, row, col)
            self.button_group.addButton(button)
            self.buttons[alignment] = button

        grid_widget.setLayout(grid_layout)
        layout.addWidget(grid_widget, 0, Qt.AlignmentFlag.AlignLeft)

        self.buttons[self.current_alignment].setChecked(True)
        self.setLayout(layout)
        #self.setMaximumWidth(120)
        #self.setMinimumWidth(200)

    def set_alignment(self, alignment: str):
        """Set alignment and emit signal"""
        if alignment in self.buttons:
            self.current_alignment = alignment
            self.buttons[alignment].setChecked(True)
            self.alignmentChanged.emit(alignment)

    def get_alignment(self) -> str:
        """Get current alignment"""
        return self.current_alignment

    def get_horizontal_alignment(self) -> str:
        """Extract horizontal alignment from current selection"""
        return self.current_alignment.split('-')[1]  # left, center, right

    def get_vertical_alignment(self) -> str:
        """Extract vertical alignment from current selection"""
        return self.current_alignment.split('-')[0]  # top, middle, bottom

    def get_css_alignment(self) -> dict:
        """Get CSS-style alignment properties"""
        h_align = self.get_horizontal_alignment()
        v_align = self.get_vertical_alignment()

        # Convert to CSS values
        css_horizontal = {
            'left': 'left',
            'center': 'center',
            'right': 'right'
        }.get(h_align, 'left')

        css_vertical = {
            'top': 'top',
            'middle': 'middle',
            'bottom': 'bottom'
        }.get(v_align, 'top')

        return {
            'text-align': css_horizontal,
            'vertical-align': css_vertical,
            'horizontal': h_align,
            'vertical': v_align
        }