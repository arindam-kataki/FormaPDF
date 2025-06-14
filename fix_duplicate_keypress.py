#!/usr/bin/env python3
"""
Fix keyPressEvent Logic Issues
Creates a corrected keyPressEvent method with proper logic flow
"""

import os
from pathlib import Path


def create_corrected_keypress_method():
    """Create a logically correct keyPressEvent method"""

    corrected_method = '''    def keyPressEvent(self, event):
        """Enhanced keyboard event handling for fields, scrolling, and zoom"""
        key = event.key()
        modifiers = event.modifiers()

        # Get selected field state once
        selected_field = self.selection_handler.get_selected_field()

        # Priority 1: Field manipulation (arrow keys only, when field selected)
        if selected_field and key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            step = 10 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1

            dx, dy = 0, 0
            if key == Qt.Key.Key_Up:
                dy = -step
            elif key == Qt.Key.Key_Down:
                dy = step
            elif key == Qt.Key.Key_Left:
                dx = -step
            elif key == Qt.Key.Key_Right:
                dx = step

            # Move the field within bounds
            new_x = selected_field.x + dx
            new_y = selected_field.y + dy
            selected_field.x = max(0, min(new_x, self.width() - selected_field.width))
            selected_field.y = max(0, min(new_y, self.height() - selected_field.height))

            self.draw_overlay()
            event.accept()
            return  # Exit early - don't process other shortcuts

        # Priority 2: Zoom shortcuts (work regardless of field selection)
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            zoom_handled = False

            if key in [Qt.Key.Key_Plus, Qt.Key.Key_Equal]:
                if hasattr(self, 'zoom_in_step'):
                    self.zoom_in_step()
                    zoom_handled = True
            elif key == Qt.Key.Key_Minus:
                if hasattr(self, 'zoom_out_step'):
                    self.zoom_out_step()
                    zoom_handled = True
            elif key == Qt.Key.Key_0:
                if hasattr(self, 'set_zoom'):
                    self.set_zoom(1.0)  # Reset to 100%
                    zoom_handled = True

            if zoom_handled:
                event.accept()
                return  # Exit early

        # Priority 3: Navigation shortcuts (Page Up/Down, Home/End)
        # These work regardless of field selection
        navigation_handled = False

        if key == Qt.Key.Key_PageUp:
            if hasattr(self, 'scroll_page'):
                self.scroll_page(-1)
                navigation_handled = True
        elif key == Qt.Key.Key_PageDown:
            if hasattr(self, 'scroll_page'):
                self.scroll_page(1)
                navigation_handled = True
        elif key == Qt.Key.Key_Home:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if hasattr(self, 'scroll_to_top'):
                    self.scroll_to_top()
                    navigation_handled = True
            else:
                if hasattr(self, 'scroll_to_left'):
                    self.scroll_to_left()
                    navigation_handled = True
        elif key == Qt.Key.Key_End:
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if hasattr(self, 'scroll_to_bottom'):
                    self.scroll_to_bottom()
                    navigation_handled = True
            else:
                if hasattr(self, 'scroll_to_right'):
                    self.scroll_to_right()
                    navigation_handled = True

        if navigation_handled:
            event.accept()
            return  # Exit early

        # Priority 4: Arrow key scrolling (ONLY when no field is selected)
        # If field is selected, arrow keys were already handled above
        if not selected_field and key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            scroll_handled = False

            if key == Qt.Key.Key_Up:
                if hasattr(self, 'scroll_vertical'):
                    self.scroll_vertical(-50)
                    scroll_handled = True
            elif key == Qt.Key.Key_Down:
                if hasattr(self, 'scroll_vertical'):
                    self.scroll_vertical(50)
                    scroll_handled = True
            elif key == Qt.Key.Key_Left:
                if hasattr(self, 'scroll_horizontal'):
                    self.scroll_horizontal(-50)
                    scroll_handled = True
            elif key == Qt.Key.Key_Right:
                if hasattr(self, 'scroll_horizontal'):
                    self.scroll_horizontal(50)
                    scroll_handled = True

            if scroll_handled:
                event.accept()
                return  # Exit early

        # Fallback: Pass unhandled events to parent
        super().keyPressEvent(event)'''

    return corrected_method


def replace_keypress_method():
    """Replace the keyPressEvent method in pdf_canvas.py with corrected version"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Replacing keyPressEvent method with corrected logic...")

    try:
        # Read current content
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find existing keyPressEvent method(s)
        import re
        pattern = r'def keyPressEvent\(self[^)]*\):'
        matches = list(re.finditer(pattern, content))

        if not matches:
            print("❌ No keyPressEvent method found")
            return False

        print(f"🔍 Found {len(matches)} keyPressEvent method(s)")

        # Remove all existing keyPressEvent methods
        new_content = content
        lines = content.split('\n')

        # Process matches in reverse order to maintain line numbers
        for match in reversed(matches):
            start_line = content[:match.start()].count('\n')

            # Find the end of this method (next method or class/function)
            method_lines = []
            current_line = start_line

            # Get the method signature line
            method_lines.append(lines[current_line])
            current_line += 1

            # Get the docstring if present
            if current_line < len(lines) and '"""' in lines[current_line]:
                while current_line < len(lines):
                    method_lines.append(lines[current_line])
                    if lines[current_line].count('"""') == 2 or (
                            lines[current_line].endswith('"""') and len(method_lines) > 1):
                        current_line += 1
                        break
                    current_line += 1

            # Get the method body (indented lines)
            base_indent = None
            while current_line < len(lines):
                line = lines[current_line]

                # Empty lines are part of the method
                if line.strip() == '':
                    method_lines.append(line)
                    current_line += 1
                    continue

                # Check indentation
                if line.startswith('    ') and not line.startswith('class ') and not line.startswith('def '):
                    # This line is part of the method body
                    if base_indent is None:
                        base_indent = len(line) - len(line.lstrip())

                    # If indentation is consistent with method body, include it
                    line_indent = len(line) - len(line.lstrip())
                    if line_indent >= base_indent or line.strip() == '':
                        method_lines.append(line)
                        current_line += 1
                    else:
                        # Less indented - probably next method/class
                        break
                else:
                    # Not indented or is a class/def - end of method
                    break

            # Remove this method from content
            start_pos = 0
            for i in range(start_line):
                start_pos = new_content.find('\n', start_pos) + 1

            end_pos = start_pos
            for line in method_lines:
                end_pos = new_content.find('\n', end_pos) + 1

            # Remove the method
            new_content = new_content[:start_pos] + new_content[end_pos:]
            print(f"  ✅ Removed keyPressEvent method at line {start_line + 1}")

        # Find a good place to insert the corrected method
        corrected_method = create_corrected_keypress_method()

        # Look for mousePressEvent or wheelEvent to insert before
        insert_targets = [
            '    def mousePressEvent(self',
            '    def wheelEvent(self',
            '    def paintEvent(self',
            '    def resizeEvent(self'
        ]

        insert_pos = -1
        for target in insert_targets:
            pos = new_content.find(target)
            if pos != -1:
                insert_pos = pos
                break

        if insert_pos != -1:
            # Insert before found method
            new_content = new_content[:insert_pos] + corrected_method + '\n\n' + new_content[insert_pos:]
            print("  ✅ Inserted corrected method before existing method")
        else:
            # Find end of class and insert there
            class_pos = new_content.find('class PDFCanvas')
            if class_pos != -1:
                # Find a reasonable place in the class
                methods_section = new_content.find('    def ', class_pos)
                if methods_section != -1:
                    new_content = new_content[:methods_section] + corrected_method + '\n\n' + new_content[
                                                                                              methods_section:]
                    print("  ✅ Inserted corrected method in class")
                else:
                    print("  ❌ Could not find insertion point in class")
                    return False
            else:
                print("  ❌ Could not find PDFCanvas class")
                return False

        # Write the updated content
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ Successfully replaced keyPressEvent method with corrected logic")
        return True

    except Exception as e:
        print(f"❌ Error replacing method: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_corrected_logic():
    """Verify the corrected logic is in place"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for key logic elements
        checks = [
            ("Single keyPressEvent method", content.count('def keyPressEvent(') == 1),
            ("Field selection priority", "selected_field and key in [Qt.Key.Key_Up" in content),
            ("Early returns", "return  # Exit early" in content),
            ("Zoom shortcuts", "ControlModifier" in content and "zoom_in_step" in content),
            ("Navigation shortcuts", "Key_PageUp" in content and "scroll_page" in content),
            ("Arrow scrolling only when no field", "not selected_field and key in [Qt.Key.Key_Up" in content),
            ("Fallback to parent", "super().keyPressEvent(event)" in content)
        ]

        all_good = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
            if not check_result:
                all_good = False

        return all_good

    except Exception as e:
        print(f"❌ Error verifying logic: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Fix keyPressEvent Logic Issues")
    print("=" * 55)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Replace with corrected method
    if not replace_keypress_method():
        print("❌ Failed to replace keyPressEvent method")
        return 1

    # Verify the corrected logic
    print("\n🔍 Verifying corrected logic...")
    if verify_corrected_logic():
        print("\n🎉 keyPressEvent logic fixed successfully!")
        print("\n🎯 Corrected behavior:")
        print("  1️⃣ Field selected + Arrow keys = Move field (priority)")
        print("  2️⃣ Ctrl + +/-/0 = Zoom (works always)")
        print("  3️⃣ Page Up/Down, Home/End = Navigate (works always)")
        print("  4️⃣ No field + Arrow keys = Scroll view")
        print("  5️⃣ Other keys = Pass to parent")
        print("\n✨ Logic improvements:")
        print("  • No conflicting arrow key behavior")
        print("  • Clean priority system with early returns")
        print("  • No redundant checks")
        print("  • Proper event handling")
        print("\n🚀 Test the application:")
        print("  python launch.py")
        return 0
    else:
        print("\n⚠️ Logic replacement completed but verification found issues")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())