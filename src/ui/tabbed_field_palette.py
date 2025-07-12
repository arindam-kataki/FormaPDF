"""
Enhanced Field Palette with Tab Control
Reorganizes the field palette into a tabbed interface with Controls and Properties tabs
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
    QLabel, QComboBox, QScrollArea, QPushButton, QFrame, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from ui.properties_panel import PropertiesPanel  # Existing properties panel


class ControlsTab(QWidget):
    """Tab containing form controls that can be added to the form"""

    fieldRequested = pyqtSignal(str)
    duplicateRequested = pyqtSignal()
    deleteRequested = pyqtSignal()
    alignRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.selected_field_type = None
        self.field_buttons = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the controls tab UI"""
        layout = QVBoxLayout()
        layout.setSpacing(5)  # Reduce spacing to maximize content area
        layout.setContentsMargins(5, 5, 5, 5)  # Remove margins to use full space

        # Field Types Section
        self._create_field_types_section(layout)

        # Field Preview Section
        #self._create_preview_section(layout)

        # Quick Actions Section
        self._create_quick_actions_section(layout)

        layout.addStretch()
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setLayout(layout)

    def _create_field_types_section(self, parent_layout):
        """Create the field types selection section"""
        field_group = QGroupBox("Form Controls")
        field_layout = QVBoxLayout()

        # ✅ FIX: Remove spacing and margins to eliminate gap
        field_layout.setSpacing(0)  # Remove spacing between widgets
        field_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins

        # Create scrollable area for field buttons - EXPAND TO FILL AVAILABLE HEIGHT
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # ✅ KEY FIX: Remove fixed height and set size policy to expand
        from PyQt6.QtWidgets import QSizePolicy
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        #scroll_area.setMinimumHeight(200)  # Minimum usable height
        scroll_area.setFrameStyle(0)  # Remove frame to maximize content area

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(5)

        scroll_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Define field types with icons and descriptions
        field_types = [
            ("text", "📝", "Text Field", "Single line text input"),
            ("textarea", "📄", "Text Area", "Multi-line text input"),
            ("password", "🔒", "Password", "Password input field"),
            ("checkbox", "☑️", "Checkbox", "Checkable box"),
            ("radio", "🔘", "Radio Button", "Single selection option"),
            ("dropdown", "📋", "Dropdown", "Selection list"),
            ("list_box", "📋", "List Box", "Multi-selection list"),
            ("date", "📅", "Date Field", "Date picker"),
            ("number", "🔢", "Number Field", "Numeric input"),
            ("email", "📧", "Email Field", "Email address input"),
            ("phone", "📞", "Phone", "Phone number input"),
            ("url", "🔗", "URL", "Website URL input"),
            ("file_upload", "📎", "File Upload", "File selection input"),
            ("button", "🔘", "Button", "Clickable button"),
            ("label", "🏷️", "Label", "Text label"),
            ("signature", "✍️", "Signature", "Digital signature area"),
        ]

        for field_type, icon, name, description in field_types:
            btn = QPushButton(f"{icon} {name}")
            btn.setToolTip(description)
            btn.setFixedHeight(35)
            btn.clicked.connect(lambda checked, ft=field_type: self._on_field_button_clicked(ft))

            # Store button reference
            self.field_buttons[field_type] = btn
            scroll_layout.addWidget(btn)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        field_layout.addWidget(scroll_area)

        field_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        field_group.setLayout(field_layout)
        parent_layout.addWidget(field_group)

        # Apply styling
        self._apply_field_button_styles()

    def _create_preview_section(self, parent_layout):
        """Create the field preview section"""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel("Select a control type to see preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(80)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 12px;
            }
        """)

        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        parent_layout.addWidget(preview_group)

    def _create_quick_actions_section(self, parent_layout):
        """Create the quick actions section with field alignment widget"""
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()

        # Create duplicate button
        self.duplicate_btn = QPushButton("📋 Duplicate (Ctrl+D)")
        self.duplicate_btn.setToolTip("Create a copy of selected field")
        self.duplicate_btn.setEnabled(False)  # Disabled by default
        self.duplicate_btn.clicked.connect(self.duplicateRequested.emit)
        actions_layout.addWidget(self.duplicate_btn)

        # Create delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setToolTip("Delete selected field")
        self.delete_btn.setEnabled(False)  # Disabled by default
        self.delete_btn.clicked.connect(self.deleteRequested.emit)
        actions_layout.addWidget(self.delete_btn)

        # Add field alignment widget
        from ui.field_alignment_widget import FieldAlignmentWidget
        self.field_alignment_widget = FieldAlignmentWidget()
        self.field_alignment_widget.alignmentRequested.connect(self.alignRequested.emit)
        self.field_alignment_widget.distributionRequested.connect(self.alignRequested.emit)
        actions_layout.addWidget(self.field_alignment_widget)

        actions_group.setLayout(actions_layout)
        parent_layout.addWidget(actions_group)

        # Connect to field manager selection changes
        self._connect_selection_updates()

    def _should_include_distribution_buttons(self):
        """Determine if distribution buttons should be included"""
        # You can make this configurable or always return True
        return True

    def _connect_selection_updates(self):
        """Connect to field manager to update button states"""
        # Get field manager reference (adjust path based on your structure)
        if hasattr(self, 'field_manager') and self.field_manager:
            if hasattr(self.field_manager, 'selection_changed'):
                self.field_manager.selection_changed.connect(self._update_action_buttons)
        elif hasattr(self, 'parent') and hasattr(self.parent(), 'field_manager'):
            field_manager = self.parent().field_manager
            if hasattr(field_manager, 'selection_changed'):
                field_manager.selection_changed.connect(self._update_action_buttons)
        else:
            print("⚠️ Could not connect to field manager selection changes")

    def _update_action_buttons(self, selected_fields):
        """Update action button states based on selection"""
        selection_count = len(selected_fields) if selected_fields else 0
        enable_buttons = selection_count >= 1

        # Update duplicate/delete buttons
        self.duplicate_btn.setEnabled(enable_buttons)
        self.delete_btn.setEnabled(enable_buttons)

        # Update button text to show count
        if selection_count > 1:
            self.duplicate_btn.setText(f"📋 Duplicate {selection_count} fields (Ctrl+D)")
        else:
            self.duplicate_btn.setText("📋 Duplicate (Ctrl+D)")

        # Update field alignment widget
        if hasattr(self, 'field_alignment_widget'):
            self.field_alignment_widget.update_selection_count(selection_count)

        print(f"🔄 Updated action buttons: {selection_count} fields selected, buttons enabled: {enable_buttons}")

    def _apply_field_button_styles(self):
        """Apply consistent styling to field buttons"""
        style = """
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """
        self.setStyleSheet(style)

    def _on_field_button_clicked(self, field_type: str):
        """Handle field button click"""
        # Clear previous selection
        self.clear_highlights()

        # Set new selection
        self.selected_field_type = field_type
        self.highlight_field_type(field_type, True)

        # Update preview
        #self._update_preview(field_type)

        # Emit signal
        self.fieldRequested.emit(field_type)
        print(f"✅ Field type {field_type} selected and ready for placement")

    def _update_preview(self, field_type: str):
        """Update the preview based on selected field type"""
        previews = {
            "text": "📝 [Text Input Field]",
            "textarea": "📄 [Multi-line Text Area]",
            "checkbox": "☑️ [✓] Checkbox",
            "radio": "🔘 ( ) Radio Button",
            "dropdown": "📋 [Select Option ▼]",
            "date": "📅 [MM/DD/YYYY]",
            "number": "🔢 [123]",
            "email": "📧 [user@example.com]",
            "signature": "✍️ [Signature Area]",
            "image": "🖼️ [Image Placeholder]",
        }

        preview_text = previews.get(field_type, f"[{field_type.title()} Field]")
        self.preview_label.setText(preview_text)

    def clear_highlights(self):
        """Clear all field type highlights"""
        for field_type, button in self.field_buttons.items():
            self.highlight_field_type(field_type, False)

    def highlight_field_type(self, field_type: str, highlight: bool = True):
        """Highlight a specific field type"""
        if field_type not in self.field_buttons:
            return

        button = self.field_buttons[field_type]

        if highlight:
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 2px solid #0078d4;
                    border-radius: 4px;
                    background-color: #e3f2fd;
                    color: #0078d4;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #bbdefb;
                    border-color: #0056b3;
                }
            """)
        else:
            button.setStyleSheet("")  # Reset to default

    def set_field_selected(self, has_selection: bool):
        """Enable/disable action buttons based on field selection"""
        # Enable/disable quick action buttons
        for attr_name in dir(self):
            if attr_name.startswith('_') and attr_name.endswith('_btn'):
                btn = getattr(self, attr_name, None)
                if btn:
                    btn.setEnabled(has_selection)

    def reset_selection(self):
        """Reset field type selection"""
        self.clear_highlights()
        self.selected_field_type = None
        self.preview_label.setText("Select a control type to see preview")

    def get_selected_field_type(self):
        """Get the currently selected field type"""
        return self.selected_field_type

    def set_field_manager(self, field_manager):
        """Set the field manager and connect to selection changes"""
        self.field_manager = field_manager

        # Connect to selection changes to update button states
        if hasattr(field_manager, 'selection_changed'):
            field_manager.selection_changed.connect(self._update_action_buttons)
            print("✅ ControlsTab connected to field manager selection changes")

class PropertiesTab(QWidget):
    """Tab containing properties for the selected form control"""

    propertyChanged = pyqtSignal(str, str, object)  # field_id, property_name, value

    def __init__(self):
        super().__init__()
        self.current_field = None
        self.field_manager = None  # Will be set by parent
        self.init_ui()

    def init_ui(self):
        """Initialize the properties tab UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Control Selection Section
        self._create_control_selection_section(layout)

        # Properties Panel
        self._create_properties_section(layout)

        layout.addStretch()
        self.setLayout(layout)

    def _create_control_selection_section(self, parent_layout):
        """Create the control selection dropdown section"""
        selection_group = QGroupBox("Selected Control")
        selection_layout = QVBoxLayout()

        # Dropdown for selecting controls
        dropdown_layout = QHBoxLayout()
        dropdown_layout.addWidget(QLabel("Control:"))

        self.control_dropdown = QComboBox()
        self.control_dropdown.addItem("No controls available", None)
        #temporary commented out
        self.control_dropdown.currentTextChanged.connect(self._on_control_selected)
        dropdown_layout.addWidget(self.control_dropdown)

        selection_layout.addLayout(dropdown_layout)

        # Info label
        self.control_info_label = QLabel("Select a control to edit its properties")
        self.control_info_label.setStyleSheet("color: #666; font-size: 11px;")
        selection_layout.addWidget(self.control_info_label)

        selection_group.setLayout(selection_layout)
        parent_layout.addWidget(selection_group)

    def _create_properties_section(self, parent_layout):
        """Create the properties editing section with enhanced appearance support"""

        # Try enhanced properties panel first
        try:
            from ui.enhanced_properties_panel import EnhancedPropertiesPanel
            self.properties_panel = EnhancedPropertiesPanel()

            # Connect property change signals with signal conversion
            if hasattr(self.properties_panel, 'propertyChanged'):
                self.properties_panel.propertyChanged.connect(self._on_property_changed_internal)
                print("✅ Connected propertyChanged signal (with conversion)")

            # Connect appearance change signals if available
            if hasattr(self.properties_panel, 'appearanceChanged'):
                self.properties_panel.appearanceChanged.connect(self._on_appearance_changed)
                print("✅ Connected appearanceChanged signal")

            parent_layout.addWidget(self.properties_panel, 1)
            print("✅ TabbedFieldPalette using EnhancedPropertiesPanel with appearance controls")

        except ImportError as e:
            print(f"⚠️ EnhancedPropertiesPanel not available: {e}")
            print("   Falling back to original PropertiesPanel...")

            # Fallback to original PropertiesPanel
            try:
                from ui.properties_panel import PropertiesPanel
                self.properties_panel = PropertiesPanel()

                # Connect property change signals with signal conversion
                if hasattr(self.properties_panel, 'propertyChanged'):
                    self.properties_panel.propertyChanged.connect(self._on_property_changed_internal)
                    print("✅ Connected propertyChanged signal (fallback with conversion)")

                parent_layout.addWidget(self.properties_panel, 1)
                print("⚠️ TabbedFieldPalette using fallback PropertiesPanel (no appearance controls)")

            except ImportError as e2:
                print(f"❌ Both PropertiesPanel versions failed: {e2}")
                print("   Creating placeholder...")

                # Final fallback - create placeholder
                properties_group = QGroupBox("Properties")
                properties_layout = QVBoxLayout()

                self.properties_placeholder = QLabel(
                    "Properties panel not available\n\n"
                    "Missing dependencies:\n"
                    "• Enhanced Properties Panel\n"
                    "• Original Properties Panel"
                )
                self.properties_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.properties_placeholder.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #ccc;
                        border-radius: 4px;
                        background-color: #f9f9f9;
                        color: #666;
                        font-size: 12px;
                        padding: 20px;
                        margin: 10px;
                    }
                """)

                properties_layout.addWidget(self.properties_placeholder)
                properties_group.setLayout(properties_layout)
                parent_layout.addWidget(properties_group)

                self.properties_panel = None
                print("❌ Created placeholder - no properties functionality available")

    def _on_property_changed_internal(self, property_name: str, value):
        """Handle property changes from enhanced properties panel and convert signal format"""
        try:
            if hasattr(self, 'current_field') and self.current_field:
                field_id = self.current_field.id

                # Convert to the expected signal format for TabbedFieldPalette
                # Original signal: propertyChanged(str, str, object) - field_id, property_name, value
                self.propertyChanged.emit(field_id, property_name, value)

                print(f"✅ Property changed: {field_id}.{property_name} = {value}")
            else:
                print("⚠️ Property changed but no current field selected")

        except Exception as e:
            print(f"❌ Error handling property change: {e}")

    def _on_appearance_changed(self, appearance_props: dict):
        """Handle appearance property changes from enhanced properties panel"""
        try:
            print(f"🎨 Appearance changed in TabbedFieldPalette: {list(appearance_props.keys())}")

            # Get currently selected field
            if hasattr(self, 'current_field') and self.current_field:
                # Update the field's appearance properties
                if 'appearance' not in self.current_field.properties:
                    self.current_field.properties['appearance'] = {}
                self.current_field.properties['appearance'].update(appearance_props)

                print(f"✅ Updated appearance for field {self.current_field.id}")

                # Notify parent components about the change
                self._notify_appearance_change(appearance_props)

            else:
                print("⚠️ No field selected for appearance update")

        except Exception as e:
            print(f"❌ Error handling appearance change: {e}")
            import traceback
            traceback.print_exc()

    def _notify_appearance_change(self, appearance_props: dict):
        """Notify parent components about appearance changes"""
        try:
            # Find the main window and trigger field re-rendering
            main_window = self._find_main_window()
            if main_window:
                # Try to trigger field display update
                if hasattr(main_window, 'update_field_display'):
                    main_window.update_field_display()
                    print("✅ Triggered field display update via main window")
                elif hasattr(main_window, 'pdf_canvas') and hasattr(main_window.pdf_canvas, 'draw_overlay'):
                    main_window.pdf_canvas.draw_overlay()
                    print("✅ Triggered field display update via PDF canvas")
                else:
                    print("⚠️ Could not find method to update field display")
            else:
                print("⚠️ Could not find main window to notify")

        except Exception as e:
            print(f"❌ Error notifying appearance change: {e}")

    def _on_control_selected(self):
        """Handle control selection from dropdown - update FieldManager as source of truth AND navigate to page"""
        try:
            current_index = self.control_dropdown.currentIndex()
            field_id = self.control_dropdown.itemData(current_index)

            print(f"🔽 DROPDOWN: User selected control: {field_id}")

            if field_id and self.field_manager:
                field = self.field_manager.get_field_by_id(field_id)
                if field:
                    # UPDATE FIELDMANAGER as source of truth
                    self.field_manager.select_field(field, multi_select=False)
                    print(f"  📋 FieldManager updated - selected: {field_id}")

                    # Update local state
                    self.current_field = field
                    self._update_properties_display(field)

                    # *** NEW: Navigate to field's page ***
                    self._navigate_to_field_page(field)

                    # Notify main window to update canvas visuals
                    self._notify_main_window(field)
                    print("  📤 Propagated to main window")

                    # CRITICAL: Force canvas overlay repaint
                    main_window = self._find_main_window()
                    if main_window and hasattr(main_window, 'pdf_canvas'):
                        main_window.pdf_canvas.draw_overlay()
                        print("  🎨 Canvas overlay repainted")

            else:
                # Clear selection in FieldManager
                if self.field_manager:
                    self.field_manager.clear_selection()
                    print("  🧹 FieldManager selection cleared")

                self.current_field = None
                self._update_properties_display(None)
                self._notify_main_window(None)

        except Exception as e:
            print(f"❌ Error in dropdown selection: {e}")

    def x_on_control_selected(self):
        """Handle control selection from dropdown - update FieldManager as source of truth"""
        try:
            current_index = self.control_dropdown.currentIndex()
            field_id = self.control_dropdown.itemData(current_index)

            print(f"🔽 DROPDOWN: User selected control: {field_id}")

            if field_id and self.field_manager:
                field = self.field_manager.get_field_by_id(field_id)
                if field:
                    # UPDATE FIELDMANAGER as source of truth
                    self.field_manager.select_field(field, multi_select=False)
                    print(f"  📋 FieldManager updated - selected: {field_id}")

                    # Update local state
                    self.current_field = field
                    self._update_properties_display(field)

                    # Notify main window to update canvas visuals
                    self._notify_main_window(field)
                    print("  📤 Propagated to main window")

                    # CRITICAL: Force canvas overlay repaint
                    main_window = self._find_main_window()
                    if main_window and hasattr(main_window, 'pdf_canvas'):
                        main_window.pdf_canvas.draw_overlay()
                        print("  🎨 Canvas overlay repainted")

            else:
                # Clear selection in FieldManager
                if self.field_manager:
                    self.field_manager.clear_selection()
                    print("  🧹 FieldManager selection cleared")

                self.current_field = None
                self._update_properties_display(None)
                self._notify_main_window(None)

        except Exception as e:
            print(f"❌ Error in dropdown selection: {e}")

    def _navigate_to_field_page(self, field):
        """Scroll to bring the selected field into view in the viewport"""
        try:
            # Get field's page and position
            field_page = getattr(field, 'page_number', getattr(field, 'page', 0))
            field_x = getattr(field, 'x', 0)
            field_y = getattr(field, 'y', 0)

            print(f"🎯 Bringing field '{field.id}' into view: page {field_page + 1}, position ({field_x}, {field_y})")

            # Find the main window
            main_window = self._find_main_window()
            if not main_window:
                print("  ⚠️ Cannot navigate - main window not found")
                return False

            # Get required components
            if not (hasattr(main_window, 'pdf_canvas') and hasattr(main_window, 'scroll_area')):
                print("  ⚠️ Required components not found")
                return False

            pdf_canvas = main_window.pdf_canvas
            scroll_area = main_window.scroll_area

            # Get current zoom level
            zoom_level = getattr(pdf_canvas, 'zoom_level', 1.0)

            # Calculate field's absolute screen position
            field_absolute_y = self._calculate_field_screen_position(pdf_canvas, field_page, field_x, field_y,
                                                                     zoom_level)

            if field_absolute_y is None:
                print("  ⚠️ Could not calculate field position")
                return False

            # Get viewport dimensions
            viewport = scroll_area.viewport()
            viewport_height = viewport.height()
            viewport_width = viewport.width()

            # Calculate where to scroll to center the field in viewport
            target_scroll_y = field_absolute_y - (viewport_height // 2)
            target_scroll_y = max(0, int(target_scroll_y))  # Don't scroll above top

            # Perform the scroll
            v_scrollbar = scroll_area.verticalScrollBar()
            current_scroll = v_scrollbar.value()

            print(f"  📜 Scrolling from {current_scroll} to {target_scroll_y} to center field")
            v_scrollbar.setValue(target_scroll_y)

            # Update page tracking
            if hasattr(main_window, 'update_page_controls'):
                main_window.update_page_controls()

            # Show status message
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage(f"Scrolled to field '{field.id}' on page {field_page + 1}", 2000)

            # Force a redraw to ensure field is highlighted
            if hasattr(pdf_canvas, 'draw_overlay'):
                pdf_canvas.draw_overlay()

            print(f"  ✅ Field brought into view at scroll position {target_scroll_y}")
            return True

        except Exception as e:
            print(f"❌ Error bringing field into view: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _calculate_field_screen_position(self, pdf_canvas, field_page, field_x, field_y, zoom_level):
        """Calculate the absolute screen Y position of a field"""
        try:
            # Method 1: Use page positions if available (most accurate)
            if hasattr(pdf_canvas, 'page_positions') and field_page < len(pdf_canvas.page_positions):
                page_top = pdf_canvas.page_positions[field_page]
                field_y_on_page = field_y * zoom_level
                absolute_y = page_top + field_y_on_page
                print(
                    f"    📐 Calculated position using page_positions: page_top={page_top}, field_y_scaled={field_y_on_page}, absolute_y={absolute_y}")
                return absolute_y

            # Method 2: Use document_to_screen_coordinates if available
            elif hasattr(pdf_canvas, 'document_to_screen_coordinates'):
                screen_coords = pdf_canvas.document_to_screen_coordinates(field_page, field_x, field_y)
                if screen_coords:
                    screen_x, screen_y = screen_coords
                    print(f"    📐 Calculated position using document_to_screen_coordinates: ({screen_x}, {screen_y})")
                    return screen_y

            # Method 3: Estimate based on page height and spacing
            elif hasattr(pdf_canvas, 'pdf_document'):
                try:
                    # Calculate estimated page height
                    page = pdf_canvas.pdf_document[field_page]
                    page_height = int(page.rect.height * zoom_level)
                    page_spacing = 15  # Default spacing between pages

                    # Estimate position
                    estimated_page_top = field_page * (page_height + page_spacing) + 15  # Add top margin
                    field_y_scaled = field_y * zoom_level
                    estimated_absolute_y = estimated_page_top + field_y_scaled

                    print(
                        f"    📐 Estimated position: page_height={page_height}, estimated_page_top={estimated_page_top}, absolute_y={estimated_absolute_y}")
                    return estimated_absolute_y

                except Exception as e:
                    print(f"    ⚠️ Error in estimation method: {e}")

            print("    ⚠️ Could not calculate field position - no suitable method available")
            return None

        except Exception as e:
            print(f"    ❌ Error calculating field position: {e}")
            return None

    def x_navigate_to_field_page(self, field):
        """Navigate to the page containing the selected field"""
        try:
            # Get field's page number
            field_page = getattr(field, 'page_number', getattr(field, 'page', 0))
            print(f"🧭 Navigating to field page: {field_page + 1}")  # Convert to 1-based for user display

            # Find the main window
            main_window = self._find_main_window()
            if not main_window:
                print("  ⚠️ Cannot navigate - main window not found")
                return False

            # Navigate using the existing page navigation methods
            if hasattr(main_window, 'jump_to_page_continuous'):
                # Use continuous view navigation (1-based page number)
                main_window.jump_to_page_continuous(field_page + 1)
                print(f"  ✅ Navigated to page {field_page + 1} using continuous view")

            elif hasattr(main_window, 'pdf_canvas') and hasattr(main_window.pdf_canvas, 'scroll_to_page'):
                # Direct canvas navigation (0-based page number)
                main_window.pdf_canvas.scroll_to_page(field_page)
                print(f"  ✅ Navigated to page {field_page + 1} using canvas scroll")

            else:
                print("  ⚠️ No navigation method available")
                return False

            # Update page controls to reflect new page
            if hasattr(main_window, 'update_page_controls'):
                main_window.update_page_controls()

            # Show status message
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage(f"Navigated to field '{field.id}' on page {field_page + 1}", 2000)

            return True

        except Exception as e:
            print(f"❌ Error navigating to field page: {e}")
            return False

    def _notify_main_window_selection(self, field):
        """Notify the main window that a field has been selected from dropdown"""
        try:
            # Find the main window
            main_window = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'on_field_selected') or hasattr(parent, 'pdf_canvas'):
                    main_window = parent
                    break
                parent = parent.parent()

            if main_window:
                print(f"  Found main window: {type(main_window).__name__}")

                # Method 1: Call the main window's field selection handler directly
                if hasattr(main_window, 'on_field_selected'):
                    main_window.on_field_selected(field)
                    print("  ✅ Called main_window.on_field_selected()")

                # Method 2: Update the canvas selection if available
                if hasattr(main_window, 'pdf_canvas') and main_window.pdf_canvas:
                    canvas = main_window.pdf_canvas

                    # Update the canvas selection handler
                    if hasattr(canvas, 'selection_handler'):
                        canvas.selection_handler.select_field(field)
                        print("  ✅ Updated canvas selection_handler")

                    # Update the enhanced drag handler if available
                    if hasattr(canvas, 'enhanced_drag_handler'):
                        canvas.enhanced_drag_handler.select_field(field)
                        print("  ✅ Updated enhanced_drag_handler")

                    # Trigger a repaint to show selection
                    canvas.update()
                    print("  ✅ Triggered canvas repaint")

                # Method 3: Update the field palette if it has other tabs
                if hasattr(main_window, 'field_palette'):
                    palette = main_window.field_palette
                    if hasattr(palette, 'controls_tab'):
                        # Update the controls tab to reflect selection
                        palette.controls_tab.set_field_selected(field is not None)
                        print("  ✅ Updated controls tab selection state")
            else:
                print("  ⚠️ Could not find main window")

        except Exception as e:
            print(f"  ❌ Error notifying main window of selection: {e}")
            import traceback
            traceback.print_exc()

    def set_field_manager(self, field_manager):
        """Set the field manager reference"""
        print(f"📝 Setting field manager: {field_manager}")  # ← ADD THIS
        print(f"  Field manager has {len(getattr(field_manager, 'fields', []))} fields")  # ← ADD THIS
        self.field_manager = field_manager
        self.refresh_control_list()

    def refresh_control_list(self):
        """Refresh the list of available controls"""
        print("🔄 Refreshing control list...")
        print(f"  DEBUG: self.field_manager = {self.field_manager}")  # ← ADD THIS
        self.control_dropdown.clear()

        if not self.field_manager:
            print("  ⚠️ No field manager available")
            self.control_dropdown.addItem("No controls available", None)
            return

        # Try different methods to get fields
        fields = []
        if hasattr(self.field_manager, 'get_all_fields'):
            fields = self.field_manager.get_all_fields()
        elif hasattr(self.field_manager, 'fields'):
            fields = self.field_manager.fields
        else:
            print("  ⚠️ Field manager has no recognizable fields method")
            self.control_dropdown.addItem("No controls available", None)
            return

        if not fields:
            print("  ℹ️ No fields found in field manager")
            self.control_dropdown.addItem("No controls available", None)
            return

        print(f"  ✅ Found {len(fields)} fields")
        for field in fields:
            try:
                # Get field type safely
                field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                if hasattr(field_type, 'value'):
                    field_type = field_type.value

                # Get field ID safely
                field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))

                display_text = f"{str(field_type).title()} - {field_id}"

                if hasattr(field, 'properties') and isinstance(field.properties, dict) and 'name' in field.properties:
                    display_text = f"{str(field_type).title()} - {field.properties['name']}"

                self.control_dropdown.addItem(display_text, field_id)
                print(f"    Added: {display_text}")

            except Exception as e:
                print(f"  ⚠️ Error adding field to dropdown: {e}")
                continue

    def set_selected_field(self, field):
        """Called externally to set selected field - ALWAYS propagate"""
        print(f"🔧 External field selection: {field.id if field else 'None'}")

        # This is coming from outside (canvas click, etc.) so propagate
        self.highlight_control(field, propagate_to_properties=True)

    def highlight_control(self, field, propagate_to_properties=True):
        """Highlight a control and optionally propagate to main window"""
        print(f"🎯 Highlighting control: {field.id if field else 'None'} (propagate={propagate_to_properties})")

        # Always update these locally
        self.current_field = field
        self._update_dropdown_selection(field)
        self._update_canvas_highlighting(field)

        # ALWAYS update properties display (user expects to see them!)
        self._update_properties_display(field)
        print("  📋 Properties panel updated")

        # Only notify main window if propagate is True
        if propagate_to_properties:
            print("  📤 Propagating to main window...")
            self._notify_main_window(field)
        else:
            print("  🚫 Not propagating to main window")

    def _update_dropdown_selection(self, field):
        """Update dropdown selection without triggering signals"""
        # Block signals to prevent recursion
        self.control_dropdown.blockSignals(True)

        try:
            if not field:
                # Select "No controls available" item
                if self.control_dropdown.count() > 0:
                    self.control_dropdown.setCurrentIndex(0)
            else:
                # Find matching item
                field_id = getattr(field, 'id', getattr(field, 'name', None))
                if field_id:
                    for i in range(self.control_dropdown.count()):
                        if self.control_dropdown.itemData(i) == field_id:
                            self.control_dropdown.setCurrentIndex(i)
                            break
            print("  ✅ Dropdown selection updated (signals blocked)")
        finally:
            # Always restore signals
            self.control_dropdown.blockSignals(False)

    def _update_canvas_highlighting(self, field):
        """Update canvas highlighting - now respects FieldManager"""
        try:
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'pdf_canvas'):
                canvas = main_window.pdf_canvas

                # Instead of forcing selection, just trigger a visual update
                if hasattr(canvas, 'draw_overlay'):
                    canvas.draw_overlay()
                    print(f"✅ Triggered visual update only")
                canvas.update()
        except Exception as e:
            print(f"❌ Error in canvas highlighting: {e}")


    def _notify_main_window(self, field):
        """Notify main window of selection (only when propagating)"""
        try:
            main_window = self._find_main_window()
            if main_window:
                # Update status bar
                if field and hasattr(main_window, 'field_info_label'):
                    field_type = getattr(field, 'field_type', 'unknown')
                    if hasattr(field_type, 'value'):
                        field_type = field_type.value
                    main_window.field_info_label.setText(f"Selected: {field_type} - {field.id}")
                elif hasattr(main_window, 'field_info_label'):
                    main_window.field_info_label.setText("No field selected")

                print("  ✅ Main window notified")
        except Exception as e:
            print(f"  ⚠️ Error notifying main window: {e}")

    def _find_main_window(self):
        """Find the main window by traversing parent hierarchy"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'pdf_canvas') or hasattr(parent, 'on_field_selected'):
                return parent
            parent = parent.parent()
        return None

    def _update_properties_display(self, field):
        """Update properties display for selected field or show no selection"""
        try:
            if hasattr(self, 'properties_panel') and self.properties_panel:
                if field:
                    self.properties_panel.show_field_properties(field)
                    print("   📋 Properties panel updated with field data")
                else:
                    self.properties_panel.show_no_selection()
                    print("   📋 Properties panel showing no selection state")

            # Update info label
            if hasattr(self, 'control_info_label'):
                if field:
                    field_type = getattr(field, 'field_type', 'unknown')
                    field_id = getattr(field, 'id', 'unknown')
                    self.control_info_label.setText(f"Editing: {field_type} - {field_id}")
                else:
                    self.control_info_label.setText("Select a control to edit its properties")

            # Update placeholder if it exists
            if hasattr(self, 'properties_placeholder'):
                if field:
                    field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                    if hasattr(field_type, 'value'):
                        field_type = field_type.value
                    field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))
                    self.properties_placeholder.setText(f"Properties for {str(field_type).title()} field:\n{field_id}")
                else:
                    self.properties_placeholder.setText("Properties panel will appear here when a control is selected")

        except Exception as e:
            print(f"❌ Error updating properties display: {e}")
            import traceback
            traceback.print_exc()

    def deprecated_update_properties_display(self, field):
        """Update the properties display for the selected field"""
        try:
            if self.properties_panel:
                if field:
                    # Use the correct method name that exists in PropertiesPanel
                    self.properties_panel.show_field_properties(field)

                    # Get field info safely
                    field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                    if hasattr(field_type, 'value'):
                        field_type = field_type.value

                    field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))

                    self.control_info_label.setText(f"Editing: {str(field_type).title()} ({field_id})")
                else:
                    # Use the correct method name for clearing
                    self.properties_panel.show_no_selection()
                    self.control_info_label.setText("Select a control to edit its properties")
            else:
                # Update placeholder
                if field:
                    field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                    if hasattr(field_type, 'value'):
                        field_type = field_type.value
                    field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))
                    self.properties_placeholder.setText(f"Properties for {str(field_type).title()} field:\n{field_id}")
                else:
                    self.properties_placeholder.setText("Properties panel will appear here when a control is selected")

        except Exception as e:
            print(f"❌ Error updating properties display: {e}")
            import traceback
            traceback.print_exc()

    def add_field_to_list(self, field):
        """Add a new field to the control list"""
        if self.control_dropdown.itemText(0) == "No controls available":
            self.control_dropdown.clear()

        display_text = f"{field.field_type.title()} - {field.id}"
        if hasattr(field, 'properties') and 'name' in field.properties:
            display_text = f"{field.field_type.title()} - {field.properties['name']}"

        self.control_dropdown.addItem(display_text, field.id)

    def remove_field_from_list(self, field_id):
        """Remove a field from the control list"""
        for i in range(self.control_dropdown.count()):
            if self.control_dropdown.itemData(i) == field_id:
                self.control_dropdown.removeItem(i)
                # Clear current selection if removed field was selected
                if (hasattr(self, 'current_field') and
                        self.current_field and
                        getattr(self.current_field, 'id', None) == field_id):
                    self.current_field = None
                    self._update_properties_display(None)
                    print(f"  ✅ Cleared selection for deleted field: {field_id}")
                break

        if self.control_dropdown.count() == 0:
            self.control_dropdown.addItem("No controls available", None)

    def refresh_and_select_field(self, field_id):
        """Refresh the dropdown and select a specific field - useful for external calls"""
        print(f"🔄 Refreshing dropdown and selecting field: {field_id}")

        # First refresh the dropdown to ensure it has latest data
        self.refresh_control_list()

        # Then try to select the field
        if field_id and self.field_manager:
            field = self.field_manager.get_field_by_id(field_id)
            if field:
                self.set_selected_field(field)
                return True

        return False

    def ensure_no_selection_option(self):
        """Ensure dropdown has a 'No controls selected' option at the top"""
        if self.control_dropdown.count() == 0:
            self.control_dropdown.addItem("No controls selected", None)
            return

        # Check if first item is already a "no selection" item
        first_item_text = self.control_dropdown.itemText(0)
        first_item_data = self.control_dropdown.itemData(0)

        if first_item_data is None and ("No control" in first_item_text or "available" in first_item_text):
            # Update the text to be consistent
            self.control_dropdown.setItemText(0, "No controls selected")
            return

        # Add "No controls selected" at the top
        self.control_dropdown.insertItem(0, "No controls selected", None)

    def refresh_control_list(self):
        """Refresh the control list and ensure proper no-selection state"""
        print("🔄 Refreshing control list...")

        # Store current selection to restore if possible
        current_field_id = None
        if hasattr(self, 'current_field') and self.current_field:
            current_field_id = getattr(self.current_field, 'id', None)

        # Clear existing items
        self.control_dropdown.clear()

        # Always add "No controls selected" first
        self.control_dropdown.addItem("No controls selected", None)

        if not self.field_manager:
            print("  ⚠️ No field manager available")
            return

        # Get fields from field manager
        fields = []
        if hasattr(self.field_manager, 'get_all_fields'):
            fields = self.field_manager.get_all_fields()
        elif hasattr(self.field_manager, 'fields'):
            fields = self.field_manager.fields
        else:
            print("  ⚠️ Field manager has no recognizable fields method")
            return

        if not fields:
            print("  ℹ️ No fields found in field manager")
            return

        print(f"  ✅ Found {len(fields)} fields")
        restore_index = 0  # Default to "No controls selected"

        for field in fields:
            try:
                # Get field information
                field_type = getattr(field, 'field_type', getattr(field, 'type', 'unknown'))
                if hasattr(field_type, 'value'):
                    field_type = field_type.value

                field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))

                display_text = f"{str(field_type).title()} - {field_id}"

                if hasattr(field, 'properties') and isinstance(field.properties, dict) and 'name' in field.properties:
                    display_text = f"{str(field_type).title()} - {field.properties['name']}"

                self.control_dropdown.addItem(display_text, field_id)
                print(f"    Added: {display_text}")

                # Check if this was the previously selected field
                if current_field_id and field_id == current_field_id:
                    restore_index = self.control_dropdown.count() - 1

            except Exception as e:
                print(f"  ⚠️ Error adding field to dropdown: {e}")
                continue

        # Restore selection if field still exists, otherwise stay at "No controls selected"
        self.control_dropdown.blockSignals(True)
        self.control_dropdown.setCurrentIndex(restore_index)
        self.control_dropdown.blockSignals(False)

        if restore_index == 0:
            self.current_field = None
            self._update_properties_display(None)
            print("  📋 Reset to no selection state")
        else:
            print(f"  🔄 Restored selection to index {restore_index}")

    def select_no_control(self):
        """Explicitly select the 'No controls selected' option"""
        print("🚫 Selecting no control...")

        # Ensure the no-selection option exists
        self.ensure_no_selection_option()

        # Block signals to prevent recursive calls
        self.control_dropdown.blockSignals(True)

        try:
            # Select the first item (should be "No controls selected")
            self.control_dropdown.setCurrentIndex(0)
            print("   ✅ Dropdown set to 'No controls selected'")
        finally:
            self.control_dropdown.blockSignals(False)

        # Clear current field and update display
        self.current_field = None
        self._update_properties_display(None)

        print("   📋 Properties cleared for no selection")

    def handle_selection_changed(self, selected_fields):
        """Handle selection changes - decide what to do based on field count"""
        print(f"📋 Properties panel: Handling {len(selected_fields)} selected fields")

        if len(selected_fields) == 1:
            # Single field selected - show it
            field = selected_fields[0]
            self.set_selected_field(field)
            print(f"   ✅ Dropdown set to single selected field: {field.name} (ID: {field.id})")
        else:
            # 0 fields OR multiple fields - clear selection
            self.select_no_control()
            print("   ✅ Dropdown set to 'No controls selected'")

    # In PropertiesTab class (not PropertiesPanel):
    def update_field_position_size(self, field_id: str, x: int, y: int, width: int, height: int):
        """Update field position and size from external changes (move/resize operations)"""
        print(f"🚨 DEBUG: update_field_position_size called with {field_id}")

        # ✅ Check if the field_id matches the dropdown selection
        current_index = self.control_dropdown.currentIndex()
        selected_field_id = self.control_dropdown.itemData(current_index)

        print(f"🚨 DEBUG: Dropdown selected field_id = {selected_field_id}")
        print(f"🚨 DEBUG: Update requested for field_id = {field_id}")

        # Only update if this field is currently selected in the dropdown
        if selected_field_id != field_id:
            print(f"🚨 DEBUG: Skipping update - field {field_id} not selected in dropdown")
            return

        # ✅ Update through the properties panel
        if hasattr(self, 'properties_panel') and self.properties_panel:
            # Get the field object from field_manager
            if not self.field_manager:
                print(f"🚨 DEBUG: No field_manager available")
                return

            field = self.field_manager.get_field_by_id(field_id)
            if not field:
                print(f"🚨 DEBUG: Field {field_id} not found in field_manager")
                return

            # Update the field object
            field.x = x
            field.y = y
            field.width = width
            field.height = height

            # Update current_field reference
            self.current_field = field

            # Call the properties panel update method (the original one)
            self.properties_panel.update_field_position_size(field_id, x, y, width, height)

class TabbedFieldPalette(QWidget):
    """Main tabbed field palette widget"""

    fieldRequested = pyqtSignal(str)
    duplicateRequested = pyqtSignal()
    deleteRequested = pyqtSignal()
    alignRequested = pyqtSignal(str)
    propertyChanged = pyqtSignal(str, str, object)

    def __init__(self):
        super().__init__()
        self.field_manager = None
        self.init_ui()

        # Connect duplicate signal from quick actions
        if hasattr(self.controls_tab, 'quick_actions'):
            self.controls_tab.quick_actions.duplicateRequested.connect(self._on_duplicate_requested)

    def init_ui(self):
        """Initialize the tabbed interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.controls_tab = ControlsTab()
        self.properties_tab = PropertiesTab()

        # Add tabs to widget
        self.tab_widget.addTab(self.controls_tab, "Controls")
        self.tab_widget.addTab(self.properties_tab, "Properties")

        # Connect signals
        self.controls_tab.fieldRequested.connect(self.fieldRequested)
        self.controls_tab.duplicateRequested.connect(self.duplicateRequested)
        self.controls_tab.deleteRequested.connect(self.deleteRequested)
        self.controls_tab.alignRequested.connect(self.alignRequested)
        self.properties_tab.propertyChanged.connect(self.propertyChanged)

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        # Apply styling
        self._apply_tab_styles()

    def _apply_tab_styles(self):
        """Apply styling to the tab widget"""
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
        """)

    def set_field_manager(self, field_manager):
        """Set the field manager for both tabs"""
        self.field_manager = field_manager

        # Connect to the unified field list change signal
        if field_manager and hasattr(field_manager, 'field_list_changed'):
            try:
                field_manager.field_list_changed.connect(self.properties_tab.refresh_control_list)
                print("✅ Connected field_list_changed signal to refresh dropdown")
            except Exception as e:
                print(f"⚠️ Failed to connect field_list_changed signal: {e}")

        self.properties_tab.set_field_manager(field_manager)
        self.controls_tab.set_field_manager(field_manager)  # Add this line

    def set_field_selected(self, has_selection: bool, field=None):
        """Update both tabs based on field selection"""
        self.controls_tab.set_field_selected(has_selection)

        if has_selection and field:
            self.properties_tab.set_selected_field(field)
            # Switch to properties tab when a field is selected
            self.tab_widget.setCurrentIndex(1)
        elif not has_selection:
            self.properties_tab.set_selected_field(None)

    def add_field_to_list(self, field):
        """Add a new field to the properties tab"""
        self.properties_tab.add_field_to_list(field)

    def remove_field_from_list(self, field_id):
        """Remove a field from the properties tab"""
        self.properties_tab.remove_field_from_list(field_id)

    def refresh_control_list(self):
        """Refresh the control list in properties tab"""
        self.properties_tab.refresh_control_list()

    def clear_highlights(self):
        """Clear highlights in controls tab"""
        self.controls_tab.clear_highlights()

    def highlight_field_type(self, field_type: str):
        """Highlight a field type in controls tab"""
        self.controls_tab.highlight_field_type(field_type, True)

    def reset_selection(self):
        """Reset selection in controls tab"""
        self.controls_tab.reset_selection()

    def get_selected_field_type(self):
        """Get selected field type from controls tab"""
        return self.controls_tab.get_selected_field_type()

    def _get_main_window(self):
        """Get the main window safely"""
        try:
            widget = self
            while widget.parent():
                widget = widget.parent()
                if hasattr(widget, 'pdf_canvas') and hasattr(widget, 'field_manager'):
                    return widget
            return None
        except:
            return None

    def _on_duplicate_requested(self):
        """Handle duplicate request from field palette"""
        try:
            # Find main window and canvas
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'pdf_canvas'):
                main_window.pdf_canvas.duplicate_selected_fields()
            else:
                print("❌ Cannot find PDF canvas for duplication")
        except Exception as e:
            print(f"❌ Error handling duplicate request: {e}")