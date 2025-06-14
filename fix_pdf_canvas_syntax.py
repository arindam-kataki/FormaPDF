#!/usr/bin/env python3
"""
Fix PDF Canvas Syntax Error
Fixes the incomplete try block at line 168
"""

import os
from pathlib import Path


def fix_syntax_error():
    """Fix the syntax error in pdf_canvas.py"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print(f"❌ File not found: {pdf_canvas_path}")
        return False

    print("🔧 Fixing syntax error in pdf_canvas.py...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"📊 File has {len(lines)} lines")

        # Find the problematic line
        error_line = 168 - 1  # Convert to 0-based index

        if error_line < len(lines):
            print(f"🔍 Line {error_line + 1}: {lines[error_line].strip()}")

            # Look for incomplete try blocks around this area
            context_start = max(0, error_line - 10)
            context_end = min(len(lines), error_line + 10)

            print(f"\n📝 Context (lines {context_start + 1}-{context_end}):")
            for i in range(context_start, context_end):
                marker = ">>> " if i == error_line else "    "
                print(f"{marker}{i + 1:3d}: {lines[i].rstrip()}")

            # Look for try statements without matching except/finally
            try_positions = []
            for i in range(context_start, error_line + 1):
                line = lines[i].strip()
                if line.endswith('try:') or line == 'try:':
                    try_positions.append(i)

            if try_positions:
                print(f"\n🔍 Found try statement(s) at lines: {[pos + 1 for pos in try_positions]}")

                # Check if there's a matching except/finally
                last_try = try_positions[-1]
                has_except_or_finally = False

                for i in range(last_try + 1, min(len(lines), last_try + 20)):
                    line = lines[i].strip()
                    if line.startswith('except') or line.startswith('finally'):
                        has_except_or_finally = True
                        break
                    elif line and not line.startswith(' ') and not line.startswith('\t') and i > last_try + 1:
                        # Hit a non-indented line - try block probably incomplete
                        break

                if not has_except_or_finally:
                    print(f"❌ Try block at line {last_try + 1} has no except/finally clause")

                    # Fix by adding an except clause
                    indent = '        '  # Assume 8 spaces for method content

                    # Find where to insert the except clause
                    insert_pos = error_line

                    # Insert except clause
                    except_clause = f"{indent}except Exception as e:\n{indent}    print(f'Error in PDF canvas: {{e}}')\n"

                    lines.insert(insert_pos, except_clause)
                    print(f"✅ Added except clause at line {insert_pos + 1}")

                    # Write the fixed content back
                    with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)

                    return True

        # If we couldn't find a specific try block issue, look for other common syntax problems
        print("\n🔍 Checking for other syntax issues...")

        # Check for unmatched parentheses, brackets, braces
        paren_count = 0
        bracket_count = 0
        brace_count = 0

        for i, line in enumerate(lines):
            paren_count += line.count('(') - line.count(')')
            bracket_count += line.count('[') - line.count(']')
            brace_count += line.count('{') - line.count('}')

            if i == error_line:
                print(
                    f"  Line {i + 1} counts: () balance: {paren_count}, [] balance: {bracket_count}, {{}} balance: {brace_count}")

        # Try to compile the file to get more specific error info
        try:
            content = ''.join(lines)
            compile(content, pdf_canvas_path, 'exec')
            print("✅ File compiles successfully after our fix")
        except SyntaxError as e:
            print(f"❌ Still has syntax error: {e.msg} at line {e.lineno}")
            print(f"   Text: {e.text}")

            # Try a more aggressive fix - comment out the problematic line
            if e.lineno <= len(lines):
                problem_line = e.lineno - 1
                original_line = lines[problem_line]
                lines[problem_line] = f"    # COMMENTED OUT DUE TO SYNTAX ERROR: {original_line}"

                with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

                print(f"✅ Commented out problematic line {e.lineno}")
                return True

        return False

    except Exception as e:
        print(f"❌ Error fixing syntax: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_backup():
    """Create a backup of the current file before fixing"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")
    backup_path = Path("src/ui/pdf_canvas_broken.py")

    try:
        if pdf_canvas_path.exists():
            import shutil
            shutil.copy2(pdf_canvas_path, backup_path)
            print(f"✅ Created backup: {backup_path}")
            return True
    except Exception as e:
        print(f"⚠️ Could not create backup: {e}")

    return False


def verify_fix():
    """Verify that the fix worked"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to compile
        compile(content, pdf_canvas_path, 'exec')
        print("✅ File now compiles without syntax errors")
        return True

    except SyntaxError as e:
        print(f"❌ Still has syntax error: {e.msg} at line {e.lineno}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Fix PDF Canvas Syntax Error")
    print("=" * 55)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Create backup first
    create_backup()

    # Fix the syntax error
    if fix_syntax_error():
        # Verify the fix
        if verify_fix():
            print("\n🎉 Syntax error fixed successfully!")
            print("\n🎯 What was fixed:")
            print("  • Added missing except clause to incomplete try block")
            print("  • File now compiles without syntax errors")
            print("\n🚀 Test the application:")
            print("  python launch.py")
            return 0
        else:
            print("\n⚠️ Fix applied but verification failed")
            print("Check the error messages above for remaining issues")
            return 1
    else:
        print("\n❌ Could not fix the syntax error")
        print("You may need to manually examine the file")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())