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

        sync_layout = QHBoxLayout()

        diagnose_btn = QPushButton("🔍 Diagnose Sync Issue")
        diagnose_btn.clicked.connect(self._diagnose_document_sync_detailed)
        sync_layout.addWidget(diagnose_btn)

        force_sync_btn = QPushButton("🔧 Force Sync Document")
        force_sync_btn.clicked.connect(self._force_document_sync)
        sync_layout.addWidget(force_sync_btn)

        layout.addLayout(sync_layout)

        # Add these buttons after your existing ones:
        test_pages_btn = QPushButton("🔍 Test Multiple Pages")
        test_pages_btn.clicked.connect(self._test_multiple_pages_for_links)
        layout.addWidget(test_pages_btn)

        debug_structure_btn = QPushButton("🔧 Debug Document Structure")
        debug_structure_btn.clicked.connect(self._debug_document_structure)
        layout.addWidget(debug_structure_btn)
        # Update statistics
        self._update_statistics()

        overlay_debug_layout = QHBoxLayout()

        debug_overlay_btn = QPushButton("🔍 Debug Overlays")
        debug_overlay_btn.clicked.connect(self._debug_overlay_visibility)
        overlay_debug_layout.addWidget(debug_overlay_btn)

        force_overlay_btn = QPushButton("🔧 Force Create Overlays")
        force_overlay_btn.clicked.connect(self._force_overlay_creation)
        overlay_debug_layout.addWidget(force_overlay_btn)

        layout.addLayout(overlay_debug_layout)

        integration_layout = QHBoxLayout()

        test_canvas_btn = QPushButton("🧪 Test Canvas Integration")
        test_canvas_btn.clicked.connect(self._test_canvas_integration)
        integration_layout.addWidget(test_canvas_btn)

        manual_integrate_btn = QPushButton("🔧 Manual Canvas Integration")
        manual_integrate_btn.clicked.connect(self._manual_canvas_integration)
        integration_layout.addWidget(manual_integrate_btn)

        layout.addLayout(integration_layout)

        overlay_test_btn = QPushButton("🔍 Test Overlay System")
        overlay_test_btn.clicked.connect(self._test_overlay_system)
        layout.addWidget(overlay_test_btn)

    def _force_overlay_creation(self):
        """Force create overlays for current page"""
        self._log("=== Force Overlay Creation ===")

        if not self.link_integration.overlay_manager:
            self._log("❌ No overlay manager")
            return

        overlay_mgr = self.link_integration.overlay_manager
        main_window = self.link_integration.main_window
        current_page = getattr(main_window, 'current_page', 0)
        current_zoom = getattr(main_window, 'current_zoom', 1.0)

        self._log(f"🔧 Force creating overlays for page {current_page + 1}")
        overlay_mgr.update_page_links(current_page, current_zoom)
        self._log(f"📊 Created {len(overlay_mgr.link_overlays)} overlays")

    def _test_overlay_system(self):
        """Simple test of overlay system"""
        self._log("=== Overlay System Test ===")

        if hasattr(self.link_integration, 'overlay_manager'):
            if self.link_integration.overlay_manager is None:
                self._log("❌ overlay_manager is None - need canvas integration")
            else:
                self._log("✅ Overlay manager exists")
                overlay_mgr = self.link_integration.overlay_manager
                self._log(f"📊 Current overlays: {len(overlay_mgr.link_overlays)}")
        else:
            self._log("❌ No overlay_manager attribute")

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

    def add_enhanced_test_buttons(self, layout):
        """Add enhanced testing buttons - FIXED VERSION"""

        # Add to the passed layout
        test_all_btn = QPushButton("🔍 Test All Pages")
        test_all_btn.clicked.connect(self._test_all_pages_for_links)
        layout.addWidget(test_all_btn)

        test_specific_btn = QPushButton("🎯 Test Common Pages")
        test_specific_btn.clicked.connect(self._test_specific_pages)
        layout.addWidget(test_specific_btn)

    def _diagnose_document_sync_detailed(self):
        """Detailed diagnosis of document sync issue"""
        self._log("=== DETAILED Document Sync Diagnosis ===")

        # Step 1: Check main window document
        main_window = self.link_integration.main_window
        if hasattr(main_window, 'document') and main_window.document:
            doc = main_window.document
            self._log("✅ Main window has document")
            self._log(f"📄 Document type: {type(doc)}")
            self._log(f"📄 Document attributes: {[attr for attr in dir(doc) if not attr.startswith('_')][:10]}")

            if hasattr(doc, 'get_page_count'):
                self._log(f"📄 Page count: {doc.get_page_count()}")

            if hasattr(doc, 'doc'):  # PyMuPDF document
                self._log(f"📋 Has PyMuPDF doc: {type(doc.doc)}")

        else:
            self._log("❌ No document in main window")
            return

        # Step 2: Check link integration
        self._log("\n--- Link Integration Check ---")
        if hasattr(self.link_integration, 'set_pdf_document'):
            self._log("✅ PDFLinkIntegration has set_pdf_document method")
        else:
            self._log("❌ PDFLinkIntegration missing set_pdf_document method")

        # Step 3: Check link manager
        self._log("\n--- Link Manager Check ---")
        link_manager = self.link_integration.link_manager
        if hasattr(link_manager, 'set_pdf_document'):
            self._log("✅ PDFLinkManager has set_pdf_document method")
        else:
            self._log("❌ PDFLinkManager missing set_pdf_document method")

        # Step 4: Check if document is actually in link manager
        if hasattr(link_manager, 'pdf_document'):
            if link_manager.pdf_document is not None:
                self._log("✅ Link manager HAS pdf_document")
                self._log(f"📋 Link manager doc type: {type(link_manager.pdf_document)}")

                # Check if it's the same document
                if link_manager.pdf_document == main_window.document:
                    self._log("✅ Documents are the SAME object")
                else:
                    self._log("⚠️ Documents are DIFFERENT objects")

            else:
                self._log("❌ Link manager pdf_document is None")
        else:
            self._log("❌ Link manager has no pdf_document attribute")

        # Step 5: Manual sync test
        self._log("\n--- Manual Sync Test ---")
        try:
            self._log("🔧 Attempting manual sync...")
            self.link_integration.set_pdf_document(main_window.document)

            # Re-check
            if hasattr(link_manager, 'pdf_document') and link_manager.pdf_document:
                self._log("✅ Manual sync SUCCESS!")

                # Test link extraction
                try:
                    test_links = link_manager.get_page_links(0)
                    self._log(f"🔗 Test extraction: {len(test_links)} links on page 1")

                    if test_links:
                        self._log("🎉 SOLUTION FOUND: Links are working!")
                        self._log("💡 Run the link test again now")
                    else:
                        self._log("⚠️ No links found on page 1 (may be normal)")

                except Exception as e:
                    self._log(f"❌ Link extraction failed: {e}")

            else:
                self._log("❌ Manual sync failed - still no document")

        except Exception as e:
            self._log(f"❌ Manual sync error: {e}")
            import traceback
            self._log(f"📋 Traceback: {traceback.format_exc()}")

    # ADD A MANUAL SYNC BUTTON TO YOUR DEBUG PANEL
    def _force_document_sync(self):
        """Force document sync from main window to link manager"""
        self._log("=== FORCE Document Sync ===")

        main_window = self.link_integration.main_window

        if not (hasattr(main_window, 'document') and main_window.document):
            self._log("❌ No document to sync")
            return

        try:
            doc = main_window.document
            self._log(f"📋 Syncing document: {type(doc)}")

            # Force sync
            self.link_integration.set_pdf_document(doc)

            # Verify
            if (hasattr(self.link_integration.link_manager, 'pdf_document') and
                    self.link_integration.link_manager.pdf_document):
                self._log("✅ SYNC SUCCESS!")

                # Update statistics
                self._update_statistics()

                # Run a quick test
                try:
                    links = self.link_integration.link_manager.get_page_links(0)
                    self._log(f"🔗 Quick test: {len(links)} links on page 1")
                except Exception as e:
                    self._log(f"⚠️ Quick test failed: {e}")

            else:
                self._log("❌ Sync failed")

        except Exception as e:
            self._log(f"❌ Sync error: {e}")

    def _test_multiple_pages_for_links(self):
        """Test multiple pages to find which ones have links"""
        self._log("=== Testing Multiple Pages for Links ===")

        link_manager = self.link_integration.link_manager
        document = link_manager.pdf_document

        if not document:
            self._log("❌ No document loaded")
            return

        try:
            total_pages = document.get_page_count()
            self._log(f"📄 Document has {total_pages} pages")

            pages_with_links = []
            test_pages = min(10, total_pages)  # Test first 10 pages

            for page_num in range(test_pages):
                try:
                    links = link_manager.get_page_links(page_num, force_refresh=True)
                    link_count = len(links)

                    if link_count > 0:
                        pages_with_links.append((page_num + 1, link_count))
                        self._log(f"📄 Page {page_num + 1}: ✅ {link_count} links")
                    else:
                        self._log(f"📄 Page {page_num + 1}: ⚪ No links")

                except Exception as e:
                    self._log(f"📄 Page {page_num + 1}: ❌ Error: {e}")

            if pages_with_links:
                self._log(f"\n🎉 FOUND LINKS! Pages: {[p[0] for p in pages_with_links]}")
                # Auto-test first page with links
                first_page = pages_with_links[0][0]
                self.page_spinbox.setValue(first_page)
                self._force_load_page()
            else:
                self._log("📋 No links found in first 10 pages")

        except Exception as e:
            self._log(f"❌ Error: {e}")

    def _test_multiple_pages_for_links(self):
        """Test multiple pages to find which ones have links"""
        self._log("=== Testing Multiple Pages for Links ===")

        if not (hasattr(self.link_integration.link_manager, 'pdf_document') and
                self.link_integration.link_manager.pdf_document):
            self._log("❌ No document loaded")
            return

        link_manager = self.link_integration.link_manager
        document = link_manager.pdf_document

        try:
            total_pages = document.get_page_count()
            self._log(f"📄 Document has {total_pages} pages")

            pages_with_links = []
            test_pages = min(10, total_pages)  # Test first 10 pages

            for page_num in range(test_pages):
                try:
                    # Force refresh to get accurate count
                    links = link_manager.get_page_links(page_num, force_refresh=True)
                    link_count = len(links)

                    if link_count > 0:
                        pages_with_links.append((page_num + 1, link_count))  # Convert to 1-based
                        self._log(f"📄 Page {page_num + 1}: ✅ {link_count} links")

                        # Show first few links
                        for i, link in enumerate(links[:2]):
                            self._log(f"   {i + 1}. {link.link_type}: {link.tooltip}")
                    else:
                        self._log(f"📄 Page {page_num + 1}: ⚪ No links")

                except Exception as e:
                    self._log(f"📄 Page {page_num + 1}: ❌ Error: {e}")

            # Summary
            if pages_with_links:
                self._log(f"\n🎉 FOUND LINKS! Pages with links: {[p[0] for p in pages_with_links]}")

                # Auto-test the first page with links
                first_page_with_links = pages_with_links[0][0]
                self._log(f"🧪 Auto-testing page {first_page_with_links}...")

                self.page_spinbox.setValue(first_page_with_links)
                self._force_load_page()

            else:
                self._log("📋 No links found in first 10 pages")
                self._log("💡 This PDF may not have hyperlinks, or they may be on later pages")

        except Exception as e:
            self._log(f"❌ Error testing pages: {e}")

    def _debug_document_structure(self):
        """Debug the document structure to see if links can be extracted"""
        self._log("=== Document Structure Debug ===")

        if not (hasattr(self.link_integration.link_manager, 'pdf_document') and
                self.link_integration.link_manager.pdf_document):
            self._log("❌ No document loaded")
            return

        link_manager = self.link_integration.link_manager
        document = link_manager.pdf_document

        try:
            self._log(f"📋 Document type: {type(document)}")
            self._log(f"📋 Document attributes: {[attr for attr in dir(document) if not attr.startswith('_')][:15]}")

            # Check if it has PyMuPDF structure
            if hasattr(document, 'doc'):
                self._log(f"✅ Has 'doc' attribute: {type(document.doc)}")

                # Try to access first page directly
                try:
                    if hasattr(document, 'get_page_count'):
                        page_count = document.get_page_count()
                        self._log(f"📄 Page count: {page_count}")

                    if page_count > 0:
                        # Test direct PyMuPDF access
                        page_0 = document.doc[0]
                        self._log(f"📄 Direct page 0 access: {type(page_0)}")

                        raw_links = page_0.get_links()
                        self._log(f"🔗 Direct raw links on page 1: {len(raw_links)}")

                        if raw_links:
                            self._log("🎉 FOUND RAW LINKS! The issue is in extract_page_links method")
                            for i, link in enumerate(raw_links[:2]):
                                self._log(f"   Raw link {i + 1}: {link}")
                        else:
                            self._log("📋 No raw links found on page 1 (may be normal)")

                except Exception as e:
                    self._log(f"❌ Error accessing page directly: {e}")

            else:
                self._log("❌ Document missing 'doc' attribute")

        except Exception as e:
            self._log(f"❌ Document structure debug failed: {e}")

    def _debug_overlay_visibility(self):
        """Debug why overlays aren't visible"""
        self._log("=== Overlay Visibility Debug ===")

        if not hasattr(self.link_integration, 'overlay_manager'):
            self._log("❌ No overlay_manager attribute")
            return

        if self.link_integration.overlay_manager is None:
            self._log("❌ overlay_manager is None - canvas integration not complete")
            return

        overlay_mgr = self.link_integration.overlay_manager
        self._log("✅ Overlay manager exists")
        self._log(f"📋 Overlay count: {len(overlay_mgr.link_overlays)}")

        if overlay_mgr.link_overlays:
            for i, overlay in enumerate(overlay_mgr.link_overlays):
                geometry = overlay.geometry()
                self._log(
                    f"   Overlay {i + 1}: pos({geometry.x()}, {geometry.y()}) size({geometry.width()}x{geometry.height()})")
                self._log(f"   Visible: {overlay.isVisible()}")
        else:
            self._log("❌ No overlay widgets exist")

    def _test_canvas_integration(self):
        """Test if canvas integration is working"""
        self._log("=== Canvas Integration Test ===")

        main_window = self.link_integration.main_window

        if hasattr(main_window, 'canvas_widget') and main_window.canvas_widget:
            canvas = main_window.canvas_widget
            self._log(f"✅ Canvas widget exists: {type(canvas)}")

            if self.link_integration.overlay_manager:
                overlay_parent = self.link_integration.overlay_manager.parent()
                if overlay_parent == canvas:
                    self._log("✅ Overlay manager is child of canvas")
                else:
                    self._log(f"❌ Overlay manager parent is: {type(overlay_parent)}")
            else:
                self._log("❌ No overlay manager")
        else:
            self._log("❌ No canvas widget found")

    def _manual_canvas_integration(self):
        """Manually integrate with canvas"""
        self._log("=== Manual Canvas Integration ===")

        main_window = self.link_integration.main_window

        if not (hasattr(main_window, 'canvas_widget') and main_window.canvas_widget):
            self._log("❌ No canvas widget to integrate with")
            return

        try:
            canvas = main_window.canvas_widget
            self._log(f"🔧 Integrating with canvas: {type(canvas)}")

            self.link_integration.integrate_with_canvas(canvas)

            if self.link_integration.overlay_manager:
                self._log("✅ Integration successful")
            else:
                self._log("❌ Integration failed")

        except Exception as e:
            self._log(f"❌ Integration error: {e}")

    def _create_overlays_for_current_page(self):
        """Create overlays for the currently visible page"""
        self._log("=== Creating Overlays for Current Page ===")

        if not self.link_integration.overlay_manager:
            self._log("❌ No overlay manager")
            return

        # You're on page 4 (0-based = 3)
        current_page = 3  # Page 4 in 0-based indexing
        current_zoom = 1.0

        self._log(f"🔧 Creating overlays for page {current_page + 1} at zoom {current_zoom}")

        try:
            overlay_mgr = self.link_integration.overlay_manager
            overlay_mgr.update_page_links(current_page, current_zoom)

            self._log(f"📊 Result: {len(overlay_mgr.link_overlays)} overlays created")

            if overlay_mgr.link_overlays:
                self._log("🎉 SUCCESS! Overlays created")
                for i, overlay in enumerate(overlay_mgr.link_overlays[:3]):
                    self._log(f"   Overlay {i + 1}: visible={overlay.isVisible()}, geometry={overlay.geometry()}")
            else:
                self._log("❌ No overlays created despite links existing")

        except Exception as e:
            self._log(f"❌ Error creating overlays: {e}")
            import traceback
            self._log(f"📋 Traceback: {traceback.format_exc()}")

    def _force_overlay_creation(self):
        """Force create overlays for current page"""
        self._log("=== Force Overlay Creation ===")

        if not self.link_integration.overlay_manager:
            self._log("❌ No overlay manager")
            return

        overlay_mgr = self.link_integration.overlay_manager

        # Get current page from main window
        main_window = self.link_integration.main_window
        current_page = getattr(main_window, 'current_page', 0)
        current_zoom = getattr(main_window, 'current_zoom', 1.0)

        self._log(f"🔧 Force creating overlays for page {current_page + 1} at zoom {current_zoom}")

        # Force update
        overlay_mgr.update_page_links(current_page, current_zoom)

        # Check results
        self._log(f"📊 Created {len(overlay_mgr.link_overlays)} overlays")