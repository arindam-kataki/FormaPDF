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

        layout.addLayout(bg_layout)
        self.setLayout(layout)

        # Connect signals
        self.bg_color_widget.colorChanged.connect(self.on_background_changed)
        self.opacity_spinner.valueChanged.connect(self.on_background_changed)

    def on_none_toggled(self, checked: bool):
        """Handle none checkbox toggle"""
        # Block all signals to prevent circular updates
        self._block_signals(True)

        try:
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

        finally:
            # Always re-enable signals
            self._block_signals(False)

        # Manually trigger change event ONCE after all updates
        self._emit_background_change()

    def on_background_changed(self):
        """Handle background property changes from color/opacity widgets"""
        # Only update checkbox state if the change came from color/opacity widgets
        # (not from the checkbox itself)
        if hasattr(self, 'none_check') and not self.none_check.signalsBlocked():
            current_color = self.bg_color_widget.get_color()
            current_opacity = self.opacity_spinner.value()
            is_transparent = current_color.alpha() == 0 or current_opacity == 0

            # Block only the checkbox to prevent recursion
            self.none_check.blockSignals(True)
            self.none_check.setChecked(is_transparent)
            self.bg_color_widget.setEnabled(not is_transparent)
            self.opacity_spinner.setEnabled(not is_transparent)
            self.none_check.blockSignals(False)

        self._emit_background_change()

    def _emit_background_change(self):
        """Emit background change with current properties"""
        self.background_props = {
            'color': self.bg_color_widget.get_color(),
            'opacity': self.opacity_spinner.value()
        }
        self.backgroundChanged.emit(self.background_props)

    def _block_signals(self, block: bool):
        """Block or unblock signals for all background widgets to prevent feedback loops"""
        try:
            widgets_to_block = [
                self.bg_color_widget,
                self.opacity_spinner,
                self.none_check
            ]

            for widget in widgets_to_block:
                if widget and hasattr(widget, 'blockSignals'):
                    widget.blockSignals(block)

        except Exception as e:
            print(f"⚠️ Error blocking/unblocking background widget signals: {e}")

    def get_background_properties(self) -> dict:
        """Get current background properties from UI state, including None/transparent state"""

        # Get base properties from UI
        color = self.bg_color_widget.get_color()
        opacity = self.opacity_spinner.value()

        # Check if None checkbox is checked OR if color/opacity indicates transparency
        is_transparent = False
        if hasattr(self, 'none_check') and self.none_check.isChecked():
            is_transparent = True
        elif color.alpha() == 0 or opacity == 0:
            is_transparent = True

        if is_transparent:
            props = {
                'color': QColor(0, 0, 0, 0),  # Fully transparent
                'opacity': 0  # Zero opacity
            }
        else:
            props = {
                'color': color,
                'opacity': opacity
            }

        print(f"🎨 BackgroundPropertyWidget.get_background_properties(): {props} (transparent: {is_transparent})")
        return props

    def set_background_properties(self, bg_props: dict):
        """Set background properties with signal blocking to prevent loops"""
        if not bg_props:
            return

        # Block signals during bulk updates to prevent multiple change events
        self._block_signals(True)

        try:
            self.background_props = bg_props

            # Update color
            if 'color' in bg_props:
                color = bg_props['color']
                self.bg_color_widget.set_color(color)

            # Update opacity
            if 'opacity' in bg_props:
                opacity = bg_props['opacity']
                self.opacity_spinner.setValue(opacity)

            # Update None checkbox state
            if hasattr(self, 'none_check'):
                color = bg_props.get('color', QColor(255, 255, 255))
                opacity = bg_props.get('opacity', 100)
                is_transparent = color.alpha() == 0 or opacity == 0

                self.none_check.setChecked(is_transparent)
                self.bg_color_widget.setEnabled(not is_transparent)
                self.opacity_spinner.setEnabled(not is_transparent)

        except Exception as e:
            print(f"⚠️ Error setting background properties: {e}")

        finally:
            # Always re-enable signals
            self._block_signals(False)

            # Emit change signal after all updates are complete
            self.on_background_changed()

