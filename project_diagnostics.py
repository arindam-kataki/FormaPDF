#!/usr/bin/env python3
"""
Project Diagnostic Script
Analyzes the current project state to determine which fixes are needed
"""

import os
import sys
from pathlib import Path
import re


def check_file_exists(filepath):
    """Check if a file exists and return status"""
    path = Path(filepath)
    return "✅" if path.exists() else "❌", path.exists()


def analyze_imports_in_file(filepath):
    """Analyze imports in a specific file"""
    if not Path(filepath).exists():
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []

        # Check for problematic relative imports
        problematic_imports = [
            'from field_renderer import',
            'from drag_handler import',
            'from properties_panel import',
        ]

        for bad_import in problematic_imports:
            if bad_import in content:
                issues.append(f"Found problematic import: {bad_import}")

        # Check for method calls that might fail
        risky_calls = [
            'clear_highlights()',
            'highlight_field_type(',
            'set_field_selected(',
        ]

        for risky_call in risky_calls:
            if risky_call in content and 'hasattr' not in content.split(risky_call)[0][-100:]:
                issues.append(f"Found unsafe method call: {risky_call}")

        return issues

    except Exception as e:
        return [f"Error reading file: {e}"]


def check_class_methods(filepath, class_name, required_methods):
    """Check if a class has required methods"""
    if not Path(filepath).exists():
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the class
        class_start = content.find(f'class {class_name}')
        if class_start == -1:
            return [f"Class {class_name} not found"]

        # Find the end of the class
        next_class = content.find('\nclass ', class_start + 1)
        if next_class == -1:
            class_content = content[class_start:]
        else:
            class_content = content[class_start:next_class]

        missing_methods = []
        for method in required_methods:
            if f'def {method}(' not in class_content:
                missing_methods.append(f"Missing method: {method}")

        return missing_methods

    except Exception as e:
        return [f"Error checking class methods: {e}"]


def check_properties_panel_typeerror():
    """Check if properties panel has the TypeError fix"""
    filepath = "src/ui/properties_panel.py"
    if not Path(filepath).exists():
        return ["File does not exist"]

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if the fix is present
        if 'isinstance(initial_value, list)' in content:
            return []  # Fix is present
        elif 'widget.setPlainText(initial_value)' in content:
            return ["TypeError fix needed - setPlainText called with potential list"]
        else:
            return ["Unable to determine if fix is needed"]

    except Exception as e:
        return [f"Error checking properties panel: {e}"]


def main():
    """Main diagnostic function"""
    print("🔍 PDF Voice Editor - Project Diagnostic")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        print("   Make sure you're running this from the project root directory.")
        return 1

    print("📁 Checking file structure...")

    # Check critical files
    critical_files = [
        "src/ui/main_window.py",
        "src/ui/pdf_canvas.py",
        "src/ui/field_palette.py",
        "src/ui/properties_panel.py",
        "src/ui/field_renderer.py",
        "src/ui/drag_handler.py",
        "src/models/field_model.py",
        "src/utils/geometry_utils.py",
        "src/utils/icon_utils.py",
    ]

    missing_files = []
    for file in critical_files:
        status, exists = check_file_exists(file)
        print(f"  {status} {file}")
        if not exists:
            missing_files.append(file)

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} critical files!")
        print("   The project structure is incomplete.")
        return 1

    print("\n🔧 Analyzing import issues...")

    # Check import issues in key files
    files_to_check = {
        "src/ui/pdf_canvas.py": "PDF Canvas imports",
        "src/ui/main_window.py": "Main Window imports",
        "src/ui/drag_handler.py": "Drag Handler imports",
    }

    import_issues_found = False
    for filepath, description in files_to_check.items():
        print(f"\n📦 {description}:")
        issues = analyze_imports_in_file(filepath)
        if issues:
            for issue in issues:
                print(f"  ❌ {issue}")
            import_issues_found = True
        else:
            print(f"  ✅ No import issues found")

    print("\n🏗️ Checking class methods...")

    # Check if required methods exist
    method_checks = [
        ("src/ui/field_palette.py", "FieldPalette", ["clear_highlights", "highlight_field_type"]),
        ("src/ui/field_palette.py", "EnhancedFieldPalette", ["clear_highlights", "highlight_field_type"]),
    ]

    method_issues_found = False
    for filepath, class_name, methods in method_checks:
        print(f"\n🎯 {class_name} methods:")
        issues = check_class_methods(filepath, class_name, methods)
        if issues:
            for issue in issues:
                print(f"  ❌ {issue}")
            method_issues_found = True
        else:
            print(f"  ✅ All required methods found")

    print("\n🐛 Checking for specific bugs...")

    # Check properties panel TypeError
    print(f"\n🔧 Properties Panel TypeError:")
    typeerror_issues = check_properties_panel_typeerror()
    typeerror_issues_found = bool(typeerror_issues)
    if typeerror_issues:
        for issue in typeerror_issues:
            print(f"  ❌ {issue}")
    else:
        print(f"  ✅ No TypeError issues found")

    print("\n" + "=" * 50)
    print("📋 DIAGNOSTIC SUMMARY:")

    # Determine which scripts need to be run
    scripts_needed = []

    if import_issues_found:
        scripts_needed.append("fix_all_import_errors.py")

    if method_issues_found:
        scripts_needed.append("fix_main_window_safe_calls.py")
        scripts_needed.append("fix_field_palette_missing_methods.py")

    if typeerror_issues_found:
        if "fix_all_import_errors.py" not in scripts_needed:
            scripts_needed.append("fix_all_import_errors.py")

    if not scripts_needed:
        print("🎉 No fixes needed! Project appears to be in good shape.")
        print("\n🚀 Try running: python launch.py")
        return 0
    else:
        print(f"⚠️ {len(scripts_needed)} fix script(s) need to be run:")
        for i, script in enumerate(scripts_needed, 1):
            print(f"  {i}. python {script}")

        print(f"\n🎯 Run them in order, then try: python launch.py")
        return len(scripts_needed)


if __name__ == "__main__":
    sys.exit(main())