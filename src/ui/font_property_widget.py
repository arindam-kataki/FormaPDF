from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QCheckBox, QGridLayout

from ui.alignment_grid_widget import AlignmentGridWidget
from ui.color_property_widget import ColorPropertyWidget


class FontPropertyWidget(QWidget):
    """Widget for font selection and styling"""

    fontChanged = pyqtSignal(dict)  # Emits font properties dict

    def __init__(self, initial_font_props: dict = None, show_alignment=True):
        super().__init__()
        self.show_alignment = show_alignment  # ← Add this line
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

        self.auto_size_check = QCheckBox("Auto")
        self.auto_size_check.setToolTip("Automatically size font to fit field height")
        self.auto_size_check.toggled.connect(self.on_auto_size_toggled)
        font_layout.addWidget(self.auto_size_check, 1, 2, Qt.AlignmentFlag.AlignLeft)

        # Font style checkboxes - stacked vertically
        style_label = QLabel("Style:")
        style_label.setFixedWidth(50)
        style_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Remove AlignVCenter from here
        #font_layout.addWidget(style_label, 3, 0,
        #                      Qt.AlignmentFlag.AlignVCenter)  # Put it in the middle row (3) with VCenter alignment

        # Stack checkboxes vertically
        self.bold_check = QCheckBox("Bold")
        #font_layout.addWidget(self.bold_check, 2, 1, Qt.AlignmentFlag.AlignLeft)

        self.italic_check = QCheckBox("Italic")
        #font_layout.addWidget(self.italic_check, 3, 1, Qt.AlignmentFlag.AlignLeft)

        self.underline_check = QCheckBox("Underline")
        #font_layout.addWidget(self.underline_check, 4, 1, Qt.AlignmentFlag.AlignLeft)

        layout.addLayout(font_layout)

        # Text color - aligned with other font controls (after style)
        color_label = QLabel("Color:")
        color_label.setFixedWidth(50)  # Same width as Font/Size labels
        color_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font_layout.addWidget(color_label, 5, 0)

        self.text_color_widget = ColorPropertyWidget("Color", QColor(0, 0, 0), allow_transparent=False)
        self.text_color_widget.colorChanged.connect(self.on_font_changed)  # Connect to font change handler
        font_layout.addWidget(self.text_color_widget, 5, 1, Qt.AlignmentFlag.AlignLeft)

        # Text alignment (CONDITIONAL) ← Add this section
        """
        if self.show_alignment:
            # Text alignment with label
            alignment_label = QLabel("Align:")
            alignment_label.setFixedWidth(50)  # Same width as other labels
            alignment_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            font_layout.addWidget(alignment_label, 6, 0, Qt.AlignmentFlag.AlignVCenter)

            self.alignment_widget = AlignmentGridWidget()  # Now has no internal label
            self.alignment_widget.alignmentChanged.connect(self.on_font_changed)
            font_layout.addWidget(self.alignment_widget, 6, 1, Qt.AlignmentFlag.AlignLeft)
        else:
            self.alignment_widget = None  # ← Important: Set to None when not created
        """
        if self.show_alignment:
            # Text alignment with label and dropdown
            alignment_label = QLabel("Align:")
            alignment_label.setFixedWidth(50)  # Same width as other labels
            alignment_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            font_layout.addWidget(alignment_label, 6, 0, Qt.AlignmentFlag.AlignVCenter)

            self.alignment_combo = QComboBox()
            self.alignment_combo.addItems(["Left", "Center", "Right"])
            self.alignment_combo.setCurrentText("Left")  # Default selection
            self.alignment_combo.setFixedWidth(100)  # Consistent width
            font_layout.addWidget(self.alignment_combo, 6, 1, Qt.AlignmentFlag.AlignLeft)
        else:
            self.alignment_combo = None  # ← Important: Set to None when not created

        self.setLayout(layout)

        # Connect signals
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        self.size_spinner.valueChanged.connect(self.on_font_changed)
        self.bold_check.toggled.connect(self.on_font_changed)
        self.italic_check.toggled.connect(self.on_font_changed)
        self.underline_check.toggled.connect(self.on_font_changed)
        self.alignment_combo.currentTextChanged.connect(self.on_font_changed)

    def on_auto_size_toggled(self, checked: bool):
        """Handle auto-size toggle"""
        self.size_spinner.setEnabled(not checked)
        self.on_font_changed()

    def on_font_changed(self):
        """Handle font property changes"""
        self.font_props = {
            'family': self.font_combo.currentText(),
            'size': self.size_spinner.value() if not self.auto_size_check.isChecked() else 'auto',
            'bold': self.bold_check.isChecked(),
            'italic': self.italic_check.isChecked(),
            'underline': self.underline_check.isChecked(),
            'alignment': self.alignment_combo.currentText()

        }
        self.fontChanged.emit(self.font_props)

    def get_font_properties(self) -> dict:
        """Get current font properties including optional alignment"""
        props = {
            'family': self.font_combo.currentText(),
            'size': self.size_spinner.value() if not self.auto_size_check.isChecked() else 'auto',
            'bold': self.bold_check.isChecked(),
            'italic': self.italic_check.isChecked(),
            'underline': self.underline_check.isChecked(),
            'alignment': self.alignment_combo.currentText(),
            'color': self.text_color_widget.get_color()
        }

        # Only include alignment if widget exists - return simple string
        if self.alignment_combo:
            props['alignment'] = self.alignment_combo.currentText()  # Just "top-left"

        return props

    def _block_signals(self, block: bool):
        """Block or unblock signals for all font widgets to prevent feedback loops"""
        try:
            widgets_to_block = [
                self.font_combo,
                self.size_spinner,
                self.bold_check,
                self.italic_check,
                self.underline_check,
                self.text_color_widget
            ]

            for widget in widgets_to_block:
                if widget and hasattr(widget, 'blockSignals'):
                    widget.blockSignals(block)

            # Block alignment widget signals if it exists
            if self.alignment_combo and hasattr(self.alignment_combo, 'blockSignals'):
                self.alignment_combo.blockSignals(block)

        except Exception as e:
            print(f"⚠️ Error blocking/unblocking signals: {e}")

    def set_font_properties(self, props: dict):
        """Set font properties from dictionary with signal blocking to prevent loops"""
        if not props:
            return

        # Block signals during bulk updates to prevent multiple change events
        self._block_signals(True)

        try:
            # Font family
            if 'family' in props:
                family = props['family']
                if family:  # Only set if not empty
                    index = self.font_combo.findText(family)
                    if index >= 0:
                        self.font_combo.setCurrentIndex(index)
                    else:
                        # Add custom font if not in list
                        self.font_combo.addItem(family)
                        self.font_combo.setCurrentText(family)

            # Font size
            if 'size' in props:
                size = props['size']
                if size == 'auto':
                    # Set auto-size checkbox and disable spinner
                    self.auto_size_check.setChecked(True)
                    self.size_spinner.setEnabled(False)
                    # Keep current spinner value for display
                else:
                    # Set specific size value
                    self.auto_size_check.setChecked(False)
                    self.size_spinner.setEnabled(True)
                    if isinstance(size, (int, float)) and 6 <= size <= 72:
                        self.size_spinner.setValue(int(size))

            # Font style properties
            if 'bold' in props:
                self.bold_check.setChecked(bool(props['bold']))

            if 'italic' in props:
                self.italic_check.setChecked(bool(props['italic']))

            if 'underline' in props:
                self.underline_check.setChecked(bool(props['underline']))

            # Text color
            if 'color' in props:
                color = props['color']
                if color:
                    # Handle different color formats
                    if isinstance(color, QColor):
                        self.text_color_widget.set_color(color)
                    elif isinstance(color, str):
                        # Handle hex colors like "#FF0000"
                        if color.startswith('#') and len(color) == 7:
                            qcolor = QColor(color)
                            if qcolor.isValid():
                                self.text_color_widget.set_color(qcolor)
                    elif isinstance(color, (list, tuple)) and len(color) >= 3:
                        # Handle RGB tuples like (255, 0, 0)
                        r, g, b = color[0], color[1], color[2]
                        a = color[3] if len(color) > 3 else 255
                        qcolor = QColor(r, g, b, a)
                        self.text_color_widget.set_color(qcolor)

            # Text alignment (only if widget exists) - simplified!
            if self.alignment_combo and 'alignment' in props:
                alignment = props['alignment']
                if isinstance(alignment, str):
                    self.alignment_combo.setCurrentText(alignment)  # Just pass the string

            # Update internal font_props dictionary
            self.font_props.update(props)

        except Exception as e:
            print(f"⚠️ Error setting font properties: {e}")

        finally:
            # Always re-enable signals
            self._block_signals(False)

            # Emit change signal after all updates are complete
            self.on_font_changed()

    def reset_to_defaults(self):
        """Reset font properties to default values"""
        default_props = {
            'family': 'Arial',
            'size': 12,
            'bold': False,
            'italic': False,
            'underline': False,
            'color': QColor(0, 0, 0),  # Black
            'alignment': 'Left'
        }

        # Add default alignment if widget exists
        if self.alignment_combo:
            default_props['alignment'] = 'Left'

        self.set_font_properties(default_props)

    def validate_font_properties(self, props: dict) -> tuple[bool, str]:
        """Validate font properties before setting them"""
        if not isinstance(props, dict):
            return False, "Properties must be a dictionary"

        # Validate font size
        if 'size' in props:
            size = props['size']
            if not isinstance(size, (int, float)) or not (6 <= size <= 72):
                return False, "Font size must be between 6 and 72"

        # Validate color format
        if 'color' in props:
            color = props['color']
            if isinstance(color, str):
                if not (color.startswith('#') and len(color) == 7):
                    return False, "Color string must be in #RRGGBB format"
            elif isinstance(color, (list, tuple)):
                if len(color) < 3 or not all(0 <= c <= 255 for c in color[:3]):
                    return False, "RGB color values must be between 0 and 255"

        # Validate alignment - simplified!
        if 'alignment' in props and self.alignment_combo:
            alignment = props['alignment']
            if not isinstance(alignment, str):
                return False, "Alignment must be a string"

            valid_alignments = [
                'left', 'center', 'right',
                'top-left', 'top-center', 'top-right',
                'middle-left', 'middle-center', 'middle-right',
                'bottom-left', 'bottom-center', 'bottom-right'
            ]
            if alignment not in valid_alignments:
                return False, f"Invalid alignment: {alignment}. Must be one of: {valid_alignments}"

        return True, "Valid"

    def get_font_qfont(self) -> QFont:
        """Get a QFont object from current font properties"""
        qfont = QFont()
        qfont.setFamily(self.font_combo.currentText())
        qfont.setPointSize(self.size_spinner.value())
        qfont.setBold(self.bold_check.isChecked())
        qfont.setItalic(self.italic_check.isChecked())
        qfont.setUnderline(self.underline_check.isChecked())
        return qfont

    def set_from_qfont(self, qfont: QFont):
        """Set font properties from a QFont object"""
        props = {
            'family': qfont.family(),
            'size': qfont.pointSize(),
            'bold': qfont.bold(),
            'italic': qfont.italic(),
            'underline': qfont.underline()
        }
        self.set_font_properties(props)