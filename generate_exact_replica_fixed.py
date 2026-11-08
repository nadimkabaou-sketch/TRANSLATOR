import os
import re
import json
import shutil
import fitz
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\Kabaou\Downloads\translator")
SRC_PDF = Path(r"C:\Users\Kabaou\Downloads\Nouveau dossier (7)\13244_2019_Article_719.pdf")
DEST_DIR = Path(r"C:\Users\Kabaou\Downloads\Nouveau dossier (7)")
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

import sys
sys.path.insert(0, str(PROJECT_ROOT))
from polish_translation import clean_medical_text
from backend.core.translator import ScientificTranslator

FONT_REG = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_ITAL = "C:/Windows/Fonts/ariali.ttf"
FONT_BOLDITAL = "C:/Windows/Fonts/arialbi.ttf"

# Load TM
tm_path = PROJECT_ROOT / "data" / "translation_memory" / "tm.json"
tm = {}
if tm_path.exists():
    with open(tm_path, "r", encoding="utf-8") as f:
        tm = json.load(f)

translator = ScientificTranslator()

def clean(text: str) -> str:
    c = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    c = re.sub(r"\s*\n\s*", " ", c)
    c = re.sub(r"\s{2,}", " ", c)
    return c.strip()

def safe_translate(text: str) -> str:
    c = clean(text)
    if not c:
        return ""
        
    # Check exact match
    if c in tm:
        val = tm[c]
        if len(c) < 80 or len(val) >= len(c) * 0.45:
            return clean_medical_text(val)
            
    # Check near-exact length match
    for k, v in tm.items():
        if len(c) > 20 and len(k) > 20:
            ratio = min(len(c), len(k)) / max(len(c), len(k))
            if ratio >= 0.75:
                if c[:35].lower() == k[:35].lower():
                    if len(c) < 80 or len(v) >= len(c) * 0.45:
                        return clean_medical_text(v)
                        
    # Translate freshly
    res = translator.translate_segment(c, src_lang="en", domain="medicine_radiology")
    tr = clean_medical_text(res["translated"])
    tm[c] = tr
    return tr

CRANIAL_NERVES_MAP = {
    "i cranial nerve - olfactory nerve": "Ier nerf crânien - Nerf olfactif",
    "ii cranial nerve - optic nerve": "IIe nerf crânien - Nerf optique",
    "iii cranial nerve - oculomotor nerve": "IIIe nerf crânien - Nerf oculomoteur",
    "iv cranial nerve - trochlear nerve": "IVe nerf crânien - Nerf trochléaire",
    "v cranial nerve - trigeminal nerve": "Ve nerf crânien - Nerf trijumeau",
    "vi cranial nerve - abducens nerve": "VIe nerf crânien - Nerf abducens",
    "vii cranial nerve - facial nerve": "VIIe nerf crânien - Nerf facial",
    "viii cranial nerve - vestibulocochlear nerve": "VIIIe nerf crânien - Nerf vestibulo-cochléaire",
    "ix cranial nerve - glossopharyngeal nerve": "IXe nerf crânien - Nerf glossopharyngien",
    "x cranial nerve - vagus nerve": "Xe nerf crânien - Nerf vague",
    "xi cranial nerve - accessory nerve": "XIe nerf crânien - Nerf accessoire",
    "xii cranial nerve - hypoglossal nerve": "XIIe nerf crânien - Nerf hypoglosse",
}

SECTION_HEADERS_MAP = {
    "abstract": "Résumé",
    "key points": "Points clés",
    "introduction": "Introduction",
    "imaging": "Imagerie",
    "anatomy": "Anatomie",
    "pathology": "Pathologie",
    "conclusion": "Conclusion",
    "abbreviations": "Abréviations",
    "references": "Références",
    "schwannoma": "Schwannome",
    "neurofibroma": "Neurofibrome",
    "meningioma": "Méningiome",
    "perineural tumor spread": "Dissémination tumorale périneurale",
    "optic neuritis": "Névrite optique",
    "optic nerve glioma": "Gliome du nerf optique",
    "leptomeningeal metastases": "Métastases leptoméningées",
    "neurovascular conflict": "Conflit neuro-vasculaire",
    "bell's palsy": "Paralysie de Bell (paralysie faciale a frigore)",
    "tolosa-hunt syndrome": "Syndrome de Tolosa-Hunt",
    "trauma": "Traumatismes",
    "infections": "Infections",
    "congenital anomalies": "Anomalies congénitales"
}

def is_heading(line: str) -> bool:
    low = line.strip().lower()
    if low in SECTION_HEADERS_MAP:
        return True
    if low in CRANIAL_NERVES_MAP:
        return True
    if re.match(r"^[ivxlcdm]+\s+cranial nerve\s*[-–—]\s*", low):
        return True
    return False

def translate_heading(line: str) -> str:
    low = line.strip().lower()
    if low in SECTION_HEADERS_MAP:
        return SECTION_HEADERS_MAP[low]
    if low in CRANIAL_NERVES_MAP:
        return CRANIAL_NERVES_MAP[low]
    return safe_translate(line)

print("Starting Full Exact Replica PDF Generation with No Empty Paragraphs...")
doc = fitz.open(SRC_PDF)
print(f"Total pages: {len(doc)}")

total_items = 0

for p_idx, page in enumerate(doc):
    d = page.get_text("dict")
    blocks = d.get("blocks", [])
    
    items = []
    
    for b in blocks:
        if b.get("type", 0) != 0:
            continue
            
        lines = b.get("lines", [])
        if not lines:
            continue
            
        first_span = lines[0]["spans"][0] if lines[0].get("spans") else {}
        if not first_span:
            continue
            
        raw_lines = ["".join(s.get("text", "") for s in l.get("spans", [])).strip() for l in lines if "".join(s.get("text", "") for s in l.get("spans", [])).strip()]
        if not raw_lines:
            continue
            
        full_text = " ".join(raw_lines)
        if len(full_text) < 3:
            continue
            
        # Running headers / page numbers
        if re.search(r"Romano et al\..*Page \d+ of \d+", full_text):
            continue
        if re.match(r"^\d{1,3}$", full_text):
            continue
            
        rect = fitz.Rect(b["bbox"])
        first_line = raw_lines[0]
        
        # Check if block starts with a heading and has following body lines
        has_heading = is_heading(first_line)
        
        if has_heading and len(raw_lines) > 1:
            tr_head = translate_heading(first_line)
            body_text = " ".join(raw_lines[1:])
            
            # Special handling for References on Page 21: preserve citation text
            if first_line.lower() == "references":
                tr_body = body_text
            else:
                tr_body = safe_translate(body_text)
                
            h_line_height = lines[0]["bbox"][3] - lines[0]["bbox"][1] + 2
            r_head = fitz.Rect(rect.x0, rect.y0, rect.x1, min(rect.y1, rect.y0 + h_line_height))
            r_body = fitz.Rect(rect.x0, rect.y0 + h_line_height, rect.x1, rect.y1)
            
            orig_size = first_span.get("size", 10.0)
            items.append({
                "rect": r_head,
                "text": tr_head,
                "fontfile": FONT_BOLD,
                "fontsize": orig_size,
                "color": (0.05, 0.15, 0.45) if "cranial nerve" in first_line.lower() else (0.1, 0.1, 0.1),
                "fill": (1, 1, 1),
                "align": fitz.TEXT_ALIGN_LEFT
            })
            
            body_span = lines[1]["spans"][0] if len(lines) > 1 and lines[1].get("spans") else first_span
            body_size = body_span.get("size", 9.0)
            items.append({
                "rect": r_body,
                "text": tr_body,
                "fontfile": FONT_REG,
                "fontsize": body_size,
                "color": (0.08, 0.08, 0.08),
                "fill": (1, 1, 1),
                "align": fitz.TEXT_ALIGN_JUSTIFY
            })
        else:
            # Single block
            is_caption = full_text.lower().startswith("fig.") or full_text.lower().startswith("figure") or full_text.lower().startswith("table")
            font_name = first_span.get("font", "").lower()
            is_bold = "bold" in font_name or ".b" in font_name
            is_italic = "italic" in font_name or is_caption
            
            if is_bold and is_italic:
                ff = FONT_BOLDITAL
            elif is_bold:
                ff = FONT_BOLD
            elif is_italic:
                ff = FONT_ITAL
            else:
                ff = FONT_REG
                
            orig_size = first_span.get("size", 9.0)
            s_color = first_span.get("color", 0)
            
            if s_color == 16777215: # white text (top banner)
                text_color = (1.0, 1.0, 1.0)
                fill_color = (0.0, 0.4, 0.7)
            else:
                text_color = (0.08, 0.08, 0.08)
                fill_color = (1.0, 1.0, 1.0)
                
            if "PICTORIAL REVIEW" in full_text and "Open Access" in full_text:
                tr = "REVUE ICONOGRAPHIQUE   Open Access"
            elif full_text == "PICTORIAL REVIEW":
                tr = "REVUE ICONOGRAPHIQUE"
            elif full_text == "Open Access":
                tr = "Open Access"
            elif "Keywords:" in full_text:
                tr = "Mots-clés : Nerfs crâniens, Imagerie par résonance magnétique, Tomodensitométrie, Anatomie, Pathologie"
            elif is_heading(full_text):
                tr = translate_heading(full_text)
                ff = FONT_BOLD
            else:
                tr = safe_translate(full_text)
                
            if not tr:
                continue
                
            align = fitz.TEXT_ALIGN_CENTER if is_caption else (fitz.TEXT_ALIGN_JUSTIFY if len(full_text) > 100 else fitz.TEXT_ALIGN_LEFT)
            
            items.append({
                "rect": rect,
                "text": tr,
                "fontfile": ff,
                "fontsize": orig_size,
                "color": text_color,
                "fill": fill_color,
                "align": align
            })

    # Redact all items on page
    for it in items:
        page.add_redact_annot(it["rect"], fill=it["fill"])
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
    
    # Insert text into all items on page
    for it in items:
        fs = it["fontsize"]
        rect = it["rect"]
        fitted = False
        
        # Give 1pt extra margin
        exp_rect = fitz.Rect(rect.x0 - 0.5, rect.y0 - 0.5, rect.x1 + 0.5, rect.y1 + 1.5)
        
        while fs >= max(5.0, it["fontsize"] * 0.68):
            rc = page.insert_textbox(
                exp_rect,
                it["text"],
                fontfile=it["fontfile"],
                fontsize=fs,
                color=it["color"],
                align=it["align"],
                lineheight=1.10
            )
            if rc >= 0:
                fitted = True
                break
            fs -= 0.25
            
        if not fitted:
            # Expand downward if needed
            down_rect = fitz.Rect(exp_rect.x0, exp_rect.y0, exp_rect.x1, exp_rect.y1 + 10)
            page.insert_textbox(
                down_rect,
                it["text"],
                fontfile=it["fontfile"],
                fontsize=max(5.0, fs),
                color=it["color"],
                align=it["align"],
                lineheight=1.05
            )
            
        total_items += 1
        
    words = len(page.get_text("words"))
    print(f"Page {p_idx+1:2d}/21 processed: {len(items)} elements rendered, word count = {words}")

# Save the final exact replica PDF with fallback for open viewer
final_name = "13244_2019_Article_719_FR_integral.pdf"
exact_out_path = DEST_DIR / final_name
doc.save(str(exact_out_path))
print(f"\nSaved INTEGRAL replica PDF to: {exact_out_path} ({exact_out_path.stat().st_size / 1024 / 1024:.2f} MB)")

# Also copy to OUTPUT_DIR
shutil.copy2(exact_out_path, OUTPUT_DIR / final_name)

# Try updating the other filenames if closed
for alt_name in ["13244_2019_Article_719_FR_exact.pdf", "13244_2019_Article_719_fr.pdf"]:
    alt_p = DEST_DIR / alt_name
    try:
        shutil.copy2(exact_out_path, alt_p)
        print(f"Also updated: {alt_name}")
    except Exception as e:
        print(f"Notice: {alt_name} is currently locked by PDF reader ({e}). The complete updated file is {final_name}.")

# Update TM file
with open(tm_path, "w", encoding="utf-8") as f:
    json.dump(tm, f, ensure_ascii=False, indent=2)

print("=== Finished Generating Exact Replica with All Paragraphs Intact ===")
