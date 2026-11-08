---
name: scientific-paper-translator
description: >-
  Translates complex academic, scientific, and medical papers (PDF, DOCX, LaTeX) into French (or other languages)
  while strictly preserving 100% of the original document layout, multi-column geometry, typography, and ALL embedded
  high-resolution figures, schematics, and imaging (MRI, CT, ultrasound) in place without text truncation or empty paragraphs.
  Trigger when the user asks to translate a scientific paper, PDF, academic article, medical document, or provides a file path or folder to translate.
---

# Scientific Paper In-Place Translator & Document Rebuilder

Autonomous engine to translate peer-reviewed scientific papers and academic articles with publication-grade fidelity.

## Key Capabilities

1. **Exact In-Place PDF Replica** :
   - Preserves 100% of page geometries, headers, footers, two-column layouts, and borders.
   - Preserves **ALL high-resolution figures, schematics, diagrams, and medical images** (MRI, CT, histology) at native resolution without any deletion or alteration.
   - Replaces English text blocks *in situ* using auto-fitted vector typography (Arial Bold for headings, Arial Regular for body, Arial Italic for captions).
   - Guarantees **zero empty paragraphs** through robust decoupled heading/body block parsing.
2. **Enriched Word DOCX Rebuilder** :
   - Reconstructs fully editable `.docx` documents containing all extracted high-resolution figures embedded right next to their corresponding figure captions.
3. **Multi-Format Publication Exports** :
   - Outputs standalone `.html`, clean structured `.txt`, and standard `.tex` (LaTeX) sources.
4. **Scientific Integrity & Protection** :
   - 100% preservation of mathematical equations, numbers, units (mm, cm, T, ms, etc.), statistical intervals (p-values, 95% CI), and bibliographic citations.
   - Enforces authoritative domain glossaries (e.g., Neuroradiology, Oncology, Physics, Computer Science).

---

## Antigravity Agent Execution Instructions

When the user asks to translate a scientific paper, article, or folder:

### 1. Identify Target Path
If the user provides a folder (e.g. `C:\Users\...\folder`), locate the `.pdf` file inside it. If a direct file path is given, use it directly.

### 2. Execute Translation CLI
Run the unified translator command:

```powershell
python translate.py "<path_to_file_or_folder>" --lang fr --domain medicine_radiology
```

### 3. Generated Deliverables
The engine produces the following deliverables directly inside the source folder:
* `<stem>_FR_integral.pdf` : Complete visual replica with all original figures and translated French text.
* `<stem>_fr.docx` : Fully editable Word document with all high-resolution figures embedded.
* `<stem>_fr.html` : Clean standalone HTML article.
* `<stem>_fr.txt` : Structured markdown/plain text.
* `<stem>_fr.tex` : Standard academic LaTeX source.

### 4. Response Guidelines
* Present direct clickable links to `<stem>_FR_integral.pdf` and `<stem>_fr.docx`.
* Summarize key paper metrics (title, authors, volume, domain, image count).
* Provide quality assurance statistics (word count ratio, citation preservation).
