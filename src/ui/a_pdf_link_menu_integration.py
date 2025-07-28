from ui.a_pdf_link_integration import PDFLinkIntegration


class PDFLinkMenuIntegration:
    """
    Helper to add link-related menu items to the main window
    """

    @staticmethod
    def add_link_menu_items(main_window, link_integration: PDFLinkIntegration):
        """
        Add link-related menu items to the main window

        Args:
            main_window: Main window with menu bar
            link_integration: Link integration instance
        """
        try:
            menu_bar = main_window.menuBar()

            # Find or create View menu
            view_menu = None
            for action in menu_bar.actions():
                if action.text() == "View":
                    view_menu = action.menu()
                    break

            if not view_menu:
                view_menu = menu_bar.addMenu("View")

            # Add separator
            view_menu.addSeparator()

            # Add link visibility toggle
            from PyQt6.QtGui import QAction
            link_action = QAction("🔗 Show PDF Links", main_window)
            link_action.setCheckable(True)
            link_action.setChecked(True)
            link_action.toggled.connect(link_integration.toggle_link_visibility)
            view_menu.addAction(link_action)

            print("📎 Link menu items added")

        except Exception as e:
            print(f"❌ Error adding link menu items: {e}")
