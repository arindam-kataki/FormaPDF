"""
Field Palette Widget
Provides UI for selecting and creating different types of form fields
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QFrame, QToolTip, QGroupBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor


class FieldButton(QPushButton):
    """Custom button for field types with icons and descriptions"""

    def __init__(self, field_type: str, display_name: str, icon: str, description: str):
        super().__init__()
        self.field_type = field_type
        self.display_name = display_name
        self.description = description

        # Set button properties
        self.setText(f"{icon} {display_name}")
        self.setMinimumHeight(40)
        self.setToolTip(description)

        # Style the button
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)


class FieldPalette(QWidget):
    """Widget containing field type buttons for creating form fields"""

    fieldRequested = pyqtSignal(str)  # field_type

    def __init__(self):
        super().__init__()
        self.field_buttons = {}
        self.selected_field_type = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(5)

        # Title
        title = QLabel("Form Fields")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel("Click to add fields to the PDF:")
        instructions.setFont(QFont("Arial", 9))
        instructions.setStyleSheet("color: #6c757d; margin-bottom: 5px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #dee2e6;")
        layout.addWidget(separator)

        # Field type definitions
        field_types = [
            ("text", "Text Field", "📝", "Single or multi-line text input"),
            ("checkbox", "Checkbox", "☑️", "Boolean checkbox for yes/no options"),
            ("radio", "Radio Button", "🔘", "Single selection from multiple options"),
            ("dropdown", "Dropdown", "📋", "Dropdown list with multiple options"),
            ("signature", "Signature", "✏️", "Digital signature capture area"),
            ("date", "Date Field", "📅", "Date picker input field"),
            ("button", "Button", "🔘", "Clickable action button"),
            ("number", "Number Field", "🔢", "Numeric input field")
        ]

        # Create buttons for each field type
        self.field_buttons = {}
        for field_type, display_name, icon, description in field_types:
            button = FieldButton(field_type, display_name, icon, description)
            # REPLACE the clicked.connect line with this:
            button.clicked.connect(lambda checked, ft=field_type: self._on_field_button_clicked(ft))
            layout.addWidget(button)
            self.field_buttons[field_type] = button

        # Add some spacing
        layout.addStretch()

        # Tips section
        tips_group = QGroupBox("💡 Tips")
        tips_layout = QVBoxLayout()

        tips = [
            "Drag fields to move them",
            "Drag handles to resize",
            "Use arrow keys for precision",
            "Ctrl+D to duplicate",
            "Delete key to remove"
        ]

        for tip in tips:
            tip_label = QLabel(f"• {tip}")
            tip_label.setFont(QFont("Arial", 8))
            tip_label.setStyleSheet("color: #6c757d;")
            tips_layout.addWidget(tip_label)

        tips_group.setLayout(tips_layout)
        tips_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        layout.addWidget(tips_group)

        self.setLayout(layout)

    def _on_field_button_clicked(self, field_type):
        """Handle field button click - track selection and emit signal"""
        print(f"🎯 Field button clicked: {field_type}")

        # Clear previous highlights
        self.clear_highlights()

        # Highlight selected button
        self.highlight_field_type(field_type, True)

        # Store the selected field type
        self.selected_field_type = field_type

        # Notify canvas about selection (if possible)
        try:
            # Try to find main window and notify canvas
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'pdf_canvas'):
                if hasattr(main_window.pdf_canvas, 'set_selected_field_type'):
                    main_window.pdf_canvas.set_selected_field_type(field_type)
                    print(f"✅ Notified canvas of selection: {field_type}")
        except Exception as e:
            print(f"⚠️ Could not notify canvas: {e}")

        # Emit the original signal for backward compatibility
        self.fieldRequested.emit(field_type)

    # 4. ADD THIS HELPER METHOD to FieldPalette class:
    def _get_main_window(self):
        """Get the main window safely"""
        try:
            widget = self
            while widget.parent():
                widget = widget.parent()
                # Look for main window characteristics
                if (hasattr(widget, 'field_palette') and
                        hasattr(widget, 'pdf_canvas')):
                    return widget
            return None
        except Exception as e:
            print(f"⚠️ Error finding main window: {e}")
            return None

    # 5. ADD THIS METHOD to FieldPalette class (for getting selected type):
    def get_selected_field_type(self):
        """Get the currently selected field type"""
        return self.selected_field_type

    # 6. ADD THIS METHOD to FieldPalette class (for external selection):
    def set_selected_field_type(self, field_type):
        """Set the selected field type externally"""
        if field_type in self.field_buttons:
            self._on_field_button_clicked(field_type)

    # 7. MAKE SURE THESE METHODS EXIST in FieldPalette class:
    # (They should already be there based on your project files)
    def clear_highlights(self):
        """Clear all field type highlights"""
        if hasattr(self, 'field_buttons'):
            for field_type in self.field_buttons:
                self.highlight_field_type(field_type, False)

    def highlight_field_type(self, field_type: str, highlight: bool = True):
        """Highlight a specific field type (e.g., when selected)"""
        if not hasattr(self, 'field_buttons') or field_type not in self.field_buttons:
            return

        button = self.field_buttons[field_type]

        if highlight:
            # Apply highlighted style
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 2px solid #0078d4;
                    border-radius: 4px;
                    background-color: #e3f2fd;
                    color: #1565c0;
                }
                QPushButton:hover {
                    background-color: #bbdefb;
                    border-color: #1976d2;
                }
            """)
        else:
            # Reset to default style
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #0078d4;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)

    def set_field_enabled(self, field_type: str, enabled: bool):
        """Enable or disable a specific field type button"""
        if field_type in self.field_buttons:
            self.field_buttons[field_type].setEnabled(enabled)

    def highlight_field_type(self, field_type: str, highlight: bool = True):
        """Highlight a specific field type (e.g., when selected)"""
        if field_type in self.field_buttons:
            button = self.field_buttons[field_type]
            if highlight:
                button.setStyleSheet(button.styleSheet() + """
                    QPushButton {
                        background-color: #e3f2fd;
                        border-color: #0078d4;
                        border-width: 2px;
                    }
                """)
            else:
                # Reset to default style
                button.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 8px 12px;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        background-color: #f8f9fa;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                        border-color: #0078d4;
                    }
                    QPushButton:pressed {
                        background-color: #dee2e6;
                    }
                """)

    def clear_highlights(self):
        """Clear all field type highlights"""
        for field_type in self.field_buttons:
            self.highlight_field_type(field_type, False)

    def set_field_selected(self, has_selection: bool):
        """Update UI based on whether a field is selected (for enhanced palette)"""
        # This method is called by the enhanced version
        pass
    def clear_highlights(self):
        """Clear all field type highlights"""
        if hasattr(self, 'field_buttons'):
            for field_type in self.field_buttons:
                self.highlight_field_type(field_type, False)

    def highlight_field_type(self, field_type: str, highlight: bool = True):
        """Highlight a specific field type (e.g., when selected)"""
        if not hasattr(self, 'field_buttons') or field_type not in self.field_buttons:
            return

        button = self.field_buttons[field_type]

        if highlight:
            # Apply highlighted style
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 2px solid #0078d4;
                    border-radius: 4px;
                    background-color: #e3f2fd;
                    color: #0078d4;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #bbdefb;
                    border-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #90caf9;
                }
            """)
        else:
            # Reset to default style
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #0078d4;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)


class ScrollableFieldPalette(QWidget):
    """Scrollable field palette that doesn't get squished in small windows"""

    fieldRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.selected_field_type = None
        self.field_buttons = {}
        self.init_scrollable_ui()

    def init_scrollable_ui(self):
        """Initialize scrollable UI"""
        # Main layout for the palette widget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumWidth(200)  # Ensure minimum width

        # Create the scrollable content widget
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(5)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        # Add field type buttons to scrollable content
        self._add_field_buttons(scroll_layout)

        # Add stretch to keep buttons at top
        scroll_layout.addStretch()

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        # Apply styles
        self.apply_scrollable_styles()

    def _add_field_buttons(self, layout):
        """Add field type buttons to layout"""
        field_types = [
            ("📝 Text Field", "text"),
            ("✅ Checkbox", "checkbox"),
            ("🔘 Radio Button", "radio"),
            ("📋 Dropdown", "dropdown"),
            ("🔢 Number", "number"),
            ("📅 Date", "date"),
            ("📧 Email", "email"),
            ("🔒 Password", "password"),
            ("📄 Textarea", "textarea"),
            ("🔗 URL", "url"),
            ("📞 Phone", "phone"),
            ("🖊️ Signature", "signature"),
            ("🔘 Button", "button"),
            ("📎 File Upload", "file"),
            ("🏷️ Label", "label")
        ]

        for display_name, field_type in field_types:
            button = QPushButton(display_name)
            button.setMinimumHeight(35)  # Ensure buttons aren't too small
            button.clicked.connect(lambda checked, ft=field_type: self._on_field_button_clicked(ft))
            layout.addWidget(button)
            self.field_buttons[field_type] = button

    def apply_scrollable_styles(self):
        """Apply styles for scrollable palette"""
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }

            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #ffffff;
                font-size: 11px;
                min-height: 30px;
            }

            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #0078d4;
            }

            QPushButton:pressed {
                background-color: #dee2e6;
            }

            /* Highlighted (selected) button style */
            QPushButton.selected {
                border: 2px solid #0078d4;
                background-color: #e3f2fd;
                color: #1565c0;
                font-weight: bold;
            }

            QPushButton.selected:hover {
                background-color: #bbdefb;
                border-color: #1976d2;
            }
        """)

    def _on_field_button_clicked(self, field_type):
        """🔧 ENHANCED: Handle field button click with auto-reset logic"""
        print(f"🎯 Field button clicked: {field_type}")

        # Clear previous highlights
        self.clear_highlights()

        # Highlight selected button
        self.highlight_field_type(field_type, True)

        # Store the selected field type
        self.selected_field_type = field_type

        # Notify main window/canvas about selection
        self._notify_canvas_selection(field_type)

        # Emit the signal for backward compatibility
        self.fieldRequested.emit(field_type)

        print(f"✅ Field type {field_type} selected and ready for placement")

    def _notify_canvas_selection(self, field_type):
        """Notify canvas about field type selection"""
        try:
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'pdf_canvas'):
                if hasattr(main_window.pdf_canvas, 'set_selected_field_type'):
                    main_window.pdf_canvas.set_selected_field_type(field_type)
                    print(f"✅ Notified canvas of selection: {field_type}")
        except Exception as e:
            print(f"⚠️ Could not notify canvas: {e}")

    def reset_selection(self):
        """🔧 NEW: Reset field type selection after placement"""
        print("🔄 Resetting field type selection...")

        # Clear highlights
        self.clear_highlights()

        # Reset selected field type
        self.selected_field_type = None

        # Notify canvas that no field type is selected
        try:
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'pdf_canvas'):
                if hasattr(main_window.pdf_canvas, 'set_selected_field_type'):
                    main_window.pdf_canvas.set_selected_field_type(None)
                    print("✅ Notified canvas: selection cleared")
        except Exception as e:
            print(f"⚠️ Could not notify canvas: {e}")

        print("✅ Field type selection reset complete")

    def clear_highlights(self):
        """Clear all field type highlights"""
        for field_type, button in self.field_buttons.items():
            button.setProperty("class", "")  # Remove selected class
            button.setStyleSheet("")  # Reset to default style
            button.style().unpolish(button)
            button.style().polish(button)

    def highlight_field_type(self, field_type: str, highlight: bool = True):
        """Highlight a specific field type"""
        if field_type not in self.field_buttons:
            return

        button = self.field_buttons[field_type]

        if highlight:
            # Add selected class for styling
            button.setProperty("class", "selected")
        else:
            # Remove selected class
            button.setProperty("class", "")

        # Force style update
        button.style().unpolish(button)
        button.style().polish(button)

    def get_selected_field_type(self):
        """Get the currently selected field type"""
        return self.selected_field_type

    def _get_main_window(self):
        """Get the main window safely"""
        try:
            widget = self
            while widget.parent():
                widget = widget.parent()
                if (hasattr(widget, 'field_palette') and
                        hasattr(widget, 'pdf_canvas')):
                    return widget
            return None
        except Exception as e:
            print(f"⚠️ Error finding main window: {e}")
            return None

class FieldPreviewWidget(QWidget):
    """Widget showing a preview of the selected field type"""

    def __init__(self):
        super().__init__()
        self.current_field_type = None
        self.setFixedSize(120, 40)
        self.setStyleSheet("border: 1px solid #ccc; background-color: white;")

    def set_field_type(self, field_type: str):
        """Set the field type to preview"""
        self.current_field_type = field_type
        self.update()

    def paintEvent(self, event):
        """Draw preview of the field type"""
        if not self.current_field_type:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw field preview based on type
        rect = self.rect().adjusted(5, 5, -5, -5)

        if self.current_field_type == "text":
            painter.drawRect(rect)
            painter.drawText(rect.adjusted(5, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, "Text...")

        elif self.current_field_type == "checkbox":
            checkbox_size = min(rect.width(), rect.height()) - 10
            checkbox_rect = rect.adjusted(5, 5, -rect.width() + checkbox_size + 5, -5)
            painter.drawRect(checkbox_rect)
            # Draw checkmark
            painter.drawLine(checkbox_rect.left() + 3, checkbox_rect.center().y(),
                           checkbox_rect.center().x(), checkbox_rect.bottom() - 3)
            painter.drawLine(checkbox_rect.center().x(), checkbox_rect.bottom() - 3,
                           checkbox_rect.right() - 3, checkbox_rect.top() + 3)

        elif self.current_field_type == "dropdown":
            painter.drawRect(rect)
            painter.drawText(rect.adjusted(5, 0, -15, 0), Qt.AlignmentFlag.AlignVCenter, "Select")
            # Draw dropdown arrow
            arrow_rect = rect.adjusted(rect.width() - 15, 0, 0, 0)
            painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignCenter, "▼")

        elif self.current_field_type == "signature":
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Sign here")

        elif self.current_field_type == "date":
            painter.drawRect(rect)
            painter.drawText(rect.adjusted(5, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, "DD/MM/YY")

        elif self.current_field_type == "button":
            painter.setBrush(QColor(240, 240, 240))
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Button")

        elif self.current_field_type == "radio":
            radio_size = min(rect.width(), rect.height()) - 10
            radio_rect = rect.adjusted(5, 5, -rect.width() + radio_size + 5, -5)
            painter.drawEllipse(radio_rect)
            # Draw filled circle
            inner_rect = radio_rect.adjusted(4, 4, -4, -4)
            painter.setBrush(QColor(0, 0, 0))
            painter.drawEllipse(inner_rect)


class QuickActionsWidget(QWidget):
    """Widget with quick action buttons for field operations"""

    duplicateRequested = pyqtSignal()
    deleteRequested = pyqtSignal()
    alignRequested = pyqtSignal(str)  # alignment type

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize quick actions UI"""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Quick Actions")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        layout.addWidget(title)

        # Action buttons
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(3)

        # Duplicate button
        self.duplicate_btn = QPushButton("📄 Duplicate (Ctrl+D)")
        self.duplicate_btn.setToolTip("Duplicate selected fields with 10px offset")
        self.duplicate_btn.clicked.connect(self.duplicateRequested.emit)
        self.duplicate_btn.setEnabled(False)  # Disabled by default
        actions_layout.addWidget(self.duplicate_btn)

        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setToolTip("Delete selected fields (Delete key)")
        self.delete_btn.clicked.connect(self.deleteRequested.emit)
        self.delete_btn.setEnabled(False)  # Disabled by default
        actions_layout.addWidget(self.delete_btn)

        # Alignment buttons
        align_group = QGroupBox("Align")
        align_layout = QHBoxLayout()
        align_layout.setSpacing(2)

        align_buttons = [
            ("⬅️", "left", "Align left"),
            ("➡️", "right", "Align right"),
            ("⬆️", "top", "Align top"),
            ("⬇️", "bottom", "Align bottom")
        ]

        for icon, alignment, tooltip in align_buttons:
            btn = QPushButton(icon)
            btn.setFixedSize(30, 25)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, a=alignment: self.alignRequested.emit(a))
            align_layout.addWidget(btn)

        align_group.setLayout(align_layout)
        actions_layout.addWidget(align_group)

        layout.addLayout(actions_layout)
        layout.addStretch()

        # Style all buttons
        self.setStyleSheet("""
            QPushButton {
                padding: 5px 8px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f8f9fa;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QPushButton:disabled {
                color: #6c757d;
                background-color: #e9ecef;
                border-color: #dee2e6;
            }
        """)

        self.setLayout(layout)

    def set_actions_enabled(self, enabled: bool):
        """Enable/disable all action buttons"""
        for button in self.findChildren(QPushButton):
            button.setEnabled(enabled)

    def set_selection_state(self, has_selection: bool, field_count: int = 0):
        """Update button states based on selection"""
        self.duplicate_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

        if has_selection and field_count > 0:
            self.duplicate_btn.setText(f"📄 Duplicate {field_count} field{'s' if field_count > 1 else ''} (Ctrl+D)")
        else:
            self.duplicate_btn.setText("📄 Duplicate (Ctrl+D)")

class EnhancedFieldPalette(QWidget):
    """Enhanced field palette with preview and quick actions"""

    fieldRequested = pyqtSignal(str)
    duplicateRequested = pyqtSignal()
    deleteRequested = pyqtSignal()
    alignRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the enhanced palette UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Main field palette
        self.field_palette = ScrollableFieldPalette()
        layout.addWidget(self.field_palette)

        # Field preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview_widget = FieldPreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Quick actions
        self.quick_actions = QuickActionsWidget()
        layout.addWidget(self.quick_actions)

        self.setLayout(layout)

        # Connect signals
        self.field_palette.fieldRequested.connect(self._on_field_requested)
        self.quick_actions.duplicateRequested.connect(self.duplicateRequested)
        self.quick_actions.deleteRequested.connect(self.deleteRequested)
        self.quick_actions.alignRequested.connect(self.alignRequested)

    def _on_field_requested(self, field_type: str):
        """Handle field request and update preview"""
        self.preview_widget.set_field_type(field_type)
        self.fieldRequested.emit(field_type)

    def set_field_selected(self, has_selection: bool):
        """Update UI based on whether a field is selected"""
        self.quick_actions.set_actions_enabled(has_selection)

    def highlight_field_type(self, field_type: str):
        """Highlight a field type in the palette"""
        self.field_palette.clear_highlights()
        if field_type:
            self.field_palette.highlight_field_type(field_type, True)
            self.preview_widget.set_field_type(field_type)
    def clear_highlights(self):
        """Clear all field type highlights"""
        if hasattr(self.field_palette, 'clear_highlights'):
            self.field_palette.clear_highlights()

    def highlight_field_type(self, field_type: str):
        """Highlight a field type in the palette"""
        # Clear existing highlights first
        if hasattr(self.field_palette, 'clear_highlights'):
            self.field_palette.clear_highlights()

        # Highlight the selected field type
        if field_type and hasattr(self.field_palette, 'highlight_field_type'):
            self.field_palette.highlight_field_type(field_type, True)

        # Update preview widget
        if hasattr(self, 'preview_widget') and field_type:
            self.preview_widget.set_field_type(field_type)

    def reset_selection(self):
        """Reset field selection (delegate to internal palette)"""
        if hasattr(self.field_palette, 'reset_selection'):
            self.field_palette.reset_selection()
            print("✅ EnhancedFieldPalette: delegated reset to internal palette")
        else:
            # Manual reset
            if hasattr(self.field_palette, 'clear_highlights'):
                self.field_palette.clear_highlights()
            if hasattr(self.field_palette, 'selected_field_type'):
                self.field_palette.selected_field_type = None
            print("✅ EnhancedFieldPalette: manual reset completed")