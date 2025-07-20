"""
User Interface Package
Contains all UI components and widgets
"""

from .pdf_canvas import PDFCanvas
from .field_palette import EnhancedFieldPalette
#from .property_widgets import PropertiesPanel
from .main_window import PDFViewerMainWindow
from .field_renderer import FieldRenderer
from .grid_control_popup import GridControlPopup

__all__ = [
    'PDFCanvas',
    'EnhancedFieldPalette',
    #'PropertiesPanel',
    'EnhancedPropertiesPanel',
    'PDFViewerMainWindow',
    'GridControlPopup'
    'FieldRenderer',
    'EnhancedFieldRenderer',      # ← ADD this
    'DragHandler',
    'SelectionHandler'
]

# ============================================================================