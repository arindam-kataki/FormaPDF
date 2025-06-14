"""
Icon Utilities
Helper functions for creating application icons and UI graphics
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QRect


def create_app_icon(size: int = 32) -> QIcon:
    """
    Create a simple application icon programmatically

    Args:
        size: Icon size in pixels

    Returns:
        QIcon object
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    painter.setBrush(QBrush(QColor(0, 120, 215)))  # Blue
    painter.setPen(QPen(QColor(255, 255, 255), 2))
    margin = 2
    painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)

    # PDF text
    painter.setPen(QPen(QColor(255, 255, 255)))
    painter.setFont(QFont("Arial", max(6, size // 4), QFont.Weight.Bold))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "PDF")

    painter.end()

    return QIcon(pixmap)


def create_field_icon(field_type: str, size: int = 16) -> QIcon:
    """
    Create an icon for a specific field type

    Args:
        field_type: Type of field ('text', 'checkbox', etc.)
        size: Icon size in pixels

    Returns:
        QIcon object
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Base styling
    painter.setPen(QPen(QColor(100, 100, 100), 1))
    painter.setBrush(QBrush(QColor(240, 240, 240)))

    if field_type == "text":
        # Text field rectangle
        painter.drawRect(1, size // 3, size - 2, size // 3)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", max(4, size // 6)))
        painter.drawText(3, size // 2 + 2, "abc")

    elif field_type == "checkbox":
        # Checkbox square
        checkbox_size = size - 4
        painter.drawRect(2, 2, checkbox_size, checkbox_size)
        # Checkmark
        painter.setPen(QPen(QColor(0, 120, 0), 2))
        painter.drawLine(4, size // 2, size // 2, size - 4)
        painter.drawLine(size // 2, size - 4, size - 2, 4)

    elif field_type == "dropdown":
        # Dropdown rectangle
        painter.drawRect(1, size // 3, size - 2, size // 3)
        # Arrow
        painter.setPen(QPen(QColor(0, 0, 0)))
        arrow_x = size - 6
        arrow_y = size // 2
        painter.drawLine(arrow_x - 2, arrow_y - 1, arrow_x, arrow_y + 1)
        painter.drawLine(arrow_x, arrow_y + 1, arrow_x + 2, arrow_y - 1)

    elif field_type == "signature":
        # Signature line
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(2, size - 4, size - 2, size - 4)
        # Pen/signature mark
        painter.setPen(QPen(QColor(0, 0, 200), 2))
        painter.drawLine(4, size - 6, size // 2, size // 2)
        painter.drawLine(size // 2, size // 2, size - 4, size - 8)

    elif field_type == "date":
        # Calendar icon
        painter.drawRect(2, 3, size - 4, size - 5)
        # Calendar grid
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        for i in range(1, 3):
            y = 3 + i * (size - 5) // 3
            painter.drawLine(2, y, size - 2, y)
        for i in range(1, 3):
            x = 2 + i * (size - 4) // 3
            painter.drawLine(x, 3, x, size - 2)

    elif field_type == "button":
        # Button with 3D effect
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        painter.drawRect(1, size // 4, size - 2, size // 2)
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", max(4, size // 6)))
        painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "OK")

    elif field_type == "radio":
        # Radio button circle
        radio_size = size - 4
        painter.drawEllipse(2, 2, radio_size, radio_size)
        # Selected dot
        painter.setBrush(QBrush(QColor(0, 120, 0)))
        dot_size = radio_size // 2
        dot_offset = (size - dot_size) // 2
        painter.drawEllipse(dot_offset, dot_offset, dot_size, dot_size)

    painter.end()

    return QIcon(pixmap)


def create_toolbar_icons():
    """
    Create a dictionary of common toolbar icons

    Returns:
        Dict mapping action names to QIcon objects
    """
    icons = {}

    # File operations
    icons['open'] = create_file_icon('open')
    icons['save'] = create_file_icon('save')
    icons['export'] = create_file_icon('export')

    # Navigation
    icons['prev'] = create_nav_icon('left')
    icons['next'] = create_nav_icon('right')

    # Zoom
    icons['zoom_in'] = create_zoom_icon('+')
    icons['zoom_out'] = create_zoom_icon('-')

    # View
    icons['grid'] = create_grid_icon()
    icons['fit_width'] = create_fit_icon()

    return icons


def create_file_icon(action: str, size: int = 16) -> QIcon:
    """Create file operation icons"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if action == 'open':
        # Folder icon
        painter.setBrush(QBrush(QColor(255, 206, 84)))
        painter.setPen(QPen(QColor(200, 150, 0)))
        painter.drawRect(2, size // 2, size - 4, size // 2 - 1)
        painter.drawRect(2, size // 3, size // 2, size // 6)

    elif action == 'save':
        # Floppy disk icon
        painter.setBrush(QBrush(QColor(100, 100, 100)))
        painter.setPen(QPen(QColor(50, 50, 50)))
        painter.drawRect(2, 1, size - 4, size - 2)
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.drawRect(3, 2, size - 6, size // 3)

    elif action == 'export':
        # Arrow pointing out of box
        painter.setPen(QPen(QColor(0, 120, 0), 2))
        painter.drawRect(2, size // 2, size - 4, size // 2 - 1)
        painter.drawLine(size // 2, 2, size // 2, size // 2)
        painter.drawLine(size // 2 - 2, 4, size // 2, 2)
        painter.drawLine(size // 2 + 2, 4, size // 2, 2)

    painter.end()
    return QIcon(pixmap)


def create_nav_icon(direction: str, size: int = 16) -> QIcon:
    """Create navigation arrow icons"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(0, 0, 0), 2))

    center_y = size // 2
    if direction == 'left':
        painter.drawLine(size - 4, center_y - 3, 4, center_y)
        painter.drawLine(4, center_y, size - 4, center_y + 3)
    elif direction == 'right':
        painter.drawLine(4, center_y - 3, size - 4, center_y)
        painter.drawLine(size - 4, center_y, 4, center_y + 3)

    painter.end()
    return QIcon(pixmap)


def create_zoom_icon(symbol: str, size: int = 16) -> QIcon:
    """Create zoom icons"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Magnifying glass circle
    painter.setPen(QPen(QColor(0, 0, 0), 2))
    circle_size = size - 6
    painter.drawEllipse(1, 1, circle_size, circle_size)

    # Handle
    painter.drawLine(circle_size - 1, circle_size - 1, size - 2, size - 2)

    # Plus or minus symbol
    painter.setPen(QPen(QColor(0, 0, 0), 1))
    center = circle_size // 2
    if symbol == '+':
        painter.drawLine(center - 2, center, center + 2, center)
        painter.drawLine(center, center - 2, center, center + 2)
    elif symbol == '-':
        painter.drawLine(center - 2, center, center + 2, center)

    painter.end()
    return QIcon(pixmap)


def create_grid_icon(size: int = 16) -> QIcon:
    """Create grid toggle icon"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setPen(QPen(QColor(100, 100, 100), 1))

    # Grid lines
    grid_spacing = size // 4
    for i in range(0, size + 1, grid_spacing):
        painter.drawLine(i, 0, i, size)
        painter.drawLine(0, i, size, i)

    painter.end()
    return QIcon(pixmap)


def create_fit_icon(size: int = 16) -> QIcon:
    """Create fit-to-width icon"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setPen(QPen(QColor(0, 0, 0), 1))

    # Rectangle representing page
    painter.drawRect(3, 2, size - 6, size - 4)

    # Arrows pointing outward
    painter.drawLine(1, size // 2, 3, size // 2 - 1)
    painter.drawLine(1, size // 2, 3, size // 2 + 1)
    painter.drawLine(size - 1, size // 2, size - 3, size // 2 - 1)
    painter.drawLine(size - 1, size // 2, size - 3, size // 2 + 1)

    painter.end()
    return QIcon(pixmap)