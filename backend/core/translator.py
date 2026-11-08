import os
import re
import time
from typing import Dict, List, Optional, Tuple, Any

import torch
from transformers import MarianMTModel, MarianTokenizer

from .entity_protector import EntityProtector
from .glossary import ScientificGlossary

class ScientificTranslator:
    """
    Core Scientific Translation Engine.
    Executes high-fidelity translation from multiple languages to academic French.
    Preserves:
      - 100% of mathematical equations & symbols
      - 100% of numbers, statistical intervals, and scientific units
      - 100% of bibliographic citations, author names, DOIs, and URLs
      - Scientific terminology consistency across disciplines.
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        try:
            torch.set_num_threads(min(8, os.cpu_count() or 4))
        except Exception:
            pass
        self.protector = EntityProtector()
        self.glossary = ScientificGlossary()
        
        # Local model cache: (src, trg) -> (tokenizer, model)
        self.models: Dict[str, Tuple[Any, Any]] = {}

        # Default model names
        self.model_map = {
            "en-fr": "Helsinki-NLP/opus-mt-en-fr",
            "de-fr": "Helsinki-NLP/opus-mt-de-fr",
            "es-fr": "Helsinki-NLP/opus-mt-es-fr",
            "it-fr": "Helsinki-NLP/opus-mt-it-fr",
            "nl-fr": "Helsinki-NLP/opus-mt-nl-fr"
        }

    def _get_or_load_model(self, src: str, trg: str = "fr"):
        pair_key = f"{src}-{trg}"
        if pair_key in self.models:
            return self.models[pair_key]

        model_name = self.model_map.get(pair_key)
        if not model_name:
            # If direct pair doesn't exist, use en-fr as primary or pivot
            model_name = self.model_map.get("en-fr")
            pair_key = "en-fr"
            if pair_key in self.models:
                return self.models[pair_key]

        try:
            print(f"[ScientificTranslator] Loading local neural model: {model_name}...")
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name).to(self.device)
            model.eval()
            self.models[pair_key] = (tokenizer, model)
            return self.models[pair_key]
        except Exception as e:
            print(f"[ScientificTranslator] Warning: Local Marian model {model_name} failed to load: {e}")
            return None, None

    def translate_segment(self, text: str, src_lang: str = "en", domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Translates a single scientific text segment (title, heading, or paragraph).
        Steps:
        1. Check Translation Memory (TM) for 100% match.
        2. Protect non-translatables (equations, numbers, units, citations, DOIs).
        3. Split into sentences to ensure maximum NMT precision.
        4. Translate each sentence using local NMT or fallback.
        5. Restore protected placeholders.
        6. Enforce domain terminology consistency via Scientific Glossary.
        """
        clean_text = text.strip()
        if not clean_text:
            return {
                "source": text,
                "translated": text,
                "cached": False,
                "warnings": []
            }

        # 1. Translation Memory query
        tm_match = self.glossary.query_tm(clean_text, threshold=98.0)
        if tm_match:
            return {
                "source": text,
                "translated": tm_match[0],
                "cached": True,
                "warnings": []
            }

        # 1b. Domain abbreviation disambiguation (e.g. avoid US -> États-Unis in medicine)
        preprocessed_text = self._preprocess_domain_abbreviations(clean_text, domain)

        # 2. Protect scientific entities
        protected_text, placeholder_map = self.protector.protect(preprocessed_text)

        # 3. Sentence segmentation
        sentences = self._split_into_sentences(protected_text)
        valid_sentences = [s.strip() for s in sentences if s.strip()]
        if not valid_sentences:
            return {"source": text, "translated": text, "cached": False, "warnings": []}

        translated_sentences = []
        all_warnings: List[str] = []

        tokenizer, model = self._get_or_load_model(src_lang, "fr")

        if model and tokenizer:
            try:
                # Batch inference for high performance
                inputs = tokenizer(valid_sentences, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_new_tokens=512, num_beams=1)
                translated_sentences = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            except Exception as ex:
                print(f"Local batch inference notice: {ex}. Using fallback.")
                for s in valid_sentences:
                    translated_sentences.append(self._fallback_translate(s, src_lang))
        else:
            for s in valid_sentences:
                translated_sentences.append(self._fallback_translate(s, src_lang))

        combined_translation = " ".join(translated_sentences).strip()

        # 4. Restore protected entities
        restored_translation, restore_warnings = self.protector.restore(combined_translation, placeholder_map)
        all_warnings.extend(restore_warnings)

        # 5. Enforce domain glossary post-translation
        final_translation = self.glossary.enforce_glossary_post(restored_translation, domain=domain)

        # 6. Save confirmed segment into Translation Memory
        self.glossary.add_to_tm(clean_text, final_translation)

        return {
            "source": text,
            "translated": final_translation,
            "cached": False,
            "warnings": all_warnings
        }

    def _preprocess_domain_abbreviations(self, text: str, domain: Optional[str]) -> str:
        """
        Disambiguates medical & technical acronyms before neural machine translation
        to eliminate false-friend mistranslations (e.g. US -> États-Unis instead of ultrasound).
        """
        result = text
        if domain == "medicine_radiology" or domain is None:
            # Expand 'US' when referring to ultrasound in radiological contexts
            result = re.sub(r"\btransvaginal US\b", "transvaginal ultrasound", result, flags=re.IGNORECASE)
            result = re.sub(r"\bpelvic US\b", "pelvic ultrasound", result, flags=re.IGNORECASE)
            result = re.sub(r"\broutine US\b", "routine ultrasound", result, flags=re.IGNORECASE)
            result = re.sub(r"\bDoppler US\b", "Doppler ultrasound", result, flags=re.IGNORECASE)
            result = re.sub(r"\badvanced US\b", "advanced ultrasound", result, flags=re.IGNORECASE)
            result = re.sub(r"\bdedicated US\b", "dedicated ultrasound", result, flags=re.IGNORECASE)
            result = re.sub(r"\bUS findings\b", "ultrasound findings", result, flags=re.IGNORECASE)
            result = re.sub(r"\bUS protocol\b", "ultrasound protocol", result, flags=re.IGNORECASE)
            result = re.sub(r"\bUS protocols\b", "ultrasound protocols", result, flags=re.IGNORECASE)
            result = re.sub(r"\bCT scan\b", "computed tomography scan", result, flags=re.IGNORECASE)
            result = re.sub(r"\bCT scans\b", "computed tomography scans", result, flags=re.IGNORECASE)
            result = re.sub(r"\bCT examination\b", "computed tomography examination", result, flags=re.IGNORECASE)
        return result

    def _fallback_translate(self, text: str, src_lang: str) -> str:
        """Fallback mechanism if local neural model is unavailable."""
        try:
            from deep_translator import MyMemoryTranslator
            res = MyMemoryTranslator(source=src_lang, target='fr').translate(text)
            if res:
                return res
        except Exception:
            pass
        return text

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Splits text into sentences while respecting protected tokens,
        abbreviations (e.g., et al., i.e., e.g., Fig., Dr., Prof.), and decimal numbers.
        """
        # Protect common abbreviations from premature splitting
        abbrevs = [r"\bet al\.", r"\bi\.e\.", r"\be\.g\.", r"\bFig\.", r"\bno\.", r"\bvol\.", r"\bDr\.", r"\bProf\."]
        temp_text = text
        for idx, ab in enumerate(abbrevs):
            temp_text = re.sub(ab, f"__ABBR_{idx}__", temp_text, flags=re.IGNORECASE)

        # Split on punctuation followed by space and uppercase
        raw_splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9_«\"])", temp_text)

        # Restore abbreviations
        sentences = []
        for s in raw_splits:
            s_clean = s
            for idx, ab in enumerate(abbrevs):
                orig = ab.replace(r"\b", "").replace(r"\.", ".")
                s_clean = s_clean.replace(f"__ABBR_{idx}__", orig)
            if s_clean.strip():
                sentences.append(s_clean.strip())

        return sentences if sentences else [text]
