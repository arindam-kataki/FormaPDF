#!/usr/bin/env python3
"""
GridControlPopup Final v3 - Complete draggable floating grid control window
Provides a modern, non-modal popup for comprehensive grid settings with snap functionality
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QSpinBox, QPushButton, QColorDialog,
    QFrame, QApplication
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QPalette, QFont, QMouseEvent, QPainter, QPen, QBrush


class GridControlPopup(QWidget):
    """
    Draggable, floating grid control window with snap functionality

    Features:
    - Stays on top but non-modal
    - Remembers position between sessions
    - Live preview as you adjust settings
    - Clean, compact design with rounded corners
    - Smooth show/hide animations
    - Snap to grid functionality
    """

    # Signals for communicating with main application
    grid_visibility_changed = pyqtSignal(bool)
    grid_spacing_changed = pyqtSignal(int)
    grid_offset_changed = pyqtSignal(int, int)  # x, y
    grid_color_changed = pyqtSignal(QColor)
    grid_reset_requested = pyqtSignal()
    snap_to_grid_changed = pyqtSignal(bool)  # Snap to grid signal
    sync_with_zoom_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Grid state
        self.grid_enabled = False
        self.snap_enabled = False
        self.sync_with_zoom_enabled = False
        self.grid_spacing = 20
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self.grid_color = QColor(200, 200, 200, 128)  # Light gray with transparency

        # Dragging state
        self.dragging = False
        self.drag_start_position = QPoint()

        # Animation
        self.fade_animation = None

        self.setup_window()
        self.setup_ui()
        self.setup_styling()
        self.setup_connections()

    def setup_window(self):
        """Configure window properties for floating popup behavior"""
        # Window flags for floating, draggable popup
        self.setWindowFlags(
            Qt.WindowType.Tool |  # Tool window (smaller title bar)
            Qt.WindowType.WindowStaysOnTopHint |  # Always on top
            Qt.WindowType.FramelessWindowHint  # No system title bar (custom styling)
        )

        # Set size and make it non-modal
        self.setFixedSize(280, 220)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        # Set window title for taskbar
        self.setWindowTitle("Grid Controls")

    def setup_ui(self):
        """Create the compact grid control interface"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 8, 12, 12)
        main_layout.setSpacing(8)

        # Title bar with drag handle
        self.create_title_bar(main_layout)

        # Grid visibility toggle
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(self.grid_enabled)
        main_layout.addWidget(self.grid_checkbox)

        # Snap to grid toggle (NOT indented)
        self.snap_checkbox = QCheckBox("Snap to Grid")
        self.snap_checkbox.setChecked(self.snap_enabled)
        self.snap_checkbox.setEnabled(self.grid_enabled)  # Only enabled when grid is visible
        main_layout.addWidget(self.snap_checkbox)

        self.sync_zoom_checkbox = QCheckBox("Scale with zoom")
        self.sync_zoom_checkbox.setChecked(self.sync_with_zoom_enabled)
        self.sync_zoom_checkbox.setToolTip("When checked, grid scales with PDF zoom level")
        layout.addWidget(self.sync_zoom_checkbox)

        # Spacing control (same pattern for all three controls)
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("Spacing:"))

        self.spacing_spinbox = QSpinBox()
        self.spacing_spinbox.setRange(5, 100)
        self.spacing_spinbox.setValue(self.grid_spacing)
        self.spacing_spinbox.setSuffix("px")
        self.spacing_spinbox.setMinimumWidth(70)
        spacing_layout.addWidget(self.spacing_spinbox)
        spacing_layout.addStretch()

        main_layout.addLayout(spacing_layout)

        # X Offset control (SAME PATTERN as spacing)
        x_offset_layout = QHBoxLayout()
        x_offset_layout.addWidget(QLabel("X Offset:"))

        self.offset_x_spinbox = QSpinBox()
        max_offset = self.grid_spacing - 1
        self.offset_x_spinbox.setRange(-max_offset, max_offset)
        self.offset_x_spinbox.setValue(self.grid_offset_x)
        self.offset_x_spinbox.setSuffix("px")
        self.offset_x_spinbox.setMinimumWidth(70)
        x_offset_layout.addWidget(self.offset_x_spinbox)
        x_offset_layout.addStretch()

        main_layout.addLayout(x_offset_layout)

        # Y Offset control (SAME PATTERN as spacing)
        y_offset_layout = QHBoxLayout()
        y_offset_layout.addWidget(QLabel("Y Offset:"))

        self.offset_y_spinbox = QSpinBox()
        max_offset = self.grid_spacing - 1
        self.offset_y_spinbox.setRange(-max_offset, max_offset)
        self.offset_y_spinbox.setValue(self.grid_offset_y)
        self.offset_y_spinbox.setSuffix("px")
        self.offset_y_spinbox.setMinimumWidth(70)
        y_offset_layout.addWidget(self.offset_y_spinbox)
        y_offset_layout.addStretch()

        main_layout.addLayout(y_offset_layout)

        # Color and reset controls
        bottom_layout = QHBoxLayout()

        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 25)
        self.update_color_button()
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedWidth(60)

        bottom_layout.addLayout(color_layout)
        bottom_layout.addWidget(self.reset_button)

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def update_offset_ranges(self):
        """Update offset spinbox ranges based on current spacing"""
        max_offset = self.grid_spacing - 1

        # Store current values
        current_x = self.offset_x_spinbox.value()
        current_y = self.offset_y_spinbox.value()

        # Update ranges
        self.offset_x_spinbox.setRange(-max_offset, max_offset)
        self.offset_y_spinbox.setRange(-max_offset, max_offset)

        # Clamp current values to new range if needed
        if current_x > max_offset:
            self.offset_x_spinbox.setValue(max_offset)
            self.grid_offset_x = max_offset
        elif current_x < -max_offset:
            self.offset_x_spinbox.setValue(-max_offset)
            self.grid_offset_x = -max_offset

        if current_y > max_offset:
            self.offset_y_spinbox.setValue(max_offset)
            self.grid_offset_y = max_offset
        elif current_y < -max_offset:
            self.offset_y_spinbox.setValue(-max_offset)
            self.grid_offset_y = -max_offset

        # Emit offset change if values were clamped
        if (current_x != self.offset_x_spinbox.value() or
                current_y != self.offset_y_spinbox.value()):
            self.grid_offset_changed.emit(self.grid_offset_x, self.grid_offset_y)

    def create_title_bar(self, main_layout):
        """Create custom title bar for dragging"""
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        # Title with drag handle indicator
        self.title_label = QLabel("📐 Grid Controls")
        self.title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #333;
                padding: 4px 0px;
            }
        """)
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        # Close button
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #666;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
                color: white;
            }
        """)
        title_layout.addWidget(self.close_button)

        main_layout.addLayout(title_layout)

        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("QFrame { color: #ddd; }")
        main_layout.addWidget(line)

    def setup_styling(self):
        """Apply modern styling with rounded corners and shadows"""
        self.setStyleSheet("""
            GridControlPopup {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }

            QLabel {
                color: #495057;
                font-size: 12px;
            }

            QCheckBox {
                font-size: 13px;
                font-weight: 500;
                color: #212529;
            }

            QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 2px 6px;
                background-color: white;
                font-size: 11px;
            }

            QSpinBox:focus {
                border-color: #0d6efd;
                outline: none;
            }

            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #5c636a;
            }

            QPushButton:pressed {
                background-color: #495057;
            }
        """)

    def setup_connections(self):
        """Connect all signals and slots"""
        # Grid controls
        self.grid_checkbox.toggled.connect(self.on_grid_visibility_changed)
        self.snap_checkbox.toggled.connect(self.on_snap_to_grid_changed)
        self.sync_zoom_checkbox.toggled.connect(self.on_sync_zoom_changed)
        self.spacing_spinbox.valueChanged.connect(self.on_spacing_changed)
        self.offset_x_spinbox.valueChanged.connect(self.on_offset_changed)
        self.offset_y_spinbox.valueChanged.connect(self.on_offset_changed)
        self.color_button.clicked.connect(self.on_color_button_clicked)
        self.reset_button.clicked.connect(self.on_reset_clicked)
        self.close_button.clicked.connect(self.hide_with_animation)

    def update_color_button(self):
        """Update color button appearance to show current color"""
        color = self.grid_color
        self.color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()});
                border: 2px solid #ccc;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #999;
            }}
        """)

    # =========================
    # EVENT HANDLERS
    # =========================

    def on_grid_visibility_changed(self, enabled: bool):
        """Handle grid visibility toggle"""
        self.grid_enabled = enabled
        self.grid_visibility_changed.emit(enabled)

        # Enable/disable snap based on grid visibility
        self.snap_checkbox.setEnabled(enabled)
        if not enabled:
            self.snap_checkbox.setChecked(False)
            self.snap_enabled = False

        # Enable/disable other controls based on grid visibility
        self.spacing_spinbox.setEnabled(enabled)
        self.offset_x_spinbox.setEnabled(enabled)
        self.offset_y_spinbox.setEnabled(enabled)
        self.color_button.setEnabled(enabled)

    def on_snap_to_grid_changed(self, enabled: bool):
        """Handle snap to grid toggle"""
        self.snap_enabled = enabled
        self.snap_to_grid_changed.emit(enabled)

    def on_sync_zoom_changed(self, checked: bool):
        """Handle sync with zoom checkbox change"""
        self.sync_with_zoom_enabled = checked
        self.sync_with_zoom_changed.emit(checked)
        print(f"📐 Sync with zoom: {'enabled' if checked else 'disabled'}")

    def on_spacing_changed(self, value: int):
        """Handle spacing changes"""
        self.grid_spacing = value

        # Update offset ranges when spacing changes
        self.update_offset_ranges()

        self.grid_spacing_changed.emit(value)

    def on_offset_changed(self):
        """Handle offset changes"""
        self.grid_offset_x = self.offset_x_spinbox.value()
        self.grid_offset_y = self.offset_y_spinbox.value()
        self.grid_offset_changed.emit(self.grid_offset_x, self.grid_offset_y)

    def on_color_button_clicked(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(
            self.grid_color,
            self,
            "Select Grid Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )

        if color.isValid():
            self.grid_color = color
            self.update_color_button()
            self.grid_color_changed.emit(color)

    def update_sync_with_zoom(self, sync_enabled: bool):
        """Update sync with zoom checkbox from external source"""
        if self.sync_with_zoom_enabled != sync_enabled:
            self.sync_with_zoom_enabled = sync_enabled
            self.sync_zoom_checkbox.setChecked(sync_enabled)

    def update_offset_ranges(self):
        """Update offset spinbox ranges based on current spacing"""
        max_offset = self.grid_spacing - 1

        # Store current values
        current_x = self.offset_x_spinbox.value()
        current_y = self.offset_y_spinbox.value()

        # Update ranges
        self.offset_x_spinbox.setRange(-max_offset, max_offset)
        self.offset_y_spinbox.setRange(-max_offset, max_offset)

        # Clamp current values to new range if needed
        if current_x > max_offset:
            self.offset_x_spinbox.setValue(max_offset)
            self.grid_offset_x = max_offset
        elif current_x < -max_offset:
            self.offset_x_spinbox.setValue(-max_offset)
            self.grid_offset_x = -max_offset

        if current_y > max_offset:
            self.offset_y_spinbox.setValue(max_offset)
            self.grid_offset_y = max_offset
        elif current_y < -max_offset:
            self.offset_y_spinbox.setValue(-max_offset)
            self.grid_offset_y = -max_offset

        # Emit offset change if values were clamped
        if (current_x != self.offset_x_spinbox.value() or
                current_y != self.offset_y_spinbox.value()):
            self.grid_offset_changed.emit(self.grid_offset_x, self.grid_offset_y)

    def on_reset_clicked(self):
        """Reset all grid settings to defaults"""
        self.grid_spacing = 20
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self.grid_color = QColor(200, 200, 200, 128)
        self.snap_enabled = False

        # Update UI
        self.spacing_spinbox.setValue(self.grid_spacing)
        self.update_offset_ranges()  # Update ranges before setting values
        self.offset_x_spinbox.setValue(self.grid_offset_x)
        self.offset_y_spinbox.setValue(self.grid_offset_y)
        self.update_color_button()

        # Emit signals
        self.grid_spacing_changed.emit(self.grid_spacing)
        self.grid_offset_changed.emit(self.grid_offset_x, self.grid_offset_y)
        self.grid_color_changed.emit(self.grid_color)
        self.snap_to_grid_changed.emit(self.snap_enabled)
        self.grid_reset_requested.emit()

    # =========================
    # DRAGGING FUNCTIONALITY
    # =========================

    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging when clicking on title area"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Only allow dragging from title area (top 30 pixels)
            if event.pos().y() <= 30:
                self.dragging = True
                self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle dragging movement"""
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            # Move window to new position
            new_pos = event.globalPosition().toPoint() - self.drag_start_position
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop dragging"""
        self.dragging = False
        super().mouseReleaseEvent(event)

    # =========================
    # SHOW/HIDE WITH ANIMATION
    # =========================

    def show_with_animation(self, near_point: QPoint = None):
        """Show popup with smooth fade-in animation"""
        if near_point:
            self.position_near_point(near_point)

        # Ensure popup is within screen bounds
        self.ensure_on_screen()

        # Show immediately
        self.show()
        self.raise_()
        self.activateWindow()

        # Optional: Add fade-in animation
        # self.setWindowOpacity(0.0)
        # self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        # self.fade_animation.setDuration(200)
        # self.fade_animation.setStartValue(0.0)
        # self.fade_animation.setEndValue(1.0)
        # self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        # self.fade_animation.start()

    def hide_with_animation(self):
        """Hide popup with smooth fade-out animation"""
        # For now, just hide immediately
        # Future: Add fade-out animation
        self.hide()

    def position_near_point(self, point: QPoint):
        """Position popup near the given point (e.g., toolbar button)"""
        # Position below the point with some offset
        x = point.x() - self.width() // 2
        y = point.y() + 30  # Below the toolbar

        self.move(x, y)

    def ensure_on_screen(self):
        """Ensure popup stays within screen boundaries"""
        screen = QApplication.primaryScreen().geometry()
        popup_rect = self.geometry()

        # Adjust horizontal position
        if popup_rect.right() > screen.right():
            popup_rect.moveRight(screen.right() - 10)
        if popup_rect.left() < screen.left():
            popup_rect.moveLeft(screen.left() + 10)

        # Adjust vertical position
        if popup_rect.bottom() > screen.bottom():
            popup_rect.moveBottom(screen.bottom() - 10)
        if popup_rect.top() < screen.top():
            popup_rect.moveTop(screen.top() + 10)

        self.setGeometry(popup_rect)

    # =========================
    # PUBLIC API
    # =========================

    def set_grid_state(self, enabled: bool, spacing: int = 20,
                       offset_x: int = 0, offset_y: int = 0,
                       color: QColor = None, snap_enabled: bool = False):
        """Update grid state from external source"""
        self.grid_enabled = enabled
        self.snap_enabled = snap_enabled
        self.grid_spacing = spacing
        self.grid_offset_x = offset_x
        self.grid_offset_y = offset_y

        if color:
            self.grid_color = color

        # Update UI controls
        self.grid_checkbox.setChecked(enabled)
        self.snap_checkbox.setChecked(snap_enabled)
        self.spacing_spinbox.setValue(spacing)
        self.update_offset_ranges()  # Update ranges after setting spacing
        self.offset_x_spinbox.setValue(offset_x)
        self.offset_y_spinbox.setValue(offset_y)
        self.update_color_button()

    def get_grid_state(self):
        """Get current grid configuration"""
        return {
            'enabled': self.grid_enabled,
            'snap_enabled': self.snap_enabled,
            'spacing': self.grid_spacing,
            'offset_x': self.grid_offset_x,
            'offset_y': self.grid_offset_y,
            'color': self.grid_color
        }


# =========================
# DEMO/TEST APPLICATION
# =========================

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Demo popup
    popup = GridControlPopup()

    # Connect signals for demo
    popup.grid_visibility_changed.connect(
        lambda enabled: print(f"Grid visibility: {enabled}")
    )
    popup.snap_to_grid_changed.connect(
        lambda enabled: print(f"Snap to grid: {enabled}")
    )
    popup.grid_spacing_changed.connect(
        lambda spacing: print(f"Grid spacing: {spacing}px")
    )
    popup.grid_offset_changed.connect(
        lambda x, y: print(f"Grid offset: ({x}, {y})")
    )
    popup.grid_color_changed.connect(
        lambda color: print(f"Grid color: {color.name()}")
    )
    popup.grid_reset_requested.connect(
        lambda: print("Grid reset requested")
    )

    # Show popup
    popup.show_with_animation()

    sys.exit(app.exec())