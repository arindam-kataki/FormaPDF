"""
Main Application Window
Clean working version of the PDF Voice Editor main window
"""

import sys
import json
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QLabel, QToolBar, QStatusBar, QPushButton,
    QComboBox, QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtGui import QAction, QKeySequence, QFont, QColor
from PyQt6.QtCore import Qt, pyqtSlot, QSettings, QRect

# Safe imports with fallbacks

from typing import TYPE_CHECKING, Dict, Any
if TYPE_CHECKING:
    from .project_management_mixin import ProjectManagementMixin

# Import the mixin
from .project_management_mixin import ProjectManagementMixin

try:
    from ui.pdf_canvas import PDFCanvas
    PDF_CANVAS_AVAILABLE = True
except ImportError:
    print("Warning: PDFCanvas not available")
    PDFCanvas = None
    PDF_CANVAS_AVAILABLE = False

try:
    from ui.field_palette import EnhancedFieldPalette
    from ui.tabbed_field_palette import TabbedFieldPalette
    from ui.properties_panel import PropertiesPanel
    FIELD_PALETTE_AVAILABLE = True
except ImportError:
    print("Warning: FieldPalette not available")
    EnhancedFieldPalette = None
    FIELD_PALETTE_AVAILABLE = False

try:
    from ui.properties_panel import PropertiesPanel
    PROPERTIES_PANEL_AVAILABLE = True
except ImportError:
    print("Warning: PropertiesPanel not available")
    PropertiesPanel = None
    PROPERTIES_PANEL_AVAILABLE = False

try:
    from models.field_model import FormField
    FIELD_MODEL_AVAILABLE = True
except ImportError:
    print("Warning: FormField model not available")
    FormField = None
    FIELD_MODEL_AVAILABLE = False

try:
    from utils.icon_utils import create_app_icon
    ICON_UTILS_AVAILABLE = True
except ImportError:
    print("Warning: Icon utils not available")
    create_app_icon = None
    ICON_UTILS_AVAILABLE = False

from .toolbar_manager import ToolbarManager
try:
    from src.ui.grid_manager import GridManager
    print("✅ GridManager import successful")
except ImportError as e:
    print(f"❌ GridManager import failed: {e}")

class PDFViewerMainWindow(QMainWindow, ProjectManagementMixin, ToolbarManager):
    """Main application window with safe fallbacks"""

    def __init__(self):
        super().__init__()
        self.current_pdf_path = None

        self.init_toolbar_manager()
        self.init_project_management()  # type: ignore

        self.init_ui()
        self.setup_connections()
        self.setup_scroll_tracking()
        self.setup_scroll_timer()

    def setup_scroll_timer(self):
        """Setup timer-based scroll rendering"""
        from PyQt6.QtCore import QTimer

        # Create timer for scroll rendering
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)  # Only fire once per scroll session
        self.scroll_timer.timeout.connect(self.render_after_scroll)

        # Flags to track what needs updating
        self.needs_scroll_update = False
        self.needs_zoom_update = False

        print("✅ Timer-based scroll rendering initialized")

    def setup_enhanced_grid(self):
        """Set up enhanced grid functionality"""
        try:
            from src.ui.grid_manager import GridManager
            from PyQt6.QtGui import QColor

            # Create the grid manager
            self.grid_manager = GridManager(self)

            # CONNECT TO YOUR CANVAS
            if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
                self.connect_grid_to_canvas()

                # 🧲 ADD SNAP-TO-GRID CONNECTION HERE 🧲
                # Connect grid manager to drag handler for snap functionality
                if hasattr(self.pdf_canvas, 'enhanced_drag_handler'):
                    self.pdf_canvas.enhanced_drag_handler.set_grid_manager(self.grid_manager)
                    print("🧲 Connected grid manager to drag handler for snap-to-grid")
                # 🧲 END SNAP CONNECTION 🧲

            # CONNECT TO YOUR CANVAS
            if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
                self.connect_grid_to_canvas()

            # Test basic functionality
            print("🔧 Testing GridManager with loaded PDF...")

            # Show grid
            #self.grid_manager.show_grid()
            #print(f"Grid visible: {self.grid_manager.is_grid_visible()}")

            # Try setting a blue color
            blue_color = QColor(0, 100, 200, 150)  # Blue with transparency
            self.grid_manager.set_grid_color(blue_color)
            print(f"Grid color set to: {blue_color.name()}")

            # Set spacing
            self.grid_manager.set_spacing(25)
            print(f"Grid spacing: {self.grid_manager.get_spacing()}px")

            print("✅ GridManager basic test completed!")

        except Exception as e:
            print(f"❌ GridManager test failed: {e}")

    def connect_grid_to_canvas(self):
        """Connect GridManager to PDF canvas"""
        # Connect GridManager changes to canvas updates
        self.grid_manager.grid_visibility_changed.connect(self.update_canvas_grid_visibility)
        self.grid_manager.grid_color_changed.connect(self.update_canvas_grid_color)
        self.grid_manager.grid_spacing_changed.connect(self.update_canvas_grid_spacing)
        self.grid_manager.grid_offset_changed.connect(self.update_canvas_grid_offset)

        print("🔗 GridManager connected to canvas")

    def update_canvas_grid_visibility(self, visible):
        """Update canvas grid visibility"""
        if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
            self.pdf_canvas.show_grid = visible
            self.pdf_canvas.draw_overlay()  # This will trigger the redraw
            print(f"📐 Canvas grid visibility updated: {visible}")

    def update_canvas_grid_color(self, color):
        """Update canvas grid color"""
        if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
            self.pdf_canvas.grid_color = color
            self.pdf_canvas.draw_overlay()  # This will trigger the redraw
            print(f"📐 Canvas grid color updated: {color.name()}")

    def update_canvas_grid_spacing(self, spacing):
        """Update canvas grid spacing"""
        if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
            self.pdf_canvas.grid_size = spacing  # Your canvas uses grid_size
            self.pdf_canvas.draw_overlay()  # This will trigger the redraw
            print(f"📐 Canvas grid spacing updated: {spacing}px")

    def update_canvas_grid_offset(self, offset_x, offset_y):
        """Update canvas grid offset"""
        if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
            self.pdf_canvas.grid_offset_x = offset_x
            self.pdf_canvas.grid_offset_y = offset_y
            self.pdf_canvas.draw_overlay()  # This will trigger the redraw
            print(f"📐 Canvas grid offset updated: ({offset_x}, {offset_y})")

    def init_ui(self):
        """Initialize the user interface"""
                # Window setup - Enhanced for resizability
        self.setWindowTitle("PDF Voice Editor - Enhanced with Draggable Fields")

        # Set initial size and make fully resizable
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(800, 600)  # Minimum usable size

        # Remove any size constraints that might prevent resizing
        self.setMaximumSize(16777215, 16777215)  # Qt's maximum size

        # Set size policy to allow growing and shrinking
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Enable window resizing (this should be default, but make it explicit)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)

        # Show the window initially in a normal state (not maximized/minimized)
        self.setWindowState(Qt.WindowState.WindowNoState)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # Create panels
        self.left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()

        # Initially hide left panel until PDF is loaded
        self.left_panel.setVisible(False)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(center_panel)
        self.splitter.setSizes([0, 1200])

        # Create UI components
        self.create_status_bar()
        self.create_toolbar()
        self.setup_scroll_shortcuts()
        self.enable_smooth_scrolling()

    def create_left_panel(self) -> QWidget:
        """Create left panel with field palette and properties"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # Field palette (with fallback)
        if FIELD_PALETTE_AVAILABLE and EnhancedFieldPalette:
            #self.field_palette = EnhancedFieldPalette()
            self.field_palette = TabbedFieldPalette()
            if hasattr(self, 'field_manager'):
                self.field_palette.set_field_manager(self.field_manager)
            left_layout.addWidget(self.field_palette)
        else:
            # Fallback widget
            self.field_palette = QLabel("Field Palette\n(Not Available)")
            self.field_palette.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.field_palette.setStyleSheet("border: 1px solid #ccc; padding: 20px;")
            left_layout.addWidget(self.field_palette)

        # Properties panel (with fallback)
        if PROPERTIES_PANEL_AVAILABLE and PropertiesPanel:
            self.properties_panel = PropertiesPanel()
            left_layout.addWidget(self.properties_panel)
        else:
            # Fallback widget
            self.properties_panel = QLabel("Properties Panel\n(Not Available)")
            self.properties_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.properties_panel.setStyleSheet("border: 1px solid #ccc; padding: 20px;")
            left_layout.addWidget(self.properties_panel)

        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(350)
        left_widget.setMinimumWidth(250)
        left_widget.setVisible(False)

        return left_widget

    def show_left_panel(self):
        """Show the left panel and adjust splitter sizes"""
        if hasattr(self, 'left_panel'):
            print("📋 Making left panel visible...")
            self.left_panel.setVisible(True)

            # Force immediate layout update before rendering
            self.left_panel.updateGeometry()
            self.splitter.updateGeometry()
            QApplication.processEvents()  # Process pending layout events

            # Restore normal proportions: 25% left, 75% center
            total_width = self.width()
            left_width = max(250, min(350, total_width * 0.25))
            center_width = total_width - left_width
            self.splitter.setSizes([int(left_width), int(center_width)])

            print(f"✅ Left panel shown with width: {left_width}px")
        else:
            print("⚠️ Left panel reference not found")

    def hide_left_panel(self):
        """Hide the left panel and give full space to center"""
        if hasattr(self, 'left_panel'):
            print("📋 Hiding left panel...")
            self.left_panel.setVisible(False)
            # Give all space to center panel
            self.splitter.setSizes([0, self.width()])
            print("✅ Left panel hidden")
        else:
            print("⚠️ Left panel reference not found")

    def toggle_left_panel(self):
        """Toggle the visibility of the left panel"""
        if hasattr(self, 'left_panel'):
            if self.left_panel.isVisible():
                self.hide_left_panel()
            else:
                self.show_left_panel()

    def create_menu_bar(self):
        """Create menu bar using project management mixin"""
        menubar = self.menuBar()

        # File Menu - handled by mixin
        file_menu = menubar.addMenu("&File")
        self.create_project_menu_items(file_menu)  # type: ignore

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Your other menus
        edit_menu = menubar.addMenu("&Edit")
        view_menu = menubar.addMenu("&View")
        tools_menu = menubar.addMenu("&Tools")
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_center_panel(self) -> QWidget:
        """Create center panel with PDF viewer"""
        # Scroll area for PDF canvas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Configure scroll bars (removed the local import)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Configure smooth scrolling via scroll bar settings
        v_scrollbar = self.scroll_area.verticalScrollBar()
        h_scrollbar = self.scroll_area.horizontalScrollBar()

        if v_scrollbar:
            v_scrollbar.setSingleStep(10)
            v_scrollbar.setPageStep(100)
        if h_scrollbar:
            h_scrollbar.setSingleStep(10)
            h_scrollbar.setPageStep(100)

        # Create PDF canvas (add this missing part)
        if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
            pass  # PDF canvas already exists
        else:
            # Create PDF canvas or fallback
            try:
                from ui.pdf_canvas import PDFCanvas
                self.pdf_canvas = PDFCanvas()
            except ImportError:
                # Fallback if PDFCanvas not available
                self.pdf_canvas = QLabel(
                    "PDF Canvas Not Available\n\n"
                    "Some modules are missing.\n"
                    "Application running in limited mode."
                )
                self.pdf_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.pdf_canvas.setStyleSheet("""
                    border: 2px dashed #ccc; 
                    background-color: #f9f9f9; 
                    color: #666;
                    font-size: 14px;
                    padding: 40px;
                """)

        self.scroll_area.setWidget(self.pdf_canvas)

        # Debug: Print scroll area configuration
        print(f"📏 Scroll area configured:")
        print(f"  Widget resizable: {self.scroll_area.widgetResizable()}")
        print(f"  H scroll policy: {self.scroll_area.horizontalScrollBarPolicy()}")
        print(f"  V scroll policy: {self.scroll_area.verticalScrollBarPolicy()}")
        return self.scroll_area

    def depecated_create_toolbar(self):
        """Create complete toolbar with page jump and zoom controls"""
        # Create main toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # ADD THIS LINE - Project management buttons (handled by mixin)
        project_actions = self.create_project_toolbar_actions(toolbar)  # type: ignore

        # File operations
        open_action = QAction("📁 Open", self)
        open_action.setToolTip("Open PDF file (Ctrl+O)")
        open_action.setShortcut("Ctrl+O")
        #open_action.triggered.connect(self.open_pdf)
        toolbar.addAction(open_action)

        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save form data (Ctrl+S)")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_form_data)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Navigation controls with page input
        prev_action = QAction("⬅️", self)
        prev_action.setToolTip("Previous page")
        prev_action.triggered.connect(self.previous_page)
        toolbar.addAction(prev_action)

        # Page input control
        from PyQt6.QtWidgets import QSpinBox, QLabel
        page_label = QLabel("Page:")
        toolbar.addWidget(page_label)

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)  # Will be updated when PDF loads
        self.page_spinbox.setValue(1)
        self.page_spinbox.setToolTip("Jump to page number")
        self.page_spinbox.valueChanged.connect(self.jump_to_page)
        self.page_spinbox.setMinimumWidth(60)
        toolbar.addWidget(self.page_spinbox)

        # Page count label
        self.page_count_label = QLabel("of 1")
        self.page_count_label.setStyleSheet("color: #666; margin-right: 8px;")
        toolbar.addWidget(self.page_count_label)

        next_action = QAction("➡️", self)
        next_action.setToolTip("Next page")
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Zoom controls with percentage selector
        zoom_out_action = QAction("🔍-", self)
        zoom_out_action.setToolTip("Zoom out")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        # Zoom percentage dropdown
        from PyQt6.QtWidgets import QComboBox
        zoom_label = QLabel("Zoom:")
        toolbar.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.setEditable(True)
        zoom_levels = ["25%", "50%", "75%", "100%", "125%", "150%", "200%", "300%", "400%", "Fit Width", "Fit Page"]
        self.zoom_combo.addItems(zoom_levels)
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setToolTip("Set zoom level")
        self.zoom_combo.currentTextChanged.connect(self.set_zoom_level)
        self.zoom_combo.setMinimumWidth(100)
        toolbar.addWidget(self.zoom_combo)

        zoom_in_action = QAction("🔍+", self)
        zoom_in_action.setToolTip("Zoom in")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        toolbar.addSeparator()

        # Quick fit actions
        fit_width_action = QAction("📏 Fit Width", self)
        fit_width_action.setToolTip("Fit page to window width")
        fit_width_action.triggered.connect(self.fit_width)
        toolbar.addAction(fit_width_action)

        fit_page_action = QAction("📄 Fit Page", self)
        fit_page_action.setToolTip("Fit entire page in window")
        fit_page_action.triggered.connect(self.fit_page)
        toolbar.addAction(fit_page_action)

        toolbar.addSeparator()

        # View controls
        self.grid_action = QAction("📐", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setToolTip("Toggle grid display")
        self.grid_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_action)

        # Grid controls section (add after existing grid toggle)
        toolbar.addSeparator()

        # Grid size controls
        grid_size_decrease = QAction("🔍-📐", self)
        grid_size_decrease.setToolTip("Decrease grid size (Ctrl+Shift+-)")
        grid_size_decrease.triggered.connect(self.decrease_grid_size)
        toolbar.addAction(grid_size_decrease)

        grid_size_increase = QAction("🔍+📐", self)
        grid_size_increase.setToolTip("Increase grid size (Ctrl+Shift+=)")
        grid_size_increase.triggered.connect(self.increase_grid_size)
        toolbar.addAction(grid_size_increase)

        toolbar.addSeparator()

        # Grid movement controls
        grid_up = QAction("📐⬆️", self)
        grid_up.setToolTip("Move grid up (Ctrl+Shift+Up)")
        grid_up.triggered.connect(self.move_grid_up)
        toolbar.addAction(grid_up)

        grid_down = QAction("📐⬇️", self)
        grid_down.setToolTip("Move grid down (Ctrl+Shift+Down)")
        grid_down.triggered.connect(self.move_grid_down)
        toolbar.addAction(grid_down)

        grid_left = QAction("📐⬅️", self)
        grid_left.setToolTip("Move grid left (Ctrl+Shift+Left)")
        grid_left.triggered.connect(self.move_grid_left)
        toolbar.addAction(grid_left)

        grid_right = QAction("📐➡️", self)
        grid_right.setToolTip("Move grid right (Ctrl+Shift+Right)")
        grid_right.triggered.connect(self.move_grid_right)
        toolbar.addAction(grid_right)

        # Grid reset
        grid_reset = QAction("📐🎯", self)
        grid_reset.setToolTip("Reset grid offset (Ctrl+Shift+0)")
        grid_reset.triggered.connect(self.reset_grid_offset)
        toolbar.addAction(grid_reset)

        # Panel toggle
        self.panel_toggle_action = QAction("📋 Panel", self)
        self.panel_toggle_action.setCheckable(True)
        self.panel_toggle_action.setChecked(False)  # Initially hidden
        self.panel_toggle_action.setToolTip("Show/hide controls and properties panel")
        self.panel_toggle_action.triggered.connect(self.toggle_left_panel)
        toolbar.addAction(self.panel_toggle_action)

        toolbar.addSeparator()

        # Info
        info_action = QAction("ℹ️", self)
        info_action.setToolTip("Show application information")
        info_action.triggered.connect(self.show_info)
        toolbar.addAction(info_action)

        # Ensure toolbar is visible
        toolbar.show()
        print("🔧 Enhanced toolbar created with page jump and zoom controls")

    def create_status_bar(self):
        """Create status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Status label
        self.field_info_label = QLabel("Ready")
        status_bar.addWidget(self.field_info_label)

        # Module status
        missing_modules = []
        if not PDF_CANVAS_AVAILABLE:
            missing_modules.append("PDFCanvas")
        if not FIELD_PALETTE_AVAILABLE:
            missing_modules.append("FieldPalette")
        if not PROPERTIES_PANEL_AVAILABLE:
            missing_modules.append("PropertiesPanel")

        if missing_modules:
            module_status = QLabel(f"Missing: {', '.join(missing_modules)}")
            module_status.setStyleSheet("color: orange;")
            status_bar.addPermanentWidget(module_status)
        else:
            status_bar.addPermanentWidget(QLabel("All modules loaded"))

    def setup_connections(self):
        
        # Restore window state from previous session
        self.restore_window_state()
        """Setup signal connections between components safely"""
        try:
            # Field palette connections - check both object and signal exist
            if (hasattr(self, 'field_palette') and 
                self.field_palette is not None and 
                hasattr(self.field_palette, 'fieldRequested')):
                try:
                    self.field_palette.fieldRequested.connect(self._on_field_type_selected)
                    print("  ✅ Connected field_palette.fieldRequested")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect fieldRequested: {e}")

            # Property change connection for the Properties tab
            if (hasattr(self, 'field_palette') and
                    self.field_palette is not None and
                    hasattr(self.field_palette, 'propertyChanged')):
                try:
                    self.field_palette.propertyChanged.connect(self.on_property_changed)
                    print("  ✅ Connected field_palette.propertyChanged")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect propertyChanged: {e}")

            if (hasattr(self, 'field_palette') and 
                self.field_palette is not None and 
                hasattr(self.field_palette, 'duplicateRequested')):
                try:
                    self.field_palette.duplicateRequested.connect(lambda: print("Duplicate requested"))
                    print("  ✅ Connected field_palette.duplicateRequested")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect duplicateRequested: {e}")

            if (hasattr(self, 'field_palette') and 
                self.field_palette is not None and 
                hasattr(self.field_palette, 'deleteRequested')):
                try:
                    self.field_palette.deleteRequested.connect(lambda: print("Delete requested"))
                    print("  ✅ Connected field_palette.deleteRequested")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect deleteRequested: {e}")

            # PDF canvas connections - check both object and signal exist
            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'fieldClicked')):
                try:
                    self.pdf_canvas.fieldClicked.connect(self.on_field_clicked)
                    print("  ✅ Connected pdf_canvas.fieldClicked")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect fieldClicked: {e}")

            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'fieldMoved')):
                try:
                    self.pdf_canvas.fieldMoved.connect(self.on_field_moved)
                    print("  ✅ Connected pdf_canvas.fieldMoved")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect fieldMoved: {e}")

            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'fieldResized')):
                try:
                    self.pdf_canvas.fieldResized.connect(self.on_field_resized)
                    print("  ✅ Connected pdf_canvas.fieldResized")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect fieldResized: {e}")

            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'positionClicked')):
                try:
                    self.pdf_canvas.positionClicked.connect(self.on_position_clicked)
                    print("  ✅ Connected pdf_canvas.positionClicked")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect positionClicked: {e}")

            # MULTI-SELECTION: Connect to FieldManager instead of canvas selectionChanged
            if (hasattr(self, 'pdf_canvas') and
                    self.pdf_canvas is not None and
                    hasattr(self.pdf_canvas, 'field_manager') and
                    hasattr(self.pdf_canvas.field_manager, 'selection_changed')):
                try:
                    self.pdf_canvas.field_manager.selection_changed.connect(self.on_multi_selection_changed)
                    print("  ✅ Connected FieldManager.selection_changed for multi-select")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect multi-selection: {e}")

            """
            if (hasattr(self, 'pdf_canvas') and 
                self.pdf_canvas is not None and 
                hasattr(self.pdf_canvas, 'selectionChanged')):
                try:
                    self.pdf_canvas.selectionChanged.connect(self.on_selection_changed)
                    print("  ✅ Connected pdf_canvas.selectionChanged")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect selectionChanged: {e}")
            """

            # Properties panel connections - check both object and signal exist
            """
            if (hasattr(self, 'properties_panel') and 
                self.properties_panel is not None and 
                hasattr(self.properties_panel, 'propertyChanged')):
                try:
                    self.properties_panel.propertyChanged.connect(self.on_property_changed)
                    print("  ✅ Connected properties_panel.propertyChanged")
                except Exception as e:
                    print(f"  ⚠️ Failed to connect propertyChanged: {e}")

            """

            # 🔧 SIMPLE: Connect canvas selection to properties panel via main window
            if (hasattr(self, 'pdf_canvas') and
                    hasattr(self.pdf_canvas, 'enhanced_drag_handler') and
                    hasattr(self, 'field_palette')):

                drag_handler = self.pdf_canvas.enhanced_drag_handler

                # Connect selection changes to main window handler
                if hasattr(drag_handler, 'selectionChanged'):
                    drag_handler.selectionChanged.connect(self._on_field_selection_changed)
                    print("✅ Connected field selection to main window")

            if hasattr(self, 'field_palette') and hasattr(self, 'pdf_canvas'):
                self.field_palette.fieldRequested.connect(self._on_field_type_selected)

                # Enhanced drag handler signals
                if hasattr(self.pdf_canvas, 'enhanced_drag_handler'):
                    drag_handler = self.pdf_canvas.enhanced_drag_handler

                    # Connect enhanced signals if they exist
                    if hasattr(drag_handler, 'dragStarted'):
                        drag_handler.dragStarted.connect(self.on_drag_started)
                        print("✅ Connected dragStarted signal")
                    if hasattr(drag_handler, 'dragProgress'):
                        drag_handler.dragProgress.connect(self.on_drag_progress)
                        print("✅ Connected dragProgress signal")
                    if hasattr(drag_handler, 'dragCompleted'):
                        drag_handler.dragCompleted.connect(self.on_drag_completed)
                        print("✅ Connected dragCompleted signal")
                    if hasattr(drag_handler, 'fieldResized'):
                        drag_handler.fieldResized.connect(self.on_field_resized)
                        print("✅ Connected fieldResized signal")
                        # PDF Canvas field selection connection
                        if (hasattr(self, 'pdf_canvas') and
                                self.pdf_canvas is not None and
                                hasattr(self.pdf_canvas, 'selection_handler')):
                            try:
                                # Connect selection handler if it exists
                                selection_handler = self.pdf_canvas.selection_handler
                                if hasattr(selection_handler, 'fieldSelected'):
                                    selection_handler.fieldSelected.connect(self.on_field_selected)
                                    print("  ✅ Connected canvas field selection signal")
                                elif hasattr(selection_handler, 'selectionChanged'):
                                    # Fallback for older signal name
                                    selection_handler.selectionChanged.connect(
                                        lambda: self.on_field_selected(selection_handler.get_selected_field())
                                    )
                                    print("  ✅ Connected canvas selection changed signal")
                            except Exception as e:
                                print(f"  ⚠️ Failed to connect canvas selection: {e}")


            print("✅ Signal connections setup completed")

        except Exception as e:
            print(f"Warning: Error setting up signal connections: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(list)
    def on_multi_selection_changed(self, selected_fields):
        """Handle multi-selection changes from FieldManager"""
        count = len(selected_fields)

        print(f"🔥 Multi-selection changed: {count} fields")

        if count == 0:
            self.statusBar().showMessage("No fields selected", 2000)
        elif count == 1:
            field = selected_fields[0]
            self.statusBar().showMessage(f"Selected: {field.id}", 2000)
        else:  # Multiple fields selected
            self.statusBar().showMessage(f"Multi-select: {count} fields", 2000)

    def on_drag_started(self, field_id: str, operation_type: str):
        """Handle drag operation start"""
        if hasattr(self, 'field_info_label'):
            self.field_info_label.setText(f"Starting {operation_type} on {field_id}")

    def on_drag_progress(self, field_id: str, x: int, y: int, w: int, h: int):
        """Handle real-time drag progress"""
        # Update properties panel if it exists
        if hasattr(self, 'properties_panel') and self.properties_panel:
            try:
                self.properties_panel.update_live_values(x, y, w, h)
            except Exception as e:
                print(f"⚠️ Error updating properties panel: {e}")

        # Update status bar with live coordinates
        if hasattr(self, 'field_info_label'):
            self.field_info_label.setText(f"{field_id}: ({x}, {y}) {w}×{h}")

    def on_drag_completed(self, field_id: str):
        """Handle drag operation completion"""
        if hasattr(self, 'field_info_label'):
            self.field_info_label.setText(f"Completed operation on {field_id}")

        # Mark document as modified
        self.document_modified = True

        # Clear live update after 2 seconds
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000,
                          lambda: self.field_info_label.setText("Ready") if hasattr(self, 'field_info_label') else None)

    def on_field_resized(self, field_id: str, x: float, y: float, width: float, height: float):
        """Handle field resize completion"""
        print(f"✅ Field {field_id} resized to ({x:.1f}, {y:.1f}) {width:.1f}×{height:.1f}")

        # Update properties panel
        if hasattr(self, 'properties_panel') and self.properties_panel:
            try:
                # Convert to int if properties panel expects int values
                self.properties_panel.update_field_values(field_id, int(x), int(y), int(width), int(height))
            except Exception as e:
                print(f"⚠️ Error updating properties after resize: {e}")

    def load_pdf_file(self, pdf_path: str):
        """
        Load PDF file - ONLY called by project management system
        """
        print(f"🔄 Loading PDF through project: {pdf_path}")
        print(f"📁 File exists: {Path(pdf_path).exists()}")

        # Verify we're in a project context
        if not hasattr(self, 'current_project_path') or not self.current_project_path:
            print("⚠️ PDF loading attempted outside of project context")
            QMessageBox.warning(
                self, "Project Required",
                "PDFs can only be opened through projects.\n\n"
                "Please create a new project or open an existing project."
            )
            return False

        # Store the path
        self.current_pdf_path = pdf_path

        # Show left panel
        print("👈 Showing left panel...")
        self.show_left_panel()

        try:
            if hasattr(self.pdf_canvas, 'load_pdf'):
                print(f"📋 Calling pdf_canvas.load_pdf({pdf_path})")
                result = self.pdf_canvas.load_pdf(pdf_path)
                print(f"📋 load_pdf returned: {result}")

                # Update controls
                if hasattr(self, 'update_page_controls'):
                    self.update_page_controls()
                if hasattr(self, 'update_zoom_controls'):
                    self.update_zoom_controls()

                if result:
                    print("✅ PDF loading succeeded")
                    filename = Path(pdf_path).name

                    # Update status displays
                    if hasattr(self, 'statusBar') and self.statusBar():
                        self.statusBar().showMessage(f"Loaded: {filename}", 3000)
                    if hasattr(self, 'field_info_label'):
                        self.field_info_label.setText(f"Loaded: {filename}")
                    if hasattr(self, 'doc_info_label'):
                        self.doc_info_label.setText(f"Document: {filename}")

                    if hasattr(self, 'update_toolbar_state'):
                        self.update_toolbar_state("project_loaded")
                        print("🔧 Toolbar state updated to show all controls")
                    else:
                        print("❌ update_toolbar_state method not available")

                    if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
                        self.setup_enhanced_grid()

                    return True
                else:
                    print("❌ PDF loading failed")
                    QMessageBox.critical(self, "Error", "Failed to load PDF file")
                    return False
            else:
                print("⚠️ PDF canvas not available")
                QMessageBox.warning(self, "Error", "PDF viewer not available")
                return False

        except Exception as e:
            print(f"❌ Error loading PDF: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load PDF:\n{str(e)}")
            return False

    def deprecated_open_pdf(self):
        """Open PDF file dialog and load selected file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            print(f"🔍 Opening PDF file: {file_path}")
            print(f"📁 File exists: {Path(file_path).exists()}")
            print(f"📏 File size: {Path(file_path).stat().st_size if Path(file_path).exists() else 'N/A'} bytes")

            print("👈 Showing left panel before PDF rendering...")
            self.show_left_panel()

            try:
                if hasattr(self.pdf_canvas, 'load_pdf'):
                    print(f"📋 Calling pdf_canvas.load_pdf({file_path})")
                    result = self.pdf_canvas.load_pdf(file_path)
                    print(f"📋 load_pdf returned: {result}")

                    self.update_page_controls()
                    self.update_zoom_controls()

                    if result:
                        print("✅ PDF loading succeeded")
                        self.current_pdf_path = file_path
                        self.statusBar().showMessage(f"Loaded: {Path(file_path).name}", 3000)
                        self.field_info_label.setText(f"Loaded: {Path(file_path).name}")
                    else:
                        print("❌ PDF loading failed")
                        self.statusBar().showMessage("Failed to load PDF", 3000)
                        QMessageBox.critical(self, "Error", "Failed to load PDF file")
                else:
                    # Fallback - just show the selected file
                    print("⚠️ pdf_canvas.load_pdf method not available, using fallback")
                    self.current_pdf_path = file_path
                    self.field_info_label.setText(f"Selected: {Path(file_path).name}")
                    QMessageBox.information(
                        self, "Info",
                        f"PDF selected: {Path(file_path).name}\n\n"
                        "PDF viewing not fully available in current mode.\n"
                        "Fix missing modules to enable full functionality."
                    )

            except Exception as e:
                print(f"❌ Exception occurred: {e}")
                QMessageBox.critical(self, "Error", f"Error opening PDF: {e}")

    @pyqtSlot()
    def save_form_data(self):
        """Save form field data"""
        if not self.current_pdf_path:
            QMessageBox.information(self, "No PDF", "Please open a PDF file first")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Form Data", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                # Create basic form data
                form_data = {
                    'pdf_path': self.current_pdf_path,
                    'timestamp': str(Path().resolve()),
                    'status': 'saved_in_limited_mode'
                }

                # Add field data if available
                if hasattr(self.pdf_canvas, 'get_fields_as_objects'):
                    try:
                        fields = self.pdf_canvas.get_fields_as_objects()
                        form_data['fields'] = [field.to_dict() for field in fields]
                        form_data['field_count'] = len(fields)
                    except:
                        form_data['fields'] = []
                        form_data['field_count'] = 0
                else:
                    form_data['fields'] = []
                    form_data['field_count'] = 0

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(form_data, f, indent=2, ensure_ascii=False)

                self.statusBar().showMessage(f"Saved to {Path(file_path).name}", 3000)

            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save: {e}")

    def reset_field_selection(self):
        """Reset field selection after placement"""
        if hasattr(self, 'field_palette') and hasattr(self.field_palette, 'reset_selection'):
            self.field_palette.reset_selection()

    @pyqtSlot()
    def show_info(self):
        """Show application information"""
        info_text = f"""
        <h3>PDF Voice Editor</h3>
        <p><b>Status:</b> Running</p>

        <p><b>Module Status:</b></p>
        <ul>
        <li>PDF Canvas: {'✅' if PDF_CANVAS_AVAILABLE else '❌'}</li>
        <li>Field Palette: {'✅' if FIELD_PALETTE_AVAILABLE else '❌'}</li>
        <li>Properties Panel: {'✅' if PROPERTIES_PANEL_AVAILABLE else '❌'}</li>
        <li>Field Model: {'✅' if FIELD_MODEL_AVAILABLE else '❌'}</li>
        <li>Icon Utils: {'✅' if ICON_UTILS_AVAILABLE else '❌'}</li>
        </ul>

        <p><b>Current PDF:</b> {self.current_pdf_path or 'None'}</p>

        {'<p><b>Note:</b> Some modules are missing. Run fix scripts to enable full functionality.</p>' if not all([PDF_CANVAS_AVAILABLE, FIELD_PALETTE_AVAILABLE, PROPERTIES_PANEL_AVAILABLE]) else ''}
        """

        QMessageBox.information(self, "Application Info", info_text)

    # Placeholder methods for signal connections
    @pyqtSlot(str)
    def create_field_at_center(self, field_type: str):
        """Create a new field at the center of the visible area"""
        print(f"Creating field of type: {field_type}")

        try:
            # Calculate center of visible area
            if hasattr(self, 'scroll_area') and self.scroll_area:
                center_x = self.scroll_area.width() // 2
                center_y = self.scroll_area.height() // 2

                # Convert to canvas coordinates
                scroll_x = self.scroll_area.horizontalScrollBar().value()
                scroll_y = self.scroll_area.verticalScrollBar().value()

                canvas_x = center_x + scroll_x
                canvas_y = center_y + scroll_y
            else:
                # Fallback position
                canvas_x, canvas_y = 200, 200

            # Create field using pdf_canvas
            if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
                field = None

                if hasattr(self.pdf_canvas, 'add_field'):
                    field = self.pdf_canvas.add_field(field_type, canvas_x, canvas_y)
                    if field:
                        print(f"✅ Created {field_type} field: {field.name}")
                        self.statusBar().showMessage(f"Created {field_type} field", 2000)

                        # Force canvas to redraw
                        if hasattr(self.pdf_canvas, 'draw_overlay'):
                            self.pdf_canvas.draw_overlay()
                        else:
                            self.pdf_canvas.update()

                elif hasattr(self.pdf_canvas, 'field_manager') and hasattr(self.pdf_canvas.field_manager, 'add_field'):
                    # Alternative: use field manager directly
                    field = self.pdf_canvas.field_manager.add_field(field_type, canvas_x, canvas_y)
                    if field:
                        print(f"✅ Created {field_type} field via field manager: {field.name}")
                        self.statusBar().showMessage(f"Created {field_type} field", 2000)
                        self.pdf_canvas.update()
                else:
                    print("❌ No field creation method available")
                    self.statusBar().showMessage("Field creation not available", 3000)
                    return None

                # ========== TABBED FIELD PALETTE INTEGRATION ==========
                if field:
                    print("🔧 STARTING TABBED FIELD PALETTE INTEGRATION")
                    self._ensure_field_manager_integration()
                    # Add to the properties tab dropdown
                    if hasattr(self, 'field_palette') and hasattr(self.field_palette, 'add_field_to_list'):
                        self.field_palette.add_field_to_list(field)
                        print(f"✅ Added {field_type} field to Properties tab list")

                    # Select the new field in both tabs (this will switch to Properties tab)
                    if hasattr(self, 'field_palette') and hasattr(self.field_palette, 'set_field_selected'):
                        self.field_palette.set_field_selected(True, field)
                        print(f"✅ Selected new {field_type} field in tabbed palette")

                    # Update status with field info
                    if hasattr(self, 'field_info_label'):
                        # Try different ways to get field ID/name based on your field object
                        field_id = getattr(field, 'id', getattr(field, 'name', 'unknown'))
                        self.field_info_label.setText(f"Created {field_type} field: {field_id}")

                    # Reset field type selection in Controls tab after a short delay
                    # This allows user to see the selection briefly, then resets so they can create another field
                    if hasattr(self, 'field_palette') and hasattr(self.field_palette, 'reset_selection'):
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(1500, lambda: (
                            self.field_palette.reset_selection(),
                            print("✅ Reset Controls tab selection - ready for next field")
                        ))

                    # Setup field manager connection if not already done
                    if hasattr(self, 'field_palette') and hasattr(self.field_palette, 'set_field_manager'):
                        if hasattr(self.pdf_canvas, 'field_manager'):
                            self.field_palette.set_field_manager(self.pdf_canvas.field_manager)
                        elif hasattr(self, 'field_manager'):
                            self.field_palette.set_field_manager(self.field_manager)

                else:
                    print(f"❌ Failed to create {field_type} field")
                    self.statusBar().showMessage(f"Failed to create {field_type} field", 3000)
                # ========== END TABBED FIELD PALETTE INTEGRATION ==========

                return field

            else:
                print("❌ PDF Canvas not available")
                self.statusBar().showMessage("PDF Canvas not available", 3000)

        except Exception as e:
            print(f"❌ Error creating field: {e}")
            self.statusBar().showMessage(f"Error creating field: {e}", 3000)
            import traceback
            traceback.print_exc()

        return None
    def deprecated_on_field_clicked(self, field_id: str):
        """Handle field click (placeholder)"""
        self.statusBar().showMessage(f"Field clicked: {field_id}", 2000)

    def deprecated_1_on_field_clicked(self, field):
        """Handle field selection from canvas"""
        # Your existing logic here...

        # Add this line:
        has_selection = field is not None
        self.field_palette.set_field_selected(has_selection, field)

        # Update status bar
        if field and hasattr(self, 'field_info_label'):
            self.field_info_label.setText(f"Selected: {field.field_type} ({field.id})")
        elif hasattr(self, 'field_info_label'):
            self.field_info_label.setText("No field selected")

    @pyqtSlot(object)
    def on_selection_changed(self, field):
        """Handle selection change (placeholder)"""
        self.statusBar().showMessage("Selection changed", 2000)

    @pyqtSlot(str, str, object)
    def on_property_changed(self, field_id: str, property_name: str, value):
        """Handle property changes from the Properties tab"""
        print(f"Property change: {field_id}.{property_name} = {value}")

        try:
            # Find the field and update it
            field = None

            if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'get_field_by_id'):
                    field = self.pdf_canvas.get_field_by_id(field_id)
                elif hasattr(self.pdf_canvas, 'field_manager') and hasattr(self.pdf_canvas.field_manager,
                                                                           'get_field_by_id'):
                    field = self.pdf_canvas.field_manager.get_field_by_id(field_id)
                elif hasattr(self.pdf_canvas, 'field_manager') and hasattr(self.pdf_canvas.field_manager, 'fields'):
                    # Search in fields list
                    for f in self.pdf_canvas.field_manager.fields:
                        if getattr(f, 'id', getattr(f, 'name', None)) == field_id:
                            field = f
                            break

            if field:
                # Update the field property using different possible methods
                if hasattr(field, 'set_property'):
                    field.set_property(property_name, value)
                elif hasattr(field, 'properties') and isinstance(field.properties, dict):
                    field.properties[property_name] = value
                elif hasattr(field, property_name):
                    setattr(field, property_name, value)
                else:
                    print(f"⚠️ Cannot set property {property_name} on field {field_id}")
                    return

                print(f"✅ Updated {field_id}.{property_name} = {value}")

                # Update the canvas display
                if hasattr(self.pdf_canvas, 'update_field_display'):
                    self.pdf_canvas.update_field_display(field)
                elif hasattr(self.pdf_canvas, 'draw_overlay'):
                    self.pdf_canvas.draw_overlay()
                else:
                    self.pdf_canvas.update()

                # Update status
                if hasattr(self, 'field_info_label'):
                    self.field_info_label.setText(f"Updated {property_name}: {value}")

            else:
                print(f"⚠️ Field not found: {field_id}")
                if hasattr(self, 'field_info_label'):
                    self.field_info_label.setText(f"Error: Field {field_id} not found")

        except Exception as e:
            print(f"❌ Error updating property: {e}")
            if hasattr(self, 'field_info_label'):
                self.field_info_label.setText(f"Error updating property: {e}")

    @pyqtSlot(str)
    def _on_field_type_selected(self, field_type):
        """Handle field type selection from palette"""
        print(f"🎯 Field type selected from palette: {field_type}")

        # Notify canvas about the selection
        if hasattr(self.pdf_canvas, 'set_selected_field_type'):
            self.pdf_canvas.set_selected_field_type(field_type)

        # Update status bar
        self.statusBar().showMessage(f"Selected {field_type} field - click on PDF to place", 3000)

    # Navigation and Zoom Methods

    @pyqtSlot()
    def previous_page(self):
        """Navigate to previous page in continuous view"""
        print("🔧 Previous page button clicked")

        if not hasattr(self.pdf_canvas, 'current_page') or not hasattr(self.pdf_canvas, 'pdf_document'):
            self.statusBar().showMessage("No PDF loaded", 1000)
            return

        current = getattr(self.pdf_canvas, 'current_page', 0)
        if current > 0:
            new_page = current - 1
            print(f"🔧 Navigating from page {current + 1} to page {new_page + 1}")

            # Use continuous view navigation
            if hasattr(self, 'jump_to_page_continuous'):
                self.jump_to_page_continuous(new_page + 1)  # jump_to_page_continuous expects 1-based
            elif hasattr(self.pdf_canvas, 'scroll_to_page'):
                self.pdf_canvas.scroll_to_page(new_page)
            else:
                self.statusBar().showMessage("Navigation not available", 1000)
                return

            self.statusBar().showMessage(f"Page {new_page + 1}", 1000)
        else:
            self.statusBar().showMessage("Already at first page", 1000)

    @pyqtSlot()
    def next_page(self):
        """Navigate to next page in continuous view"""
        print("🔧 Next page button clicked")

        if not hasattr(self.pdf_canvas, 'current_page') or not hasattr(self.pdf_canvas, 'pdf_document'):
            self.statusBar().showMessage("No PDF loaded", 1000)
            return

        current = getattr(self.pdf_canvas, 'current_page', 0)
        total_pages = self.pdf_canvas.pdf_document.page_count

        if current < total_pages - 1:
            new_page = current + 1
            print(f"🔧 Navigating from page {current + 1} to page {new_page + 1}")

            # Use continuous view navigation
            if hasattr(self, 'jump_to_page_continuous'):
                self.jump_to_page_continuous(new_page + 1)  # jump_to_page_continuous expects 1-based
            elif hasattr(self.pdf_canvas, 'scroll_to_page'):
                self.pdf_canvas.scroll_to_page(new_page)
            else:
                self.statusBar().showMessage("Navigation not available", 1000)
                return

            self.statusBar().showMessage(f"Page {new_page + 1}", 1000)
        else:
            self.statusBar().showMessage("Already at last page", 1000)

    @pyqtSlot()
    def x_previous_page(self):
        """Navigate to previous page"""
        if not hasattr(self.pdf_canvas, 'current_page'):
            self.statusBar().showMessage("No PDF loaded", 1000)
            return

        if hasattr(self.pdf_canvas, 'current_page') and self.pdf_canvas.current_page > 0:
            if hasattr(self.pdf_canvas, 'set_page'):
                new_page = self.pdf_canvas.current_page - 1
                self.pdf_canvas.set_page(new_page)
                self.statusBar().showMessage(f"Page {new_page + 1}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Navigation not available", 1000)
        else:
            self.statusBar().showMessage("Already at first page", 1000)

    @pyqtSlot()
    def x_next_page(self):
        """Navigate to next page"""
        if not hasattr(self.pdf_canvas, 'current_page') or not hasattr(self.pdf_canvas, 'pdf_document'):
            self.statusBar().showMessage("No PDF loaded", 1000)
            return

        if (self.pdf_canvas.pdf_document and 
            self.pdf_canvas.current_page < self.pdf_canvas.pdf_document.page_count - 1):
            if hasattr(self.pdf_canvas, 'set_page'):
                new_page = self.pdf_canvas.current_page + 1
                self.pdf_canvas.set_page(new_page)
                self.statusBar().showMessage(f"Page {new_page + 1}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Navigation not available", 1000)
        else:
            self.statusBar().showMessage("Already at last page", 1000)

    @pyqtSlot()
    def zoom_in(self):
        """Increase zoom level"""
        if not hasattr(self.pdf_canvas, 'zoom_level') or not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = min(current_zoom * 1.25, 5.0)
        self.pdf_canvas.set_zoom(new_zoom)
        zoom_percent = int(new_zoom * 100)
        self.statusBar().showMessage(f"Zoom: {zoom_percent}%", 1000)
        self.update_document_info()

    @pyqtSlot()
    def zoom_out(self):
        """Decrease zoom level"""
        if not hasattr(self.pdf_canvas, 'zoom_level') or not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        current_zoom = self.pdf_canvas.zoom_level
        new_zoom = max(current_zoom / 1.25, 0.1)
        self.pdf_canvas.set_zoom(new_zoom)
        zoom_percent = int(new_zoom * 100)
        self.statusBar().showMessage(f"Zoom: {zoom_percent}%", 1000)
        self.update_document_info()

    @pyqtSlot()
    def fit_width(self):
        """Fit PDF page to window width"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Fit width not available", 1000)
            return

        try:
            # Calculate zoom needed to fit width
            available_width = self.scroll_area.viewport().width() - 40  # Account for margins
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)
            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            new_zoom = available_width / page_width
            new_zoom = max(0.1, min(new_zoom, 5.0))  # Clamp to reasonable range

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)
            self.statusBar().showMessage(f"Fit width: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Fit width failed", 1000)

    @pyqtSlot()
    def toggle_grid(self):
        """Toggle grid display"""
        if hasattr(self.pdf_canvas, 'toggle_grid'):
            self.pdf_canvas.toggle_grid()

            # Update grid action state if it exists
            if hasattr(self, 'grid_action') and hasattr(self.pdf_canvas, 'show_grid'):
                self.grid_action.setChecked(self.pdf_canvas.show_grid)

            grid_status = "on" if getattr(self.pdf_canvas, 'show_grid', False) else "off"
            self.statusBar().showMessage(f"Grid {grid_status}", 1000)
        else:
            self.statusBar().showMessage("Grid toggle not available", 1000)

    @pyqtSlot()
    def increase_grid_size(self):
        """Increase grid size"""
        if hasattr(self.pdf_canvas, 'increase_grid_size'):
            if self.pdf_canvas.increase_grid_size():
                grid_info = self.pdf_canvas.get_grid_info()
                self.statusBar().showMessage(f"Grid size: {grid_info['size']}px", 1000)
            else:
                self.statusBar().showMessage("Grid size at maximum (100px)", 1000)
        else:
            self.statusBar().showMessage("Grid size adjustment not available", 1000)

    @pyqtSlot()
    def decrease_grid_size(self):
        """Decrease grid size"""
        if hasattr(self.pdf_canvas, 'decrease_grid_size'):
            if self.pdf_canvas.decrease_grid_size():
                grid_info = self.pdf_canvas.get_grid_info()
                self.statusBar().showMessage(f"Grid size: {grid_info['size']}px", 1000)
            else:
                self.statusBar().showMessage("Grid size at minimum (5px)", 1000)
        else:
            self.statusBar().showMessage("Grid size adjustment not available", 1000)

    @pyqtSlot()
    def move_grid_up(self):
        """Move grid up"""
        if hasattr(self.pdf_canvas, 'move_grid_up'):
            self.pdf_canvas.move_grid_up()
            grid_info = self.pdf_canvas.get_grid_info()
            self.statusBar().showMessage(f"Grid offset: ({grid_info['offset_x']}, {grid_info['offset_y']})", 1000)

    @pyqtSlot()
    def move_grid_down(self):
        """Move grid down"""
        if hasattr(self.pdf_canvas, 'move_grid_down'):
            self.pdf_canvas.move_grid_down()
            grid_info = self.pdf_canvas.get_grid_info()
            self.statusBar().showMessage(f"Grid offset: ({grid_info['offset_x']}, {grid_info['offset_y']})", 1000)

    @pyqtSlot()
    def move_grid_left(self):
        """Move grid left"""
        if hasattr(self.pdf_canvas, 'move_grid_left'):
            self.pdf_canvas.move_grid_left()
            grid_info = self.pdf_canvas.get_grid_info()
            self.statusBar().showMessage(f"Grid offset: ({grid_info['offset_x']}, {grid_info['offset_y']})", 1000)

    @pyqtSlot()
    def move_grid_right(self):
        """Move grid right"""
        if hasattr(self.pdf_canvas, 'move_grid_right'):
            self.pdf_canvas.move_grid_right()
            grid_info = self.pdf_canvas.get_grid_info()
            self.statusBar().showMessage(f"Grid offset: ({grid_info['offset_x']}, {grid_info['offset_y']})", 1000)

    @pyqtSlot()
    def reset_grid_offset(self):
        """Reset grid offset to origin"""
        if hasattr(self.pdf_canvas, 'reset_grid_offset'):
            self.pdf_canvas.reset_grid_offset()
            self.statusBar().showMessage("Grid offset reset to origin", 1000)

    @pyqtSlot()
    def zoom_to_fit(self):
        """Zoom to fit entire page in window"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Zoom to fit not available", 1000)
            return

        try:
            # Calculate zoom to fit both width and height
            available_width = self.scroll_area.width() - 40
            available_height = self.scroll_area.height() - 40
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)

            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            page_height = self.pdf_canvas.page_pixmap.height() / current_zoom

            zoom_for_width = available_width / page_width
            zoom_for_height = available_height / page_height

            # Use the smaller zoom to ensure page fits completely
            new_zoom = min(zoom_for_width, zoom_for_height)
            new_zoom = max(0.1, min(new_zoom, 5.0))

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)
            self.statusBar().showMessage(f"Zoom to fit: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Zoom to fit failed", 1000)

    def deprecated_jump_to_page(self):
        """Jump to specific page number"""
        if not hasattr(self, 'page_spinbox'):
            return

        page_number = self.page_spinbox.value()

        # Use continuous scrolling
        if hasattr(self, 'jump_to_page_continuous'):
            self.jump_to_page_continuous(page_number)
        else:
            # Fallback to old method
            if hasattr(self.pdf_canvas, 'set_page'):
                self.pdf_canvas.set_page(page_number - 1)
                self.update_document_info()

    def jump_to_page(self):
        """Jump to specific page number"""
        if not hasattr(self, 'page_spinbox'):
            return

        page_number = self.page_spinbox.value()

        # Use continuous scrolling
        if hasattr(self, 'jump_to_page_continuous'):
            self.jump_to_page_continuous(page_number)
        else:
            # Fallback to old method
            if hasattr(self.pdf_canvas, 'set_page'):
                self.pdf_canvas.set_page(page_number - 1)
                self.update_document_info()

    # Page and Zoom Control Methods
    @pyqtSlot(int)
    def deprecated_jump_to_page(self, page_number: int):
        """Jump to specific page number"""
        if hasattr(self.pdf_canvas, 'go_to_page'):
            if self.pdf_canvas.go_to_page(page_number):
                self.statusBar().showMessage(f"Jumped to page {page_number}", 1000)
                self.update_document_info()
            else:
                self.statusBar().showMessage("Invalid page number", 1000)
        else:
            self.statusBar().showMessage("Page navigation not available", 1000)

    @pyqtSlot(str)
    def set_zoom_level(self, zoom_text: str):
        """Set zoom level from dropdown selection"""
        if not hasattr(self.pdf_canvas, 'set_zoom'):
            self.statusBar().showMessage("Zoom not available", 1000)
            return

        try:
            if zoom_text == "Fit Width":
                self.fit_width()
            elif zoom_text == "Fit Page":
                self.fit_page()
            elif zoom_text.endswith('%'):
                # Extract percentage value
                percent_str = zoom_text.replace('%', '').strip()
                percent = int(percent_str)
                zoom_level = percent / 100.0
                zoom_level = max(0.1, min(zoom_level, 5.0))  # Clamp to reasonable range

                self.pdf_canvas.set_zoom(zoom_level)
                self.statusBar().showMessage(f"Zoom set to {percent}%", 1000)
                self.update_document_info()
            else:
                # Try to parse as number
                percent = float(zoom_text)
                zoom_level = percent / 100.0
                zoom_level = max(0.1, min(zoom_level, 5.0))

                self.pdf_canvas.set_zoom(zoom_level)
                self.statusBar().showMessage(f"Zoom set to {int(percent)}%", 1000)
                self.update_document_info()

        except ValueError:
            self.statusBar().showMessage("Invalid zoom value", 1000)

    @pyqtSlot()
    def deprecated_fit_page(self):
        """Fit entire page in window"""
        if (not hasattr(self.pdf_canvas, 'page_pixmap') or 
            not hasattr(self.pdf_canvas, 'set_zoom') or
            not self.pdf_canvas.page_pixmap):
            self.statusBar().showMessage("Fit page not available", 1000)
            return

        try:
            # Calculate zoom to fit both width and height
            available_width = self.scroll_area.width() - 40
            available_height = self.scroll_area.height() - 40
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)

            page_width = self.pdf_canvas.page_pixmap.width() / current_zoom
            page_height = self.pdf_canvas.page_pixmap.height() / current_zoom

            zoom_for_width = available_width / page_width
            zoom_for_height = available_height / page_height

            # Use smaller zoom to ensure page fits completely
            new_zoom = min(zoom_for_width, zoom_for_height)
            new_zoom = max(0.1, min(new_zoom, 5.0))

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)

            # Update zoom combo
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText(f"{zoom_percent}%")

            self.statusBar().showMessage(f"Fit page: {zoom_percent}%", 1000)
            self.update_document_info()
        except Exception as e:
            self.statusBar().showMessage("Fit page failed", 1000)

    @pyqtSlot()
    def fit_page(self):
        """Fit current page (not entire document) to window"""
        if not hasattr(self.pdf_canvas, 'pdf_document') or not self.pdf_canvas.pdf_document:
            return

        try:
            # Get CURRENT PAGE dimensions, not entire document
            current_page_num = getattr(self.pdf_canvas, 'current_page', 0)
            page = self.pdf_canvas.pdf_document[current_page_num]

            # Calculate single page size at current zoom
            current_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)
            page_width = page.rect.width
            page_height = page.rect.height

            # Available space
            available_width = self.scroll_area.viewport().width() - 40
            available_height = self.scroll_area.viewport().height() - 40

            # Calculate zoom for single page
            zoom_for_width = available_width / page_width
            zoom_for_height = available_height / page_height
            new_zoom = min(zoom_for_width, zoom_for_height)
            new_zoom = max(0.1, min(new_zoom, 5.0))

            self.pdf_canvas.set_zoom(new_zoom)
            zoom_percent = int(new_zoom * 100)
            self.statusBar().showMessage(f"Fit page: {zoom_percent}%", 1000)

        except Exception as e:
            self.statusBar().showMessage("Fit page failed", 1000)

    def update_page_controls(self):
        """Update page number controls based on current document"""
        print("🔧 update_page_controls called")

        try:
            # Debug the condition checks
            has_canvas = hasattr(self, 'pdf_canvas')
            has_document = has_canvas and hasattr(self.pdf_canvas, 'pdf_document')
            document_exists = has_document and self.pdf_canvas.pdf_document is not None

            print(f"  📋 has_canvas: {has_canvas}")
            print(f"  📋 has_document: {has_document}")
            print(f"  📋 document_exists: {document_exists}")

            if document_exists:
                # Try to get page count
                try:
                    page_count = self.pdf_canvas.pdf_document.page_count
                    print(f"  📋 page_count: {page_count}")
                except Exception as e:
                    print(f"  ❌ Error getting page_count: {e}")
                    page_count = None

                if page_count and page_count > 0:
                    current_page = getattr(self.pdf_canvas, 'current_page', 0) + 1
                    total_pages = page_count

                    print(f"  📋 Setting page controls: {current_page} of {total_pages}")

                    # Update page spinbox (prevent signal loops)
                    if hasattr(self, 'page_spinbox'):
                        self.page_spinbox.blockSignals(True)
                        self.page_spinbox.setMaximum(total_pages)
                        self.page_spinbox.setValue(current_page)
                        self.page_spinbox.blockSignals(False)
                        print(f"  ✅ Updated page_spinbox: max={total_pages}, value={current_page}")

                    # Update page count label
                    if hasattr(self, 'page_count_label'):
                        self.page_count_label.setText(f"of {total_pages}")
                        print(f"  ✅ Updated page_count_label: 'of {total_pages}'")

                    return  # Success, exit early

            # Fallback case - no document loaded or error
            print("  📋 Falling back to 'no document' state")
            if hasattr(self, 'page_spinbox'):
                self.page_spinbox.blockSignals(True)
                self.page_spinbox.setMaximum(1)
                self.page_spinbox.setValue(1)
                self.page_spinbox.blockSignals(False)
                print("  ⚠️ Set page_spinbox to default (1 of 1)")

            if hasattr(self, 'page_count_label'):
                self.page_count_label.setText("of 1")
                print("  ⚠️ Set page_count_label to 'of 1'")

        except Exception as e:
            print(f"❌ Error in update_page_controls: {e}")
            import traceback
            traceback.print_exc()

    def deprecated_update_page_controls(self):
        """Update page number controls based on current document"""
        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                current_page = getattr(self.pdf_canvas, 'current_page', 0) + 1
                total_pages = self.pdf_canvas.pdf_document.page_count

                # Update page spinbox
                if hasattr(self, 'page_spinbox'):
                    self.page_spinbox.setMaximum(total_pages)
                    self.page_spinbox.setValue(current_page)

                # Update page count label
                if hasattr(self, 'page_count_label'):
                    self.page_count_label.setText(f"of {total_pages}")

            else:
                # No document loaded
                if hasattr(self, 'page_spinbox'):
                    self.page_spinbox.setMaximum(1)
                    self.page_spinbox.setValue(1)

                if hasattr(self, 'page_count_label'):
                    self.page_count_label.setText("of 1")

        except Exception as e:
            pass  # Fail silently

    def update_zoom_controls(self):
        """Update zoom controls based on current zoom level"""
        try:
            if hasattr(self.pdf_canvas, 'zoom_level'):
                current_zoom = self.pdf_canvas.zoom_level
                zoom_percent = int(current_zoom * 100)

                # Update zoom combo
                if hasattr(self, 'zoom_combo'):
                    self.zoom_combo.setCurrentText(f"{zoom_percent}%")

        except Exception as e:
            pass  # Fail silently


    def setup_scroll_shortcuts(self):
        """Setup keyboard shortcuts for scrolling"""
        from PyQt6.QtGui import QShortcut

        # Zoom shortcuts
        zoom_in_shortcut = QShortcut("Ctrl++", self)
        zoom_in_shortcut.activated.connect(self.zoom_in)

        zoom_out_shortcut = QShortcut("Ctrl+-", self)
        zoom_out_shortcut.activated.connect(self.zoom_out)

        zoom_reset_shortcut = QShortcut("Ctrl+0", self)
        zoom_reset_shortcut.activated.connect(self.reset_zoom)

        # Fit shortcuts
        fit_width_shortcut = QShortcut("Ctrl+1", self)
        fit_width_shortcut.activated.connect(self.fit_width)

        fit_page_shortcut = QShortcut("Ctrl+2", self)
        fit_page_shortcut.activated.connect(self.fit_page)

        # Page navigation shortcuts
        next_page_shortcut = QShortcut("Ctrl+Right", self)
        next_page_shortcut.activated.connect(self.next_page)

        prev_page_shortcut = QShortcut("Ctrl+Left", self)
        prev_page_shortcut.activated.connect(self.previous_page)

        # Alternative page navigation
        page_down_shortcut = QShortcut("Page_Down", self)
        page_down_shortcut.activated.connect(self.next_page)

        page_up_shortcut = QShortcut("Page_Up", self)
        page_up_shortcut.activated.connect(self.previous_page)

    @pyqtSlot()
    def reset_zoom(self):
        """Reset zoom to 100%"""
        if hasattr(self.pdf_canvas, 'set_zoom'):
            self.pdf_canvas.set_zoom(1.0)
            self.statusBar().showMessage("Zoom reset to 100%", 1000)
            self.update_document_info()

            # Update zoom combo if it exists
            if hasattr(self, 'zoom_combo'):
                self.zoom_combo.setCurrentText("100%")
        else:
            self.statusBar().showMessage("Zoom not available", 1000)

    def enable_smooth_scrolling(self):
        """Enable smooth scrolling for the scroll area"""
        if hasattr(self, 'scroll_area'):
            # Configure scroll bar step sizes for smoother scrolling
            v_scrollbar = self.scroll_area.verticalScrollBar()
            h_scrollbar = self.scroll_area.horizontalScrollBar()

            if v_scrollbar:
                v_scrollbar.setSingleStep(10)
                v_scrollbar.setPageStep(100)
            if h_scrollbar:
                h_scrollbar.setSingleStep(10)
                h_scrollbar.setPageStep(100)

    def update_document_info(self):
        """Update document information display - enhanced version"""
        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                # Get current page info
                current_page = getattr(self.pdf_canvas, 'current_page', 0) + 1
                total_pages = self.pdf_canvas.pdf_document.page_count

                # Get zoom info
                zoom_level = getattr(self.pdf_canvas, 'zoom_level', 1.0)
                zoom_percent = int(zoom_level * 100)

                # Get field count
                field_count = 0
                if hasattr(self.pdf_canvas, 'get_fields_as_objects'):
                    try:
                        fields = self.pdf_canvas.get_fields_as_objects()
                        field_count = len(fields)
                    except:
                        pass

                # Update display
                info_text = f"Page {current_page} of {total_pages} | Zoom: {zoom_percent}% | Fields: {field_count}"
                self.field_info_label.setText(info_text)

            else:
                self.field_info_label.setText("No document loaded")

        except Exception as e:
            # Fallback to basic info
            self.field_info_label.setText("Document info unavailable")

        # Update page and zoom controls
        self.update_page_controls()
        self.update_zoom_controls()

    def depecated_setup_scroll_tracking(self):
        """Setup scroll tracking for continuous view"""
        if hasattr(self, 'scroll_area'):
            # Connect scroll bar to track current page
            v_scrollbar = self.scroll_area.verticalScrollBar()
            if v_scrollbar:
                v_scrollbar.valueChanged.connect(self.update_current_page_from_scroll)

    def setup_scroll_tracking(self):
        """Setup scroll tracking for continuous view with timer-based rendering"""
        if hasattr(self, 'scroll_area'):
            # Connect scroll bar to mark dirty flag instead of immediate rendering
            v_scrollbar = self.scroll_area.verticalScrollBar()
            if v_scrollbar:
                v_scrollbar.valueChanged.connect(self.mark_scroll_dirty)

            h_scrollbar = self.scroll_area.horizontalScrollBar()
            if h_scrollbar:
                h_scrollbar.valueChanged.connect(self.mark_scroll_dirty)

            print("✅ Timer-based scroll tracking connected")

    def mark_scroll_dirty(self):
        """Mark that scrolling occurred - will render after scroll stops"""
        self.needs_scroll_update = True

        # Restart timer - will fire 150ms after scrolling stops
        self.scroll_timer.stop()
        self.scroll_timer.start(150)

    def render_after_scroll(self):
        """Render controls after scrolling stops - timer callback"""
        try:
            if not self.needs_scroll_update:
                return

            print("🎨 Timer render: updating page tracking and controls")

            # Update current page tracking first
            self.update_page_tracking_from_scroll()

            # Render all controls using reliable method
            self.pdf_canvas.draw_overlay()

            # Update toolbar if page changed
            self.update_page_controls()
            self.update_document_info()

            # Clear flags
            self.needs_scroll_update = False
            self.needs_zoom_update = False

        except Exception as e:
            print(f"⚠️ Error in timer render: {e}")
            # Fallback to simple render
            self.pdf_canvas.draw_overlay()

    def update_page_tracking_from_scroll(self):
        """Update current page tracking without rendering"""
        try:
            # Get scroll position
            v_scrollbar = self.scroll_area.verticalScrollBar()
            scroll_y = v_scrollbar.value()

            # Calculate current page
            current_page = self.pdf_canvas.get_current_page_from_scroll(scroll_y)
            old_page = getattr(self.pdf_canvas, 'current_page', -1)

            # Update page tracking
            self.pdf_canvas.current_page = current_page

            if old_page != current_page:
                print(f"📄 Page changed: {old_page} → {current_page}")

        except Exception as e:
            print(f"⚠️ Error updating page tracking: {e}")

    def on_zoom_changed(self, new_zoom_level: float):
        """Handle zoom level changes with timer-based rendering"""
        old_zoom = getattr(self.pdf_canvas, 'zoom_level', 1.0)

        print(f"🔍 Zoom changed: {old_zoom:.1f}x → {new_zoom_level:.1f}x")

        # Update canvas zoom
        self.pdf_canvas.set_zoom(new_zoom_level)

        # Mark for timer-based update instead of immediate render
        self.needs_zoom_update = True
        self.needs_scroll_update = True

        # Start timer for zoom update
        self.scroll_timer.stop()
        self.scroll_timer.start(100)

        # Note: zoom focus point maintenance removed for simplicity

    def mark_zoom_dirty(self):
        """Mark that zoom changed - will render after zoom stabilizes"""
        self.needs_zoom_update = True
        self.needs_scroll_update = True  # Also update scroll-related rendering

        # Restart timer with shorter delay for zoom (more responsive)
        self.scroll_timer.stop()
        self.scroll_timer.start(100)

    def update_current_page_from_scroll(self):
        """Update current page and render controls - with viewport calculation"""
        try:
            # Get scroll and viewport information
            v_scrollbar = self.scroll_area.verticalScrollBar()
            h_scrollbar = self.scroll_area.horizontalScrollBar()

            scroll_x = h_scrollbar.value()
            scroll_y = v_scrollbar.value()
            viewport_width = self.scroll_area.viewport().width()
            viewport_height = self.scroll_area.viewport().height()

            # Create viewport rectangle in canvas coordinates
            viewport_rect = QRect(scroll_x, scroll_y, viewport_width, viewport_height)

            # Calculate visible page range
            start_page = self.pdf_canvas.get_page_at_y_position(scroll_y)
            end_page = self.pdf_canvas.get_page_at_y_position(scroll_y + viewport_height)

            # Ensure valid page range
            max_page = self.pdf_canvas.get_page_count() - 1
            start_page = max(0, min(start_page, max_page))
            end_page = max(start_page, min(end_page, max_page))

            # Update current page tracking
            current_page = self.pdf_canvas.get_current_page_from_scroll(scroll_y)
            old_page = getattr(self.pdf_canvas, 'current_page', -1)
            self.pdf_canvas.current_page = current_page

            # Only render if page changed or significant scroll
            if old_page != current_page or self._should_force_redraw():
                print(f"📜 Rendering: pages {start_page}-{end_page}, viewport: {viewport_rect}")
                self.pdf_canvas.draw_controls_and_overlay(start_page, end_page, viewport_rect)
                # ADD THIS: Update toolbar when page changes
                self.update_page_controls()

            # Update UI
            self.update_document_info()

        except Exception as e:
            print(f"⚠️ Error in scroll update: {e}")
            # Fallback to simple update
            self.pdf_canvas.draw_overlay()

    def _should_force_redraw(self):
        """Determine if we should force a redraw (throttling)"""
        import time
        current_time = time.time()

        if not hasattr(self, '_last_redraw_time'):
            self._last_redraw_time = 0

        # Force redraw every 100ms max (10 FPS)
        if current_time - self._last_redraw_time > 0.1:
            self._last_redraw_time = current_time
            return True

        return False

    def deprecated_update_current_page_from_scroll(self):
        """Update current page info based on scroll position"""
        if not hasattr(self.pdf_canvas, 'get_current_page_from_scroll'):
            return

        try:
            v_scrollbar = self.scroll_area.verticalScrollBar()
            scroll_position = v_scrollbar.value()

            # Get current page from scroll position
            current_page = self.pdf_canvas.get_current_page_from_scroll(scroll_position)

            # DEBUG: Show scroll tracking is working
            old_page = getattr(self.pdf_canvas, 'current_page', -1)
            #print(
            #clear
            # f"📜 MAIN: Scroll tracking: position={scroll_position}, detected_page={current_page}, old_page={old_page}")

            if old_page != current_page:
                print(f"📜 MAIN: Page changed {old_page} → {current_page}, redrawing fields")
                self.pdf_canvas.draw_overlay()  # Force field redraw

            # Update the canvas current_page for compatibility
            self.pdf_canvas.current_page = current_page

            # ALSO call the canvas method to update field rendering
            if hasattr(self.pdf_canvas, 'update_current_page_from_scroll'):
                self.pdf_canvas.update_current_page_from_scroll()

            # Update UI
            self.update_document_info()

        except Exception as e:
            print(f"⚠️ Error in main window scroll tracking: {e}")

    def jump_to_page_continuous(self, page_number):
        """Jump to page in continuous view"""
        if hasattr(self.pdf_canvas, 'scroll_to_page'):
            # Convert to 0-based indexing
            page_index = page_number - 1
            self.pdf_canvas.scroll_to_page(page_index)

    def get_navigation_state(self) -> dict:
        """Get current navigation state for UI updates"""
        state = {
            'has_document': False,
            'can_go_previous': False,
            'can_go_next': False,
            'current_page': 0,
            'total_pages': 0,
            'zoom_percent': 100
        }

        try:
            if hasattr(self.pdf_canvas, 'pdf_document') and self.pdf_canvas.pdf_document:
                state['has_document'] = True
                state['current_page'] = getattr(self.pdf_canvas, 'current_page', 0) + 1
                state['total_pages'] = self.pdf_canvas.pdf_document.page_count
                state['can_go_previous'] = getattr(self.pdf_canvas, 'current_page', 0) > 0
                state['can_go_next'] = getattr(self.pdf_canvas, 'current_page', 0) < state['total_pages'] - 1
                state['zoom_percent'] = int(getattr(self.pdf_canvas, 'zoom_level', 1.0) * 100)

        except Exception:
            pass

        return state


    @pyqtSlot(str)
    def deprecated_create_field_at_center(self, field_type: str):
        """Create a new field at the center of the visible area"""
        print(f"Creating field of type: {field_type}")
        # Implementation would go herecls

    @pyqtSlot(str)
    def on_field_clicked(self, field_id: str):
        """Handle field click - SIMPLIFIED"""
        print(f"Field clicked: {field_id}")

        try:
            # Find field object
            field = None
            if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'field_manager'):
                    for f in self.pdf_canvas.field_manager.fields:
                        if getattr(f, 'id', None) == field_id:
                            field = f
                            break

            if field:
                print(f"✅ Found field object: {field}")
                # Just call field selection - NO integration!
                self.on_field_selected(field)

        except Exception as e:
            print(f"❌ Error handling field click: {e}")

    @pyqtSlot(str, int, int)
    def on_field_moved(self, field_id: str, x: int, y: int):
        """Handle field movement"""
        print(f"Field {field_id} moved to ({x}, {y})")

    @pyqtSlot(str, int, int, int, int)
    def on_field_resized(self, field_id: str, x: int, y: int, width: int, height: int):
        """Handle field resize"""
        print(f"Field {field_id} resized to {width}x{height} at ({x}, {y})")

    @pyqtSlot(int, int)
    def on_position_clicked(self, x: int, y: int):
        """Handle position click (no field)"""
        print(f"Position clicked: ({x}, {y})")

    @pyqtSlot(object)
    def on_selection_changed(self, field):
        """Handle selection change"""
        if field:
            print(f"Field selected: {field}")
        else:
            print("Selection cleared")

    @pyqtSlot(str, str, object)
    def on_property_changed(self, field_id: str, property_name: str, value):
        """Handle property changes from the Properties tab"""
        print(f"Property change: {field_id}.{property_name} = {value}")

        try:
            # Find the field and update it
            field = None

            if hasattr(self, 'pdf_canvas') and self.pdf_canvas:
                if hasattr(self.pdf_canvas, 'get_field_by_id'):
                    field = self.pdf_canvas.get_field_by_id(field_id)
                elif hasattr(self.pdf_canvas, 'field_manager') and hasattr(self.pdf_canvas.field_manager,
                                                                           'get_field_by_id'):
                    field = self.pdf_canvas.field_manager.get_field_by_id(field_id)
                elif hasattr(self.pdf_canvas, 'field_manager') and hasattr(self.pdf_canvas.field_manager, 'fields'):
                    # Search in fields list
                    for f in self.pdf_canvas.field_manager.fields:
                        if getattr(f, 'id', getattr(f, 'name', None)) == field_id:
                            field = f
                            break

            if field:
                # Update the field property using different possible methods
                if hasattr(field, 'set_property'):
                    field.set_property(property_name, value)
                elif hasattr(field, 'properties') and isinstance(field.properties, dict):
                    field.properties[property_name] = value
                elif hasattr(field, property_name):
                    setattr(field, property_name, value)
                else:
                    print(f"⚠️ Cannot set property {property_name} on field {field_id}")
                    return

                print(f"✅ Updated {field_id}.{property_name} = {value}")

                # Update the canvas display
                if hasattr(self.pdf_canvas, 'update_field_display'):
                    self.pdf_canvas.update_field_display(field)
                elif hasattr(self.pdf_canvas, 'draw_overlay'):
                    self.pdf_canvas.draw_overlay()
                else:
                    self.pdf_canvas.update()

                # Update status
                if hasattr(self, 'field_info_label'):
                    self.field_info_label.setText(f"Updated {property_name}: {value}")

            else:
                print(f"⚠️ Field not found: {field_id}")
                if hasattr(self, 'field_info_label'):
                    self.field_info_label.setText(f"Error: Field {field_id} not found")

        except Exception as e:
            print(f"❌ Error updating property: {e}")
            if hasattr(self, 'field_info_label'):
                self.field_info_label.setText(f"Error updating property: {e}")

    def delete_selected_field(self):
        """Delete the currently selected field"""
        try:
            # Get the currently selected field from the canvas
            selected_field = None

            if hasattr(self, 'pdf_canvas') and self.pdf_canvas:

                selected_field = None

                if hasattr(self.pdf_canvas, 'selection_handler') and self.pdf_canvas.selection_handler:
                    selected_field = self.pdf_canvas.selection_handler.get_selected_field()
                elif hasattr(self.pdf_canvas, 'enhanced_drag_handler') and self.pdf_canvas.enhanced_drag_handler:
                    # For multi-selection, get the first selected field
                    selected_fields = self.pdf_canvas.enhanced_drag_handler.get_selected_fields()
                    selected_field = selected_fields[0] if selected_fields else None
                elif hasattr(self.pdf_canvas, 'get_selected_field'):
                    selected_field = self.pdf_canvas.get_selected_field()

            if selected_field:
                field_id = getattr(selected_field, 'id', getattr(selected_field, 'name', 'unknown'))
                field_type = getattr(selected_field, 'field_type', getattr(selected_field, 'type', 'field'))

                # Remove from canvas/field manager
                success = False
                if hasattr(self.pdf_canvas, 'remove_field'):
                    success = self.pdf_canvas.remove_field(selected_field)
                elif hasattr(self.pdf_canvas, 'field_manager') and hasattr(self.pdf_canvas.field_manager,
                                                                           'remove_field'):
                    success = self.pdf_canvas.field_manager.remove_field(selected_field)

                if success:
                    print(f"✅ Deleted {field_type} field: {field_id}")

                    # IMPORTANT: Refresh the entire control list from field manager
                    if hasattr(self, 'field_palette') and hasattr(self.field_palette, 'refresh_control_list'):
                        self.field_palette.refresh_control_list()
                        print("  ✅ Refreshed entire control list after deletion")

                    # Clear selection in both tabs
                    if hasattr(self, 'field_palette') and hasattr(self.field_palette, 'set_field_selected'):
                        self.field_palette.set_field_selected(False, None)
                        print("  ✅ Cleared field selection")

                    # Update status
                    if hasattr(self, 'field_info_label'):
                        self.field_info_label.setText("Field deleted")

                    self.statusBar().showMessage(f"Deleted {field_type} field", 2000)
                    self.pdf_canvas.update()

        except Exception as e:
            print(f"❌ Error deleting field: {e}")
            self.statusBar().showMessage(f"Error deleting field: {e}", 3000)

    def refresh_field_list(self):
        """Refresh the field list in the properties tab"""
        try:
            if hasattr(self, 'field_palette') and hasattr(self.field_palette, 'refresh_control_list'):
                self.field_palette.refresh_control_list()
                print("✅ Refreshed field list in Properties tab")
        except Exception as e:
            print(f"❌ Error refreshing field list: {e}")

    def setup_field_manager_integration(self):
        """Setup field manager integration"""
        try:
            field_manager = None

            # Try to find field manager in different locations
            if hasattr(self, 'field_manager'):
                field_manager = self.field_manager
            elif hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'field_manager'):
                field_manager = self.pdf_canvas.field_manager

            if field_manager and hasattr(self, 'field_palette'):
                if hasattr(self.field_palette, 'set_field_manager'):
                    self.field_palette.set_field_manager(field_manager)
                    print("✅ Connected field manager to tabbed palette")

                # Refresh the field list
                self.refresh_field_list()

        except Exception as e:
            print(f"❌ Error setting up field manager integration: {e}")

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)

        # Update scroll area when window is resized
        if hasattr(self, 'scroll_area') and self.scroll_area:
            # Force scroll area to update its viewport
            self.scroll_area.updateGeometry()

        # Update status bar with window size (optional)
        if hasattr(self, 'statusBar'):
            size = event.size()
            # Uncomment the next line if you want to see window size in status bar
            # self.statusBar().showMessage(f"Window size: {size.width()}x{size.height()}", 2000)

        # Ensure splitter proportions are maintained
        if hasattr(self, 'splitter') and self.splitter:
            # Maintain proportional sizing
            total_width = self.width()
            left_width = max(250, min(400, total_width * 0.25))  # 25% but between 250-400px
            center_width = total_width - left_width - 20  # 20px for splitter handle
            self.splitter.setSizes([int(left_width), int(center_width)])



    def save_window_state(self):
        """Save window state and geometry"""
        try:
            settings = QSettings('PDFVoiceEditor', 'MainWindow')
            settings.setValue('geometry', self.saveGeometry())
            settings.setValue('windowState', self.saveState())
            if hasattr(self, 'splitter'):
                settings.setValue('splitterSizes', self.splitter.saveState())
        except Exception as e:
            print(f"Could not save window state: {e}")

    def restore_window_state(self):
        """Restore window state and geometry"""
        try:
            settings = QSettings('PDFVoiceEditor', 'MainWindow')
            geometry = settings.value('geometry')
            if geometry:
                self.restoreGeometry(geometry)
            window_state = settings.value('windowState')
            if window_state:
                self.restoreState(window_state)
            if hasattr(self, 'splitter'):
                splitter_state = settings.value('splitterSizes')
                if splitter_state:
                    self.splitter.restoreState(splitter_state)
        except Exception as e:
            print(f"Could not restore window state: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        self.save_window_state()
        super().closeEvent(event)

    def _ensure_field_manager_integration(self):
        """Ensure field manager is properly connected to tabbed palette"""
        print("🔧 Setting up field manager integration...")

        try:
            field_manager = None

            # Try to find field manager in different locations
            if hasattr(self, 'field_manager'):
                field_manager = self.field_manager
                print("  ✅ Found field_manager in main window")
            elif hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'field_manager'):
                field_manager = self.pdf_canvas.field_manager
                print("  ✅ Found field_manager in pdf_canvas")
            else:
                print("  ❌ No field manager found")
                return

            print(f"  Field manager type: {type(field_manager)}")
            print(f"  Field manager has {len(getattr(field_manager, 'fields', []))} fields")

            if field_manager and hasattr(self, 'field_palette'):
                if hasattr(self.field_palette, 'set_field_manager'):
                    print("  🔗 Setting field manager on tabbed palette...")
                    print(f"  Field manager to set: {field_manager}")  # ← ADD THIS
                    self.field_palette.set_field_manager(field_manager)
                    print("  ✅ Connected field manager to tabbed palette")
                else:
                    print("  ❌ Tabbed palette has no set_field_manager method")
            else:
                print("  ❌ No field palette or field manager available")

        except Exception as e:
            print(f"❌ Error setting up field manager integration: {e}")
            import traceback
            traceback.print_exc()

    def debug_dropdown_integration(self):
        """Debug method to test dropdown integration manually"""
        print("🔍 DEBUG: Testing dropdown integration")

        # Check field manager
        if hasattr(self, 'pdf_canvas') and hasattr(self.pdf_canvas, 'field_manager'):
            fm = self.pdf_canvas.field_manager
            print(f"  Field manager has {len(fm.fields)} fields:")
            for i, field in enumerate(fm.fields):
                print(f"    {i}: {field.id} ({field.field_type})")

        # Test field manager integration
        print("  Testing field manager integration...")
        self._ensure_field_manager_integration()

        # Check if tabbed palette has field manager
        if hasattr(self, 'field_palette'):
            props_tab = self.field_palette.properties_tab
            print(f"  Properties tab field manager: {props_tab.field_manager is not None}")

            # Force refresh
            print("  Forcing dropdown refresh...")
            props_tab.refresh_control_list()

            print(f"  Dropdown count after refresh: {props_tab.control_dropdown.count()}")
            for i in range(props_tab.control_dropdown.count()):
                text = props_tab.control_dropdown.itemText(i)
                data = props_tab.control_dropdown.itemData(i)
                print(f"    Item {i}: '{text}' -> {data}")

    def on_field_selected(self, field):
        """Handle field selection from canvas - FIXED to prevent dropdown revert"""
        try:
            field_id = getattr(field, 'id', 'None') if field else 'None'
            print(f"📌 MAIN WINDOW: Field selected from canvas: {field_id}")

            # Get current selection state from properties tab
            if hasattr(self, 'field_palette') and self.field_palette:
                properties_tab = self.field_palette.properties_tab
                current_selection = getattr(properties_tab, 'current_field', None)
                current_id = getattr(current_selection, 'id', 'None') if current_selection else 'None'
                print(f"   Current properties selection: {current_id}")

                # CHECK: Is this field already selected?
                if (current_selection and field and
                        getattr(current_selection, 'id', None) == getattr(field, 'id', None)):
                    print(f"   ✅ Field {field_id} is already selected - skipping update to prevent revert")
                    return

                # Field is different, proceed with normal selection
                print(f"   🔄 Field changed from {current_id} to {field_id} - proceeding with update")
                properties_tab.highlight_control(field, propagate_to_properties=True)
                print("   ✅ Called highlight_control")

        except Exception as e:
            print(f"❌ Error in field selection handler: {e}")

    @pyqtSlot(list)
    def _on_field_selection_changed(self, selected_fields):
        """Handle field selection changes from canvas - just pass through"""
        print(f"🎯 Main window: Passing {len(selected_fields)} selected fields to properties panel")

        if hasattr(self, 'field_palette'):
            properties_tab = self.field_palette.properties_tab
            properties_tab.handle_selection_changed(selected_fields)

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("PDF Voice Editor")
    app.setApplicationVersion("1.1")

    # Set application icon if available
    if ICON_UTILS_AVAILABLE and create_app_icon:
        try:
            app.setWindowIcon(create_app_icon(32))
        except Exception:
            pass  # Continue without icon if it fails

    # Create and show main window
    window = PDFViewerMainWindow()
    window.show()

    print("🎉 PDF Voice Editor started!")
    if not all([PDF_CANVAS_AVAILABLE, FIELD_PALETTE_AVAILABLE, PROPERTIES_PANEL_AVAILABLE]):
        print("⚠️  Running in limited mode - some modules are missing")
        print("   Run fix scripts to enable full functionality")
    else:
        print("✅ All modules loaded successfully")

    # Run the application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
