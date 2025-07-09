from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QCheckBox, QGridLayout


class FontPropertyWidget(QWidget):
    """Widget for font selection and styling"""

    fontChanged = pyqtSignal(dict)  # Emits font properties dict

    def __init__(self, initial_font_props: dict = None):
        super().__init__()
        self.font_props = initial_font_props or {
            'family': 'Arial',
            'size': 12,
            'bold': False,
            'italic': False
        }
        self.init_ui()

    def init_ui(self):
        """Initialize font property UI with consistent styling"""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Font family row
        font_layout = QGridLayout()
        font_layout.setHorizontalSpacing(8)  # Same as position controls
        font_layout.setVerticalSpacing(5)

        # Font family
        font_label = QLabel("Font:")
        font_label.setFixedWidth(50)  # Same width as position labels
        font_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font_layout.addWidget(font_label, 0, 0)

        self.font_combo = QComboBox()
        self.font_combo.setMaximumWidth(120)  # Reasonable width for font names
        self.font_combo.setMinimumWidth(120)
        self.font_combo.addItems(['Arial', 'Times New Roman', 'Courier New', 'Helvetica', 'Georgia'])
        font_layout.addWidget(self.font_combo, 0, 1, Qt.AlignmentFlag.AlignLeft)

        # Font size
        size_label = QLabel("Size:")
        size_label.setFixedWidth(50)  # Same width as position labels
        size_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font_layout.addWidget(size_label, 1, 0)

        self.size_spinner = QSpinBox()
        self.size_spinner.setRange(8, 72)
        self.size_spinner.setValue(12)
        self.size_spinner.setMaximumWidth(50)  # Same as position spinners
        self.size_spinner.setMinimumWidth(50)
        font_layout.addWidget(self.size_spinner, 1, 1, Qt.AlignmentFlag.AlignLeft)

        # Font style checkboxes - stacked vertically
        style_label = QLabel("Style:")
        style_label.setFixedWidth(50)
        style_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Remove AlignVCenter from here
        font_layout.addWidget(style_label, 3, 0,
                              Qt.AlignmentFlag.AlignVCenter)  # Put it in the middle row (3) with VCenter alignment

        # Stack checkboxes vertically
        self.bold_check = QCheckBox("Bold")
        font_layout.addWidget(self.bold_check, 2, 1, Qt.AlignmentFlag.AlignLeft)

        self.italic_check = QCheckBox("Italic")
        font_layout.addWidget(self.italic_check, 3, 1, Qt.AlignmentFlag.AlignLeft)

        self.underline_check = QCheckBox("Underline")
        font_layout.addWidget(self.underline_check, 4, 1, Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(font_layout)
        self.setLayout(layout)

        # Connect signals
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        self.size_spinner.valueChanged.connect(self.on_font_changed)
        self.bold_check.toggled.connect(self.on_font_changed)
        self.italic_check.toggled.connect(self.on_font_changed)
        self.underline_check.toggled.connect(self.on_font_changed)

    def on_auto_size_toggled(self, checked: bool):
        """Handle auto-size toggle"""
        self.size_spin.setEnabled(not checked)
        self.on_font_changed()

    def on_font_changed(self):
        """Handle font property changes"""
        self.font_props = {
            'family': self.family_combo.currentText(),
            'size': self.size_spin.value() if not self.auto_size_check.isChecked() else 'auto',
            'bold': self.bold_check.isChecked(),
            'italic': self.italic_check.isChecked()
        }
        self.fontChanged.emit(self.font_props)

    def get_font_properties(self) -> dict:
        """Get current font properties"""
        return self.font_props.copy()

    def set_font_properties(self, font_props: dict):
        """Set font properties"""
        self.font_props = font_props

        # Update UI
        self.family_combo.setCurrentText(font_props.get('family', 'Arial'))

        if font_props.get('size') == 'auto':
            self.auto_size_check.setChecked(True)
            self.size_spin.setEnabled(False)
        else:
            self.size_spin.setValue(int(font_props.get('size', 12)))
            self.auto_size_check.setChecked(False)

        self.bold_check.setChecked(font_props.get('bold', False))
        self.italic_check.setChecked(font_props.get('italic', False))