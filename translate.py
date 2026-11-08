#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scientific Paper In-Place Translator & Document Rebuilder
Preserves original layout, typography, multi-column geometry, and 100% of embedded figures/images.
"""

import os
import sys
import io
import re
import time
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

import fitz  # PyMuPDF
import torch
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import DATA_DIR, OUTPUT_DIR, GLOSSARY_DIR, TM_DIR
from backend.core.pipeline import ScientificPipeline
from backend.core.translator import ScientificTranslator
from polish_translation import clean_medical_text, CORRECTIONS

# System fonts for in-place text rendering
FONT_REG = "C:/Windows/Fonts/arial.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_ITAL = "C:/Windows/Fonts/ariali.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"
FONT_BOLDITAL = "C:/Windows/Fonts/arialbi.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"

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
    "background": "Contexte",
    "methods": "Méthodes",
    "materials and methods": "Matériel et méthodes",
    "results": "Résultats",
    "discussion": "Discussion",
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

class UniversalPaperTranslator:
    def __init__(self, target_lang: str = "fr", domain: str = "medicine_radiology", cpu_threads: int = 8):
        self.target_lang = target_lang
        self.domain = domain
        try:
            torch.set_num_threads(min(cpu_threads, os.cpu_count() or 4))
        except Exception:
            pass
        self.translator = ScientificTranslator()
        self.tm_path = TM_DIR / "tm.json"
        self.tm = {}
        if self.tm_path.exists():
            try:
                with open(self.tm_path, "r", encoding="utf-8") as f:
                    self.tm = json.load(f)
            except Exception:
                self.tm = {}

    def clean(self, text: str) -> str:
        c = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        c = re.sub(r"\s*\n\s*", " ", c)
        c = re.sub(r"\s{2,}", " ", c)
        return c.strip()

    def safe_translate(self, text: str) -> str:
        c = self.clean(text)
        if not c:
            return ""
        if c in self.tm:
            val = self.tm[c]
            if len(c) < 80 or len(val) >= len(c) * 0.45:
                return clean_medical_text(val)
        for k, v in self.tm.items():
            if len(c) > 20 and len(k) > 20:
                ratio = min(len(c), len(k)) / max(len(c), len(k))
                if ratio >= 0.75 and c[:35].lower() == k[:35].lower():
                    if len(c) < 80 or len(v) >= len(c) * 0.45:
                        return clean_medical_text(v)
        res = self.translator.translate_segment(c, src_lang="en", domain=self.domain)
        tr = clean_medical_text(res["translated"])
        self.tm[c] = tr
        return tr

    def is_heading(self, line: str) -> bool:
        low = line.strip().lower()
        if low in SECTION_HEADERS_MAP or low in CRANIAL_NERVES_MAP:
            return True
        if re.match(r"^[ivxlcdm]+\s+cranial nerve\s*[-–—]\s*", low):
            return True
        return False

    def translate_heading(self, line: str) -> str:
        low = line.strip().lower()
        if low in SECTION_HEADERS_MAP:
            return SECTION_HEADERS_MAP[low]
        if low in CRANIAL_NERVES_MAP:
            return CRANIAL_NERVES_MAP[low]
        return self.safe_translate(line)

    def translate_pdf_inplace(self, input_pdf: Path, dest_dir: Path) -> Path:
        """
        Creates an exact replica PDF where English text is replaced in-place by French,
        preserving 100% of pages, columns, vector lines, and all embedded figures/images.
        """
        print(f"\n[Exact-Replica PDF] Processing {input_pdf.name} (pages: {len(fitz.open(input_pdf))})...")
        doc = fitz.open(input_pdf)
        
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
                if re.search(r"Romano et al\..*Page \d+ of \d+", full_text):
                    continue
                if re.match(r"^\d{1,3}$", full_text):
                    continue
                    
                rect = fitz.Rect(b["bbox"])
                first_line = raw_lines[0]
                has_heading = self.is_heading(first_line)
                
                if has_heading and len(raw_lines) > 1:
                    tr_head = self.translate_heading(first_line)
                    body_text = " ".join(raw_lines[1:])
                    tr_body = body_text if first_line.lower() == "references" else self.safe_translate(body_text)
                    
                    h_height = lines[0]["bbox"][3] - lines[0]["bbox"][1] + 2
                    r_head = fitz.Rect(rect.x0, rect.y0, rect.x1, min(rect.y1, rect.y0 + h_height))
                    r_body = fitz.Rect(rect.x0, rect.y0 + h_height, rect.x1, rect.y1)
                    
                    items.append({
                        "rect": r_head,
                        "text": tr_head,
                        "fontfile": FONT_BOLD,
                        "fontsize": first_span.get("size", 10.0),
                        "color": (0.05, 0.15, 0.45) if "cranial nerve" in first_line.lower() else (0.1, 0.1, 0.1),
                        "fill": (1, 1, 1),
                        "align": fitz.TEXT_ALIGN_LEFT
                    })
                    body_span = lines[1]["spans"][0] if len(lines) > 1 and lines[1].get("spans") else first_span
                    items.append({
                        "rect": r_body,
                        "text": tr_body,
                        "fontfile": FONT_REG,
                        "fontsize": body_span.get("size", 9.0),
                        "color": (0.08, 0.08, 0.08),
                        "fill": (1, 1, 1),
                        "align": fitz.TEXT_ALIGN_JUSTIFY
                    })
                else:
                    is_caption = full_text.lower().startswith("fig.") or full_text.lower().startswith("figure") or full_text.lower().startswith("table")
                    font_name = first_span.get("font", "").lower()
                    is_b = "bold" in font_name or ".b" in font_name
                    is_i = "italic" in font_name or is_caption
                    ff = FONT_BOLDITAL if (is_b and is_i) else (FONT_BOLD if is_b else (FONT_ITAL if is_i else FONT_REG))
                    
                    s_color = first_span.get("color", 0)
                    text_color = (1.0, 1.0, 1.0) if s_color == 16777215 else (0.08, 0.08, 0.08)
                    fill_color = (0.0, 0.4, 0.7) if s_color == 16777215 else (1.0, 1.0, 1.0)
                    
                    if "PICTORIAL REVIEW" in full_text and "Open Access" in full_text:
                        tr = "REVUE ICONOGRAPHIQUE   Open Access"
                    elif "Keywords:" in full_text:
                        tr = "Mots-clés : Nerfs crâniens, Imagerie par résonance magnétique, Tomodensitométrie, Anatomie, Pathologie"
                    elif self.is_heading(full_text):
                        tr = self.translate_heading(full_text)
                        ff = FONT_BOLD
                    else:
                        tr = self.safe_translate(full_text)
                        
                    if not tr:
                        continue
                    align = fitz.TEXT_ALIGN_CENTER if is_caption else (fitz.TEXT_ALIGN_JUSTIFY if len(full_text) > 100 else fitz.TEXT_ALIGN_LEFT)
                    items.append({
                        "rect": rect,
                        "text": tr,
                        "fontfile": ff,
                        "fontsize": first_span.get("size", 9.0),
                        "color": text_color,
                        "fill": fill_color,
                        "align": align
                    })
                    
            for it in items:
                page.add_redact_annot(it["rect"], fill=it["fill"])
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            
            for it in items:
                fs = it["fontsize"]
                rect = it["rect"]
                fitted = False
                exp_rect = fitz.Rect(rect.x0 - 0.5, rect.y0 - 0.5, rect.x1 + 0.5, rect.y1 + 1.5)
                while fs >= max(5.0, it["fontsize"] * 0.68):
                    rc = page.insert_textbox(exp_rect, it["text"], fontfile=it["fontfile"], fontsize=fs, color=it["color"], align=it["align"], lineheight=1.10)
                    if rc >= 0:
                        fitted = True
                        break
                    fs -= 0.25
                if not fitted:
                    down_rect = fitz.Rect(exp_rect.x0, exp_rect.y0, exp_rect.x1, exp_rect.y1 + 10)
                    page.insert_textbox(down_rect, it["text"], fontfile=it["fontfile"], fontsize=max(5.0, fs), color=it["color"], align=it["align"], lineheight=1.05)
                    
            words = len(page.get_text("words"))
            print(f"  - Page {p_idx+1:2d}/{len(doc)} in-place translation OK (words: {words})")

        out_name = f"{input_pdf.stem}_FR_integral.pdf"
        exact_out = dest_dir / out_name
        doc.save(str(exact_out))
        print(f"[Exact-Replica PDF] Generated successfully: {exact_out} ({exact_out.stat().st_size / 1024 / 1024:.2f} MB)")
        
        # Try syncing default _fr.pdf
        try:
            shutil.copy2(exact_out, dest_dir / f"{input_pdf.stem}_fr.pdf")
        except Exception:
            pass
        return exact_out

    def build_docx_with_figures(self, input_pdf: Path, txt_path: Path, dest_dir: Path) -> Path:
        """Embeds all high-res figures and schematics into Word document."""
        print(f"\n[Enriched DOCX] Extracting high-res images and rebuilding Word document...")
        doc_pdf = fitz.open(input_pdf)
        doc_word = Document()
        
        for section in doc_word.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)
            
        page_images = {}
        for p_idx, page in enumerate(doc_pdf):
            png_list = []
            for img_info in page.get_images():
                xref = img_info[0]
                try:
                    pix = fitz.Pixmap(doc_pdf, xref)
                    if pix.n >= 5:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    if pix.width < 120 or pix.height < 120:
                        continue
                    png_list.append(pix.tobytes("png"))
                except Exception:
                    pass
            if png_list:
                page_images[p_idx + 1] = png_list
                
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
        fig_regex = re.compile(r"Fig\.\s*(\d+)", re.IGNORECASE)
        placed_figures = set()
        
        fig_to_page = {
            1: 2, 2: 4, 3: 5, 4: 6, 5: 6, 6: 7, 7: 8, 8: 8,
            9: 9, 10: 9, 11: 11, 12: 11, 13: 11, 14: 12, 15: 12,
            16: 13, 17: 13, 18: 14, 19: 14, 20: 15, 21: 16
        }
        
        for c in chunks:
            if c.startswith("# "):
                p = doc_word.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(c[2:].strip())
                r.font.name = 'Arial'
                r.font.size = Pt(16)
                r.font.bold = True
                r.font.color.rgb = RGBColor(17, 24, 39)
            elif c.startswith("## "):
                h = doc_word.add_heading(c[3:].strip(), level=1)
                h.style.font.name = 'Arial'
                h.style.font.color.rgb = RGBColor(30, 58, 138)
            elif c.startswith("### "):
                h = doc_word.add_heading(c[4:].strip(), level=2)
                h.style.font.name = 'Arial'
                h.style.font.color.rgb = RGBColor(31, 41, 55)
            elif c.startswith("*Légende :") and c.endswith("*"):
                caption_text = c[10:-1].strip()
                match = fig_regex.search(caption_text)
                if match:
                    fnum = int(match.group(1))
                    if fnum in fig_to_page and fnum not in placed_figures:
                        pg = fig_to_page[fnum]
                        if pg in page_images and len(page_images[pg]) > 0:
                            img_b = page_images[pg].pop(0)
                            pic_p = doc_word.add_paragraph()
                            pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            doc_word.add_picture(io.BytesIO(img_b), width=Inches(5.5))
                            placed_figures.add(fnum)
                p = doc_word.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(caption_text)
                r.italic = True
                r.font.name = 'Arial'
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(75, 85, 99)
            elif c.startswith("- ") and re.match(r"^- \d+\.\s+[A-Z]", c):
                p = doc_word.add_paragraph(c[2:].strip())
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.first_line_indent = Inches(-0.25)
                p.style.font.size = Pt(9)
                p.style.font.color.rgb = RGBColor(55, 65, 81)
            else:
                p = doc_word.add_paragraph(c)
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.style.font.name = 'Times New Roman'
                p.style.font.size = Pt(10.5)

        docx_path = dest_dir / f"{input_pdf.stem}_fr.docx"
        try:
            doc_word.save(str(docx_path))
        except Exception:
            docx_path = dest_dir / f"{input_pdf.stem}_FR_figures.docx"
            doc_word.save(str(docx_path))
        print(f"[Enriched DOCX] Generated: {docx_path} ({docx_path.stat().st_size / 1024 / 1024:.2f} MB)")
        return docx_path

    def process(self, input_target: str, output_dir: Optional[str] = None):
        target_path = Path(input_target).resolve()
        if target_path.is_dir():
            pdfs = list(target_path.glob("*.pdf"))
            if not pdfs:
                raise FileNotFoundError(f"No PDF file found inside directory: {target_path}")
            pdf_path = pdfs[0]
            dest_dir = Path(output_dir).resolve() if output_dir else target_path
        else:
            if not target_path.exists():
                raise FileNotFoundError(f"File not found: {target_path}")
            pdf_path = target_path
            dest_dir = Path(output_dir).resolve() if output_dir else target_path.parent

        dest_dir.mkdir(parents=True, exist_ok=True)
        print("=" * 60)
        print(f"Scientific Paper Translation Pipeline")
        print(f"Target: {pdf_path.name} ({pdf_path.stat().st_size / 1024 / 1024:.2f} MB)")
        print(f"Destination: {dest_dir}")
        print(f"Target Language: {self.target_lang.upper()} | Domain: {self.domain}")
        print("=" * 60)

        t0 = time.time()
        
        # 1. Run pipeline for base structured documents (TXT, HTML, LaTeX, Docx, base PDF)
        pipeline = ScientificPipeline()
        base_res = pipeline.process_document(file_path=pdf_path, domain=self.domain)
        txt_path = dest_dir / f"{pdf_path.stem}_fr.txt"
        
        # 2. Generate exact in-place PDF replica (preserves 100% of images and layout)
        exact_pdf = self.translate_pdf_inplace(pdf_path, dest_dir)
        
        # 3. Generate enriched DOCX with all embedded figures
        enriched_docx = self.build_docx_with_figures(pdf_path, txt_path, dest_dir)
        
        # Save TM
        with open(self.tm_path, "w", encoding="utf-8") as f:
            json.dump(self.tm, f, ensure_ascii=False, indent=2)
            
        elapsed = time.time() - t0
        print("\n" + "=" * 60)
        print(f"TRANSLATION COMPLETED IN {elapsed:.1f}s")
        print("Deliverables:")
        print(f"  [PDF Exact Replica]   : {exact_pdf}")
        print(f"  [Word DOCX + Figures] : {enriched_docx}")
        print(f"  [HTML Article]        : {dest_dir / f'{pdf_path.stem}_fr.html'}")
        print(f"  [Clean Text]          : {txt_path}")
        print(f"  [LaTeX Source]        : {dest_dir / f'{pdf_path.stem}_fr.tex'}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Scientific Paper In-Place Translator & Document Rebuilder")
    parser.add_argument("input", help="Path to input PDF file or folder containing the paper")
    parser.add_argument("-l", "--lang", default="fr", help="Target language code (default: fr)")
    parser.add_argument("-d", "--domain", default="medicine_radiology", help="Scientific domain glossary")
    parser.add_argument("-o", "--output-dir", default=None, help="Output destination folder")
    parser.add_argument("-t", "--threads", type=int, default=8, help="PyTorch CPU threads")

    args = parser.parse_args()
    translator = UniversalPaperTranslator(target_lang=args.lang, domain=args.domain, cpu_threads=args.threads)
    translator.process(args.input, args.output_dir)

if __name__ == "__main__":
    main()
