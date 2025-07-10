# File: src/ui/field_alignment_widget.py
"""
Field Alignment Widget
Provides alignment and distribution controls for multiple selected fields
Uses clickable buttons like AlignmentGridWidget
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QFrame)


class FieldAlignmentWidget(QWidget):
    """Field alignment widget with clickable buttons like AlignmentGridWidget"""

    alignmentRequested = pyqtSignal(str)  # alignment_type
    distributionRequested = pyqtSignal(str)  # distribution_type

    def __init__(self):
        super().__init__()
        self.current_selection_count = 0
        self.alignment_buttons = {}
        self.distribution_buttons = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the field alignment UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Alignment section (2x3 grid)
        self._create_alignment_section(layout)

        # Distribution section (1x2)
        self._create_distribution_section(layout)

        # Apply styling similar to AlignmentGridWidget
        self._apply_button_styles()

        self.setLayout(layout)

    def _create_alignment_section(self, parent_layout):
        """Create the alignment section with 2x3 grid layout"""
        align_frame = QFrame()
        align_layout = QHBoxLayout()
        align_layout.setContentsMargins(0, 0, 0, 0)
        align_layout.setSpacing(5)

        # Label matching text alignment widget style
        align_label = QLabel("Align:")
        align_layout.addWidget(align_label)

        # Create 2x3 grid for alignment buttons
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(2)  # Tighter spacing like AlignmentGridWidget

        # Alignment button definitions (text, alignment_type, row, col)
        button_definitions = [
            # Row 0: Horizontal alignments
            ("◀", "left", 0, 0, "Align Left"),
            ("↔", "center_horizontal", 0, 1, "Align Center Horizontally"),
            ("▶", "right", 0, 2, "Align Right"),
            # Row 1: Vertical alignments
            ("▲", "top", 1, 0, "Align Top"),
            ("↕", "center_vertical", 1, 1, "Align Center Vertically"),
            ("▼", "bottom", 1, 2, "Align Bottom")
        ]

        # Create alignment buttons
        for text, alignment_type, row, col, tooltip in button_definitions:
            button = QPushButton(text)
            button.setFixedSize(28, 28)  # Same size as AlignmentGridWidget
            button.setToolTip(tooltip)
            button.setEnabled(False)  # Disabled by default

            # Connect with proper lambda closure
            button.clicked.connect(lambda checked, a=alignment_type: self._on_alignment_clicked(a))

            grid_layout.addWidget(button, row, col)
            self.alignment_buttons[alignment_type] = button

        grid_widget.setLayout(grid_layout)
        align_layout.addWidget(grid_widget)
        align_layout.addStretch()

        align_frame.setLayout(align_layout)
        parent_layout.addWidget(align_frame)

    def _create_distribution_section(self, parent_layout):
        """Create the distribution section matching alignment style"""
        dist_frame = QFrame()
        dist_layout = QHBoxLayout()
        dist_layout.setContentsMargins(0, 0, 0, 0)
        dist_layout.setSpacing(5)

        # Label matching text alignment widget style
        dist_label = QLabel("Distribute:")
        dist_layout.addWidget(dist_label)

        # Distribution button definitions (text, distribution_type, tooltip)
        dist_button_definitions = [
            ("⟷", "distribute_horizontal", "Distribute Horizontally"),
            ("⟸", "distribute_vertical", "Distribute Vertically")
        ]

        # Create distribution buttons
        for text, dist_type, tooltip in dist_button_definitions:
            button = QPushButton(text)
            button.setFixedSize(28, 28)  # Same size as alignment buttons
            button.setToolTip(tooltip)
            button.setEnabled(False)  # Disabled by default

            # Connect with proper lambda closure
            button.clicked.connect(lambda checked, d=dist_type: self._on_distribution_clicked(d))

            dist_layout.addWidget(button)
            self.distribution_buttons[dist_type] = button

        dist_layout.addStretch()

        dist_frame.setLayout(dist_layout)
        parent_layout.addWidget(dist_frame)

    def _apply_button_styles(self):
        """Apply styling similar to AlignmentGridWidget"""
        self.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QPushButton:disabled {
                color: #6c757d;
                background-color: #e9ecef;
                border-color: #dee2e6;
            }
        """)

    def _on_alignment_clicked(self, alignment_type):
        """Handle alignment button click"""
        print(f"🎯 Field alignment: {alignment_type}")
        self.alignmentRequested.emit(alignment_type)

    def _on_distribution_clicked(self, distribution_type):
        """Handle distribution button click"""
        print(f"🎯 Field distribution: {distribution_type}")
        self.distributionRequested.emit(distribution_type)

    def update_selection_count(self, count):
        """Update button states based on field selection count"""
        self.current_selection_count = count

        # Enable alignment buttons when 2+ fields selected
        enable_align = count >= 2
        for button in self.alignment_buttons.values():
            button.setEnabled(enable_align)

        # Enable distribution buttons when 3+ fields selected
        enable_distribute = count >= 3
        for button in self.distribution_buttons.values():
            button.setEnabled(enable_distribute)

        print(f"🔄 Field alignment widget: {count} fields selected")
        print(f"   Align enabled: {enable_align}, Distribute enabled: {enable_distribute}")

    def get_selection_count(self):
        """Get current selection count"""
        return self.current_selection_count

    def set_enabled(self, enabled):
        """Enable/disable the entire widget"""
        for button in self.alignment_buttons.values():
            button.setEnabled(enabled and self.current_selection_count >= 2)

        for button in self.distribution_buttons.values():
            button.setEnabled(enabled and self.current_selection_count >= 3)