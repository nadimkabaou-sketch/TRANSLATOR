import os
import re
import io
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
from polish_translation import clean_medical_text, CORRECTIONS
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

# Translator fallback for unmatched text
translator = ScientificTranslator()

def clean_text(text: str) -> str:
    c = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    c = re.sub(r"\s*\n\s*", " ", c)
    c = re.sub(r"\s{2,}", " ", c)
    return c.strip()

def get_font_and_style(first_span, is_caption=False, is_heading=False):
    font_name = first_span.get("font", "").lower()
    is_b = "bold" in font_name or ".b" in font_name or is_heading
    is_i = "italic" in font_name or "oblique" in font_name or ".i" in font_name or is_caption
    
    if is_b and is_i:
        return FONT_BOLDITAL
    elif is_b:
        return FONT_BOLD
    elif is_i:
        return FONT_ITAL
    else:
        return FONT_REG

def get_translation(text: str) -> str:
    c = clean_text(text)
    if not c:
        return ""
        
    # Check TM directly
    if c in tm:
        return clean_medical_text(tm[c])
        
    # Check TM partial match
    for k, v in tm.items():
        if len(c) > 25 and (c[:35] in k or k[:35] in c):
            return clean_medical_text(v)
            
    # Fallback to model translation
    res = translator.translate_segment(c, src_lang="en", domain="medicine_radiology")
    translated = clean_medical_text(res["translated"])
    tm[c] = translated
    return translated

def process_pdf():
    print(f"Opening original PDF: {SRC_PDF.name}")
    doc = fitz.open(SRC_PDF)
    print(f"Total pages: {len(doc)}")
    
    total_replaced = 0
    
    for page_idx, page in enumerate(doc):
        d = page.get_text("dict")
        blocks = d.get("blocks", [])
        
        items_to_replace = []
        
        for b in blocks:
            # 0 is text block, 1 is image
            if b.get("type", 0) != 0:
                continue
                
            lines = b.get("lines", [])
            if not lines:
                continue
                
            first_span = lines[0]["spans"][0] if lines[0].get("spans") else {}
            if not first_span:
                continue
                
            raw_text = " ".join("".join(s.get("text", "") for s in l.get("spans", [])).strip() for l in lines).strip()
            if not raw_text or len(raw_text) < 3:
                continue
                
            # Skip page running headers & page numbers to preserve authentic layout
            if re.search(r"Romano et al\..*Page \d+ of \d+", raw_text):
                continue
            if re.match(r"^\d{1,3}$", raw_text):
                continue
                
            # Check if caption or heading
            is_caption = raw_text.lower().startswith("fig.") or raw_text.lower().startswith("figure") or raw_text.lower().startswith("table")
            is_heading = len(raw_text) < 60 and ("nerve" in raw_text.lower() or "abstract" in raw_text.lower() or "points" in raw_text.lower() or "introduction" in raw_text.lower() or "anatomy" in raw_text.lower() or "pathology" in raw_text.lower() or "conclusion" in raw_text.lower() or "references" in raw_text.lower())
            
            # Special case for page 1 top banner
            if "PICTORIAL REVIEW" in raw_text and "Open Access" in raw_text:
                tr_text = "REVUE ICONOGRAPHIQUE   Open Access"
            elif "Keywords:" in raw_text:
                tr_text = "Mots-clés : Nerfs crâniens, Imagerie par résonance magnétique, Tomodensitométrie, Anatomie, Pathologie"
            elif "Key points" in raw_text:
                tr_text = "Points clés"
            elif "Abstract" == raw_text:
                tr_text = "Résumé"
            elif raw_text == "Imaging":
                tr_text = "Imagerie"
            elif raw_text == "Anatomy":
                tr_text = "Anatomie"
            elif raw_text == "Pathology":
                tr_text = "Pathologie"
            elif raw_text == "Conclusion":
                tr_text = "Conclusion"
            elif raw_text == "Abbreviations":
                tr_text = "Abréviations"
            elif raw_text == "References":
                tr_text = "Références"
            else:
                tr_text = get_translation(raw_text)
                
            if not tr_text:
                continue
                
            font_path = get_font_and_style(first_span, is_caption=is_caption, is_heading=is_heading)
            orig_size = first_span.get("size", 9.0)
            
            # Text color (black / dark gray)
            s_color = first_span.get("color", 0)
            if s_color == 16777215: # white
                text_color = (1.0, 1.0, 1.0)
                fill_color = (0.0, 0.4, 0.7) # blue bar for header
            else:
                text_color = (0.08, 0.08, 0.08)
                fill_color = (1.0, 1.0, 1.0) # clean white redaction
                
            rect = fitz.Rect(b["bbox"])
            items_to_replace.append({
                "rect": rect,
                "text": tr_text,
                "fontfile": font_path,
                "fontsize": orig_size,
                "color": text_color,
                "fill": fill_color,
                "align": fitz.TEXT_ALIGN_LEFT
            })
            
        # 1. Add redaction annotations for this page
        for it in items_to_replace:
            page.add_redact_annot(it["rect"], fill=it["fill"])
            
        # 2. Apply redactions while STRICTLY PRESERVING ALL 34 IMAGES
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        
        # 3. Insert translated French text
        for it in items_to_replace:
            fs = it["fontsize"]
            rect = it["rect"]
            fitted = False
            
            # Slightly expand rect width and height to give French text breathing room without touching images
            expanded_rect = fitz.Rect(rect.x0 - 1, rect.y0 - 0.5, rect.x1 + 1, rect.y1 + 1)
            
            while fs >= max(5.5, it["fontsize"] * 0.70):
                rc = page.insert_textbox(
                    expanded_rect,
                    it["text"],
                    fontfile=it["fontfile"],
                    fontsize=fs,
                    color=it["color"],
                    align=it["align"],
                    lineheight=1.12
                )
                if rc >= 0:
                    fitted = True
                    break
                fs -= 0.3
                
            if not fitted:
                # If tight, expand downward slightly
                down_rect = fitz.Rect(expanded_rect.x0, expanded_rect.y0, expanded_rect.x1, expanded_rect.y1 + 6)
                page.insert_textbox(
                    down_rect,
                    it["text"],
                    fontfile=it["fontfile"],
                    fontsize=max(5.5, fs),
                    color=it["color"],
                    align=it["align"],
                    lineheight=1.05
                )
                
            total_replaced += 1
            
        print(f"Page {page_idx+1:2d}/21 processed: {len(items_to_replace)} text blocks translated in-place (images preserved).")
        
    print(f"\nTotal blocks translated in-place across document: {total_replaced}")
    
    # Save output exact replica PDF
    exact_out_path = DEST_DIR / "13244_2019_Article_719_FR_exact.pdf"
    doc.save(str(exact_out_path))
    print(f"Saved exact replica PDF to: {exact_out_path} ({exact_out_path.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Also save to data/outputs
    out_local = OUTPUT_DIR / "13244_2019_Article_719_FR_exact.pdf"
    shutil.copy2(exact_out_path, out_local)
    
    # Try updating 13244_2019_Article_719_fr.pdf if not locked
    fr_default = DEST_DIR / "13244_2019_Article_719_fr.pdf"
    try:
        shutil.copy2(exact_out_path, fr_default)
        print(f"Also updated: {fr_default}")
    except Exception as e:
        print(f"Notice: {fr_default} is currently locked by a PDF viewer, accessible via {exact_out_path.name}")
        
    # Save updated TM
    with open(tm_path, "w", encoding="utf-8") as f:
        json.dump(tm, f, ensure_ascii=False, indent=2)
        
    print("=== In-Place PDF Exact Replica Generation Finished Successfully ===")

if __name__ == "__main__":
    process_pdf()
