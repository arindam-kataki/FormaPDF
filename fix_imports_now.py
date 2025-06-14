python - c
"
import os
from pathlib import Path

pdf_canvas_path = Path('src/ui/pdf_canvas.py')
if pdf_canvas_path.exists():
    with open(pdf_canvas_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('from field_renderer import FieldRenderer', 'from ui.field_renderer import FieldRenderer')
    content = content.replace('from drag_handler import DragHandler, SelectionHandler',
                              'from ui.drag_handler import DragHandler, SelectionHandler')

    with open(pdf_canvas_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print('✅ Fixed pdf_canvas.py imports')
else:
    print('❌ pdf_canvas.py not found')
"