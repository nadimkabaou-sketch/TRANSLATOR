import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz

class ScientificGlossary:
    """
    Manages domain-specific scientific glossaries (EN -> FR)
    and Translation Memory (TM) to maintain strict terminology consistency.
    """

    def __init__(self, glossary_dir: Optional[Path] = None, tm_dir: Optional[Path] = None):
        self.glossary_dir = glossary_dir or (Path(__file__).resolve().parent.parent.parent / "data" / "glossaries")
        self.tm_dir = tm_dir or (Path(__file__).resolve().parent.parent.parent / "data" / "translation_memory")
        self.glossaries: Dict[str, Dict[str, str]] = {}
        self.translation_memory: Dict[str, str] = {}
        self.load_glossaries()
        self.load_translation_memory()

    def load_glossaries(self):
        """Loads all domain JSON glossaries from the glossary directory."""
        self.glossary_dir.mkdir(parents=True, exist_ok=True)
        # Create core built-in glossaries if missing
        self._ensure_default_glossaries()

        for file_path in self.glossary_dir.glob("*.json"):
            domain = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.glossaries[domain] = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load glossary {file_path}: {e}")

    def _ensure_default_glossaries(self):
        """Initializes default comprehensive glossaries across scientific disciplines."""
        # 1. Medicine & Radiology (Includes RSNA Endometriosis terms, MRI, US, anatomy)
        med_rad = {
            "deep endometriosis": "endométriose profonde",
            "transvaginal ultrasound": "échographie endovaginale",
            "transvaginal US": "échographie endovaginale",
            "magnetic resonance imaging": "imagerie par résonance magnétique",
            "MRI": "IRM",
            "TVUS": "échographie endovaginale",
            "endometrioma": "endométriome",
            "endometriomas": "endométriomes",
            "uterosacral ligament": "ligament utéro-sacré",
            "uterosacral ligaments": "ligaments utéro-sacrés",
            "USL": "LUS",
            "torus uterinus": "torus utérin",
            "pouch of Douglas": "cul-de-sac de Douglas",
            "rectovaginal septum": "septum recto-vaginal",
            "kissing ovaries": "ovaires accolés (« kissing ovaries »)",
            "T2 dark spot sign": "signe du spot sombre en T2 (« T2 dark spot sign »)",
            "mushroom cap sign": "signe du chapeau de champignon (« mushroom cap sign »)",
            "architectural distortion": "distorsion architecturale",
            "stromal": "stromal",
            "fibrosis": "fibrose",
            "cyclical hemorrhage": "hémorragie cyclique",
            "anterior compartment": "compartiment antérieur",
            "posterior compartment": "compartiment postérieur",
            "lateral pelvic compartment": "compartiment pelvien latéral",
            "extrapelvic": "extrapelvien",
            "bowel wall invasion": "invasion de la paroi intestinale",
            "bladder endometriosis": "endométriose vésicale",
            "sliding sign": "signe du glissement (« sliding sign »)",
            "malignant transformation": "dégénérescence maligne",
            "clear cell carcinoma": "carcinome à cellules claires",
            "endometrioid carcinoma": "carcinome endométrioïde",
            "field of view": "champ de vue (FOV)",
            "signal intensity": "intensité du signal",
            "hyperintense": "hyperintense",
            "hypointense": "hypointense",
            "isointense": "isointense",
            "enhancement": "rehaussement",
            "contrast-enhanced": "rehaussé par le produit de contraste"
        }

        # 2. Physics & Mathematics
        phys_math = {
            "ground state": "état fondamental",
            "wave function": "fonction d'onde",
            "quantum entanglement": "intrication quantique",
            "eigenvalue": "valeur propre",
            "eigenvalues": "valeurs propres",
            "eigenvector": "vecteur propre",
            "boundary conditions": "conditions aux limites",
            "differential equation": "équation différentielle",
            "standard deviation": "écart-type",
            "confidence interval": "intervalle de confiance",
            "least squares": "moindres carrés",
            "signal-to-noise ratio": "rapport signal sur bruit (SNR)",
            "spatial resolution": "résolution spatiale"
        }

        # 3. Biology & Genetics
        bio_gen = {
            "gene expression": "expression génique",
            "stem cells": "cellules souches",
            "pathway": "voie de signalisation",
            "homeostasis": "homéostasie",
            "apoptosis": "apoptose",
            "transcription factor": "facteur de transcription",
            "wild type": "type sauvage",
            "knockout": "invalidation génique (knockout)",
            "cell lineage": "lignée cellulaire"
        }

        # 4. Computer Science & AI
        cs_ai = {
            "deep learning": "apprentissage profond",
            "machine learning": "apprentissage automatique",
            "neural network": "réseau de neurones",
            "convolutional neural network": "réseau de neurones convolutif",
            "loss function": "fonction de perte",
            "backpropagation": "rétropropagation",
            "ground truth": "vérité terrain",
            "overfitting": "surapprentissage",
            "benchmark": "banc d'essai",
            "state-of-the-art": "état de l'art"
        }

        defaults = {
            "medicine_radiology.json": med_rad,
            "physics_mathematics.json": phys_math,
            "biology_genetics.json": bio_gen,
            "computer_science_ai.json": cs_ai
        }

        for fname, data in defaults.items():
            fpath = self.glossary_dir / fname
            if not fpath.exists():
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    def load_translation_memory(self):
        """Loads persistent translation memory pairs."""
        self.tm_dir.mkdir(parents=True, exist_ok=True)
        tm_file = self.tm_dir / "tm.json"
        if tm_file.exists():
            try:
                with open(tm_file, "r", encoding="utf-8") as f:
                    self.translation_memory = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load TM: {e}")

    def save_translation_memory(self):
        """Saves current translation memory pairs."""
        self.tm_dir.mkdir(parents=True, exist_ok=True)
        tm_file = self.tm_dir / "tm.json"
        try:
            with open(tm_file, "w", encoding="utf-8") as f:
                json.dump(self.translation_memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save TM: {e}")

    def query_tm(self, source_text: str, threshold: float = 95.0) -> Optional[Tuple[str, float]]:
        """Checks if a matching segment exists in Translation Memory."""
        clean_src = source_text.strip()
        if clean_src in self.translation_memory:
            return self.translation_memory[clean_src], 100.0

        for tm_src, tm_trg in self.translation_memory.items():
            score = fuzz.ratio(clean_src, tm_src)
            if score >= threshold:
                return tm_trg, float(score)
        return None

    def add_to_tm(self, source_text: str, target_text: str):
        """Stores a confirmed translation pair into Translation Memory."""
        if source_text and target_text:
            self.translation_memory[source_text.strip()] = target_text.strip()
            self.save_translation_memory()

    def get_domain_terms(self, domain: Optional[str] = None) -> Dict[str, str]:
        """Returns aggregated dictionary of terms, prioritizing a specific domain."""
        combined: Dict[str, str] = {}
        # Load all terms
        for d, terms in self.glossaries.items():
            if d != domain:
                combined.update(terms)
        # Overlay specified domain
        if domain and domain in self.glossaries:
            combined.update(self.glossaries[domain])
        return combined

    def enforce_glossary_post(self, translated_text: str, domain: Optional[str] = None) -> str:
        """
        Scans translated text and ensures preferred French terminology is consistently applied.
        For example, preventing erratic variations of key scientific nouns.
        """
        terms = self.get_domain_terms(domain)
        result = translated_text

        # Sort terms by length descending to replace compound terms first
        sorted_pairs = sorted(terms.items(), key=lambda x: len(x[0]), reverse=True)

        for src_en, trg_fr in sorted_pairs:
            # If English term leaked into the translation, replace with exact French term
            pattern = re.compile(rf"\b{re.escape(src_en)}\b", re.IGNORECASE)
            result = pattern.sub(trg_fr, result)

        return result
