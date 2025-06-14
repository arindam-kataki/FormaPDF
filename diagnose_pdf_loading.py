#!/usr/bin/env python3
"""
Diagnose PDF Loading Issues
Checks why PDFs aren't loading and adds debugging
"""

import os
from pathlib import Path


def add_pdf_loading_debug():
    """Add debugging to PDF loading process"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")
    main_window_path = Path("src/ui/main_window.py")

    print("🔧 Adding PDF loading diagnostics...")

    # Add debug to main window open_pdf method
    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            main_content = f.read()

        # Check if open_pdf method exists and add debugging
        if 'def open_pdf(self):' in main_content:
            # Find the method and add debug output
            debug_code = '''
        print(f"🔍 Opening PDF file: {file_path}")
        print(f"📁 File exists: {Path(file_path).exists()}")
        print(f"📏 File size: {Path(file_path).stat().st_size if Path(file_path).exists() else 'N/A'} bytes")'''

            # Insert debug after file_path is defined
            if 'if file_path:' in main_content:
                insertion_point = main_content.find('if file_path:')
                line_end = main_content.find('\n', insertion_point)

                # Check if debug already added
                if '🔍 Opening PDF file:' not in main_content:
                    main_content = main_content[:line_end] + debug_code + main_content[line_end:]
                    print("  ✅ Added debug to main window open_pdf method")

        # Add debug to PDF canvas load call
        canvas_debug = '''
            print(f"📋 Calling pdf_canvas.load_pdf({file_path})")
            result = self.pdf_canvas.load_pdf(file_path)
            print(f"📋 load_pdf returned: {result}")
            if not result:
                print("❌ PDF loading failed")
                self.statusBar().showMessage("Failed to load PDF", 3000)
            else:
                print("✅ PDF loading succeeded")'''

        # Replace simple load_pdf call with debug version
        if 'self.pdf_canvas.load_pdf(file_path)' in main_content and '📋 Calling pdf_canvas.load_pdf' not in main_content:
            main_content = main_content.replace(
                'if self.pdf_canvas.load_pdf(file_path):',
                canvas_debug + '\n            if result:'
            )
            print("  ✅ Added debug to PDF canvas load call")

        # Write back to main window
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(main_content)

    except Exception as e:
        print(f"⚠️ Could not add main window debug: {e}")

    # Add debug to PDF canvas load_pdf method
    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            canvas_content = f.read()

        if 'def load_pdf(self, pdf_path:' in canvas_content:
            # Add comprehensive debugging to load_pdf method
            load_debug = '''
        print(f"🔧 PDFCanvas.load_pdf called with: {pdf_path}")

        # Check if fitz is available
        try:
            import fitz
            print("✅ PyMuPDF (fitz) is available")
        except ImportError as e:
            print(f"❌ PyMuPDF (fitz) import failed: {e}")
            return False'''

            # Insert debug at start of load_pdf method
            load_start = canvas_content.find('def load_pdf(self, pdf_path:')
            if load_start != -1:
                # Find the start of the method body (after the docstring if present)
                method_lines = canvas_content[load_start:].split('\n')
                insert_line = 1  # After method signature

                # Skip docstring if present
                if len(method_lines) > 1 and '"""' in method_lines[1]:
                    # Find end of docstring
                    for i in range(2, len(method_lines)):
                        if '"""' in method_lines[i]:
                            insert_line = i + 1
                            break

                # Check if debug already added
                if '🔧 PDFCanvas.load_pdf called' not in canvas_content:
                    # Insert the debug code
                    method_lines.insert(insert_line, load_debug)

                    # Reconstruct the content
                    new_method = '\n'.join(method_lines[:50])  # Take first 50 lines to avoid issues
                    canvas_content = canvas_content.replace(
                        '\n'.join(method_lines[:50]),
                        new_method
                    )
                    print("  ✅ Added debug to PDF canvas load_pdf method")

        # Add debug to render_page method
        render_debug = '''
        print(f"🎨 Rendering page {self.current_page + 1}")'''

        if 'def render_page(self):' in canvas_content and '🎨 Rendering page' not in canvas_content:
            render_start = canvas_content.find('def render_page(self):')
            if render_start != -1:
                # Find first line of method body
                lines = canvas_content[render_start:].split('\n')
                if len(lines) > 2:
                    # Insert after method signature and docstring
                    insert_pos = render_start + len(lines[0]) + len(lines[1]) + 2
                    canvas_content = canvas_content[:insert_pos] + render_debug + canvas_content[insert_pos:]
                    print("  ✅ Added debug to render_page method")

        # Write back to PDF canvas
        with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
            f.write(canvas_content)

    except Exception as e:
        print(f"⚠️ Could not add PDF canvas debug: {e}")


def check_dependencies():
    """Check if required dependencies are available"""

    print("🔍 Checking dependencies...")

    dependencies = [
        ('PyMuPDF (fitz)', 'fitz'),
        ('PyQt6.QtWidgets', 'PyQt6.QtWidgets'),
        ('PyQt6.QtGui', 'PyQt6.QtGui'),
        ('PyQt6.QtCore', 'PyQt6.QtCore'),
    ]

    for name, module in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")


def analyze_pdf_canvas_structure():
    """Analyze the structure of PDFCanvas to find potential issues"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    if not pdf_canvas_path.exists():
        print("❌ pdf_canvas.py not found")
        return

    print("🔍 Analyzing PDFCanvas structure...")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for key methods
        key_methods = [
            'def __init__(self',
            'def load_pdf(self',
            'def render_page(self',
            'def set_page(self',
            'def set_zoom(self',
        ]

        for method in key_methods:
            if method in content:
                print(f"  ✅ {method.replace('def ', '').replace('(self', '')} method exists")
            else:
                print(f"  ❌ {method.replace('def ', '').replace('(self', '')} method missing")

        # Check for fitz imports
        if 'import fitz' in content:
            print("  ✅ fitz import found")
        else:
            print("  ❌ fitz import missing")

        # Check for QPixmap usage
        if 'QPixmap' in content:
            print("  ✅ QPixmap usage found")
        else:
            print("  ❌ QPixmap usage missing")

    except Exception as e:
        print(f"❌ Error analyzing PDFCanvas: {e}")


def create_minimal_working_load_pdf():
    """Create a minimal working load_pdf method if the current one is broken"""

    pdf_canvas_path = Path("src/ui/pdf_canvas.py")

    try:
        with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if load_pdf method needs to be replaced
        if 'def load_pdf(self, pdf_path:' not in content:
            print("🔧 Adding minimal load_pdf method...")

            minimal_load_pdf = '''
    def load_pdf(self, pdf_path: str) -> bool:
        """Load PDF document - minimal working version"""
        print(f"🔧 Loading PDF: {pdf_path}")

        try:
            import fitz
            print("✅ fitz imported successfully")

            # Open the PDF
            self.pdf_document = fitz.open(pdf_path)
            print(f"✅ PDF opened: {self.pdf_document.page_count} pages")

            # Reset to first page
            self.current_page = 0
            self.zoom_level = 1.0

            # Render the first page
            self.render_page()
            print("✅ First page rendered")

            # Update styling
            self.setStyleSheet("border: 1px solid #ccc; background-color: white;")

            return True

        except Exception as e:
            print(f"❌ Error loading PDF: {e}")
            import traceback
            traceback.print_exc()
            return False'''

            # Find where to insert the method
            class_pos = content.find('class PDFCanvas')
            if class_pos != -1:
                # Find a good insertion point
                first_method = content.find('    def ', class_pos)
                if first_method != -1:
                    content = content[:first_method] + minimal_load_pdf + '\n' + content[first_method:]

                    with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    print("✅ Added minimal load_pdf method")
                    return True

        print("✅ load_pdf method already exists")
        return True

    except Exception as e:
        print(f"❌ Error creating minimal load_pdf: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PDF Voice Editor - Diagnose PDF Loading Issues")
    print("=" * 55)

    # Check if we're in the right directory
    if not Path("src").exists():
        print("❌ Error: 'src' directory not found.")
        return 1

    # Check dependencies
    check_dependencies()
    print()

    # Analyze PDF canvas structure
    analyze_pdf_canvas_structure()
    print()

    # Add debugging to PDF loading
    add_pdf_loading_debug()
    print()

    # Ensure minimal load_pdf method exists
    create_minimal_working_load_pdf()

    print("🎉 PDF loading diagnostics added!")
    print("\n🎯 Now test the application:")
    print("1. Run: python launch.py")
    print("2. Click 📁 Open and select a PDF")
    print("3. Watch the console for debug messages")
    print("\n📋 Debug messages to look for:")
    print("  🔍 Opening PDF file: [path]")
    print("  📁 File exists: True")
    print("  📏 File size: [bytes] bytes")
    print("  🔧 PDFCanvas.load_pdf called with: [path]")
    print("  ✅ PyMuPDF (fitz) is available")
    print("  ✅ PDF opened: [X] pages")
    print("  🎨 Rendering page 1")
    print("\n🚨 If you see errors, they'll help identify the problem!")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())