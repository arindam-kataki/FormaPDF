#!/usr/bin/env python3
"""
Simple Working PDF Generator - Guaranteed to work with any ReportLab version
"""


def create_simple_pdf():
    """Create a simple multi-page PDF with different sizes"""

    try:
        # Import only what we absolutely need
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        print("✅ Basic ReportLab imports successful")
    except ImportError as e:
        print(f"❌ Cannot import ReportLab: {e}")
        return False

    # Define page sizes manually (width, height in points)
    page_sizes = [
        ("A4 Portrait", 595, 842),
        ("A4 Landscape", 842, 595),
        ("US Letter", 612, 792),
        ("US Letter Landscape", 792, 612),
        ("US Legal", 612, 1008),
        ("A3", 842, 1191),
        ("A5", 420, 595),
        ("A6", 298, 420),
        ("Tabloid", 792, 1224),
        ("B4", 709, 1001),
        ("B5", 499, 709),
        ("Business Card", 252, 144),
        ("Postcard 4x6", 288, 432),
        ("Photo 5x7", 360, 504),
        ("Square 6x6", 432, 432),
        ("Banner 3x11", 216, 792),
        ("Custom Large", 648, 864),
        ("Envelope DL", 312, 624),
        ("Envelope C5", 459, 649),
        ("Extra Large", 720, 936)
    ]

    filename = "multi_page_sizes_sample.pdf"
    print(f"🚀 Creating PDF: {filename}")

    # Create PDF
    c = canvas.Canvas(filename)

    for i, (name, width, height) in enumerate(page_sizes, 1):
        print(f"  📝 Page {i}: {name} ({width}×{height} pts)")

        # Set page size
        c.setPageSize((width, height))

        # Calculate margins
        margin = min(width, height) * 0.1

        # Title
        title_size = min(20, width / 30)
        c.setFont("Helvetica-Bold", title_size)
        title = f"Page {i}: {name}"
        title_width = c.stringWidth(title, "Helvetica-Bold", title_size)
        c.drawString((width - title_width) / 2, height - margin - 30, title)

        # Dimensions
        c.setFont("Helvetica", min(12, width / 50))
        y_pos = height - margin - 70

        width_in = width / 72
        height_in = height / 72
        width_mm = width * 25.4 / 72
        height_mm = height * 25.4 / 72

        c.drawString(margin, y_pos, f"Dimensions: {width_in:.2f}\" × {height_in:.2f}\"")
        y_pos -= 20
        c.drawString(margin, y_pos, f"Millimeters: {width_mm:.0f}mm × {height_mm:.0f}mm")
        y_pos -= 20
        c.drawString(margin, y_pos, f"Points: {width:.0f} × {height:.0f} pts")
        y_pos -= 20
        c.drawString(margin, y_pos, f"Aspect Ratio: {(width_in / height_in):.3f}:1")
        y_pos -= 40

        # Content
        c.setFont("Helvetica-Bold", min(14, width / 40))
        c.drawString(margin, y_pos, "Sample Content:")
        y_pos -= 25

        c.setFont("Helvetica", min(10, width / 60))
        content_lines = [
            f"This is page {i} demonstrating the {name} format.",
            "This page size is useful for various applications:",
            "• Document layout testing",
            "• Print compatibility verification",
            "• PDF application development",
            "• Cross-platform compatibility",
            "",
            "The content should scale appropriately to fit",
            "the page dimensions while maintaining readability.",
            "",
            f"Page area: {(width_in * height_in):.1f} square inches"
        ]

        for line in content_lines:
            if y_pos > margin + 60:
                c.drawString(margin, y_pos, line)
                y_pos -= 15

        # Draw border
        try:
            c.setStrokeColor(colors.blue)
            c.setLineWidth(1)
            c.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0)
        except:
            # If colors don't work, just draw a simple border
            c.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0)

        # Footer
        c.setFont("Helvetica", min(8, width / 80))
        footer = f"Multi-Page PDF Test • Page {i} of {len(page_sizes)} • {name}"
        footer_width = c.stringWidth(footer, "Helvetica", min(8, width / 80))
        c.drawString((width - footer_width) / 2, margin / 2, footer)

        # Next page
        c.showPage()

    # Save
    c.save()
    print(f"✅ PDF created successfully: {filename}")
    print(f"📊 Total pages: {len(page_sizes)}")

    return True


if __name__ == "__main__":
    print("🔧 Simple PDF Generator")
    print("=" * 40)

    success = create_simple_pdf()

    if success:
        print("\n🎉 SUCCESS!")
        print("📄 Your multi-page PDF is ready for testing!")
        print("\n📋 Contains 20 different page sizes:")
        print("  • ISO formats (A3, A4, A5, A6)")
        print("  • US formats (Letter, Legal, Tabloid)")
        print("  • Business cards and postcards")
        print("  • Custom and specialty sizes")
        print("  • Both portrait and landscape orientations")
    else:
        print("\n❌ Failed to create PDF")
        print("Check that ReportLab is properly installed")