"""
Enhanced Field Renderer with Appearance Support
Updated field renderer that applies font, border, and background appearance properties
"""

from typing import List, Optional, Dict, Any
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt, QRect

from models.field_model import FormField, FieldType


class EnhancedFieldRenderer:
    """Enhanced field renderer with appearance property support"""

    def __init__(self):
        # Default colors (fallback when no appearance properties)
        self.default_selection_color = QColor(0, 120, 215)
        self.default_selection_bg_color = QColor(0, 120, 215, 30)
        self.default_normal_color = QColor(100, 100, 100)
        self.default_normal_bg_color = QColor(255, 255, 255, 150)
        self.default_text_color = QColor(0, 0, 0)
        self.default_font = QFont("Arial", 12)

    def render_fields(self, painter: QPainter, fields: List[FormField],
                      selected_field: Optional[FormField] = None, current_page: int = 0,
                      zoom_level: float = 1.0, coord_transform_func=None):
        """Render all form fields with appearance properties"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Filter fields for current page
        page_fields = [field for field in fields if getattr(field, 'page_number', 0) == current_page]

        for field in page_fields:
            is_selected = field == selected_field
            self.render_single_field(painter, field, is_selected, zoom_level, coord_transform_func)

    def render_single_field(self, painter: QPainter, field: FormField, is_selected: bool = False,
                            zoom_level: float = 1.0, coord_transform_func=None):
        """Render a single form field with appearance properties"""

        # Apply coordinate transformation if available
        if coord_transform_func:
            page_num = getattr(field, 'page_number', 0)
            screen_coords = coord_transform_func(page_num, field.x, field.y)
            if not screen_coords:
                return
            screen_x, screen_y = screen_coords
            screen_width = field.width * zoom_level
            screen_height = field.height * zoom_level
        else:
            screen_x, screen_y = field.x, field.y
            screen_width, screen_height = field.width, field.height

        # Get appearance properties
        appearance = field.properties.get('appearance', {})

        # Render field background
        self._render_field_background(painter, field, appearance, screen_x, screen_y,
                                      screen_width, screen_height, is_selected)

        # Render field border
        self._render_field_border(painter, field, appearance, screen_x, screen_y,
                                  screen_width, screen_height, is_selected)

        # Render field content
        self._render_field_content(painter, field, appearance, screen_x, screen_y,
                                   screen_width, screen_height, zoom_level)

        # Render field name (for debugging/selection)
        if is_selected:
            #self._render_field_name(painter, field, screen_x, screen_y)
            self._render_resize_handles(painter, screen_x, screen_y, screen_width, screen_height)

    def _render_field_background(self, painter: QPainter, field: FormField, appearance: Dict[str, Any],
                                 x: float, y: float, width: float, height: float, is_selected: bool):
        """Render field background using appearance properties"""

        # Get background color from appearance or use default
        if 'background_color' in appearance:
            bg_color = appearance['background_color']
            if isinstance(bg_color, QColor):
                # If fully transparent, don't draw background
                if bg_color.alpha() == 0:
                    return
            else:
                bg_color = self.default_normal_bg_color
        else:
            bg_color = self.default_selection_bg_color if is_selected else self.default_normal_bg_color

        # Convert coordinates to integers
        x, y, width, height = int(x), int(y), int(width), int(height)

        # Fill background
        painter.fillRect(x, y, width, height, bg_color)

    def _render_field_border(self, painter: QPainter, field: FormField, appearance: Dict[str, Any],
                             x: float, y: float, width: float, height: float, is_selected: bool):
        """Render field border using appearance properties"""

        # Get border properties from appearance
        border_props = appearance.get('border', {})

        # Border color
        if 'color' in border_props and isinstance(border_props['color'], QColor):
            border_color = border_props['color']
            # If transparent, don't draw border
            if border_color.alpha() == 0:
                return
        else:
            border_color = self.default_selection_color if is_selected else self.default_normal_color

        # Border width
        border_width_map = {
            'hairline': 0.5,
            'thin': 1,
            'medium': 2,
            'thick': 3
        }
        border_width = border_width_map.get(border_props.get('width', 'thin'), 1)
        if is_selected:
            border_width = max(border_width, 2)  # Selection always at least 2px

        # Border style
        border_style = border_props.get('style', 'solid')
        pen_style_map = {
            'solid': Qt.PenStyle.SolidLine,
            'dashed': Qt.PenStyle.DashLine,
            'dotted': Qt.PenStyle.DotLine
        }
        pen_style = pen_style_map.get(border_style, Qt.PenStyle.SolidLine)

        # Convert coordinates to integers
        x, y, width, height = int(x), int(y), int(width), int(height)

        # Set pen and draw border
        painter.setPen(QPen(border_color, border_width, pen_style))

        if border_style == 'underline':
            # Draw only bottom line for underline style
            painter.drawLine(x, y + height - 1, x + width, y + height - 1)
        elif border_style in ['beveled', 'inset']:
            # Draw 3D-style border (simplified)
            light_color = border_color.lighter(150)
            dark_color = border_color.darker(150)

            if border_style == 'beveled':
                # Raised effect
                painter.setPen(QPen(light_color, border_width))
                painter.drawLine(x, y, x + width - 1, y)  # Top
                painter.drawLine(x, y, x, y + height - 1)  # Left
                painter.setPen(QPen(dark_color, border_width))
                painter.drawLine(x + width - 1, y, x + width - 1, y + height - 1)  # Right
                painter.drawLine(x, y + height - 1, x + width - 1, y + height - 1)  # Bottom
            else:  # inset
                # Depressed effect
                painter.setPen(QPen(dark_color, border_width))
                painter.drawLine(x, y, x + width - 1, y)  # Top
                painter.drawLine(x, y, x, y + height - 1)  # Left
                painter.setPen(QPen(light_color, border_width))
                painter.drawLine(x + width - 1, y, x + width - 1, y + height - 1)  # Right
                painter.drawLine(x, y + height - 1, x + width - 1, y + height - 1)  # Bottom
        else:
            # Standard rectangular border
            painter.drawRect(x, y, width, height)

    def _render_field_content(self, painter: QPainter, field: FormField, appearance: Dict[str, Any],
                              x: float, y: float, width: float, height: float, zoom_level: float = 1.0):
        """Render field content using appearance properties"""

        # Get font properties
        font_props = appearance.get('font', {})
        text_color = appearance.get('text_color', self.default_text_color)
        text_alignment = appearance.get('text_alignment', 'left')

        # Create font
        font = self._create_font_from_properties(font_props, height, zoom_level)
        painter.setFont(font)

        # Set text color
        if isinstance(text_color, QColor):
            painter.setPen(QPen(text_color))
        else:
            painter.setPen(QPen(self.default_text_color))

        # Convert coordinates to integers
        x, y, width, height = int(x), int(y), int(width), int(height)

        self._render_field_name_label(painter, field, x, y, 1.5)

        # Render based on field type
        if field.type == FieldType.TEXT:
            self._render_text_field_content(painter, field, x, y, width, height, text_alignment)
        elif field.type == FieldType.CHECKBOX:
            self._render_checkbox_content(painter, field, x, y, width, height)
        elif field.type == FieldType.DROPDOWN:
            self._render_dropdown_content(painter, field, x, y, width, height, text_alignment)
        elif field.type == FieldType.SIGNATURE:
            self._render_signature_content(painter, field, x, y, width, height)
        elif field.type == FieldType.DATE:
            self._render_date_content(painter, field, x, y, width, height, text_alignment)
        elif field.type == FieldType.BUTTON:
            self._render_button_content(painter, field, x, y, width, height, text_alignment)
        elif field.type == FieldType.RADIO:
            self._render_radio_content(painter, field, x, y, width, height)
        elif field.type == FieldType.LABEL:
            self._render_label_content(painter, field, x, y, width, height, text_alignment)
        elif field.type == FieldType.FILE_UPLOAD:
            self._render_file_upload_content(painter, field, x, y, width, height, text_alignment)

    def _render_field_name_label(self, painter: QPainter, field: FormField,
                                 x: float, y: float, zoom_level: float = 1.0):
        """Render field name in black box above control with 50% opacity"""
        if not field.name:
            return

        painter.save()

        # Calculate font size based on zoom
        font_size = max(8, int(8 * zoom_level))
        name_font = QFont("Arial", font_size)
        painter.setFont(name_font)

        # Measure text dimensions
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(field.name)
        text_height = font_metrics.height()

        # Calculate padding (scaled with zoom)
        padding_x = max(4, int(4 * zoom_level))
        padding_y = max(2, int(3 * zoom_level))

        # Calculate box dimensions
        box_width = text_width + (padding_x * 2)
        box_height = text_height + (padding_y * 2)

        # Position box so its bottom almost touches control top
        box_x = int(x)
        box_y = int(y - box_height - 1)  # 1px gap between box and control

        # Draw black background box with 50% opacity
        box_rect = QRect(box_x, box_y, box_width, box_height)
        black_bg = QColor(0, 0, 0, 127)  # Black with 50% opacity (127 out of 255)
        painter.fillRect(box_rect, black_bg)

        # Draw white text with 50% opacity
        white_text = QColor(255, 255, 255, 127)  # White with 50% opacity (127 out of 255)
        painter.setPen(QPen(white_text))
        text_x = box_x + padding_x
        text_y = box_y + padding_y + font_metrics.ascent()
        painter.drawText(text_x, text_y, field.name)

        painter.restore()

    def _create_font_from_properties(self, font_props: Dict[str, Any], field_height: float, zoom_level: float) -> QFont:
        """Create QFont from font properties"""
        family = font_props.get('family', 'Arial')
        size = font_props.get('size', 12)
        bold = font_props.get('bold', False)
        italic = font_props.get('italic', False)

        # Handle auto-sizing
        if size == 'auto':
            # Auto-size based on field height and zoom
            size = max(8, int((field_height - 4) * zoom_level * 0.6))
        else:
            # Scale with zoom
            size = max(8, int(size * zoom_level))

        font = QFont(family, size)
        font.setBold(bold)
        font.setItalic(italic)

        return font

    def _get_text_alignment_flag(self, alignment: str) -> Qt.AlignmentFlag:
        """Convert text alignment string to Qt flag"""
        alignment_map = {
            'left': Qt.AlignmentFlag.AlignLeft,
            'center': Qt.AlignmentFlag.AlignCenter,
            'right': Qt.AlignmentFlag.AlignRight
        }
        return alignment_map.get(alignment, Qt.AlignmentFlag.AlignLeft)

    def _render_text_field_content(self, painter: QPainter, field: FormField,
                                   x: int, y: int, width: int, height: int, alignment: str):
        """Render text field content with alignment"""
        value = field.value if field.value else "Input Field"
        text_rect = painter.boundingRect(x + 5, y, width - 10, height,
                                         self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter,
                                         str(value))
        painter.drawText(text_rect, self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter,
                         str(value))

    def _render_checkbox_content(self, painter: QPainter, field: FormField,
                                 x: int, y: int, width: int, height: int):
        """Render checkbox content"""
        checkbox_size = min(width - 4, height - 4, 16)
        checkbox_x = x + (width - checkbox_size) // 2
        checkbox_y = y + (height - checkbox_size) // 2

        painter.drawRect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)

        # Draw checkmark if checked
        if field.properties.get('checked', False) or field.value:
            painter.drawLine(
                checkbox_x + 3, checkbox_y + checkbox_size // 2,
                checkbox_x + checkbox_size // 2, checkbox_y + checkbox_size - 3
            )
            painter.drawLine(
                checkbox_x + checkbox_size // 2, checkbox_y + checkbox_size - 3,
                checkbox_x + checkbox_size - 3, checkbox_y + 3
            )

    def _render_dropdown_content(self, painter: QPainter, field: FormField,
                                 x: int, y: int, width: int, height: int, alignment: str):
        """Render dropdown content with alignment"""
        text = field.value if field.value else "Select Option"
        display_text = f"{text} ▼"
        text_rect = painter.boundingRect(x + 5, y, width - 10, height,
                                         self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter,
                                         display_text)
        painter.drawText(text_rect, self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter,
                         display_text)

    def _render_signature_content(self, painter: QPainter, field: FormField,
                                  x: int, y: int, width: int, height: int):
        """Render signature field content"""
        painter.drawText(x + 5, y + height // 2 + 4, field.map_to)

        # Draw signature line
        line_y = y + height - 10
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawLine(x + 10, line_y, x + width - 10, line_y)

    def _render_date_content(self, painter: QPainter, field: FormField,
                             x: int, y: int, width: int, height: int, alignment: str):
        """Render date field content with alignment"""
        value = field.value if field.value else "DD/MM/YYYY"
        text_rect = painter.boundingRect(x + 5, y, width - 10, height,
                                         self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter,
                                         str(value))
        painter.drawText(text_rect, self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter,
                         str(value))

    def _render_button_content(self, painter: QPainter, field: FormField,
                               x: int, y: int, width: int, height: int, alignment: str):
        """Render button content with alignment"""
        button_text = field.properties.get('button_text', 'Click')
        text_rect = painter.boundingRect(x + 5, y, width - 10, height,
                                         self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter,
                                         button_text)
        painter.drawText(text_rect, self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter,
                         button_text)

    def _render_file_upload_content(self, painter: QPainter, field: FormField,
                                    x: int, y: int, width: int, height: int, alignment: str):
        """Render file upload field content - Modern Upload Box style"""

        # Get file upload properties
        accepted_types = field.properties.get("accepted_types", "All Files")
        max_size_mb = field.properties.get("max_size_mb", 10)
        multiple_files = field.properties.get("multiple_files", False)

        # Save current painter state
        painter.save()

        # Calculate icon size based on field height
        icon_size = min(height - 8, 16)
        icon_x = x + 8
        icon_y = y + (height - icon_size) // 2

        # Draw upload icon (⬆️ arrow)
        icon_rect = QRect(icon_x, icon_y, icon_size, icon_size)

        # Use Unicode arrow or draw simple arrow
        painter.setPen(QPen(QColor(70, 130, 180), 2))  # Blue color

        # Draw simple up arrow
        arrow_center_x = icon_x + icon_size // 2
        arrow_center_y = icon_y + icon_size // 2

        # Arrow shaft (vertical line)
        painter.drawLine(arrow_center_x, arrow_center_y + icon_size // 3,
                         arrow_center_x, arrow_center_y - icon_size // 3)

        # Arrow head (two lines forming ^)
        arrow_head_size = icon_size // 4
        painter.drawLine(arrow_center_x, arrow_center_y - icon_size // 3,
                         arrow_center_x - arrow_head_size, arrow_center_y - icon_size // 3 + arrow_head_size)
        painter.drawLine(arrow_center_x, arrow_center_y - icon_size // 3,
                         arrow_center_x + arrow_head_size, arrow_center_y - icon_size // 3 + arrow_head_size)

        # Main text: "Upload" + file type info
        text_x = icon_x + icon_size + 8
        text_y = y + height // 2

        # Build main text
        main_text = "Upload"

        # Add file type constraint if not "All Files"
        type_info = ""
        if accepted_types == "PDF":
            type_info = "PDF"
        elif accepted_types == "Images (PNG, JPG)":
            type_info = "Images"
        elif accepted_types == "Documents (DOC, DOCX)":
            type_info = "Documents"

        if type_info:
            main_text = f"Upload {type_info}"

        # Draw main text
        painter.setPen(QPen(QColor(70, 130, 180)))  # Blue to match icon
        main_font = painter.font()
        painter.setFont(main_font)
        painter.drawText(text_x, text_y + 4, main_text)

        # Draw secondary info (constraints) in smaller text below
        if height > 30:  # Only show secondary info if field is tall enough
            constraints = []

            # Add size limit
            if max_size_mb > 0:
                constraints.append(f"{max_size_mb}MB max")

            # Add multiple files indicator
            if multiple_files:
                constraints.append("Multiple files")

            if constraints:
                constraint_text = " • ".join(constraints)

                # Smaller font for constraints
                small_font = painter.font()
                small_font.setPointSize(max(8, small_font.pointSize() - 2))
                painter.setFont(small_font)

                painter.setPen(QPen(QColor(128, 128, 128)))  # Gray for secondary info
                painter.drawText(text_x, text_y + 16, constraint_text)

        # Restore painter state
        painter.restore()

    def _render_label_content(self, painter: QPainter, field: FormField,
                              x: int, y: int, width: int, height: int, alignment: str):

        print(f"🏷️ Enhanced renderer: Rendering label ")

        """Render label content with alignment"""
        # Get label text from properties or use default
        label_text = field.properties.get("label_text", field.value if field.value else field.map_to)

        # Get word wrap setting
        word_wrap = field.properties.get("word_wrap", True)

        # Get alignment flags (use the universal alignment from appearance)
        align_flag = self._get_text_alignment_flag(alignment) | Qt.AlignmentFlag.AlignVCenter

        # Add word wrap if enabled
        if word_wrap:
            align_flag |= Qt.TextFlag.TextWordWrap

        # Draw the label text
        text_rect = QRect(x + 2, y + 2, width - 4, height - 4)
        painter.drawText(text_rect, align_flag, str(label_text))

    # Convert alignment to Qt flags
    def _get_alignment_flags(self, alignment: str) -> Qt.AlignmentFlag:
        """Convert alignment string to Qt alignment flags"""
        alignment_map = {
            # Top row
            "Top Left": Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
            "Top Center": Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
            "Top Right": Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,

            # Middle row (vertical center)
            "Middle Left": Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            "Middle Center": Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter,
            "Middle Right": Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,

            # Bottom row
            "Bottom Left": Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
            "Bottom Center": Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            "Bottom Right": Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,

            # Legacy compatibility
            "Left": Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            "Center": Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter,
            "Right": Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
        }

        return alignment_map.get(alignment, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

    def _render_radio_content(self, painter: QPainter, field: FormField,
                              x: int, y: int, width: int, height: int):
        """Render radio button content"""
        radio_size = min(width - 4, height - 4, 16)
        radio_x = x + (width - radio_size) // 2
        radio_y = y + (height - radio_size) // 2

        # Draw radio circle
        painter.drawEllipse(radio_x, radio_y, radio_size, radio_size)

        # Draw selection dot if selected
        if field.properties.get('selected', False) or field.value:
            dot_size = radio_size // 3
            dot_x = radio_x + (radio_size - dot_size) // 2
            dot_y = radio_y + (radio_size - dot_size) // 2
            painter.setBrush(QBrush(painter.pen().color()))
            painter.drawEllipse(dot_x, dot_y, dot_size, dot_size)

    def _render_file_upload_field(self, painter: QPainter, field: FormField, x: int, y: int, width: int, height: int):
        """Render file upload field content - Simple Upload Icon + Text"""

        # Draw simple upload arrow icon
        icon_size = min(height - 6, 14)
        icon_x = x + 6
        icon_y = y + (height - icon_size) // 2

        # Simple up arrow
        painter.setPen(QPen(QColor(70, 130, 180), 2))
        arrow_center_x = icon_x + icon_size // 2
        arrow_center_y = icon_y + icon_size // 2

        # Arrow shaft
        painter.drawLine(arrow_center_x, arrow_center_y + icon_size // 3,
                         arrow_center_x, arrow_center_y - icon_size // 3)

        # Arrow head
        arrow_head_size = icon_size // 4
        painter.drawLine(arrow_center_x, arrow_center_y - icon_size // 3,
                         arrow_center_x - arrow_head_size, arrow_center_y - icon_size // 3 + arrow_head_size)
        painter.drawLine(arrow_center_x, arrow_center_y - icon_size // 3,
                         arrow_center_x + arrow_head_size, arrow_center_y - icon_size // 3 + arrow_head_size)

        # "Upload" text
        text_x = icon_x + icon_size + 8
        painter.setPen(QPen(QColor(70, 130, 180)))
        painter.drawText(text_x, y + height // 2 + 4, "Upload")

    def _render_field_name(self, painter: QPainter, field: FormField, x: int, y: int):
        """Render field name for debugging/selection"""
        painter.setPen(QPen(QColor(0, 120, 215)))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(x, y - 5, field.name)

    def _render_resize_handles(self, painter: QPainter, x: float, y: float, width: float, height: float):
        """Render resize handles for selected field"""
        handle_size = 8
        handle_color = QColor(0, 120, 215)
        handle_bg_color = QColor(255, 255, 255)

        # Convert to integers
        x, y, width, height = int(x), int(y), int(width), int(height)

        painter.setPen(QPen(handle_color, 1))
        painter.setBrush(QBrush(handle_bg_color))

        # Handle positions: corners and midpoints
        positions = [
            (x - handle_size // 2, y - handle_size // 2),  # Top-left
            (x + width // 2 - handle_size // 2, y - handle_size // 2),  # Top-middle
            (x + width - handle_size // 2, y - handle_size // 2),  # Top-right
            (x - handle_size // 2, y + height // 2 - handle_size // 2),  # Middle-left
            (x + width - handle_size // 2, y + height // 2 - handle_size // 2),  # Middle-right
            (x - handle_size // 2, y + height - handle_size // 2),  # Bottom-left
            (x + width // 2 - handle_size // 2, y + height - handle_size // 2),  # Bottom-middle
            (x + width - handle_size // 2, y + height - handle_size // 2)  # Bottom-right
        ]

        for hx, hy in positions:
            painter.drawRect(hx, hy, handle_size, handle_size)

    def render_grid(self, painter: QPainter, width: int, height: int, grid_size: int):
        """Render grid overlay"""
        pen = QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        # Vertical lines
        for x in range(0, width, grid_size):
            painter.drawLine(x, 0, x, height)

        # Horizontal lines
        for y in range(0, height, grid_size):
            painter.drawLine(0, y, width, y)