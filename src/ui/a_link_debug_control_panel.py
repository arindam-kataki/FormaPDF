# Step 3: Enhanced debug control panel to test lazy loading

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QWidget,
                             QCheckBox, QPushButton, QSpinBox, QTextEdit)
from PyQt6.QtCore import pyqtSlot


class LinkDebugControlPanel(QWidget):
    """
    Enhanced control panel for debugging lazy loading
    """

    def __init__(self, link_integration, parent=None):
        super().__init__(parent)
        self.link_integration = link_integration
        self.init_ui()

    def init_ui(self):
        """Initialize the debug control panel UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("🔗 Link Debug Panel")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: blue;")
        layout.addWidget(title)

        # === VISUAL CONTROLS ===
        visual_group = QLabel("Visual Controls:")
        visual_group.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(visual_group)

        # Link visibility toggle
        self.visibility_checkbox = QCheckBox("Show link overlays")
        self.visibility_checkbox.setChecked(True)
        self.visibility_checkbox.toggled.connect(self._on_visibility_toggled)
        layout.addWidget(self.visibility_checkbox)

        # Debug visual indicators
        self.debug_visual_checkbox = QCheckBox("Show debug rectangles (red borders)")
        self.debug_visual_checkbox.setChecked(False)
        self.debug_visual_checkbox.toggled.connect(self._on_debug_visual_toggled)
        layout.addWidget(self.debug_visual_checkbox)

        # === LAZY LOADING CONTROLS ===
        lazy_group = QLabel("Lazy Loading Controls:")
        lazy_group.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lazy_group)

        # Manual page selector for testing
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Test Page:"))

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(999)  # Will be updated when document loads
        page_layout.addWidget(self.page_spinbox)

        force_load_btn = QPushButton("Force Load Page")
        force_load_btn.clicked.connect(self._force_load_page)
        page_layout.addWidget(force_load_btn)

        layout.addLayout(page_layout)

        # Cache controls
        cache_layout = QHBoxLayout()

        clear_cache_btn = QPushButton("Clear Link Cache")
        clear_cache_btn.clicked.connect(self._clear_cache)
        cache_layout.addWidget(clear_cache_btn)

        show_cache_btn = QPushButton("Show Cache Status")
        show_cache_btn.clicked.connect(self._show_cache_status)
        cache_layout.addWidget(show_cache_btn)

        self.add_enhanced_test_buttons(layout)

        layout.addLayout(cache_layout)

        # === STATISTICS DISPLAY ===
        stats_group = QLabel("Current Page Statistics:")
        stats_group.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(stats_group)

        self.stats_label = QLabel("No links found")
        self.stats_label.setStyleSheet("color: gray; font-size: 12px; padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.stats_label)

        # === DEBUG LOG ===
        log_group = QLabel("Debug Log:")
        log_group.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_group)

        self.debug_log = QTextEdit()
        self.debug_log.setMaximumHeight(150)
        self.debug_log.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.debug_log)

        # === ACTION BUTTONS ===
        action_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Refresh Current Page")
        refresh_btn.clicked.connect(self._refresh_current_page)
        action_layout.addWidget(refresh_btn)

        test_btn = QPushButton("🧪 Run Link Test")
        test_btn.clicked.connect(self._run_link_test)
        action_layout.addWidget(test_btn)

        layout.addLayout(action_layout)

        # Update statistics
        self._update_statistics()

    @pyqtSlot(bool)
    def _on_visibility_toggled(self, visible: bool):
        """Handle visibility toggle"""
        self.link_integration.toggle_link_visibility(visible)
        self._log(f"Link visibility: {'ON' if visible else 'OFF'}")

    @pyqtSlot(bool)
    def _on_debug_visual_toggled(self, visible: bool):
        """Toggle debug visual indicators"""
        # This would need to be implemented in your overlay manager
        self._log(f"Debug visuals: {'ON' if visible else 'OFF'}")

        if hasattr(self.link_integration, 'overlay_manager'):
            # Add debug styling to overlays
            for overlay in self.link_integration.overlay_manager.link_overlays:
                if visible:
                    overlay.setStyleSheet("background-color: rgba(255, 0, 0, 50); border: 2px solid red;")
                else:
                    overlay.setStyleSheet("")

    @pyqtSlot()
    def _force_load_page(self):
        """Force load a specific page for testing"""
        page_num = self.page_spinbox.value() - 1  # Convert to 0-based
        self._log(f"Force loading page {page_num + 1}...")

        if hasattr(self.link_integration, 'overlay_manager'):
            # Force refresh by clearing cache first
            if hasattr(self.link_integration.link_manager, 'page_links_cache'):
                if page_num in self.link_integration.link_manager.page_links_cache:
                    del self.link_integration.link_manager.page_links_cache[page_num]
                    self._log(f"Cleared cache for page {page_num + 1}")

            # Now update
            zoom = getattr(self.link_integration.main_window, 'current_zoom', 1.0)
            self.link_integration.overlay_manager.update_page_links(page_num, zoom)
            self._update_statistics()

    @pyqtSlot()
    def _clear_cache(self):
        """Clear the link cache"""
        if hasattr(self.link_integration.link_manager, 'page_links_cache'):
            cache_size = len(self.link_integration.link_manager.page_links_cache)
            self.link_integration.link_manager.page_links_cache.clear()
            self._log(f"Cleared cache ({cache_size} pages)")

    @pyqtSlot()
    def _show_cache_status(self):
        """Show cache status"""
        if hasattr(self.link_integration.link_manager, 'page_links_cache'):
            cache = self.link_integration.link_manager.page_links_cache
            cached_pages = sorted(cache.keys())
            total_links = sum(len(links) for links in cache.values())

            self._log(f"Cache Status: {len(cached_pages)} pages cached")
            self._log(f"Cached pages: {[p + 1 for p in cached_pages]}")  # Convert to 1-based
            self._log(f"Total cached links: {total_links}")

    @pyqtSlot()
    def _refresh_current_page(self):
        """Refresh current page"""
        if hasattr(self.link_integration, 'overlay_manager'):
            manager = self.link_integration.overlay_manager
            if manager.current_page >= 0:
                self._log(f"Refreshing page {manager.current_page + 1}")
                manager.update_page_links(manager.current_page, manager.current_zoom)
                self._update_statistics()

    @pyqtSlot()
    def _run_link_test(self):
        """Run comprehensive link test"""
        self._log("=== Running Link Test ===")

        # Test 1: Check if link manager exists
        if not self.link_integration.link_manager:
            self._log("❌ FAIL: No link manager")
            return
        else:
            self._log("✅ PASS: Link manager exists")

        # Test 2: Check if PDF document is loaded
        if not hasattr(self.link_integration.link_manager,
                       'pdf_document') or not self.link_integration.link_manager.pdf_document:
            self._log("❌ FAIL: No PDF document loaded")
            return
        else:
            self._log("✅ PASS: PDF document loaded")

        # Test 3: Check overlay manager
        if not self.link_integration.overlay_manager:
            self._log("❌ FAIL: No overlay manager")
            return
        else:
            self._log("✅ PASS: Overlay manager exists")

        # Test 4: Try to get links from current page
        try:
            current_page = getattr(self.link_integration.overlay_manager, 'current_page', 0)
            links = self.link_integration.link_manager.get_page_links(current_page)
            self._log(f"✅ PASS: Got {len(links)} links from page {current_page + 1}")
        except Exception as e:
            self._log(f"❌ FAIL: Error getting links: {e}")

        self._log("=== Test Complete ===")

    def _update_statistics(self):
        """Update the statistics display"""
        stats = self.link_integration.get_link_statistics()

        if stats['total'] == 0:
            self.stats_label.setText("No links found on current page")
        else:
            type_breakdown = ", ".join([f"{count} {link_type}" for link_type, count in stats['by_type'].items()])
            self.stats_label.setText(f"{stats['total']} links: {type_breakdown}")

    def _log(self, message: str):
        """Add message to debug log"""
        self.debug_log.append(message)
        print(f"🐛 DEBUG: {message}")

    def update_page_range(self, max_pages: int):
        """Update the page range when document loads"""
        self.page_spinbox.setMaximum(max_pages)

    def _test_all_pages_for_links(self):
        """Test all pages to find which ones have links"""
        if not self.link_integration.link_manager:
            self._log("❌ No link manager available")
            return

        if not hasattr(self.link_integration.link_manager,
                       'pdf_document') or not self.link_integration.link_manager.pdf_document:
            self._log("❌ No PDF document loaded")
            return

        document = self.link_integration.link_manager.pdf_document
        total_pages = document.get_page_count()

        self._log(f"=== Testing all {total_pages} pages for links ===")

        pages_with_links = []
        total_links_found = 0

        for page_num in range(total_pages):
            try:
                # Force refresh to get accurate count
                links = self.link_integration.link_manager.get_page_links(page_num, force_refresh=True)
                link_count = len(links)

                if link_count > 0:
                    pages_with_links.append((page_num + 1, link_count))  # Convert to 1-based
                    total_links_found += link_count

                    self._log(f"📄 Page {page_num + 1}: {link_count} links")

                    # Show first few links
                    for i, link in enumerate(links[:3]):
                        self._log(f"   {i + 1}. {link.link_type}: {link.tooltip}")
                    if len(links) > 3:
                        self._log(f"   ... and {len(links) - 3} more")
                else:
                    self._log(f"📄 Page {page_num + 1}: No links")

            except Exception as e:
                self._log(f"❌ Error testing page {page_num + 1}: {e}")

        self._log("=== SUMMARY ===")
        if pages_with_links:
            self._log(f"✅ Found links on {len(pages_with_links)} pages:")
            for page_num, count in pages_with_links:
                self._log(f"   Page {page_num}: {count} links")
            self._log(f"📊 Total links in document: {total_links_found}")

            # Auto-test the first page with links
            if pages_with_links:
                test_page = pages_with_links[0][0] - 1  # Convert back to 0-based
                self._log(f"🧪 Auto-testing page {test_page + 1} with {pages_with_links[0][1]} links...")
                self.page_spinbox.setValue(test_page + 1)
                self._force_load_page()
        else:
            self._log("❌ No links found in entire document")

    def _test_specific_pages(self):
        """Test specific pages that are more likely to have links"""
        test_pages = [0, 1, 2]  # Usually first few pages have links

        self._log("=== Testing specific pages for links ===")

        for page_num in test_pages:
            try:
                links = self.link_integration.link_manager.get_page_links(page_num, force_refresh=True)
                self._log(f"📄 Page {page_num + 1}: {len(links)} links")

                if links:
                    self._log(f"🎯 Testing page {page_num + 1} with visual overlays...")
                    self.page_spinbox.setValue(page_num + 1)
                    self._force_load_page()
                    break  # Stop at first page with links

            except Exception as e:
                self._log(f"❌ Error testing page {page_num + 1}: {e}")

    # Add this button to your debug panel init_ui method:
    def add_enhanced_test_buttons(self):
        """Add enhanced testing buttons"""

        # Add to your layout
        test_all_btn = QPushButton("🔍 Test All Pages")
        test_all_btn.clicked.connect(self._test_all_pages_for_links)
        layout.addWidget(test_all_btn)

        test_specific_btn = QPushButton("🎯 Test Common Pages")
        test_specific_btn.clicked.connect(self._test_specific_pages)
        layout.addWidget(test_specific_btn)

    def add_enhanced_test_buttons(self, layout):
        """Add enhanced testing buttons - FIXED VERSION"""

        # Add to the passed layout
        test_all_btn = QPushButton("🔍 Test All Pages")
        test_all_btn.clicked.connect(self._test_all_pages_for_links)
        layout.addWidget(test_all_btn)

        test_specific_btn = QPushButton("🎯 Test Common Pages")
        test_specific_btn.clicked.connect(self._test_specific_pages)
        layout.addWidget(test_specific_btn)
