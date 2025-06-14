"""
Fix for properties_panel.py TypeError
"""


def fix_properties_panel():
    """Fix the TypeError in properties_panel.py"""

    from pathlib import Path

    properties_panel_path = Path("src/ui/properties_panel.py")

    if not properties_panel_path.exists():
        print(f"File not found: {properties_panel_path}")
        return False

    print("Fixing properties_panel.py TypeError...")

    try:
        # Read the file
        with open(properties_panel_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find and fix the MultilineTextPropertyWidget __init__ method
        old_init = '''    def __init__(self, name: str, initial_value: str = ""):
        widget = QTextEdit()
        widget.setMaximumHeight(80)
        widget.setPlainText(initial_value)
        super().__init__(name, widget, "textChanged")'''

        new_init = '''    def __init__(self, name: str, initial_value = ""):
        widget = QTextEdit()
        widget.setMaximumHeight(80)

        # Handle both string and list inputs
        if isinstance(initial_value, list):
            text_value = '\\n'.join(initial_value)
        else:
            text_value = str(initial_value) if initial_value else ""

        widget.setPlainText(text_value)
        super().__init__(name, widget, "textChanged")'''

        if old_init in content:
            content = content.replace(old_init, new_init)
            print("  ✅ Fixed MultilineTextPropertyWidget.__init__")

        # Also fix the set_value method to be more robust
        old_set_value = '''    def set_value(self, value):
        self.widget.blockSignals(True)
        if isinstance(value, list):
            self.widget.setPlainText('\\n'.join(value))
        else:
            self.widget.setPlainText(str(value))
        self.widget.blockSignals(False)'''

        new_set_value = '''    def set_value(self, value):
        self.widget.blockSignals(True)
        if isinstance(value, list):
            self.widget.setPlainText('\\n'.join(str(v) for v in value))
        else:
            self.widget.setPlainText(str(value) if value else "")
        self.widget.blockSignals(False)'''

        if old_set_value in content:
            content = content.replace(old_set_value, new_set_value)
            print("  ✅ Fixed MultilineTextPropertyWidget.set_value")
        else:
            # If exact match not found, let's be more flexible
            import re
            # Look for the set_value method in MultilineTextPropertyWidget
            pattern = r'(class MultilineTextPropertyWidget.*?def set_value\(self, value\):.*?self\.widget\.blockSignals\(False\))'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                old_method = match.group(1)
                # Replace just the problematic line
                new_method = old_method.replace(
                    "self.widget.setPlainText('\\n'.join(value))",
                    "self.widget.setPlainText('\\n'.join(str(v) for v in value))"
                ).replace(
                    "self.widget.setPlainText(str(value))",
                    "self.widget.setPlainText(str(value) if value else \"\")"
                )
                content = content.replace(old_method, new_method)
                print("  ✅ Fixed MultilineTextPropertyWidget.set_value (flexible match)")

        # Write back the fixed content
        with open(properties_panel_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ properties_panel.py TypeError fixed!")
        return True

    except Exception as e:
        print(f"Error fixing properties_panel.py: {e}")
        return False


if __name__ == "__main__":
    fix_properties_panel()