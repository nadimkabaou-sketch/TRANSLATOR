import os
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from .extractor import DocumentExtractor
from .language_detector import LanguageDetector
from .translator import ScientificTranslator
from .quality_controller import QualityController
from .document_builder import DocumentBuilder
from .academic_resolver import AcademicResolver
from ..config import UPLOAD_DIR, OUTPUT_DIR

class ScientificPipeline:
    """
    Orchestrates the entire translation workflow:
    Input Document / DOI -> Extraction -> Detection -> Protected Scientific Translation
    -> Scientific Quality Audit -> Document Reconstruction (PDF, DOCX, LaTeX, TXT, HTML).
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.extractor = DocumentExtractor()
        self.language_detector = LanguageDetector()
        self.translator = ScientificTranslator()
        self.quality_controller = QualityController()
        self.document_builder = DocumentBuilder(self.output_dir)
        self.academic_resolver = AcademicResolver()

    def process_document(
        self,
        file_path: Optional[str or Path] = None,
        doi_or_url: Optional[str] = None,
        domain: Optional[str] = "medicine_radiology",
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        
        def update_progress(stage: str, percent: int):
            if progress_callback:
                progress_callback(stage, percent)
            print(f"[Pipeline] {percent}% - {stage}")

        # STAGE 1: INGESTION & EXTRACTION
        update_progress("Extraction du document...", 10)
        
        if doi_or_url:
            # Academic direct resolution
            extracted_doc = self._ingest_doi_or_url(doi_or_url)
        elif file_path:
            extracted_doc = self.extractor.extract(file_path)
        else:
            raise ValueError("Either file_path or doi_or_url must be provided.")

        raw_elements = extracted_doc.get("elements", [])
        if not raw_elements:
            raise ValueError("No extractable elements found in the document.")

        # STAGE 2: LANGUAGE DETECTION
        update_progress("Détection automatique de la langue...", 25)
        # Sample the first 3 paragraphs
        sample_text = " ".join([e.get("text", "") for e in raw_elements[:4]])
        lang_info = self.language_detector.detect(sample_text)
        src_lang = lang_info["code"]
        print(f"[Pipeline] Detected Language: {lang_info['name']} ({src_lang}) with confidence {lang_info['confidence']}")

        # STAGE 3: TRANSLATION WITH SCIENTIFIC INTEGRITY PROTECTION
        update_progress("Traduction scientifique fidèle en cours...", 40)
        translated_elements = []
        total_elems = len(raw_elements)

        for idx, elem in enumerate(raw_elements):
            e_type = elem.get("type", "paragraph")
            src_text = elem.get("text", "")

            # Don't translate pure equations, figures or verbatim references
            if e_type in ["equation"] or (e_type == "figure" and src_text == "[Figure Image]"):
                trg_text = src_text
                warnings = []
            elif e_type == "reference":
                # References must strictly preserve original author names, dates, journal titles and DOIs
                trg_text = src_text
                warnings = []
            elif e_type == "table" and "table_data" in elem:
                # Translate table cell by cell
                trg_table_data = []
                for row in elem["table_data"]:
                    trg_row = []
                    for cell in row:
                        if cell and not cell.isnumeric():
                            res = self.translator.translate_segment(cell, src_lang=src_lang, domain=domain)
                            trg_row.append(res["translated"])
                        else:
                            trg_row.append(cell)
                    trg_table_data.append(trg_row)
                elem_copy = dict(elem)
                elem_copy["table_data"] = trg_table_data
                elem_copy["text"] = self.translator.translate_segment(src_text, src_lang=src_lang, domain=domain)["translated"]
                translated_elements.append(elem_copy)
                continue
            else:
                # Standard segment (title, heading, paragraph, caption, reference)
                res = self.translator.translate_segment(src_text, src_lang=src_lang, domain=domain)
                trg_text = res["translated"]
                warnings = res.get("warnings", [])

            trg_elem = dict(elem)
            trg_elem["text"] = trg_text
            trg_elem["warnings"] = warnings
            translated_elements.append(trg_elem)

            # Progressive update between 40% and 80%
            current_pct = 40 + int((idx + 1) / total_elems * 40)
            update_progress(f"Traduction du paragraphe {idx+1}/{total_elems}...", current_pct)

        # Translated document representation
        translated_doc = dict(extracted_doc)
        title_res = self.translator.translate_segment(extracted_doc.get("title", ""), src_lang=src_lang, domain=domain)
        translated_doc["title"] = title_res["translated"]
        translated_doc["elements"] = translated_elements

        # STAGE 4: QUALITY CONTROL & AUDIT
        update_progress("Contrôle qualité scientifique et audit de fidélité...", 85)
        qc_report = self.quality_controller.audit_document(raw_elements, translated_elements)

        # STAGE 5: DOCUMENT RECONSTRUCTION (PDF, DOCX, LaTeX, TXT, HTML)
        update_progress("Reconstruction et exportation multi-formats...", 95)
        base_name = Path(extracted_doc.get("file_name", "scientific_paper")).stem
        export_paths = self.document_builder.build_all(translated_doc, base_name)

        # If file_path was provided and points to a folder outside output_dir, also deliver exports to source folder
        if file_path:
            source_dir = Path(file_path).parent
            if source_dir.exists() and source_dir.resolve() != self.output_dir.resolve():
                for fmt, fpath in export_paths.items():
                    dest = source_dir / Path(fpath).name
                    try:
                        shutil.copy2(fpath, dest)
                        print(f"[Pipeline] Exported {fmt.upper()} to source folder: {dest}")
                    except Exception as err:
                        print(f"[Pipeline] Notice: Failed to copy {fmt} to source folder: {err}")

        update_progress("Traduction scientifique terminée avec succès !", 100)

        return {
            "source_doc": extracted_doc,
            "translated_doc": translated_doc,
            "detected_language": lang_info,
            "target_language": "fr",
            "qc_report": qc_report,
            "export_files": export_paths
        }

    def _ingest_doi_or_url(self, identifier: str) -> Dict[str, Any]:
        """Resolves an article from DOI / URL into a structured document."""
        # 1. Fetch metadata via PubMed or Crossref
        pm_data = self.academic_resolver.fetch_pubmed(identifier)
        if "error" not in pm_data:
            title = pm_data.get("title", "Article")
            authors = ", ".join(pm_data.get("authors", []))
            journal = pm_data.get("journal", "")
            
            elements = [
                {"id": "elem_0", "type": "title", "level": 1, "text": title},
                {"id": "elem_1", "type": "paragraph", "level": None, "text": f"Auteurs : {authors}"},
                {"id": "elem_2", "type": "paragraph", "level": None, "text": f"Revue : {journal}"},
                {"id": "elem_3", "type": "heading", "level": 1, "text": "Abstract"}
            ]

            elem_id = 4
            for sec in pm_data.get("abstract_sections", []):
                if sec.get("label"):
                    elements.append({
                        "id": f"elem_{elem_id}",
                        "type": "heading",
                        "level": 2,
                        "text": sec["label"].title()
                    })
                    elem_id += 1
                elements.append({
                    "id": f"elem_{elem_id}",
                    "type": "paragraph",
                    "level": None,
                    "text": sec.get("text", "")
                })
                elem_id += 1

            return {
                "title": title,
                "file_name": f"pubmed_{pm_data.get('pmid', 'article')}.txt",
                "source_type": "pubmed",
                "elements": elements
            }
        else:
            # Fallback to Crossref
            cr_data = self.academic_resolver.resolve_doi(identifier)
            title = cr_data.get("title", "Article")
            authors = ", ".join(cr_data.get("authors", []))
            return {
                "title": title,
                "file_name": f"crossref_{cr_data.get('doi', 'article').replace('/', '_')}.txt",
                "source_type": "crossref",
                "elements": [
                    {"id": "elem_0", "type": "title", "level": 1, "text": title},
                    {"id": "elem_1", "type": "paragraph", "level": None, "text": f"Auteurs : {authors}"},
                    {"id": "elem_2", "type": "paragraph", "level": None, "text": cr_data.get("abstract", "")}
                ]
            }
