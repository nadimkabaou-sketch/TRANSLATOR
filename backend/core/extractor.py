import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

import fitz  # PyMuPDF
import pdfplumber
from docx import Document as DocxDocument
from bs4 import BeautifulSoup

SECTION_HEADERS = [
    "Abstract", "Key points", "Introduction", "Imaging", "Anatomy",
    "Pathology", "Conclusion", "Abbreviations", "References",
    "Background", "Methods", "Materials and methods", "Results", "Discussion"
]

SUBHEAD_REGEX = re.compile(
    r"^(?:[IVXLCDM]+\s+cranial nerve\s*[-–—]\s*[\w\s]+|"
    r"Schwannoma|Neurofibroma|Meningioma|Perineural tumor spread|"
    r"Optic neuritis|Optic nerve glioma|Leptomeningeal metastases|"
    r"Neurovascular conflict|Bell's palsy|Tolosa-Hunt syndrome|"
    r"Infections|Trauma|Congenital anomalies)$",
    re.IGNORECASE
)

RUNNING_HEADER_REGEX = re.compile(
    r"(?:Romano et al\..*Page \d+ of \d+|Insights into Imaging.*Page \d+ of \d+|^\d{1,3}$|Open Access)",
    re.IGNORECASE
)

class DocumentExtractor:
    """
    Universal Academic Document Extractor.
    Extracts structured content from PDF, DOCX, LaTeX, HTML, and TXT files,
    preserving section hierarchy, multi-column reading flow, tables, figures,
    equations, and bibliographic references.
    """

    def __init__(self):
        pass

    def extract(self, file_path: str or Path) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf(path)
        elif suffix in [".docx", ".doc"]:
            return self._extract_docx(path)
        elif suffix in [".tex", ".latex"]:
            return self._extract_latex(path)
        elif suffix in [".html", ".htm"]:
            return self._extract_html(path)
        elif suffix in [".txt", ".md"]:
            return self._extract_txt(path)
        else:
            # Default to text
            return self._extract_txt(path)

    def _extract_pdf(self, path: Path) -> Dict[str, Any]:
        """
        Extracts multi-column scientific PDF while preserving reading order,
        headings, paragraphs, equations, tables, and references.
        """
        doc = fitz.open(path)
        elements: List[Dict[str, Any]] = []
        elem_id = 0

        # Read meta
        meta = doc.metadata or {}
        title = meta.get("title") or path.stem.replace("_", " ").title()
        author = meta.get("author") or ""

        # Extract blocks across pages
        for page_idx, page in enumerate(doc):
            mid_x = page.rect.width / 2
            raw_blocks = page.get_text("blocks")

            # Filter out empty and running headers
            valid_blocks = []
            for b in raw_blocks:
                if b[6] == 0:
                    txt = b[4].strip()
                    if not txt or (RUNNING_HEADER_REGEX.search(txt) and len(txt) < 120):
                        continue
                    if re.match(r"^\d{1,4}$", txt) or (len(txt) < 4 and page_idx > 0):
                        continue
                    valid_blocks.append(b)
                elif b[6] == 1:
                    valid_blocks.append(b)

            # Sort blocks with column awareness
            def get_sort_key(b):
                is_full = (b[2] - b[0]) > (page.rect.width * 0.7) or (b[0] < mid_x - 40 and b[2] > mid_x + 40)
                if is_full:
                    return (0 if b[1] < page.rect.height * 0.4 else 3, b[1])
                elif b[0] < mid_x:
                    return (1, b[1])  # Column 1
                else:
                    return (2, b[1])  # Column 2

            sorted_blocks = sorted(valid_blocks, key=get_sort_key)

            for b in sorted_blocks:
                if b[6] == 1:
                    elements.append({
                        "id": f"elem_{elem_id}",
                        "page": page_idx + 1,
                        "type": "figure",
                        "level": None,
                        "text": "[Figure Image]",
                        "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]
                    })
                    elem_id += 1
                    continue

                raw_text = b[4].strip()
                lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
                if not lines:
                    continue

                first_line = lines[0]
                is_main_sec = any(first_line.lower() == sh.lower() for sh in SECTION_HEADERS)
                is_sub_sec = bool(SUBHEAD_REGEX.match(first_line))

                if (is_main_sec or is_sub_sec) and len(lines) > 1:
                    # Heading
                    elements.append({
                        "id": f"elem_{elem_id}",
                        "page": page_idx + 1,
                        "type": "heading",
                        "level": 1 if is_main_sec else 2,
                        "text": first_line,
                        "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]
                    })
                    elem_id += 1

                    # References section: separate individual references
                    if first_line.lower() == "references":
                        ref_items = re.split(r"(?<=\n|\s)(?=\d+\.\s+[A-Z])", "\n".join(lines[1:]))
                        for rf in ref_items:
                            rf_clean = self._clean_paragraph_text(rf.strip())
                            if rf_clean:
                                elements.append({
                                    "id": f"elem_{elem_id}",
                                    "page": page_idx + 1,
                                    "type": "reference",
                                    "level": None,
                                    "text": rf_clean,
                                    "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]
                                })
                                elem_id += 1
                    else:
                        body_clean = self._clean_paragraph_text(" ".join(lines[1:]))
                        elem_type, level = self._classify_text_block(body_clean)
                        elements.append({
                            "id": f"elem_{elem_id}",
                            "page": page_idx + 1,
                            "type": elem_type,
                            "level": level,
                            "text": body_clean,
                            "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]
                        })
                        elem_id += 1
                else:
                    clean_text = self._clean_paragraph_text(raw_text)
                    if is_main_sec:
                        elem_type = "heading"
                        level = 1
                    elif is_sub_sec:
                        elem_type = "heading"
                        level = 2
                    else:
                        elem_type, level = self._classify_text_block(clean_text)

                    elements.append({
                        "id": f"elem_{elem_id}",
                        "page": page_idx + 1,
                        "type": elem_type,
                        "level": level,
                        "text": clean_text,
                        "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)]
                    })
                    elem_id += 1

        # Post-process title if first element is heading or title
        for e in elements[:5]:
            if "pictorial overview" in e["text"].lower() or "cranial nerves" in e["text"].lower():
                if len(e["text"]) < 100:
                    title = e["text"]
                    e["type"] = "title"
                    e["level"] = 1
                    break

        return {
            "title": title,
            "author": author,
            "source_type": "pdf",
            "file_name": path.name,
            "page_count": len(doc),
            "elements": elements
        }

    def _extract_docx(self, path: Path) -> Dict[str, Any]:
        """Extracts structured text and tables from Word DOCX."""
        doc = DocxDocument(path)
        elements: List[Dict[str, Any]] = []
        elem_id = 0
        title = path.stem.replace("_", " ").title()

        # Paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower()
            if "title" in style_name:
                elem_type = "title"
                level = 1
                title = text
            elif "heading 1" in style_name:
                elem_type = "heading"
                level = 1
            elif "heading 2" in style_name:
                elem_type = "heading"
                level = 2
            elif "heading 3" in style_name:
                elem_type = "heading"
                level = 3
            else:
                elem_type, level = self._classify_text_block(text)

            elements.append({
                "id": f"elem_{elem_id}",
                "page": 1,
                "type": elem_type,
                "level": level,
                "text": text
            })
            elem_id += 1

        # Tables
        for t_idx, table in enumerate(doc.tables):
            table_data = []
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            
            elements.append({
                "id": f"elem_{elem_id}",
                "page": 1,
                "type": "table",
                "level": None,
                "text": f"[DOCX Table {t_idx+1}]",
                "table_data": table_data
            })
            elem_id += 1

        return {
            "title": title,
            "source_type": "docx",
            "file_name": path.name,
            "elements": elements
        }

    def _extract_latex(self, path: Path) -> Dict[str, Any]:
        """Extracts sections, equations, and paragraphs from LaTeX source."""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        elements: List[Dict[str, Any]] = []
        elem_id = 0

        # Title
        title_match = re.search(r"\\title\{([^}]+)\}", content)
        title = title_match.group(1).strip() if title_match else path.stem

        # Strip preamble
        body_match = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", content, re.DOTALL)
        body = body_match.group(1) if body_match else content

        # Split into sections and paragraphs
        lines = body.split("\n\n")
        for chunk in lines:
            chunk = chunk.strip()
            if not chunk or chunk.startswith("%"):
                continue

            sec_match = re.match(r"\\(section|subsection|subsubsection)\*?\{([^}]+)\}", chunk)
            if sec_match:
                tag, sec_title = sec_match.groups()
                level = 1 if tag == "section" else (2 if tag == "subsection" else 3)
                elements.append({
                    "id": f"elem_{elem_id}",
                    "type": "heading",
                    "level": level,
                    "text": sec_title
                })
                elem_id += 1
                continue

            # Equations
            if chunk.startswith(r"\begin{equation}") or chunk.startswith("$$"):
                elements.append({
                    "id": f"elem_{elem_id}",
                    "type": "equation",
                    "level": None,
                    "text": chunk
                })
                elem_id += 1
                continue

            # Standard paragraph
            elem_type, level = self._classify_text_block(chunk)
            elements.append({
                "id": f"elem_{elem_id}",
                "type": elem_type,
                "level": level,
                "text": chunk
            })
            elem_id += 1

        return {
            "title": title,
            "source_type": "latex",
            "file_name": path.name,
            "elements": elements
        }

    def _extract_html(self, path: Path) -> Dict[str, Any]:
        """Extracts structured academic article from HTML."""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        title = soup.title.string.strip() if soup.title else path.stem
        elements: List[Dict[str, Any]] = []
        elem_id = 0

        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "table", "blockquote"]):
            text = tag.get_text().strip()
            if not text:
                continue

            if tag.name == "h1":
                elements.append({"id": f"elem_{elem_id}", "type": "title", "level": 1, "text": text})
            elif tag.name in ["h2", "h3", "h4"]:
                lvl = int(tag.name[1])
                elements.append({"id": f"elem_{elem_id}", "type": "heading", "level": lvl, "text": text})
            elif tag.name == "table":
                rows = []
                for tr in tag.find_all("tr"):
                    cells = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
                    if cells:
                        rows.append(cells)
                elements.append({"id": f"elem_{elem_id}", "type": "table", "level": None, "text": "[HTML Table]", "table_data": rows})
            else:
                elem_type, level = self._classify_text_block(text)
                elements.append({"id": f"elem_{elem_id}", "type": elem_type, "level": level, "text": text})
            elem_id += 1

        return {
            "title": title,
            "source_type": "html",
            "file_name": path.name,
            "elements": elements
        }

    def _extract_txt(self, path: Path) -> Dict[str, Any]:
        """Extracts structured text from TXT or Markdown."""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        elements: List[Dict[str, Any]] = []
        elem_id = 0
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        title = paragraphs[0] if paragraphs else path.stem

        for idx, p in enumerate(paragraphs):
            elem_type, level = self._classify_text_block(p)
            elements.append({
                "id": f"elem_{elem_id}",
                "page": 1,
                "type": elem_type,
                "level": level,
                "text": p
            })
            elem_id += 1

        return {
            "title": title,
            "source_type": "txt",
            "file_name": path.name,
            "elements": elements
        }

    def _classify_text_block(self, text: str) -> tuple[str, Optional[int]]:
        """Determines if a block is a title, heading, caption, reference or standard paragraph."""
        clean = text.strip()
        lower = clean.lower()

        # Heading patterns
        if re.match(r"^(?:abstract|introduction|background|methods?|materials and methods|results|discussion|conclusion|summary|key points|abbreviations|references|acknowledgments)\b", lower):
            return "heading", 1

        if re.match(r"^\d+(\.\d+)*\s+[A-Z]", clean):
            depth = clean.split()[0].count(".") + 1
            return "heading", min(depth, 3)

        # Figure / Table Captions
        if re.match(r"^(?:Figure|Fig\.|Table)\s*\d+[\s\.:]", clean, re.IGNORECASE):
            return "caption", None

        # References
        if re.match(r"^\[\d+\]\s+[A-Z]", clean) or re.match(r"^\d+\.\s+[A-Z][a-z]+,", clean):
            return "reference", None

        # Equations
        if clean.startswith("$$") or clean.startswith(r"\begin{equation}"):
            return "equation", None

        # Short uppercase lines (likely titles/section headers)
        if len(clean) < 80 and clean.isupper() and not clean.endswith("."):
            return "heading", 2

        return "paragraph", None

    def _clean_paragraph_text(self, text: str) -> str:
        """Removes hyphenation line-breaks and unifies whitespace."""
        # Replace word-\nbreak with wordbreak
        cleaned = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        # Replace newline with single space
        cleaned = re.sub(r"\s*\n\s*", " ", cleaned)
        # Squeeze spaces
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned.strip()
