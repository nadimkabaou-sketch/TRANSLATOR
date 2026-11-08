import os
from pathlib import Path
from typing import Dict, List, Any

# PDF generation via ReportLab
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import inch

# DOCX generation via python-docx
from docx import Document as DocxDoc
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

class DocumentBuilder:
    """
    Reconstructs translated academic documents into publication-ready files:
    PDF, DOCX, LaTeX, TXT, and HTML.
    Faithfully preserves original hierarchy, headings, tables, figures, equations,
    and bibliography layout.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_all(self, doc_data: Dict[str, Any], base_filename: str) -> Dict[str, str]:
        """Generates all supported output formats and returns their file paths."""
        stem = Path(base_filename).stem
        paths = {
            "pdf": str(self.build_pdf(doc_data, f"{stem}_fr.pdf")),
            "docx": str(self.build_docx(doc_data, f"{stem}_fr.docx")),
            "latex": str(self.build_latex(doc_data, f"{stem}_fr.tex")),
            "txt": str(self.build_txt(doc_data, f"{stem}_fr.txt")),
            "html": str(self.build_html(doc_data, f"{stem}_fr.html"))
        }
        return paths

    def build_pdf(self, doc_data: Dict[str, Any], filename: str) -> Path:
        """Generates high-quality scientific PDF with academic styling."""
        pdf_path = self.output_dir / filename
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()

        # Custom academic styles
        title_style = ParagraphStyle(
            'AcademicTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#111827'),
            alignment=1, # Center
            spaceAfter=14
        )

        h1_style = ParagraphStyle(
            'AcademicH1',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        )

        h2_style = ParagraphStyle(
            'AcademicH2',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#1F2937'),
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            'AcademicBody',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#27272A'),
            alignment=4, # Justify
            spaceAfter=8,
            firstLineIndent=14
        )

        caption_style = ParagraphStyle(
            'AcademicCaption',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#4B5563'),
            spaceBefore=4,
            spaceAfter=10
        )

        ref_style = ParagraphStyle(
            'AcademicRef',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#374151'),
            spaceAfter=4
        )

        story = []

        # Document Title
        title_text = doc_data.get("title", "Article Scientifique")
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 10))

        # Elements
        for elem in doc_data.get("elements", []):
            e_type = elem.get("type", "paragraph")
            text = elem.get("text", "")

            # Escape XML entities for ReportLab
            clean_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            if e_type == "title":
                continue # Already placed
            elif e_type == "heading":
                lvl = elem.get("level", 1)
                st = h1_style if lvl == 1 else h2_style
                story.append(Paragraph(clean_text, st))
            elif e_type == "caption":
                story.append(Paragraph(clean_text, caption_style))
            elif e_type == "reference":
                story.append(Paragraph(clean_text, ref_style))
            elif e_type == "equation":
                eq_style = ParagraphStyle('Eq', parent=body_style, fontName='Courier', alignment=1)
                story.append(Paragraph(clean_text, eq_style))
            elif e_type == "table" and "table_data" in elem:
                table_rows = elem["table_data"]
                if table_rows:
                    t_cells = [[Paragraph(str(c), body_style) for c in row] for row in table_rows]
                    t = Table(t_cells)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#1E3A8A')),
                        ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.HexColor('#1E3A8A')),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    story.append(Spacer(1, 6))
                    story.append(t)
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(clean_text, body_style))

        doc.build(story)
        return pdf_path

    def build_docx(self, doc_data: Dict[str, Any], filename: str) -> Path:
        """Generates editable Microsoft Word DOCX."""
        docx_path = self.output_dir / filename
        doc = DocxDoc()

        # Set default font
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(11)

        # Title
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_p.add_run(doc_data.get("title", "Article Scientifique"))
        title_run.font.name = 'Arial'
        title_run.font.size = Pt(16)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(17, 24, 39)

        # Elements
        for elem in doc_data.get("elements", []):
            e_type = elem.get("type", "paragraph")
            text = elem.get("text", "")

            if e_type == "title":
                continue
            elif e_type == "heading":
                lvl = elem.get("level", 1)
                h = doc.add_heading(text, level=min(lvl, 3))
                h.style.font.name = 'Arial'
                h.style.font.color.rgb = RGBColor(30, 58, 138)
            elif e_type == "caption":
                p = doc.add_paragraph()
                r = p.add_run(text)
                r.italic = True
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(75, 85, 99)
            elif e_type == "reference":
                p = doc.add_paragraph(text)
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.first_line_indent = Inches(-0.25)
                p.style.font.size = Pt(9.5)
            elif e_type == "table" and "table_data" in elem:
                t_data = elem["table_data"]
                if t_data and len(t_data) > 0:
                    t = doc.add_table(rows=len(t_data), cols=len(t_data[0]))
                    t.style = 'Table Grid'
                    for r_idx, row in enumerate(t_data):
                        for c_idx, cell_text in enumerate(row):
                            t.cell(r_idx, c_idx).text = str(cell_text)
            else:
                p = doc.add_paragraph(text)
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        doc.save(str(docx_path))
        return docx_path

    def build_latex(self, doc_data: Dict[str, Any], filename: str) -> Path:
        """Generates standard academic LaTeX source."""
        latex_path = self.output_dir / filename
        title = doc_data.get("title", "Article Scientifique")

        lines = [
            r"\documentclass[11pt,a4paper]{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[french]{babel}",
            r"\usepackage{amsmath,amssymb}",
            r"\usepackage{geometry}",
            r"\usepackage{hyperref}",
            r"\geometry{margin=2.5cm}",
            f"\\title{{{title}}}",
            r"\date{\today}",
            r"\begin{document}",
            r"\maketitle",
            ""
        ]

        for elem in doc_data.get("elements", []):
            e_type = elem.get("type", "paragraph")
            text = elem.get("text", "")

            if e_type == "title":
                continue
            elif e_type == "heading":
                lvl = elem.get("level", 1)
                cmd = r"\section" if lvl == 1 else (r"\subsection" if lvl == 2 else r"\subsubsection")
                lines.append(f"{cmd}{{{text}}}")
            elif e_type == "equation":
                lines.append(text)
            elif e_type == "caption":
                lines.append(f"\\caption{{{text}}}")
            elif e_type == "reference":
                lines.append(f"\\noindent {text}\\\\")
            else:
                lines.append(f"{text}\n")

        lines.append(r"\end{document}")

        with open(latex_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return latex_path

    def build_txt(self, doc_data: Dict[str, Any], filename: str) -> Path:
        """Generates plain text and structured Markdown."""
        txt_path = self.output_dir / filename
        lines = [f"# {doc_data.get('title', 'Article')}\n"]

        for elem in doc_data.get("elements", []):
            e_type = elem.get("type", "paragraph")
            text = elem.get("text", "")

            if e_type == "title":
                continue
            elif e_type == "heading":
                lvl = elem.get("level", 1)
                prefix = "#" * (lvl + 1)
                lines.append(f"\n{prefix} {text}\n")
            elif e_type == "caption":
                lines.append(f"\n*Légende : {text}*\n")
            elif e_type == "reference":
                lines.append(f"- {text}")
            elif e_type == "table" and "table_data" in elem:
                t_data = elem["table_data"]
                lines.append("\n[TABLE]")
                for r in t_data:
                    lines.append(" | ".join(str(c) for c in r))
                lines.append("")
            else:
                lines.append(f"\n{text}\n")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return txt_path

    def build_html(self, doc_data: Dict[str, Any], filename: str) -> Path:
        """Generates clean HTML article layout."""
        html_path = self.output_dir / filename
        title = doc_data.get("title", "Article")

        content_html = [f"<h1 class='doc-title'>{title}</h1>"]

        for elem in doc_data.get("elements", []):
            e_type = elem.get("type", "paragraph")
            text = elem.get("text", "")

            if e_type == "title":
                continue
            elif e_type == "heading":
                lvl = elem.get("level", 1)
                content_html.append(f"<h{lvl+1} class='doc-heading'>{text}</h{lvl+1}>")
            elif e_type == "caption":
                content_html.append(f"<p class='doc-caption'><em>{text}</em></p>")
            elif e_type == "reference":
                content_html.append(f"<div class='doc-reference'>{text}</div>")
            elif e_type == "table" and "table_data" in elem:
                t_data = elem["table_data"]
                rows = "".join([f"<tr>{''.join([f'<td>{c}</td>' for c in r])}</tr>" for r in t_data])
                content_html.append(f"<table class='doc-table'>{rows}</table>")
            else:
                content_html.append(f"<p class='doc-paragraph'>{text}</p>")

        template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Times New Roman', serif; line-height: 1.6; max-width: 860px; margin: 40px auto; padding: 0 20px; color: #111827; }}
        h1.doc-title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; text-align: center; color: #1e3a8a; font-size: 24px; margin-bottom: 30px; }}
        h2.doc-heading {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px; margin-top: 30px; }}
        h3.doc-heading {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1f2937; margin-top: 20px; }}
        p.doc-paragraph {{ text-align: justify; margin-bottom: 14px; text-indent: 1.5em; }}
        p.doc-caption {{ font-size: 0.9em; color: #4b5563; font-style: italic; margin-bottom: 14px; }}
        .doc-reference {{ font-size: 0.85em; color: #374151; margin-bottom: 8px; padding-left: 24px; text-indent: -24px; }}
        table.doc-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        table.doc-table td {{ border-top: 1px solid #d1d5db; border-bottom: 1px solid #d1d5db; padding: 8px; text-align: left; }}
    </style>
</head>
<body>
    {''.join(content_html)}
</body>
</html>"""

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(template)

        return html_path
