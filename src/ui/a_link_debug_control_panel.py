"""
Link Debug Control Panel - Missing Implementation
Debug panel for analyzing PDF link system performance and status
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QGroupBox, QListWidget, QListWidgetItem, QProgressBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QSpinBox,
    QComboBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
from typing import Dict, List, Any, Optional
import time
import traceback

from a_pdf_link_overlay_manager import PDFLinkIntegration
from a_pdf_link_manager import PDFLink, LinkType


class LinkDebugControlPanel(QWidget):
    """
    Debug control panel for PDF link system
    Provides detailed information about link extraction, performance, and errors
    """

    # Signals
    debugInfoUpdated = pyqtSignal(str)  # Debug message
    performanceDataUpdated = pyqtSignal(dict)  # Performance metrics

    def __init__(self, link_integration: PDFLinkIntegration, parent=None):
        super().__init__(parent)

        self.link_integration = link_integration
        self.debug_messages = []
        self.performance_data = {}
        self.auto_refresh = True
        self.refresh_interval = 2000  # 2 seconds

        # Setup UI
        self._setup_ui()
        self._connect_signals()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh_debug_info)
        self.refresh_timer.start(self.refresh_interval)

        print("🐛 LinkDebugControlPanel initialized")

    def _setup_ui(self):
        """Setup the debug panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("🐛 Link Debug Panel")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Control buttons
        self._create_control_buttons(layout)

        # Tabs for different debug views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # System status tab
        self._create_system_status_tab()

        # Performance tab
        self._create_performance_tab()

        # Debug log tab
        self._create_debug_log_tab()

        # Link analysis tab
        self._create_link_analysis_tab()

        # Settings tab
        self._create_debug_settings_tab()

    def _create_control_buttons(self, layout):
        """Create control buttons"""
        button_layout = QHBoxLayout()

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._manual_refresh)
        button_layout.addWidget(self.refresh_button)

        # Auto-refresh toggle
        self.auto_refresh_check = QCheckBox("Auto-refresh")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.toggled.connect(self._toggle_auto_refresh)
        button_layout.addWidget(self.auto_refresh_check)

        # Clear log button
        self.clear_log_button = QPushButton("🧹 Clear Log")
        self.clear_log_button.clicked.connect(self._clear_debug_log)
        button_layout.addWidget(self.clear_log_button)

        # Run diagnostics button
        self.diagnostics_button = QPushButton("🔍 Run Diagnostics")
        self.diagnostics_button.clicked.connect(self._run_comprehensive_diagnostics)
        button_layout.addWidget(self.diagnostics_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _create_system_status_tab(self):
        """Create system status tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # System status display
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)

        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        self.status_text.setFont(QFont("Courier", 9))
        status_layout.addWidget(self.status_text)

        layout.addWidget(status_group)

        # Component status table
        components_group = QGroupBox("Component Status")
        components_layout = QVBoxLayout(components_group)

        self.components_table = QTableWidget()
        self.components_table.setColumnCount(3)
        self.components_table.setHorizontalHeaderLabels(["Component", "Status", "Details"])
        self.components_table.horizontalHeader().setStretchLastSection(True)
        components_layout.addWidget(self.components_table)

        layout.addWidget(components_group)

        self.tab_widget.addTab(widget, "System Status")

    def _create_performance_tab(self):
        """Create performance monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Performance metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QVBoxLayout(metrics_group)

        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(2)
        self.performance_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.performance_table.horizontalHeader().setStretchLastSection(True)
        metrics_layout.addWidget(self.performance_table)

        layout.addWidget(metrics_group)

        # Cache information
        cache_group = QGroupBox("Cache Information")
        cache_layout = QVBoxLayout(cache_group)

        self.cache_info_text = QTextEdit()
        self.cache_info_text.setReadOnly(True)
        self.cache_info_text.setMaximumHeight(100)
        self.cache_info_text.setFont(QFont("Courier", 9))
        cache_layout.addWidget(self.cache_info_text)

        layout.addWidget(cache_group)

        # Overlay statistics
        overlay_group = QGroupBox("Overlay Statistics")
        overlay_layout = QVBoxLayout(overlay_group)

        self.overlay_stats_text = QTextEdit()
        self.overlay_stats_text.setReadOnly(True)
        self.overlay_stats_text.setMaximumHeight(100)
        self.overlay_stats_text.setFont(QFont("Courier", 9))
        overlay_layout.addWidget(self.overlay_stats_text)

        layout.addWidget(overlay_group)

        self.tab_widget.addTab(widget, "Performance")

    def _create_debug_log_tab(self):
        """Create debug log tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Log level filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Log Level:"))

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["All", "Error", "Warning", "Info", "Debug"])
        self.log_level_combo.currentTextChanged.connect(self._filter_debug_log)
        filter_layout.addWidget(self.log_level_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Debug log display
        self.debug_log_text = QTextEdit()
        self.debug_log_text.setReadOnly(True)
        self.debug_log_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.debug_log_text)

        self.tab_widget.addTab(widget, "Debug Log")

    def _create_link_analysis_tab(self):
        """Create link analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Page selector
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Analyze Page:"))

        self.analyze_page_spinbox = QSpinBox()
        self.analyze_page_spinbox.setMinimum(1)
        self.analyze_page_spinbox.valueChanged.connect(self._analyze_page_links)
        page_layout.addWidget(self.analyze_page_spinbox)

        analyze_button = QPushButton("🔍 Analyze")
        analyze_button.clicked.connect(self._analyze_current_page)
        page_layout.addWidget(analyze_button)

        page_layout.addStretch()
        layout.addLayout(page_layout)

        # Link analysis results
        self.link_analysis_text = QTextEdit()
        self.link_analysis_text.setReadOnly(True)
        self.link_analysis_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.link_analysis_text)

        self.tab_widget.addTab(widget, "Link Analysis")

    def _create_debug_settings_tab(self):
        """Create debug settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Refresh settings
        refresh_group = QGroupBox("Refresh Settings")
        refresh_layout = QVBoxLayout(refresh_group)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Refresh Interval (ms):"))

        self.refresh_interval_spinbox = QSpinBox()
        self.refresh_interval_spinbox.setRange(500, 10000)
        self.refresh_interval_spinbox.setValue(2000)
        self.refresh_interval_spinbox.valueChanged.connect(self._update_refresh_interval)
        interval_layout.addWidget(self.refresh_interval_spinbox)

        interval_layout.addStretch()
        refresh_layout.addLayout(interval_layout)

        layout.addWidget(refresh_group)

        # Debug verbosity
        verbosity_group = QGroupBox("Debug Verbosity")
        verbosity_layout = QVBoxLayout(verbosity_group)

        self.verbose_logging_check = QCheckBox("Enable verbose logging")
        self.verbose_logging_check.toggled.connect(self._toggle_verbose_logging)
        verbosity_layout.addWidget(self.verbose_logging_check)

        self.performance_tracking_check = QCheckBox("Enable performance tracking")
        self.performance_tracking_check.setChecked(True)
        verbosity_layout.addWidget(self.performance_tracking_check)

        layout.addWidget(verbosity_group)

        # Export options
        export_group = QGroupBox("Export Debug Data")
        export_layout = QVBoxLayout(export_group)

        export_log_button = QPushButton("📤 Export Debug Log")
        export_log_button.clicked.connect(self._export_debug_log)
        export_layout.addWidget(export_log_button)

        export_performance_button = QPushButton("📊 Export Performance Data")
        export_performance_button.clicked.connect(self._export_performance_data)
        export_layout.addWidget(export_performance_button)

        layout.addWidget(export_group)

        layout.addStretch()
        self.tab_widget.addTab(widget, "Settings")

    def _connect_signals(self):
        """Connect signals from link integration"""
        if self.link_integration:
            # Connect to debug events if available
            if hasattr(self.link_integration, 'debugInfoUpdated'):
                self.link_integration.debugInfoUpdated.connect(self._add_debug_message)

    def _add_debug_message(self, message: str, level: str = "INFO"):
        """Add a debug message to the log"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"

        self.debug_messages.append({
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'formatted': formatted_message
        })

        # Keep only last 1000 messages
        if len(self.debug_messages) > 1000:
            self.debug_messages = self.debug_messages[-1000:]

        self._update_debug_log_display()
        self.debugInfoUpdated.emit(formatted_message)

    def _update_debug_log_display(self):
        """Update the debug log display"""
        if not hasattr(self, 'debug_log_text'):
            return

        # Get current filter
        filter_level = self.log_level_combo.currentText() if hasattr(self, 'log_level_combo') else "All"

        # Filter messages
        filtered_messages = []
        for msg in self.debug_messages:
            if filter_level == "All" or msg['level'] == filter_level.upper():
                filtered_messages.append(msg['formatted'])

        # Update display
        self.debug_log_text.clear()
        self.debug_log_text.append('\n'.join(filtered_messages[-100:]))  # Show last 100 messages

        # Auto-scroll to bottom
        cursor = self.debug_log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.debug_log_text.setTextCursor(cursor)

    def _manual_refresh(self):
        """Manual refresh of debug information"""
        self._add_debug_message("Manual refresh triggered", "INFO")
        self._update_all_debug_info()

    def _auto_refresh_debug_info(self):
        """Auto-refresh debug information"""
        if self.auto_refresh:
            self._update_all_debug_info()

    def _update_all_debug_info(self):
        """Update all debug information"""
        try:
            self._update_system_status()
            self._update_performance_metrics()
            self._update_cache_info()
            self._update_overlay_stats()
        except Exception as e:
            self._add_debug_message(f"Error updating debug info: {e}", "ERROR")

    def _update_system_status(self):
        """Update system status display"""
        if not hasattr(self, 'status_text'):
            return

        status_lines = []

        # Check link integration
        if self.link_integration:
            status_lines.append("✅ Link Integration: Active")

            # Check link manager
            if self.link_integration.link_manager:
                status_lines.append("✅ Link Manager: Active")
            else:
                status_lines.append("❌ Link Manager: Not Available")

            # Check overlay manager
            if self.link_integration.overlay_manager:
                status_lines.append("✅ Overlay Manager: Active")
            else:
                status_lines.append("❌ Overlay Manager: Not Available")

            # Check document
            if self.link_integration.current_document:
                doc = self.link_integration.current_document
                status_lines.append(f"📄 Document: Loaded ({len(doc)} pages)")
            else:
                status_lines.append("📄 Document: Not Loaded")
        else:
            status_lines.append("❌ Link Integration: Not Available")

        self.status_text.setPlainText('\n'.join(status_lines))

        # Update components table
        self._update_components_table()

    def _update_components_table(self):
        """Update components status table"""
        if not hasattr(self, 'components_table'):
            return

        components = [
            ("Link Integration", "✅ Active" if self.link_integration else "❌ Inactive", "Main integration object"),
            ("Link Manager",
             "✅ Active" if self.link_integration and self.link_integration.link_manager else "❌ Inactive",
             "PDF link extraction"),
            ("Overlay Manager",
             "✅ Active" if self.link_integration and self.link_integration.overlay_manager else "❌ Inactive",
             "Visual overlays"),
            ("Canvas Widget",
             "✅ Active" if self.link_integration and self.link_integration.canvas_widget else "❌ Inactive",
             "PDF canvas"),
            ("Document",
             "✅ Loaded" if self.link_integration and self.link_integration.current_document else "❌ Not Loaded",
             "PDF document")
        ]

        self.components_table.setRowCount(len(components))

        for row, (component, status, details) in enumerate(components):
            self.components_table.setItem(row, 0, QTableWidgetItem(component))
            self.components_table.setItem(row, 1, QTableWidgetItem(status))
            self.components_table.setItem(row, 2, QTableWidgetItem(details))

    def _update_performance_metrics(self):
        """Update performance metrics"""
        if not hasattr(self, 'performance_table'):
            return

        metrics = []

        # Get metrics from link manager
        if self.link_integration and self.link_integration.link_manager:
            cache_info = self.link_integration.link_manager.get_cache_info()
            metrics.extend([
                ("Cached Pages", str(cache_info.get('cached_pages', 0))),
                ("Total Cached Links", str(cache_info.get('total_cached_links', 0))),
                ("Named Destinations", str(cache_info.get('named_destinations', 0))),
                ("Max Cache Size", str(cache_info.get('max_cache_size', 0)))
            ])

        # Get metrics from overlay manager
        if self.link_integration and self.link_integration.overlay_manager:
            overlay_stats = self.link_integration.overlay_manager.get_overlay_stats()
            metrics.extend([
                ("Active Overlay Pages", str(overlay_stats.get('active_pages', 0))),
                ("Total Overlays", str(overlay_stats.get('total_overlays', 0))),
                ("Pooled Overlays", str(overlay_stats.get('pooled_overlays', 0))),
                ("Current Page", str(overlay_stats.get('current_page', 0) + 1))
            ])

        # Update table
        self.performance_table.setRowCount(len(metrics))

        for row, (metric, value) in enumerate(metrics):
            self.performance_table.setItem(row, 0, QTableWidgetItem(metric))
            self.performance_table.setItem(row, 1, QTableWidgetItem(value))

    def _update_cache_info(self):
        """Update cache information display"""
        if not hasattr(self, 'cache_info_text'):
            return

        if self.link_integration and self.link_integration.link_manager:
            cache_info = self.link_integration.link_manager.get_cache_info()

            cache_text = []
            cache_text.append(f"Cached Pages: {cache_info.get('cached_pages', 0)}")
            cache_text.append(f"Total Links: {cache_info.get('total_cached_links', 0)}")
            cache_text.append(f"Named Destinations: {cache_info.get('named_destinations', 0)}")
            cache_text.append(f"Max Cache Size: {cache_info.get('max_cache_size', 0)}")

            # Calculate cache efficiency
            cached_pages = cache_info.get('cached_pages', 0)
            if cached_pages > 0:
                avg_links_per_page = cache_info.get('total_cached_links', 0) / cached_pages
                cache_text.append(f"Avg Links/Page: {avg_links_per_page:.1f}")

            self.cache_info_text.setPlainText('\n'.join(cache_text))
        else:
            self.cache_info_text.setPlainText("Cache information not available")

    def _update_overlay_stats(self):
        """Update overlay statistics display"""
        if not hasattr(self, 'overlay_stats_text'):
            return

        if self.link_integration and self.link_integration.overlay_manager:
            stats = self.link_integration.overlay_manager.get_overlay_stats()

            stats_text = []
            stats_text.append(f"Active Pages: {stats.get('active_pages', 0)}")
            stats_text.append(f"Total Overlays: {stats.get('total_overlays', 0)}")
            stats_text.append(f"Pooled Overlays: {stats.get('pooled_overlays', 0)}")
            stats_text.append(f"Current Page: {stats.get('current_page', 0) + 1}")
            stats_text.append(f"Visible Pages: {stats.get('visible_pages_count', 0)}")

            self.overlay_stats_text.setPlainText('\n'.join(stats_text))
        else:
            self.overlay_stats_text.setPlainText("Overlay statistics not available")

    def _analyze_page_links(self, page_number: int):
        """Analyze links for specific page"""
        if not self.link_integration or not self.link_integration.link_manager:
            return

        page_index = page_number - 1

        try:
            start_time = time.time()
            links = self.link_integration.link_manager.extract_page_links(page_index)
            extraction_time = time.time() - start_time

            analysis_text = []
            analysis_text.append(f"=== Page {page_number} Link Analysis ===")
            analysis_text.append(f"Extraction Time: {extraction_time:.4f} seconds")
            analysis_text.append(f"Total Links Found: {len(links)}")
            analysis_text.append("")

            # Analyze by type
            link_types = {}
            for link in links:
                link_type = link.link_type.value
                link_types[link_type] = link_types.get(link_type, 0) + 1

            analysis_text.append("Links by Type:")
            for link_type, count in link_types.items():
                analysis_text.append(f"  {link_type}: {count}")

            analysis_text.append("")
            analysis_text.append("Link Details:")

            for i, link in enumerate(links, 1):
                analysis_text.append(f"{i}. {link.description}")
                analysis_text.append(f"   Type: {link.link_type.value}")
                analysis_text.append(f"   Bounds: ({link.bounds.x():.1f}, {link.bounds.y():.1f}, "
                                     f"{link.bounds.width():.1f}, {link.bounds.height():.1f})")
                analysis_text.append(f"   Target: {link.target}")
                analysis_text.append("")

            if hasattr(self, 'link_analysis_text'):
                self.link_analysis_text.setPlainText('\n'.join(analysis_text))

            self._add_debug_message(f"Analyzed page {page_number}: {len(links)} links in {extraction_time:.4f}s",
                                    "INFO")

        except Exception as e:
            error_msg = f"Error analyzing page {page_number}: {e}"
            self._add_debug_message(error_msg, "ERROR")
            if hasattr(self, 'link_analysis_text'):
                self.link_analysis_text.setPlainText(error_msg)

    def _analyze_current_page(self):
        """Analyze current page"""
        page_number = self.analyze_page_spinbox.value()
        self._analyze_page_links(page_number)

    def _run_comprehensive_diagnostics(self):
        """Run comprehensive diagnostics"""
        self._add_debug_message("Running comprehensive diagnostics...", "INFO")

        diagnostics = []

        try:
            # Test link integration
            diagnostics.append("=== Link Integration Diagnostics ===")
            if self.link_integration:
                diagnostics.append("✅ Link integration object exists")

                # Test link manager
                if self.link_integration.link_manager:
                    diagnostics.append("✅ Link manager exists")

                    # Test document
                    if self.link_integration.current_document:
                        doc = self.link_integration.current_document
                        diagnostics.append(f"✅ Document loaded: {len(doc)} pages")

                        # Test link extraction
                        try:
                            start_time = time.time()
                            test_links = self.link_integration.link_manager.extract_page_links(0)
                            extraction_time = time.time() - start_time
                            diagnostics.append(
                                f"✅ Link extraction test: {len(test_links)} links in {extraction_time:.4f}s")
                        except Exception as e:
                            diagnostics.append(f"❌ Link extraction test failed: {e}")
                    else:
                        diagnostics.append("⚠️ No document loaded")
                else:
                    diagnostics.append("❌ No link manager")

                # Test overlay manager
                if self.link_integration.overlay_manager:
                    diagnostics.append("✅ Overlay manager exists")

                    # Test overlay stats
                    try:
                        stats = self.link_integration.overlay_manager.get_overlay_stats()
                        diagnostics.append(f"✅ Overlay stats: {stats}")
                    except Exception as e:
                        diagnostics.append(f"❌ Overlay stats failed: {e}")
                else:
                    diagnostics.append("❌ No overlay manager")
            else:
                diagnostics.append("❌ No link integration")

            # Display results
            result_text = '\n'.join(diagnostics)
            self._add_debug_message("Diagnostics completed", "INFO")

            # Show in debug log
            self._add_debug_message("=== DIAGNOSTICS RESULTS ===", "INFO")
            for line in diagnostics:
                self._add_debug_message(line, "INFO")

        except Exception as e:
            error_msg = f"Diagnostics failed: {e}\n{traceback.format_exc()}"
            self._add_debug_message(error_msg, "ERROR")

    @pyqtSlot(bool)
    def _toggle_auto_refresh(self, enabled: bool):
        """Toggle auto-refresh"""
        self.auto_refresh = enabled
        if enabled:
            self.refresh_timer.start(self.refresh_interval)
            self._add_debug_message("Auto-refresh enabled", "INFO")
        else:
            self.refresh_timer.stop()
            self._add_debug_message("Auto-refresh disabled", "INFO")

    @pyqtSlot(int)
    def _update_refresh_interval(self, interval: int):
        """Update refresh interval"""
        self.refresh_interval = interval
        if self.auto_refresh:
            self.refresh_timer.start(interval)
        self._add_debug_message(f"Refresh interval updated to {interval}ms", "INFO")

    @pyqtSlot(bool)
    def _toggle_verbose_logging(self, enabled: bool):
        """Toggle verbose logging"""
        level = "DEBUG" if enabled else "INFO"
        self._add_debug_message(f"Verbose logging {'enabled' if enabled else 'disabled'}", level)

    @pyqtSlot()
    def _clear_debug_log(self):
        """Clear debug log"""
        self.debug_messages.clear()
        if hasattr(self, 'debug_log_text'):
            self.debug_log_text.clear()
        self._add_debug_message("Debug log cleared", "INFO")

    @pyqtSlot(str)
    def _filter_debug_log(self, filter_level: str):
        """Filter debug log by level"""
        self._update_debug_log_display()

    @pyqtSlot()
    def _export_debug_log(self):
        """Export debug log to file"""
        try:
            from PyQt6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Debug Log", "debug_log.txt", "Text Files (*.txt)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("PDF Link Debug Log\n")
                    f.write("=" * 50 + "\n\n")

                    for msg in self.debug_messages:
                        f.write(f"{msg['formatted']}\n")

                self._add_debug_message(f"Debug log exported to {file_path}", "INFO")

        except Exception as e:
            self._add_debug_message(f"Failed to export debug log: {e}", "ERROR")

    @pyqtSlot()
    def _export_performance_data(self):
        """Export performance data to file"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            import json

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Performance Data", "performance_data.json", "JSON Files (*.json)"
            )

            if file_path:
                performance_data = {
                    'timestamp': time.time(),
                    'cache_info': {},
                    'overlay_stats': {},
                    'system_status': {}
                }

                # Collect performance data
                if self.link_integration and self.link_integration.link_manager:
                    performance_data['cache_info'] = self.link_integration.link_manager.get_cache_info()

                if self.link_integration and self.link_integration.overlay_manager:
                    performance_data['overlay_stats'] = self.link_integration.overlay_manager.get_overlay_stats()

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(performance_data, f, indent=2)

                self._add_debug_message(f"Performance data exported to {file_path}", "INFO")

        except Exception as e:
            self._add_debug_message(f"Failed to export performance data: {e}", "ERROR")

    def update_document_info(self, document, document_path: str = ""):
        """Update debug panel when document changes"""
        if hasattr(self, 'analyze_page_spinbox') and document:
            self.analyze_page_spinbox.setMaximum(len(document))

        self._add_debug_message(f"Document updated: {document_path}", "INFO")
        self._update_all_debug_info()


if __name__ == '__main__':
    print("LinkDebugControlPanel - Use as module import")