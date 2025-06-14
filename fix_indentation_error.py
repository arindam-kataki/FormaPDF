#!/usr/bin/env python3
"""
Fix Indentation Error in main_window.py
Fixes the IndentationError at line 618
"""

import os
from pathlib import Path


def fix_indentation_error():
    """Fix the indentation error in main_window.py"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Fixing indentation error in main_window.py...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the problematic area around line 618
        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Look for the problematic pattern
            if ('if hasattr(self.field_palette,' in line or
                    'if hasattr(self.field_palette,' in line.strip()):

                # This is an if statement that needs proper indentation
                fixed_lines.append(line)
                i += 1

                # Check if the next line is properly indented
                if i < len(lines):
                    next_line = lines[i]

                    # If the next line doesn't start with whitespace, it needs indentation
                    if (next_line.strip() and
                            not next_line.startswith('    ') and
                            not next_line.startswith('\t')):
                        # Add proper indentation (4 spaces)
                        indented_line = '            ' + next_line.strip() + '\n'
                        fixed_lines.append(indented_line)
                        print(f"  ✅ Fixed indentation at line {i + 1}: {next_line.strip()}")
                        i += 1
                        continue

            fixed_lines.append(line)
            i += 1

        # Also fix any lines that have unsafe method calls by making them properly indented
        final_lines = []
        for i, line in enumerate(fixed_lines):
            # Check for lines that might be continuation of if statements
            if (line.strip().startswith('self.field_palette.') and
                    i > 0 and
                    'if hasattr' in fixed_lines[i - 1]):

                # Ensure proper indentation
                if not line.startswith('        '):
                    # Add proper indentation for the method call inside the if block
                    indented_line = '            ' + line.strip() + '\n'
                    final_lines.append(indented_line)
                    print(f"  ✅ Fixed method call indentation at line {i + 1}: {line.strip()}")
                else:
                    final_lines.append(line)
            else:
                final_lines.append(line)

        # Write the fixed content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)

        print("✅ Indentation error fixed in main_window.py")
        return True

    except Exception as e:
        print(f"❌ Error fixing main_window.py: {e}")
        import traceback
        traceback.print_exc()
        return False


def fix_all_method_calls_safely():
    """Fix all unsafe method calls in main_window.py by making them safe"""

    main_window_path = Path("src/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ File not found: {main_window_path}")
        return False

    print("🔧 Making all field_palette method calls safe...")

    try:
        # Read the current content
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # List of method calls to make safe
        unsafe_patterns = [
            (
                r'(\s*)self\.field_palette\.clear_highlights\(\)',
                r'\1if hasattr(self.field_palette, "clear_highlights"):\n\1    self.field_palette.clear_highlights()'
            ),
            (
                r'(\s*)self\.field_palette\.highlight_field_type\(([^)]+)\)',
                r'\1if hasattr(self.field_palette, "highlight_field_type"):\n\1    self.field_palette.highlight_field_type(\2)'
            ),
            (
                r'(\s*)self\.field_palette\.set_field_selected\(([^)]+)\)',
                r'\1if hasattr(self.field_palette, "set_field_selected"):\n\1    self.field_palette.set_field_selected(\2)'
            ),
        ]

        # Apply regex replacements
        import re
        changes_made = 0

        for pattern, replacement in unsafe_patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                changes_made += len(matches)
                print(f"  ✅ Made {len(matches)} method calls safe")

        # Write the updated content back to file
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Made {changes_made} method calls safe in main_window.py")
        return True

    except Exception as e:
        print(f"❌ Error making method calls safe: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Indentation Error Fixer")
    print("=" * 55)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        print("   Make sure you're running this from the project root directory.")
        return 1

    # Fix the indentation error
    print("Step 1: Fixing indentation error...")
    if not fix_indentation_error():
        print("❌ Failed to fix indentation error")
        return 1

    # Make method calls safe
    print("\nStep 2: Making method calls safe...")
    if not fix_all_method_calls_safely():
        print("❌ Failed to make method calls safe")
        return 1

    print("\n🎉 All fixes applied successfully!")
    print("\n🎯 Next steps:")
    print("1. Try running: python launch.py")
    print("2. If you get missing method errors, run: python fix_field_palette_missing_methods.py")
    print("3. If you get other import errors, run: python fix_all_import_errors.py")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())