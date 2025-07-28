
"""
PDF Link Integration - Connects link system to main PDF viewer
Location: src/ui/pdf_link_integration.py
"""

from typing import Optional
from PyQt6.QtCore import QObject, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox
from src.core.a_pdf_link_manager import PDFLinkManager, PDFLink
from a_pdf_link_overlay import PDFLinkOverlayManager


class PDFLinkIntegration(QObject):
    """
    Integration helper that connects the link system to the main PDF viewer
    """
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.link_manager = PDFLinkManager(self)
        self.overlay_manager = None
        
        # Setup connections
        self._setup_connections()
        
        print("📎 PDFLinkIntegration initialized")
    
    def _setup_connections(self):
        """Set up signal connections"""
        # Connect link manager signals to main window navigation
        self.link_manager.internalLinkClicked.connect(self._handle_internal_navigation)
        self.link_manager.externalLinkClicked.connect(self._handle_external_link)
        self.link_manager.linkClicked.connect(self._handle_any_link_click)
    
    def integrate_with_canvas(self, canvas_widget):
        """
        Integrate link system with the PDF canvas widget
        
        Args:
            canvas_widget: The main PDF canvas widget
        """
        if not canvas_widget:
            print("❌ Cannot integrate links: no canvas widget")
            return
        
        print("📎 Integrating links with PDF canvas")
        
        # Create overlay manager as child of canvas
        self.overlay_manager = PDFLinkOverlayManager(canvas_widget)
        self.overlay_manager.set_link_manager(self.link_manager)
        
        # Position overlay manager to cover the entire canvas
        self.overlay_manager.setGeometry(canvas_widget.rect())
        
        # Connect canvas events
        if hasattr(canvas_widget, 'pageChanged'):
            canvas_widget.pageChanged.connect(self._on_page_changed)
        
        if hasattr(canvas_widget, 'zoomChanged'):
            canvas_widget.zoomChanged.connect(self._on_zoom_changed)
        
        # Connect to canvas resize events
        original_resize = canvas_widget.resizeEvent
        def enhanced_resize(event):
            original_resize(event)
            if self.overlay_manager:
                self.overlay_manager.setGeometry(canvas_widget.rect())
        canvas_widget.resizeEvent = enhanced_resize
        
        print("✅ Link integration with canvas complete")
    
    def set_pdf_document(self, pdf_document):
        """
        Set the PDF document for link extraction
        
        Args:
            pdf_document: PDF document object
        """
        self.link_manager.set_pdf_document(pdf_document)
        
        if self.overlay_manager:
            # Clear existing overlays when document changes
            self.overlay_manager.clear_overlays()
    
    @pyqtSlot(int)
    def _on_page_changed(self, page_num: int):
        """Handle page change event"""
        if self.overlay_manager:
            # Get current zoom level
            zoom_level = 1.0
            if hasattr(self.main_window, 'current_zoom'):
                zoom_level = self.main_window.current_zoom
            
            # Update overlays for new page
            self.overlay_manager.update_page_links(page_num, zoom_level)
    
    @pyqtSlot(float)
    def _on_zoom_changed(self, zoom_level: float):
        """Handle zoom change event"""
        if self.overlay_manager:
            self.overlay_manager.update_zoom(zoom_level)
    
    def _handle_internal_navigation(self, page_num: int, x: float, y: float):
        """Handle internal link navigation"""
        print(f"📍 Internal link navigation to page {page_num + 1} at ({x}, {y})")
        
        # Use the main window's navigation system
        if hasattr(self.main_window, 'navigate_to_page_with_coordinates'):
            self.main_window.navigate_to_page_with_coordinates(page_num, x, y)
        elif hasattr(self.main_window, '_navigate_to_page'):
            self.main_window._navigate_to_page(page_num)
        else:
            print("❌ No navigation method available in main window")
    
    def _handle_external_link(self, url: str):
        """Handle external link click"""
        print(f"🌐 External link clicked: {url}")
        
        # Show status message
        if hasattr(self.main_window, 'statusBar'):
            self.main_window.statusBar().showMessage(f"Opened external link: {url}", 3000)
    
    def _handle_any_link_click(self, link: PDFLink):
        """Handle any link click for logging/analytics"""
        print(f"📊 Link analytics: {link.link_type} link clicked on page {link.page_num + 1}")
        
        # Update status bar with link info
        if hasattr(self.main_window, 'statusBar'):
            status_msg = f"Link: {link.tooltip}"
            self.main_window.statusBar().showMessage(status_msg, 2000)
    
    def toggle_link_visibility(self, visible: bool):
        """Toggle visibility of all link overlays"""
        if self.overlay_manager:
            self.overlay_manager.toggle_link_visibility(visible)
    
    def get_link_statistics(self) -> dict:
        """Get statistics about current page links"""
        if self.overlay_manager:
            return self.overlay_manager.get_link_statistics()
        return {'total': 0, 'by_type': {}}