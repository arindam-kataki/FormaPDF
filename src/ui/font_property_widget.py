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
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Font family row
        family_layout = QHBoxLayout()
        family_layout.addWidget(QLabel("Font:"))

        self.family_combo = QComboBox()
        self.family_combo.addItems([
            "Arial", "Helvetica", "Times-Roman", "Courier",
            "Symbol", "ZapfDingbats", "Times-Bold", "Times-Italic",
            "Courier-Bold", "Courier-Oblique"
        ])
        self.family_combo.setCurrentText(self.font_props['family'])
        self.family_combo.currentTextChanged.connect(self.on_font_changed)

        family_layout.addWidget(self.family_combo)
        layout.addLayout(family_layout)

        # Font size row
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))

        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setValue(self.font_props['size'])
        self.size_spin.valueChanged.connect(self.on_font_changed)

        self.auto_size_check = QCheckBox("Auto")
        self.auto_size_check.toggled.connect(self.on_auto_size_toggled)

        size_layout.addWidget(self.size_spin)
        size_layout.addWidget(self.auto_size_check)
        size_layout.addStretch()
        layout.addLayout(size_layout)

        # Font style row
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Style:"))

        self.bold_check = QCheckBox("Bold")
        self.bold_check.setChecked(self.font_props['bold'])
        self.bold_check.toggled.connect(self.on_font_changed)

        self.italic_check = QCheckBox("Italic")
        self.italic_check.setChecked(self.font_props['italic'])
        self.italic_check.toggled.connect(self.on_font_changed)

        style_layout.addWidget(self.bold_check)
        style_layout.addWidget(self.italic_check)
        style_layout.addStretch()
        layout.addLayout(style_layout)

        self.setLayout(layout)

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