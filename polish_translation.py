import re
import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\Kabaou\Downloads\translator")
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"
DEST_DIR = Path(r"C:\Users\Kabaou\Downloads\Nouveau dossier (7)")

import sys
sys.path.insert(0, str(PROJECT_ROOT))
from backend.core.document_builder import DocumentBuilder

# Comprehensive medical neuroradiological corrections dictionary (ordered by length)
CORRECTIONS = [
    # False-friends & Latin anatomical errors
    (r"\bViandes et canaux faciaux internes\b", "Méat acoustique interne et canal facial"),
    (r"\bViandes auditives internes\b", "Méat acoustique interne (conduit auditif interne)"),
    (r"\bviande auditive interne\b", "conduit auditif interne (méat acoustique interne)"),
    (r"\bviandes auditives\b", "méat acoustique interne"),
    (r"\bIX Pr[ée]ambule jugulaire\b", "IX Foramen jugulaire"),
    (r"\bX Pr[ée]paratifs jugulaires\b", "X Foramen jugulaire"),
    (r"\bXI\.? Pr[ée]paratifs jugulaires\b", "XI Foramen jugulaire"),
    (r"\bV2 Pour m[ée]moire rotundum\b", "V2 Foramen rond (foramen rotundum)"),
    (r"\bPour m[ée]moire rotundum\b", "Foramen rond (foramen rotundum)"),
    (r"\bCanal optimal\b", "Canal optique"),
    (r"\bcanal optimal\b", "canal optique"),
    (r"\bGlyome nerveux optimal\b", "Gliome du nerf optique"),
    (r"\bgliome nerveux optimal\b", "gliome du nerf optique"),
    (r"\bnerf optical\b", "nerf optique"),
    (r"\bnerfs optiques\b", "nerfs optiques"),
    (r"\bNerf optical\b", "Nerf optique"),
    (r"\bL'augmentation du nerf\b", "Le rehaussement du nerf"),
    (r"\bl'augmentation du nerf\b", "le rehaussement du nerf"),
    (r"\baugmentation du nerf\b", "rehaussement du nerf"),
    (r"\baugmentation nerveuse\b", "rehaussement du nerf"),
    (r"\baugmentation de contraste\b", "rehaussement après injection de contraste"),
    (r"\bprocession libre [aà] l'[ée]tat stationnaire\b", "précession libre en régime permanent (SSFP)"),
    (r"\bprocession libre [aà] l'[ée]tat d'[ée]quilibre\b", "précession libre en régime permanent (SSFP)"),
    (r"\bprocession libre en [ée]tat d'[ée]quilibre\b", "précession libre en régime permanent (SSFP)"),
    (r"\bprocession libre\b", "précession libre (SSFP)"),
    (r"\bétalon d'or\b", "méthode de référence (gold standard)"),
    (r"\bl'étalon d'or\b", "la méthode de référence (gold standard)"),
    (r"\bL'étalon d'or\b", "La méthode de référence (gold standard)"),
    (r"\bl'or technique standard\b", "la technique de référence"),
    (r"\bRegards sur l'imagerie\b", "Insights into Imaging"),
    (r"\bRegard sur l'imagerie\b", "Insights into Imaging"),
    (r"\bperspectives de l'imagerie\b", "Insights into Imaging"),
    (r"\bPerspectives de l'imagerie\b", "Insights into Imaging"),
    (r"\bmati[èe]re blanche\b", "substance blanche"),
    (r"\bmati[èe]re grise\b", "substance grise"),
    (r"\bmati[èe]re grise p[ée]riaqueductaire\b", "substance grise périaqueducale"),
    (r"\bfossa cr[âa]nienne ant[ée]rieure\b", "fosse crânienne antérieure"),
    (r"\bfossa cr[âa]nienne moyenne\b", "fosse crânienne moyenne"),
    (r"\bfossa cr[âa]nienne post[ée]rieure\b", "fosse crânienne postérieure"),
    (r"\bfossa pterygopalatine\b", "fosse ptérygo-palatine"),
    (r"\bfossa infratemporelle\b", "fosse infra-temporale"),
    (r"\bfossa\b", "fosse"),
    (r"\bplaque de cribiforme\b", "lame criblée"),
    (r"\bPlaque de criblage\b", "Lame criblée"),
    (r"\bplaque de criblage\b", "lame criblée"),
    (r"\bfilets olfactif\b", "filets olfactifs"),
    (r"\bfiliae olfactif\b", "filets olfactifs"),
    (r"\blobe noncus\b", "uncus"),
    (r"\bnoncus\b", "uncus"),
    (r"\bforaminas\b", "foramens"),
    (r"\bdes foramens\b", "des foramens"),
    (r"\bFosse orbitale sup[ée]rieure\b", "Fissure orbitaire supérieure"),
    (r"\bfosse orbitale sup[ée]rieure\b", "fissure orbitaire supérieure"),
    (r"\bfosse orbitale inf[ée]rieure\b", "fissure orbitaire inférieure"),
    (r"\bMystus oblique sup[ée]rieur\b", "Muscle oblique supérieur"),
    (r"\bmystus oblique sup[ée]rieur\b", "muscle oblique supérieur"),
    (r"\bmuscle r[ée]ctus lat[ée]ral\b", "muscle droit latéral"),
    (r"\bmuscle réctus médian\b", "muscle droit médial"),
    (r"\brectus m[ée]dian\b", "droit médial"),
    (r"\brectus moyen\b", "droit médial"),
    (r"\brectus lat[ée]ral\b", "droit latéral"),
    (r"\brectus sup[ée]rieur\b", "droit supérieur"),
    (r"\brectus inf[ée]rieur\b", "droit inférieur"),
    (r"\bMuscles de langue\b", "Muscles de la langue"),
    (r"\bmuscles de langue\b", "muscles de la langue"),
    (r"\bmuscles de l'organisme\b", "muscles effecteurs cibles (dénervation)"),
    (r"\bmuscles de l'organe final\b", "muscles cibles de l'organe effecteur"),
    (r"\btomographies calcul[ée]es\b", "tomodensitométrie (TDM)"),
    (r"\btomographie calcul[ée]e \(CT\)\b", "tomodensitométrie (TDM)"),
    (r"\bTomographie calcul[ée]e \(CT\)\b", "Tomodensitométrie (TDM)"),
    (r"\btomographie calcul[ée]e\b", "tomodensitométrie (TDM)"),
    (r"\bTomographie calcul[ée]e\b", "Tomodensitométrie (TDM)"),
    (r"\bLes dysfonctionnements cr[âa]niens\b", "Les dysfonctions des nerfs crâniens"),
    (r"\bles dysfonctionnements cr[âa]niens\b", "les dysfonctions des nerfs crâniens"),
    (r"\bdysfonctionnements cr[âa]niens\b", "dysfonctions des nerfs crâniens"),
    (r"\bconflit neurovasculaire\b", "conflit neuro-vasculaire"),
    (r"\bdiss[ée]mination p[ée]rineurale\b", "dissémination périneurale (PNS)"),
    (r"\bpropagande p[ée]rineurale\b", "dissémination périneurale (PNS)"),
    (r"\bpropagation p[ée]rineurale\b", "dissémination périneurale (PNS)"),
    (r"\binvasion p[ée]rineurale\b", "invasion périneurale (PNI)"),
    (r"\bpr[ée]cession libre en r[ée]gime permanent\b", "précession libre en régime permanent (SSFP)"),
    (r"\bconstuctive interference in steady state\b", "CISS (constructive interference in steady state)"),
    (r"\bliquide c[ée]r[ée]bro-spinal \(CSF\)\b", "liquide cérébro-spinal (LCR)"),
    (r"\bliquide c[ée]r[ée]bro-spinal\b", "liquide cérébro-spinal (LCR)"),
    (r"\bCSF\b", "LCR"),
    (r"\bCT\b", "TDM"),
    (r"\bTC\b", "TDM"),
    (r"\bPrésentation\b", "Introduction"),
    (r"\b## Présentation\b", "## Introduction")
]

def clean_medical_text(text: str) -> str:
    cleaned = text
    for pattern, repl in CORRECTIONS:
        cleaned = re.sub(pattern, repl, cleaned)
    return cleaned

def polish_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    polished = clean_medical_text(content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(polished)
    print(f"Polished {path.name} ({len(content)} -> {len(polished)} chars)")

if __name__ == "__main__":
    print("=== Starting Neuroradiological French Polishing ===")
    # Polish text and HTML directly
    polish_file(OUTPUT_DIR / "13244_2019_Article_719_fr.txt")
    polish_file(OUTPUT_DIR / "13244_2019_Article_719_fr.html")
    polish_file(OUTPUT_DIR / "13244_2019_Article_719_fr.tex")

    # Reconstruct DOCX and PDF with polished text
    txt_content = (OUTPUT_DIR / "13244_2019_Article_719_fr.txt").read_text(encoding="utf-8")

    # Parse sections and reconstruct elements
    lines = txt_content.split("\n\n")
    reconstructed_elements = []
    title = "Imagerie des nerfs crâniens : un aperçu pictural"
    elem_id = 0

    for chunk in lines:
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk.startswith("# "):
            title = chunk[2:].strip()
        elif chunk.startswith("## "):
            reconstructed_elements.append({
                "id": f"elem_{elem_id}",
                "type": "heading",
                "level": 1,
                "text": chunk[3:].strip()
            })
            elem_id += 1
        elif chunk.startswith("### "):
            reconstructed_elements.append({
                "id": f"elem_{elem_id}",
                "type": "heading",
                "level": 2,
                "text": chunk[4:].strip()
            })
            elem_id += 1
        elif chunk.startswith("*Légende :") and chunk.endswith("*"):
            caption_text = chunk[10:-1].strip()
            reconstructed_elements.append({
                "id": f"elem_{elem_id}",
                "type": "caption",
                "level": None,
                "text": caption_text
            })
            elem_id += 1
        elif chunk.startswith("- ") and len(chunk) > 10 and re.match(r"^- \d+\.\s+[A-Z]", chunk):
            reconstructed_elements.append({
                "id": f"elem_{elem_id}",
                "type": "reference",
                "level": None,
                "text": chunk[2:].strip()
            })
            elem_id += 1
        else:
            reconstructed_elements.append({
                "id": f"elem_{elem_id}",
                "type": "paragraph",
                "level": None,
                "text": chunk
            })
            elem_id += 1

    doc_data = {
        "title": title,
        "elements": reconstructed_elements
    }

    builder = DocumentBuilder(OUTPUT_DIR)
    builder.build_pdf(doc_data, "13244_2019_Article_719_fr.pdf")
    builder.build_docx(doc_data, "13244_2019_Article_719_fr.docx")
    print("PDF and DOCX rebuilt with polished medical French terminology!")

    # Copy all 5 files to destination folder
    for ext in ["pdf", "docx", "txt", "html", "tex"]:
        fname = f"13244_2019_Article_719_fr.{ext}"
        src = OUTPUT_DIR / fname
        dst = DEST_DIR / fname
        try:
            shutil.copy2(src, dst)
            print(f"Copied {fname} to {DEST_DIR} ({dst.stat().st_size / 1024:.1f} KB)")
        except Exception as e:
            print(f"Notice: Could not copy {fname} (possibly open in viewer): {e}")

    print("=== Medical Polishing Completed Successfully ===")
