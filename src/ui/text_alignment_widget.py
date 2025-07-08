from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QButtonGroup, QWidget, QLabel, QRadioButton


class TextAlignmentWidget(QWidget):
    """Widget for text alignment selection"""

    alignmentChanged = pyqtSignal(str)

    def __init__(self, initial_alignment: str = 'left'):
        super().__init__()
        self.current_alignment = initial_alignment
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Align:"))

        # Create radio button group
        self.button_group = QButtonGroup()

        self.left_radio = QRadioButton("Left")
        self.center_radio = QRadioButton("Center")
        self.right_radio = QRadioButton("Right")

        self.button_group.addButton(self.left_radio, 0)
        self.button_group.addButton(self.center_radio, 1)
        self.button_group.addButton(self.right_radio, 2)

        # Set initial selection
        alignment_map = {'left': self.left_radio, 'center': self.center_radio, 'right': self.right_radio}
        alignment_map.get(self.current_alignment, self.left_radio).setChecked(True)

        # Connect signals
        self.button_group.buttonClicked.connect(self.on_alignment_changed)

        layout.addWidget(self.left_radio)
        layout.addWidget(self.center_radio)
        layout.addWidget(self.right_radio)
        layout.addStretch()

        self.setLayout(layout)

    def on_alignment_changed(self, button):
        """Handle alignment change"""
        if button == self.left_radio:
            self.current_alignment = 'left'
        elif button == self.center_radio:
            self.current_alignment = 'center'
        elif button == self.right_radio:
            self.current_alignment = 'right'

        self.alignmentChanged.emit(self.current_alignment)

    def get_alignment(self) -> str:
        """Get current alignment"""
        return self.current_alignment

    def set_alignment(self, alignment: str):
        """Set alignment"""
        self.current_alignment = alignment
        alignment_map = {'left': self.left_radio, 'center': self.center_radio, 'right': self.right_radio}
        alignment_map.get(alignment, self.left_radio).setChecked(True)
