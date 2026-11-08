import io
import fitz
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

PROJECT_ROOT = Path(r"c:\Users\Kabaou\Downloads\translator")
SRC_PDF = Path(r"C:\Users\Kabaou\Downloads\Nouveau dossier (7)\13244_2019_Article_719.pdf")
DEST_DIR = Path(r"C:\Users\Kabaou\Downloads\Nouveau dossier (7)")
TXT_PATH = DEST_DIR / "13244_2019_Article_719_fr.txt"

print("=== Building Word DOCX with Embedded High-Res Medical Figures ===")

doc_pdf = fitz.open(SRC_PDF)
doc_word = Document()

# Page setup: Normal margins
for section in doc_word.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Extract images by page
page_images = {}
for p_idx, page in enumerate(doc_pdf):
    imgs = page.get_images()
    png_list = []
    for img_info in imgs:
        xref = img_info[0]
        try:
            pix = fitz.Pixmap(doc_pdf, xref)
            if pix.n >= 5:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            # Skip tiny publisher icons (less than 100px width/height)
            if pix.width < 120 or pix.height < 120:
                continue
            png_bytes = pix.tobytes("png")
            png_list.append(png_bytes)
        except Exception as e:
            pass
    if png_list:
        page_images[p_idx + 1] = png_list

print(f"Extracted high-res images across {len(page_images)} pages")

# Read polished text
with open(TXT_PATH, "r", encoding="utf-8") as f:
    text = f.read()

chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
title = "Imagerie des nerfs crâniens : un aperçu pictural"

# Track which figure images have been placed
fig_regex = re.compile(r"Fig\.\s*(\d+)", re.IGNORECASE)
placed_figures = set()

# Mapping of figure numbers to pages
fig_to_page = {
    1: 2, 2: 4, 3: 5, 4: 6, 5: 6, 6: 7, 7: 8, 8: 8,
    9: 9, 10: 9, 11: 11, 12: 11, 13: 11, 14: 12, 15: 12,
    16: 13, 17: 13, 18: 14, 19: 14, 20: 15, 21: 16
}

for c in chunks:
    if c.startswith("# "):
        # Title
        p = doc_word.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(c[2:].strip())
        r.font.name = 'Arial'
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = RGBColor(17, 24, 39)
    elif c.startswith("## "):
        # Heading 1
        h = doc_word.add_heading(c[3:].strip(), level=1)
        h.style.font.name = 'Arial'
        h.style.font.color.rgb = RGBColor(30, 58, 138)
    elif c.startswith("### "):
        # Heading 2
        h = doc_word.add_heading(c[4:].strip(), level=2)
        h.style.font.name = 'Arial'
        h.style.font.color.rgb = RGBColor(31, 41, 55)
    elif c.startswith("*Légende :") and c.endswith("*"):
        caption_text = c[10:-1].strip()
        
        # Check if this caption has an associated figure image
        match = fig_regex.search(caption_text)
        if match:
            fig_num = int(match.group(1))
            if fig_num in fig_to_page and fig_num not in placed_figures:
                pg = fig_to_page[fig_num]
                if pg in page_images and len(page_images[pg]) > 0:
                    img_bytes = page_images[pg].pop(0)
                    # Insert the medical image
                    pic_p = doc_word.add_paragraph()
                    pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    doc_word.add_picture(io.BytesIO(img_bytes), width=Inches(5.5))
                    placed_figures.add(fig_num)
        
        # Insert caption text
        p = doc_word.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(caption_text)
        r.italic = True
        r.font.name = 'Arial'
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(75, 85, 99)
    elif c.startswith("- ") and re.match(r"^- \d+\.\s+[A-Z]", c):
        # Reference
        p = doc_word.add_paragraph(c[2:].strip())
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.style.font.size = Pt(9)
        p.style.font.color.rgb = RGBColor(55, 65, 81)
    else:
        # Standard paragraph
        p = doc_word.add_paragraph(c)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.style.font.name = 'Times New Roman'
        p.style.font.size = Pt(10.5)

docx_path = DEST_DIR / "13244_2019_Article_719_fr.docx"
try:
    doc_word.save(str(docx_path))
    print(f"Saved enhanced Word DOCX with {len(placed_figures)} embedded figures to: {docx_path} ({docx_path.stat().st_size / 1024 / 1024:.2f} MB)")
except Exception as e:
    # If locked, save to alternative name
    alt_path = DEST_DIR / "13244_2019_Article_719_FR_figures.docx"
    doc_word.save(str(alt_path))
    print(f"Saved to {alt_path} ({alt_path.stat().st_size / 1024 / 1024:.2f} MB)")

print("=== Finished Embedding Figures in DOCX ===")
